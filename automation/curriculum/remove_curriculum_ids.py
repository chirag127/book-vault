"""Strip hardcoded 'id' fields from all curriculum files.

Enables future additions without manual ID maintenance; IDs are dynamically
assigned by build_curriculum_2000.py upon compilation.
"""
from __future__ import annotations

import re
from pathlib import Path

CURRICULUM_DIR = Path(__file__).resolve().parent

CURRICULUM_FILES = [
    "curriculum_01_learning.py",
    "curriculum_02_communication.py",
    "curriculum_03_psychology.py",
    "curriculum_04_personal_dev.py",
    "curriculum_05_finance.py",
    "curriculum_06_economics.py",
    "curriculum_07_computer_science.py",
    "curriculum_08_ai_tech.py",
    "curriculum_09_philosophy.py",
    "curriculum_10_history.py",
    "curriculum_11_science.py",
    "curriculum_12_society.py",
    "curriculum_13_biography.py",
]


def strip_ids_from_file(file_path: Path) -> int:
    content = file_path.read_text(encoding="utf-8")
    # Pattern matching "id": "0001", or 'id': '0001', with optional trailing whitespace
    pattern = re.compile(r"""["']id["']:\s*["'][^"']+["'],\s*""")
    new_content, count = pattern.subn("", content)
    if count > 0:
        file_path.write_text(new_content, encoding="utf-8")
    return count


def main() -> int:
    total_stripped = 0
    print("=" * 60)
    print("STRIPPING HARDCODED IDs FROM ALL CURRICULUM FILES")
    print("=" * 60)
    for filename in CURRICULUM_FILES:
        fpath = CURRICULUM_DIR / filename
        if fpath.exists():
            count = strip_ids_from_file(fpath)
            total_stripped += count
            print(f"[OK] {filename:<35} -> stripped {count} IDs")
        else:
            print(f"[SKIP] {filename:<35} -> file not found")

    print("-" * 60)
    print(f"Total IDs stripped: {total_stripped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
