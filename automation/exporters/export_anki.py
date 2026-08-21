from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from ..core.config import ROOT



def extract_flashcards_from_markdown(md_text: str) -> list[tuple[str, str]]:
    """Extract Q: ... A: ... flashcard pairs from markdown."""
    cards = []
    # Match Q: ... ? followed by A: ...
    pattern = re.compile(r"^Q:\s*(.+?)\s*\n+A:\s*(.+?)(?=\n\s*(?:Q:|#|$))", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(md_text):
        q = match.group(1).strip()
        a = match.group(2).strip().replace("\n", " ")
        cards.append((q, a))
    return cards


def export_anki_deck(output_path: Path | None = None) -> Path:
    """Scan all book practical chapters and export an Anki-compatible TSV/CSV deck."""
    if output_path is None:
        output_path = ROOT / "vault_anki_deck.tsv"

    cards: list[tuple[str, str, str, str]] = []
    md_files = list(ROOT.glob("md/**/*.md"))

    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8")
        except OSError:
            continue

        extracted = extract_flashcards_from_markdown(content)
        if extracted:
            book_slug = f.parent.name if f.parent.name != "md" else "General"
            for q, a in extracted:
                cards.append((q, a, book_slug, str(f.relative_to(ROOT))))

    with open(output_path, "w", encoding="utf-8", newline="") as out_file:
        writer = csv.writer(out_file, delimiter="\t")
        writer.writerow(["# Front (Question)", "Back (Answer)", "Book Tag", "Source Note"])
        for q, a, tag, note in cards:
            writer.writerow([q, a, tag, note])

    print(f"[anki] Exported {len(cards)} active recall flashcards -> {output_path.name}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export all active recall flashcards to an Anki-ready deck.")
    parser.add_argument("--output", "-o", help="Output file path (default: vault_anki_deck.tsv).")
    args = parser.parse_args()

    out_path = Path(args.output) if args.output else None
    export_anki_deck(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
