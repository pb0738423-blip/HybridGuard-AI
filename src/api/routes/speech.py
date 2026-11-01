"""Live Speech Fact-Checking API routes for HybridGuard AI.
Handles streaming audio chunks, asynchronous verification queues, and latency metrics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.schemas import SpeechChunkRequest
from src.speech.realtime import session_manager

logger = logging.getLogger("hybridguard.api_speech")
router = APIRouter(prefix="/api/speech", tags=["Live Speech Fact Checking"])


@router.post("/session")
def create_session() -> Dict[str, Any]:
    """Start a new real-time speech verification session."""
    session = session_manager.create_session()
    return {
        "session_id": session.session_id,
        "status": "active",
        "created_at": session.created_at,
        "message": "Session initialized. Stream speech transcript chunks to /api/speech/chunk",
    }


@router.post("/chunk")
def ingest_chunk(req: SpeechChunkRequest) -> Dict[str, Any]:
    """Ingest a live transcript chunk from speech-to-text recognition."""
    session = session_manager.get_session(req.session_id)
    if not session:
        # Auto-create if expired or not registered
        session = session_manager.create_session(session_id=req.session_id)

    res = session.ingest_transcript_chunk(
        text=req.text,
        timestamp_sec=req.timestamp_sec,
        is_final=req.is_final,
    )
    return res


@router.get("/status/{session_id}")
def get_session_status(session_id: str) -> Dict[str, Any]:
    """Poll live session state, transcript buffer, and verified claim results."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Speech session not found or expired")
    return session.get_live_status()


@router.delete("/session/{session_id}")
def close_session(session_id: str) -> Dict[str, Any]:
    """Terminate an active speech session."""
    session_manager.remove_session(session_id)
    return {"session_id": session_id, "status": "closed"}

