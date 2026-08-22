import time
import json
import os
import httpx
from pathlib import Path
from openai import OpenAI
from g4f.client import Client as G4FClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

QUESTIONS = [
    "Q1: In 2 sentences, explain the central thesis of Make It Stick by Peter Brown.",
    "Q2: What are the 4 Laws of Behavior Change from Atomic Habits by James Clear?",
    "Q3: Explain the difference between System 1 and System 2 thinking in Kahneman's Thinking, Fast and Slow.",
    "Q4: What is the Lindy Effect and how does Nassim Taleb apply it to books and ideas?",
    "Q5: Write a concise Python function that performs binary search on a sorted list.",
    "Q6: Summarize the concept of 'Desirable Difficulties' in cognitive psychology.",
    "Q7: What is the core lesson of Viktor Frankl's Man's Search for Meaning regarding purpose?",
    "Q8: Name the 3 pillars of Ray Dalio's Principles for systematic decision making.",
    "Q9: Explain how spaced repetition shifts memory consolidation along the Ebbinghaus forgetting curve.",
    "Q10: In 2 sentences, explain why massed practice (cramming) creates an illusion of competence."
]

zen_url = os.getenv("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1")
nvidia_key = os.getenv("NVIDIA_API_KEY", "")
nvidia_url = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
nvidia_model = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash-0731")

def test_zen_model(model_name, q):
    t0 = time.time()
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(f"{zen_url}/chat/completions", json={
                "model": model_name,
                "messages": [{"role": "user", "content": q}],
                "max_tokens": 300,
                "temperature": 0.2
            })
            if r.status_code == 200:
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or msg.get("reasoning_content") or ""
                return True, round(time.time() - t0, 2), len(content.split()), content[:65].replace("\n", " ")
            return False, round(time.time() - t0, 2), 0, f"HTTP {r.status_code}"
    except Exception as e:
        return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

def test_nvidia(q):
    if not nvidia_key:
        return False, 0.0, 0, "No key configured"
    t0 = time.time()
    try:
        client = OpenAI(base_url=nvidia_url, api_key=nvidia_key)
        resp = client.chat.completions.create(
            model=nvidia_model,
            messages=[{"role": "user", "content": q}],
            max_tokens=300,
            temperature=0.2
        )
        content = resp.choices[0].message.content or ""
        return True, round(time.time() - t0, 2), len(content.split()), content[:65].replace("\n", " ")
    except Exception as e:
        return False, round(time.time() - t0, 2), 0, str(type(e).__name__)

def test_g4f(q):
    t0 = time.time()
    try:
        client = G4FClient()
        resp = client.chat.completions.create(
            model="",
            messages=[{"role": "user", "content": q}],
        )
        content = (resp.choices[0].message.content or "").strip()
        model = getattr(resp, "model", "auto")
        clean_text = content[:50].replace("\n", " ")
        return True, round(time.time() - t0, 2), len(content.split()), f"[{model}] {clean_text}"
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
print(" 10-QUESTION BENCHMARK: ZEN vs NVIDIA vs GPT4FREE", flush=True)
print("==========================================================================\n", flush=True)

results = {name: {"ok": 0, "fail": 0, "latencies": [], "words": []} for name, _ in targets}

for i, q in enumerate(QUESTIONS, start=1):
    print(f"--- [Q{i}/10] {q[:60]}... ---", flush=True)
    for name, fn in targets:
        ok, latency, words, excerpt = fn(q)
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
    time.sleep(0.5)

print("==========================================================================", flush=True)
print(" FINAL 10-QUESTION BENCHMARK RESULTS", flush=True)
print("==========================================================================", flush=True)
for name, data in results.items():
    avg_lat = round(sum(data["latencies"]) / len(data["latencies"]), 2) if data["latencies"] else 0
    avg_words = round(sum(data["words"]) / len(data["words"]), 1) if data["words"] else 0
    print(f"{name:<24} | Success: {data['ok']}/10 ({data['ok']*10}%) | Avg Latency: {avg_lat:>4}s | Avg Words: {avg_words}", flush=True)
print("==========================================================================", flush=True)
