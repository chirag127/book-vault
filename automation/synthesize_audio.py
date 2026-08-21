from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

from .config import ROOT, load_settings
from .manifest import load_manifest
from .taxonomy import PILLAR_DIRS


def _clean_spoken_text(markdown_text: str) -> str:
    """Strip YAML front matter, headers, and markdown symbols to produce clean text for TTS."""
    text = markdown_text.strip()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    # Replace markdown headings with spoken pauses
    text = re.sub(r"^#+\s+(.+)$", r"\1.\n", text, flags=re.MULTILINE)
    # Remove markdown link formatting [[slug|Title]] -> Title
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    # Remove standard markdown links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bold, italics, code fences
    text = re.sub(r"[*_`#>]", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def synthesize_text_to_mp3(text: str, output_path: Path, voice: str = "en-US-ChristopherNeural") -> bool:
    """Synthesize text to MP3 using edge-tts with fallback to gTTS."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return True
    except ImportError:
        pass

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="en")
        tts.save(str(output_path))
        return True
    except Exception as exc:
        print(f"[tts] Synthesis failed: {exc}", file=sys.stderr)
        return False


def synthesize_book_audio(slug: str, voice: str = "en-US-ChristopherNeural") -> bool:
    """Locate the Audio-Listening-Edition.md for a book and synthesize its MP3."""
    matches = list(ROOT.glob(f"md/*/*/{slug}/Audio-Listening-Edition.md"))
    if not matches:
        # Check single file fallback
        matches = list(ROOT.glob(f"md/*/*/{slug}.md"))
    if not matches:
        print(f"[tts] No audio edition found for slug '{slug}'", file=sys.stderr)
        return False

    audio_md = matches[0]
    book_dir = audio_md.parent if audio_md.name == "Audio-Listening-Edition.md" else audio_md.parent / slug
    mp3_path = book_dir / "Audio-Listening-Edition.mp3"

    text = _clean_spoken_text(audio_md.read_text(encoding="utf-8"))
    if not text:
        print(f"[tts] Audio edition at {audio_md} is empty.", file=sys.stderr)
        return False

    print(f"[tts] Synthesizing {len(text.split())} words for '{slug}' -> {mp3_path.relative_to(ROOT)}...")
    success = asyncio.run(synthesize_text_to_mp3(text, mp3_path, voice=voice))
    if success:
        print(f"[tts] [OK] Successfully generated audio: {mp3_path.relative_to(ROOT)}")
    return success



def main() -> int:
    parser = argparse.ArgumentParser(description="Synthesize Audio Listening Editions into MP3 audio files.")
    parser.add_argument("--slug", help="Synthesize audio for a specific book slug.")
    parser.add_argument("--all", action="store_true", help="Synthesize audio for all available books.")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Voice for synthesis (default: en-US-ChristopherNeural).")
    args = parser.parse_args()

    if args.slug:
        return 0 if synthesize_book_audio(args.slug, voice=args.voice) else 1

    if args.all:
        audio_files = list(ROOT.glob("md/*/*/Audio-Listening-Edition.md"))
        print(f"[tts] Found {len(audio_files)} book audio editions to synthesize.")
        for path in audio_files:
            slug = path.parent.name
            synthesize_book_audio(slug, voice=args.voice)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
