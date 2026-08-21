# Universal Book Vault

![Universal Book Vault icon](_assets/book-vault-icon.svg)

> A researched, interconnected reading system organized by learning dependency rather than alphabetic order — built from a canonical 2,000-book curriculum.

## Start here

1. Begin with [[md/01-Learning-Cognition-and-Meta-Skills/README|Learning, Cognition & Meta-Skills]] — the vault opens with how to read, take notes, and learn.
2. Follow the 12-pillar sequence in [[READING-ORDER]].
3. Explore the four-level classification in [[SUBCATEGORY-MAP]].
4. Browse the live dashboards in [[MOCs/00-MASTER-INDEX|MOCs]] (Obsidian Dataview) or the static catalog in [[ALL-BOOKS]].
5. Use [[START-HERE]] for a quick goal-based route.

## Four-level classification (Faceted / MECE)

Every book gets exactly one canonical home, and every dimension beyond that is captured as metadata, not folders:

1. **Level 1 — Pillar:** one of 12 mutually-exclusive master domains → `md/0X-<Pillar>/`
2. **Level 2 — Category:** the pillar's non-overlapping sub-areas → `md/0X-<Pillar>/NN-<Category>/`
3. **Level 3 — Subcategory:** the book's finer topic (front matter + manifest)
4. **Level 4 — Tags / Theme:** free-form `tags`, `book_type`, `difficulty`, `read_status` — the faceted search surface used by Dataview MOCs

Reorganizing a topic never moves a file: it only changes YAML metadata. The 12 pillars are **Learning, Cognition & Meta-Skills · Thinking, Rationality & Mental Models · Psychology, Behavior & Neuroscience · Mathematics, Statistics & Quantitative Logic · Computer Science & Software Engineering · Artificial Intelligence & Data Systems · Economics, Markets & Investing · Business, Strategy & Enterprise · Leadership, Organizations & Management · Natural Sciences, Health & Biology · History, Geopolitics & Civilization · Philosophy, Ethics & Human Society.**

## Learning principle

The vault starts with the skill of reading and learning well, then develops reasoning and mental models, quantitative foundations, technical capability, financial and organizational understanding, health and the physical world, societies and power, and finally philosophy, biography, and future-oriented thinking. Books are ordered inside each pillar by curriculum number.

## Vault conventions

- One canonical book equals one Markdown file (currently **775 books**).
- Every book belongs to exactly one primary pillar and one primary category.
- Every note carries a `## Related Books` section with at least three computed wikilinks (same author, same category, reading-order neighbors, cross-pillar topic bridges) plus `next_reads` front matter — the vault is a knowledge graph, not a folder of isolated files.
- Book notes use faceted front matter, source lists, limitations and criticism, practical applications, and text-to-speech-friendly recaps.
- Fiction is excluded by default and documented separately in [[EXCLUDED-FICTION]].
- The canonical catalog is maintained in [[BOOK-MANIFEST]] and regenerated from the curriculum by `automation/curriculum.py`.

## Production scope

The vault is built from the canonical 2,000-book curriculum; the current manifest holds 775 verified entries (slots 001–800 after deduplication). Summaries use maximum-depth treatment: normally 4,000–8,000 words, longer for foundational or technically complex works. Influential but controversial works are retained with explicit evidence, criticism, and limitations.

The generation pipeline is fully automated in Python: web research (with author names in every query, deduplicated sources) → LLM generation via OpenCode Zen (Ox Alpha Free, keyless) with NVIDIA fallback and exponential backoff → validation → self-repair → atomic write. It runs for days unattended, one book at a time or concurrently, and never creates a duplicate file. See [[automation/README|automation/README.md]] for commands.

See [[OBSIDIAN-SETUP]] for TTS, front matter, plugin, and cross-platform Markdown conventions.
