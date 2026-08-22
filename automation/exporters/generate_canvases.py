from __future__ import annotations

import json
import uuid
from pathlib import Path

from ..core.config import ROOT
from ..core.manifest import category_folder, load_manifest
from ..core.taxonomy import PILLAR_DIRS



def _node_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_pillar_canvas(pillar_name: str, pillar_folder: str, books: list[dict[str, str]]) -> Path:
    """Generate an Obsidian .canvas visual mind-map for one pillar."""
    pillar_books = [b for b in books if b["pillar"] == pillar_name]
    canvas_dir = ROOT / "md" / pillar_folder
    canvas_dir.mkdir(parents=True, exist_ok=True)
    canvas_path = canvas_dir / f"{pillar_folder}.canvas"

    nodes = []
    edges = []

    # 1. Header / Pillar Title Node
    title_node_id = _node_id()
    nodes.append({
        "id": title_node_id,
        "type": "text",
        "text": f"# 🏛️ {pillar_name}\n\n**Total Books**: {len(pillar_books)} | **Curriculum Track**: MECE 3-Level",
        "x": 0,
        "y": 0,
        "width": 600,
        "height": 180,
        "color": "1",  # Red / Crimson
    })

    # Group books by category
    by_category: dict[str, list[dict[str, str]]] = {}
    for book in pillar_books:
        by_category.setdefault(book["category"], []).append(book)

    start_y = 260
    col_width = 380
    row_height = 200
    gap_x = 80
    gap_y = 50

    prev_cat_node_id = title_node_id

    for cat_idx, (category, cat_books) in enumerate(by_category.items()):
        cat_node_id = _node_id()
        cat_x = 0
        cat_y = start_y + cat_idx * (len(cat_books) * (row_height + gap_y) + 80)

        # Category Hub Node
        nodes.append({
            "id": cat_node_id,
            "type": "text",
            "text": f"## 📂 {category}\n*{len(cat_books)} books*",
            "x": cat_x,
            "y": cat_y,
            "width": 320,
            "height": 120,
            "color": "3",  # Yellow / Gold
        })

        # Connect Pillar -> Category
        edges.append({
            "id": _node_id(),
            "fromNode": title_node_id if cat_idx == 0 else prev_cat_node_id,
            "fromSide": "bottom",
            "toNode": cat_node_id,
            "toSide": "top",
        })
        prev_cat_node_id = cat_node_id

        # Books in Category
        prev_book_node_id = cat_node_id
        for book_idx, book in enumerate(cat_books):
            book_node_id = _node_id()
            book_x = cat_x + col_width + gap_x
            book_y = cat_y + book_idx * (row_height + gap_y)

            # Check if book folder or markdown file exists
            cat_dir = category_folder(book["pillar"], book["category"])
            book_file_rel = f"md/{pillar_folder}/{cat_dir}/{book['slug']}/README.md"

            nodes.append({
                "id": book_node_id,
                "type": "text",
                "text": f"### 📖 {book['title']}\n*By {book['author']}*\n\n- **Difficulty**: `{book['difficulty']}`\n- **Type**: {book.get('book_type', 'Core Text')}\n- 🔗 [[{book['slug']}/README|Open Reading Guide]]\n- 🎧 [[{book['slug']}/Audio-Listening-Edition|Open Audio Edition]]",
                "x": book_x,
                "y": book_y,
                "width": 360,
                "height": 190,
                "color": "4",  # Green / Emerald
            })

            # Connect Category -> First Book, and Book -> Next Book
            edges.append({
                "id": _node_id(),
                "fromNode": prev_book_node_id,
                "fromSide": "right" if prev_book_node_id == cat_node_id else "bottom",
                "toNode": book_node_id,
                "toSide": "left" if prev_book_node_id == cat_node_id else "top",
            })
            prev_book_node_id = book_node_id

    canvas_data = {
        "nodes": nodes,
        "edges": edges,
    }
    canvas_path.write_text(json.dumps(canvas_data, indent=2), encoding="utf-8")
    return canvas_path


def generate_book_canvas(book_dir: Path) -> Path | None:
    """Generate an interactive visual mindmap Canvas for a specific book directory."""
    readme_path = book_dir / "README.md"
    if not readme_path.exists():
        return None

    canvas_path = book_dir / f"{book_dir.name}.canvas"
    readme_text = readme_path.read_text(encoding="utf-8")

    import re
    title_m = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", readme_text, re.M)
    author_m = re.search(r"^author:\s*[\"']?(.*?)[\"']?$", readme_text, re.M)
    title = title_m.group(1) if title_m else book_dir.name
    author = author_m.group(1) if author_m else "Author"

    nodes = []
    edges = []

    # 1. Central Book Node
    root_id = _node_id()
    nodes.append({
        "id": root_id,
        "type": "text",
        "text": f"# 📖 {title}\n*By {author}*\n\n🔗 [[README|Executive Summary]]",
        "x": 0,
        "y": 0,
        "width": 420,
        "height": 180,
        "color": "1",  # Red / Ruby
    })

    # 2. Chapters & Concept Notes
    chapter_files = sorted([f for f in book_dir.glob("*.md") if f.name not in {"README.md", "Audio-Listening-Edition.md", "Quiz.md", "Flashcards.md"}])

    chap_start_x = 520
    chap_start_y = -((len(chapter_files) - 1) * 220) // 2
    for i, chap in enumerate(chapter_files):
        chap_id = _node_id()
        chap_name = chap.stem.replace("-", " ")
        nodes.append({
            "id": chap_id,
            "type": "text",
            "text": f"### 📑 {chap_name}\n\n🔗 [[{chap.stem}|Read Chapter Breakdown]]",
            "x": chap_start_x,
            "y": chap_start_y + (i * 240),
            "width": 380,
            "height": 160,
            "color": "3",  # Yellow / Amber for concept notes
        })
        edges.append({
            "id": _node_id(),
            "fromNode": root_id,
            "fromSide": "right",
            "toNode": chap_id,
            "toSide": "left",
        })

    # 3. Companion Editions Node (Audio, Quiz, Flashcards)
    side_x = -480
    audio_id = _node_id()
    nodes.append({
        "id": audio_id,
        "type": "text",
        "text": f"### 🎧 Companion Editions\n\n- 🎧 [[Audio-Listening-Edition|Spoken Audio Synthesis]]\n- 🧩 [[Quiz|Knowledge Assessment Quiz]]\n- 🎴 [[Flashcards|Active Recall Flashcards]]",
        "x": side_x,
        "y": -120,
        "width": 380,
        "height": 180,
        "color": "5",  # Cyan / Blue
    })
    edges.append({
        "id": _node_id(),
        "fromNode": root_id,
        "fromSide": "left",
        "toNode": audio_id,
        "toSide": "right",
    })

    # 4. Action & Navigation Node
    nav_id = _node_id()
    nodes.append({
        "id": nav_id,
        "type": "text",
        "text": f"### 🧭 Navigation & Curriculum\n\n- 🏠 [[../README|Category Hub]]\n- 📚 Master Catalog Index",
        "x": side_x,
        "y": 100,
        "width": 380,
        "height": 140,
        "color": "6",  # Purple
    })
    edges.append({
        "id": _node_id(),
        "fromNode": root_id,
        "fromSide": "left",
        "toNode": nav_id,
        "toSide": "right",
    })

    canvas_data = {"nodes": nodes, "edges": edges}
    canvas_path.write_text(json.dumps(canvas_data, indent=2), encoding="utf-8")
    return canvas_path


def generate_all_canvases() -> list[Path]:
    """Generate all 12 pillar canvas mind-maps and book canvases."""
    books = load_manifest(ROOT / "automation" / "manifest.csv")
    created = []
    for pillar_name, folder in PILLAR_DIRS.items():
        path = generate_pillar_canvas(pillar_name, folder, books)
        created.append(path)
        print(f"[canvas] Generated {path.relative_to(ROOT)}", flush=True)

    for book_dir in sorted(ROOT.glob("md/*/*/*")):
        if book_dir.is_dir() and (book_dir / "README.md").exists():
            b_canvas = generate_book_canvas(book_dir)
            if b_canvas:
                created.append(b_canvas)
    return created


def main() -> int:
    created = generate_all_canvases()
    print(f"\n[OK] Generated {len(created)} Obsidian Canvas maps successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
