"""Tests for automation/core/length.py — Content-adaptive word bounds."""
from __future__ import annotations

from automation.core.length import (
    BOOK_TYPE_RANGES,
    DEEP_PILLARS,
    LIGHT_PILLARS,
    MAX_CAP,
    MIN_FLOOR,
    length_label,
    word_bounds,
)


class TestWordBounds:
    """word_bounds() derives (min, max) from book metadata."""

    def test_unknown_type_uses_default(self):
        lo, hi = word_bounds({"book_type": "Unknown", "pillar": "Some Pillar"})
        assert lo >= MIN_FLOOR
        assert hi <= MAX_CAP
        assert hi > lo

    def test_practical_guide_is_shorter_than_academic(self):
        practical, _ = word_bounds({"book_type": "Practical Guide", "pillar": "Business"})
        academic, _ = word_bounds({"book_type": "Academic Text", "pillar": "Mathematics"})
        assert practical < academic

    def test_s_priority_raises_ceiling(self):
        s_book = {"book_type": "Practical Guide", "priority": "S", "pillar": "Business"}
        a_book = {"book_type": "Practical Guide", "priority": "A", "pillar": "Business"}
        _, s_hi = word_bounds(s_book)
        _, a_hi = word_bounds(a_book)
        assert s_hi > a_hi

    def test_advanced_difficulty_raises_both(self):
        adv = {"book_type": "Case Study", "difficulty": "Advanced", "pillar": "Business"}
        inter = {"book_type": "Case Study", "difficulty": "Intermediate", "pillar": "Business"}
        adv_lo, adv_hi = word_bounds(adv)
        inter_lo, inter_hi = word_bounds(inter)
        assert adv_lo > inter_lo
        assert adv_hi > inter_hi

    def test_deep_pillar_raises_ceiling(self):
        deep = {"book_type": "Handbook / Reference", "pillar": "Mathematics, Statistics & Quantitative Logic"}
        other = {"book_type": "Handbook / Reference", "pillar": "Business, Strategy & Enterprise"}
        _, deep_hi = word_bounds(deep)
        _, other_hi = word_bounds(other)
        assert deep_hi > other_hi

    def test_light_pillar_caps_ceiling(self):
        light = {"book_type": "Handbook / Reference", "pillar": "Learning, Cognition & Meta-Skills"}
        other = {"book_type": "Handbook / Reference", "pillar": "Mathematics, Statistics & Quantitative Logic"}
        _, light_hi = word_bounds(light)
        _, other_hi = word_bounds(other)
        assert light_hi <= other_hi

    def test_always_respects_floor_and_cap(self):
        # Extreme values: S-priority Advanced in deep pillar
        extreme = {
            "book_type": "Academic Text",
            "priority": "S",
            "difficulty": "Advanced",
            "pillar": "Computer Science & Software Engineering",
        }
        lo, hi = word_bounds(extreme)
        assert lo >= MIN_FLOOR
        assert hi <= MAX_CAP
        assert hi > lo

    def test_all_book_types_produce_valid_ranges(self):
        for book_type in BOOK_TYPE_RANGES:
            lo, hi = word_bounds({"book_type": book_type, "pillar": "Business"})
            assert lo >= MIN_FLOOR
            assert hi <= MAX_CAP
            assert hi > lo

    def test_min_range_gap_is_1000(self):
        """hi must be at least lo + 1000 after all adjustments."""
        tight = {"book_type": "Practical Guide", "pillar": "Business"}
        lo, hi = word_bounds(tight)
        assert hi >= lo + 1000


class TestLengthLabel:
    """length_label() maps max_words to a human string."""

    def test_concise(self):
        assert length_label(1000, 5000) == "concise"

    def test_substantial(self):
        assert length_label(2000, 7000) == "substantial"

    def test_maximum_depth(self):
        assert length_label(3000, 12000) == "maximum-depth"

    def test_exact_boundary_concise(self):
        assert length_label(1000, 5000) == "concise"

    def test_exact_boundary_substantial(self):
        assert length_label(1000, 8000) == "substantial"
