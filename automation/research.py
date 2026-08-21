from __future__ import annotations

import html
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings


class ResearchError(RuntimeError):
    """Raised when required source research fails."""


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    query: str
    content: str


def _clean_text(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _dokobot_search(query: str) -> list[dict[str, str]]:
    search_url = "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})
    result = subprocess.run(
        ["dokobot", "read", "--local", search_url],
        capture_output=True,
        text=True,
        timeout=90,
        check=True,
    )
    text = result.stdout or result.stderr
    urls = []
    for url in re.findall(r"https?://[^\s)<>\"']+", text):
        url = url.rstrip(".,;")
        if "google.com/search" not in url and url not in urls:
            urls.append(url)
    return [{"title": url, "url": url, "content": text[:3000]} for url in urls[:8]]


def _yacy_search(query: str, settings: Settings) -> list[dict[str, str]]:
    """Search a local YaCy peer (https://github.com/yacy/yacy_search_server).

    YaCy exposes an OpenAI-independent REST JSON API on port 8090 by default.
    The peer must already be running; the caller falls through to other
    backends when the connection fails.
    """
    url = settings.yacy_url + "/yacysearch.json?" + urllib.parse.urlencode(
        {"query": query, "maximumRecords": 8, "resource": "global", "nav": "http"}
    )
    request = urllib.request.Request(url, headers={"User-Agent": "UniversalBookVaultResearch/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    items = []
    for channel in data.get("channels", []):
        for item in channel.get("items", []):
            items.append(
                {
                    "title": str(item.get("title", "")),
                    "url": str(item.get("link", "")),
                    "content": str(item.get("description", "")),
                }
            )
    return [item for item in items if item.get("url")]


def _ddgs_search(query: str) -> list[dict[str, str]]:
    """DuckDuckGo search with one retry; never raises.

    Transient rate limiting and bot detection are common on free search
    endpoints, so failures are converted into empty results and the caller
    falls through to the next backend.
    """
    try:
        from ddgs import DDGS  # type: ignore
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except ImportError:
            return []
    results: list[dict[str, str]] = []
    for attempt in range(3):
        try:
            search = DDGS()
            for item in search.text(
                query,
                region="us-en",
                safesearch="moderate",
                max_results=8,
                backend="auto",
            ):
                results.append(
                    {
                        "title": str(item.get("title", "")),
                        "url": str(item.get("href") or item.get("url") or ""),
                        "content": str(item.get("body", "")),
                    }
                )
            return [item for item in results if item["url"]]
        except Exception:
            if attempt < 2:  # exponential backoff: 3s, then 6s
                time.sleep(3 * (2**attempt))
            continue
    return []


def _stdlib_search(query: str) -> list[dict[str, str]]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "UniversalBookVaultResearch/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                page = response.read().decode("utf-8", errors="replace")
            results = []
            for href, title in re.findall(r'result__a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', page, flags=re.I):
                results.append({"title": _clean_text(title), "url": html.unescape(href), "content": ""})
            return results[:8]
        except (OSError, urllib.error.URLError, ValueError):
            if attempt < 2:  # exponential backoff: 2s, 4s
                time.sleep(2 * (2**attempt))
            continue
    return []


def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().lstrip("www.")
    except ValueError:
        return (url or "").lower()


def _domain_priority(url: str) -> int:
    """Lower is better. Official publishers, universities, and governments rank
    above wikis and aggregators; Amazon/Goodreads rank last."""
    domain = _domain(url)
    if domain.endswith(".edu") or domain.endswith(".gov"):
        return 0
    publishers = (
        "penguinrandomhouse", "hup.harvard", "oup.com", "cambridge.org", "mitpress",
        "springer", "wiley.com", "simonandschuster", "macmillan", "harpercollins",
        "wwnorton", "profilebooks", "farrar", "knopfdoubleday", "yalebooks",
    )
    if any(p in domain for p in publishers):
        return 0
    if domain in ("wikipedia.org", "britannica.com") or domain.endswith(".org"):
        return 1
    if "amazon" in domain or "goodreads" in domain:
        return 3
    return 2


def _norm_title(title: str) -> str:
    """Normalize a source title for near-duplicate comparison.

    Lowercases, strips separators and punctuation, drops generic noise words,
    and keeps only the significant words so truncated or lightly reworded
    listings of the same page compare equal.
    """
    text = html.unescape(re.sub(r"<[^>]+>", " ", title or "")).lower()
    text = re.sub(r"[|:\u2014\u2013\u2013-]", " ", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    noise = {
        "the", "a", "an", "and", "of", "for", "book", "books", "homepage",
        "official", "author", "authors", "site", "review", "summary", "pdf",
        "free", "download", "amazon", "goodreads", "wikipedia", "publisher",
        "co", "uk", "com", "net", "org", "google", "blog", "interview",
        "press", "edition", "kindle", "audible", "paperback", "hardcover",
    }
    return " ".join(word for word in text.split() if word not in noise)


def _near_duplicate(norm: str, kept: list[str], min_words: int = 4) -> bool:
    """True when one normalized title is a word-prefix of another.

    A listing cut off at '...' (e.g. "How to Take Smart Notes: One Simple
    Technique to Boost Writing") is a word-prefix of the full listing, so it
    collapses. A short listing with an added brand segment ("... | MIT Press")
    is NOT a word-prefix of the full subtitle, so distinct publisher and
    author pages survive.
    """
    for candidate in kept:
        norm_words = norm.split()
        candidate_words = candidate.split()
        short, long = (
            (norm_words, candidate_words)
            if len(norm_words) <= len(candidate_words)
            else (candidate_words, norm_words)
        )
        if len(short) >= min_words and long[: len(short)] == short:
            return True
    return False


def _dedupe_sources(items: list[dict[str, str]], max_sources: int = 8) -> list[dict[str, str]]:
    """Collapse near-duplicate search hits.

    Rules: prefer higher-priority domains first; at most two hits per domain;
    drop titles that are near-duplicates of an already-kept title; cap the
    final bundle so the model sees distinct, high-value sources.
    """
    ranked = sorted(items, key=lambda item: (_domain_priority(item.get("url", "")), item.get("url", "")))
    kept: list[dict[str, str]] = []
    kept_titles: list[str] = []
    domain_count: dict[str, int] = {}
    for item in ranked:
        domain = _domain(item.get("url", ""))
        if domain_count.get(domain, 0) >= 2:
            continue
        norm = _norm_title(item.get("title", "")) or _norm_title(item.get("url", ""))
        if _near_duplicate(norm, kept_titles):
            continue
        kept.append(item)
        kept_titles.append(norm)
        domain_count[domain] = domain_count.get(domain, 0) + 1
        if len(kept) >= max_sources:
            break
    return kept


def _fetch_page(url: str) -> str:
    """Fetch one source page with exponential backoff on transient errors."""
    for attempt in range(3):
        try:
            from ddgs import DDGS  # type: ignore

            extracted = DDGS().extract(url, fmt="text_plain")
            content = str(extracted.get("content", "")).strip()
            if content:
                return content[:7000]
        except Exception:
            pass
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "UniversalBookVaultResearch/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return _clean_text(response.read().decode("utf-8", errors="replace"))[:7000]
        except (OSError, urllib.error.URLError, ValueError):
            if attempt < 2:  # exponential backoff: 2s, 4s
                time.sleep(2 * (2**attempt))
            continue
    return ""


def _search(query: str, settings: Settings) -> list[dict[str, str]]:
    if settings.use_yacy:
        try:
            found = _yacy_search(query, settings)
            if found:
                print(f"        SEARCH (yacy): {len(found)} hits for '{query[:80]}'", flush=True)
                return found
        except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
            pass
    if settings.use_dokobot:
        try:
            found = _dokobot_search(query)
            if found:
                print(f"        SEARCH (dokobot): {len(found)} hits for '{query[:80]}'", flush=True)
                return found
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        found = _ddgs_search(query)
    except Exception:
        found = []
    if found:
        print(f"        SEARCH (ddgs): {len(found)} hits for '{query[:80]}'", flush=True)
        return found
    found = _stdlib_search(query)
    print(f"        SEARCH (stdlib ddg): {len(found)} hits for '{query[:80]}'", flush=True)
    return found


def search_book(book: dict[str, str], settings: Settings) -> list[Source]:
    title = book["title"]
    author = book["author"]
    queries = [
        f'"{title}" "{author}" key ideas concepts framework summary',
        f'"{title}" "{author}" official publisher author interview talk',
        f'"{title}" "{author}" research criticism limitations analysis',
        f'"{title}" "{author}" practical applications core takeaways',
    ]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    found: dict[str, dict[str, str]] = {}

    def _run_one_search(q: str):
        return q, _search(q, settings)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_one_search, q) for q in queries]
        for future in as_completed(futures):
            try:
                q, results = future.result()
                for result in results:
                    if result.get("url") and result["url"] not in found:
                        found[result["url"]] = {**result, "query": q}
            except Exception:
                pass

    if not found:
        # Fallback to direct title search
        fallback_results = _search(f"{title} {author} book summary", settings)
        for r in fallback_results:
            if r.get("url"):
                found[r["url"]] = {**r, "query": title}

    if not found:
        raise ResearchError(f"No sources found for {book['title']}.")

    candidates = _dedupe_sources(list(found.values()), max_sources=8)

    def _fetch_one_source(item: dict[str, str]) -> Source:
        content = item.get("snippet", item.get("content", ""))
        if not content or len(content) < 200:
            try:
                fetched = _fetch_page(item["url"])
                if fetched:
                    content = fetched
            except Exception:
                pass
        return Source(item.get("title", item["url"]), item["url"], item.get("query", ""), content)

    sources: list[Source] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        source_futures = [executor.submit(_fetch_one_source, item) for item in candidates]
        for future in as_completed(source_futures):
            try:
                sources.append(future.result())
            except Exception:
                pass

    return sources if sources else [Source(title, "", "fallback", "Book summary context.")]



def save_research(path: Path, book: dict[str, str], sources: list[Source]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "researched_at": datetime.now(timezone.utc).isoformat(),
        "book": book,
        "sources": [asdict(source) for source in sources],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_bundle(sources: list[Source]) -> str:
    return "\n\n".join(
        f"SOURCE {index}\nTitle: {source.title}\nURL: {source.url}\nQuery: {source.query}\nContent:\n{source.content}"
        for index, source in enumerate(sources, 1)
    )
