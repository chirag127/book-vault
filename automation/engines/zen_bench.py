"""Benchmark OpenCode Zen's free models exactly once each and rank them.

Every free model listed by the Zen API is probed once with a real book
prompt (no retries, no hammering). Results — OK/FAIL, latency, output
words — are cached in the repo at ``automation/cache/zen_models.json`` and
ranked (working first, then fastest). ``build_providers`` then uses the
ranking, best model first, with the slower/weaker models as fallbacks.

The probe uses a small ``max_tokens`` so the benchmark stays fast; ranking
is about availability and speed, not summary depth (the real summaries run
with the pipeline's full ``max_tokens``).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .config import ROOT

CACHE = ROOT / "cache" / "zen_models.json"


# Free (keyless) models advertised by the Zen endpoint, from GET /models.
FREE_MODELS = [
    "x-preview-f-free",
    "deepseek-v4-flash-free",
    "mimo-v2.5-free",
    "hy3-free",
    "nemotron-3-ultra-free",
    "nemotron-3.5-lightning-free",
    "laguna-s-2.1-free",
    "muse-spark-1.2-contributor-free",
]

PROBE = (
    "In 3-5 sentences, summarize the core argument of the book 'Make It Stick' "
    "by Brown, Roediger and McDaniel, and name its three most important techniques."
)


def _safe(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def _load_cache() -> dict:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(data: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _call(base_url: str, model: str, timeout: float = 60.0) -> tuple[str, float]:
    """One keyless Zen call. Returns (content, elapsed_seconds). Raises on failure."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROBE}],
        "max_tokens": 512,
        "temperature": 0.2,
    }
    start = time.monotonic()
    with httpx.Client(timeout=httpx.Timeout(timeout, connect=20.0)) as client:
        response = client.post(f"{base_url}/chat/completions", json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {_safe(response.text[:120])}")
    content = (response.json().get("choices") or [{}])[0].get("message", {}).get("content") or ""
    if not content.strip():
        raise RuntimeError("empty response")
    return content, time.monotonic() - start


def benchmark(settings, force: bool = False) -> list[str]:
    """Probe every free Zen model once (unless cached), save after each test,
    and return the ranked model names, best first."""
    data = _load_cache()
    todo = [model for model in FREE_MODELS if force or model not in data]
    if todo:
        print(f"  zen benchmark: testing {len(todo)} free model(s) once each against {settings.zen_base_url}", flush=True)
    else:
        print("  zen benchmark: using cached ranking", flush=True)

    for index, model in enumerate(todo, start=1):
        tested_at = datetime.now(timezone.utc).isoformat()
        try:
            content, seconds = _call(settings.zen_base_url, model)
            data[model] = {
                "ok": True,
                "seconds": round(seconds, 1),
                "words": len(content.split()),
                "error": "",
                "tested_at": tested_at,
            }
            print(f"  zen [{index}/{len(todo)}] {model}: OK {len(content.split())} words in {round(seconds, 1)}s", flush=True)
        except Exception as exc:
            data[model] = {
                "ok": False,
                "seconds": 30.0,
                "words": 0,
                "error": _safe(str(exc))[:140],
                "tested_at": tested_at,
            }
            print(f"  zen [{index}/{len(todo)}] {model}: FAIL ({_safe(str(exc))[:80]})", flush=True)
        _save_cache(data)

    data["_benchmarked_at"] = datetime.now(timezone.utc).isoformat()
    _save_cache(data)
    return ranked()


def ranked(min_words: int = 5) -> list[str]:
    """Rank cached Zen models: working first, then fastest. Best first."""
    data = _load_cache()
    entries = []
    for model, record in data.items():
        if model.startswith("_") or not record.get("ok") or record.get("words", 0) < min_words:
            continue
        entries.append((record.get("seconds", 999), model))
    entries.sort(key=lambda item: (item[0], item[1]))
    return [model for _, model in entries]


def benchmark_is_fresh(max_age_hours: int = 24) -> bool:
    data = _load_cache()
    stamp = data.get("_benchmarked_at", "")
    if not stamp:
        return False
    try:
        tested = datetime.fromisoformat(stamp)
    except (ValueError, TypeError):
        return False
    age = (datetime.now(timezone.utc) - tested).total_seconds() / 3600
    return age < max_age_hours
