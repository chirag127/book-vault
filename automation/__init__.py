"""Universal Book Vault — Automated Research, Synthesis & Export System."""

from __future__ import annotations

from .core.config import ROOT, ConfigurationError, Settings, load_settings
from .core.manifest import category_folder, load_manifest
from .core.taxonomy import PILLAR_DIRS
from .core.length import length_label, word_bounds

from .core.validate import validate_note, validate_tree
from .engines.generate import process_one, run
from .engines.llm_client import generate_markdown
from .engines.prompts import TEMPLATE_VERSION, build_audio_tts_prompt, build_modular_reading_prompt
from .research.research import load_research, save_research, search_book, source_bundle
from .audio.synthesize_audio import synthesize_book_audio
from .search.vault_search import search_vault
from .exporters.build_site_data import build_web_data
from .exporters.generate_canvases import generate_all_canvases
from .exporters.export_anki import export_anki_deck
from .exporters.export_ebook import bundle_book_ebook

__all__ = [
    "ROOT",
    "ConfigurationError",
    "Settings",
    "load_settings",
    "category_folder",
    "load_manifest",
    "PILLAR_DIRS",
    "length_label",

    "word_bounds",
    "validate_note",
    "validate_tree",
    "process_one",
    "run",
    "generate_markdown",
    "TEMPLATE_VERSION",
    "build_audio_tts_prompt",
    "build_modular_reading_prompt",
    "load_research",
    "save_research",
    "search_book",
    "source_bundle",
    "synthesize_book_audio",
    "search_vault",
    "build_web_data",
    "generate_all_canvases",
    "export_anki_deck",
    "bundle_book_ebook",
]
