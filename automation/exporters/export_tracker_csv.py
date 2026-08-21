"""Export book vault reading list to standard CSV for Hardcover, Goodreads, and StoryGraph."""
from __future__ import annotations

import csv
from pathlib import Path
from ..core.config import ROOT
from ..core.manifest import load_manifest


def export_tracker_csv(output_path: Path | None = None) -> Path:
    output_path = output_path or (ROOT / "vault_reading_export.csv")
    books = load_manifest(ROOT / "automation" / "manifest.csv")

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Title",
            "Author",
            "Year Published",
            "Pillar",
            "Category",
            "Subcategory",
            "Exclusive Shelf",
            "My Rating",
            "Tags",
        ])
        for b in books:
            writer.writerow([
                b["title"],
                b["author"],
                b.get("published", ""),
                b["pillar"],
                b["category"],
                b.get("subcategory", ""),
                "to-read",
                "",
                f"{b['pillar']}; {b['category']}",
            ])

    print(f"[export] Generated standard tracker CSV -> {output_path.relative_to(ROOT)} ({len(books)} books)")
    return output_path


if __name__ == "__main__":
    export_tracker_csv()
