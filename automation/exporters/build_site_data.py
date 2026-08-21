from __future__ import annotations

import json
from pathlib import Path

from ..core.config import ROOT
from ..core.manifest import category_folder, load_manifest
from ..core.recommendations import get_recommendations_for_book
from ..core.taxonomy import PILLAR_DIRS




def build_web_data() -> dict:
    books = load_manifest(ROOT / "automation" / "manifest.csv")
    site_dir = ROOT / "site"
    site_data_dir = site_dir / "data"
    site_data_dir.mkdir(parents=True, exist_ok=True)

    catalog = []
    for b in books:
        pillar_folder = PILLAR_DIRS.get(b["pillar"], "")
        cat_dir = category_folder(b["pillar"], b["category"])
        book_dir = ROOT / "md" / pillar_folder / cat_dir / b["slug"]
        single_file = ROOT / "md" / pillar_folder / cat_dir / f"{b['slug']}.md"

        # Check status
        is_generated = False
        chapters = []
        has_audio = False

        if book_dir.exists() and book_dir.is_dir():
            is_generated = True
            has_audio = (book_dir / "Audio-Listening-Edition.md").exists()
            for f in sorted(book_dir.glob("*.md")):
                if f.name != "Audio-Listening-Edition.md":
                    chapters.append({
                        "name": f.name,
                        "title": f.name.replace(".md", "").replace("-", " "),
                        "path": f"md/{pillar_folder}/{cat_dir}/{b['slug']}/{f.name}",
                        "content": f.read_text(encoding="utf-8"),
                    })
        elif single_file.exists() and single_file.is_file():
            is_generated = True
            chapters.append({
                "name": "README.md",
                "title": "Complete Summary",
                "path": f"md/{pillar_folder}/{cat_dir}/{b['slug']}.md",
                "content": single_file.read_text(encoding="utf-8"),
            })

        audio_content = ""
        if book_dir.exists() and (book_dir / "Audio-Listening-Edition.md").exists():
            audio_content = (book_dir / "Audio-Listening-Edition.md").read_text(encoding="utf-8")

        recs = [
            {"title": r["title"], "slug": r["slug"], "author": r["author"], "pillar": r["pillar"]}
            for r in get_recommendations_for_book(b["slug"], books, limit=3)
        ]


        catalog.append({
            "number": b.get("number", "000"),
            "title": b["title"],
            "author": b["author"],
            "published": b["published"],
            "pillar": b["pillar"],
            "pillar_folder": pillar_folder,
            "category": b["category"],
            "subcategory": b.get("subcategory", ""),
            "slug": b["slug"],
            "difficulty": b.get("difficulty", "Introductory"),
            "book_type": b.get("book_type", "Core Text"),
            "status": "Generated" if is_generated else "Pending",
            "has_audio": has_audio,
            "audio_content": audio_content,
            "chapters": chapters,
            "recommendations": recs,
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

    print(f"[site] Exported {len(catalog)} books to {out_json.relative_to(ROOT)} and {out_js.relative_to(ROOT)} ({data['generated_books']} generated)")
    return data



if __name__ == "__main__":
    build_web_data()
