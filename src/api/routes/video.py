"""Video and YouTube Shorts Verification API routes for HybridGuard AI.
Handles URL validation, transcript retrieval (API + manual fallback), and timestamped claim checks.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    TranscriptAnalyzeRequest,
    VideoAnalyzeRequest,
    VideoAnalysisResponse,
)
from src.video.segmenter import analyze_transcript_timeline
from src.video.transcript import fetch_youtube_transcript, parse_manual_transcript
from src.video.url_validator import validate_youtube_url

logger = logging.getLogger("hybridguard.api_video")
router = APIRouter(prefix="/api", tags=["YouTube Video & Shorts Analysis"])

# In-memory storage for analysis results
_ANALYSIS_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/video/analyze", response_model=VideoAnalysisResponse)
def analyze_video(req: VideoAnalyzeRequest) -> VideoAnalysisResponse:
    """Analyze a YouTube video or Shorts link by extracting transcript,
    identifying timestamped factual claims, and verifying each with web evidence.
    """
    # 1. Validate YouTube / Shorts URL
    validation = validate_youtube_url(req.url)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    video_id = validation["video_id"]
    is_shorts = validation["is_shorts"]
    embed_url = validation["embed_url"]
    canonical_url = validation["canonical_url"]

    # 2. Retrieve transcript (manual fallback or auto captions)
    if req.manual_transcript and req.manual_transcript.strip():
        transcript_res = parse_manual_transcript(req.manual_transcript)
    else:
        transcript_res = fetch_youtube_transcript(video_id)

    if not transcript_res["available"] or not transcript_res["segments"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Transcript unavailable",
                "message": transcript_res["error"],
                "video_id": video_id,
                "embed_url": embed_url,
                "requires_manual_transcript": True,
            },
        )

    # 3. Analyze timeline and timestamped claims
    analysis = analyze_transcript_timeline(
        segments=transcript_res["segments"],
        max_claims_to_verify=req.max_claims,
    )

    analysis_id = f"vid-{uuid.uuid4().hex[:10]}"
    response_payload = {
        "analysis_id": analysis_id,
        "video_id": video_id,
        "is_shorts": is_shorts,
        "embed_url": embed_url,
        "canonical_url": canonical_url,
        "transcript_source": transcript_res["source"],
        "summary": analysis["summary"],
        "timeline_chunks": analysis["timeline_chunks"],
        "timestamped_claims": analysis["timestamped_claims"],
    }

    _ANALYSIS_STORE[analysis_id] = response_payload
    return VideoAnalysisResponse(**response_payload)


@router.post("/transcript/analyze", response_model=VideoAnalysisResponse)
def analyze_transcript(req: TranscriptAnalyzeRequest) -> VideoAnalysisResponse:
    """Analyze a pasted or uploaded transcript directly."""
    transcript_res = parse_manual_transcript(req.transcript)

    if not transcript_res["available"] or not transcript_res["segments"]:
        raise HTTPException(status_code=400, detail=transcript_res["error"])

    video_id = req.video_id
    embed_url = f"https://www.youtube.com/embed/{video_id}?enablejsapi=1" if video_id else None
    canonical_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

    analysis = analyze_transcript_timeline(
        segments=transcript_res["segments"],
        max_claims_to_verify=req.max_claims,
    )

    analysis_id = f"trans-{uuid.uuid4().hex[:10]}"
    response_payload = {
        "analysis_id": analysis_id,
        "video_id": video_id,
        "is_shorts": False,
        "embed_url": embed_url,
        "canonical_url": canonical_url,
        "transcript_source": transcript_res["source"],
        "summary": analysis["summary"],
        "timeline_chunks": analysis["timeline_chunks"],
        "timestamped_claims": analysis["timestamped_claims"],
    }

    _ANALYSIS_STORE[analysis_id] = response_payload
    return VideoAnalysisResponse(**response_payload)


@router.get("/analysis/{analysis_id}")
def get_analysis_by_id(analysis_id: str) -> Dict[str, Any]:
    """Retrieve previously processed video or transcript analysis by ID."""
    if analysis_id not in _ANALYSIS_STORE:
        raise HTTPException(status_code=404, detail="Analysis session ID not found")
    return _ANALYSIS_STORE[analysis_id]

