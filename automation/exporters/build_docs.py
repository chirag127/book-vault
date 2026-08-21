"""Regenerate the index docs, Maps of Content, and note template.

Run after `python -m automation.curriculum` (which rebuilds manifest.csv,
taxonomy.py, SUBCATEGORY-MAP.md, and the md/ folder tree).

    .venv/Scripts/python -m automation.build_docs

Produces:
- ALL-BOOKS.md            full catalog grouped by pillar -> category
- READING-ORDER.md        12-pillar learning sequence
- MOCs/00-MASTER-INDEX.md master dashboard (Dataview + static tables)
- MOCs/0X-<Pillar>-MOC.md per-pillar dashboards
- templates/book-summary-template.md
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..core.config import ROOT
from ..curriculum.curriculum import PILLARS, slugify

from ..core.manifest import load_manifest

ALL_BOOKS_PATH = ROOT / "ALL-BOOKS.md"
READING_ORDER_PATH = ROOT / "READING-ORDER.md"
MOC_ROOT = ROOT / "MOCs"
TEMPLATE_PATH = ROOT / "templates" / "book-summary-template.md"


def _wikilink(book: dict[str, str]) -> str:
    return f"[[{book['slug']}|{book['title']}]]"


def _grouped(books: list[dict[str, str]]) -> dict[str, dict[str, list[dict[str, str]]]]:
    by_pillar: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for book in books:
        by_pillar[book["pillar"]][book["category"]].append(book)
    for pillar in by_pillar.values():
        for category_books in pillar.values():
            category_books.sort(key=lambda b: (int(b.get("number") or 0), b["title"].casefold()))
    return by_pillar


def build_all_books(books: list[dict[str, str]]) -> str:
    by_pillar = _grouped(books)
    lines = [
        "# All Books",
        "",
        "> Complete index of every book in the vault. One canonical file per book — a book may be linked from many places but physically exists only once, under `md/`.",
        "",
        f"> **{len(books)} books** across 12 pillars (four-level classification: Pillar → Category → Subcategory → Tags), generated from the canonical 2,000-book curriculum. See [[BOOK-MANIFEST]], [[SUBCATEGORY-MAP]], and the dashboards in [[MOCs/00-MASTER-INDEX|MOCs]].",
        "",
        "Status legend: **complete** = note written and validated; **planned** = listed in the manifest and awaiting generation by the pipeline.",
        "",
    ]
    for _, folder, display in PILLARS:
        pillar_books = by_pillar.get(display, {})
        if not pillar_books:
            continue
        lines.append(f"## {display}")
        lines.append("")
        for category, category_books in pillar_books.items():
            lines.append(f"### {category} ({len(category_books)})")
            lines.append("")
            lines.append("| # | Status | Book | Author | Subcategory | Difficulty |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for book in category_books:
                status = "complete" if book["status"] == "complete" else "planned"
                lines.append(
                    f"| {book['number']} | {status} | {_wikilink(book)} | {book['author']} | {book['subcategory']} | {book['difficulty']} |"
                )
            lines.append("")
    lines.append("## Navigation")
    lines.append("")
    lines.append("← Previous: [[START-HERE]]")
    lines.append("")
    lines.append("↑ Pillar sequence: [[READING-ORDER]]")
    lines.append("")
    lines.append("→ Next: [[BOOK-MANIFEST]]")
    lines.append("")
    return "\n".join(lines)


def build_reading_order(books: list[dict[str, str]]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for book in books:
        counts[book["pillar"]] += 1

    lines = [
        "# Canonical Learning Order",
        "",
        "> The 12 pillars are ordered as a curriculum: learning and cognition first, then reasoning, quantitative foundations, technical capability, money and organizations, life and the physical world, societies and power, and finally philosophy, biography, and the future.",
        "",
        "> Within each pillar, books are ordered by curriculum number inside their level-2 category; see [[SUBCATEGORY-MAP]], [[ALL-BOOKS]], and the dashboards in [[MOCs/00-MASTER-INDEX|MOCs]].",
        "",
        "## The sequence",
        "",
    ]
    for index, (_, folder, display) in enumerate(PILLARS, start=1):
        count = counts.get(display, 0)
        if not count:
            continue
        lines.append(f"{index}. [[md/{folder}/README|{display}]] — {count} books")
    lines.append("")
    lines.append("## Important design rule")
    lines.append("")
    lines.append("A book may link to books in later pillars when the connection is meaningful, but its primary pillar remains the pillar where it is most useful in this curriculum. Wikilinks create a graph; the numbered pillars create a reliable path through that graph. Every book note carries a `## Related Books` section with at least three computed wikilinks and a `next_reads` front-matter list, so the graph stays connected even before the vault is fully generated.")
    lines.append("")
    return "\n".join(lines)


def _moc_body(display: str, folder: str, by_category: dict[str, list[dict[str, str]]], mocs_link: str) -> str:
    lines = [
        f"# {display} — Map of Content",
        "",
        f"> Level-1 pillar. Books live in `md/{folder}/<NN-Category>/<Slug>.md`. Category = level 2, subcategory = level 3, tags = level 4. Index: [[{mocs_link}|MOCs]]. Full sequence: [[READING-ORDER]].",
        "",
        "## Dashboard (Dataview)",
        "",
        "````dataview",
        "TABLE WITHOUT ID",
        '  file.link AS "Book",',
        '  category AS "Category",',
        '  subcategory AS "Subcategory",',
        '  author AS "Author",',
        '  difficulty AS "Difficulty",',
        '  read_status AS "Status",',
        '  rating AS "Rating"',
        f'FROM "md/{folder}"',
        "SORT file.name ASC",
        "````",
        "",
        "## Catalog",
        "",
    ]
    for category, category_books in by_category.items():
        lines.append(f"### {category} ({len(category_books)})")
        lines.append("")
        lines.append("| # | Book | Author | Difficulty | Status |")
        lines.append("| --- | --- | --- | --- | --- |")
        for book in category_books:
            status = "complete" if book["status"] == "complete" else "planned"
            lines.append(f"| {book['number']} | {_wikilink(book)} | {book['author']} | {book['difficulty']} | {status} |")
        lines.append("")
    return "\n".join(lines)


def write_mocs(books: list[dict[str, str]]) -> None:
    by_pillar = _grouped(books)
    MOC_ROOT.mkdir(parents=True, exist_ok=True)
    master = [
        "# Maps of Content — Master Index",
        "",
        "> Dashboards for the 12 pillars. Each MOC combines a live Dataview query (Obsidian) with a static table (GitHub / plain Markdown).",
        "",
    ]
    for index, (_, folder, display) in enumerate(PILLARS, start=1):
        count = sum(len(v) for v in by_pillar.get(display, {}).values())
        if not count:
            continue
        slug = slugify(display)
        moc_name = f"{index:02d}-{slug}-MOC"
        master.append(f"{index}. [[MOCs/{moc_name}|{display}]] — {count} books")
        body = _moc_body(display, folder, by_pillar[display], "MOCs/00-MASTER-INDEX")
        (MOC_ROOT / f"{moc_name}.md").write_text(body + "\n", encoding="utf-8")
    master.append("")
    master.append("## Navigation")
    master.append("")
    master.append("← Previous: [[ALL-BOOKS]]")
    master.append("")
    master.append("→ Next: [[READING-ORDER]]")
    master.append("")
    (MOC_ROOT / "00-MASTER-INDEX.md").write_text("\n".join(master), encoding="utf-8")
    print(f"WROTE {len(by_pillar)} pillar MOCs -> {MOC_ROOT.relative_to(ROOT)}")


TEMPLATE = """---
title: "Book Title"
subtitle: "Subtitle if applicable"
author:
  - "Author Name"
published: YYYY
pillar: "Level 1 — Pillar"
category: "Level 2 — Category"
subcategory: "Level 3 — Subcategory"
topic: "Level 4 — Finer theme"
learning_stage: ""
prerequisites: ""
tags:
  - books
  - pillar-keyword
  - relevant-topic
difficulty: beginner
book_type: "Practical Guide | Theoretical Synthesis | Case Study | Biography / Memoir | Handbook / Reference | Academic Text"
read_status: "Completed"
rating: 5
reading_order_seq: 0
estimated_summary_reading_time: "XX minutes"
next_reads:
  - "[[Related-Book-Slug|Related Book]]"
status: complete
---

# Book Title

> One original sentence explaining why this book matters.

## Quick Take

A concise overview of the entire book — works for a reader with five minutes.

## Why Read This Book?

- Why the book became important.
- Who should read it and what they gain.
- Who might not benefit from it.
- Any important limitations.

## The Central Question

What problem, question, or challenge is the author addressing?

## The Core Thesis

The main argument in plain language.

## The Big Picture

How the major ideas fit together — a conceptual narrative, not a list.

## Key Ideas

### 1. Key Idea Name

What it means, why it matters, and how the author supports it — with evidence and examples.

## Evidence and Examples

What supports the claims, and how strong that evidence is.

## Criticism and Limitations

What critics dispute, what may be outdated, and where the argument has boundary conditions.

## Practical Use

What the reader can actually do with this knowledge.

## Connections to Other Books in This Vault

Weave at least three [[wikilinks]] into this section, naming each intellectual relationship (agreement, extension, contradiction, prerequisite).

## If You Remember Only Five Things

1. ...
2. ...
3. ...
4. ...
5. ...

```mermaid
flowchart LR
  Idea1 --> Idea2 --> Idea3
```

Audio description: explain the diagram in words for text-to-speech.

## TTS-Friendly Recap

A spoken summary of the entire note, written to be read aloud.

## Related Books

- [[Related-Book-Slug|Related Book]] — why it connects.

## Sources and Further Reading

- Author or publisher official page: URL
- Reliable secondary source: URL

## Navigation

← Previous: [[Previous-Book|Previous Book]]
↑ Category: [[Pillar-README|Pillar]]
→ Next: [[Next-Book|Next Book]]
"""


def write_template() -> None:
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.write_text(TEMPLATE, encoding="utf-8")
    print(f"WROTE template -> {TEMPLATE_PATH.relative_to(ROOT)}")


def main() -> None:
    books = load_manifest(ROOT / "automation" / "manifest.csv")
    ALL_BOOKS_PATH.write_text(build_all_books(books), encoding="utf-8")
    READING_ORDER_PATH.write_text(build_reading_order(books), encoding="utf-8")
    write_mocs(books)
    write_template()
    print(f"WROTE {ALL_BOOKS_PATH.relative_to(ROOT)} ({len(books)} books)")
    print(f"WROTE {READING_ORDER_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
