from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Any
import httpx
from ddgs import DDGS
from youtube_transcript_api import YouTubeTranscriptApi


@dataclass
class YouTubeVideo:
    title: str
    url: str
    video_id: str
    channel: str
    transcript: str = ""


def _extract_video_id(url_or_id: str) -> str:
    if "youtu.be/" in url_or_id:
        return url_or_id.split("youtu.be/")[-1].split("?")[0]
    if "youtube.com/watch" in url_or_id:
        parsed = urllib.parse.urlparse(url_or_id)
        params = urllib.parse.parse_qs(parsed.query)
        return params.get("v", [""])[0]
    return url_or_id


def fetch_youtube_transcript(video_id: str, max_chars: int = 4000) -> str:
    """Fetch closed captions / transcript text with automatic fallback for IP blocks."""
    # Attempt 1: Direct YouTubeTranscriptApi
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id)
        full_text = " ".join([getattr(t, "text", "") for t in fetched if getattr(t, "text", "")])
        full_text = re.sub(r"\s+", " ", full_text).strip()
        if full_text:
            return full_text[:max_chars] + "..." if len(full_text) > max_chars else full_text
    except Exception:
        pass

    # Attempt 2: Public YouTube video page description & captions metadata
    try:
        resp = httpx.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=8.0,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            # Extract shortDescription
            desc_match = re.search(r'"shortDescription":"(.*?)","isCrawlable"', resp.text)
            if desc_match:
                raw_desc = desc_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore")
                clean_desc = re.sub(r"\\n", "\n", raw_desc).strip()
                if len(clean_desc) > 80:
                    return f"[Video Overview & Timestamps]\n{clean_desc[:max_chars]}"
    except Exception:
        pass

    return ""


def search_youtube_summaries(title: str, author: str, max_results: int = 3, fetch_transcripts: bool = True) -> list[YouTubeVideo]:
    """Search DuckDuckGo for top YouTube book summaries, extracting metadata and transcripts."""
    query = f"site:youtube.com {title} {author} animated book summary review"
    videos: list[YouTubeVideo] = []
    seen_ids: set[str] = set()

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 2):
                href = r.get("href", "")
                if "youtube.com/watch" not in href and "youtu.be/" not in href:
                    continue
                vid_id = _extract_video_id(href)
                if not vid_id or vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)

                vid_title = r.get("title", f"{title} Summary")
                # Clean video title
                vid_title = re.sub(r"\s*-\s*YouTube$", "", vid_title, flags=re.I)
                body = r.get("body", "")

                transcript = ""
                if fetch_transcripts:
                    transcript = fetch_youtube_transcript(vid_id, max_chars=3500)

                videos.append(
                    YouTubeVideo(
                        title=vid_title,
                        url=f"https://www.youtube.com/watch?v={vid_id}",
                        video_id=vid_id,
                        channel=body[:60] if body else "YouTube",
                        transcript=transcript,
                    )
                )
                if len(videos) >= max_results:
                    break
    except Exception:
        pass

    return videos


def format_youtube_markdown_section(videos: list[YouTubeVideo]) -> str:
    """Render curated video summary markdown cards for README.md."""
    if not videos:
        return ""

    lines = [
        "## 🎥 Curated Video Summaries & Key Lessons",
        "",
        "> High-yield visual summaries and animated breakdowns for multi-modal learning:",
        "",
    ]

    for v in videos:
        lines.append(f"- 🎬 **[{v.title}]({v.url})**")
        if v.transcript:
            snippet = v.transcript[:180].strip().replace("\n", " ")
            lines.append(f"  > *\"{snippet}...\"*")
        lines.append("")

    return "\n".join(lines).strip()
