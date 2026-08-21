"""Interactive CLI tool to Chat with the Book Vault using LLM and semantic search."""
from __future__ import annotations

import argparse
import sys
from ..core.config import ROOT, load_settings
from ..core.manifest import load_manifest
from ..engines.llm_client import call_llm
from ..search.vault_search import search_vault


def ask_vault(query: str) -> str:
    settings = load_settings()
    manifest_books = load_manifest(ROOT / "automation" / "manifest.csv")
    
    # 1. Search relevant notes in vault
    results = search_vault(query, top_k=4)
    context_blocks = []
    
    for r in results:
        context_blocks.append(f"--- BOOK: {r.book_title} (Pillar: {r.pillar}) ---\n{r.matched_text[:800]}")
    
    context_str = "\n\n".join(context_blocks) if context_blocks else "No direct matching notes found."
    
    prompt = f"""You are the Universal Book Vault AI Assistant, an expert on 775 canonical books across 12 knowledge pillars.
Answer the user's question accurately, citing specific books, mental models, and author insights based on the vault knowledge below.

VAULT KNOWLEDGE BASE:
{context_str}

USER QUESTION:
{query}

Provide a structured, insightful answer with markdown bullet points and book wikilinks (e.g. [[Book-Title]]):"""

    print(f"\n🧠 Synthesizing answer across vault for: '{query}'...\n", flush=True)
    response = call_llm(
        prompt=prompt,
        settings=settings,
        model="x-preview-f-free",
        provider_name="zen",
    )
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description="Chat with your Book Vault")
    parser.add_argument("query", nargs="*", help="Question to ask your vault")
    args = parser.parse_args()

    q = " ".join(args.query).strip() if args.query else ""
    if not q:
        q = input("Ask a question across your Book Vault: ").strip()
    
    if q:
        answer = ask_vault(q)
        print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
