# Python Book Automation

Python is the sole automation runtime for this vault. No Node, shell-only, or other-language automation is used.

## The curriculum pipeline

The vault is driven by the canonical 2,000-book curriculum. Rebuild the machine-readable manifest from the transcribed curriculum, then regenerate the index docs, before generating notes:

```bash
.venv/Scripts/python -m automation.curriculum   # manifest.csv + taxonomy.py + SUBCATEGORY-MAP.md + category READMEs
.venv/Scripts/python -m automation.build_docs   # ALL-BOOKS.md + READING-ORDER.md
```

- Curriculum source: `automation/curriculum_data_1.py` (001–400) and `automation/curriculum_data_2.py` (401–800). Each entry is `(number, priority, category, subcategory, title, author)`.
- The builder deduplicates (title + author-surname key), flags vague entries, maps every book into the **12-pillar MECE taxonomy** (four levels: Pillar → Category → Subcategory → Tags), and writes `automation/manifest.csv` — currently **775 canonical books** across **12 pillars / 98 categories**.
- Add books by appending entries to the curriculum data files, re-running the two commands above; the loop mode picks new rows up automatically.

`automation/build_docs.py` also regenerates `ALL-BOOKS.md`, `READING-ORDER.md`, the 12 pillar **Maps of Content** (`MOCs/`) with Obsidian Dataview queries plus static tables, and `templates/book-summary-template.md` (faceted front matter: pillar, category, subcategory, topic, book_type, read_status, reading_order_seq, next_reads).

## Knowledge-graph linking

Before every note is generated, `automation/graph.py` computes the book's link neighborhood from the whole manifest: same-author works, same-subcategory peers, reading-order neighbors (previous/next curriculum numbers), and cross-category topic bridges. The prompt requires a `## Related Books` section with every computed wikilink plus at least three wikilinks woven into the prose, and the validator rejects a note with fewer than three wikilinks — so the vault stays a connected graph even before all books exist. Every one of the 775 books currently has at least three computed related books.

## What it does

- Reads the canonical manifest at `automation/manifest.csv` (one row per book).
- Researches each book with free search backends: YaCy (local peer) → Dokobot (optional) → `ddgs` → standard-library DuckDuckGo HTML.
- Generates the Markdown note with the provider chain: OpenCode Zen **Ox Alpha Free** (free, keyless) → Zen **Big Pickle** (keyless) → **NVIDIA** (when `NVIDIA_API_KEY` is set) → **gpt4free auto** (best-ranked community provider, last resort).
- Validates every note against a universal core before writing it atomically (`*.md.tmp` → rename).
- Stores each book under `md/<Pillar>/<NN-Category>/<Slug>.md` (four-level classification: Pillar → Category → Subcategory → Tags).
- Skips books whose note already has `status: complete` unless `--force` is used, so repeated or long-running runs never duplicate work.
- A single-instance lock prevents two concurrent pipeline runs from generating the same book.

## Install

```bash
python -m venv .venv
# Windows:
.venv/Scripts/python -m pip install -r requirements.txt
# macOS / Linux:
.venv/bin/python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and review the settings. The default setup needs **no API key at all**: Zen's Ox Alpha Free model answers keyless, and gpt4free auto provides the last-resort fallback. Add an `NVIDIA_API_KEY` only if you want the NVIDIA fallback (or want NVIDIA as primary via `PRIMARY_PROVIDER=nvidia`).

## Security

Never put a real API key in source code or chat. Keep any NVIDIA key only in `.env` (gitignored). Ox Alpha Free is zero-retention; the free NVIDIA endpoints are trial-only and log usage for security purposes.

## Staged execution

First run a plan without API calls:

```bash
python -m automation.generate --limit 1 --dry-run
```

Then generate one new manifest entry:

```bash
python -m automation.generate --slug Thinking-in-Bets --limit 1
```

Validate the vault:

```bash
python -m automation.validate_vault
```

Then use progressively larger resumable batches. `--limit` now counts *pending* books only, so repeating the same command always makes progress:

```bash
python -m automation.generate --limit 5
python -m automation.validate_vault
python -m automation.generate --limit 25
```

## Sequential processing and rate limiting

The pipeline is strictly **sequential — one book at a time, no concurrency, and no artificial sleeps**. It never waits "just in case"; it only sleeps when something actually needs waiting:

- **LLM calls** (Zen → Zen Big Pickle → NVIDIA → gpt4free): exponential backoff + jitter on HTTP 429 and temporary 5xx errors (roughly 3s, 6s, 12s, 24s, 48s, capped ~120s). When the primary provider is exhausted or fails hard, the pipeline automatically falls back to the next provider in the chain — it cannot get permanently rate-limited.
- **Search backends** (YaCy → ddgs → stdlib): each retries with exponential backoff (ddgs: 3s, 6s; stdlib and page fetches: 2s, 4s) and degrades to the next backend without crashing the batch.
- **Between books and between loop passes**: no sleep at all — the next book starts immediately after the previous one finishes.

## Provider chain, gpt4free auto-benchmark, and caching

Provider order: **1. Zen Ox Alpha Free** → **2. Zen Big Pickle** → **3. NVIDIA** (only if a real key is in `.env`) → **4. gpt4free auto** (last resort).

- **gpt4free auto**: `G4F_ENABLED=on` (default) benchmarks every working text provider **exactly once** with a real book prompt using g4f's `model=""` auto mode (best available model per provider). Results — OK/FAIL, latency, word count — are cached in `automation/cache/g4f_providers.json` and ranked (working first, then fastest). Generation then tries the ranked providers in order, one attempt each, until one returns content. A completed benchmark is reused for 24h (`G4F_MAX_AGE_HOURS`).
- **Response cache**: every successful LLM response is stored at `automation/cache/llm/<key>.json` (key = book slug + template version) and reused verbatim on later runs — no book is ever generated twice, even after a crash or restart.
- Both caches live inside the repo (not gitignored) so the benchmark and every generated response are preserved.

## Verbose output

## Verbose output

The pipeline prints **every step** of every book to the console, so a long run is fully observable:

```
======================================================================
PIPELINE START (sequential — one book at a time, no concurrency)
  manifest   : automation/manifest.csv
  providers  : zen (x-preview-f-free) -> zen-bigpickle (big-pickle) -> nvidia (deepseek-ai/deepseek-v4-flash-0731) + g4f auto
  word gate  : 2500–15000
  backoff    : exponential + jitter on every 429/5xx/network error (no artificial sleeps)
  loop mode  : yes (continuous, no sleep between passes)
======================================================================

--- BOOK 1/1 | #001 | Make It Stick | Learning, Cognition & Meta-Skills > Learning Science & Cognitive Load ---
  [1/4] research: searching the web for 'Make It Stick' by Peter C. Brown; Henry L. Roediger III; Mark A. McDaniel
        running 9 search queries (all include title + author name)
        SEARCH (ddgs): 8 hits for '"Make It Stick" "Peter C. Brown..." official publisher author site'
        [1/9] '"Make It Stick" ... official publisher author site' -> 2 new unique source(s)
        ...
        sources kept: 12 (deduplicated, publisher/author sites first)
  [2/4] generating note (target 4000-15000 words, graph context: 14 related books)
        LLM: trying provider 1/2: zen (x-preview-f-free)
        LLM zen: HTTP 200 OK, 4382 words
        generated 4382 words
  [3/4] validation: PASS (0 issues)
  [4/4] WROTE md/01-Learning-Cognition-and-Meta-Skills/01-Learning-Science-Cognitive-Load/Make-It-Stick.md (4382 words)
```

Any retry, backoff, provider fallback, repair pass, or quality stop is printed with its reason — nothing happens silently.

## Running for days

To keep generating until the manifest is exhausted (new rows added to `manifest.csv` are picked up on later passes), run in loop mode — one book at a time, continuously, with **no sleep between books**:

```bash
python -m automation.generate --limit 1 --loop
```

In **cmd**:

```bat
python -m automation.generate --limit 1 --loop
```

In **PowerShell**:

```powershell
python -m automation.generate --limit 1 --loop
```

To run it detached so it survives the terminal closing, use PowerShell `Start-Process`:

```powershell
Start-Process -WindowStyle Hidden -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m","automation.generate","--limit","1","--loop"
```

Ctrl-C (or `Stop-Process` for the hidden run) stops it cleanly between passes; the lock releases automatically. Restarting resumes exactly where it stopped because complete notes are skipped — and partially generated drafts are reused instead of regenerated. If you want more than one book per pass (still sequential, no sleep), raise `--limit` — e.g. `--limit 10` processes ten books per pass, one after the other.

The pipeline is idempotent: books with `status: complete` are skipped unless `--force`; the single-instance lock prevents two runs from generating the same book; every write is atomic.

Completed notes are skipped unless `--force` is used. `--no-web` produces a `draft` note with a clearly labeled research-needed section when search backends are unavailable.

## Search backends

Python search order: YaCy (if `YACY_SEARCH=on` and a peer runs at `YACY_URL`) → Dokobot (if `DOKO_SEARCH=on`) → `ddgs` → stdlib DuckDuckGo HTML.

- YaCy: https://github.com/yacy/yacy_search_server — self-hosted, no external rate limits, ideal for long runs.
- ddgs: https://github.com/deedy5/ddgs — free DuckDuckGo client (`pip install ddgs`).

This is not a promise of unlimited search. Respect provider terms, rate limits, and robots rules. If no reliable research is available, the pipeline stops for that book instead of marking it complete.

## Flexible note structure

The generator does not force every book into the same section order. A technical book can use definitions, algorithms, assumptions, examples, and failure modes. A biography can use chronology, turning points, context, decisions, and legacy. A philosophy book can use concepts, arguments, objections, and implications. A business book can use framework, evidence, implementation, and case analysis.

Every complete note still needs:

- Valid front matter.
- A clear title and explanation of the book.
- The book's central argument or governing question.
- Evidence or source discussion.
- Strengths and contributions.
- Weaknesses, criticism, limitations, or counterarguments.
- Exactly five memorable points.
- A TTS-friendly recap.
- Sources and navigation.
