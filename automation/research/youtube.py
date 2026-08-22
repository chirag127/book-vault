from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

import httpx
from ddgs import DDGS


@dataclass
class YouTubeVideo:
    title: str
    url: str
    video_id: str
    channel: str
    transcript: str = ""


def extract_video_id(url_or_id: str) -> str:
    """Extract 11-char YouTube video ID from various URL structures."""
    if "youtu.be/" in url_or_id:
        return url_or_id.split("youtu.be/")[-1].split("?")[0]
    if "youtube.com/watch" in url_or_id:
        parsed = urllib.parse.urlparse(url_or_id)
        params = urllib.parse.parse_qs(parsed.query)
        return params.get("v", [""])[0]
    return url_or_id


class _SilentLogger:
    def debug(self, msg: str) -> None: pass
    def warning(self, msg: str) -> None: pass
    def error(self, msg: str) -> None: pass


def extract_transcript_from_yt_dlp(url: str, max_chars: int = 4000) -> str:
    """Attempt transcript extraction using yt-dlp metadata with browser clients."""
    try:
        import yt_dlp

        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "quiet": True,
            "no_warnings": True,
            "logger": _SilentLogger(),
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web_creator", "web", "ios"],
                }
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get("subtitles") or info.get("automatic_captions") or {}
            for lang in ["en", "en-US", "en-GB"]:
                if lang in subs:
                    entries = subs[lang]
                    vtt_url = next((e.get("url") for e in entries if e.get("ext") in ("vtt", "json3", "srv3")), None)
                    if vtt_url:
                        raw = httpx.get(vtt_url, timeout=6.0).text
                        clean = re.sub(r"<[^>]+>", " ", raw)
                        clean = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}", " ", clean)
                        clean = re.sub(r"\s+", " ", clean).strip()
                        if clean:
                            return clean[:max_chars] + "..." if len(clean) > max_chars else clean

            # Fallback to rich video description
            desc = info.get("description", "").strip()
            if len(desc) > 80:
                return f"[YouTube Overview & Summary Breakdown]\n{desc[:max_chars]}"
    except Exception:
        pass
    return ""


def extract_direct_captions(video_id: str, max_chars: int = 4000) -> str:
    """Fetch public caption tracks directly via Web Player JSON."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            page = resp.read().decode("utf-8", errors="ignore")

        # Search for caption tracks in player response
        match = re.search(r'captionTracks\\":(\[.*?\])', page)
        if not match:
            match = re.search(r'"captionTracks":(\[.*?\])', page)
        if match:
            raw_str = match.group(1).replace(r'\"', '"')
            tracks = json.loads(raw_str)
            for track in tracks:
                track_url = track.get("baseUrl")
                if track_url:
                    with urllib.request.urlopen(track_url, timeout=5) as c_resp:
                        xml_data = c_resp.read().decode("utf-8", errors="ignore")
                    text = re.sub(r"<[^>]+>", " ", xml_data)
                    text = html.unescape(text)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text:
                        return text[:max_chars] + "..." if len(text) > max_chars else text

        # Extract YouTube shortDescription if captions are protected
        desc_match = re.search(r'"shortDescription":"(.*?)","isCrawlable"', page)
        if desc_match:
            raw_desc = desc_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore")
            clean_desc = re.sub(r"\\n", "\n", raw_desc).strip()
            if len(clean_desc) > 80:
                return f"[YouTube Overview & Summary Breakdown]\n{clean_desc[:max_chars]}"
    except Exception:
        pass
    return ""


def fetch_youtube_transcript(video_id_or_url: str, max_chars: int = 4000) -> str:
    """Fetch video transcript using multi-stage extraction (yt-dlp -> Direct Web Captions -> Description)."""
    vid_id = extract_video_id(video_id_or_url)
    full_url = f"https://www.youtube.com/watch?v={vid_id}"

    # 1. Direct Web Captions
    transcript = extract_direct_captions(vid_id, max_chars=max_chars)
    if transcript:
        return transcript

    # 2. yt-dlp Extractor
    transcript = extract_transcript_from_yt_dlp(full_url, max_chars=max_chars)
    if transcript:
        return transcript

    return ""


def search_youtube_summaries(
    title: str, author: str, max_results: int = 3, fetch_transcripts: bool = True
) -> list[YouTubeVideo]:
    """Search for top curated book summary videos using yt-dlp directly (with DDGS fallback)."""
    clean_query = f"{title} {author} animated book summary review".strip()
    videos: list[YouTubeVideo] = []
    seen_ids: set[str] = set()

    # 1. Primary Search: Native yt-dlp search (`ytsearch`)
    try:
        import yt_dlp

        ydl_opts = {
            "skip_download": True,
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
            "logger": _SilentLogger(),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_target = f"ytsearch{max_results * 2}:{clean_query}"
            res = ydl.extract_info(search_target, download=False)
            entries = res.get("entries", []) if res else []
            for e in entries:
                vid_id = e.get("id") or extract_video_id(e.get("url", ""))
                if not vid_id or vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)

                vid_title = e.get("title") or f"{title} Summary"
                uploader = e.get("uploader") or e.get("channel") or "YouTube"
                desc = e.get("description") or ""

                transcript = ""
                if fetch_transcripts:
                    transcript = fetch_youtube_transcript(vid_id, max_chars=3500)
                if not transcript and desc:
                    transcript = f"[Video Summary & Overview]\n{desc.strip()}"

                videos.append(
                    YouTubeVideo(
                        title=vid_title,
                        url=f"https://www.youtube.com/watch?v={vid_id}",
                        video_id=vid_id,
                        channel=uploader,
                        transcript=transcript,
                    )
                )
                if len(videos) >= max_results:
                    break
    except Exception:
        pass

    # 2. Secondary Fallback: DuckDuckGo if yt-dlp search yields 0 items
    if not videos:
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(f"site:youtube.com {clean_query}", max_results=max_results * 2):
                    href = r.get("href", "")
                    if "youtube.com/watch" not in href and "youtu.be/" not in href:
                        continue
                    vid_id = extract_video_id(href)
                    if not vid_id or vid_id in seen_ids:
                        continue
                    seen_ids.add(vid_id)

                    vid_title = r.get("title", f"{title} Summary")
                    vid_title = re.sub(r"\s*-\s*YouTube$", "", vid_title, flags=re.I)
                    body = r.get("body", "")

                    transcript = ""
                    if fetch_transcripts:
                        transcript = fetch_youtube_transcript(vid_id, max_chars=3500)
                    if not transcript and body:
                        transcript = f"[Video Summary & Overview]\n{body.strip()}"

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
            snippet = v.transcript.replace("\n", " ")[:180].strip()
            lines.append(f"  > *\"{snippet}...\"*")
        lines.append("")

    return "\n".join(lines).strip()
