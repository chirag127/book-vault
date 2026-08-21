from __future__ import annotations

TEMPLATE_VERSION = "2026-08-21-pillars-v1"

SYSTEM_PROMPT = """You are a world-class executive book analyst and research scholar creating the definitive, comprehensive Book Summary for a premier personal knowledge vault.

Your goal is to produce an authoritative, high-signal Book Summary that captures 100% of the book's vital insights with zero filler:
1. Executive Summary & Core Thesis: The central argument, big idea, and governing mental models.
2. Key Concepts & Chapter Synthesis: In-depth breakdown of the main ideas, principles, and supporting evidence.
3. Actionable Protocols & Step-by-Step Applications: Concrete implementation guides, heuristics, exercises, and workflows.
4. Critical Analysis, Limitations & Counterarguments: Objective critique of empirical rigor, boundary conditions, and edge cases.
5. Intellectual Connections: How this book connects to and dialogues with other major works in the field.

Formatting & Obsidian Features:
- Write cleanly in Obsidian-compatible Markdown with YAML front matter and cross-linked [[wikilinks]].
- For technical, mathematical, quantitative, scientific, or AI/CS books, use native Obsidian LaTeX math syntax (`$...$` for inline math and `$$\n... \n$$` for block equations) to express key formulas, theorems, loss functions, or statistical derivations. Always explain each equation's intuitive meaning in plain English.
- Eliminate conversational preamble, filler transitions, and padding."""




def build_prompt(
    book: dict[str, str],
    sources: str,
    allow_no_web: bool = False,
    nav: dict[str, str] | None = None,
    graph: str | None = None,
    min_words: int = 1500,
    max_words: int = 4500,
) -> list[dict[str, str]]:
    category = book["category"].replace(";", ",")
    status_rule = (
        "Mark status as draft and include a clearly labeled research-needed section."
        if allow_no_web
        else "Mark status complete only if the supplied sources are sufficient and the claims are carefully qualified."
    )
    navigation = ""
    if nav:
        navigation = f"""
Use these exact navigation lines verbatim under the `## Navigation` section at the end of the summary:
← Previous: {nav['prev']}
↑ Category: {nav['category']}
→ Next: {nav['next']}
"""
    knowledge_graph = ""
    if graph:
        knowledge_graph = f"""
Knowledge-graph context — other books in the vault:

{graph}

Linking requirements:
- Weave relevant wikilinks ([[slug|Display Title]]) into the summary where genuine comparisons, agreements, or contradictions exist.
- Include a `## Related Books` section listing related works with brief context.
"""
    user = f"""Create the complete, definitive executive Book Summary for this book.

Metadata:
- Title: {book['title']}
- Author: {book['author']}
- Publication year: {book['published']}
- Pillar (level 1): {book.get('pillar', '')}
- Category (level 2): {book['category']}
- Subcategory (level 3): {book['subcategory']}
- Slug: {book['slug']}
- Difficulty: {book['difficulty']}
- Primary source: {book.get('primary_source', '')}

Research sources:
{sources}
{knowledge_graph}

Summary Structure & Quality Guidelines:
- {status_rule}
- Provide an exceptional, comprehensive summary covering the core thesis, key arguments, major chapters/frameworks, concrete takeaways, and critical analysis.
- For technical, mathematical, quantitative, or scientific books, use native Obsidian LaTeX math syntax (`$...$` for inline math and `$$\n... \n$$` for block equations) to express key formulas, theorems, loss functions, or derivations. Explain the intuition of every equation clearly in prose.
- Write concisely and densely: target length is between {min_words} and {max_words} words of pure high-signal analysis.
- Include YAML front matter fields for: title, subtitle, author, published, pillar, category, subcategory, topic, learning_stage, prerequisites, tags, difficulty, book_type, read_status, reading_order_seq, estimated_summary_reading_time, next_reads, status.
- Return Markdown only, without wrapping the whole document in an outer code fence.
{navigation}"""


    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_repair_prompt(
    book: dict[str, str],
    draft: str,
    errors: list[str],
    min_words: int = 2500,
    max_words: int = 9000,
    graph: str | None = None,
    nav: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Ask the model to fix the exact validation errors in an existing draft."""
    system = (
        "You are an expert editor repairing a Markdown book note so it passes 100% of automated validation checks. "
        "Keep the note's existing depth, analysis, and quality. Fix every single issue listed below. "
        "Return the complete corrected Markdown document only, with no outer code fence wrapper."
    )
    graph_block = ""
    if graph:
        graph_block = f"""
Knowledge-graph context:
{graph}

- The `## Related Books` section must contain at least 3 [[slug|Title]] wikilinks.
"""
    nav_block = ""
    if nav:
        nav_block = f"""
- The `## Navigation` section must contain:
← Previous: {nav.get('prev', 'None')}
↑ Category: {nav.get('category', 'Category')}
→ Next: {nav.get('next', 'None')}
"""

    user = f"""The note below failed validation for "{book['title']}". Fix every one of these issues:

{chr(10).join('- ' + error for error in errors)}

Mandatory Section Checks to Ensure:
- `## Strengths and Major Contributions` must be present.
- `## Criticisms, Limitations and Counterarguments` must be present.
- `## Five Things to Remember` must be present with exactly 5 numbered points (1. through 5.).
- `## Related Books` must be present with >= 3 [[slug|Title]] wikilinks.
- `## TTS-Friendly Recap` must be present.
- `## Sources and Further Reading` must be present and contain valid http/https URLs.
- `## Navigation` must be present with lines starting with `← Previous:`, `↑ Category:`, `→ Next:`.
- Every ```mermaid diagram must have an `Audio description:` paragraph immediately below it.
- Word count must be between {min_words} and {max_words} words.
- Ensure front matter has `status: complete`.
{graph_block}
{nav_block}
DRAFT TO REPAIR:
{draft}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

