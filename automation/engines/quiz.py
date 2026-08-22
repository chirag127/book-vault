from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import Settings

TEMPLATE_QUIZ_VERSION = "2026-08-22-quiz-v1"


def build_quiz_prompt(
    book: dict[str, str],
    reading_content: str,
    num_questions: int = 10,
) -> list[dict[str, str]]:
    """Build a prompt to generate a 10-question multiple choice Quiz.md based on the book summary."""
    system_prompt = (
        "You are an expert pedagogical exam designer creating an authoritative, high-signal knowledge "
        "assessment quiz based on an in-depth book summary for an Obsidian knowledge vault."
    )

    user_prompt = f"""Generate an interactive 10-question multiple-choice quiz for the book "{book['title']}" by {book['author']}.

Base the questions directly on the provided book summary content below to test deep conceptual understanding, mental models, key frameworks, and practical applications.

=== BOOK SUMMARY CONTENT ===
{reading_content[:20000]}
============================

STRICT OUTPUT FORMAT RULES:
1. Start with valid YAML frontmatter:
---
title: "{book['title']} — Knowledge Quiz"
book_slug: "{book['slug']}"
note_type: "quiz"
tags: [quiz, {book.get('category', '').lower().replace(' ', '-').replace('&', 'and')}]
---

2. Top-level heading:
# 📝 {book['title']} — Knowledge Quiz

Test your understanding of the core concepts, mental models, and practical takeaways from *{book['title']}* by {book['author']}.

3. Fenced quiz code block:
```quiz
book: {book['slug']}
title: {book['title']} — Knowledge Quiz
---
Q1. [Clear conceptual question testing understanding, not trivia]
A) [Plausible distractor]
B) [Correct answer]
C) [Plausible distractor]
D) [Plausible distractor]
ANSWER: B
EXPLANATION: [1-2 sentences explaining precisely why this answer is correct based on the book's frameworks]

Q2. [Question 2...]
A) ...
B) ...
C) ...
D) ...
ANSWER: ...
EXPLANATION: ...

... up to Q10.
```

4. Quick Reference Key:
After the ```quiz ... ``` block, include a summary table of the key concepts assessed.

Ensure all 10 questions test meaningful principles and actionable heuristics from the book.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_quiz_content(
    settings: Settings,
    book: dict[str, str],
    destination_dir: Path,
) -> str | None:
    """Generate Quiz.md content for a book directory using its existing concept notes / README."""
    from .llm_client import generate_markdown

    # Aggregate text from all concept notes and README.md
    texts = []
    readme_path = destination_dir / "README.md"
    if readme_path.exists():
        texts.append(readme_path.read_text(encoding="utf-8"))

    for note in sorted(destination_dir.glob("*.md")):
        if note.name not in {"README.md", "Audio-Listening-Edition.md", "Quiz.md"}:
            texts.append(f"\n--- Note: {note.name} ---\n" + note.read_text(encoding="utf-8"))

    if not texts:
        return None

    combined_summary = "\n\n".join(texts)
    prompt = build_quiz_prompt(book, combined_summary)

    raw = generate_markdown(
        settings,
        prompt,
        cache_key=f"book-quiz-{book['slug']}-{TEMPLATE_QUIZ_VERSION}",
    )
    return raw
