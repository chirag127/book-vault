from __future__ import annotations

TEMPLATE_VERSION = "2026-08-21-pillars-v1"

SYSTEM_PROMPT = """You are a world-class executive book analyst and research scholar creating the definitive, comprehensive Book Summary for a premier personal knowledge vault.

Your goal is to produce an authoritative, high-signal Book Summary that captures 100% of the book's vital insights with zero filler:
1. Executive Summary & Core Thesis: The central argument, big idea, and governing mental models.
2. Key Concepts & Chapter Synthesis: In-depth breakdown of the main ideas, principles, and supporting evidence.
3. Actionable Protocols & Step-by-Step Applications: Concrete implementation guides, heuristics, exercises, and workflows.
4. Critical Analysis, Limitations & Counterarguments: Objective critique of empirical rigor, boundary conditions, and edge cases.
5. Intellectual Connections: How this book connects to and dialogues with other major works in the field.

Obsidian & Visual Markdown Capabilities:
- Obsidian Callouts: Use appropriate callout boxes (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!EXAMPLE]`, `> [!QUOTE]`) to highlight key takeaways, critical warnings, or memorable author quotes.
- Visual Mermaid Diagrams: When explaining complex systems, processes, loops, or decision trees, use Mermaid diagrams (```mermaid ... ```).
- Structured Comparison Tables: Use Markdown tables to compare strategies, pros/cons, phases, or theoretical models.
- LaTeX Math Blocks: For quantitative, mathematical, statistical, or AI/CS books, use Obsidian LaTeX math (`$...$` for inline math, `$$\n...\n$$` for block formulas). Explain every equation in clear prose.
- Action Checklists: Use `- [ ]` markdown task items for implementation protocols and actionable habits.
- Bidirectional Wikilinks: Cross-link related concepts and books with `[[slug|Display Title]]`.
- Eliminate conversational preamble, filler transitions, and padding."""


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
        navigation = f"""
Navigation links:
← Previous: {nav['prev']}
↑ Category: {nav['category']}
→ Next: {nav['next']}
"""
    knowledge_graph = ""
    if graph:
        knowledge_graph = f"""
Knowledge-graph context:
{graph}
"""

    user = f"""Create the complete, modular multi-file Reading Edition for "{book['title']}" by {book['author']}.

Book Metadata:
- Title: {book['title']}
- Author: {book['author']}
- Publication year: {book['published']}
- Pillar: {book.get('pillar', '')}
- Category: {book['category']}
- Subcategory: {book['subcategory']}
- Slug: {book['slug']}
- Difficulty: {book['difficulty']}

Research sources:
{sources}
{knowledge_graph}

DYNAMIC MODULARIZATION ARCHITECTURE:
You have full editorial autonomy to decide the optimal number of modular chapter/concept files (between 2 to 7 files) and their exact contextual filenames based on this book's specific genre, thesis, and structure (e.g., historical periods, mathematical proofs, business case studies, or cognitive frameworks).

Requirements:
1. Always start with === FILE: README.md === (The Hub):
   - YAML front matter (`title`, `author`, `published`, `pillar`, `category`, `subcategory`, `slug`, `difficulty`, `tags: [book-summary, mental-models]`, `status: complete`).
   - `# {book['title']} — Executive Summary & Reading Guide`
   - `*By {book['author']} ({book['published']})*`
   - `> [!ABSTRACT] One-Sentence Core Thesis` (High-density distillation of the main truth).
   - `## 🧠 Core Mental Models & Big Picture` (Underlying paradigms and cognitive shifts).
   - `## ⚡ 3 Key Actionable Takeaways` (Top 3 distilled bullet points).
   - `## 🚀 30-Day Action & Implementation Protocol` (Concrete weekly checklist of what to do differently).
   - `## 💡 Golden Quotes & Memorable Passages` (> [!QUOTE] callouts).
   - Master Table of Contents with Markdown links to EVERY modular chapter file you decide to create (e.g. `./01-Mental-Models.md`, `./02-Cognitive-Biases.md`...) + link to `[[Audio-Listening-Edition|🎧 Audio Listening Edition]]`.
   - `## 📚 External References & Book Trackers` with markdown links to Open Library, Goodreads, Google Books, Hardcover, and StoryGraph search queries for this book.
   - {navigation}

2. Generate 2 to 6 Contextual Chapter/Concept Files (The Spokes):
   - Format: `=== FILE: 01-[Contextual-Name].md ===`, `=== FILE: 02-[Contextual-Name].md ===`, etc.
   - EVERY file must begin with YAML front matter (`title`, `author`, `book_slug`), followed by `# {book['title']} — [Chapter/Concept Name]` and `*By {book['author']}*`.
   - Focus on deep, high-signal explanation of that specific topic/phase/framework.
   - One of the practical/action chapters MUST include a section titled `## Active Recall & Spaced Repetition Flashcards` with 3 to 5 `Q: ... ? / A: ...` pairs.
   - The final chapter should cover critical analysis, boundary conditions, and `## Related Books` wikilinks.


Quality Guidelines:
- High-signal density, no fluff, no repetitive filler.
- Use Callouts (`> [!TIP]`, `> [!IMPORTANT]`, `> [!QUOTE]`), Tables, Checklists, and LaTeX where relevant.
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
- Year: {book['published']}
- Category: {book.get('category', '')}

Research sources:
{sources}

Audio/TTS Script Guidelines:
1. Written specifically for spoken voice narration and Text-to-Speech (TTS) listening apps.
2. Natural, engaging spoken prose with conversational transitions ("In this opening section...", "The pivotal takeaway here is...").
3. DO NOT include Markdown tables, ASCII diagrams, raw bullet symbols, or visual formatting that sounds awkward when read aloud by a screen reader.
4. Structure the audio script into clearly spoken narration sections:
   - Part 1: Welcome & Executive Core Thesis
   - Part 2: The Key Frameworks Explained
   - Part 3: Real-World Applications & Practical Protocols
   - Part 4: Critical Perspectives & What to Watch Out For
   - Part 5: Final Summary & Takeaway
5. Start with YAML frontmatter:
---
title: "{book['title']} (Audio Listening Edition)"
author: "{book['author']}"
published: {book['published']}
book_slug: "{book['slug']}"
edition: "Audio-TTS"
status: complete
---

# {book['title']} — Audio Listening Edition
*By {book['author']}*


Length: 1,200 to 2,500 spoken words of smooth, engaging audio narration.
"""
    return [
        {"role": "system", "content": "You are a master audiobook narrator and audio scriptwriter creating a seamless spoken-word audio edition of a book summary for TTS listening."},
        {"role": "user", "content": user},
    ]


def build_prompt(
    book: dict[str, str],
    sources: str,
    allow_no_web: bool = False,
    nav: dict[str, str] | None = None,
    graph: str | None = None,
    min_words: int = 1500,
    max_words: int = 4500,
) -> list[dict[str, str]]:
    return build_modular_reading_prompt(book, sources, allow_no_web, nav, graph, min_words, max_words)


