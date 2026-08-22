"""Precompute cross-domain recommendations for each book in the vault."""
from __future__ import annotations

import re


def precompute_book_tokens(books: list[dict[str, str]]) -> dict[str, set[str]]:
    """Precompute token sets for all books in O(N)."""
    token_cache = {}
    for b in books:
        text = f"{b.get('title', '')} {b.get('category', '')} {b.get('subcategory', '')} {b.get('topic', '')}".lower()
        token_cache[b["slug"]] = set(re.findall(r"\b[a-zA-Z]{4,}\b", text))
    return token_cache


def get_recommendations_for_book(
    target_slug: str,
    books: list[dict[str, str]],
    limit: int = 4,
    token_cache: dict[str, set[str]] | None = None,
) -> list[dict[str, str]]:
    target = next((b for b in books if b["slug"] == target_slug), None)
    if not target:
        return []

    if token_cache is None:
        token_cache = precompute_book_tokens(books)

    target_tokens = token_cache.get(target_slug, set())
    target_author = target.get("author", "").lower()
    target_pillar = target.get("pillar", "")

    scores: list[tuple[float, dict[str, str]]] = []
    for b in books:
        if b["slug"] == target_slug:
            continue
        score = 0.0
        # Same author bonus
        b_author = b.get("author", "").lower()
        if target_author and (target_author in b_author or b_author in target_author):
            score += 5.0
        # Same pillar bonus
        if target_pillar and target_pillar == b.get("pillar"):
            score += 2.0
        # Shared keywords bonus
        b_tokens = token_cache.get(b["slug"], set())
        shared = target_tokens.intersection(b_tokens)
        score += len(shared) * 1.5

        if score > 0:
            scores.append((score, b))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scores[:limit]]
