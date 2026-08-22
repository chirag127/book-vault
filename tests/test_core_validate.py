"""Tests for automation/core/validate.py — Frontmatter parsing, note validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from automation.core.validate import (
    ValidationError,
    parse_frontmatter,
    validate_book_directory,
    validate_note,
)


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------
class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        text = '---\ntitle: "Test Book"\nauthor: "Author"\n---\nBody content.'
        meta, body = parse_frontmatter(text)
        assert meta["title"] == "Test Book"
        assert meta["author"] == "Author"
        assert "Body content." in body

    def test_missing_frontmatter(self):
        with pytest.raises(ValidationError, match="Missing YAML"):
            parse_frontmatter("No frontmatter here.")

    def test_unclosed_frontmatter(self):
        with pytest.raises(ValidationError, match="Unclosed"):
            parse_frontmatter("---\ntitle: Test\nBody.")

    def test_frontmatter_not_dict(self):
        with pytest.raises(ValidationError, match="mapping"):
            parse_frontmatter("---\n- item1\n- item2\n---\nBody.")

    def test_empty_frontmatter_values(self):
        text = '---\ntitle: "Empty"\n---\nBody.'
        meta, body = parse_frontmatter(text)
        assert isinstance(meta, dict)
        assert "Body." in body


# ---------------------------------------------------------------------------
# validate_note
# ---------------------------------------------------------------------------
class TestValidateNote:
    def test_valid_note(self, tmp_path):
        readme = tmp_path / "README.md"
        content = (
            '---\ntitle: "Test Book"\nauthor: "Author"\nslug: test\n---\n\n'
            + "# Test Book\n" + " ".join(["word"] * 2000)
        )
        readme.write_text(content, encoding="utf-8")
        errors = validate_note(tmp_path)
        assert errors == []

    def test_missing_file(self, tmp_path):
        errors = validate_note(tmp_path / "nonexistent")
        assert len(errors) >= 1
        assert "missing" in errors[0].lower()

    def test_invalid_frontmatter(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("Not YAML frontmatter.", encoding="utf-8")
        errors = validate_note(tmp_path)
        assert len(errors) >= 1

    def test_placeholder_detected(self, tmp_path):
        readme = tmp_path / "README.md"
        content = '---\ntitle: "Test"\n---\n\n' + " ".join(["word"] * 1000) + "\n\nlorem ipsum dolor"
        readme.write_text(content, encoding="utf-8")
        errors = validate_note(tmp_path)
        assert any("placeholder" in e.lower() or "lorem" in e.lower() for e in errors)

    def test_too_short_single_file(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text('---\ntitle: "Short"\n---\n\nJust a few words.', encoding="utf-8")
        errors = validate_note(tmp_path, min_words=1000)
        assert any("short" in e.lower() for e in errors)

    def test_too_short_book_folder(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text('---\ntitle: "Short"\n---\n\nShort.', encoding="utf-8")
        errors = validate_note(tmp_path)
        # Book folder with < 1000 total words should flag
        assert any("short" in e.lower() or "too" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# validate_book_directory
# ---------------------------------------------------------------------------
class TestValidateBookDirectory:
    def test_nonexistent_directory(self, tmp_path):
        report = validate_book_directory(tmp_path / "nonexistent")
        assert len(report["errors"]) >= 1

    def test_empty_directory(self, tmp_path):
        report = validate_book_directory(tmp_path)
        assert any("Missing README" in e for e in report["errors"])

    def test_valid_minimal_directory(self, tmp_path):
        # Create a minimal valid book directory
        readme = tmp_path / "README.md"
        readme.write_text(
            '---\ntitle: "Test"\nauthor: "Author"\nslug: test\n---\n\n'
            + " ".join(["word"] * 1500),
            encoding="utf-8",
        )
        concept1 = tmp_path / "01-Concept-One.md"
        concept1.write_text("# Concept One\n" + " ".join(["word"] * 500), encoding="utf-8")
        concept2 = tmp_path / "02-Concept-Two.md"
        concept2.write_text("# Concept Two\n" + " ".join(["word"] * 500), encoding="utf-8")
        audio = tmp_path / "Audio-Listening-Edition.md"
        audio.write_text("# Audio Edition\n" + " ".join(["word"] * 500), encoding="utf-8")
        quiz = tmp_path / "Quiz.md"
        quiz.write_text("# Quiz\n```quiz\nQ1\n```", encoding="utf-8")
        flashcards = tmp_path / "Flashcards.md"
        flashcards.write_text("# Flashcards\nQ: Test?\nA: Answer.", encoding="utf-8")

        report = validate_book_directory(tmp_path)
        # Should have minimal errors for a well-formed directory
        critical_errors = [e for e in report["errors"] if "Broken MOC" not in e]
        assert len(critical_errors) == 0

    def test_broken_yaml_prefix(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("yaml\n---\ntitle: Test\n---\nContent.", encoding="utf-8")
        report = validate_book_directory(tmp_path)
        assert any("yaml" in e.lower() for e in report["errors"])

    def test_missing_concept_notes_warning(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            '---\ntitle: "Test"\nauthor: "Auth"\nslug: test\n---\n\n'
            + " ".join(["word"] * 1500),
            encoding="utf-8",
        )
        report = validate_book_directory(tmp_path)
        assert any("concept" in w.lower() for w in report["warnings"])

    def test_anti_hallucination_check(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            '---\ntitle: "Test"\n---\n\n'
            + " ".join(["word"] * 1500)
            + "\n\nas an AI language model, I can help.",
            encoding="utf-8",
        )
        report = validate_book_directory(tmp_path)
        assert any("hallucination" in e.lower() or "placeholder" in e.lower() for e in report["errors"])
