"""Tests for automation/engines/llm_client.py — Provider chain, backoff, cache, rate limiter."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automation.core.config import load_settings
from automation.engines.llm_client import (
    LLM_CACHE_DIR,
    Provider,
    RateLimiter,
    _backoff_delay,
    _cache_path,
    _sanitize,
    build_providers,
    configure_limiter,
    generate_markdown,
    load_cached_response,
    save_cached_response,
)


# ---------------------------------------------------------------------------
# _sanitize / _cache_path
# ---------------------------------------------------------------------------
class TestSanitize:
    def test_normal(self):
        assert _sanitize("hello-world") == "hello-world"

    def test_special_chars(self):
        assert _sanitize("foo/bar:baz") == "foo_bar_baz"

    def test_unicode(self):
        result = _sanitize("ünïcödé")
        assert result.isascii()


class TestCachePath:
    def test_returns_path(self):
        p = _cache_path("test-key")
        assert isinstance(p, Path)
        assert p.suffix == ".json"
        assert "test-key" in p.name


# ---------------------------------------------------------------------------
# LLM response cache
# ---------------------------------------------------------------------------
class TestLLMCache:
    def test_roundtrip(self, tmp_path):
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            key = "test-cache-roundtrip"
            content = "This is a test summary with multiple words."
            save_cached_response(key, content, "test-provider")
            loaded = load_cached_response(key)
            assert loaded == content

    def test_missing_key_returns_none(self, tmp_path):
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            assert load_cached_response("nonexistent-key") is None

    def test_empty_content_returns_none(self, tmp_path):
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            save_cached_response("empty-key", "   ", "provider")
            assert load_cached_response("empty-key") is None

    def test_corrupt_json_returns_none(self, tmp_path):
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            path = tmp_path / "corrupt.json"
            path.write_text("not valid json {{{", encoding="utf-8")
            assert load_cached_response("corrupt") is None


# ---------------------------------------------------------------------------
# _backoff_delay
# ---------------------------------------------------------------------------
class TestBackoffDelay:
    def test_increases_with_attempt(self):
        d0 = _backoff_delay(0, base=2.0, cap=60.0)
        d1 = _backoff_delay(1, base=2.0, cap=60.0)
        d2 = _backoff_delay(2, base=2.0, cap=60.0)
        # Base increases exponentially (with jitter, min check)
        assert d1 > d0 * 0.5  # allow for jitter
        assert d2 > d1 * 0.5

    def test_capped(self):
        for attempt in range(20):
            delay = _backoff_delay(attempt, base=2.0, cap=60.0)
            assert delay <= 60.0 * 1.25 + 1.0  # cap + jitter margin

    def test_positive(self):
        for attempt in range(10):
            assert _backoff_delay(attempt) > 0


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------
class TestRateLimiter:
    def test_respects_interval(self):
        limiter = RateLimiter(calls_per_minute=60)  # 1/sec
        start = time.monotonic()
        limiter.wait()
        limiter.wait()
        elapsed = time.monotonic() - start
        # Should take at least ~1 second (minus floating point noise)
        assert elapsed >= 0.8

    def test_configure_limiter(self):
        configure_limiter(120)
        # Just verify it doesn't crash; the limiter is set


# ---------------------------------------------------------------------------
# build_providers
# ---------------------------------------------------------------------------
class TestBuildProviders:
    def test_zen_primary_returns_zen_first(self):
        settings = load_settings()
        providers = build_providers(settings)
        assert len(providers) >= 1
        assert providers[0].label == "zen"
        assert providers[0].model == settings.zen_model

    def test_nvidia_included_when_key_set(self):
        settings = load_settings()
        providers = build_providers(settings)
        labels = [p.label for p in providers]
        if settings.nvidia_api_key:
            assert "nvidia" in labels
        # If no key, nvidia should not be in the chain
        if not settings.nvidia_api_key:
            assert "nvidia" not in labels

    def test_providers_are_provider_instances(self):
        settings = load_settings()
        providers = build_providers(settings)
        for p in providers:
            assert isinstance(p, Provider)


# ---------------------------------------------------------------------------
# generate_markdown with cache
# ---------------------------------------------------------------------------
class TestGenerateMarkdownCache:
    def test_cache_hit_skips_providers(self, tmp_path):
        """When a cached response exists, no provider is called."""
        settings = load_settings()
        key = "test-cache-hit-skip"
        content = "Cached book summary with enough words to pass validation."
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            save_cached_response(key, content, "test")
            # Should return cached without calling any provider
            result = generate_markdown(
                settings,
                [{"role": "user", "content": "test"}],
                cache_key=key,
            )
            assert result == content

    def test_generation_error_when_all_fail(self, tmp_path):
        """When all providers fail, GenerationError is raised."""
        from automation.engines.llm_client import GenerationError
        settings = load_settings()
        with patch("automation.engines.llm_client.LLM_CACHE_DIR", tmp_path):
            with patch("automation.engines.llm_client.build_providers", return_value=[]):
                with pytest.raises(GenerationError):
                    generate_markdown(
                        settings,
                        [{"role": "user", "content": "test"}],
                        retries=0,
                    )
