"""Precompute cross-domain recommendations for each book in the vault."""
from __future__ import annotations

import re
from pathlib import Path
from .config import ROOT
from .manifest import load_manifest


def get_recommendations_for_book(target_slug: str, books: list[dict[str, str]], limit: int = 4) -> list[dict[str, str]]:
    target = next((b for b in books if b["slug"] == target_slug), None)
    if not target:
        return []

    target_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", (target["title"] + " " + target["category"] + " " + target["subcategory"]).lower()))

    scores: list[tuple[float, dict[str, str]]] = []
    for b in books:
        if b["slug"] == target_slug:
            continue
        score = 0.0
        # Same author bonus
        if target["author"] and target["author"].lower() in b["author"].lower():
            score += 5.0
        # Same pillar bonus
        if target["pillar"] == b["pillar"]:
            score += 2.0
        # Shared keywords bonus
        b_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", (b["title"] + " " + b["category"] + " " + b["subcategory"]).lower()))
        shared = target_tokens.intersection(b_tokens)
        score += len(shared) * 1.5

        if score > 0:
            scores.append((score, b))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scores[:limit]]
