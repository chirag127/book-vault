# Universal Book Vault

![Universal Book Vault icon](_assets/book-vault-icon.svg)

> A researched, interconnected reading system organized by learning dependency rather than alphabetic order — built from a canonical 2,000-book curriculum.

## Start here

1. Open the interactive **[[MOCs/VAULT-DASHBOARD|📊 Vault Dashboard]]** for live reading progress and audio edition toggles.
2. Explore the **[[MOCs/00-MASTER-INDEX|🗺️ Master Maps of Content]]** across all 12 Knowledge Pillars.
3. Explore the **12 Visual Canvas Mind-Maps** (e.g. `[[01-Learning-Cognition-and-Meta-Skills.canvas]]`).
4. Track reading progress in the **[[MOCs/READING-KANBAN|📋 Reading Kanban Pipeline]]**.
5. Launch overnight batch generation in PowerShell: `powershell -ExecutionPolicy Bypass -File "run_overnight.ps1"`

## Four-level classification (Faceted / MECE)

Every book gets exactly one canonical home, and every dimension beyond that is captured as metadata, not folders:

1. **Level 1 — Pillar:** one of 12 mutually-exclusive master domains → `md/0X-<Pillar>/`
2. **Level 2 — Category:** the pillar's non-overlapping sub-areas → `md/0X-<Pillar>/NN-<Category>/`
3. **Level 3 — Subcategory:** the book's finer topic (front matter + manifest)
4. **Level 4 — Tags / Theme:** free-form `tags`, `book_type`, `difficulty`, `read_status` — the faceted search surface used by Dataview MOCs

Reorganizing a topic never moves a file: it only changes YAML metadata. The 12 pillars are **Learning, Cognition & Meta-Skills · Thinking, Rationality & Mental Models · Psychology, Behavior & Neuroscience · Mathematics, Statistics & Quantitative Logic · Computer Science & Software Engineering · Artificial Intelligence & Data Systems · Economics, Markets & Investing · Business, Strategy & Enterprise · Leadership, Organizations & Management · Natural Sciences, Health & Biology · History, Geopolitics & Civilization · Philosophy, Ethics & Human Society.**

## Learning principle

The vault starts with the skill of reading and learning well, then develops reasoning and mental models, quantitative foundations, technical capability, financial and organizational understanding, health and the physical world, societies and power, and finally philosophy, biography, and future-oriented thinking.

## Vault conventions

- One canonical book equals one modular directory with atomic PKM concept notes and an audio listening edition.
- Every book belongs to exactly one primary pillar and one primary category.
- Every note carries rich bidirectional wikilinks to related concept notes and cross-domain bridges.
- Book notes strictly adhere to markdownlint standards.

## Production scope

The vault covers 775 verified entries across the 12 pillars. Summaries use maximum-depth treatment: normally 4,000–8,000 words, longer for foundational or technically complex works.

The generation pipeline is fully automated in Python: web research across 6 search vectors → LLM generation via Zen with NVIDIA and g4f fallbacks → validation → self-repair → atomic write.

