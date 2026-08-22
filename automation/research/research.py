"""Research aggregator: multi-backend search with deduplication and caching."""
from __future__ import annotations

import concurrent.futures
import json
import re
import string
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ..core.config import ROOT, Settings

RESEARCH_CACHE_DIR = ROOT / "automation" / "research"


@dataclass
class Source:
    title: str
    url: str
    query: str
    content: str


def _domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _domain_priority(url: str) -> int:
    dom = _domain(url)
    if dom.endswith(".edu") or dom.endswith(".gov"):
        return 0
    publisher_domains = {
        "penguinrandomhouse.com",
        "harpercollins.com",
        "simonandschuster.com",
        "macmillan.com",
        "hachettebookgroup.com",
        "wiley.com",
        "routledge.com",
        "cambridge.org",
        "oup.com",
        "harvard.edu",
        "mit.edu",
    }
    if any(dom.endswith(p) for p in publisher_domains):
        return 0
    if "wikipedia.org" in dom or "openlibrary.org" in dom or "crossref.org" in dom:
        return 1
    if "amazon.com" in dom or "goodreads.com" in dom:
        return 3
    return 2


def _norm_title(title: str) -> str:
    cleaned = title.lower()
    noise = ["the", "a", "an", "official", "summary", "review", "book", "guide", "pdf", "edition"]
    for char in string.punctuation + "—–-":
        cleaned = cleaned.replace(char, " ")
    words = [w for w in cleaned.split() if w not in noise]
    return " ".join(words)


def _near_duplicate(title: str, seen: list[str], min_words: int = 4) -> bool:
    raw_a = " ".join(title.lower().split())
    norm = _norm_title(title)
    if not norm and not raw_a:
        return False
    norm_words = norm.split()
    for s in seen:
        raw_b = " ".join(s.lower().split())
        s_words = _norm_title(s).split()
        if raw_a == raw_b or (norm and norm == _norm_title(s)):
            return True
        if len(raw_a.split()) >= min_words and (raw_b.startswith(raw_a) or raw_a.startswith(raw_b)):
            return True
        if norm_words and s_words:
            if len(norm_words) >= min_words or len(s_words) >= min_words:
                short, long_ = (norm, _norm_title(s)) if len(norm) < len(_norm_title(s)) else (_norm_title(s), norm)
                if long_.startswith(short) or short in long_:
                    return True
            if norm_words == s_words[:len(norm_words)] or s_words == norm_words[:len(s_words)]:
                return True
    return False


def _dedupe_sources(items: list[dict[str, Any]], max_sources: int = 10) -> list[dict[str, Any]]:
    sorted_items = sorted(items, key=lambda x: _domain_priority(x.get("url", "")))
    unique: list[dict[str, Any]] = []
    seen_titles: list[str] = []
    domain_counts: dict[str, int] = {}

    for item in sorted_items:
        title = item.get("title", "")
        url = item.get("url", "")
        dom = _domain(url)
        if domain_counts.get(dom, 0) >= 2:
            continue
        norm = _norm_title(title)
        if _near_duplicate(norm, seen_titles):
            continue
        seen_titles.append(norm)
        domain_counts[dom] = domain_counts.get(dom, 0) + 1
        unique.append(item)
        if len(unique) >= max_sources:
            break

    return unique


def source_bundle(sources: list[Source]) -> str:
    if not sources:
        return "No web sources available."
    blocks = []
    for i, s in enumerate(sources, 1):
        source_type = "VIDEO TRANSCRIPT" if "youtube.com" in s.url.lower() else "WEB RESEARCH"
        blocks.append(
            f"=== VERIFIED RESEARCH DOSSIER {i}: {s.title} ({source_type}) ===\n"
            f"URL: {s.url}\n"
            f"Query: {s.query}\n"
            f"Content:\n{s.content}\n"
        )
    return "\n\n".join(blocks)


def save_research(path_or_slug: Path | str, sources: list[Source], book: dict[str, Any] | None = None) -> None:
    p = Path(path_or_slug)
    if not p.suffix:
        p = RESEARCH_CACHE_DIR / f"{path_or_slug}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": (book or {}).get("slug", p.stem),
        "researched_at": datetime.now(timezone.utc).isoformat(),
        "book": book or {},
        "sources": [asdict(s) for s in sources],
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_research(slug_or_path: str | Path, max_age_hours: float = 72.0) -> list[Source] | None:
    p = Path(slug_or_path)
    if not p.suffix:
        p = RESEARCH_CACHE_DIR / f"{slug_or_path}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        researched_at = datetime.fromisoformat(data["researched_at"])
        age_hours = (datetime.now(timezone.utc) - researched_at).total_seconds() / 3600.0
        if age_hours > max_age_hours:
            return None
        return [Source(**s) for s in data.get("sources", [])]
    except Exception:
        return None


def search_book(book: dict[str, str], settings: Settings) -> list[Source]:
    title = book.get("title", "")
    author = book.get("author", "")
    queries = [
        f"{title} {author} summary concepts framework",
        f"{title} {author} key ideas chapter summary",
    ]

    results: list[dict[str, str]] = []

    # DDGS search
    if settings.use_ddgs:
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                for q in queries:
                    for r in ddgs.text(q, max_results=5):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "query": q,
                            "content": r.get("body", ""),
                        })
        except Exception:
            pass

    # OpenLibrary search
    if settings.use_openlibrary and len(results) < 5:
        try:
            q_enc = urllib.parse.quote_plus(f"{title} {author}")
            url = f"https://openlibrary.org/search.json?q={q_enc}&limit=3"
            resp = httpx.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                for doc in data.get("docs", [])[:3]:
                    doc_title = doc.get("title", title)
                    doc_author = ", ".join(doc.get("author_name", [author]))
                    first_sentence = " ".join(doc.get("first_sentence", []))
                    subjects = ", ".join(doc.get("subject", [])[:10])
                    body = f"OpenLibrary record for {doc_title} by {doc_author}. Subjects: {subjects}. {first_sentence}"
                    results.append({
                        "title": f"OpenLibrary: {doc_title}",
                        "url": f"https://openlibrary.org{doc.get('key', '')}",
                        "query": title,
                        "content": body,
                    })
        except Exception:
            pass

    # Wikipedia search
    if settings.use_wikipedia and len(results) < 8:
        try:
            q_enc = urllib.parse.quote_plus(title)
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={q_enc}&format=json"
            resp = httpx.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("query", {}).get("search", [])[:2]:
                    wiki_title = item.get("title", "")
                    snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(wiki_title.replace(' ', '_'))}"
                    results.append({
                        "title": f"Wikipedia: {wiki_title}",
                        "url": page_url,
                        "query": title,
                        "content": snippet,
                    })
        except Exception:
            pass

    deduped = _dedupe_sources(results, max_sources=10)
    return [
        Source(
            title=d.get("title", "Untitled Source"),
            url=d.get("url", ""),
            query=d.get("query", title),
            content=d.get("content", ""),
        )
        for d in deduped
    ]
