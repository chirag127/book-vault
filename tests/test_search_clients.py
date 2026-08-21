from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch
from automation.research.search_clients import (
    crossref_search,
    ddgs_search,
    openlibrary_search,
    wikipedia_search,
    _load_cached,
    _save_cached,
)
from automation.research.research import load_research, save_research, Source


def test_search_cache_roundtrip():
    backend = "test_backend"
    query = "unit test query cache isolated 2"
    sample = [{"title": "Cached Title", "url": "https://example.com"}]
    _save_cached(backend, query, sample)
    loaded = _load_cached(backend, query, ttl_hours=1.0)
    assert loaded is not None
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Cached Title"


def test_openlibrary_search_mock():
    query = "Make It Stick Brown Unique Query 2"
    mock_data = json.dumps({
        "docs": [
            {
                "title": "Make It Stick",
                "author_name": ["Peter C. Brown"],
                "first_publish_year": 2014,
                "subject": ["Learning", "Memory"],
                "key": "/books/OL123M",
            }
        ]
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("automation.research.search_clients.urlopen", return_value=mock_resp):
        results = openlibrary_search(query, max_results=3)
        assert len(results) >= 1
        assert "Make It Stick" in results[0]["title"]


def test_crossref_search_mock():
    query = "Roediger Retrieval Practice Unique Query 2"
    mock_data = json.dumps({
        "message": {
            "items": [
                {
                    "title": ["The Power of Testing Memory"],
                    "author": [{"given": "Henry", "family": "Roediger"}],
                    "published": {"date-parts": [[2006]]},
                    "URL": "https://doi.org/10.1111/j.1745-6916.2006.00012.x",
                    "DOI": "10.1111/j.1745-6916.2006.00012.x",
                }
            ]
        }
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("automation.research.search_clients.urlopen", return_value=mock_resp):
        results = crossref_search(query, max_results=3)
        assert len(results) >= 1
        assert "The Power of Testing Memory" in results[0]["title"]


def test_wikipedia_search_mock():
    query = "Make It Stick Unique Query 2"
    mock_data = json.dumps([
        query,
        ["Testing effect"],
        ["The testing effect is the finding that long-term memory is increased..."],
        ["https://en.wikipedia.org/wiki/Testing_effect"],
    ]).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("automation.research.search_clients.urlopen", return_value=mock_resp):
        results = wikipedia_search(query, max_results=3)
        assert len(results) >= 1
        assert "Testing effect" in results[0]["title"]


def test_load_research_dossier_cache():
    slug = "test-dossier-cache-roundtrip-2"
    sources = [
        Source(
            title="Dossier Source",
            url="https://example.com/source",
            query="test query",
            content="Extracted text body for analysis",
        )
    ]
    save_research(slug, sources)
    loaded = load_research(slug, max_age_hours=1.0)
    assert loaded is not None
    assert len(loaded) == 1
    assert loaded[0].title == "Dossier Source"
    assert loaded[0].content == "Extracted text body for analysis"
