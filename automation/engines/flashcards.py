from __future__ import annotations

import re
from pathlib import Path


def extract_flashcards_from_book(book_dir: Path) -> list[tuple[str, str]]:
    """Extract all flashcards from concept notes in a book folder."""
    cards: list[tuple[str, str]] = []
    
    for f in sorted(book_dir.glob("*.md")):
        if f.name in {"README.md", "Audio-Listening-Edition.md", "Quiz.md", "Flashcards.md"}:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except OSError:
            continue

        # Format 1: > [!QUESTION]- Question \n > Answer
        callout_pat = re.compile(r"> \[!QUESTION\]-?\s*(.+?)\n((?:> .*\n?)+)", re.MULTILINE)
        for m in callout_pat.finditer(content):
            q = m.group(1).strip()
            raw_a = re.sub(r"^>\s*", "", m.group(2), flags=re.MULTILINE).strip()
            # Stop answer at any trailing commentary paragraph
            a_paragraphs = raw_a.split("\n\n")
            clean_a_parts = []
            for p in a_paragraphs:
                p_str = p.strip()
                if p_str.startswith("These protocols") or p_str.startswith("Cross-links:") or p_str.startswith("See [["):
                    break
                clean_a_parts.append(p_str.replace("\n", " "))
            a = " ".join(clean_a_parts).strip()
            if q and a:
                cards.append((q, a))

        # Format 2: Q: ... A: ...
        qa_pat = re.compile(r"^Q:\s*(.+?)\n+A:\s*(.+?)(?=\n+Q:|\n+##|\n+Cross-links:|\n+These protocols|\Z)", re.MULTILINE | re.DOTALL)
        for m in qa_pat.finditer(content):
            q = m.group(1).strip()
            raw_a = m.group(2).strip()
            a_first_para = raw_a.split("\n\n")[0].strip().replace("\n", " ")
            if q and a_first_para and (q, a_first_para) not in cards:
                cards.append((q, a_first_para))

    return cards


def write_book_flashcards_note(book_dir: Path, book: dict[str, str], next_book: dict[str, str] | None = None) -> Path:
    """Generate and write Flashcards.md containing the interactive ```flashcards block."""
    cards = extract_flashcards_from_book(book_dir)
    if not cards:
        # Fallback card based on book thesis
        cards = [
            (f"What is the core thesis of {book['title']}?", f"An authoritative synthesis of {book.get('category', 'core principles')} by {book.get('author', 'the author')}."),
        ]

    flashcards_file = book_dir / "Flashcards.md"

    cards_block = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in cards)

    next_book_link = f"[[{next_book['slug']}/README|➡️ Next Book: {next_book['title']}]]" if next_book else "[[README|🏠 Vault Index]]"

    content = f"""---
title: "{book['title']} — Active Recall Flashcards"
author: "{book.get('author', '')}"
book_slug: "{book.get('slug', book_dir.name)}"
parent_hub: "[[README]]"
note_type: "flashcard-deck"
---

# {book['title']} — Active Recall Flashcards

*By {book.get('author', '')}*

```flashcards
{cards_block}
```

---

## 🧭 Sequential Reading Navigation
| Previous | Up | Next Book in Curriculum |
| :--- | :---: | :--- |
| [[Quiz|🧩 Previous: Knowledge Assessment Quiz]] | [[README|🏠 Current Book Hub]] | {next_book_link} |
"""
    flashcards_file.write_text(content.strip() + "\n", encoding="utf-8")
    return flashcards_file
