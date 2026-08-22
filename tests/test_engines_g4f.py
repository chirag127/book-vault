"""Tests for g4f_client.py and zen_bench.py — provider ranking, caching, safety."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from automation.engines.g4f_client import (
    _load_cache,
    _safe,
    _save_cache,
    benchmark_is_fresh,
    ranked_providers,
)
from automation.engines.zen_bench import (
    _load_cache as zen_load_cache,
    _save_cache as zen_save_cache,
    benchmark_is_fresh as zen_benchmark_is_fresh,
    ranked as zen_ranked,
)


# ---------------------------------------------------------------------------
# g4f_client
# ---------------------------------------------------------------------------
class TestG4fSafe:
    def test_ascii_passthrough(self):
        assert _safe("hello world") == "hello world"

    def test_non_ascii_replaced(self):
        result = _safe("über café naïve")
        assert "?" in result  # non-ASCII replaced with ?

    def test_empty_string(self):
        assert _safe("") == ""


class TestG4fCacheRoundtrip:
    def test_save_and_load(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            data = {
                "Groq": {"ok": True, "seconds": 1.2, "words": 100, "model": "test", "limit": 128000},
                "_benchmarked_at": datetime.now(timezone.utc).isoformat(),
            }
            _save_cache(data)
            loaded = _load_cache()
            assert "Groq" in loaded
            assert loaded["Groq"]["ok"] is True

    def test_missing_cache_returns_empty(self, tmp_path):
        cache_file = tmp_path / "nonexistent.json"
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            assert _load_cache() == {}


class TestG4fRankedProviders:
    def test_ranked_excludes_not_ok(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        data = {
            "Good": {"ok": True, "seconds": 1.0, "words": 50, "limit": 0},
            "Bad": {"ok": False, "seconds": 10.0, "words": 0, "limit": 0},
            "_benchmarked_at": "2026-01-01T00:00:00+00:00",
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            ranked = ranked_providers()
            assert "Good" in ranked
            assert "Bad" not in ranked

    def test_ranked_prefers_higher_limit(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        data = {
            "SmallCtx": {"ok": True, "seconds": 1.0, "words": 50, "limit": 8000},
            "LargeCtx": {"ok": True, "seconds": 1.5, "words": 50, "limit": 128000},
            "_benchmarked_at": "2026-01-01T00:00:00+00:00",
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            ranked = ranked_providers()
            assert ranked.index("LargeCtx") < ranked.index("SmallCtx")

    def test_ranked_prefers_faster_same_limit(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        data = {
            "Slow": {"ok": True, "seconds": 5.0, "words": 50, "limit": 10000},
            "Fast": {"ok": True, "seconds": 1.0, "words": 50, "limit": 10000},
            "_benchmarked_at": "2026-01-01T00:00:00+00:00",
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            ranked = ranked_providers()
            assert ranked.index("Fast") < ranked.index("Slow")


class TestG4fBenchmarkFresh:
    def test_fresh_when_recent(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        data = {"_benchmarked_at": datetime.now(timezone.utc).isoformat()}
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            assert benchmark_is_fresh(max_age_hours=24) is True

    def test_stale_when_old(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        data = {"_benchmarked_at": "2020-01-01T00:00:00+00:00"}
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            assert benchmark_is_fresh(max_age_hours=24) is False

    def test_no_stamp(self, tmp_path):
        cache_file = tmp_path / "g4f_providers.json"
        cache_file.write_text("{}", encoding="utf-8")
        with patch("automation.engines.g4f_client.PROVIDERS_CACHE", cache_file):
            assert benchmark_is_fresh() is False


# ---------------------------------------------------------------------------
# zen_bench
# ---------------------------------------------------------------------------
class TestZenSafe:
    def test_ascii(self):
        assert zen_ranked.__module__ == "automation.engines.zen_bench"

    def test_zen_safe_ascii(self):
        from automation.engines.zen_bench import _safe
        assert _safe("hello") == "hello"
        result = _safe("日本語テスト")
        assert "?" in result


class TestZenCacheRoundtrip:
    def test_save_and_load(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {
            "x-preview-f-free": {"ok": True, "seconds": 2.1, "words": 50, "error": ""},
            "_benchmarked_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            zen_save_cache(data)
            loaded = zen_load_cache()
            assert "x-preview-f-free" in loaded
            assert loaded["x-preview-f-free"]["ok"] is True


class TestZenRanked:
    def test_ranked_by_speed(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {
            "slow-model": {"ok": True, "seconds": 5.0, "words": 20},
            "fast-model": {"ok": True, "seconds": 1.0, "words": 20},
            "_benchmarked_at": datetime.now(timezone.utc).isoformat(),
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            ranked = zen_ranked()
            assert ranked.index("fast-model") < ranked.index("slow-model")

    def test_ranked_excludes_failed(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {
            "ok-model": {"ok": True, "seconds": 1.0, "words": 20},
            "fail-model": {"ok": False, "seconds": 10.0, "words": 0},
            "_benchmarked_at": datetime.now(timezone.utc).isoformat(),
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            ranked = zen_ranked()
            assert "ok-model" in ranked
            assert "fail-model" not in ranked

    def test_ranked_excludes_low_words(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {
            "sparse": {"ok": True, "seconds": 1.0, "words": 2},
            "rich": {"ok": True, "seconds": 1.0, "words": 20},
            "_benchmarked_at": datetime.now(timezone.utc).isoformat(),
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            ranked = zen_ranked(min_words=5)
            assert "rich" in ranked
            assert "sparse" not in ranked


class TestZenBenchmarkFresh:
    def test_fresh(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {"_benchmarked_at": datetime.now(timezone.utc).isoformat()}
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            assert zen_benchmark_is_fresh(max_age_hours=24) is True

    def test_stale(self, tmp_path):
        cache_file = tmp_path / "zen_models.json"
        data = {"_benchmarked_at": "2020-01-01T00:00:00+00:00"}
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        with patch("automation.engines.zen_bench.CACHE", cache_file):
            assert zen_benchmark_is_fresh(max_age_hours=24) is False
