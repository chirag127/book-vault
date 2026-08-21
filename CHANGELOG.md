# Changelog

## 2026-08-21 — gpt4free auto-benchmark, full provider chain, response caching

### Provider chain (tested live)
- Full fallback chain now: **Zen Ox Alpha Free** → **Zen Big Pickle** → **NVIDIA** (when key set) → **gpt4free auto** (last resort).
- Live tests: Zen `x-preview-f-free` HTTP 200 ✓ · NVIDIA `deepseek-ai/deepseek-v4-flash-0731` ✓ (100 words) · Zen `big-pickle` listed in `/models` but returns 429 for keyless direct access (paid tier) — pipeline backoff absorbs it and fails over to NVIDIA · gpt4free auto ✓ (best-ranked provider answered in ~1s).

### gpt4free auto-benchmark (`automation/g4f_client.py`)
- Benchmarks **every working text provider exactly once** (63 tested) with a real book prompt using g4f `model=""` auto mode; results (OK/FAIL, latency, words) cached per-provider in `automation/cache/g4f_providers.json`, ranked working-first-then-fastest, reused for `G4F_MAX_AGE_HOURS` (24).
- Generation tries ranked providers in order, one attempt each, until one returns content; auto mode falls back to a provider's first declared model when it rejects `model=""`.
- Result: 5 of 63 providers working — ranked **Groq → Gemini → CohereForAI_C4AI_Command → Yqcloud → Cloudflare**.
- Fixed console crash on non-ASCII provider error text (cp1252 safe).

### Response caching
- Every successful LLM response is cached at `automation/cache/llm/<slug>-<template-version>.json` and reused verbatim (verified: second call returns CACHED with no provider call). Cache lives in the repo, not gitignored.
- `generate.py` passes `cache_key` (book slug + `TEMPLATE_VERSION`) to `generate_markdown`; repair passes stay uncached.

### Config
- Added `OPENCODE_ZEN_BIGPICKLE_MODEL=big-pickle`, `G4F_ENABLED=on`, `G4F_MAX_AGE_HOURS=24` to `config.py`, `.env`, `.env.example`; upgraded `g4f` in `.venv`; `requirements.txt` updated.
- Stale pipeline processes stopped; stale lock cleared.

## 2026-08-21 — 12-pillar MECE taxonomy (Faceted / Hybrid system)

### Taxonomy restructure
- Replaced the 38-category tree with the **12-pillar MECE taxonomy**: Learning, Cognition & Meta-Skills · Thinking, Rationality & Mental Models · Psychology, Behavior & Neuroscience · Mathematics, Statistics & Quantitative Logic · Computer Science & Software Engineering · Artificial Intelligence & Data Systems · Economics, Markets & Investing · Business, Strategy & Enterprise · Leadership, Organizations & Management · Natural Sciences, Health & Biology · History, Geopolitics & Civilization · Philosophy, Ethics & Human Society.
- **Four-level classification** (Faceted / MECE Hybrid): Level 1 Pillar (folder) → Level 2 Category (folder, from each pillar's canonical non-overlapping sub-areas) → Level 3 Subcategory (front matter) → Level 4 Tags/Theme (front matter). Every book has exactly one primary pillar and category; reorganizing a topic now only edits YAML, never moves files.
- MECE mapping table in `automation/curriculum.py` maps all 38 old categories (and subcategories) into the 12 pillars; cross-pillar overrides re-home books properly (e.g. *Negotiation* → Leadership pillar, *SQL* → Data Engineering, *The Republic* → Political Philosophy, *Creative Act* → Life Design & Meaning). Verified: every pillar folder matches its canonical L2 list exactly — no foreign or single-book folders.
- All **775 books** placed; per-pillar counts 34–106 (balanced), 12 pillars / 98 categories.
- Removed the old 34-category and 38-category trees entirely (their content was superseded by the 12-pillar taxonomy).

### Faceted front matter + MOCs + template
- Note front matter now requires the faceted schema: `pillar`, `category`, `subcategory`, `topic`, `book_type` (Practical Guide / Theoretical Synthesis / Case Study / Biography / Memoir / Handbook / Reference / Academic Text), `read_status`, `reading_order_seq`, `next_reads`, `prerequisites`, `tags`; the validator enforces the enums.
- Added `MOCs/` — 12 pillar Maps of Content with live **Dataview** dashboards plus static tables (GitHub-friendly), and a `00-MASTER-INDEX`; `automation/build_docs.py` regenerates them.
- Added `templates/book-summary-template.md` with the full faceted front matter and the 3-layer note body (Source → Evaluation → Transfer).
- Regenerated `ALL-BOOKS.md` (grouped pillar → category), `READING-ORDER.md` (12-pillar sequence), `SUBCATEGORY-MAP.md`, `README.md`, `START-HERE.md`, `BOOK-MANIFEST.md`.
- Knowledge-graph coverage re-verified under the new taxonomy: **775/775 books have ≥3 computed related books**.

## 2026-08-21 — Canonical 2,000-book curriculum, knowledge-graph linking

### Curriculum (new canonical structure)
- Adopted the canonical 2,000-book curriculum as the single source of truth. Transcribed curriculum slots 001–800 into `automation/curriculum_data_1.py` / `curriculum_data_2.py`; the builder (`automation/curriculum.py`) generates `manifest.csv`, `taxonomy.py`, `SUBCATEGORY-MAP.md`, and category READMEs.
- **775 canonical books** across **38 categories** (800 slots − 25 duplicates removed; 6 vague/non-book entries replaced with real verified books).
- New taxonomy: 38 categories ordered as a learning sequence (Learning How to Learn → … → Biography and Case Studies), each with numbered subcategories.
- Old 34-category layout (11 notes) superseded so every book has exactly one canonical file; the removed trees were later deleted entirely (see the 12-pillar entry below).
- Regenerated `ALL-BOOKS.md` (775-row index) and `READING-ORDER.md` from the manifest via `automation/build_docs.py`; updated `README.md`, `START-HERE.md`, `BOOK-MANIFEST.md`.

### Knowledge-graph linking (per-book prompts)
- New `automation/graph.py` computes each book's link neighborhood from the full manifest: same-author works (with false-positive protection: Benjamin Graham ≠ Ronald Graham), same-subcategory peers, reading-order neighbors, and cross-category topic bridges (stemmed title tokens + same subcategory in other categories).
- Every note's prompt now includes this computed context and requires a `## Related Books` section with all computed wikilinks plus ≥3 wikilinks woven into prose; the validator enforces ≥3 wikilinks. **100% of the 775 books have ≥3 computed related books.**
- Fixed slug generation (apostrophes, `!`/`?`) so slugs are clean (`Let's Talk Money` → `Lets-Talk-Money`).

## 2026-08-21 — Restructure, provider chain, and long-running automation

### Structure
- Consolidated the vault: all 34 category folders now live under `md/` at the repository root (`md/01-How-to-Read-and-Learn/...`), keeping category → subcategory nesting.
- Updated every root navigation file and the automation manifest paths to the `md/` layout.
- Added `ALL-BOOKS.md` (master index), `CHANGELOG.md`, and `VALIDATION-REPORT.md`.
- Added the subcategory **Note-Taking and Knowledge Management** to category 01.

### Content
- Added 2 essential books to the manifest (status: planned):
  - [[How-to-Take-Smart-Notes|How to Take Smart Notes]] — Sönke Ahrens (2017)
  - [[Building-a-Second-Brain|Building a Second Brain]] — Tiago Forte (2022)
- Raised summary size targets: the prompt now pushes new notes toward 4,000–8,000 words (up to 15,000 for foundational works); validator max raised to 15,000 words.

### Automation (Python-only)
- **Provider chain**: OpenCode Zen **Ox Alpha Free** (`x-preview-f-free`, free and keyless) is now the primary model; NVIDIA (`deepseek-ai/deepseek-v4-flash-0731`) is the automatic fallback when `NVIDIA_API_KEY` is set. New `automation/llm_client.py` replaces `nvidia_client.py`; Zen is called over plain HTTP with no Authorization header (the Zen free endpoint rejects one).
- **Robust long runs**: `--limit` now counts *pending* books only (repeated runs always progress); new `--loop --sleep` mode keeps generating until the manifest is exhausted and reloads the manifest each pass; a single-instance lock prevents two pipelines from generating the same book; every backend failure is contained per book so a rate limit never kills the batch.
- **Self-repair**: notes that fail validation are sent back to the model with the exact error list (up to 2 repair passes) instead of being permanently stuck.
- **Search**: added YaCy local-peer backend (`YACY_SEARCH=on`, `YACY_URL`); hardened `ddgs` with retry and graceful fallback; search queries include author names.
- **Validation**: drafts are no longer blocked by the sources-URL check; `validate_vault` now detects duplicate book files.
- Created project `.venv` and installed `requirements.txt` (includes `ddgs`).

### Validation
- All 11 existing book notes pass structural validation; no duplicate book files.
- 3 books pending generation: Thinking in Bets, How to Take Smart Notes, Building a Second Brain.
