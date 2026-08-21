"""Import Kindle, Readwise, or text highlights directly into the book vault notes."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from ..core.config import ROOT
from ..core.manifest import category_folder, load_manifest
from ..core.taxonomy import PILLAR_DIRS


def import_highlights_to_book(slug: str, highlights_text: str) -> Path | None:
    books = load_manifest(ROOT / "automation" / "manifest.csv")
    book = next((b for b in books if b["slug"].lower() == slug.lower()), None)
    if not book:
        print(f"[highlights] Book with slug '{slug}' not found in manifest.", flush=True)
        return None

    pillar_folder = PILLAR_DIRS.get(book["pillar"], book["pillar"])
    cat_folder = category_folder(book["pillar"], book["category"])
    book_dir = ROOT / "md" / pillar_folder / cat_folder / book["slug"]
    
    target_file = book_dir / "README.md"
    if not target_file.exists():
        # Fallback to single file if directory doesn't exist yet
        single_file = ROOT / "md" / pillar_folder / cat_folder / f"{book['slug']}.md"
        if single_file.exists():
            target_file = single_file
        else:
            book_dir.mkdir(parents=True, exist_ok=True)
            target_file = book_dir / "README.md"
            target_file.write_text(f"# {book['title']}\n*By {book['author']}*\n\n", encoding="utf-8")

    content = target_file.read_text(encoding="utf-8")
    
    section_header = "\n\n## 📝 Personal Highlights & Marginalia\n"
    if "## 📝 Personal Highlights & Marginalia" not in content:
        content += section_header

    formatted_highlights = "\n".join(f"> {line.strip()}" for line in highlights_text.strip().splitlines() if line.strip())
    content += f"\n### Imported on {Path(__file__).stem}\n{formatted_highlights}\n"

    target_file.write_text(content, encoding="utf-8")
    print(f"[highlights] Successfully appended highlights to {target_file.relative_to(ROOT)}", flush=True)
    return target_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Import personal highlights into book vault")
    parser.add_argument("--slug", required=True, help="Book slug (e.g. Make-It-Stick)")
    parser.add_argument("--file", help="Path to text file containing highlights")
    parser.add_argument("--text", help="Raw highlight text string")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("Please provide --file or --text with highlight content.")
        return 1

    import_highlights_to_book(args.slug, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
