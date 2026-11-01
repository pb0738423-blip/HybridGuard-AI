"""Unit tests for YouTube URL validation, Shorts parsing, transcript fallback, and timeline segmentation."""

import pytest

from src.video.segmenter import group_transcript_into_chunks
from src.video.transcript import parse_manual_transcript
from src.video.url_validator import extract_youtube_video_id, validate_youtube_url


def test_youtube_url_validator():
    # 1. Shorts URL (matching user reference)
    res_shorts = validate_youtube_url("https://www.youtube.com/shorts/aUyVATJqEoQ")
    assert res_shorts["is_valid"] is True
    assert res_shorts["video_id"] == "aUyVATJqEoQ"
    assert res_shorts["is_shorts"] is True
    assert "embed/aUyVATJqEoQ" in res_shorts["embed_url"]

    # 2. Standard Watch URL
    res_watch = validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert res_watch["is_valid"] is True
    assert res_watch["video_id"] == "dQw4w9WgXcQ"
    assert res_watch["is_shorts"] is False

    # 3. youtu.be Shortlink
    res_shortlink = validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert res_shortlink["is_valid"] is True
    assert res_shortlink["video_id"] == "dQw4w9WgXcQ"

    # 4. Invalid URL
    res_invalid = validate_youtube_url("https://vimeo.com/123456")
    assert res_invalid["is_valid"] is False
    assert res_invalid["video_id"] is None


def test_parse_manual_transcript_with_timestamps():
    pasted = """
    [00:05] The study confirmed a 20% increase in renewable energy adoption.
    [00:20] Scientists in California recorded the phenomenon in laboratory conditions.
    """
    res = parse_manual_transcript(pasted)
    assert res["available"] is True
    assert len(res["segments"]) == 2
    assert res["segments"][0]["start"] == 5.0
    assert res["segments"][1]["start"] == 20.0
    assert res["segments"][0]["timestamp_formatted"] == "00:05"


def test_group_transcript_into_chunks():
    segments = [
        {"start": 0.0, "duration": 5.0, "text": "Segment one."},
        {"start": 5.0, "duration": 10.0, "text": "Segment two."},
        {"start": 15.0, "duration": 20.0, "text": "Segment three."},
    ]
    chunks = group_transcript_into_chunks(segments, target_duration=15.0)
    assert len(chunks) >= 1
    assert "start" in chunks[0]
    assert "text" in chunks[0]

