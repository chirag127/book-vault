from __future__ import annotations

import json
import random
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from .config import ROOT, Settings

# HTTP statuses that indicate the provider is temporarily unavailable or
# rate-limiting us; these are worth backing off and retrying.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

LLM_CACHE_DIR = ROOT / "automation" / "cache" / "llm"


class GenerationError(RuntimeError):
    """Raised when every configured provider fails."""


@dataclass(frozen=True)
class Provider:
    label: str
    base_url: str
    api_key: str | None
    model: str
    thinking_extra: bool


# ---------------------------------------------------------------------------
# Shared rate limiter: with multiple worker threads, all LLM calls across all
# threads are spaced to a global calls-per-minute cap. It only sleeps when the
# cap would actually be exceeded (no proactive pacing when idle), and every
# 429/5xx still gets exponential backoff on top.
# ---------------------------------------------------------------------------
_limiter_lock = threading.Lock()
_limiter: "RateLimiter | None" = None


class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.min_interval = 60.0 / max(1, calls_per_minute)
        self._lock = threading.Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        """Block only as long as needed to respect the global call rate."""
        with self._lock:
            now = time.monotonic()
            delay = self._next_at - now
            if delay > 0:
                time.sleep(delay)
                now = time.monotonic()
            self._next_at = max(now, self._next_at) + self.min_interval


def configure_limiter(calls_per_minute: int) -> None:
    global _limiter
    with _limiter_lock:
        _limiter = RateLimiter(calls_per_minute)


def _wait_limiter() -> None:
    global _limiter
    with _limiter_lock:
        limiter = _limiter
    if limiter is None:
        configure_limiter(20)  # defensive default when called outside the pipeline
        with _limiter_lock:
            limiter = _limiter
    limiter.wait()


def build_providers(settings: Settings) -> list[Provider]:
    """Return the provider chain in call order.

    1. OpenCode Zen **Ox Alpha Free** — the single best keyless model, used
       exclusively as primary (per the chosen configuration).
    2. NVIDIA (requires NVIDIA_API_KEY; only included when the key is set).
    g4f is handled separately by generate_markdown as the last resort.
    """
    zen = Provider(
        label="zen",
        base_url=settings.zen_base_url,
        api_key=None,
        model=settings.zen_model,
        thinking_extra=False,
    )
    nvidia = Provider(
        label="nvidia",
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key or None,
        model=settings.nvidia_model,
        thinking_extra=True,
    )
    if settings.primary_provider == "nvidia":
        if not nvidia.api_key:
            raise GenerationError("PRIMARY_PROVIDER=nvidia but NVIDIA_API_KEY is not set.")
        return [nvidia, zen]
    chain = [zen]
    if nvidia.api_key:
        chain.append(nvidia)
    return chain


def _backoff_delay(attempt: int, base: float = 2.0, cap: float = 60.0) -> float:
    """Exponential backoff with jitter: base * 2^attempt, capped, plus up to 25% jitter."""
    delay = min(cap, base * (2**attempt))
    return delay + random.uniform(0.0, min(1.0, delay * 0.25))


# ---------------------------------------------------------------------------
# Response cache: every successful LLM response is stored in the repo at
# automation/cache/llm/<key>.json so nothing is ever regenerated twice.
# ---------------------------------------------------------------------------
def _sanitize(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", key)


def _cache_path(key: str) -> Path:
    return LLM_CACHE_DIR / f"{_sanitize(key)}.json"


def load_cached_response(key: str) -> str | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        content = data.get("content", "")
        return content if content.strip() else None
    except (OSError, json.JSONDecodeError):
        return None


def save_cached_response(key: str, content: str, provider: str) -> Path:
    LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    payload = {
        "key": key,
        "provider": provider,
        "words": len(content.split()),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "content": content,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def generate_markdown(settings: Settings, messages: Iterable[dict[str, str]], retries: int = 7, cache_key: str | None = None) -> str:
    """Generate markdown through the provider chain with repo-side caching.

    Chain: Zen Ox Alpha Free (7 exponential-backoff retries) -> NVIDIA ->
    g4f (best-ranked). If ``cache_key`` is given and a cached response exists,
    it is reused and no provider is called at all.
    """
    if cache_key:
        cached = load_cached_response(cache_key)
        if cached is not None:
            print(f"        LLM: CACHED response reused for key '{cache_key}' ({len(cached.split())} words)", flush=True)
            return cached

    providers = build_providers(settings)
    if not providers:
        raise GenerationError("No providers configured.")
    last_error: GenerationError | None = None
    for index, provider in enumerate(providers, start=1):
        _wait_limiter()
        print(f"        LLM: trying provider {index}/{len(providers)}: {provider.label} ({provider.model})", flush=True)
        try:
            if provider.label.startswith("zen"):
                content = _generate_with_zen(provider, settings, messages, retries)
            else:
                content = _generate_with_sdk(provider, settings, messages, retries)
            if cache_key:
                save_cached_response(cache_key, content, provider.label)
            return content
        except GenerationError as exc:
            last_error = exc
            print(f"        LLM: provider failed: {provider.label}: {exc}", flush=True)

    # Last resort: gpt4free, using the best-ranked provider from the benchmark.
    if settings.use_g4f:
        try:
            from .g4f_client import generate_markdown_g4f

            _wait_limiter()
            print("        LLM: all Zen/NVIDIA providers failed — falling back to gpt4free (best-ranked)", flush=True)
            content = generate_markdown_g4f(list(messages), retries=0)
            if cache_key:
                save_cached_response(cache_key, content, "g4f")
            return content
        except Exception as exc:
            last_error = GenerationError(f"g4f failed: {exc}")
            print(f"        LLM: g4f failed: {exc}", flush=True)

    raise GenerationError(f"All providers failed. Last error: {last_error}")


def _generate_with_zen(
    provider: Provider,
    settings: Settings,
    messages: Iterable[dict[str, str]],
    retries: int,
) -> str:
    """Call OpenCode Zen directly over HTTP without any Authorization header.

    The Zen free endpoints return 401 when the OpenAI SDK sends its dummy
    'not-needed' bearer token, so the SDK is bypassed for this provider.
    Rate limits (429) and temporary 5xx errors back off exponentially.
    """
    payload = {
        "model": provider.model,
        "messages": list(messages),
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "max_tokens": settings.max_tokens,
    }
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
                response = client.post(f"{provider.base_url}/chat/completions", json=payload)
            if response.status_code in RETRYABLE_STATUS:
                delay = _backoff_delay(attempt, base=3.0, cap=120.0)
                print(f"        LLM {provider.label}: HTTP {response.status_code}, backing off {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
                if attempt >= retries:
                    raise GenerationError(f"{provider.label} rate-limited after {retries} retries: HTTP {response.status_code}")
                time.sleep(delay)
                continue
            if response.status_code == 401:
                raise GenerationError(f"{provider.label} rejected the request (401). The free endpoint accepts no Authorization header.")
            response.raise_for_status()
            data = response.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            if not content.strip():
                raise GenerationError(f"{provider.label} returned an empty response.")
            print(f"        LLM {provider.label}: HTTP 200 OK, {len(content.split())} words", flush=True)
            return content.strip()
        except GenerationError:
            raise
        except Exception as exc:  # transient network errors, timeouts
            if attempt >= retries:
                raise GenerationError(f"{provider.label} generation failed: {exc}") from exc
            delay = _backoff_delay(attempt)
            print(f"        LLM {provider.label}: transient error ({exc.__class__.__name__}), retrying in {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
            time.sleep(delay)
    raise AssertionError("unreachable")


def _generate_with_sdk(
    provider: Provider,
    settings: Settings,
    messages: Iterable[dict[str, str]],
    retries: int,
) -> str:
    client = OpenAI(base_url=provider.base_url, api_key=provider.api_key or "not-needed")
    for attempt in range(retries + 1):
        try:
            kwargs: dict = {
                "model": provider.model,
                "messages": list(messages),
                "temperature": settings.temperature,
                "top_p": settings.top_p,
                "max_tokens": settings.max_tokens,
            }
            if provider.thinking_extra:
                kwargs["extra_body"] = {
                    "chat_template_kwargs": {
                        "thinking": True,
                        "reasoning_effort": "high",
                    }
                }
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            if not content.strip():
                raise GenerationError(f"{provider.label} returned an empty response.")
            print(f"        LLM {provider.label}: OK, {len(content.split())} words", flush=True)
            return content.strip()
        except RateLimitError:
            if attempt >= retries:
                raise GenerationError(f"{provider.label} rate-limited after {retries} retries.")
            delay = _backoff_delay(attempt, base=5.0, cap=120.0)
            print(f"        LLM {provider.label}: rate-limited, backing off {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
            time.sleep(delay)
        except APIStatusError as exc:
            if exc.status_code in RETRYABLE_STATUS:
                if attempt >= retries:
                    raise GenerationError(f"{provider.label} failed after {retries} retries: HTTP {exc.status_code}")
                delay = _backoff_delay(attempt, base=3.0, cap=120.0)
                print(f"        LLM {provider.label}: HTTP {exc.status_code}, backing off {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
                time.sleep(delay)
            else:
                raise GenerationError(f"{provider.label} generation failed: {exc}") from exc
        except APIConnectionError:
            if attempt >= retries:
                raise GenerationError(f"{provider.label} connection failed after {retries} retries.")
            delay = _backoff_delay(attempt)
            print(f"        LLM {provider.label}: connection error, retrying in {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
            time.sleep(delay)
        except GenerationError:
            raise
        except Exception as exc:  # any other SDK or network exception
            if attempt >= retries:
                raise GenerationError(f"{provider.label} generation failed: {exc}") from exc
            delay = _backoff_delay(attempt)
            print(f"        LLM {provider.label}: {exc.__class__.__name__}, retrying in {delay:.1f}s (attempt {attempt + 1}/{retries + 1})", flush=True)
            time.sleep(delay)
    raise AssertionError("unreachable")
