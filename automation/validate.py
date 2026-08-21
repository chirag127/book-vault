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


def validate_note(path: Path, min_words: int = 1000, max_words: int = 25000) -> list[str]:
    """Lightweight validation: ensures YAML frontmatter is valid and note has substantial content."""
    target_file = path / "README.md" if path.is_dir() else path
    if not target_file.exists():
        return [f"missing summary file at {path}"]
    text = target_file.read_text(encoding="utf-8")
    errors: list[str] = []
    try:
        metadata, body = parse_frontmatter(text)
    except (ValidationError, yaml.YAMLError) as exc:
        return [str(exc)]

    # Basic word count verification
    words = len(re.findall(r"\b[\w’'-]+\b", body))
    if path.is_dir():
        # Sum word count across all markdown files in the book directory
        total_words = sum(len(re.findall(r"\b[\w’'-]+\b", f.read_text(encoding="utf-8"))) for f in path.glob("*.md"))
        if total_words < 1000:
            errors.append(f"book folder is too short ({total_words} words; expected >= 1000)")
    elif words < 500:
        errors.append(f"note is too short ({words} words; expected >= 500)")

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


def validate_tree(root: Path, min_words: int = 1500, max_words: int = 25000) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for path in _vault_md_files(root):
        if path.name == "README.md" and not (path.parent.parent.name.startswith("md") or re.match(r"^\d{2}-", path.parent.name)):
            continue
        errors = validate_note(path, min_words=min_words, max_words=max_words)
        if errors:
            results[str(path)] = errors
    return results


def find_duplicate_book_files(root: Path) -> list[tuple[str, list[Path]]]:
    """Return book slugs that exist in more than one physical location."""
    by_stem: dict[str, list[Path]] = {}
    for path in root.glob("md/*/*/*"):
        if path.is_dir() and not path.name.startswith("."):
            by_stem.setdefault(path.name, []).append(path)
        elif path.is_file() and path.suffix == ".md" and path.name != "README.md":
            by_stem.setdefault(path.stem, []).append(path)
    return [(stem, paths) for stem, paths in by_stem.items() if len(paths) > 1]

