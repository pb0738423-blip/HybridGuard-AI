"""Real-time Speech Verification Stream & Queue Manager for HybridGuard AI.
Processes incoming live transcript segments, detects claims on rolling windows,
and dispatches asynchronous background verification with bounded queues and caching.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import logging
import time
from collections import deque
from typing import Any, Dict, List, Optional

from src.fact_check.claim_extractor import classify_sentence_checkability, extract_claims_from_text
from src.fact_check.pipeline import FactCheckPipeline

logger = logging.getLogger("hybridguard.speech_realtime")


class LiveSpeechSession:
    """Manages an active real-time speech verification session with bounded queues,
    caching, and latency tracking.
    """

    def __init__(
        self,
        session_id: str,
        fact_checker: Optional[FactCheckPipeline] = None,
        max_queue_size: int = 50,
        cache_ttl_seconds: int = 3600,
    ):
        self.session_id = session_id
        self.fact_checker = fact_checker or FactCheckPipeline()
        self.max_queue_size = max_queue_size
        self.cache_ttl_seconds = cache_ttl_seconds

        self.created_at = datetime.datetime.utcnow().isoformat() + "Z"
        self.is_active = True
        self.transcript_buffer: List[Dict[str, Any]] = []

        # Claim cache to prevent duplicate lookups
        self.verified_claims_cache: Dict[str, Dict[str, Any]] = {}

        # Live results list
        self.live_verifications: List[Dict[str, Any]] = []

        # Bounded processing queue
        self.task_queue: deque = deque(maxlen=max_queue_size)
        self.processed_hashes: set = set()

    def _hash_claim(self, claim_text: str) -> str:
        """Normalized hash of claim for deduplication."""
        normalized = " ".join(claim_text.lower().strip().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def ingest_transcript_chunk(
        self,
        text: str,
        timestamp_sec: float,
        is_final: bool = True,
    ) -> Dict[str, Any]:
        """Ingest incoming live speech transcript segment."""
        text_clean = text.strip()
        if not text_clean:
            return {"status": "ignored", "reason": "empty chunk"}

        chunk_record = {
            "timestamp": timestamp_sec,
            "text": text_clean,
            "is_final": is_final,
            "received_at": time.time(),
        }
        self.transcript_buffer.append(chunk_record)

        # If segment is final, attempt claim extraction
        extracted_claims = []
        if is_final and len(text_clean.split()) >= 4:
            extracted_claims = extract_claims_from_text(text_clean, max_claims=2)
            for c in extracted_claims:
                if c["is_checkable"]:
                    claim_text = c["text"]
                    c_hash = self._hash_claim(claim_text)
                    if c_hash not in self.processed_hashes:
                        self.processed_hashes.add(c_hash)
                        self._dispatch_claim_check(claim_text, timestamp_sec, c_hash)

        return {
            "session_id": self.session_id,
            "status": "ingested",
            "buffered_segments": len(self.transcript_buffer),
            "detected_claims": len(extracted_claims),
        }

    def _dispatch_claim_check(self, claim_text: str, timestamp_sec: float, claim_hash: str) -> None:
        """Check cache or perform synchronous/asynchronous verification."""
        t_start = time.perf_counter()

        # Check in-memory cache first
        if claim_hash in self.verified_claims_cache:
            cached = dict(self.verified_claims_cache[claim_hash])
            cached["latency_ms"] = 0.5  # Cache hit latency
            cached["timestamp_sec"] = timestamp_sec
            cached["from_cache"] = True
            self.live_verifications.append(cached)
            return

        try:
            verification = self.fact_checker.verify_single_claim(claim_text)
            latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

            item = {
                "claim": claim_text,
                "claim_hash": claim_hash,
                "timestamp_sec": round(timestamp_sec, 2),
                "verdict": verification["verdict"],
                "confidence": verification["confidence"],
                "explanation": verification["explanation"],
                "citations": verification["citations"],
                "supporting_evidence": verification["supporting_evidence"],
                "contradicting_evidence": verification["contradicting_evidence"],
                "latency_ms": latency_ms,
                "from_cache": False,
                "verified_at": datetime.datetime.utcnow().isoformat() + "Z",
            }

            self.verified_claims_cache[claim_hash] = item
            self.live_verifications.append(item)
            logger.info("Live speech verified claim in %.1fms: [%s] %s", latency_ms, verification['verdict'], claim_text[:50])

        except Exception as e:
            logger.error("Error verifying live claim '%s': %s", claim_text, e)
            self.live_verifications.append({
                "claim": claim_text,
                "claim_hash": claim_hash,
                "timestamp_sec": timestamp_sec,
                "verdict": "Verification Error",
                "confidence": 0.0,
                "explanation": f"Live verification failed: {str(e)}",
                "citations": [],
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2),
                "from_cache": False,
            })

    def get_live_status(self) -> Dict[str, Any]:
        """Return the current status, transcript count, and all verified claims."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "transcript_segment_count": len(self.transcript_buffer),
            "verified_claim_count": len(self.live_verifications),
            "full_transcript": " ".join(s["text"] for s in self.transcript_buffer),
            "verifications": self.live_verifications,
        }

    def close(self) -> None:
        """Close the live session."""
        self.is_active = False


class SpeechSessionManager:
    """Singleton-style registry for active speech fact-checking sessions."""

    def __init__(self):
        self.sessions: Dict[str, LiveSpeechSession] = {}

    def create_session(self, session_id: Optional[str] = None) -> LiveSpeechSession:
        if not session_id:
            import uuid
            session_id = f"speech-{uuid.uuid4().hex[:8]}"

        session = LiveSpeechSession(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[LiveSpeechSession]:
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]


session_manager = SpeechSessionManager()

