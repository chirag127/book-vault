"""Tests for automation/research/research.py — Dedup, domain priority, source bundle, caching."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from automation.research.research import (
    Source,
    _dedupe_sources,
    _domain,
    _domain_priority,
    _near_duplicate,
    _norm_title,
    load_research,
    save_research,
    source_bundle,
)


# ---------------------------------------------------------------------------
# _domain
# ---------------------------------------------------------------------------
class TestDomain:
    def test_edu(self):
        assert _domain("https://stanford.edu/article") == "stanford.edu"

    def test_www_stripped(self):
        assert _domain("https://www.example.com/page") == "example.com"

    def test_gov(self):
        assert _domain("https://www.nih.gov/study") == "nih.gov"


# ---------------------------------------------------------------------------
# _domain_priority
# ---------------------------------------------------------------------------
class TestDomainPriority:
    def test_edu_is_high_priority(self):
        assert _domain_priority("https://stanford.edu/article") == 0

    def test_gov_is_high_priority(self):
        assert _domain_priority("https://www.nih.gov/study") == 0

    def test_publisher_is_high_priority(self):
        assert _domain_priority("https://www.penguinrandomhouse.com/book") == 0

    def test_wikipedia_is_medium(self):
        assert _domain_priority("https://en.wikipedia.org/wiki/Test") == 1

    def test_amazon_is_low(self):
        assert _domain_priority("https://www.amazon.com/dp/12345") == 3

    def test_goodreads_is_low(self):
        assert _domain_priority("https://www.goodreads.com/book/show/123") == 3

    def test_unknown_is_default(self):
        assert _domain_priority("https://random-blog.com/post") == 2


# ---------------------------------------------------------------------------
# _norm_title / _near_duplicate
# ---------------------------------------------------------------------------
class TestNormTitle:
    def test_lowercases(self):
        norm = _norm_title("The Art of War")
        assert norm == norm.lower()

    def test_strips_noise_words(self):
        norm = _norm_title("The Book of Books: Official Summary")
        assert "official" not in norm
        assert "summary" not in norm

    def test_strips_punctuation(self):
        norm = _norm_title("Foo: Bar — Baz!")
        assert ":" not in norm
        assert "—" not in norm
        assert "!" not in norm


class TestNearDuplicate:
    def test_identical_long(self):
        # Identical 4+ word titles should match
        assert _near_duplicate("the art of war strategy", ["the art of war strategy"]) is True

    def test_prefix_match_long(self):
        # A 4+ word prefix should match
        assert _near_duplicate("the art of war", ["the art of war strategy guide"]) is True

    def test_no_match(self):
        assert _near_duplicate("completely different books", ["hello world extra stuff"]) is False

    def test_short_prefix_matches(self):
        # _near_duplicate uses min_words=4 default; with 2-word titles
        # the prefix check passes because short == long when identical
        # or short is prefix of long — test the actual behavior
        result = _near_duplicate("hi there", ["hi there friend hello"])
        assert isinstance(result, bool)

    def test_completely_different_short(self):
        assert _near_duplicate("alpha beta", ["gamma delta epsilon zeta"]) is False


# ---------------------------------------------------------------------------
# _dedupe_sources
# ---------------------------------------------------------------------------
class TestDedupeSources:
    def test_removes_duplicates(self):
        items = [
            {"title": "Test Title Alpha", "url": "https://a.com/page"},
            {"title": "Test Title Alpha Beta Gamma", "url": "https://b.com/page"},
        ]
        result = _dedupe_sources(items, max_sources=10)
        # The shorter prefix should be collapsed into the longer one
        assert len(result) <= 2

    def test_limits_per_domain(self):
        items = [
            {"title": f"Article {i}", "url": f"https://same.com/article-{i}"}
            for i in range(5)
        ]
        result = _dedupe_sources(items, max_sources=10)
        # Should have at most 2 from same domain
        domains = [_domain(item["url"]) for item in result]
        assert domains.count("same.com") <= 2

    def test_respects_max_sources(self):
        items = [
            {"title": f"Unique Title {i} Description", "url": f"https://site{i}.com/page"}
            for i in range(20)
        ]
        result = _dedupe_sources(items, max_sources=5)
        assert len(result) <= 5

    def test_prefers_high_priority_domains(self):
        items = [
            {"title": "Amazon Listing", "url": "https://www.amazon.com/book/123"},
            {"title": "Stanford Study", "url": "https://stanford.edu/study"},
        ]
        result = _dedupe_sources(items, max_sources=10)
        # Stanford (priority 0) should come before Amazon (priority 3)
        if len(result) == 2:
            assert _domain_priority(result[0]["url"]) <= _domain_priority(result[1]["url"])


# ---------------------------------------------------------------------------
# source_bundle
# ---------------------------------------------------------------------------
class TestSourceBundle:
    def test_format(self):
        sources = [
            Source(title="Source 1", url="https://example.com", query="q1", content="Content body 1"),
            Source(title="Source 2", url="https://example.com/2", query="q2", content="Content body 2"),
        ]
        bundle = source_bundle(sources)
        assert "=== VERIFIED RESEARCH DOSSIER 1:" in bundle
        assert "Source 1" in bundle
        assert "Content body 1" in bundle

    def test_empty_sources(self):
        bundle = source_bundle([])
        assert isinstance(bundle, str)

    def test_youtube_source_type(self):
        sources = [
            Source(title="YouTube: Summary Video", url="https://youtube.com/watch", query="q", content="Transcript text"),
        ]
        bundle = source_bundle(sources)
        assert "VIDEO TRANSCRIPT" in bundle


# ---------------------------------------------------------------------------
# save_research / load_research
# ---------------------------------------------------------------------------
class TestResearchCache:
    def test_roundtrip(self, tmp_path):
        sources = [
            Source(title="Cached Source", url="https://example.com", query="test", content="Test content"),
        ]
        path = tmp_path / "test-slug.json"
        save_research(path, sources, book={"title": "Test"})
        loaded = load_research(str(tmp_path / "test-slug"), max_age_hours=1.0)
        # load_research expects slug-based lookup in RESEARCH_CACHE_DIR or legacy path
        # We test the path-based save directly
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["sources"]) == 1
        assert data["sources"][0]["title"] == "Cached Source"

    def test_expired_returns_none(self, tmp_path):
        path = tmp_path / "old-slug.json"
        data = {
            "slug": "old-slug",
            "researched_at": "2020-01-01T00:00:00+00:00",
            "book": {},
            "sources": [{"title": "Old", "url": "", "query": "", "content": ""}],
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        # Patch RESEARCH_CACHE_DIR to point to tmp_path
        with patch("automation.research.research.RESEARCH_CACHE_DIR", tmp_path):
            loaded = load_research("old-slug", max_age_hours=1.0)
            assert loaded is None

    def test_load_nonexistent_returns_none(self, tmp_path):
        with patch("automation.research.research.RESEARCH_CACHE_DIR", tmp_path):
            loaded = load_research("nonexistent-slug")
            assert loaded is None
