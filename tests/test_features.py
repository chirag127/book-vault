from __future__ import annotations

import json
from pathlib import Path
from automation.generate_canvases import generate_pillar_canvas
from automation.vault_search import search_vault, _tokenize
from automation.synthesize_audio import _clean_spoken_text



def test_canvas_generation(tmp_path):
    sample_books = [
        {
            "title": "Make It Stick",
            "author": "Peter C. Brown",
            "pillar": "Learning, Cognition & Meta-Skills",
            "category": "Learning Science & Cognitive Load",
            "slug": "Make-It-Stick",
            "difficulty": "Introductory",
        }
    ]
    path = generate_pillar_canvas("Learning, Cognition & Meta-Skills", "01-Learning-Cognition-and-Meta-Skills", sample_books)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 3



def test_vault_search_tokenization():
    tokens = _tokenize("How to Make It Stick: 2026 Edition!")
    assert "how" in tokens
    assert "make" in tokens
    assert "stick" in tokens
    assert "2026" in tokens


def test_spoken_text_cleaner():
    markdown = """---
title: "Sample Book"
author: "Author Name"
---

# Sample Book — Audio Edition
*By Author Name*

Here is a paragraph with a [[Make-It-Stick|link]] and a [regular link](https://example.com).
> [!NOTE]
> Important takeaway here.
"""
    cleaned = _clean_spoken_text(markdown)
    assert "Sample Book" in cleaned
    assert "link" in cleaned
    assert "---" not in cleaned
    assert "[[" not in cleaned
    assert "https://" not in cleaned
