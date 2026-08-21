from __future__ import annotations

from automation.taxonomy import PILLAR_DIRS


def test_pillar_dirs_count():
    assert len(PILLAR_DIRS) == 12, "Expected exactly 12 master pillars."


def test_pillar_dirs_format():
    for name, folder in PILLAR_DIRS.items():
        assert len(name) > 0
        assert folder[:2].isdigit(), f"Folder {folder} must start with 2-digit number."
        assert "-" in folder, f"Folder {folder} must use hyphenated slug."
