from __future__ import annotations

from automation.core.taxonomy import PILLAR_DIRS


def test_pillar_dirs_count():
    assert len(PILLAR_DIRS) == 13


def test_pillar_dirs_format():
    for name, folder in PILLAR_DIRS.items():
        assert folder.startswith(tuple(f"{i:02d}-" for i in range(1, 14)))
        assert len(name) > 3

