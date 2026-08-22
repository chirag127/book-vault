"""automation/research/__init__.py"""
from __future__ import annotations

from .research import (
    Source,
    load_research,
    save_research,
    search_book,
    source_bundle,
)

__all__ = [
    "Source",
    "load_research",
    "save_research",
    "search_book",
    "source_bundle",
]
