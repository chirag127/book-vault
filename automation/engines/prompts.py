from __future__ import annotations

import urllib.parse
from typing import Any

TEMPLATE_VERSION = "2026-08-22-book-summary-v6"

SYSTEM_PROMPT = """You are an elite polymath scholar, executive intelligence analyst, and master pedagogical architect creating the definitive, university-caliber Book Summary vault notes.

Your mission is to produce an exhaustive, authoritative, high-signal Book Summary that captures 100% of the book's vital insights, operating principles, mental models, and actionable protocols with ZERO fluff:
1. Executive Brief & Core Thesis: The central argument, non-obvious breakthrough ("The Premise"), target audience ROI, and foundational paradigm shift ("The So What?").
2. Deep Mental Models & Theoretical Foundations: Exhaustive explanation of core concepts, mathematical/systemic relationships, feedback loops, and root mechanisms organized across 3–5 authentic thematic pillars.
3. Empirical Evidence, Real Case Studies & Benchmarks: Detailed historical, scientific, psychological, or business case studies directly from the text with measurable outcomes and controlled findings.
4. Actionable Protocols & Decision Frameworks: Step-by-step implementation playbooks, decision trees, checklists, and concrete heuristics for real-world execution.
5. Critical Evaluation & Boundary Conditions: Rigorous analysis of model failure modes, edge cases, counter-arguments, and cross-disciplinary connections.

STRICT NON-NEGOTIABLE ANTI-HALLUCINATION PROTOCOL:
- Absolute Factual Fidelity: Every summary, concept, model, heuristic, equation, and case study MUST be authentic to the author and the actual published text.
- ZERO Hallucination Mandate: You are STRICTLY PROHIBITED from inventing fake citations, fictional statistical samples, fabricated case studies, or imaginary chapter names.
- Honest Handling of Recent or Niche Books: When analyzing newly published books (e.g. 2023–2026 releases) or specialized monographs where granular chapter text is limited in public training corpora, YOU MUST EXPLICITLY ACKNOWLEDGE THIS LIMITATION in README.md. Synthesize the verified core thesis, public abstracts, and author lectures transparently, clearly denoting what is confirmed vs. areas where readers should consult the primary text for deeper operational specifics.
- No Filler / Fluff: Never pad summaries with generic platitudes or invented anecdotes. State every verified concept with maximal density, clarity, and precision.

Obsidian & Visual Markdown Capabilities:
- Obsidian Callouts: Use appropriate callout boxes (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!EXAMPLE]`, `> [!QUOTE]`, `> [!QUESTION]-`) to highlight key takeaways, critical warnings, memorable author quotes, and collapsible active recall prompts.
- Visual Mermaid Diagrams: When explaining complex systems, processes, feedback loops, or decision trees, use valid Mermaid diagrams (```mermaid ... ```).
- Structured Comparison Tables: Use Markdown tables to compare strategies, pros/cons, phases, or theoretical models.
- LaTeX Math Blocks: For quantitative, mathematical, statistical, economic, or AI/CS books, use Obsidian LaTeX math (`$...$` for inline math, `$$\\n...\\n$$` for block formulas). Explain every variable and term in clear prose.
- Action Checklists: Use `- [ ]` markdown task items for implementation protocols and actionable habits.
- Bidirectional Wikilinks: Cross-link related concepts and books with `[[slug|Display Title]]` (or escaped `[[slug\\|Display Title]]` inside tables).
- Eliminate conversational preamble, filler transitions, and padding."""


def _book_links(title: str, author: str = "") -> str:
    """Generate minimal search URLs for all book tracker platforms."""
    query = urllib.parse.quote_plus(title)

    return f"""- [Open Library](https://openlibrary.org/search?q={query})
- [Goodreads](https://www.goodreads.com/search?q={query})
- [Google Books](https://www.google.com/search?tbm=bks&q={query})
- [WorldCat](https://search.worldcat.org/search?q={query})
- [Hardcover](https://hardcover.app/search?q={query})
- [StoryGraph](https://app.thestorygraph.com/browse?search_term={query})"""


def build_modular_reading_prompt(
    book: dict[str, str],
    sources: str,
    allow_no_web: bool = False,
    nav: dict[str, str] | None = None,
    graph: str | None = None,
    min_words: int = 1800,
    max_words: int = 4500,
) -> list[dict[str, str]]:
    category = book["category"].replace(";", ",")
    navigation = ""
    if nav:
        navigation = f"""## 🧭 Navigation

| Direction | Link |
| :--- | :--- |
| **Previous Book** | {nav['prev']} |
| **Category Hub** | {nav['category']} |
| **Next Book** | {nav['next']} |"""

    knowledge_graph = ""
    if graph:
        knowledge_graph = f"""
Knowledge-graph context:
{graph}
"""

    book_links = _book_links(book["title"], book["author"])

    user = f"""Create the complete, authoritative multi-file Executive Book Summary for "{book['title']}" by {book['author']}.

Book Metadata:
- Title: {book['title']}
- Author: {book['author']}
- First Published: {book.get('first_published', book.get('published', ''))}
- Latest Published: {book.get('latest_published', book.get('published', ''))}
- Pillar: {book.get('pillar', '')}
- Category: {book['category']}
- Subcategory: {book.get('subcategory', '')}
- Topic: {book.get('topic', '')}
- Slug: {book['slug']}
- Difficulty: {book.get('difficulty', 'Intermediate')}

Research sources & dossier:
{sources}
{knowledge_graph}

CRITICAL ANTI-HALLUCINATION & SCOPE DIRECTIVE:
1. Ground every claim, framework, and concept strictly in authentic, verifiable knowledge of "{book['title']}".
2. If this book is a recent release (e.g. 2023–2026) or if granular chapter details are sparse in the research dossier, DO NOT invent fake case studies or fictitious research experiments. Instead, synthesize the confirmed core thesis, published interviews, and conceptual frameworks truthfully.
3. If specific aspects of the book have limited documentation in the dossier, include an honest notice in `README.md`:
   ```markdown
   > [!NOTE] Epistemic Scope & Synthesis Notice
   > This summary is synthesized based on verified bibliographic abstracts, research dossiers, and core author publications. For comprehensive case studies and specialized implementation nuances, readers are encouraged to reference the primary work.
   ```

CRITICAL OUTPUT SEPARATION RULE:
You MUST output the complete summary across modular files using the exact delimiter format below. Each file begins with its own header line:
=== FILE: README.md ===
=== FILE: 01-[Specific-Book-Theme-Title].md ===
=== FILE: 02-[Specific-Book-Theme-Title].md ===
=== FILE: 03-[Specific-Book-Theme-Title].md ===
(Divide the book into 3 to 5 substantive thematic chapter files named dynamically after the book's authentic major sections, key laws, or core frameworks in kebab-case).

DO NOT output a single blob of Markdown. DO NOT wrap file blocks in outer ```markdown ``` code fences. Every file MUST begin with its frontmatter (---) and end cleanly with markdown content.

EXECUTIVE BOOK SUMMARY ARCHITECTURE (Blinkist / Shortform / getAbstract Standard):

1. Executive Hub & Master Guide (=== FILE: README.md ===):
   - Comprehensive YAML frontmatter:
     ```yaml
     title: "{book['title']}"
     author: "{book['author']}"
     first_published: {book.get('first_published', book.get('published', ''))}
     latest_published: {book.get('latest_published', book.get('published', ''))}
     published: {book.get('published', book.get('first_published', ''))}
     pillar: "{book.get('pillar', '')}"
     category: "{category}"
     subcategory: "{book.get('subcategory', '')}"
     topic: "{book.get('topic', '')}"
     slug: "{book['slug']}"
     difficulty: "{book.get('difficulty', 'Intermediate')}"
     status: complete
     note_type: book-summary
     tags: [insert-3-to-6-relevant-lowercase-tags]
     ```
   - `# {book['title']} — Complete Book Summary & Executive Guide`
   - `*By {book['author']} (First Published: {book.get('first_published', book.get('published', ''))}, Latest: {book.get('latest_published', book.get('published', ''))})*`
   - `## ⚡ Executive Summary & Value Proposition`:
     - **The Central Premise**: 1-2 sentence definition of the core thesis and problem solved.
     - **The Transformation ("So What?")**: Why this matters and how it shifts the reader's paradigm or operating model.
     - **Core Audience & Applicability**: Who gains the highest ROI from this work.
     - **Executive Takeaways (Top 5 Insights)**: 5 concise, high-signal bullet points capturing the breakthrough ideas.
   - Master Table of Contents as a clean Markdown table with wikilinks to every chapter summary file you generate and the companion editions:
     ```markdown
     ## 📑 Master Table of Contents
     | Chapter | Summary Focus & Mental Models |
     | :--- | :--- |
     | [[01-[Chapter-Slug]\\|01 · [Chapter Title] ]] | [One-sentence summary of this section's core insights & models] |
     | [[02-[Chapter-Slug]\\|02 · [Chapter Title] ]] | [One-sentence summary of this section's core insights & models] |
     | [[03-[Chapter-Slug]\\|03 · [Chapter Title] ]] | [One-sentence summary of this section's core insights & models] |
     | [[Audio-Listening-Edition\\|🎧 Audio Listening Edition]] | Complete spoken narration synthesis |
     | [[Quiz\\|🧩 Knowledge Assessment Quiz]] | Active recall test with explanations |
     | [[Flashcards\\|📚 Spaced Repetition Flashcards]] | Interactive recall deck |
     ```
   - `## 🎥 Curated Video Summaries & Lectures` section with verified video summaries and author talks.
   - `## 📚 External References & Book Trackers` section with these exact links:
{book_links}
   - {navigation}

2. Thematic Chapter Summary Files (=== FILE: 01-[Specific-Title].md ===, === FILE: 02-[Specific-Title].md ===, etc.):
   - Generate 3 to 5 comprehensive summary chapter files covering the book's authentic parts/themes.
   - YAML frontmatter on EVERY chapter file:
     ```yaml
     title: "{book['title']} — [Chapter/Part Title]"
     author: "{book['author']}"
     book_slug: "{book['slug']}"
     parent_hub: "[[README]]"
     note_type: summary-chapter
     tags: [insert-2-to-4-relevant-lowercase-tags]
     ```
   - `# {book['title']} — [Chapter/Part Title]` and `*By {book['author']}*`.
   - Comprehensive, deep summary of that specific part of the book:
     - **Thematic Deep-Dive**: In-depth analysis of the core principles, mental models, and author arguments.
     - **Frameworks & Mechanisms**: Detailed breakdown of formulas, loops, systems, and diagrams (Mermaid diagrams where helpful, LaTeX math for quantitative models).
     - **Evidence & Empirical Support**: Case studies, experiments, or historical events cited in the book.
     - **Implementation Protocols**: Concrete step-by-step action items and decision heuristics.
   - Rich internal wikilinks between the book's summary chapters and cross-references to foundational works.
   - EVERY concept chapter file MUST conclude with a dedicated `## 🧠 Active Recall & Knowledge Checks` section featuring 3 to 5 interactive Obsidian collapsible question callouts:
     ```markdown
     > [!QUESTION]- What is the core mechanism of [concept]?
     > **Direct Answer:** [Dense, precise explanation of the mechanism.]
     > 
     > **Key Implication:** [How to apply or recognize this in practice.]

     > [!QUESTION]- Why does [traditional belief] fail according to the author?
     > **Direct Answer:** [Evidence-backed rationale explaining the failure mode.]
     ```
   - The concluding chapter MUST additionally include `## ⚠️ Critical Limitations & Boundary Conditions` (where the author's model fails or does not apply) AND `## 🌉 Comparative Synthesis & Related Vault Works`.

STRICT FORMATTING & CLEANLINESS RULES:
- NO trailing horizontal rules (`---`) at the bottom of any file.
- NO outer ` ```markdown ` or ` ``` ` code fences wrapping file blocks.
- Exactly one blank line before and after headings, tables, callouts, and lists.
- Target total word count across all files: {min_words} to {max_words} words.
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_audio_tts_prompt(
    book: dict[str, str],
    sources: str,
) -> list[dict[str, str]]:
    user = f"""Create the definitive single-file Audio/TTS Listening Edition for "{book['title']}" by {book['author']}.

Book Metadata:
- Title: {book['title']}
- Author: {book['author']}
- Year: {book.get('first_published', book.get('published', ''))}
- Pillar: {book.get('pillar', '')}
- Category: {book.get('category', '')}
- Subcategory: {book.get('subcategory', '')}

Research sources & dossier:
{sources}

CRITICAL ANTI-HALLUCINATION DIRECTIVE:
Ground all spoken text strictly in the authentic published work. Do NOT invent fictional experiments or fake anecdotes. If this is a recent or specialized volume, clearly convey the author's primary thesis and verified core frameworks honestly.

TARGET AUDIENCE & TONE:
You are narrating a premium, long-form audio book summary for an intelligent, curious listener who wants deep, substantive understanding without academic jargon or shallow soundbites. The tone is conversational, authoritative, engaging, and clear.

FORMATTING REQUIREMENTS:
- Produce EXACTLY ONE complete markdown file starting with frontmatter.
- Frontmatter:
  ```yaml
  title: "{book['title']} — Audio Listening Edition"
  author: "{book['author']}"
  book_slug: "{book['slug']}"
  note_type: audio-listening-edition
  tags: [audiobook, audio-summary, spoken-edition]
  ```
- Use 5 to 7 clearly delineated narration parts with `#` and `##` headings:
  - `# 🎧 {book['title']} — Audio Listening Edition`
  - `## Part One: The Big Idea & Why It Matters`
  - `## Part Two: Core Principles & Mechanisms`
  - `## Part Three: Chapter Breakdowns & Key Arguments`
  - `## Part Four: Real-World Applications & Action Protocols`
  - `## Part Five: Critical Perspectives & Limitations`
  - `## Part Six: Final Synthesis & Core Takeaway`
- Write in pure, natural spoken English meant to be read aloud by TTS engines (e.g., ElevenLabs / EdgeTTS / OpenAI TTS).
- Avoid bulleted lists in the spoken body; use rhythmic, natural paragraphs with conversational transitions.
- Total spoken length: 1,500 to 3,000 words.
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_quiz_prompt(
    book: dict[str, str],
    sources: str,
) -> list[dict[str, str]]:
    user = f"""Create an interactive knowledge assessment quiz for "{book['title']}" by {book['author']}.

Book Metadata:
- Title: {book['title']}
- Author: {book['author']}
- Slug: {book['slug']}

Research Context:
{sources}

REQUIREMENTS:
- Produce a single file `Quiz.md` with frontmatter:
  ```yaml
  title: "{book['title']} — Knowledge Quiz"
  book_slug: "{book['slug']}"
  note_type: quiz
  tags: [quiz, assessment, active-recall]
  ```
- `# 🧩 {book['title']} — Knowledge Assessment Quiz`
- Include a valid interactive Obsidian quiz block:
  ```quiz
  book: {book['slug']}
  title: {book['title']} — Knowledge Quiz
  Q1. [Question testing core thesis]
  A) [Option A]
  B) [Option B]
  C) [Option C]
  D) [Option D]
  ANSWER: [A/B/C/D]
  EXPLANATION: [Clear explanation grounded in the book's concepts]

  Q2. [Question testing key mechanism]
  ...
  (Create 8 to 12 rigorous, multiple-choice questions spanning all major chapters)
  ```
- Follow the quiz block with a summary table of the key takeaways tested.
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_book_outline_prompt(
    book: dict[str, str],
    sources: str,
) -> list[dict[str, str]]:
    """Stage 1: Prompt LLM to design the authentic modular chapter outline for the book."""
    user = f"""Design the authentic, comprehensive structural outline and chapter division for "{book['title']}" by {book['author']}.

Book Metadata:
- Title: {book['title']}
- Author: {book['author']}
- Pillar: {book.get('pillar', '')}
- Category: {book.get('category', '')}
- Topic: {book.get('topic', '')}

Research dossier:
{sources}

OUTPUT REQUIREMENTS:
You MUST output a valid, clean JSON object (and nothing else) specifying the core thesis, top takeaways, and 3 to 5 thematic concept chapters.

JSON FORMAT:
```json
{{
  "thesis": "1-2 sentence definition of the core thesis and problem solved.",
  "transformation": "Why this matters and how it shifts the reader's paradigm.",
  "target_audience": "Who gains the highest ROI from this work.",
  "top_insights": [
    "Insight 1...",
    "Insight 2...",
    "Insight 3...",
    "Insight 4...",
    "Insight 5..."
  ],
  "chapters": [
    {{
      "index": 1,
      "filename": "01-[Specific-Thematic-Slug].md",
      "title": "01 · [Specific Thematic Title]",
      "focus": "One sentence summary of this chapter's mental models and protocols."
    }},
    {{
      "index": 2,
      "filename": "02-[Specific-Thematic-Slug].md",
      "title": "02 · [Specific Thematic Title]",
      "focus": "One sentence summary of this chapter's mental models and protocols."
    }},
    {{
      "index": 3,
      "filename": "03-[Specific-Thematic-Slug].md",
      "title": "03 · [Specific Thematic Title]",
      "focus": "One sentence summary of this chapter's mental models and protocols."
    }}
  ]
}}
```
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_chapter_concept_prompt(
    book: dict[str, str],
    chapter_info: dict[str, Any],
    outline: dict[str, Any],
    sources: str,
    target_words: int = 1000,
) -> list[dict[str, str]]:
    """Stage 2: Prompt LLM to write an in-depth standalone concept chapter note."""
    user = f"""Write the complete, authoritative, long-form concept chapter note for:
Chapter: {chapter_info.get('title', '')}
Filename: {chapter_info.get('filename', '')}
Book: "{book['title']}" by {book['author']}

Focus & Mental Models to cover:
{chapter_info.get('focus', '')}

Book Core Thesis Context:
{outline.get('thesis', '')}

Research dossier:
{sources}

FORMATTING REQUIREMENTS:
- Produce EXACTLY ONE complete markdown file starting with frontmatter:
  ```yaml
  title: "{book['title']} — {chapter_info.get('title', '')}"
  author: "{book['author']}"
  book_slug: "{book['slug']}"
  parent_hub: "[[README]]"
  note_type: summary-chapter
  tags: [insert-3-to-5-relevant-lowercase-tags]
  ```
- `# {book['title']} — {chapter_info.get('title', '')}`
- `*By {book['author']}*`
- `## 🧠 Core Mental Models & Frameworks` (Deep mathematical, cognitive, systemic, or strategic models with LaTeX math if quantitative).
- `## 🔬 Empirical Evidence & Case Studies` (Historical, psychological, or business experiments and verified proofs directly from the text).
- `## 🛠️ Step-by-Step Implementation Protocols` (Actionable checklists, heuristics, and decision frameworks).
- `## ⚠️ Critical Limitations & Edge Cases` (Where this mental model breaks down).
- `## 🧠 Active Recall & Knowledge Checks` (3 to 5 collapsible Obsidian question callouts: `> [!QUESTION]- ...`).
- Target length: {target_words} words. Dense, high-signal, university-grade rigor with zero conversational filler.
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_readme_hub_prompt(
    book: dict[str, str],
    outline: dict[str, Any],
    nav: dict[str, str] | None = None,
    graph: str | None = None,
) -> str:
    """Stage 3: Dynamically assemble the Master Hub README.md from the outline."""
    category = book["category"].replace(";", ",")
    navigation = ""
    if nav:
        navigation = f"""## 🧭 Navigation

| Direction | Link |
| :--- | :--- |
| **Previous Book** | {nav['prev']} |
| **Category Hub** | {nav['category']} |
| **Next Book** | {nav['next']} |"""

    book_links = _book_links(book["title"], book["author"])

    toc_rows = []
    for chap in outline.get("chapters", []):
        fn = chap.get("filename", "").replace(".md", "")
        title = chap.get("title", "")
        focus = chap.get("focus", "")
        toc_rows.append(f"| [[{fn}\\|{title}]] | {focus} |")

    toc_rows.append("| [[Audio-Listening-Edition\\|🎧 Audio Listening Edition]] | Complete spoken narration synthesis |")
    toc_rows.append("| [[Quiz\\|🧩 Knowledge Assessment Quiz]] | Active recall test with explanations |")
    toc_rows.append("| [[Flashcards\\|🎴 Active Recall Flashcards]] | Interactive recall deck |")
    toc_table = "\n".join(toc_rows)

    insights_bullets = "\n".join(f"- **Insight {i+1}**: {ins}" for i, ins in enumerate(outline.get("top_insights", [])))

    content = f"""---
title: "{book['title']}"
author: "{book['author']}"
first_published: {book.get('first_published', book.get('published', ''))}
latest_published: {book.get('latest_published', book.get('published', ''))}
published: {book.get('published', book.get('first_published', ''))}
pillar: "{book.get('pillar', '')}"
category: "{category}"
subcategory: "{book.get('subcategory', '')}"
topic: "{book.get('topic', '')}"
slug: "{book['slug']}"
difficulty: "{book.get('difficulty', 'Intermediate')}"
status: complete
note_type: book-summary
tags: [book-summary, executive-brief, {book['slug'].lower()}]
---

# {book['title']} — Complete Book Summary & Executive Guide

*By {book['author']} (First Published: {book.get('first_published', book.get('published', ''))}, Latest: {book.get('latest_published', book.get('published', ''))})*

## ⚡ Executive Summary & Value Proposition

- **The Central Premise**: {outline.get('thesis', '')}
- **The Transformation ("So What?")**: {outline.get('transformation', '')}
- **Core Audience & Applicability**: {outline.get('target_audience', '')}

### 🔑 Executive Takeaways (Top Insights)
{insights_bullets}

## 📑 Master Table of Contents

| Chapter | Summary Focus & Mental Models |
| :--- | :--- |
{toc_table}

## 📚 External References & Book Trackers
{book_links}

{navigation}
"""
    return content.strip() + "\n"

