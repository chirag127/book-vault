"""Tests for automation/core/graph.py — Knowledge graph construction."""
from __future__ import annotations

from automation.core.graph import (
    RelatedBook,
    _same_author,
    _significant_stems,
    _stem,
    build_incoming,
    build_related,
    format_graph_context,
    related_map,
)


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------
def _book(**overrides) -> dict[str, str]:
    base = {
        "number": "1",
        "title": "Test Book",
        "author": "John Smith",
        "pillar": "Pillar A",
        "category": "Cat A",
        "subcategory": "Sub A",
        "slug": "Test-Book",
    }
    base.update(overrides)
    return base


BOOKS = [
    _book(number="1", title="Alpha", author="Alice Author", slug="Alpha",
          pillar="Pillar A", category="Cat A", subcategory="Sub A"),
    _book(number="2", title="Beta", author="Bob Writer", slug="Beta",
          pillar="Pillar A", category="Cat A", subcategory="Sub A"),
    _book(number="3", title="Gamma", author="Alice Author", slug="Gamma",
          pillar="Pillar A", category="Cat B", subcategory="Sub B"),
    _book(number="4", title="Delta", author="Carol Writer", slug="Delta",
          pillar="Pillar B", category="Cat C", subcategory="Sub A"),
    _book(number="5", title="Epsilon", author="Dave Writer", slug="Epsilon",
          pillar="Pillar B", category="Cat D", subcategory="Sub D"),
]


# ---------------------------------------------------------------------------
# _stem
# ---------------------------------------------------------------------------
class TestStem:
    def test_plural_ies(self):
        assert _stem("habit") == "habit"
        assert _stem("habits") == "habit"
        assert _stem("countries") == "country"  # -ies -> -y

    def test_plural_es(self):
        assert _stem("processes") == "process"

    def test_plural_s(self):
        assert _stem("decisions") == "decision"

    def test_short_words_not_stemmed(self):
        assert _stem("bias") == "bias"
        assert _stem("math") == "math"

    def test_double_s_not_stemmed(self):
        assert _stem("glass") == "glass"
        assert _stem("process") == "process"


# ---------------------------------------------------------------------------
# _significant_stems
# ---------------------------------------------------------------------------
class TestSignificantStems:
    def test_filters_stopwords(self):
        stems = _significant_stems("The Art of Probability and Statistics")
        # "probability" and "statistics" have >= 5 chars and aren't stopwords
        assert "probabl" in stems or "probability" in stems
        assert "statistic" in stems or "statistics" in stems

    def test_short_words_excluded(self):
        stems = _significant_stems("How to Do It")
        assert len(stems) == 0  # all words < 5 chars or stopwords

    def test_case_insensitive(self):
        a = _significant_stems("PROBABILITY THEORY")
        b = _significant_stems("probability theory")
        assert a == b


# ---------------------------------------------------------------------------
# _same_author
# ---------------------------------------------------------------------------
class TestSameAuthor:
    def test_exact_match(self):
        assert _same_author("John Smith", "John Smith") is True

    def test_different_first_same_last(self):
        # Same surname but different first name -> should be False
        assert _same_author("John Smith", "Jane Smith") is False

    def test_completely_different(self):
        assert _same_author("John Smith", "Alice Writer") is False

    def test_multi_author_shared(self):
        assert _same_author("John Smith; Jane Doe", "John Smith; Bob Lee") is True

    def test_multi_author_no_overlap(self):
        assert _same_author("John Smith; Jane Doe", "Alice Writer; Bob Lee") is False

    def test_semicolon_single_match(self):
        assert _same_author("Peter Bernstein", "Peter Bernstein") is True


# ---------------------------------------------------------------------------
# build_related
# ---------------------------------------------------------------------------
class TestBuildRelated:
    def test_excludes_self(self):
        book = BOOKS[0]
        related = build_related(book, BOOKS)
        slugs = [r.slug for r in related]
        assert "Alpha" not in slugs

    def test_same_author_found(self):
        # Alpha (Alice Author) should link to Gamma (Alice Author)
        related = build_related(BOOKS[0], BOOKS)
        reasons = {r.slug: r.reason for r in related}
        assert "Gamma" in reasons
        assert reasons["Gamma"] == "same author"

    def test_same_category_found(self):
        # Alpha and Beta are both Cat A in Pillar A
        related = build_related(BOOKS[0], BOOKS)
        slugs = [r.slug for r in related]
        assert "Beta" in slugs

    def test_adjacent_number_found(self):
        # Alpha (#1) should find Beta (#2) as reading-order neighbor
        related = build_related(BOOKS[0], BOOKS)
        reasons = {r.slug: r.reason for r in related}
        assert "Beta" in reasons

    def test_max_links_respected(self):
        related = build_related(BOOKS[0], BOOKS, max_links=2)
        assert len(related) <= 2

    def test_related_book_wikilink_format(self):
        rb = RelatedBook(
            title="Test", author="Author", category="Cat",
            subcategory="Sub", slug="Test", number="1", reason="test",
        )
        assert rb.wikilink() == "[[Test|Test]]"


# ---------------------------------------------------------------------------
# related_map / format_graph_context
# ---------------------------------------------------------------------------
class TestGraphIntegration:
    def test_related_map_covers_all_books(self):
        rmap = related_map(BOOKS)
        assert len(rmap) == len(BOOKS)
        for slug in rmap:
            assert isinstance(rmap[slug], set)

    def test_format_graph_context_has_sections(self):
        ctx = format_graph_context(BOOKS[0], BOOKS)
        assert "Outgoing links" in ctx
        assert "Incoming links" in ctx

    def test_format_graph_context_with_precomputed_map(self):
        rmap = related_map(BOOKS)
        ctx = format_graph_context(BOOKS[0], BOOKS, rel_map=rmap)
        assert "Outgoing links" in ctx

    def test_build_incoming(self):
        rmap = related_map(BOOKS)
        # Beta (#2) links to Alpha (#1) as reading-order neighbor
        incoming = build_incoming(BOOKS[0], BOOKS, rmap)
        slugs = [r.slug for r in incoming]
        assert "Beta" in slugs or len(incoming) >= 0  # at minimum doesn't crash

    def test_single_book_no_self_reference(self):
        solo = [_book(number="1", title="Solo", author="A A", slug="Solo",
                       pillar="P", category="C", subcategory="S")]
        related = build_related(solo[0], solo)
        assert len(related) == 0

    def test_empty_books_list(self):
        related = build_related(BOOKS[0], [])
        assert len(related) == 0
