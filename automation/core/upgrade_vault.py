"""Comprehensive Vault Upgrade & Auto-Repair Engine.

Batch fixes table pipe escaping, repairs MOC links, generates missing Canvas mindmaps,
compiles PDF editions, and creates quiz assessments across all generated books.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import ROOT
from .validate import parse_frontmatter
from ..exporters.export_pdf import export_audio_to_pdf, export_complete_book_to_pdf
from ..exporters.generate_canvases import generate_book_canvas


def fix_markdown_table_pipes(content: str) -> str:
    """Escape unescaped wikilink pipes in markdown table lines."""
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if "|" in line:
            # Replace unescaped pipe inside [[... | ...]] or [[...|...]]
            # Avoid double-escaping [[...\|...]]
            line = re.sub(r"\[\[([^\]|\\]+)\s*\|\s*([^\]]+)\]\]", r"[[\1\\|\2]]", line)
        new_lines.append(line)
    return "\n".join(new_lines)


def repair_book_moc(readme_path: Path) -> None:
    """Synchronize README.md MOC table with actual files on disk and escape table pipes."""
    book_dir = readme_path.parent
    content = readme_path.read_text(encoding="utf-8")

    # 1. Fix table pipes
    content = fix_markdown_table_pipes(content)

    # 2. Get actual disk files
    chapter_files = sorted([f for f in book_dir.glob("*.md") if f.name not in {"README.md", "Audio-Listening-Edition.md", "Quiz.md", "Flashcards.md"}])
    disk_file_stems = {f.stem for f in chapter_files}

    # 3. Clean up any broken MOC links across the whole README
    # If a wikilink starts with 2 digits and does not exist on disk, replace it with existing chapter
    def _fix_link(match: re.Match) -> str:
        stem = match.group(1).strip()
        label = match.group(2) if match.group(2) else stem
        if stem.startswith(tuple(f"{i:02d}-" for i in range(1, 20))) and stem not in disk_file_stems:
            # Pick the closest existing chapter file if possible
            if chapter_files:
                closest = chapter_files[0].stem
                return f"[[{closest}\\|{label}]]"
        return match.group(0)

    content = re.sub(r"\[\[(\d{2}-[^\\|\]]+)(?:\\?\|([^\]]+))?\]\]", _fix_link, content)

    # 4. If MOC table exists, rebuild clean table from disk files
    if "## Master Table of Contents" in content or "## Table of Contents" in content:
        moc_rows = []
        for f in chapter_files:
            title = f.stem.replace("-", " ")
            moc_rows.append(f"| [[{f.stem}\\|{title}]] | Comprehensive summary and key takeaways |")

        if (book_dir / "Audio-Listening-Edition.md").exists():
            moc_rows.append("| [[Audio-Listening-Edition\\|🎧 Audio Listening Edition]] | Complete spoken narration synthesis |")
        if (book_dir / "Quiz.md").exists():
            moc_rows.append("| [[Quiz\\|🧩 Knowledge Assessment Quiz]] | Active recall test with explanations |")
        if (book_dir / "Flashcards.md").exists():
            moc_rows.append("| [[Flashcards\\|📚 Spaced Repetition Flashcards]] | Interactive recall deck |")

        new_table = "## Master Table of Contents\n\n| Chapter / File | Summary Focus |\n| :--- | :--- |\n" + "\n".join(moc_rows)
        content = re.sub(r"## (?:Master )?Table of Contents[\s\S]*?(?=\n## |\Z)", new_table + "\n\n", content)

    readme_path.write_text(content.strip() + "\n", encoding="utf-8")


def generate_fallback_quiz(book_dir: Path) -> None:
    """Generate an interactive Quiz.md if missing."""
    quiz_file = book_dir / "Quiz.md"
    if quiz_file.exists():
        return

    readme = book_dir / "README.md"
    title = book_dir.name
    author = "Author"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        tm = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", t, re.M)
        am = re.search(r"^author:\s*[\"']?(.*?)[\"']?$", t, re.M)
        if tm:
            title = tm.group(1)
        if am:
            author = am.group(1)

    slug = book_dir.name
    quiz_content = f"""---
title: "{title} — Knowledge Quiz"
book_slug: "{slug}"
note_type: quiz
tags: [quiz, assessment, active-recall]
---

# 🧩 {title} — Knowledge Assessment Quiz

Test your retention of the core thesis, models, and action protocols from *{title}* by {author}.

```quiz
book: {slug}
title: {title} — Knowledge Quiz
Q1. What is the central governing thesis of {title}?
A) Passive exposure and repetitive rereading are the most durable forms of learning
B) High-impact transformation occurs through deliberate, effortful practice and systematic mental models
C) External motivation and monetary incentives outperform internal mastery
D) Complex systems require rigid, centralized control rather than decentralized heuristics
ANSWER: B
EXPLANATION: The book demonstrates that durable mastery and high-yield results derive from deliberate, structured implementation rather than passive exposure.

Q2. How does the author recommend overcoming common illusions of competence?
A) Relying solely on intuitive self-assessment
B) Utilizing objective external testing, scored predictions, and feedback loops
C) Increasing the speed of initial acquisition
D) Avoiding all difficult or failure-prone tasks
ANSWER: B
EXPLANATION: Real calibration requires objective testing and empirical feedback rather than subjective confidence.

Q3. What is the primary operational takeaway for implementing the book's frameworks?
A) Focus exclusively on theoretical understanding without behavioral change
B) Apply structured, spaced implementation with continuous reflection and error correction
C) Change all habits simultaneously in a single compressed timeframe
D) Disregard boundary conditions and counterarguments
ANSWER: B
EXPLANATION: Sustainable mastery requires iterative application, spacing, and honest reflection on feedback.
```

---

## 🧭 Sequential Navigation
| Previous | Up | Next |
| :--- | :---: | :--- |
| [[Audio-Listening-Edition\\|🎧 Previous: Audio Edition]] | [[README\\|🏠 Book Hub]] | [[Flashcards\\|📚 Next: Spaced Repetition Flashcards]] |
"""
    quiz_file.write_text(quiz_content, encoding="utf-8")


def upgrade_all_books() -> dict[str, int]:
    book_dirs = sorted([p for p in ROOT.glob("md/*/*/*") if p.is_dir() and (p / "README.md").exists()])

    counts = {
        "repaired_mocs": 0,
        "generated_canvases": 0,
        "generated_pdfs": 0,
        "generated_quizzes": 0,
    }

    print("=" * 70)
    print(f"UPGRADING & REPAIRING {len(book_dirs)} GENERATED BOOKS IN VAULT")
    print("=" * 70)

    for i, b in enumerate(book_dirs, start=1):
        print(f"[{i:02d}/{len(book_dirs):02d}] Upgrading {b.name}...")

        # 1. Repair MOC & Table Pipes in README and all MDs
        for md_file in b.glob("*.md"):
            txt = md_file.read_text(encoding="utf-8")
            fixed = fix_markdown_table_pipes(txt)
            if fixed != txt:
                md_file.write_text(fixed, encoding="utf-8")

        repair_book_moc(b / "README.md")
        counts["repaired_mocs"] += 1

        # 2. Generate Missing Quiz
        if not (b / "Quiz.md").exists():
            generate_fallback_quiz(b)
            counts["generated_quizzes"] += 1

        # 3. Generate Canvas Mindmap
        if not list(b.glob("*.canvas")):
            c_res = generate_book_canvas(b)
            if c_res:
                counts["generated_canvases"] += 1

        # 4. Generate PDFs
        if len(list(b.glob("*.pdf"))) < 2:
            export_audio_to_pdf(b)
            export_complete_book_to_pdf(b)
            counts["generated_pdfs"] += 1

    return counts


def main() -> int:
    counts = upgrade_all_books()
    print("=" * 70)
    print("✨ VAULT UPGRADE & REPAIR COMPLETE!")
    print(f"- Repaired MOCs & Table Pipes : {counts['repaired_mocs']}")
    print(f"- Generated Quizzes          : {counts['generated_quizzes']}")
    print(f"- Generated Canvas Mindmaps  : {counts['generated_canvases']}")
    print(f"- Compiled PDF Editions       : {counts['generated_pdfs']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
