"""Transcript Extraction and Manual Fallback Parser for HybridGuard AI.
Integrates youtube-transcript-api with graceful fallback to user-provided transcripts.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hybridguard.transcript")


def format_seconds_to_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def parse_timestamp_to_seconds(ts_str: str) -> Optional[float]:
    """Parse strings like '01:23' or '1:02:15' to seconds float."""
    parts = ts_str.strip("[]() ").split(":")
    try:
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    return None


def fetch_youtube_transcript(video_id: str) -> Dict[str, Any]:
    """Retrieve English captions for a YouTube video or Shorts using youtube-transcript-api."""
    logger.info("Attempting automatic transcript retrieval for video ID: %s", video_id)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try retrieving english captions (manual or auto-generated)
        # Note: in modern youtube-transcript-api, get_transcript takes video_id and languages list
        transcript_data = None
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        except Exception:
            # Try fetching any available transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Find first available transcript (or translated)
            try:
                t = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
            except Exception:
                t = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
            if t:
                transcript_data = t.fetch()

        if transcript_data:
            formatted = []
            for item in transcript_data:
                start_sec = float(item.get("start", 0.0))
                duration_sec = float(item.get("duration", 0.0))
                text = item.get("text", "").strip()
                if text:
                    formatted.append({
                        "start": round(start_sec, 2),
                        "duration": round(duration_sec, 2),
                        "timestamp_formatted": format_seconds_to_timestamp(start_sec),
                        "text": text,
                    })

            logger.info("Retrieved %d transcript segments for %s", len(formatted), video_id)
            return {
                "available": True,
                "video_id": video_id,
                "source": "YouTube Captions API",
                "segment_count": len(formatted),
                "segments": formatted,
                "full_transcript": " ".join(item["text"] for item in formatted),
                "error": None,
            }

    except Exception as e:
        logger.warning("Automatic transcript fetch failed for %s: %s", video_id, e)

    return {
        "available": False,
        "video_id": video_id,
        "source": None,
        "segment_count": 0,
        "segments": [],
        "full_transcript": "",
        "error": (
            "Automatic captions could not be retrieved (captions may be disabled, private, "
            "or non-English). Please paste or upload the transcript in the manual input panel below."
        ),
    }


def parse_manual_transcript(raw_text: str, words_per_minute: int = 140) -> Dict[str, Any]:
    """Parse user-pasted transcript with optional timestamps or plain text."""
    if not raw_text or not raw_text.strip():
        return {
            "available": False,
            "segments": [],
            "full_transcript": "",
            "error": "Pasted transcript is empty.",
        }

    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    segments = []

    # Check for timestamps in lines like [01:23] or 01:23
    ts_pattern = re.compile(r"^(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?)\s*(.*)$")

    current_sec = 0.0
    seconds_per_word = 60.0 / words_per_minute

    has_explicit_timestamps = False

    for line in lines:
        match = ts_pattern.match(line)
        if match:
            has_explicit_timestamps = True
            ts_str, content = match.groups()
            parsed_sec = parse_timestamp_to_seconds(ts_str)
            if parsed_sec is not None:
                current_sec = parsed_sec
            text = content.strip()
        else:
            text = line

        if not text:
            continue

        word_count = len(text.split())
        duration = max(2.0, word_count * seconds_per_word)

        segments.append({
            "start": round(current_sec, 2),
            "duration": round(duration, 2),
            "timestamp_formatted": format_seconds_to_timestamp(current_sec),
            "text": text,
        })

        if not has_explicit_timestamps:
            current_sec += duration

    full_text = " ".join(s["text"] for s in segments)

    return {
        "available": True,
        "source": "Manual User Transcript" + (" (with explicit timestamps)" if has_explicit_timestamps else " (estimated pacing)"),
        "segment_count": len(segments),
        "segments": segments,
        "full_transcript": full_text,
        "error": None,
    }

