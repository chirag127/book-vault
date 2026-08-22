"""Free, robust search clients for Book Vault research pipeline with diskcache TTL."""
from __future__ import annotations

import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from ..core.config import ROOT

SEARCH_CACHE_DIR = ROOT / "automation" / "cache" / "search"


def _cache_key(backend: str, query: str) -> Path:
    safe_backend = re.sub(r"[^\w-]", "_", backend.lower())
    safe_q = re.sub(r"[^\w-]", "_", query.lower())[:80]
    return SEARCH_CACHE_DIR / safe_backend / f"{safe_q}.json"


def _load_cached(backend: str, query: str, ttl_hours: float = 72.0) -> list[dict[str, Any]] | None:
    path = _cache_key(backend, query)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"])
        age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600.0
        if age_hours > ttl_hours:
            return None
        return data.get("results", [])
    except Exception:
        return None


def _save_cached(backend: str, query: str, results: list[dict[str, Any]]) -> None:
    path = _cache_key(backend, query)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "backend": backend,
        "query": query,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def ddgs_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    cached = _load_cached("ddgs", query)
    if cached is not None:
        return cached
    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "query": query,
                    "content": r.get("body", ""),
                })
    except Exception:
        pass
    _save_cached("ddgs", query, results)
    return results


def openlibrary_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    cached = _load_cached("openlibrary", query)
    if cached is not None:
        return cached
    results = []
    try:
        q_enc = urllib.parse.quote_plus(query)
        url = f"https://openlibrary.org/search.json?q={q_enc}&limit={max_results}"
        req = Request(url, headers={"User-Agent": "BookVault/1.0 (knowledge-management)"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for doc in data.get("docs", [])[:max_results]:
                title = doc.get("title", "Unknown Title")
                authors = ", ".join(doc.get("author_name", ["Unknown"]))
                year = doc.get("first_publish_year", "N/A")
                subjects = ", ".join(doc.get("subject", [])[:10])
                first_sentence = doc.get("first_sentence", "")
                if isinstance(first_sentence, list):
                    first_sentence = " ".join(first_sentence)
                key = doc.get("key", "")
                body = f"OpenLibrary Record: {title} by {authors} ({year}). Subjects: {subjects}. {first_sentence}".strip()
                results.append({
                    "title": f"OpenLibrary: {title} by {authors}",
                    "url": f"https://openlibrary.org{key}",
                    "query": query,
                    "content": body,
                })
    except Exception:
        pass
    _save_cached("openlibrary", query, results)
    return results


def crossref_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    cached = _load_cached("crossref", query)
    if cached is not None:
        return cached
    results = []
    try:
        q_enc = urllib.parse.quote_plus(query)
        url = f"https://api.crossref.org/works?query={q_enc}&rows={max_results}"
        req = Request(url, headers={"User-Agent": "BookVault/1.0 (mailto:admin@example.com)"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("message", {}).get("items", [])
            for item in items[:max_results]:
                titles = item.get("title", [])
                title = titles[0] if titles else "Untitled Work"
                authors_list = []
                for a in item.get("author", []):
                    name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                    if name:
                        authors_list.append(name)
                author_str = ", ".join(authors_list) or "Unknown Author"
                doi = item.get("DOI", "")
                link = item.get("URL", f"https://doi.org/{doi}")
                results.append({
                    "title": f"Crossref: {title}",
                    "url": link,
                    "query": query,
                    "content": f"Academic Article: {title} by {author_str}. DOI: {doi}",
                })
    except Exception:
        pass
    _save_cached("crossref", query, results)
    return results


def wikipedia_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    cached = _load_cached("wikipedia", query)
    if cached is not None:
        return cached
    results = []
    try:
        q_enc = urllib.parse.quote_plus(query)
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={q_enc}&limit={max_results}&namespace=0&format=json"
        req = Request(url, headers={"User-Agent": "BookVault/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if len(data) >= 4:
                titles = data[1]
                descriptions = data[2]
                links = data[3]
                for title, desc, link in zip(titles, descriptions, links):
                    results.append({
                        "title": f"Wikipedia: {title}",
                        "url": link,
                        "query": query,
                        "content": desc,
                    })
    except Exception:
        pass
    _save_cached("wikipedia", query, results)
    return results
