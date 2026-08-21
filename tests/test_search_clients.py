from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from automation.search_clients import (
    openlibrary_search,
    crossref_search,
    wikipedia_search,
    _save_cached,
    _load_cached,
)


def test_search_cache_roundtrip(tmp_path):
    query = "unit_test_query_cache_isolated"
    sample = [{"title": "Test Title", "url": "https://example.com", "snippet": "Sample text", "source": "test"}]
    _save_cached("test_backend", query, sample)
    cached = _load_cached("test_backend", query, ttl_hours=1.0)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0]["title"] == "Test Title"


def test_openlibrary_search_mock():
    mock_data = {
        "docs": [
            {
                "title": "Make It Stick",
                "author_name": ["Peter C. Brown"],
                "first_publish_year": 2014,
                "subject": ["Cognition", "Learning"],
                "key": "/books/OL123M",
            }
        ]
    }
    with patch("automation.search_clients._load_cached", return_value=None), \
         patch("automation.search_clients.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        results = openlibrary_search("Make It Stick Brown Unique Query", max_results=2)
        assert len(results) >= 1
        assert "Make It Stick" in results[0]["title"]
        assert results[0]["source"] == "openlibrary"


def test_crossref_search_mock():
    mock_data = {
        "message": {
            "items": [
                {
                    "title": ["The Power of Testing: Memory Retrieval"],
                    "DOI": "10.1037/0033-295X.113.2.181",
                    "URL": "https://doi.org/10.1037/0033-295X.113.2.181",
                    "container-title": ["Psychological Review"],
                    "published": {"date-parts": [[2006]]},
                    "author": [{"given": "Henry", "family": "Roediger"}],
                }
            ]
        }
    }
    with patch("automation.search_clients._load_cached", return_value=None), \
         patch("automation.search_clients.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        results = crossref_search("Roediger Retrieval Practice Unique Query", max_results=2)
        assert len(results) >= 1
        assert "Crossref" in results[0]["title"]
        assert "Roediger" in results[0]["snippet"]


def test_wikipedia_search_mock():
    mock_data = [
        "Make It Stick",
        ["Make It Stick (book)"],
        ["A book about the science of successful learning."],
        ["https://en.wikipedia.org/wiki/Make_It_Stick"],
    ]
    with patch("automation.search_clients._load_cached", return_value=None), \
         patch("automation.search_clients.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        results = wikipedia_search("Make It Stick Unique Query", max_results=2)
        assert len(results) >= 1
        assert "Wikipedia" in results[0]["title"]
        assert results[0]["source"] == "wikipedia"


def test_load_research_dossier_cache(tmp_path):
    from automation.research import save_research, load_research, Source
    slug = "test-cached-slug"
    test_file = tmp_path / f"{slug}.json"
    book = {"title": "Test Book", "author": "Author Name", "slug": slug}
    sources = [Source("Title 1", "https://example.com", "q1", "Content 1")]
    save_research(test_file, book, sources)
    with patch("automation.research.RESEARCH_CACHE_DIR", tmp_path):
        loaded = load_research(slug)
        assert loaded is not None
        assert len(loaded) == 1
        assert loaded[0].title == "Title 1"

