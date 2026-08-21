from __future__ import annotations

import os
from unittest.mock import patch
from automation.core.config import Settings, load_settings


def test_default_settings_loaded():
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.pipeline_workers >= 5
    assert settings.llm_retries >= 7
    assert settings.search_retries >= 3
    assert settings.zen_model == "x-preview-f-free"


def test_custom_env_workers():
    with patch.dict(os.environ, {"PIPELINE_WORKERS": "10", "SEARCH_RETRIES": "5"}):
        settings = load_settings()
        assert settings.pipeline_workers == 10
        assert settings.search_retries == 5
