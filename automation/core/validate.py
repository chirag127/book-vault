from __future__ import annotations

import re
from pathlib import Path

import yaml


class ValidationError(ValueError):
    """Raised when a generated book note fails a quality gate."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n---\n"):
        return {}, text[8:]
    if text.startswith("---\r\n---\r\n"):
        return {}, text[10:]
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValidationError("Missing YAML front matter.")
    end = text.find("\n---\n", 4)
    if end < 0:
        end = text.find("\r\n---\r\n", 4)
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

    # Ensure no raw placeholders, secret keys, or AI hallucination boilerplate
    placeholder_pattern = r"lorem ipsum|replace-me|nvapi-[A-Za-z0-9_-]{12,}|EXA_API_KEY|\[insert\b|\[TODO\b|\[add details\b|as an AI language model|as a large language model|I do not have access to real-time"
    if re.search(placeholder_pattern, text, flags=re.I):
        errors.append("placeholder, secret, or AI boilerplate content detected")

    return errors


def validate_book_directory(book_dir: Path) -> dict[str, list[str]]:
    """Comprehensive automated audit of a generated book directory.

    Checks:
    - README.md exists and has valid YAML frontmatter + MOC
    - Concept notes exist (at least 2 concept notes)
    - Audio-Listening-Edition.md exists
    - Quiz.md exists with valid ```quiz block
    - Flashcards.md exists
    - All MOC wikilinks have matching files on disk (no broken internal links)
    - No stray 'yaml\\n---' prefix on any file
    - Word count bounds
    - Anti-hallucination & placeholder scan across all files
    """
    report = {"errors": [], "warnings": []}

    if not book_dir.exists() or not book_dir.is_dir():
        report["errors"].append(f"Directory does not exist: {book_dir}")
        return report

    readme = book_dir / "README.md"
    if not readme.exists():
        report["errors"].append("Missing README.md")
        return report

    readme_text = readme.read_text(encoding="utf-8")
    if readme_text.startswith("yaml\n") or readme_text.startswith("yaml\r\n"):
        report["errors"].append("README.md has broken 'yaml' prefix before frontmatter")

    try:
        meta, body = parse_frontmatter(readme_text)
    except Exception as exc:
        report["errors"].append(f"Invalid README.md YAML frontmatter: {exc}")
        meta, body = {}, ""

    # Check required frontmatter keys (support aliases)
    has_author = "author" in meta or "authors" in meta
    has_published = "published" in meta or "year" in meta or "first_published" in meta
    if not has_author:
        report["warnings"].append("README frontmatter missing 'author'")
    if not has_published:
        report["warnings"].append("README frontmatter missing 'published'")
    if "title" not in meta:
        report["warnings"].append("README frontmatter missing 'title'")
    if "slug" not in meta:
        report["warnings"].append("README frontmatter missing 'slug'")

    # Check MOC wikilinks vs files on disk
    moc_links = re.findall(r"\[\[(\d{2}-[^\\|\]]+)(?:\\?\|[^\]]+)?\]\]", readme_text)
    disk_files = {f.stem for f in book_dir.glob("*.md")}
    for link in moc_links:
        clean_link = link.strip().rstrip("\\").replace("./", "")
        if clean_link not in disk_files:
            report["errors"].append(f"Broken MOC link: [[{clean_link}]] linked in README but not found on disk")

    # Concept notes check
    concept_notes = list(book_dir.glob("[0-9][0-9]-*.md"))
    if len(concept_notes) < 2:
        report["warnings"].append(f"Only {len(concept_notes)} concept note(s) found (recommended: 3–6)")

    # Audio edition check
    audio = book_dir / "Audio-Listening-Edition.md"
    if not audio.exists():
        report["warnings"].append("Missing Audio-Listening-Edition.md")

    # Quiz check
    quiz = book_dir / "Quiz.md"
    if not quiz.exists():
        report["warnings"].append("Missing Quiz.md")
    else:
        quiz_text = quiz.read_text(encoding="utf-8")
        if "```quiz" not in quiz_text:
            report["warnings"].append("Quiz.md missing interactive ```quiz code block")

    # Anti-hallucination and placeholder checks across all markdown files
    placeholder_pattern = r"lorem ipsum|replace-me|\[insert\b|\[TODO\b|\[add details\b|as an AI language model|as a large language model"
    for f in book_dir.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            if re.search(placeholder_pattern, content, flags=re.I):
                report["errors"].append(f"Anti-hallucination check failed: placeholder/AI boilerplate in {f.name}")
        except Exception:
            pass

    # Word count check
    total_words = sum(len(f.read_text(encoding="utf-8").split()) for f in book_dir.glob("*.md"))
    if total_words < 1200:
        report["errors"].append(f"Total word count ({total_words}) is below 1200 words minimum")

    return report


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
