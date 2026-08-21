from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from .config import ROOT
from .taxonomy import TAXONOMY, get_target_path, find_subcategory

MD_ROOT = ROOT / "md"


def migrate_notes() -> None:
    """Migrate all notes in md/ to the standardized 3-level taxonomy hierarchy."""
    print("Starting vault taxonomy migration to 3-level hierarchy...", flush=True)

    # 1. Locate all book notes (excluding README.md)
    book_files = [f for f in MD_ROOT.rglob("*.md") if f.name.lower() != "readme.md"]
    print(f"Found {len(book_files)} book note(s) to migrate.", flush=True)

    for file_path in book_files:
        slug = file_path.stem
        # Map Make-It-Stick or others to proper subcategory
        # Default mapping for Make-It-Stick -> 01-01-01
        if slug == "Make-It-Stick":
            p, c, s = find_subcategory("01-01-01")
            new_rel_path = get_target_path(p, c, s, slug)
        else:
            p, c, s = find_subcategory("01-01-01")
            new_rel_path = get_target_path(p, c, s, slug)

        new_abs_path = ROOT / new_rel_path
        new_abs_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.resolve() != new_abs_path.resolve():
            print(f"  Migrating {file_path.name} -> {new_rel_path}", flush=True)
            content = file_path.read_text(encoding="utf-8")
            new_abs_path.write_text(content, encoding="utf-8")
            try:
                file_path.unlink()
            except Exception:
                pass

    # 2. Clean up empty old category directories
    for p in sorted(MD_ROOT.glob("*"), reverse=True):
        if p.is_dir():
            for sub in sorted(p.glob("*"), reverse=True):
                if sub.is_dir():
                    readme = sub / "README.md"
                    if readme.exists():
                        readme.unlink(missing_ok=True)
                    try:
                        sub.rmdir()
                    except OSError:
                        pass
            readme = p / "README.md"
            if readme.exists():
                readme.unlink(missing_ok=True)
            try:
                p.rmdir()
            except OSError:
                pass

    print("Vault migration completed successfully!", flush=True)


if __name__ == "__main__":
    migrate_notes()
