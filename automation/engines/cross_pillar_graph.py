"""
automation.engines.cross_pillar_graph
-------------------------------------
Extracts and builds semantic cross-pillar bridges connecting concepts across the 12 Knowledge Pillars.
"""
from __future__ import annotations

import json
from pathlib import Path
from automation.core.config import ROOT

# Canonical cross-pillar concept mappings
CROSS_PILLAR_CONCEPTS = {
    "Compounding & Exponential Growth": [
        {"pillar": "01-Learning-Cognition-and-Meta-Skills", "concept": "Knowledge Accretion & Habit Compounding", "books": ["Atomic-Habits", "Make-It-Stick"]},
        {"pillar": "07-Economics-Markets-and-Investing", "concept": "Compound Interest & Capital Accumulation", "books": ["The-Psychology-of-Money", "The-Essays-of-Warren-Buffett"]},
        {"pillar": "08-Business-Strategy-and-Enterprise", "concept": "Flywheel Effects & Scaling", "books": ["Good-to-Great", "Zero-to-One"]},
    ],
    "First-Principles Thinking & Inversion": [
        {"pillar": "02-Thinking-Rationality-and-Mental-Models", "concept": "Inversion & Mental Models", "books": ["Poor-Charlies-Almanack", "Seeking-Wisdom"]},
        {"pillar": "04-Mathematics-Statistics-and-Quantitative-Logic", "concept": "Deductive Proofs & Axioms", "books": ["How-Not-to-Be-Wrong", "Principles-of-Mathematical-Analysis"]},
        {"pillar": "05-Computer-Science-and-Software-Engineering", "concept": "Algorithmic Complexity & Architecture", "books": ["Clean-Architecture", "Structure-and-Interpretation-of-Computer-Programs"]},
    ],
    "Antifragility & Risk Management": [
        {"pillar": "02-Thinking-Rationality-and-Mental-Models", "concept": "Antifragile Systems & Asymmetry", "books": ["Antifragile", "Skin-in-the-Game"]},
        {"pillar": "07-Economics-Markets-and-Investing", "concept": "Tail Risk & Fat-Tailed Distributions", "books": ["The-Black-Swan", "Fooled-by-Randomness"]},
        {"pillar": "10-Natural-Sciences-Health-and-Biology", "concept": "Hormesis & Evolutionary Adaptation", "books": ["Why-We-Sleep", "The-Extended-Phenotype"]},
    ],
    "Incentive Structures & Game Theory": [
        {"pillar": "03-Psychology-Behavior-and-Neuroscience", "concept": "Operant Conditioning & Dopamine Circuits", "books": ["Thinking-Fast-and-Slow", "Behave"]},
        {"pillar": "07-Economics-Markets-and-Investing", "concept": "Market Equilibrium & Mechanism Design", "books": ["Freakonomics", "Economics-in-One-Lesson"]},
        {"pillar": "09-Leadership-Organizations-and-Management", "concept": "Principal-Agent Problems & Alignment", "books": ["High-Output-Management", "Measure-What-Matters"]},
    ],
}


def build_cross_pillar_graph() -> dict:
    """Builds and saves the cross-pillar knowledge graph."""
    graph_path = ROOT / "md" / "cross_pillar_graph.json"
    graph_path.write_text(json.dumps(CROSS_PILLAR_CONCEPTS, indent=2, ensure_ascii=False), encoding="utf-8")
    return CROSS_PILLAR_CONCEPTS


def main() -> int:
    graph = build_cross_pillar_graph()
    print(f"[cross-pillar] Built cross-pillar graph with {len(graph)} universal concepts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
