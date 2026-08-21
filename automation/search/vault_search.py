from __future__ import annotations

import argparse
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..core.config import ROOT



@dataclass
class SearchHit:
    file_path: Path
    title: str
    author: str
    score: float
    best_excerpt: str


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())


def _extract_title_author(text: str) -> tuple[str, str]:
    title_match = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?", text, re.MULTILINE)
    author_match = re.search(r"^author:\s*[\"']?([^\"'\n]+)[\"']?", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Book Note"
    author = author_match.group(1).strip() if author_match else "Unknown"
    return title, author


def search_vault(query: str, top_k: int = 5) -> list[SearchHit]:
    """Search all Markdown files across the vault using term-frequency scoring."""
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    hits: list[SearchHit] = []
    md_files = list(ROOT.glob("md/**/*.md"))

    for path in md_files:
        if path.name == "README.md" and len(path.parts) <= 3:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue

        tokens = _tokenize(content)
        if not tokens:
            continue

        counts = Counter(tokens)
        score = 0.0
        for term in query_terms:
            tf = counts.get(term, 0)
            if tf > 0:
                score += (1 + math.log(tf))

        if score > 0:
            title, author = _extract_title_author(content)
            # Find best snippet
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 80]
            best_snippet = paragraphs[0] if paragraphs else content[:200]
            best_snippet_score = 0
            for p in paragraphs:
                p_tokens = Counter(_tokenize(p))
                p_score = sum(p_tokens.get(t, 0) for t in query_terms)
                if p_score > best_snippet_score:
                    best_snippet_score = p_score
                    best_snippet = p

            hits.append(SearchHit(
                file_path=path,
                title=title,
                author=author,
                score=score,
                best_excerpt=best_snippet[:300].replace("\n", " ") + "...",
            ))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def main() -> int:
    parser = argparse.ArgumentParser(description="Instant Semantic & Full-Text Search across Book Vault summaries.")
    parser.add_argument("query", nargs="+", help="Search query terms or question.")
    parser.add_argument("--top", type=int, default=5, help="Number of top hits to display (default 5).")
    args = parser.parse_args()

    query_str = " ".join(args.query)
    print(f"\n[SEARCH] Searching Book Vault for: '{query_str}'\n" + "=" * 70)

    hits = search_vault(query_str, top_k=args.top)
    if not hits:
        print("No matching book summaries found.")
        return 0

    for idx, hit in enumerate(hits, 1):
        rel_path = hit.file_path.relative_to(ROOT)
        print(f"[{idx}] {hit.title} (Score: {hit.score:.2f})")
        print(f"    Author : {hit.author}")
        print(f"    Path   : [[{rel_path}]]")
        print(f"    Excerpt: \"{hit.best_excerpt}\"\n")


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
