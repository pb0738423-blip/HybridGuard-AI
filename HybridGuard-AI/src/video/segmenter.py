"""Transcript Segmentation and Timestamped Claim Verification for HybridGuard AI.
Aligns checkable claims with exact video timestamps and verifies them with genuine evidence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.fact_check.claim_extractor import extract_claims_from_text
from src.fact_check.pipeline import FactCheckPipeline
from src.video.transcript import format_seconds_to_timestamp

logger = logging.getLogger("hybridguard.video_segmenter")

DISCLAIMER_VIDEO = (
    "Factual verification assesses individual empirical claims extracted from the video transcript. "
    "A single inaccurate or contradicted statement does not automatically render the entire video or "
    "speaker untrustworthy. Context, satire, misstatements, and evolving news events must be considered."
)


def group_transcript_into_chunks(
    segments: List[Dict[str, Any]],
    target_duration: float = 30.0,
) -> List[Dict[str, Any]]:
    """Group fine-grained transcript lines into coherent timeline chunks."""
    if not segments:
        return []

    chunks = []
    current_texts = []
    chunk_start = segments[0]["start"]
    current_end = chunk_start

    for seg in segments:
        current_texts.append(seg["text"])
        current_end = seg["start"] + seg.get("duration", 2.0)

        if (current_end - chunk_start) >= target_duration:
            chunk_text = " ".join(current_texts)
            chunks.append({
                "start": chunk_start,
                "end": current_end,
                "timestamp_formatted": format_seconds_to_timestamp(chunk_start),
                "text": chunk_text,
            })
            current_texts = []
            chunk_start = current_end

    if current_texts:
        chunk_text = " ".join(current_texts)
        chunks.append({
            "start": chunk_start,
            "end": current_end,
            "timestamp_formatted": format_seconds_to_timestamp(chunk_start),
            "text": chunk_text,
        })

    return chunks


def analyze_transcript_timeline(
    segments: List[Dict[str, Any]],
    fact_checker: Optional[FactCheckPipeline] = None,
    max_claims_to_verify: int = 8,
) -> Dict[str, Any]:
    """Segment transcript, extract timestamped claims, and verify them against evidence."""
    if fact_checker is None:
        fact_checker = FactCheckPipeline()

    chunks = group_transcript_into_chunks(segments)
    logger.info("Grouped transcript into %d timeline chunks", len(chunks))

    timestamped_claims = []
    total_claims_checked = 0

    for chunk in chunks:
        if total_claims_checked >= max_claims_to_verify:
            break

        chunk_claims = extract_claims_from_text(chunk["text"], max_claims=2)
        for claim_info in chunk_claims:
            if total_claims_checked >= max_claims_to_verify:
                break

            claim_text = claim_info["text"]
            # Verify claim with evidence search
            verification = fact_checker.verify_single_claim(claim_text)

            timestamped_claims.append({
                "claim": claim_text,
                "timestamp_seconds": chunk["start"],
                "timestamp_formatted": chunk["timestamp_formatted"],
                "chunk_context": chunk["text"][:200] + "...",
                "is_checkable": claim_info["is_checkable"],
                "checkability_category": claim_info["category"],
                "verdict": verification["verdict"],
                "confidence": verification["confidence"],
                "explanation": verification["explanation"],
                "citations": verification["citations"],
                "supporting_evidence": verification["supporting_evidence"],
                "contradicting_evidence": verification["contradicting_evidence"],
            })
            total_claims_checked += 1

    # Summarize video claims
    verdicts = [c["verdict"] for c in timestamped_claims if c["is_checkable"]]
    supported_cnt = verdicts.count("Supported")
    contradicted_cnt = verdicts.count("Contradicted")
    partial_cnt = verdicts.count("Partially Supported / Misleading")
    insufficient_cnt = verdicts.count("Insufficient Evidence")

    needs_review_claims = [
        c for c in timestamped_claims
        if c["verdict"] in ("Contradicted", "Partially Supported / Misleading", "Insufficient Evidence")
    ]

    summary = {
        "total_claims_assessed": len(timestamped_claims),
        "supported_claims": supported_cnt,
        "contradicted_claims": contradicted_cnt,
        "partial_misleading_claims": partial_cnt,
        "insufficient_evidence_claims": insufficient_cnt,
        "needs_review_count": len(needs_review_claims),
        "overall_status": (
            "Well Supported" if contradicted_cnt == 0 and partial_cnt == 0 and supported_cnt > 0
            else "Caution: Contains Questionable / Contradicted Claims" if contradicted_cnt > 0
            else "Mixed / Needs Further Context" if partial_cnt > 0
            else "Inconclusive / Unverified Claims"
        ),
        "disclaimer": DISCLAIMER_VIDEO,
    }

    return {
        "summary": summary,
        "timeline_chunks": chunks,
        "timestamped_claims": timestamped_claims,
    }

