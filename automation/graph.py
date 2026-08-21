"""Build the per-book knowledge-graph context handed to the generator.

Every book note gets a rich linking context computed from the canonical
manifest, so the vault becomes a genuinely interconnected knowledge graph:

- Same-author works (the author's other books in the vault)
- Same-subcategory peers (the closest topical neighbors, in reading order)
- Adjacent curriculum numbers (the previous/next books in the learning sequence)
- Cross-category bridges (books in *other* categories that share a meaningful
  topic — shared significant title tokens after light stemming, or the same
  subcategory name in a different category)

The result is a list of ``RelatedBook`` entries rendered as Obsidian wikilinks
with display aliases, injected into the generation prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Tokens too generic to signal a meaningful cross-category bridge.
_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "for", "in", "on", "to", "with",
    "at", "by", "from", "is", "are", "how", "why", "what", "book", "books",
    "your", "you", "my", "it", "its", "vol", "volume", "guide", "introduction",
    "introducing", "introductionto", "making", "make", "new", "art", "science",
    "man", "men", "do", "does", "done", "don't", "dont", "not", "no", "be",
    "can't", "cant", "ever", "never", "way", "ways", "life", "lives", "world",
    "future", "history", "age", "ages", "power", "powers", "design", "designing",
    "building", "build", "think", "thinking", "learn", "learning", "good",
    "great", "better", "best", "little", "big", "human", "humans",
}


def _stem(token: str) -> str:
    """Light plural/verb stemming so 'habit' matches 'habits'."""
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        return token[:-1]
    return token


def _significant_stems(title: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", title.casefold())
    significant: set[str] = set()
    for token in tokens:
        if len(token) >= 5 and token not in _STOPWORDS:
            significant.add(_stem(token))
    return significant


def _name_tokens(author: str) -> set[str]:
    return {t for part in author.split(";") for t in re.findall(r"[a-z]+", part.casefold())}


def _surnames(author: str) -> set[str]:
    surnames: set[str] = set()
    for part in author.split(";"):
        tokens = part.split()
        if tokens:
            surnames.add(tokens[-1].casefold())
    return surnames


def _first_tokens(author: str) -> set[str]:
    firsts: set[str] = set()
    for part in author.split(";"):
        tokens = part.split()
        if tokens:
            firsts.add(tokens[0].casefold())
    return firsts


def _same_author(author_a: str, author_b: str) -> bool:
    """True when two author strings plausibly name the same person.

    Surname matches alone are not enough (Benjamin Graham vs Ronald Graham,
    Peter Bernstein vs William Bernstein). For single-author books we require
    the first name to match too; for multi-author books we require a shared
    surname plus at least one shared first name across the author lists.
    """
    shared_surnames = _surnames(author_a) & _surnames(author_b)
    if not shared_surnames:
        return False
    single_a = ";" not in author_a
    single_b = ";" not in author_b
    if single_a and single_b:
        return bool(_first_tokens(author_a) & _first_tokens(author_b))
    return bool(_first_tokens(author_a) & _first_tokens(author_b))


@dataclass(frozen=True)
class RelatedBook:
    title: str
    author: str
    category: str
    subcategory: str
    slug: str
    number: str
    reason: str

    def wikilink(self) -> str:
        return f"[[{self.slug}|{self.title}]]"


def _num(book: dict[str, str]) -> int:
    try:
        return int(book.get("number", "0") or 0)
    except ValueError:
        return 0


def build_related(book: dict[str, str], books: list[dict[str, str]], max_links: int = 24) -> list[RelatedBook]:
    """Return the most meaningful related books, ranked and deduplicated."""
    slug = book["slug"]
    others = [b for b in books if b["slug"] != slug]
    my_number = _num(book)

    ranked: list[RelatedBook] = []
    seen: set[str] = set()

    def add(candidate: dict[str, str], reason: str) -> None:
        if candidate["slug"] in seen:
            return
        seen.add(candidate["slug"])
        ranked.append(
            RelatedBook(
                title=candidate["title"],
                author=candidate["author"],
                category=candidate["category"],
                subcategory=candidate["subcategory"],
                slug=candidate["slug"],
                number=candidate.get("number", ""),
                reason=reason,
            )
        )

    ordered = sorted(others, key=_num)

    # 1. Same author (strongest signal of intellectual kinship).
    for other in ordered:
        if _same_author(book["author"], other["author"]):
            add(other, "same author")

    # 2. Same category (level 2) peers, in curriculum reading order.
    for other in ordered:
        if other["pillar"] == book["pillar"] and other["category"] == book["category"]:
            add(other, f"same category ({other['category']})")

    # 3. Adjacent curriculum numbers (previous / next in the learning sequence).
    for other in ordered:
        other_number = _num(other)
        if other_number in (my_number - 1, my_number + 1) and other_number > 0:
            add(other, "reading-order neighbor")

    # 4. Cross-pillar bridges: shared significant title stems.
    my_tokens = _significant_stems(book["title"])
    for other in ordered:
        if other["pillar"] == book["pillar"]:
            continue
        shared = my_tokens & _significant_stems(other["title"])
        if shared:
            add(other, f"shares topic ({', '.join(sorted(shared)[:2])})")

    # 5. Cross-pillar bridges: same subcategory (level 3) topic in another pillar.
    for other in ordered:
        if other["pillar"] == book["pillar"]:
            continue
        if other["subcategory"] == book["subcategory"]:
            add(other, f"same topic in {other['pillar']}")

    # 6. Pillar-peer fallback: earliest books of the same pillar's reading
    # sequence, so even isolated books get a healthy link neighborhood.
    if len(ranked) < 3:
        for other in ordered:
            if other["pillar"] != book["pillar"]:
                continue
            add(other, "pillar reading-sequence peer")
            if len(ranked) >= 3:
                break

    return ranked[:max_links]


def related_map(books: list[dict[str, str]], max_links: int = 24) -> dict[str, set[str]]:
    """Precompute every book's outgoing link set once per manifest load."""
    return {b["slug"]: {r.slug for r in build_related(b, books, max_links=max_links)} for b in books}


def build_incoming(book: dict[str, str], books: list[dict[str, str]], rel_map: dict[str, set[str]], limit: int = 12) -> list[RelatedBook]:
    """Books whose computed neighborhood links to this book (inbound context)."""
    inbound = [b for b in books if b["slug"] != book["slug"] and book["slug"] in rel_map.get(b["slug"], set())]
    inbound.sort(key=_num)
    result = []
    for b in inbound[:limit]:
        result.append(
            RelatedBook(
                title=b["title"],
                author=b["author"],
                category=b["category"],
                subcategory=b["subcategory"],
                slug=b["slug"],
                number=b.get("number", ""),
                reason="links to this book",
            )
        )
    return result


def format_graph_context(book: dict[str, str], books: list[dict[str, str]], max_links: int = 24, rel_map: dict[str, set[str]] | None = None) -> str:
    """Full link context: outgoing links (this book -> others) and incoming
    links (other books -> this book), so the generator sees its place in the
    graph, not just its own edges.
    """
    related = build_related(book, books, max_links=max_links)
    if rel_map is None:
        rel_map = related_map(books, max_links=max_links)
    incoming = build_incoming(book, books, rel_map, limit=12)
    lines = ["Outgoing links (this note must link to these):"]
    if related:
        for entry in related:
            lines.append(f"- {entry.wikilink()} — {entry.author} ({entry.category} > {entry.subcategory}) — {entry.reason}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("Incoming links (these notes link to this one; mention the strongest as validation of the book's role):")
    if incoming:
        for entry in incoming:
            lines.append(f"- {entry.wikilink()} — {entry.author} ({entry.category} > {entry.subcategory})")
    else:
        lines.append("- (none yet)")
    return "\n".join(lines)
