"""Fact-Checking and Claim Extraction API routes for HybridGuard AI.
Coordinates live web evidence retrieval (Wikipedia REST API / DuckDuckGo) without hallucinated citations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    Citation,
    ClaimExtractRequest,
    EvidenceExcerpt,
    FactCheckRequest,
    FactCheckResponse,
)
from src.fact_check.claim_extractor import extract_claims_from_text
from src.fact_check.pipeline import FactCheckPipeline
from src.fact_check.search_provider import get_search_provider

logger = logging.getLogger("hybridguard.api_fact_check")
router = APIRouter(prefix="/api", tags=["Evidence-Based Fact Checking"])

# Shared pipeline instance
_FACT_CHECKER: FactCheckPipeline = FactCheckPipeline(provider_name="wikipedia")


@router.post("/fact-check", response_model=FactCheckResponse)
def verify_claim(req: FactCheckRequest) -> FactCheckResponse:
    """Verify an individual factual claim against live external search evidence."""
    try:
        result = _FACT_CHECKER.verify_single_claim(
            claim_text=req.claim,
            max_evidence_results=req.max_evidence_results,
        )

        citations = [Citation(**c) for c in result["citations"]]
        supporting = [EvidenceExcerpt(**s) for s in result["supporting_evidence"]]
        contradicting = [EvidenceExcerpt(**c) for c in result["contradicting_evidence"]]

        return FactCheckResponse(
            claim=result["claim"],
            verdict=result["verdict"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            citations=citations,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            checkability_info=result.get("checkability_info"),
        )

    except Exception as e:
        logger.error("Fact-check verification error: %s", e)
        raise HTTPException(status_code=500, detail=f"Fact-check verification failed: {str(e)}")


@router.post("/claims/extract")
def extract_claims(req: ClaimExtractRequest) -> Dict[str, Any]:
    """Extract and classify checkable factual assertions from arbitrary input text."""
    try:
        claims = extract_claims_from_text(req.text, max_claims=req.max_claims)
        checkable_count = sum(1 for c in claims if c["is_checkable"])

        return {
            "total_extracted": len(claims),
            "checkable_count": checkable_count,
            "claims": claims,
        }
    except Exception as e:
        logger.error("Claim extraction error: %s", e)
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.post("/fact-check/article")
def verify_article(req: ClaimExtractRequest) -> Dict[str, Any]:
    """Extract checkable claims from article text and verify each with external evidence."""
    try:
        return _FACT_CHECKER.verify_article_claims(req.text, max_claims=req.max_claims)
    except Exception as e:
        logger.error("Article fact-checking error: %s", e)
        raise HTTPException(status_code=500, detail=f"Article verification failed: {str(e)}")

