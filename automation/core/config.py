from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")



class ConfigurationError(RuntimeError):
    """Raised when required pipeline configuration is missing or unsafe."""


@dataclass(frozen=True)
class Settings:
    primary_provider: str
    zen_base_url: str
    zen_model: str
    zen_ox_alpha_retries: int
    zen_fallback_retries: int
    zen_fallback_models: list[str]
    nvidia_api_key: str
    nvidia_base_url: str
    nvidia_model: str
    max_tokens: int
    temperature: float
    top_p: float
    min_words: int
    max_words: int
    llm_retries: int
    fallback_retries: int
    search_retries: int
    use_ddgs: bool
    use_openlibrary: bool
    use_wikipedia: bool
    use_crossref: bool
    use_yacy: bool
    yacy_url: str
    use_dokobot: bool
    use_g4f: bool
    g4f_max_age_hours: int
    pipeline_workers: int
    llm_calls_per_minute: int
    zen_max_models: int


def _bool_flag(name: str, default: str = "off") -> bool:
    return os.getenv(name, default).lower() not in {"0", "false", "off"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be numeric.") from exc


def load_settings() -> Settings:
    primary = os.getenv("PRIMARY_PROVIDER", "zen").strip().lower()
    if primary not in {"zen", "nvidia"}:
        raise ConfigurationError("PRIMARY_PROVIDER must be 'zen' or 'nvidia'.")

    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if nvidia_key in {"nvapi-replace-me", "replace-me", "your-nvidia-key-here"}:
        nvidia_key = ""
    if primary == "nvidia" and not nvidia_key:
        raise ConfigurationError("PRIMARY_PROVIDER=nvidia requires NVIDIA_API_KEY in .env.")

    fallback_models_raw = os.getenv(
        "ZEN_FALLBACK_MODELS",
        "nemotron-3-ultra-free,laguna-s-2.1-free,nemotron-3.5-lightning-free,muse-spark-1.2-contributor-free,hy3-free,big-pickle",
    )
    zen_fallback_models = [m.strip() for m in fallback_models_raw.split(",") if m.strip()]

    return Settings(
        primary_provider=primary,
        zen_base_url=os.getenv("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/"),
        zen_model=os.getenv("OPENCODE_ZEN_MODEL", "x-preview-f-free"),
        zen_ox_alpha_retries=_int("ZEN_OX_ALPHA_RETRIES", 0),
        zen_fallback_retries=_int("ZEN_FALLBACK_RETRIES", 0),
        zen_fallback_models=zen_fallback_models,
        nvidia_api_key=nvidia_key,
        nvidia_base_url=os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/"),
        nvidia_model=os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash-0731"),
        max_tokens=min(_int("MAX_TOKENS", _int("NVIDIA_MAX_TOKENS", 65536)), 131072),
        temperature=_float("TEMPERATURE", _float("NVIDIA_TEMPERATURE", 0.2)),
        top_p=_float("TOP_P", _float("NVIDIA_TOP_P", 0.95)),
        min_words=max(500, _int("BOOK_MIN_WORDS", 2500)),
        max_words=max(2000, _int("BOOK_MAX_WORDS", 15000)),
        llm_retries=max(1, _int("LLM_RETRIES", 10)),
        fallback_retries=max(1, _int("FALLBACK_RETRIES", 10)),
        search_retries=max(1, _int("SEARCH_RETRIES", 5)),
        use_ddgs=_bool_flag("DDGS_SEARCH", "on"),
        use_openlibrary=_bool_flag("OPENLIBRARY_SEARCH", "on"),
        use_wikipedia=_bool_flag("WIKIPEDIA_SEARCH", "on"),
        use_crossref=_bool_flag("CROSSREF_SEARCH", "on"),
        use_yacy=_bool_flag("YACY_SEARCH", "off"),
        yacy_url=os.getenv("YACY_URL", "http://localhost:8090").rstrip("/"),
        use_dokobot=_bool_flag("DOKO_SEARCH", "off"),
        use_g4f=_bool_flag("G4F_ENABLED", "on"),
        g4f_max_age_hours=max(1, _int("G4F_MAX_AGE_HOURS", 24)),
        pipeline_workers=max(1, _int("PIPELINE_WORKERS", 10)),
        llm_calls_per_minute=max(1, _int("LLM_CALLS_PER_MINUTE", 120)),
        zen_max_models=max(1, min(11, _int("ZEN_MAX_MODELS", 11))),
    )
