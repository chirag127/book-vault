from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CURRICULUM_DIR = Path(__file__).resolve().parent

MODULES = [
    ("01", "Learning, Thinking & Knowledge", "01-Learning-Thinking-and-Knowledge", "curriculum_01_learning.py", "BOOKS_01"),
    ("02", "Communication, Writing & Social Intelligence", "02-Communication-Writing-and-Social-Intelligence", "curriculum_02_communication.py", "BOOKS_02"),
    ("03", "Psychology & Human Behavior", "03-Psychology-and-Human-Behavior", "curriculum_03_psychology.py", "BOOKS_03"),
    ("04", "Personal Development & Life Skills", "04-Personal-Development-and-Life-Skills", "curriculum_04_personal_dev.py", "BOOKS_04"),
    ("05", "Finance, Investing & Wealth", "05-Finance-Investing-and-Wealth", "curriculum_05_finance.py", "BOOKS_05"),
    ("06", "Economics, Business & Entrepreneurship", "06-Economics-Business-and-Entrepreneurship", "curriculum_06_economics.py", "BOOKS_06"),
    ("07", "Computer Science & Technology Concepts", "07-Computer-Science-and-Technology-Concepts", "curriculum_07_computer_science.py", "BOOKS_07"),
    ("08", "Artificial Intelligence & Future Technology", "08-Artificial-Intelligence-and-Future-Technology", "curriculum_08_ai_tech.py", "BOOKS_08"),
    ("09", "Philosophy, Ethics & Decision-Making", "09-Philosophy-Ethics-and-Decision-Making", "curriculum_09_philosophy.py", "BOOKS_09"),
    ("10", "History, Civilization & Geopolitics", "10-History-Civilization-and-Geopolitics", "curriculum_10_history.py", "BOOKS_10"),
    ("11", "Science, Nature & the Universe", "11-Science-Nature-and-the-Universe", "curriculum_11_science.py", "BOOKS_11"),
    ("12", "Society, Politics, Law & Public Policy", "12-Society-Politics-Law-and-Public-Policy", "curriculum_12_society.py", "BOOKS_12"),
    ("13", "Biography, Memoir & Lives", "13-Biography-Memoir-and-Lives", "curriculum_13_biography.py", "BOOKS_13"),
]


def clean_name(s: str) -> str:
    """Format string for clean folder names."""
    # Strip numbering prefix like "01. " or "02. "
    s = re.sub(r"^\d+\.\s*", "", s).strip()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
    return s


def parse_hierarchy_from_file(file_path: Path) -> list[dict]:
    """Parse Level 2 (Category), Level 3 (Subcategory), and book dicts line-by-line."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    books = []
    current_category = "General"
    current_subcategory = "General"

    for line in lines:
        stripped = line.strip()
        # Check Level 2
        l2_match = re.search(r"LEVEL 2:\s*(?:(\d+)\.\s*)?([^(#]+)", stripped, re.IGNORECASE)
        if l2_match:
            cat_num = l2_match.group(1) or ""
            cat_name = l2_match.group(2).strip()
            if cat_num:
                current_category = f"{int(cat_num):02d}-{clean_name(cat_name)}"
            else:
                current_category = clean_name(cat_name)

        # Check Level 3
        l3_match = re.search(r"LEVEL 3:\s*([^(#]+)", stripped, re.IGNORECASE)
        if l3_match:
            current_subcategory = l3_match.group(1).strip().title()

        # Check book dict line
        if stripped.startswith("{") and ("title" in stripped or "slug" in stripped):
            # Parse dict safely
            try:
                import ast

                b = ast.literal_eval(stripped.rstrip(","))
                b["category"] = current_category
                b["subcategory"] = current_subcategory
                books.append(b)
            except Exception as e:
                print(f"Error parsing line: {stripped} -> {e}")

    return books


def compile_and_validate_manifest():
    all_books = []
    seen_ids = set()
    seen_slugs = set()
    slug_counts: dict[str, int] = {}

    print("=" * 70)
    print("VALIDATING & COMPILING 2,000-BOOK SUMMARY-FIRST LIFETIME CURRICULUM")
    print("=" * 70)

    for domain_code, domain_name, domain_folder, filename, varname in MODULES:
        file_path = CURRICULUM_DIR / filename
        books_in_module = parse_hierarchy_from_file(file_path)
        print(f"Domain {domain_code}: {domain_name:<50} -> {len(books_in_module):>4} books")

        for b in books_in_module:
            b_copy = dict(b)
            b_copy["domain_code"] = domain_code
            b_copy["domain_name"] = domain_name
            b_copy["domain_folder"] = domain_folder

            # Ensure unique slug
            base_slug = b_copy["slug"]
            if base_slug in seen_slugs:
                slug_counts[base_slug] = slug_counts.get(base_slug, 1) + 1
                b_copy["slug"] = f"{base_slug}-{slug_counts[base_slug]}"
                print(f"  [DEDUP SLUG] {base_slug} -> {b_copy['slug']}")
            seen_slugs.add(b_copy["slug"])

            all_books.append(b_copy)

    print("-" * 70)
    print(f"TOTAL BOOKS PARSED: {len(all_books)}")
    assert len(all_books) == 2000, f"Expected 2000 books, got {len(all_books)}"

    # Check ID sequence
    for i, b in enumerate(all_books, start=1):
        expected_id = f"{i:04d}"
        b["id"] = expected_id
        b["number"] = expected_id

    # Write manifest.csv
    manifest_path = PROJECT_ROOT / "automation" / "manifest.csv"
    headers = [
        "number",
        "id",
        "priority",
        "title",
        "author",
        "first_published",
        "latest_published",
        "published",
        "domain",
        "pillar",
        "category",
        "subcategory",
        "topic",
        "slug",
        "difficulty",
        "status",
        "path",
        "type",
        "reading_mode",
        "summary_depth",
        "learning_stage",
        "prerequisites",
        "primary_source",
    ]

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for b in all_books:
            first_pub = b.get("first_published", "")
            latest_pub = b.get("latest_published", "")
            domain_f = b["domain_folder"]
            cat_f = b["category"]
            slug = b["slug"]

            # Standardized path
            rel_path = f"md/{domain_f}/{cat_f}/{slug}.md"

            # Check if summary already exists in vault
            full_path = PROJECT_ROOT / rel_path
            status = "complete" if full_path.exists() else "planned"

            writer.writerow(
                {
                    "number": b["id"],
                    "id": b["id"],
                    "priority": b.get("priority", "P0"),
                    "title": b["title"],
                    "author": b["author"],
                    "first_published": first_pub,
                    "latest_published": latest_pub,
                    "published": first_pub,
                    "domain": f"{b['domain_code']}-{b['domain_name']}",
                    "pillar": b["domain_name"],
                    "category": b["category"],
                    "subcategory": b.get("subcategory", b.get("topic", "")),
                    "topic": b.get("topic", ""),
                    "slug": slug,
                    "difficulty": b.get("difficulty", "Intermediate"),
                    "status": status,
                    "path": rel_path,
                    "type": b.get("type", "nonfiction"),
                    "reading_mode": b.get("reading_mode", "summary"),
                    "summary_depth": b.get("summary_depth", "detailed"),
                    "learning_stage": b.get("learning_stage", "Foundation"),
                    "prerequisites": b.get("prerequisites", ""),
                    "primary_source": b.get("primary_source", ""),
                }
            )

    print(f"Successfully compiled {len(all_books)} books to {manifest_path}")


if __name__ == "__main__":
    compile_and_validate_manifest()
