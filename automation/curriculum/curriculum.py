"""Build the canonical manifest and taxonomy from the 2,000-book curriculum.

Implements the Faceted / MECE Hybrid System:

- Level 1 (Pillar): 12 mutually-exclusive master domains -> `md/0X-<Pillar>/`
- Level 2 (Category): each pillar's non-overlapping sub-areas -> `md/0X-<Pillar>/NN-<Category>/`
- Level 3 (Subcategory): the book's finer topic, kept in the manifest and front matter
- Level 4 (Theme): free-form `tags` in front matter, used by Dataview MOCs

One canonical file per book. This module:
- Loads the transcribed curriculum entries (curriculum_data_1.py / _2.py).
- Maps every book into exactly one (pillar, category) via the MECE mapping table.
- Detects duplicates (same title + same author-surname) and keeps one canonical row.
- Flags non-book / vague entries for human review.
- Writes automation/manifest.csv, automation/taxonomy.py, SUBCATEGORY-MAP.md,
  pillar/category READMEs, MOCs/, and templates/.

The manifest is the single source of truth; never hand-edit generated files
unless you re-run this module afterwards.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .curriculum_data_1 import CURRICULUM as CORE_1
from .curriculum_data_2 import CURRICULUM as CORE_2

ROOT = Path(__file__).resolve().parents[1]
MD_ROOT = ROOT / "md"
MANIFEST_PATH = ROOT / "automation" / "manifest.csv"
TAXONOMY_PATH = ROOT / "automation" / "taxonomy.py"
SUBCATEGORY_MAP_PATH = ROOT / "SUBCATEGORY-MAP.md"

# ---------------------------------------------------------------------------
# Level 1: the 12 pillars (MECE master domains), in learning sequence.
# ---------------------------------------------------------------------------
PILLARS = [
    ("P01", "01-Learning-Cognition-and-Meta-Skills", "Learning, Cognition & Meta-Skills"),
    ("P02", "02-Thinking-Rationality-and-Mental-Models", "Thinking, Rationality & Mental Models"),
    ("P03", "03-Psychology-Behavior-and-Neuroscience", "Psychology, Behavior & Neuroscience"),
    ("P04", "04-Mathematics-Statistics-and-Quantitative-Logic", "Mathematics, Statistics & Quantitative Logic"),
    ("P05", "05-Computer-Science-and-Software-Engineering", "Computer Science & Software Engineering"),
    ("P06", "06-Artificial-Intelligence-and-Data-Systems", "Artificial Intelligence & Data Systems"),
    ("P07", "07-Economics-Markets-and-Investing", "Economics, Markets & Investing"),
    ("P08", "08-Business-Strategy-and-Enterprise", "Business, Strategy & Enterprise"),
    ("P09", "09-Leadership-Organizations-and-Management", "Leadership, Organizations & Management"),
    ("P10", "10-Natural-Sciences-Health-and-Biology", "Natural Sciences, Health & Biology"),
    ("P11", "11-History-Geopolitics-and-Civilization", "History, Geopolitics & Civilization"),
    ("P12", "12-Philosophy-Ethics-and-Human-Society", "Philosophy, Ethics & Human Society"),
]
PILLAR_KEY_TO_ENTRY = {key: (folder, display) for key, folder, display in PILLARS}

# ---------------------------------------------------------------------------
# Level 2: each pillar's canonical, non-overlapping categories (in order).
# ---------------------------------------------------------------------------
L2_BY_PILLAR: dict[str, list[str]] = {
    "P01": [
        "Learning Science & Cognitive Load",
        "Memory & Retention Systems",
        "Focus, Attention & Deep Work",
        "Note-Taking & PKM Systems",
        "Reading, Writing & Research",
        "Habits & Skill Acquisition",
    ],
    "P02": [
        "Cognitive Biases & Heuristics",
        "Decision Theory & Choice Architecture",
        "Probabilistic & Bayesian Reasoning",
        "Mental Models & Systems Thinking",
        "Risk, Uncertainty & Antifragility",
        "Critical Thinking & Epistemology",
    ],
    "P03": [
        "Social Psychology & Group Dynamics",
        "Persuasion, Influence & Rhetoric",
        "Motivation, Drive & Volition",
        "Neuroscience & Neurobiology",
        "Emotions, Stress & Resilience",
        "Relationships, Communication & Conflict",
    ],
    "P04": [
        "Mathematical Intuition & Foundations",
        "Probability & Combinatorics",
        "Statistical Inference & Modeling",
        "Causality & Experimental Design",
        "Data Analysis & Visualization",
    ],
    "P05": [
        "Algorithms & Data Structures",
        "Computer Architecture & Operating Systems",
        "Networking & Distributed Systems",
        "Software Design & Architecture",
        "Engineering Operations & DevOps",
        "Cybersecurity & Cryptography",
    ],
    "P06": [
        "Machine Learning Foundations",
        "Deep Learning & Neural Architectures",
        "Natural Language Processing & LLMs",
        "AI Engineering & Autonomous Agents",
        "Data Engineering & Big Data",
        "AI Safety, Ethics & Alignment",
    ],
    "P07": [
        "Microeconomics & Incentives",
        "Macroeconomics & Monetary Systems",
        "Economic & Financial History",
        "Personal Finance & Wealth Building",
        "Value Investing & Security Analysis",
        "Market Dynamics & Trading",
    ],
    "P08": [
        "Entrepreneurship & Startups",
        "Competitive Strategy & Moats",
        "Product Management & Design",
        "Marketing, Brand & Positioning",
        "Sales, GTM & Growth",
        "Accounting & Corporate Finance",
    ],
    "P09": [
        "High-Output Management",
        "Organizational Culture & Structure",
        "Executive Leadership & Strategy Execution",
        "Negotiation & Dealmaking",
        "Team Dynamics & Collaboration",
    ],
    "P10": [
        "Physics, Cosmology & the Universe",
        "Evolutionary Biology & Genetics",
        "Human Physiology & Metabolism",
        "Nutrition & Metabolic Health",
        "Sleep, Recovery & Longevity",
        "Exercise Physiology & Movement",
    ],
    "P11": [
        "World History & Macro-Civilizations",
        "Regional & National Histories",
        "Geopolitics & Grand Strategy",
        "Warfare, Military Strategy & Conflict",
        "Political Philosophy, Law & Governance",
    ],
    "P12": [
        "Ancient & Practical Philosophy",
        "Eastern & Indian Philosophies",
        "Modern Philosophy, Mind & Language",
        "Ethics, Morality & Justice",
        "Sociology, Anthropology & Culture",
        "Life Design & Meaning",
    ],
}

# ---------------------------------------------------------------------------
# MECE mapping: old curriculum category key -> (pillar, default category,
# {old subcategory: override}). Overrides are either a plain level-2 category
# name (same pillar) or a (pillar_key, category) tuple that re-pillars the
# book, so a subcategory can move to its proper home in another pillar.
# ---------------------------------------------------------------------------
CATEGORY_MAP: dict[str, tuple[str, str, dict[str, object]]] = {
    # -- P01: Learning, Cognition & Meta-Skills
    "Learning": ("P01", "Learning Science & Cognitive Load", {
        "Memory": "Memory & Retention Systems",
        "Focus": "Focus, Attention & Deep Work",
        "Time": "Focus, Attention & Deep Work",
        "Productivity": "Focus, Attention & Deep Work",
        "Habits": "Habits & Skill Acquisition",
        "Practice": "Habits & Skill Acquisition",
        "Expertise": "Habits & Skill Acquisition",
        "Mastery": "Habits & Skill Acquisition",
        "Reading": "Reading, Writing & Research",
        "Writing": "Reading, Writing & Research",
        "Research": "Reading, Writing & Research",
        "Knowledge": "Note-Taking & PKM Systems",
        "Notes": "Note-Taking & PKM Systems",
    }),
    # -- P02: Thinking, Rationality & Mental Models
    "Thinking": ("P02", "Cognitive Biases & Heuristics", {
        "Rationality": "Critical Thinking & Epistemology",
        "Forecasting": "Probabilistic & Bayesian Reasoning",
        "Decision Making": "Decision Theory & Choice Architecture",
        "Mental Models": "Mental Models & Systems Thinking",
        "Probability": "Probabilistic & Bayesian Reasoning",
        "Bayesian Thinking": "Probabilistic & Bayesian Reasoning",
        "Uncertainty": "Risk, Uncertainty & Antifragility",
        "Risk": "Risk, Uncertainty & Antifragility",
        "Incentives": "Risk, Uncertainty & Antifragility",
        "Measurement": "Probabilistic & Bayesian Reasoning",
        "Prediction": "Probabilistic & Bayesian Reasoning",
        "Logic": "Critical Thinking & Epistemology",
        "Skepticism": "Critical Thinking & Epistemology",
        "Critical Thinking": "Critical Thinking & Epistemology",
        "Game Theory": "Decision Theory & Choice Architecture",
    }),
    "Science": ("P02", "Critical Thinking & Epistemology", {
        "Chaos": ("P10", "Physics, Cosmology & the Universe"),
        "Complexity": ("P10", "Physics, Cosmology & the Universe"),
        "Overview": ("P10", "Physics, Cosmology & the Universe"),
        "Information": ("P04", "Mathematical Intuition & Foundations"),
    }),
    # -- P03: Psychology, Behavior & Neuroscience
    "Psychology": ("P03", "Social Psychology & Group Dynamics", {
        "Social Influence": "Persuasion, Influence & Rhetoric",
        "Persuasion": "Persuasion, Influence & Rhetoric",
        "Behavior": "Neuroscience & Neurobiology",
        "Motivation": "Motivation, Drive & Volition",
        "Addiction": "Neuroscience & Neurobiology",
        "Happiness": "Emotions, Stress & Resilience",
        "Emotion": "Emotions, Stress & Resilience",
        "Neuroscience": "Neuroscience & Neurobiology",
        "Relationships": "Relationships, Communication & Conflict",
        "Transactional Analysis": "Relationships, Communication & Conflict",
    }),
    "Communication": ("P01", "Reading, Writing & Research", {
        "Negotiation": ("P09", "Negotiation & Dealmaking"),
        "Difficult Talks": ("P03", "Relationships, Communication & Conflict"),
        "Conflict": ("P03", "Relationships, Communication & Conflict"),
        "Empathy": ("P03", "Relationships, Communication & Conflict"),
        "Rhetoric": ("P03", "Persuasion, Influence & Rhetoric"),
        "Speaking": ("P03", "Persuasion, Influence & Rhetoric"),
        "Presentations": ("P03", "Persuasion, Influence & Rhetoric"),
        "Advertising": ("P08", "Marketing, Brand & Positioning"),
        "Copywriting": ("P08", "Marketing, Brand & Positioning"),
        "Communication": ("P03", "Persuasion, Influence & Rhetoric"),
    }),
    # -- P04: Mathematics, Statistics & Quantitative Logic
    "Math": ("P04", "Mathematical Intuition & Foundations", {}),
    "Statistics": ("P04", "Statistical Inference & Modeling", {
        "Probability": "Probability & Combinatorics",
        "Data Science": "Data Analysis & Visualization",
        "Bayesian": "Statistical Inference & Modeling",
        "Visualization": "Data Analysis & Visualization",
        "Causality": "Causality & Experimental Design",
        "Experimentation": "Causality & Experimental Design",
        "Data": "Statistical Inference & Modeling",
    }),
    # -- P05: Computer Science & Software Engineering
    "CS": ("P05", "Algorithms & Data Structures", {
        "Systems": "Computer Architecture & Operating Systems",
        "Operating Systems": "Computer Architecture & Operating Systems",
        "Networking": "Networking & Distributed Systems",
        "Databases": "Networking & Distributed Systems",
        "Distributed Systems": "Networking & Distributed Systems",
        "Compilers": "Computer Architecture & Operating Systems",
        "Architecture": "Computer Architecture & Operating Systems",
        "Security": "Cybersecurity & Cryptography",
        "Cryptography": "Cybersecurity & Cryptography",
        "History": "Computer Architecture & Operating Systems",
        "Computing": "Algorithms & Data Structures",
    }),
    "Software": ("P05", "Software Design & Architecture", {
        "Reliability": "Engineering Operations & DevOps",
        "DevOps": "Engineering Operations & DevOps",
        "Delivery": "Engineering Operations & DevOps",
    }),
    "Systems": ("P05", "Networking & Distributed Systems", {
        "SQL": ("P06", "Data Engineering & Big Data"),
        "Microservices": "Software Design & Architecture",
        "Architecture": "Software Design & Architecture",
        "Kubernetes": "Engineering Operations & DevOps",
        "Linux": "Computer Architecture & Operating Systems",
        "Cloud": "Engineering Operations & DevOps",
        "Observability": "Engineering Operations & DevOps",
        "APIs": "Software Design & Architecture",
        "Security": "Cybersecurity & Cryptography",
        "Performance": "Engineering Operations & DevOps",
    }),
    "Security": ("P05", "Cybersecurity & Cryptography", {}),
    "Web": ("P05", "Software Design & Architecture", {}),
    "Cloud": ("P05", "Engineering Operations & DevOps", {
        "Distributed": "Networking & Distributed Systems",
        "Architecture": "Software Design & Architecture",
    }),
    # -- P06: Artificial Intelligence & Data Systems
    "AI": ("P06", "Machine Learning Foundations", {
        "Deep Learning": "Deep Learning & Neural Architectures",
        "Generative AI": "Deep Learning & Neural Architectures",
        "PyTorch": "Deep Learning & Neural Architectures",
        "NLP": "Natural Language Processing & LLMs",
        "Transformers": "Natural Language Processing & LLMs",
        "LLMs": "Natural Language Processing & LLMs",
        "LLM Engineering": "Natural Language Processing & LLMs",
        "RAG": "Natural Language Processing & LLMs",
        "ML Systems": "AI Engineering & Autonomous Agents",
        "AI Engineering": "AI Engineering & Autonomous Agents",
        "ML Engineering": "AI Engineering & Autonomous Agents",
        "Production": "AI Engineering & Autonomous Agents",
        "MLOps": "AI Engineering & Autonomous Agents",
        "Agents": "AI Engineering & Autonomous Agents",
        "Agentic Systems": "AI Engineering & Autonomous Agents",
        "Interpretability": "AI Safety, Ethics & Alignment",
        "Safety": "AI Safety, Ethics & Alignment",
        "Alignment": "AI Safety, Ethics & Alignment",
        "Society": "AI Safety, Ethics & Alignment",
        "Data": "Data Engineering & Big Data",
    }),
    "Data Engineering": ("P06", "Data Engineering & Big Data", {}),
    "Technology": ("P06", "AI Safety, Ethics & Alignment", {
        "Computing History": ("P05", "Computer Architecture & Operating Systems"),
        "Biotechnology": ("P10", "Evolutionary Biology & Genetics"),
        "Computing": ("P05", "Computer Architecture & Operating Systems"),
        "Open Source": ("P05", "Software Design & Architecture"),
    }),
    # -- P07: Economics, Markets & Investing
    "Finance": ("P07", "Personal Finance & Wealth Building", {
        "Corporate": ("P08", "Accounting & Corporate Finance"),
        "Valuation": ("P08", "Accounting & Corporate Finance"),
        "Accounting": ("P08", "Accounting & Corporate Finance"),
        "Fraud": ("P08", "Accounting & Corporate Finance"),
        "Capital": ("P08", "Accounting & Corporate Finance"),
        "Private Equity": ("P08", "Accounting & Corporate Finance"),
    }),
    "Investing": ("P07", "Value Investing & Security Analysis", {
        "Indexing": "Market Dynamics & Trading",
        "Markets": "Market Dynamics & Trading",
        "Cycles": "Market Dynamics & Trading",
        "Allocation": "Personal Finance & Wealth Building",
        "Mutual Funds": "Market Dynamics & Trading",
        "Behavioral": "Market Dynamics & Trading",
        "Quant": "Market Dynamics & Trading",
        "Trading": "Market Dynamics & Trading",
        "Capital": "Market Dynamics & Trading",
        "Bubbles": "Market Dynamics & Trading",
    }),
    "Economics": ("P07", "Microeconomics & Incentives", {
        "Institutions": ("P11", "Political Philosophy, Law & Governance"),
        "History": "Economic & Financial History",
        "Crises": "Economic & Financial History",
        "Debt": "Economic & Financial History",
        "Interest Rates": "Economic & Financial History",
        "Inequality": "Economic & Financial History",
        "Economic History": "Economic & Financial History",
        "Macro": "Macroeconomics & Monetary Systems",
        "China": "Macroeconomics & Monetary Systems",
        "Globalization": "Macroeconomics & Monetary Systems",
        "Political Economy": ("P11", "Political Philosophy, Law & Governance"),
        "Trade": "Economic & Financial History",
        "India": ("P11", "Regional & National Histories"),
    }),
    # -- P08: Business, Strategy & Enterprise
    "Business": ("P09", "High-Output Management", {
        "Strategy": ("P08", "Competitive Strategy & Moats"),
        "Business History": ("P08", "Competitive Strategy & Moats"),
        "Business": ("P08", "Competitive Strategy & Moats"),
        "Capital Allocation": ("P08", "Accounting & Corporate Finance"),
        "Companies": ("P08", "Competitive Strategy & Moats"),
    }),
    "Entrepreneurship": ("P08", "Entrepreneurship & Startups", {
        "Networks": "Competitive Strategy & Moats",
        "Product": "Product Management & Design",
        "Growth": "Sales, GTM & Growth",
    }),
    "Product": ("P08", "Product Management & Design", {
        "Growth": "Sales, GTM & Growth",
        "Pricing": "Sales, GTM & Growth",
    }),
    "Marketing": ("P08", "Marketing, Brand & Positioning", {}),
    "Sales": ("P08", "Sales, GTM & Growth", {}),
    "Accounting": ("P08", "Accounting & Corporate Finance", {}),
    # -- P09: Leadership, Organizations & Management
    "Leadership": ("P09", "Executive Leadership & Strategy Execution", {
        "Management": "High-Output Management",
        "Culture": "Organizational Culture & Structure",
        "Organizations": "Organizational Culture & Structure",
        "Teams": "Team Dynamics & Collaboration",
    }),
    # -- P10: Natural Sciences, Health & Biology
    "Health": ("P10", "Human Physiology & Metabolism", {
        "Sleep": "Sleep, Recovery & Longevity",
        "Longevity": "Sleep, Recovery & Longevity",
        "Exercise": "Exercise Physiology & Movement",
        "Movement": "Exercise Physiology & Movement",
        "Sports Science": "Exercise Physiology & Movement",
        "Nutrition": "Nutrition & Metabolic Health",
        "Metabolism": "Nutrition & Metabolic Health",
        "Breath": "Human Physiology & Metabolism",
        "Mental Health": ("P03", "Emotions, Stress & Resilience"),
        "CBT": ("P03", "Emotions, Stress & Resilience"),
        "Stress": ("P03", "Emotions, Stress & Resilience"),
        "Relationships": ("P03", "Relationships, Communication & Conflict"),
        "Happiness": ("P03", "Emotions, Stress & Resilience"),
    }),
    "Biology": ("P10", "Evolutionary Biology & Genetics", {
        "Medicine": "Human Physiology & Metabolism",
        "Human Body": "Human Physiology & Metabolism",
        "Ecology": "Evolutionary Biology & Genetics",
        "Neuroscience": ("P03", "Neuroscience & Neurobiology"),
        "Ethics": ("P12", "Ethics, Morality & Justice"),
    }),
    "Physics": ("P10", "Physics, Cosmology & the Universe", {}),
    # -- P11: History, Geopolitics & Civilization
    "History": ("P11", "World History & Macro-Civilizations", {
        "WWII": "Warfare, Military Strategy & Conflict",
        "Europe": "Regional & National Histories",
        "US History": "Regional & National Histories",
        "Britain": "Regional & National Histories",
        "China": "Regional & National Histories",
        "Japan": "Regional & National Histories",
        "Renaissance": "Regional & National Histories",
    }),
    "India": ("P11", "Regional & National Histories", {
        "Society": ("P12", "Sociology, Anthropology & Culture"),
        "Constitution": "Political Philosophy, Law & Governance",
        "Judiciary": "Political Philosophy, Law & Governance",
        "Politics": "Political Philosophy, Law & Governance",
        "Economics": ("P07", "Macroeconomics & Monetary Systems"),
        "Economy": ("P07", "Macroeconomics & Monetary Systems"),
        "Business": ("P08", "Competitive Strategy & Moats"),
    }),
    "Politics": ("P11", "Political Philosophy, Law & Governance", {}),
    "Power": ("P11", "Geopolitics & Grand Strategy", {
        "Strategy": "Warfare, Military Strategy & Conflict",
        "War": "Warfare, Military Strategy & Conflict",
    }),
    "Geopolitics": ("P11", "Geopolitics & Grand Strategy", {
        "Strategy": "Warfare, Military Strategy & Conflict",
    }),
    # -- P12: Philosophy, Ethics & Human Society
    "Philosophy": ("P12", "Modern Philosophy, Mind & Language", {
        "Stoicism": "Ancient & Practical Philosophy",
        "Ethics": "Ethics, Morality & Justice",
        "Existentialism": "Modern Philosophy, Mind & Language",
        "Eastern Philosophy": "Eastern & Indian Philosophies",
        "Indian Philosophy": "Eastern & Indian Philosophies",
        "Logic": ("P02", "Critical Thinking & Epistemology"),
        "Mind": "Modern Philosophy, Mind & Language",
        "Free Will": "Modern Philosophy, Mind & Language",
        "Knowledge": "Modern Philosophy, Mind & Language",
        "Language": "Modern Philosophy, Mind & Language",
        "Meaning": "Life Design & Meaning",
    }),
    "Sociology": ("P12", "Sociology, Anthropology & Culture", {
        "Culture": ("P09", "Organizational Culture & Structure"),
        "Institutions": ("P11", "Political Philosophy, Law & Governance"),
    }),
    "Biography": ("P12", "Life Design & Meaning", {
        "Investing": ("P07", "Value Investing & Security Analysis"),
        "Business": ("P08", "Competitive Strategy & Moats"),
        "Science": ("P10", "Physics, Cosmology & the Universe"),
    }),
    "Personal Development": ("P12", "Life Design & Meaning", {
        "Habits": ("P01", "Habits & Skill Acquisition"),
        "Stoicism": "Ancient & Practical Philosophy",
    }),
    "Decision Making": ("P02", "Decision Theory & Choice Architecture", {
        "Creativity": ("P12", "Life Design & Meaning"),
        "Innovation": ("P08", "Competitive Strategy & Moats"),
        "Design Thinking": ("P08", "Product Management & Design"),
        "Design": ("P08", "Product Management & Design"),
        "Product": ("P08", "Product Management & Design"),
        "Strategy": ("P08", "Competitive Strategy & Moats"),
        "Problem Solving": "Mental Models & Systems Thinking",
    }),
}

# Difficulty mapping: priority is NOT difficulty; S books are foundational so
# they get intermediate treatment, A/B start at beginner.
def difficulty_for(priority: str) -> str:
    return "intermediate" if priority == "S" else "beginner"


# Authors / titles that indicate a placeholder rather than a specific book.
VAGUE_AUTHORS = {
    "related practitioner literature",
    "use primary research for medical decisions",
    "various authors",
    "various legal biographies",
    "industry history",
}


def slugify(text: str) -> str:
    cleaned = text.replace("'", "").replace("’", "").replace("!", "").replace("?", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", cleaned).strip("-")
    return re.sub(r"-{2,}", "-", slug) or "untitled"


def author_surname(author: str) -> str:
    """Last token of the last author entry, used as a duplicate key."""
    parts = [p.strip() for p in author.split(";") if p.strip()]
    if not parts:
        return ""
    return parts[-1].split()[-1].lower() if parts[-1].split() else ""


def load_entries() -> list[tuple]:
    return CORE_1 + CORE_2


def build() -> dict:
    entries = load_entries()
    seen_key: dict[tuple[str, str], str] = {}  # (title, surname) -> canonical number
    duplicates: list[tuple[str, str, str, str]] = []
    flagged: list[tuple[str, str, str, str]] = []
    rows: list[dict[str, str]] = []
    used: dict[str, set[str]] = {display: set() for _, _, display in PILLARS}

    for number, priority, key, topic, title, author in entries:
        mapped = CATEGORY_MAP.get(key)
        if mapped is None:
            flagged.append((number, title, author, f"unknown category key '{key}'"))
            continue
        pillar_key, default_l2, overrides = mapped
        override = overrides.get(topic)
        if override is None:
            l2 = default_l2
        elif isinstance(override, tuple):
            pillar_key, l2 = override
        else:
            l2 = override  # plain category name in the same pillar
        pillar_folder, pillar_display = PILLAR_KEY_TO_ENTRY[pillar_key]

        if title.casefold().startswith("examine evidence-based") or author.casefold() in VAGUE_AUTHORS:
            flagged.append((number, title, author, "not a specific book / vague entry"))
            continue

        dup_key = (title.casefold().strip(), author_surname(author))
        if dup_key in seen_key:
            duplicates.append((number, seen_key[dup_key], title, author))
            continue
        seen_key[dup_key] = number

        if l2 not in L2_BY_PILLAR[pillar_key]:
            flagged.append((number, title, author, f"category '{l2}' not in pillar {pillar_key}"))
            continue
        used[pillar_display].add(l2)

        slug = slugify(title)
        l2_index = L2_BY_PILLAR[pillar_key].index(l2) + 1
        path = f"md/{pillar_folder}/{l2_index:02d}-{slugify(l2)}/{slug}.md"
        rows.append(
            {
                "number": number,
                "priority": priority,
                "title": title,
                "author": author,
                "published": "",
                "pillar": pillar_display,
                "category": l2,
                "subcategory": topic,
                "learning_stage": "",
                "prerequisites": "",
                "slug": slug,
                "difficulty": difficulty_for(priority),
                "status": "planned",
                "primary_source": "",
                "path": path,
            }
        )

    taxonomy = {display: [l2 for l2 in L2_BY_PILLAR[key] if l2 in used[display]] for key, _, display in PILLARS}
    taxonomy = {display: l2s for display, l2s in taxonomy.items() if l2s}

    write_manifest(rows)
    write_taxonomy()
    write_subcategory_map(taxonomy)
    write_readmes(taxonomy)
    return {
        "total": len(rows),
        "duplicates": duplicates,
        "flagged": flagged,
        "taxonomy": taxonomy,
    }


def write_manifest(rows: list[dict[str, str]]) -> None:
    columns = [
        "number", "priority", "title", "author", "published", "pillar",
        "category", "subcategory", "learning_stage", "prerequisites", "slug",
        "difficulty", "status", "primary_source", "path",
    ]
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"WROTE manifest: {len(rows)} books -> {MANIFEST_PATH.relative_to(ROOT)}")


def write_taxonomy() -> None:
    lines = [
        "# Generated by automation/curriculum.py — do not hand-edit; re-run the builder.",
        '"""Pillar folder mappings derived from the canonical curriculum."""',
        "",
        "PILLAR_DIRS = {",
    ]
    for _, folder, display in PILLARS:
        lines.append(f'    "{display}": "{folder}",')
    lines.append("}")
    lines.append("")
    TAXONOMY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE taxonomy -> {TAXONOMY_PATH.relative_to(ROOT)}")


def write_subcategory_map(taxonomy: dict[str, list[str]]) -> None:
    lines = [
        "# Subcategory Map",
        "",
        "> Four-level classification: **Pillar** (level 1, folder) → **Category** (level 2, folder) → **Subcategory** (level 3, front matter) → **Tags** (level 4, front matter). Each book has exactly one primary pillar and one primary category; subcategories and tags create the faceted graph.",
        "",
        "> Generated by automation/curriculum.py — re-run the builder after editing the curriculum.",
        "",
    ]
    for index, (key, folder, display) in enumerate(PILLARS, start=1):
        l2s = taxonomy.get(display, [])
        if not l2s:
            continue
        lines.append(f"## {index:02d} — {display}")
        lines.append("")
        for sub_index, l2 in enumerate(l2s, start=1):
            lines.append(f"{sub_index}. {l2}")
        lines.append("")
    SUBCATEGORY_MAP_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE subcategory map -> {SUBCATEGORY_MAP_PATH.relative_to(ROOT)}")


def write_readmes(taxonomy: dict[str, list[str]]) -> None:
    for key, folder, display in PILLARS:
        l2s = taxonomy.get(display, [])
        if not l2s:
            continue
        pillar_dir = MD_ROOT / folder
        pillar_dir.mkdir(parents=True, exist_ok=True)
        subcats = "\n".join(f"{i}. {s}" for i, s in enumerate(l2s, start=1))
        readme = f"""# {display}

> Level 1 of the four-level classification. Book notes live in the category folders below; subcategories and tags live in each note's front matter and are surfaced by the Dataview dashboards in [[MOCs/00-MASTER-INDEX|MOCs]].

## Categories

{subcats}

## Status

Book files are generated one at a time by the automation pipeline and appear here as they pass validation.
"""
        (pillar_dir / "README.md").write_text(readme, encoding="utf-8")
        for l2_index, l2 in enumerate(l2s, start=1):
            l2_dir = pillar_dir / f"{l2_index:02d}-{slugify(l2)}"
            l2_dir.mkdir(parents=True, exist_ok=True)
            l2_readme = f"""# {l2}

> Level 2 category of [[README|{display}]]. Books in this folder share exactly one primary category; see [[SUBCATEGORY-MAP]] for the full four-level taxonomy.
"""
            (l2_dir / "README.md").write_text(l2_readme, encoding="utf-8")
    print(f"WROTE pillar + category READMEs under {MD_ROOT.relative_to(ROOT)}")


if __name__ == "__main__":
    result = build()
    print(f"\nTOTAL BOOKS: {result['total']}")
    print(f"DUPLICATES REMOVED: {len(result['duplicates'])}")
    for dup_number, canonical, title, author in result["duplicates"]:
        print(f"  #{dup_number} -> #{canonical} | {title} — {author}")
    print(f"FLAGGED FOR REVIEW: {len(result['flagged'])}")
    for number, title, author, reason in result["flagged"]:
        print(f"  #{number} | {title} — {author} | {reason}")
