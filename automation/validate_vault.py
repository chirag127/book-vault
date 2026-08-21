from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, load_settings
from .validate import find_duplicate_book_files, validate_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated book notes.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    settings = load_settings()
    failures = validate_tree(args.root, min_words=settings.min_words, max_words=settings.max_words)
    duplicates = find_duplicate_book_files(args.root)
    exit_code = 0
    if failures:
        exit_code = 1
        for path, errors in failures.items():
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        print(f"{len(failures)} file(s) failed validation.")
    if duplicates:
        exit_code = 1
        for stem, paths in duplicates:
            print(f"DUPLICATE {stem}:")
            for path in paths:
                print(f"  - {path}")
        print(f"{len(duplicates)} duplicate book file(s) found.")
    if exit_code == 0:
        print("All book notes passed flexible structural validation. No duplicate book files.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
