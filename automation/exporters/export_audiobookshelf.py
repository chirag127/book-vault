"""
automation.exporters.export_audiobookshelf
-----------------------------------------
Generates structured Audiobookshelf metadata and folder exports for self-hosted audiobook servers.
"""
from __future__ import annotations

import json
from pathlib import Path
from automation.core.config import ROOT, get_settings


def export_audiobookshelf_metadata(slug: str) -> dict | None:
    """Creates audiobookshelf metadata.json for a book's audio listening edition."""
    chapters_file = ROOT / "audio" / slug / "chapters.json"
    if not chapters_file.exists():
        return None

    meta = json.loads(chapters_file.read_text(encoding="utf-8"))
    
    abs_meta = {
        "title": meta.get("title", slug),
        "author": meta.get("author", "Unknown"),
        "narrator": f"AI Neural Voice ({meta.get('voice', 'default')})",
        "description": f"Universal Book Vault Audio Listening Edition for {meta.get('title', slug)}.",
        "duration": meta.get("total_duration_est_min", 0) * 60,
        "chapters": [
            {
                "id": idx + 1,
                "start": ch.get("start_time_sec", 0),
                "end": ch.get("end_time_sec", 0),
                "title": ch.get("title", f"Chapter {idx + 1}"),
            }
            for idx, ch in enumerate(meta.get("chapters", []))
        ],
    }

    out_file = ROOT / "audio" / slug / "audiobookshelf.json"
    out_file.write_text(json.dumps(abs_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return abs_meta


def main() -> int:
    audio_dir = ROOT / "audio"
    if not audio_dir.exists():
        print("[audiobookshelf] No audio directory found.")
        return 0

    count = 0
    for book_folder in audio_dir.iterdir():
        if book_folder.is_dir():
            res = export_audiobookshelf_metadata(book_folder.name)
            if res:
                count += 1

    print(f"[audiobookshelf] Exported Audiobookshelf metadata for {count} books.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
