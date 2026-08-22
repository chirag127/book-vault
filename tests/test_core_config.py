"""Tests for automation/core/config.py — Settings, load_settings, env overrides."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from automation.core.config import ConfigurationError, Settings, load_settings


class TestLoadSettings:
    """load_settings() with default .env."""

    def test_returns_settings_instance(self):
        s = load_settings()
        assert isinstance(s, Settings)

    def test_defaults_are_sane(self):
        s = load_settings()
        assert s.pipeline_workers >= 5
        assert s.llm_retries >= 7
        assert s.search_retries >= 3
        assert s.zen_model == "x-preview-f-free"
        assert s.primary_provider in {"zen", "nvidia"}
        assert 0.0 <= s.temperature <= 1.0
        assert 0.0 <= s.top_p <= 1.0
        assert s.min_words >= 500
        assert s.max_words >= 2000
        assert s.max_words > s.min_words

    def test_zen_base_url_no_trailing_slash(self):
        s = load_settings()
        assert not s.zen_base_url.endswith("/")

    def test_nvidia_base_url_no_trailing_slash(self):
        s = load_settings()
        assert not s.nvidia_base_url.endswith("/")


class TestEnvOverrides:
    """Environment variable overrides work correctly."""

    def test_workers_override(self):
        with patch.dict(os.environ, {"PIPELINE_WORKERS": "12"}):
            s = load_settings()
            assert s.pipeline_workers == 12

    def test_llm_retries_override(self):
        with patch.dict(os.environ, {"LLM_RETRIES": "15"}):
            s = load_settings()
            assert s.llm_retries == 15

    def test_search_retries_override(self):
        with patch.dict(os.environ, {"SEARCH_RETRIES": "7"}):
            s = load_settings()
            assert s.search_retries == 7

    def test_zen_model_override(self):
        with patch.dict(os.environ, {"OPENCODE_ZEN_MODEL": "big-pickle"}):
            s = load_settings()
            assert s.zen_model == "big-pickle"

    def test_temperature_override(self):
        with patch.dict(os.environ, {"TEMPERATURE": "0.7"}):
            s = load_settings()
            assert abs(s.temperature - 0.7) < 0.001

    def test_max_tokens_capped_at_131072(self):
        with patch.dict(os.environ, {"MAX_TOKENS": "999999"}):
            s = load_settings()
            assert s.max_tokens == 131072

    def test_g4f_enabled_off(self):
        with patch.dict(os.environ, {"G4F_ENABLED": "off"}):
            s = load_settings()
            assert s.use_g4f is False

    def test_ddgs_search_off(self):
        with patch.dict(os.environ, {"DDGS_SEARCH": "off"}):
            s = load_settings()
            assert s.use_ddgs is False

    def test_pipeline_workers_floor_is_1(self):
        with patch.dict(os.environ, {"PIPELINE_WORKERS": "0"}):
            s = load_settings()
            assert s.pipeline_workers == 1

    def test_min_words_floor_is_500(self):
        with patch.dict(os.environ, {"BOOK_MIN_WORDS": "100"}):
            s = load_settings()
            assert s.min_words == 500


class TestValidation:
    """Invalid configuration raises ConfigurationError."""

    def test_invalid_primary_provider(self):
        with patch.dict(os.environ, {"PRIMARY_PROVIDER": "openai"}):
            with pytest.raises(ConfigurationError, match="zen.*nvidia"):
                load_settings()

    def test_nvidia_primary_without_key(self):
        with patch.dict(os.environ, {"PRIMARY_PROVIDER": "nvidia", "NVIDIA_API_KEY": ""}):
            with pytest.raises(ConfigurationError, match="NVIDIA_API_KEY"):
                load_settings()

    def test_invalid_max_tokens_raises(self):
        with patch.dict(os.environ, {"MAX_TOKENS": "not-a-number"}):
            with pytest.raises(ConfigurationError, match="integer"):
                load_settings()

    def test_invalid_temperature_raises(self):
        with patch.dict(os.environ, {"TEMPERATURE": "very-hot"}):
            with pytest.raises(ConfigurationError, match="numeric"):
                load_settings()
