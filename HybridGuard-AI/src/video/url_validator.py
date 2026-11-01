"""YouTube URL Validation and Sanitization for Standard Videos and Shorts.
Supports full desktop, mobile, shorts, and shortened youtu.be links.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger("hybridguard.url_validator")

# Regex pattern for 11-character YouTube video IDs
YOUTUBE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Safely extract the 11-character YouTube video ID from various URL formats.
    
    Supports:
    - https://www.youtube.com/shorts/aUyVATJqEoQ
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://m.youtube.com/watch?v=dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ
    - Raw 11-char ID directly: aUyVATJqEoQ
    """
    if not url or not isinstance(url, str):
        return None

    url_str = url.strip()

    # If user passed a bare 11-char ID
    if YOUTUBE_ID_REGEX.match(url_str):
        return url_str

    try:
        parsed = urlparse(url_str)
        hostname = (parsed.hostname or "").lower()

        # Handle youtu.be/<id>
        if hostname in ("youtu.be", "www.youtu.be"):
            path_parts = parsed.path.strip("/").split("/")
            if path_parts and YOUTUBE_ID_REGEX.match(path_parts[0]):
                return path_parts[0]

        # Handle youtube.com/shorts/<id>
        if "youtube.com" in hostname or "youtube-nocookie.com" in hostname:
            path = parsed.path.strip("/")
            if path.startswith("shorts/"):
                parts = path.split("/")
                if len(parts) >= 2 and YOUTUBE_ID_REGEX.match(parts[1]):
                    return parts[1]

            # Handle youtube.com/embed/<id>
            if path.startswith("embed/"):
                parts = path.split("/")
                if len(parts) >= 2 and YOUTUBE_ID_REGEX.match(parts[1]):
                    return parts[1]

            # Handle standard watch?v=<id>
            qs = parse_qs(parsed.query)
            if "v" in qs and qs["v"]:
                vid = qs["v"][0]
                if YOUTUBE_ID_REGEX.match(vid):
                    return vid

    except Exception as e:
        logger.debug("Error parsing YouTube URL '%s': %s", url_str, e)

    return None


def validate_youtube_url(url: str) -> Dict[str, Any]:
    """Validate YouTube URL and return metadata dictionary with embed links."""
    video_id = extract_youtube_video_id(url)

    if not video_id:
        return {
            "is_valid": False,
            "video_id": None,
            "error": "Invalid YouTube URL. Please provide a standard YouTube video link or Shorts URL (e.g., https://www.youtube.com/shorts/aUyVATJqEoQ).",
            "embed_url": None,
            "canonical_url": None,
        }

    is_shorts = "/shorts/" in url.lower()

    return {
        "is_valid": True,
        "video_id": video_id,
        "is_shorts": is_shorts,
        "embed_url": f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&origin=*",
        "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
        "error": None,
    }

