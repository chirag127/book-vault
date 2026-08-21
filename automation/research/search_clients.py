from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from ..core.config import ROOT


SEARCH_CACHE_DIR = ROOT / "cache" / "search"



def _cache_path(backend: str, query: str) -> Path:
    import re
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{backend}_{query}")[:120]
    return SEARCH_CACHE_DIR / f"{clean}.json"


def _load_cached(backend: str, query: str, ttl_hours: float = 48.0) -> list[dict[str, Any]] | None:
    path = _cache_path(backend, query)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        saved_at = data.get("saved_at", 0)
        if time.time() - saved_at > ttl_hours * 3600:
            return None
        return data.get("results", [])
    except Exception:
        return None


def _save_cached(backend: str, query: str, results: list[dict[str, Any]]) -> None:
    try:
        SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(backend, query)
        payload = {
            "backend": backend,
            "query": query,
            "saved_at": time.time(),
            "results": results,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass


def ddgs_search(query: str, max_results: int = 5, retries: int = 5) -> list[dict[str, str]]:
    """Search DuckDuckGo keylessly with exponential backoff retries and disk caching."""
    cached = _load_cached("ddgs", query)
    if cached is not None:
        return cached

    results: list[dict[str, str]] = []
    last_err: Exception | None = None

    # Try duckduckgo_search / ddgs package first
    for attempt in range(retries + 1):
        try:
            from duckduckgo_search import DDGS  # type: ignore
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=max_results)
                for item in ddg_gen or []:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("href", item.get("link", "")),
                        "snippet": item.get("body", item.get("snippet", "")),
                        "source": "ddgs",
                    })
                if results:
                    _save_cached("ddgs", query, results)
                    return results
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(1.5 * (2**attempt))
            continue

    # Fallback to stdlib HTML scrape if package fails
    try:
        from .research import _ddg_stdlib
        stdlib_res = _ddg_stdlib(query, max_results=max_results)
        if stdlib_res:
            res_dicts = [{"title": r.title, "url": r.url, "snippet": r.snippet, "source": "ddgs_html"} for r in stdlib_res]
            _save_cached("ddgs", query, res_dicts)
            return res_dicts
    except Exception:
        pass

    return results


def openlibrary_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Query OpenLibrary keyless search API for book bibliographic metadata and subjects."""
    cached = _load_cached("openlibrary", query)
    if cached is not None:
        return cached

    results: list[dict[str, str]] = []
    url = f"https://openlibrary.org/search.json?q={quote_plus(query)}&limit={max_results}"
    req = Request(url, headers={"User-Agent": "BookVault/2.0 (open-knowledge; contact@example.com)"})
    try:
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for doc in data.get("docs", [])[:max_results]:
                title = doc.get("title", "")
                authors = ", ".join(doc.get("author_name", []))
                first_year = doc.get("first_publish_year", "")
                subjects = ", ".join(doc.get("subject", [])[:8])
                key = doc.get("key", "")
                full_url = f"https://openlibrary.org{key}" if key else ""
                snippet = f"Author(s): {authors}. Published: {first_year}. Key topics: {subjects}."
                results.append({
                    "title": f"{title} (OpenLibrary)",
                    "url": full_url,
                    "snippet": snippet.strip(),
                    "source": "openlibrary",
                })
        if results:
            _save_cached("openlibrary", query, results)
    except Exception:
        pass

    return results


def crossref_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Query Crossref API for scholarly citations, DOIs, and academic abstracts."""
    cached = _load_cached("crossref", query)
    if cached is not None:
        return cached

    results: list[dict[str, str]] = []
    url = f"https://api.crossref.org/works?query={quote_plus(query)}&rows={max_results}"
    req = Request(url, headers={"User-Agent": "BookVault/2.0 (mailto:vault@example.com)"})
    try:
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("message", {}).get("items", [])
            for item in items[:max_results]:
                titles = item.get("title", [])
                title = titles[0] if titles else "Untitled Work"
                doi = item.get("DOI", "")
                full_url = item.get("URL", f"https://doi.org/{doi}" if doi else "")
                container = item.get("container-title", [""])[0] if item.get("container-title") else ""
                year = item.get("published", {}).get("date-parts", [[None]])[0][0] or ""
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])[:3])
                snippet = f"Scholarly Citation: {authors} ({year}). {container}. DOI: {doi}."
                results.append({
                    "title": f"{title} (Crossref)",
                    "url": full_url,
                    "snippet": snippet.strip(),
                    "source": "crossref",
                })
        if results:
            _save_cached("crossref", query, results)
    except Exception:
        pass

    return results


def wikipedia_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """Query Wikipedia keyless API for encyclopedia summaries of books and authors."""
    cached = _load_cached("wikipedia", query)
    if cached is not None:
        return cached

    results: list[dict[str, str]] = []
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit={max_results}&namespace=0&format=json"
    req = Request(url, headers={"User-Agent": "BookVault/2.0 (mailto:vault@example.com)"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if len(data) >= 4:
                titles = data[1]
                descriptions = data[2]
                urls = data[3]
                for t, desc, u in zip(titles, descriptions, urls):
                    if t and desc:
                        results.append({
                            "title": f"{t} (Wikipedia)",
                            "url": u,
                            "snippet": desc,
                            "source": "wikipedia",
                        })
        if results:
            _save_cached("wikipedia", query, results)
    except Exception:
        pass

    return results
