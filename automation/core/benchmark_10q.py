import time
import os
import httpx
from pathlib import Path
from openai import OpenAI
from g4f.client import Client as G4FClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# 10 Short, punchy test questions designed for fast execution (<100 tokens output)
QUESTIONS = [
    "Q1: In 1 sentence, define the core message of Make It Stick.",
    "Q2: List the 4 Laws of Behavior Change from Atomic Habits.",
    "Q3: Define System 1 vs System 2 thinking in 20 words or less.",
    "Q4: In 1 sentence, define the Lindy Effect.",
    "Q5: Write a 3-line Python binary search function.",
    "Q6: Define 'Desirable Difficulties' in 15 words or less.",
    "Q7: What is the main message of Man's Search for Meaning?",
    "Q8: List Ray Dalio's 3-step loop for reality calibration.",
    "Q9: What does the Ebbinghaus forgetting curve show?",
    "Q10: Why is cramming ineffective for long-term recall?"
]

zen_url = os.getenv("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1")
nvidia_key = os.getenv("NVIDIA_API_KEY", "")
nvidia_url = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
nvidia_model = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash-0731")

MAX_TOKENS = 120
MAX_TIMEOUT = 10.0  # Strict 10-second cutoff

def test_zen_model(model_name, q):
    t0 = time.time()
    try:
        with httpx.Client(timeout=MAX_TIMEOUT) as client:
            r = client.post(f"{zen_url}/chat/completions", json={
                "model": model_name,
                "messages": [{"role": "user", "content": q}],
                "max_tokens": MAX_TOKENS,
                "temperature": 0.2
            })
            if r.status_code == 200:
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or msg.get("reasoning_content") or choice.get("text") or ""
                return True, round(time.time() - t0, 2), len(content.split()), content[:60].replace("\n", " ")
            return False, round(time.time() - t0, 2), 0, f"HTTP {r.status_code}"
    except Exception as e:
        return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

def test_nvidia(q):
    if not nvidia_key:
        return False, 0.0, 0, "No key configured"
    t0 = time.time()
    try:
        client = OpenAI(base_url=nvidia_url, api_key=nvidia_key, timeout=MAX_TIMEOUT, max_retries=0)
        resp = client.chat.completions.create(
            model=nvidia_model,
            messages=[{"role": "user", "content": q}],
            max_tokens=MAX_TOKENS,
            temperature=0.2
        )
        content = resp.choices[0].message.content or ""
        return True, round(time.time() - t0, 2), len(content.split()), content[:60].replace("\n", " ")
    except Exception as e:
        return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

def test_g4f(q):
    t0 = time.time()
    try:
        client = G4FClient()
        resp = client.chat.completions.create(
            model="",
            messages=[{"role": "user", "content": q}],
            timeout=MAX_TIMEOUT
        )
        content = (resp.choices[0].message.content or "").strip()
        model = getattr(resp, "model", "auto")
        clean_text = content[:45].replace("\n", " ")
        return True, round(time.time() - t0, 2), len(content.split()), f"[{model}] {clean_text}"
    except Exception as e:
        return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

def run_with_hard_timeout(fn, q, timeout_sec=10.0):
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, q)
        try:
            return future.result(timeout=timeout_sec)
        except FuturesTimeout:
            return False, round(time.time() - t0, 2), 0, "HardTimeout >10s"
        except Exception as e:
            return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

targets = [
    ("Zen: Nemotron-3-Ultra", lambda q: test_zen_model("nemotron-3-ultra-free", q)),
    ("Zen: Laguna-S-2.1", lambda q: test_zen_model("laguna-s-2.1-free", q)),
    ("Zen: Ox-Alpha", lambda q: test_zen_model("x-preview-f-free", q)),
    ("NVIDIA: DeepSeek-V4", test_nvidia),
    ("G4F: Auto Client", test_g4f)
]

print("==========================================================================", flush=True)
print(" FAST 10-QUESTION BENCHMARK (HARD 10.0s TIMEOUT PER MODEL)", flush=True)
print("==========================================================================\n", flush=True)

results = {name: {"ok": 0, "fail": 0, "latencies": [], "words": []} for name, _ in targets}

for i, q in enumerate(QUESTIONS, start=1):
    print(f"--- [Q{i}/10] {q} ---", flush=True)
    for name, fn in targets:
        ok, latency, words, excerpt = run_with_hard_timeout(fn, q, timeout_sec=10.0)
        safe_excerpt = excerpt.encode("ascii", "replace").decode("ascii")
        if ok:
            results[name]["ok"] += 1
            results[name]["latencies"].append(latency)
            results[name]["words"].append(words)
            print(f"  [PASS] {name:<24} | {latency:>4}s | {words:>3} words | {safe_excerpt}", flush=True)
        else:
            results[name]["fail"] += 1
            print(f"  [FAIL] {name:<24} | {latency:>4}s | Error: {safe_excerpt}", flush=True)
    print(flush=True)

print("==========================================================================", flush=True)
print(" FINAL BENCHMARK SCORECARD (<10s SPEED & RELIABILITY)", flush=True)
print("==========================================================================", flush=True)
for name, data in results.items():
    avg_lat = round(sum(data["latencies"]) / len(data["latencies"]), 2) if data["latencies"] else 0
    avg_words = round(sum(data["words"]) / len(data["words"]), 1) if data["words"] else 0
    score = data['ok']
    pct = score * 10
    print(f"{name:<24} | Score: {score:>2}/10 ({pct:>3}%) | Avg Latency: {avg_lat:>4}s | Avg Output: {avg_words:>4} words", flush=True)
print("==========================================================================", flush=True)
