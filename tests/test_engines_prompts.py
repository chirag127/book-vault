"""Tests for automation/engines/prompts.py — Prompt builders produce valid structure."""
from __future__ import annotations

from automation.engines.prompts import (
    SYSTEM_PROMPT,
    TEMPLATE_VERSION,
    build_audio_tts_prompt,
    build_modular_reading_prompt,
    build_quiz_prompt,
)


BOOK = {
    "title": "Test Book Title",
    "author": "Test Author",
    "slug": "Test-Book-Title",
    "pillar": "Learning, Thinking & Knowledge",
    "category": "Learning Science",
    "subcategory": "Cognitive Load",
    "difficulty": "Intermediate",
    "first_published": "2020",
    "published": "2020",
}


class TestSystemPrompt:
    def test_not_empty(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_mentions_hallucination(self):
        assert "hallucination" in SYSTEM_PROMPT.lower()

    def test_mentions_obsidian(self):
        assert "obsidian" in SYSTEM_PROMPT.lower() or "wikilink" in SYSTEM_PROMPT.lower()

    def test_mentions_mermaid(self):
        assert "mermaid" in SYSTEM_PROMPT.lower()


class TestTemplateVersion:
    def test_is_string(self):
        assert isinstance(TEMPLATE_VERSION, str)
        assert len(TEMPLATE_VERSION) > 5


class TestBuildModularReadingPrompt:
    def test_returns_two_messages(self):
        msgs = build_modular_reading_prompt(BOOK, "Test sources.", min_words=2000, max_words=5000)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_user_contains_book_title(self):
        msgs = build_modular_reading_prompt(BOOK, "Test sources.")
        assert "Test Book Title" in msgs[1]["content"]

    def test_user_contains_sources(self):
        msgs = build_modular_reading_prompt(BOOK, "My research dossier content.")
        assert "My research dossier content." in msgs[1]["content"]

    def test_user_contains_file_markers(self):
        msgs = build_modular_reading_prompt(BOOK, "Sources.")
        assert "=== FILE:" in msgs[1]["content"]

    def test_user_contains_word_targets(self):
        msgs = build_modular_reading_prompt(BOOK, "Sources.", min_words=2000, max_words=5000)
        assert "2000" in msgs[1]["content"]
        assert "5000" in msgs[1]["content"]

    def test_graph_context_included(self):
        msgs = build_modular_reading_prompt(BOOK, "Sources.", graph="Outgoing links:\n- [[Some-Book]]")
        assert "Outgoing links" in msgs[1]["content"]

    def test_navigation_included(self):
        nav = {"prev": "[[Prev|Prev]]", "category": "[[Cat|Cat]]", "next": "[[Next|Next]]"}
        msgs = build_modular_reading_prompt(BOOK, "Sources.", nav=nav)
        assert "Prev" in msgs[1]["content"]

    def test_anti_hallucination_notice(self):
        msgs = build_modular_reading_prompt(BOOK, "Sources.")
        assert "anti-hallucination" in msgs[1]["content"].lower() or "hallucination" in msgs[1]["content"].lower()


class TestBuildAudioTTSPrompt:
    def test_returns_two_messages(self):
        msgs = build_audio_tts_prompt(BOOK, "Test sources.")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_user_contains_book_title(self):
        msgs = build_audio_tts_prompt(BOOK, "Test sources.")
        assert "Test Book Title" in msgs[1]["content"]

    def test_user_mentions_tts(self):
        msgs = build_audio_tts_prompt(BOOK, "Sources.")
        assert "tts" in msgs[1]["content"].lower() or "audio" in msgs[1]["content"].lower()


class TestBuildQuizPrompt:
    def test_returns_two_messages(self):
        msgs = build_quiz_prompt(BOOK, "Test sources.")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_user_contains_quiz_block(self):
        msgs = build_quiz_prompt(BOOK, "Sources.")
        assert "```quiz" in msgs[1]["content"]

    def test_user_contains_book_title(self):
        msgs = build_quiz_prompt(BOOK, "Sources.")
        assert "Test Book Title" in msgs[1]["content"]
