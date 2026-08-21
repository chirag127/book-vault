"""Generate Obsidian Kanban Board for tracking reading progress."""
from __future__ import annotations

from pathlib import Path
from ..core.config import ROOT
from ..core.manifest import load_manifest


def generate_kanban(manifest_path: Path | None = None, output_path: Path | None = None) -> Path:
    manifest_path = manifest_path or (ROOT / "automation" / "manifest.csv")
    output_path = output_path or (ROOT / "MOCs" / "READING-KANBAN.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    books = load_manifest(manifest_path)

    lines = [
        "---",
        "kanban-plugin: basic",
        "tags:",
        "  - reading-tracker",
        "  - kanban",
        "---",
        "",
        "# 📋 Reading Journey & Pipeline",
        "",
        "## 📥 Backlog (Curriculum Queue)",
        "",
    ]

    # First 20 books in Backlog
    for b in books[:20]:
        lines.append(f"- [ ] [[{b['slug']}|{b['title']}]] — *{b['author']}* (Pillar: {b['pillar']})")

    lines.extend([
        "",
        "## 📖 Currently Reading",
        "",
        "- [ ] [[Make-It-Stick|Make It Stick]] — *Peter C. Brown* #active-learning",
        "",
        "## 🔁 Spaced Repetition Review Queue",
        "",
        "- [ ] [[Make-It-Stick|Make It Stick]] — *Flashcard Recall Session (Day 3)*",
        "",
        "## ✅ Mastered & Implemented",
        "",
        "",
        "%% kanban:settings",
        "```",
        '{"kanban-plugin":"basic","lane-width":280,"show-checkboxes":true,"archive-with-date":true}',
        "```",
        "%%",
        "",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[kanban] Generated Obsidian Kanban board -> {output_path.relative_to(ROOT)}")
    return output_path


if __name__ == "__main__":
    generate_kanban()
