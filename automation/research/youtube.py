"""YouTube Book Summary & Video Lecture Research Client.

Uses yt-dlp to search for top animated book summaries, author lectures, and
high-yield video breakdowns, extracting transcripts and curated watch links.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from ..core.config import ROOT

YOUTUBE_CACHE_DIR = ROOT / "cache" / "youtube"


def _cache_path(query: str) -> Path:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", query)[:120]
    return YOUTUBE_CACHE_DIR / f"{clean}.json"


def _load_cached(query: str, ttl_hours: float = 72.0) -> list[dict[str, Any]] | None:
    path = _cache_path(query)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("saved_at", 0) > ttl_hours * 3600:
            return None
        return data.get("videos", [])
    except Exception:
        return None


def _save_cached(query: str, videos: list[dict[str, Any]]) -> None:
    try:
        YOUTUBE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(query)
        payload = {
            "query": query,
            "saved_at": time.time(),
            "videos": videos,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass


def fetch_video_transcript(video_id: str) -> str:
    """Extract full video transcript via youtube_transcript_api or subtitles with multi-language fallback."""
    # 1. Primary: youtube_transcript_api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        t_list = api.list(video_id)
        transcript = None
        target_langs = ["en", "en-US", "en-GB", "en-CA", "en-IN", "en-AU"]
        try:
            transcript = t_list.find_transcript(target_langs)
        except Exception:
            try:
                transcript = t_list.find_generated_transcript(target_langs)
            except Exception:
                for t in t_list:
                    if t.language_code.startswith("en"):
                        transcript = t
                        break

        if transcript:
            snippets = transcript.fetch()
            full_text = " ".join(item.get("text", "") for item in snippets if item.get("text"))
            cleaned = re.sub(r"\s+", " ", full_text).strip()
            if cleaned:
                return cleaned[:12000]
    except Exception:
        pass

    # 2. Fallback: yt-dlp subtitle JSON extraction
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            subs = (info.get("subtitles") or {}).get("en") or (info.get("automatic_captions") or {}).get("en")
            if subs:
                for sub_entry in subs:
                    if sub_entry.get("url") and sub_entry.get("ext") in ("json3", "vtt"):
                        import urllib.request
                        req = urllib.request.Request(sub_entry["url"], headers={"User-Agent": "UniversalBookVault/1.0"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            raw = resp.read().decode("utf-8", errors="ignore")
                            if sub_entry.get("ext") == "json3":
                                data = json.loads(raw)
                                texts = [e.get("utf8", "") for event in data.get("events", []) for e in event.get("segs", [])]
                                return re.sub(r"\s+", " ", " ".join(texts)).strip()[:12000]
                            else:
                                clean_vtt = re.sub(r"<[^>]+>|WEBVTT[\s\S]*?\n\n|\d{2}:\d{2}:\d{2}[\s\S]*?-->[\s\S]*?\n", " ", raw)
                                return re.sub(r"\s+", " ", clean_vtt).strip()[:12000]
    except Exception:
        pass

    return ""


def search_youtube_summaries(title: str, author: str = "", max_results: int = 5) -> list[dict[str, Any]]:
    """Search YouTube for high-yield book summaries, author lectures, and animated overviews."""
    first_author = author.split(";")[0].strip() if author else ""
    query = f"{title} {first_author} book summary".strip()

    cached = _load_cached(query)
    if cached is not None:
        return cached

    videos: list[dict[str, Any]] = []

    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            entries = info.get("entries", []) if info else []

            for entry in entries:
                if not entry:
                    continue
                vid_id = entry.get("id", "")
                if not vid_id:
                    continue

                vid_title = entry.get("title", "")
                channel = entry.get("uploader", "") or entry.get("channel", "YouTube")
                url = f"https://www.youtube.com/watch?v={vid_id}"
                duration = entry.get("duration")

                # Try fetching transcript
                transcript = fetch_video_transcript(vid_id)

                videos.append({
                    "id": vid_id,
                    "title": vid_title,
                    "channel": channel,
                    "url": url,
                    "duration": duration,
                    "transcript": transcript if transcript else "",
                    "has_transcript": bool(transcript),
                })

        if videos:
            _save_cached(query, videos)
    except Exception as exc:
        print(f"[youtube] Search error for '{query}': {exc}")

    return videos


def format_youtube_markdown_section(videos: list[dict[str, Any]], limit: int = 3) -> str:
    """Format top YouTube summaries into a clean Markdown section."""
    if not videos:
        return ""

    lines = ["## 🎥 Curated Video Summaries & Lectures\n"]
    for v in videos[:limit]:
        title = v.get("title", "Book Summary").replace("[", "").replace("]", "")
        channel = v.get("channel", "YouTube")
        url = v.get("url", "")
        lines.append(f"- [{title}]({url}) — *by {channel}*")

    return "\n".join(lines) + "\n"
