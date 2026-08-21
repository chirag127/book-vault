from __future__ import annotations

import re
from pathlib import Path

import yaml


class ValidationError(ValueError):
    """Raised when a generated book note fails a quality gate."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValidationError("Missing YAML front matter.")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError("Unclosed YAML front matter.")
    metadata = yaml.safe_load(text[4:end]) or {}
    if not isinstance(metadata, dict):
        raise ValidationError("Front matter must be a mapping.")
    return metadata, text[end + 5 :]


def validate_note(path: Path, min_words: int = 1500, max_words: int = 25000) -> list[str]:
    """Lightweight validation: ensures YAML frontmatter is valid and note has substantial content."""
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    try:
        metadata, body = parse_frontmatter(text)
    except (ValidationError, yaml.YAMLError) as exc:
        return [str(exc)]

    # Basic word count verification (must be a genuine long-form summary)
    words = len(re.findall(r"\b[\w’'-]+\b", body))
    if words < 1000:
        errors.append(f"note is too short ({words} words; expected >= 1000)")

    # Ensure no raw placeholders or leaked template tags
    if re.search(r"lorem ipsum|replace-me|nvapi-[A-Za-z0-9_-]{12,}|EXA_API_KEY", text, flags=re.I):
        errors.append("placeholder or secret-like content found")

    return errors



def _vault_md_files(root: Path):
    """All markdown files under the vault, skipping archives and hidden dirs."""
    for path in sorted(root.glob("**/*.md")):
        parts = path.parts
        if any(part.startswith("_") or part.startswith(".") for part in parts):
            continue
        yield path


def validate_tree(root: Path, min_words: int = 2500, max_words: int = 9000) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for path in _vault_md_files(root):
        if path.name == "README.md" or path.parent.name.startswith(".") or not re.match(r"^\d{2}-", path.parent.name):
            continue
        errors = validate_note(path, min_words=min_words, max_words=max_words)
        if errors:
            results[str(path)] = errors
    return results


def find_duplicate_book_files(root: Path) -> list[tuple[str, list[Path]]]:
    """Return book slugs that exist in more than one physical location.

    Only files whose parent folder looks like a numbered subcategory folder
    (e.g. `01-Reading-Fundamentals`) are treated as book notes. Archive and
    hidden folders are excluded so tombstones never count as duplicates.
    """
    by_stem: dict[str, list[Path]] = {}
    for path in _vault_md_files(root):
        if path.name == "README.md" or not re.match(r"^\d{2}-", path.parent.name):
            continue
        by_stem.setdefault(path.stem, []).append(path)
    return [(stem, paths) for stem, paths in by_stem.items() if len(paths) > 1]
