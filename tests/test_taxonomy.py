from __future__ import annotations

from automation.core.taxonomy import PILLAR_DIRS


def test_pillar_dirs_count():
    assert len(PILLAR_DIRS) == 12


def test_pillar_dirs_format():
    for name, folder in PILLAR_DIRS.items():
        assert folder.startswith(("01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-", "09-", "10-", "11-", "12-"))
        assert len(name) > 3
