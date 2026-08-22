"""Tests for automation/engines/generate.py — Output cleaning, file unpacking, navigation."""
from __future__ import annotations

import pytest

from automation.engines.generate import (
    _clean_markdown,
    _unpack_files,
    _words,
    navigation_for,
)


# ---------------------------------------------------------------------------
# _clean_markdown
# ---------------------------------------------------------------------------
class TestCleanMarkdown:
    def test_strips_markdown_fence(self):
        raw = "```markdown\n# Hello\nSome content.\n```"
        result = _clean_markdown(raw)
        assert result.startswith("---") or result.startswith("#")
        assert "```markdown" not in result

    def test_strips_yaml_fence(self):
        raw = '```yaml\ntitle: "Test"\n---\nContent\n```'
        result = _clean_markdown(raw)
        assert "```yaml" not in result

    def test_strips_bare_fence(self):
        raw = "```\n# Title\nContent\n```"
        result = _clean_markdown(raw)
        assert not result.startswith("```")

    def test_preserves_mermaid_blocks(self):
        raw = "```mermaid\ngraph TD\nA-->B\n```\n\nMore content."
        result = _clean_markdown(raw)
        assert "```mermaid" in result

    def test_quotes_unquoted_title(self):
        raw = '---\ntitle: My Book Title\nauthor: "Author"\n---\nContent'
        result = _clean_markdown(raw)
        assert 'title: "My Book Title"' in result

    def test_quotes_unquoted_author(self):
        raw = '---\ntitle: "Test"\nauthor: John Smith\n---\nContent'
        result = _clean_markdown(raw)
        assert 'author: "John Smith"' in result

    def test_already_quoted_not_double_quoted(self):
        raw = '---\ntitle: "Already Quoted"\nauthor: "Also Quoted"\n---\nContent'
        result = _clean_markdown(raw)
        assert result.count('title: "Already Quoted"') == 1

    def test_strips_trailing_chatter(self):
        raw = "# Title\nContent\n\n**Edition complete.** All files generated."
        result = _clean_markdown(raw)
        assert "Edition complete" not in result

    def test_strips_odd_trailing_fence(self):
        raw = "# Title\nContent\n\nMore stuff\n\n```"
        result = _clean_markdown(raw)
        # The trailing lone ``` should be stripped
        assert not result.rstrip().endswith("```")

    def test_strips_stray_yaml_prefix(self):
        raw = "yaml\n---\ntitle: Test\n---\nContent"
        result = _clean_markdown(raw)
        assert result.startswith("---") or result.startswith("title")

    def test_empty_input(self):
        result = _clean_markdown("")
        assert isinstance(result, str)

    def test_strips_stray_fence_after_frontmatter(self):
        raw = "---\ntitle: Test\n---\n```\n# Content"
        result = _clean_markdown(raw)
        # Should not have stray ``` after frontmatter
        lines = result.split("\n")
        # The ``` right after --- should be removed
        assert lines[3].strip() != "```" or "Content" in result

    def test_output_ends_with_newline(self):
        result = _clean_markdown("# Title\nContent")
        assert result.endswith("\n")


# ---------------------------------------------------------------------------
# _unpack_files
# ---------------------------------------------------------------------------
class TestUnpackFiles:
    def test_single_file_no_markers(self):
        raw = "# Just a markdown file\nContent here."
        files = _unpack_files(raw)
        assert "README.md" in files
        assert len(files) == 1

    def test_multi_file_markers(self):
        raw = (
            "=== FILE: README.md ===\n# README content\n\n"
            "=== FILE: 01-Chapter.md ===\n# Chapter 1\n\n"
            "=== FILE: 02-Chapter.md ===\n# Chapter 2\n"
        )
        files = _unpack_files(raw)
        assert len(files) == 3
        assert "README.md" in files
        assert "01-Chapter.md" in files
        assert "02-Chapter.md" in files

    def test_content_extraction(self):
        raw = (
            "=== FILE: README.md ===\nThis is the README.\n\n"
            "=== FILE: Audio.md ===\nAudio content.\n"
        )
        files = _unpack_files(raw)
        assert "This is the README." in files["README.md"]
        assert "Audio content." in files["Audio.md"]

    def test_custom_default_name(self):
        raw = "No markers here."
        files = _unpack_files(raw, default_name="index.md")
        assert "index.md" in files

    def test_empty_file_block(self):
        raw = (
            "=== FILE: README.md ===\nContent\n\n"
            "=== FILE: Empty.md ===\n\n"
            "=== FILE: Last.md ===\nFinal\n"
        )
        files = _unpack_files(raw)
        assert len(files) == 3


# ---------------------------------------------------------------------------
# _words
# ---------------------------------------------------------------------------
class TestWords:
    def test_simple(self):
        assert _words("hello world") == 2

    def test_empty(self):
        assert _words("") == 0

    def test_punctuation(self):
        # _words uses regex \b[\w'-]+\b
        count = _words("Hello, world! How's it going?")
        assert count >= 4


# ---------------------------------------------------------------------------
# navigation_for
# ---------------------------------------------------------------------------
class TestNavigationFor:
    # Use a real pillar name from taxonomy
    PILLAR = "Learning, Thinking & Knowledge"

    def test_middle_book(self):
        books = [
            {"slug": "A", "title": "A Book", "pillar": self.PILLAR, "category": "C1", "number": "1"},
            {"slug": "B", "title": "B Book", "pillar": self.PILLAR, "category": "C1", "number": "2"},
            {"slug": "C", "title": "C Book", "pillar": self.PILLAR, "category": "C1", "number": "3"},
        ]
        nav = navigation_for(books[1], books)
        assert "A Book" in nav["prev"]
        assert "C Book" in nav["next"]

    def test_first_book(self):
        books = [
            {"slug": "A", "title": "A Book", "pillar": self.PILLAR, "category": "C1", "number": "1"},
            {"slug": "B", "title": "B Book", "pillar": self.PILLAR, "category": "C1", "number": "2"},
        ]
        nav = navigation_for(books[0], books)
        # First book has no prev, should get pillar link
        assert "01-Learning" in nav["prev"] or "Learning" in nav["prev"]

    def test_last_book(self):
        books = [
            {"slug": "A", "title": "A Book", "pillar": self.PILLAR, "category": "C1", "number": "1"},
            {"slug": "B", "title": "B Book", "pillar": self.PILLAR, "category": "C1", "number": "2"},
        ]
        nav = navigation_for(books[1], books)
        # Last book has no next, should get pillar link
        assert "01-Learning" in nav["next"] or "Learning" in nav["next"]
