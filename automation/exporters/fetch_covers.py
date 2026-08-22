from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

import httpx

from ..core.config import ROOT
from ..core.manifest import load_manifest


# Substrings that indicate a derivative commentary rather than the authentic book
DERIVATIVE_PATTERNS = [
    r"\bsummary\s+of\b",
    r"\banalysis\s+of\b",
    r"\bstudy\s+guide\b",
    r"\bworkbook\s+for\b",
    r"\bcliffsnotes\b",
    r"\bquicklet\b",
    r"\binstaread\b",
    r"\bbookrags\b",
    r"\bsparknotes\b",
    r"\bkey\s+takeaways\b",
    r"\bcompanion\s+to\b",  # unless book title starts with Companion
]


def _normalize(s: str) -> str:
    """Normalize string for fuzzy token matching."""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score_candidate(doc: dict[str, Any], target_title: str, target_author: str, target_year: str = "") -> float:
    """Score an Open Library search result candidate to find the true authentic canonical book."""
    score = 0.0

    cand_title = doc.get("title", "")
    cand_title_norm = _normalize(cand_title)
    target_title_norm = _normalize(target_title)

    # 1. Reject or penalize obvious derivative works / summaries
    is_target_companion = "companion" in target_title_norm
    for pat in DERIVATIVE_PATTERNS:
        if re.search(pat, cand_title.lower()):
            if not (is_target_companion and "companion" in pat):
                score -= 150.0

    # 2. Title matching
    if cand_title_norm == target_title_norm:
        score += 80.0
    elif cand_title_norm.startswith(target_title_norm) or target_title_norm.startswith(cand_title_norm):
        score += 50.0
    else:
        # Check token overlap
        target_tokens = set(target_title_norm.split())
        cand_tokens = set(cand_title_norm.split())
        if target_tokens:
            overlap = len(target_tokens & cand_tokens) / len(target_tokens)
            score += overlap * 40.0

    # 3. Author matching
    cand_authors = [_normalize(a) for a in doc.get("author_name", [])]
    target_authors = [_normalize(a.strip()) for a in target_author.split(";") if a.strip()]
    
    author_matched = False
    for ta in target_authors:
        # Check author last name
        last_name = ta.split()[-1] if ta.split() else ta
        for ca in cand_authors:
            if ta in ca or ca in ta:
                score += 50.0
                author_matched = True
                break
            elif last_name and last_name in ca:
                score += 30.0
                author_matched = True
                break
        if author_matched:
            break

    if not author_matched and cand_authors:
        score -= 40.0  # Penalize book with completely different author

    # 4. Cover presence
    if doc.get("cover_i"):
        score += 25.0
    elif doc.get("isbn"):
        score += 10.0

    # 5. Edition count / popularity (favors the canonical main work)
    edition_count = doc.get("edition_count", 1)
    if edition_count > 10:
        score += 15.0
    elif edition_count > 3:
        score += 5.0

    # 6. Publication year match
    cand_year = str(doc.get("first_publish_year", ""))
    if target_year and cand_year and target_year.isdigit() and cand_year.isdigit():
        diff = abs(int(target_year) - int(cand_year))
        if diff == 0:
            score += 10.0
        elif diff <= 2:
            score += 5.0

    return score


def fetch_book_metadata_and_cover(
    title: str,
    author: str,
    published: str = "",
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch verified book metadata, high-res cover, and identifiers with disambiguation."""
    first_author = author.split(";")[0].strip()
    
    should_close = False
    if client is None:
        client = httpx.Client(timeout=10.0)
        should_close = True

    candidates = []

    try:
        # Strategy A: Structured title + author search
        q_title = urllib.parse.quote_plus(title)
        q_auth = urllib.parse.quote_plus(first_author)
        url_a = f"https://openlibrary.org/search.json?title={q_title}&author={q_auth}&limit=5&fields=key,title,author_name,cover_i,isbn,first_publish_year,edition_count,number_of_pages_median,subject"
        resp_a = client.get(url_a)
        if resp_a.status_code == 200:
            candidates.extend(resp_a.json().get("docs", []))

        # Strategy B: General query fallback if no candidates
        if len(candidates) < 2:
            q_all = urllib.parse.quote_plus(f"{title} {first_author}")
            url_b = f"https://openlibrary.org/search.json?q={q_all}&limit=5&fields=key,title,author_name,cover_i,isbn,first_publish_year,edition_count,number_of_pages_median,subject"
            resp_b = client.get(url_b)
            if resp_b.status_code == 200:
                for doc in resp_b.json().get("docs", []):
                    if doc.get("key") not in {c.get("key") for c in candidates}:
                        candidates.append(doc)
    except Exception:
        pass
    finally:
        if should_close:
            client.close()

    # Disambiguation: score candidates
    best_doc = None
    best_score = -999.0

    for doc in candidates:
        sc = score_candidate(doc, title, author, published)
        if sc > best_score:
            best_score = sc
            best_doc = doc

    # Construct metadata result
    result: dict[str, Any] = {
        "title": title,
        "author": author,
        "published": published,
        "cover_url": "",
        "cover_id": None,
        "isbn": "",
        "openlibrary_key": "",
        "pages": None,
        "subjects": [],
        "confidence": "low",
    }

    if best_doc and best_score > 30.0:
        result["confidence"] = "high" if best_score > 80.0 else "medium"
        result["openlibrary_key"] = best_doc.get("key", "")
        
        # Cover resolution
        cover_id = best_doc.get("cover_i")
        if cover_id:
            result["cover_id"] = cover_id
            result["cover_url"] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        
        # ISBN resolution
        isbns = best_doc.get("isbn", [])
        if isbns:
            # Prefer 13-digit ISBN
            isbn_13 = next((i for i in isbns if len(i) == 13 and i.isdigit()), None)
            result["isbn"] = isbn_13 or isbns[0]
            if not result["cover_url"]:
                result["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{result['isbn']}-L.jpg"

        result["pages"] = best_doc.get("number_of_pages_median")
        result["subjects"] = (best_doc.get("subject") or [])[:6]
    else:
        # Fallback direct title link
        short_query = urllib.parse.quote_plus(title)
        result["cover_url"] = f"https://covers.openlibrary.org/b/title/{short_query}-M.jpg?default=false"

    return result


def build_covers_cache(limit: int | None = None) -> dict[str, Any]:
    """Build or update the comprehensive site covers & metadata cache (site/data/covers.json and site/data/book_meta.json)."""
    manifest_path = ROOT / "automation" / "manifest.csv"
    books = load_manifest(manifest_path)
    site_data_dir = ROOT / "site" / "data"
    site_data_dir.mkdir(parents=True, exist_ok=True)

    covers_file = site_data_dir / "covers.json"
    meta_file = site_data_dir / "book_meta.json"

    covers_cache: dict[str, str] = {}
    meta_cache: dict[str, Any] = {}

    if covers_file.exists():
        try:
            covers_cache = json.loads(covers_file.read_text(encoding="utf-8"))
        except Exception:
            covers_cache = {}

    if meta_file.exists():
        try:
            meta_cache = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta_cache = {}

    to_fetch = [b for b in books if b["slug"] not in meta_cache]
    if limit:
        to_fetch = to_fetch[:limit]

    from ..core.colors import bold, cyan, dim, green, magenta, yellow

    print(f"{cyan('[covers]')} {bold(str(len(meta_cache)))} verified book records cached, resolving {yellow(str(len(to_fetch)))} new...")

    with httpx.Client(timeout=12.0) as client:
        for i, b in enumerate(to_fetch, start=1):
            meta = fetch_book_metadata_and_cover(b["title"], b["author"], b.get("published", ""), client)
            meta_cache[b["slug"]] = meta
            covers_cache[b["slug"]] = meta["cover_url"]

            if i % 15 == 0 or i == len(to_fetch):
                conf_color = green if meta["confidence"] == "high" else yellow
                print(f"  {cyan('[covers]')} resolved {bold(f'{i}/{len(to_fetch)}')} books (last: {magenta(b['slug'])} -> confidence {conf_color(meta['confidence'])})", flush=True)
                covers_file.write_text(json.dumps(covers_cache, indent=2, ensure_ascii=False), encoding="utf-8")
                meta_file.write_text(json.dumps(meta_cache, indent=2, ensure_ascii=False), encoding="utf-8")

    covers_file.write_text(json.dumps(covers_cache, indent=2, ensure_ascii=False), encoding="utf-8")
    meta_file.write_text(json.dumps(meta_cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{green('✓ [covers]')} Successfully saved {bold(str(len(meta_cache)))} rich book records to {cyan(str(meta_file.relative_to(ROOT)))}")
    return meta_cache


if __name__ == "__main__":
    build_covers_cache()
