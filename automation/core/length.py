"""Content-adaptive summary length.

A book's summary target is derived from its actual content profile instead
of one fixed gate: shallow practical books get concise treatments, dense
academic works and reference texts get maximum-depth treatments. The bounds
are deterministic (derived only from the manifest's own metadata — book
type, curriculum priority, difficulty, and pillar), so the same book always
gets the same target and the validator enforces it.
"""

from __future__ import annotations

# Base word range per book_type (the manifest's own classification).
BOOK_TYPE_RANGES = {
    "Practical Guide": (1200, 2500),
    "Case Study": (1400, 2800),
    "Biography / Memoir": (1500, 3000),
    "Theoretical Synthesis": (1800, 3500),
    "Handbook / Reference": (2000, 4000),
    "Academic Text": (2200, 4500),
}
_DEFAULT_RANGE = (1500, 3000)

DEEP_PILLARS = {
    "Mathematics, Statistics & Quantitative Logic",
    "Computer Science & Software Engineering",
    "Artificial Intelligence & Data Systems",
    "Natural Sciences, Health & Biology",
    "Philosophy, Ethics & Human Society",
}

LIGHT_PILLARS = {
    "Business, Strategy & Enterprise",
    "Leadership, Organizations & Management",
    "Learning, Cognition & Meta-Skills",
}

MIN_FLOOR = 1000
MAX_CAP = 5000



def word_bounds(book: dict[str, str]) -> tuple[int, int]:
    """Return the (min, max) word gate for this book, content-adaptive.

    Adjustments, all derived from the manifest's own metadata:
    - book_type sets the base range (Academic Text >> Practical Guide).
    - priority S (foundational, read-early) raises the ceiling and floor.
    - difficulty Advanced raises both bounds.
    - deep pillars (technical content) raise the ceiling.
    - light pillars (practical guidance) cap the ceiling.
    """
    lo, hi = BOOK_TYPE_RANGES.get(book.get("book_type", ""), _DEFAULT_RANGE)

    if book.get("priority") == "S":
        lo = max(lo, 2500)
        hi += 2500

    if book.get("difficulty") == "Advanced":
        lo += 1500
        hi += 2000

    if book.get("pillar") in DEEP_PILLARS:
        hi += 2000

    if book.get("pillar") in LIGHT_PILLARS:
        hi = min(hi, 7500)

    lo = max(MIN_FLOOR, lo)
    hi = min(MAX_CAP, max(lo + 1000, hi))
    return lo, hi


def length_label(min_words: int, max_words: int) -> str:
    """Human label for the target size, used in prompts and logs."""
    if max_words <= 5000:
        return "concise"
    if max_words <= 8000:
        return "substantial"
    return "maximum-depth"
