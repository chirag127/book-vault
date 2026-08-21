from __future__ import annotations

import argparse
import re
from pathlib import Path

from ..core.config import ROOT
from ..core.manifest import load_manifest



def bundle_book_ebook(slug: str, output_dir: Path | None = None) -> Path | None:
    """Bundle all modular chapters of a book into a single publication-ready markdown document."""
    matches = list(ROOT.glob(f"md/*/*/{slug}"))
    if not matches:
        print(f"[ebook] Book folder '{slug}' not found.")
        return None

    book_dir = matches[0]
    out_dir = output_dir or (ROOT / "ebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}-Complete-Edition.md"

    md_files = sorted([f for f in book_dir.glob("*.md") if f.name != "Audio-Listening-Edition.md"])
    if not md_files:
        print(f"[ebook] No chapters found in {book_dir.relative_to(ROOT)}.")
        return None

    compiled_text = []
    for f in md_files:
        content = f.read_text(encoding="utf-8").strip()
        # Clean internal front matter on non-README files
        if f.name != "README.md":
            content = re.sub(r"^---[\s\S]*?---\n", "", content)
        compiled_text.append(content)

    final_content = "\n\n---\n\n".join(compiled_text) + "\n"
    out_file.write_text(final_content, encoding="utf-8")
    print(f"[ebook] Compiled {len(md_files)} chapters -> {out_file.relative_to(ROOT)}")
    return out_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Export modular book summaries into bundled publication-ready documents.")
    parser.add_argument("--slug", required=True, help="Book slug to export.")
    parser.add_argument("--out", help="Output directory.")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else None
    bundle_book_ebook(args.slug, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
