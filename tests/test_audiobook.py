from __future__ import annotations

from automation.audio.synthesize_audiobook import extract_audio_chapters


def test_extract_audio_chapters():
    sample_md = """---
title: Make It Stick
---

# Make It Stick — Audio Edition
Welcome to the audio listening edition of Make It Stick.

## Part 1: Core Thesis
Learning that is hard sticks better than effortless rereading.

## Part 2: Practical Protocols
Space out your retrieval practice.
"""
    chapters = extract_audio_chapters(sample_md)
    assert len(chapters) >= 2
    assert chapters[0].word_count > 0
    assert chapters[1].title == "Part 1: Core Thesis"
    assert chapters[1].start_time_sec >= 0
