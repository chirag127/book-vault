from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

from ..core.config import ROOT
from ..core.manifest import category_folder, load_manifest
from ..core.recommendations import get_recommendations_for_book
from ..core.taxonomy import PILLAR_DIRS


def _clean_for_search(text: str) -> str:
    """Strip YAML frontmatter, markdown formatting, wikilinks, and fences for clean keyword search."""
    # Strip YAML frontmatter
    text = re.sub(r"^---\s*[\s\S]*?---\s*", "", text)
    # Strip code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Convert wikilinks [[slug|display]] -> display or [[slug]] -> slug
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # Strip markdown headers, bold, italics, links
    text = re.sub(r"[#*_`>~]", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Collapse multiple whitespace
    return re.sub(r"\s+", " ", text).strip()


def build_web_data() -> dict:
    books = load_manifest(ROOT / "automation" / "manifest.csv")
    site_dir = ROOT / "site"
    site_data_dir = site_dir / "data"
    site_data_dir.mkdir(parents=True, exist_ok=True)

    # Load cached cover URLs if available
    covers_file = site_data_dir / "covers.json"
    covers_cache: dict[str, str] = {}
    if covers_file.exists():
        try:
            covers_cache = json.loads(covers_file.read_text(encoding="utf-8"))
        except Exception:
            covers_cache = {}

    catalog = []
    search_index = []
    from ..core.recommendations import precompute_book_tokens
    token_cache = precompute_book_tokens(books)

    for b in books:
        pillar_folder = PILLAR_DIRS.get(b["pillar"], "")
        cat_dir = category_folder(b["pillar"], b["category"])
        book_dir = ROOT / "md" / pillar_folder / cat_dir / b["slug"]
        single_file = ROOT / "md" / pillar_folder / cat_dir / f"{b['slug']}.md"

        is_generated = False
        chapters = []
        has_audio = False
        has_quiz = False
        quiz_content = ""
        full_text_sample = ""

        if book_dir.exists() and book_dir.is_dir():
            is_generated = True
            has_audio = (book_dir / "Audio-Listening-Edition.md").exists()
            has_quiz = (book_dir / "Quiz.md").exists()
            if has_quiz:
                quiz_content = (book_dir / "Quiz.md").read_text(encoding="utf-8")

            for f in sorted(book_dir.glob("*.md")):
                if f.name not in {"Audio-Listening-Edition.md", "Quiz.md"}:
                    content = f.read_text(encoding="utf-8")
                    if f.name == "README.md":
                        full_text_sample = _clean_for_search(content)[:1500]
                    chapters.append({
                        "name": f.name,
                        "title": f.name.replace(".md", "").replace("-", " "),
                        "path": f"md/{pillar_folder}/{cat_dir}/{b['slug']}/{f.name}",
                        "content": content,
                    })
        elif single_file.exists() and single_file.is_file():
            is_generated = True
            content = single_file.read_text(encoding="utf-8")
            full_text_sample = _clean_for_search(content)[:1500]
            chapters.append({
                "name": "README.md",
                "title": "Complete Summary",
                "path": f"md/{pillar_folder}/{cat_dir}/{b['slug']}.md",
                "content": content,
            })

        audio_content = ""
        if book_dir.exists() and (book_dir / "Audio-Listening-Edition.md").exists():
            audio_content = (book_dir / "Audio-Listening-Edition.md").read_text(encoding="utf-8")

        recs = [
            {"title": r["title"], "slug": r["slug"], "author": r["author"], "pillar": r["pillar"]}
            for r in get_recommendations_for_book(b["slug"], books, limit=3, token_cache=token_cache)
        ]

        # Search query uses strictly the book title
        title_query = urllib.parse.quote_plus(b["title"])

        external_trackers = {
            "openlibrary": f"https://openlibrary.org/search?q={title_query}",
            "goodreads": f"https://www.goodreads.com/search?q={title_query}",
            "google_books": f"https://www.google.com/search?tbm=bks&q={title_query}",
            "worldcat": f"https://search.worldcat.org/search?q={title_query}",
            "hardcover": f"https://hardcover.app/search?q={title_query}",
            "storygraph": f"https://app.thestorygraph.com/browse?search_term={title_query}",
        }

        # Cover URL
        cover_url = covers_cache.get(
            b["slug"],
            f"https://covers.openlibrary.org/b/title/{urllib.parse.quote_plus(b['title'])}-M.jpg?default=false"
        )

        item = {
            "number": b.get("number", "000"),
            "id": b.get("id", b.get("number", "000")),
            "title": b["title"],
            "author": b["author"],
            "first_published": b.get("first_published", b.get("published", "")),
            "latest_published": b.get("latest_published", b.get("published", "")),
            "published": b.get("published", b.get("first_published", "")),
            "pillar": b["pillar"],
            "domain": b.get("domain", b["pillar"]),
            "pillar_folder": pillar_folder,
            "category": b["category"],
            "subcategory": b.get("subcategory", ""),
            "topic": b.get("topic", ""),
            "slug": b["slug"],
            "difficulty": b.get("difficulty", "Introductory"),
            "priority": b.get("priority", "P0"),
            "type": b.get("type", "nonfiction"),
            "reading_mode": b.get("reading_mode", "summary"),
            "summary_depth": b.get("summary_depth", "detailed"),
            "book_type": b.get("book_type", "Core Text"),
            "status": "Generated" if is_generated else "Pending",
            "cover_url": cover_url,
            "has_audio": has_audio,
            "audio_content": audio_content,
            "has_quiz": has_quiz,
            "quiz_content": quiz_content,
            "chapters": chapters,
            "recommendations": recs,
            "external_trackers": external_trackers,
        }
        catalog.append(item)

        # Lightweight search index record
        search_index.append({
            "slug": b["slug"],
            "title": b["title"],
            "author": b["author"],
            "first_published": b.get("first_published", b.get("published", "")),
            "latest_published": b.get("latest_published", b.get("published", "")),
            "pillar": b["pillar"],
            "category": b["category"],
            "subcategory": b.get("subcategory", ""),
            "topic": b.get("topic", ""),
            "difficulty": b.get("difficulty", "Introductory"),
            "status": "Generated" if is_generated else "Pending",
            "cover_url": cover_url,
            "search_text": f"{b['title']} {b['author']} {b['pillar']} {b['category']} {b.get('subcategory', '')} {b.get('topic', '')} {full_text_sample}".lower(),
        })

    data = {
        "pillars": PILLAR_DIRS,
        "total_books": len(catalog),
        "generated_books": len([b for b in catalog if b["status"] == "Generated"]),
        "books": catalog,
    }

    out_json = site_data_dir / "vault_data.json"
    out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    out_js = site_data_dir / "vault_data.js"
    out_js.write_text("window.VAULT_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")

    out_search = site_data_dir / "search_index.json"
    out_search.write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")

    from ..core.colors import bold, cyan, green, yellow
    print(f"{green('✓ [site]')} Exported {bold(str(len(catalog)))} books to {cyan(str(out_json.relative_to(ROOT)))} and {cyan(str(out_js.relative_to(ROOT)))} ({green(str(data['generated_books']))} generated, {yellow(str(len(catalog) - data['generated_books']))} pending)")
    return data


if __name__ == "__main__":
    build_web_data()
