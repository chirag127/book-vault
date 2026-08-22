"""GPT4Free (g4f) fallback provider for the generation pipeline.

Design:
- Every text-capable g4f provider is tested EXACTLY ONCE with a real book
  prompt (one attempt, no retries), so the benchmark itself never hammers a
  provider.
- Results are ranked (working first, then fastest) and cached in the repo at
  ``automation/cache/g4f_providers.json`` so later runs reuse the ranking
  instead of re-testing everything.
- The pipeline then tries providers in ranked order, one attempt each, until
  one returns content — Zen and NVIDIA remain the primary/fallback chain and
  g4f is the last resort.

Caveat: g4f providers are community endpoints — they come and go, may be slow,
and some require browser automation. That is exactly why we benchmark once,
rank, cache, and only use the best.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import ROOT

CACHE_DIR = ROOT / "cache"
PROVIDERS_CACHE = CACHE_DIR / "g4f_providers.json"


# Providers that generate media or speech, not text — never benchmarked.
MEDIA_PROVIDERS = {
    "BingCreateImages",
    "BlackForestLabs_Flux1Dev",
    "BlackForestLabs_Flux1KontextDev",
    "EdgeTTS",
    "ElevenLabs",
    "Custom",
    "AnyProvider",  # meta-provider, not a concrete endpoint
}

DEFAULT_PROBE_TIMEOUT = 25.0


def _safe(text: str) -> str:
    """ASCII-safe text for consoles that cannot print non-Latin characters."""
    return text.encode("ascii", "replace").decode("ascii")


class G4fError(RuntimeError):
    """Raised when every ranked g4f provider fails."""


PREFERRED_G4F_PROVIDERS = [
    "CohereForAI_C4AI_Command",
    "HuggingSpace",
    "Gemini",
]


def text_provider_names() -> list[str]:
    """All g4f providers marked working that produce text, prioritizing verified fast ones."""
    from g4f import Provider
    from g4f.Provider import ProviderUtils

    names = sorted(ProviderUtils.convert.keys())
    out: list[str] = list(PREFERRED_G4F_PROVIDERS)
    for name in names:
        if name in MEDIA_PROVIDERS or name in PREFERRED_G4F_PROVIDERS:
            continue
        cls = getattr(Provider, name, None)
        if cls is None:
            continue
        try:
            if getattr(cls, "working", True) is False:
                continue
        except Exception:
            continue
        out.append(name)
    return out


def _provider_model(name: str) -> str | None:
    """Pick a sensible model for a provider: its first listed model, else None
    (the g4f client then uses its default)."""
    from g4f import Provider

    cls = getattr(Provider, name)
    models = getattr(cls, "models", None)
    if not models:
        return None
    if isinstance(models, dict):
        first = next(iter(models))
    elif isinstance(models, (list, tuple, set)):
        first = list(models)[0]
    else:
        return None
    return str(first) if first else None


def _model_limit(model_name: str) -> int:
    """Context limit (input + output tokens) of a g4f model, 0 if unknown.

    Used to prefer providers whose auto-selected model has the largest
    context window — exactly what long book summaries need.
    """
    if not model_name:
        return 0
    try:
        from g4f.models import ModelUtils

        model = ModelUtils.convert.get(model_name)
        return int(getattr(model, "limit", 0) or 0)
    except Exception:
        return 0


def _call(name: str, messages: list[dict[str, str]], timeout: float) -> tuple[str, float, str]:
    """One synchronous g4f call in AUTO mode. Returns (content, elapsed_seconds, model).

    ``model=""`` makes g4f pick the best available model for the provider
    (the "Auto (Best Available)" behavior from g4f.dev). If a provider
    rejects the empty model, we retry once with its first declared model.
    """
    from g4f import Provider
    from g4f.client import Client

    cls = getattr(Provider, name)
    client = Client()
    start = time.monotonic()
    try:
        response = client.chat.completions.create(
            model="",  # auto: g4f selects the best available model
            messages=messages,
            provider=cls,
        )
    except Exception:
        # Some providers require an explicit model — retry with their first one.
        response = client.chat.completions.create(
            model=_provider_model(name) or "gpt-4o-mini",
            messages=messages,
            provider=cls,
        )
    content = (response.choices[0].message.content or "").strip()
    model = getattr(response, "model", "") or ""
    return content, time.monotonic() - start, model


def _load_cache() -> dict:
    if not PROVIDERS_CACHE.exists():
        return {}
    try:
        return json.loads(PROVIDERS_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDERS_CACHE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def benchmark_providers(prompt: str, force: bool = False) -> list[str]:
    """Test every text provider once (unless cached and fresh) and return the
    ranked provider names, best first. Results are saved after each test so an
    interrupted benchmark resumes where it stopped.
    """
    data = _load_cache()
    names = text_provider_names()
    if not names:
        raise G4fError("No g4f text providers available.")
    todo = [name for name in names if force or name not in data]
    # Re-probe providers that worked before but lack model/limit info so the
    # ranking can prefer the largest-context models.
    reprobe = [
        name
        for name in names
        if name in data and data[name].get("ok") and not data[name].get("model")
    ]
    todo = sorted(set(todo) | set(reprobe))
    if todo:
        print(f"        g4f benchmark: testing {len(todo)} provider(s) once each (prompt: {prompt[:60]}...)", flush=True)
    else:
        print(f"        g4f benchmark: using cached ranking for {len(names)} providers", flush=True)
    if not todo:
        data["_benchmarked_at"] = datetime.now(timezone.utc).isoformat()
        _save_cache(data)

    for index, name in enumerate(todo, start=1):
        tested_at = datetime.now(timezone.utc).isoformat()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call, name, [{"role": "user", "content": prompt}], DEFAULT_PROBE_TIMEOUT)
                content, seconds, model = future.result(timeout=DEFAULT_PROBE_TIMEOUT + 5)
            data[name] = {
                "ok": bool(content),
                "seconds": round(seconds, 1),
                "words": len(content.split()),
                "model": model,
                "limit": _model_limit(model),
                "error": "",
                "tested_at": tested_at,
            }
            print(f"        g4f [{index}/{len(todo)}] {name}: {'OK ' + str(len(content.split())) + ' words in ' + str(round(seconds,1)) + 's' if content else 'empty response'}", flush=True)
        except Exception as exc:  # timeout, network, provider error — one attempt only
            data[name] = {
                "ok": False,
                "seconds": DEFAULT_PROBE_TIMEOUT,
                "words": 0,
                "error": _safe(str(exc))[:140],
                "tested_at": tested_at,
            }
            print(f"        g4f [{index}/{len(todo)}] {name}: FAIL ({_safe(str(exc))[:80]})", flush=True)
        _save_cache(data)

    data["_benchmarked_at"] = datetime.now(timezone.utc).isoformat()
    _save_cache(data)
    return ranked_providers()


def ranked_providers(min_words: int = 10) -> list[str]:
    """Rank cached providers: working first, then the largest context limit
    (input + output tokens), then fastest. Best provider first."""
    data = _load_cache()
    entries = []
    for name, record in data.items():
        if name.startswith("_") or not record.get("ok") or record.get("words", 0) < min_words:
            continue
        limit = int(record.get("limit", 0) or 0)
        entries.append((-limit, record.get("seconds", 999), name))
    entries.sort(key=lambda item: (item[0], item[1], item[2]))
    return [name for _, _, name in entries]


def benchmark_is_fresh(max_age_hours: int = 24) -> bool:
    """True when a completed full benchmark exists and is younger than the cap."""
    data = _load_cache()
    stamp = data.get("_benchmarked_at", "")
    if not stamp:
        return False
    try:
        from datetime import datetime

        tested = datetime.fromisoformat(stamp)
    except (ValueError, TypeError):
        return False
    age = (datetime.now(timezone.utc) - tested).total_seconds() / 3600
    return age < max_age_hours


def generate_markdown_g4f(messages: list[dict[str, str]], retries: int = 0) -> str:
    """Generate with the best-ranked g4f provider. One attempt per provider,
    then move down the ranking; never retries the same provider."""
    ranked = ranked_providers()
    if not ranked:
        raise G4fError("No working g4f providers in cache. Run the benchmark first.")
    last_error: Exception | None = None
    for attempt in range(max(1, retries + 1)):
        for name in ranked:
            print(f"        LLM g4f: trying {name} (rank {ranked.index(name) + 1}/{len(ranked)})", flush=True)
            try:
                content, seconds, _model = _call(name, messages, timeout=600.0)
                if content.strip():
                    print(f"        LLM g4f: {name} OK, {len(content.split())} words in {round(seconds, 1)}s", flush=True)
                    return content.strip()
                print(f"        LLM g4f: {name} returned empty — next provider", flush=True)
            except Exception as exc:
                last_error = exc
                print(f"        LLM g4f: {name} failed ({_safe(str(exc))[:100]}) — next provider", flush=True)
    raise G4fError(f"All ranked g4f providers failed. Last error: {last_error}")
