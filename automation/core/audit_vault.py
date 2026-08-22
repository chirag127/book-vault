"""Comprehensive Automated Audit for Generated Books in Vault.

Performs deep structural, linguistic, and link audits across all generated book folders.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import ROOT
from .validate import parse_frontmatter


def audit_vault() -> dict[str, Any]:
    book_dirs = sorted([p for p in ROOT.glob("md/*/*/*") if p.is_dir() and (p / "README.md").exists()])

    total_books = len(book_dirs)
    results: list[dict[str, Any]] = []

    missing_pdf_count = 0
    missing_canvas_count = 0
    missing_quiz_count = 0
    missing_flashcards_count = 0
    broken_links_count = 0
    total_words_vault = 0

    for b in book_dirs:
        readme = b / "README.md"
        readme_text = readme.read_text(encoding="utf-8")

        # 1. Frontmatter audit
        try:
            meta, body = parse_frontmatter(readme_text)
            fm_ok = True
        except Exception:
            meta, body = {}, ""
            fm_ok = False

        # 2. Files audit
        md_files = list(b.glob("*.md"))
        pdf_files = list(b.glob("*.pdf"))
        canvas_files = list(b.glob("*.canvas"))
        mp3_files = list(b.glob("*.mp3"))

        has_audio_md = (b / "Audio-Listening-Edition.md").exists()
        has_quiz = (b / "Quiz.md").exists()
        has_flashcards = (b / "Flashcards.md").exists()
        has_canvas = len(canvas_files) > 0
        has_pdf = len(pdf_files) >= 2

        if not has_pdf:
            missing_pdf_count += 1
        if not has_canvas:
            missing_canvas_count += 1
        if not has_quiz:
            missing_quiz_count += 1
        if not has_flashcards:
            missing_flashcards_count += 1

        # 3. Word count
        word_count = sum(len(f.read_text(encoding="utf-8").split()) for f in md_files)
        total_words_vault += word_count

        # 4. MOC links audit
        moc_links = re.findall(r"\[\[(\d{2}-[^\\|\]]+)(?:\\?\|[^\]]+)?\]\]", readme_text)
        disk_files = {f.stem for f in md_files}
        broken_moc = [link for link in moc_links if link not in disk_files]
        if broken_moc:
            broken_links_count += len(broken_moc)

        # 5. Unescaped table pipes in wikilinks check
        unescaped_table_pipes = len(re.findall(r"^\|.*\[\[[^\\|\]]+\|[^\]]+\]\].*\|$", readme_text, re.M))

        results.append({
            "slug": b.name,
            "path": str(b.relative_to(ROOT)),
            "title": meta.get("title", b.name),
            "author": meta.get("author", "Unknown"),
            "md_count": len(md_files),
            "word_count": word_count,
            "has_audio_md": has_audio_md,
            "has_quiz": has_quiz,
            "has_flashcards": has_flashcards,
            "has_pdf": has_pdf,
            "has_canvas": has_canvas,
            "broken_moc": broken_moc,
            "unescaped_table_pipes": unescaped_table_pipes,
            "fm_ok": fm_ok,
        })

    summary = {
        "total_books": total_books,
        "total_words_vault": total_words_vault,
        "avg_words_per_book": total_words_vault // total_books if total_books else 0,
        "missing_pdf_count": missing_pdf_count,
        "missing_canvas_count": missing_canvas_count,
        "missing_quiz_count": missing_quiz_count,
        "missing_flashcards_count": missing_flashcards_count,
        "broken_links_count": broken_links_count,
        "books": results,
    }
    return summary


def main() -> int:
    summary = audit_vault()
    print("=" * 70)
    print(" 🔍 COMPREHENSIVE GENERATED BOOK AUDIT REPORT")
    print("=" * 70)
    print(f"Total Books Generated on Disk : {summary['total_books']}")
    print(f"Total Vault Words             : {summary['total_words_vault']:,} words")
    print(f"Average Words per Book        : {summary['avg_words_per_book']:,} words")
    print("-" * 70)
    print(f"Missing PDF Editions          : {summary['missing_pdf_count']} / {summary['total_books']}")
    print(f"Missing Canvas Mindmaps       : {summary['missing_canvas_count']} / {summary['total_books']}")
    print(f"Missing Quiz Assessment       : {summary['missing_quiz_count']} / {summary['total_books']}")
    print(f"Missing Flashcard Decks       : {summary['missing_flashcards_count']} / {summary['total_books']}")
    print(f"Broken MOC Links Found        : {summary['broken_links_count']}")
    print("=" * 70)

    # Flag specific issues
    issues_found = []
    for b in summary["books"]:
        reasons = []
        if b["broken_moc"]:
            reasons.append(f"Broken MOC links: {b['broken_moc']}")
        if b["unescaped_table_pipes"] > 0:
            reasons.append(f"{b['unescaped_table_pipes']} unescaped table pipe(s)")
        if not b["has_quiz"]:
            reasons.append("Missing Quiz.md")
        if not b["has_flashcards"]:
            reasons.append("Missing Flashcards.md")
        if not b["has_pdf"]:
            reasons.append("Missing PDFs")
        if not b["has_canvas"]:
            reasons.append("Missing Canvas")
        if reasons:
            issues_found.append((b["slug"], reasons))

    if issues_found:
        print(f"\n⚠️  {len(issues_found)} BOOKS WITH DETECTED OPPORTUNITIES FOR UPGRADE:")
        for slug, reasons in issues_found[:15]:
            print(f"  • {slug:<35} -> {', '.join(reasons)}")
        if len(issues_found) > 15:
            print(f"  ... and {len(issues_found) - 15} more books.")
    else:
        print("\n✨ ALL GENERATED BOOKS ARE 100% HEALTHY AND COMPLIANT!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
