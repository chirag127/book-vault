# Book Vault — Agent Instructions (OpenCode 2)

## Project Overview
Personal knowledge-management system generating long-form book summaries in Obsidian Markdown.
Pipeline: manifest.csv → research.py (4 search backends) → generate.py (Zen LLM) → validate.py → md/

## Quick Commands
| Task | Command |
|---|---|
| Generate 1 book | `python -m automation.generate --slug Make-It-Stick` |
| Batch (10 books) | `python -m automation.run_pipeline --phase batch --limit 10` |
| Validate vault | `python -m automation.validate_vault` |
| Benchmark models | `python -m automation.zen_bench` |
| Run all tests | `pytest tests/ -v` |
| Smoke test | `python -m automation.run_pipeline --phase smoke` |

## Pipeline Architecture
- `automation/config.py` — single source of truth for all settings (Settings dataclass)
- `automation/llm_client.py` — Zen free fallback chain (11 models), tenacity 20-retry Ox Alpha
- `automation/research.py` — DDGS + OpenLibrary + Crossref + Wikipedia parallel search
- `automation/search_clients.py` — 4 free search clients with diskcache TTL
- `automation/length.py` — adaptive word bounds per book depth/genre
- `automation/validate.py` — YAML frontmatter + word count + structure validation

## Taxonomy (3-Level Hierarchy)
- 3 levels: L1 Pillar (12) → L2 Category (max 12) → L3 Subcategory (max 12)
- Path: `md/{LL-NN-SS}/Book-Slug.md` (numbers spaced with gaps for future insertions)
- Every L3 must have ≥ 1 book. Max 12 items per level.

## Coding Standards
- Python: `from __future__ import annotations` on every file
- Markdown: All `.md` files (book summaries, MOCs, docs) MUST strictly follow markdownlint rules (standard heading hierarchy, proper blank lines around blocks, fenced code blocks with language indicators, correct list formatting, no trailing whitespace, single trailing newline).
- All new settings go in `automation/core/config.py` Settings dataclass + `.env`
- Never use `pickle`, `shelve`, or global mutable state
- Tests in `tests/` using `pytest` + `respx` for HTTP mocking


## Do Not
- Never edit `manifest.csv` by hand (use `python -m automation.curriculum`)
- Never commit `.env` with real API keys
- Never write book notes outside the `md/` directory
- Never increase PIPELINE_WORKERS above 10 on the free Zen tier
