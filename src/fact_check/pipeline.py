"""Unified Fact-Checking Pipeline for HybridGuard AI.
Orchestrates claim extraction, search retrieval, evidence assessment, and verdict synthesis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.fact_check.claim_extractor import classify_sentence_checkability, extract_claims_from_text
from src.fact_check.evidence_evaluator import evaluate_claim_against_evidence
from src.fact_check.search_provider import SearchProvider, get_search_provider

logger = logging.getLogger("hybridguard.fact_check_pipeline")


class FactCheckPipeline:
    """End-to-end evidence-based fact checking pipeline."""

    def __init__(self, search_provider: Optional[SearchProvider] = None, provider_name: str = "wikipedia"):
        self.search_provider = search_provider or get_search_provider(provider_name)

    def verify_single_claim(self, claim_text: str, max_evidence_results: int = 4) -> Dict[str, Any]:
        """Verify an individual factual claim against live external search evidence."""
        claim_clean = claim_text.strip()
        logger.info("Verifying claim: '%s'", claim_clean)

        # 1. Assess checkability
        checkability = classify_sentence_checkability(claim_clean)
        is_checkable = checkability["is_checkable"]

        # 2. Retrieve evidence if checkable
        evidence_docs = []
        if is_checkable:
            # Query external provider
            evidence_docs = self.search_provider.search(claim_clean, max_results=max_evidence_results)

        # 3. Synthesize stance and verdict
        result = evaluate_claim_against_evidence(
            claim_text=claim_clean,
            evidence_docs=evidence_docs,
            is_checkable=is_checkable,
        )

        result["checkability_info"] = checkability
        return result

    def verify_article_claims(self, text: str, max_claims: int = 5) -> Dict[str, Any]:
        """Extract checkable claims from arbitrary article text and verify each."""
        extracted_claims = extract_claims_from_text(text, max_claims=max_claims)
        verified_results = []

        total_checkable = 0
        supported_count = 0
        contradicted_count = 0
        partial_count = 0
        insufficient_count = 0

        for claim_info in extracted_claims:
            claim_text = claim_info["text"]
            res = self.verify_single_claim(claim_text)
            verified_results.append(res)

            verdict = res["verdict"]
            if res["checkability_info"]["is_checkable"]:
                total_checkable += 1
                if verdict == "Supported":
                    supported_count += 1
                elif verdict == "Contradicted":
                    contradicted_count += 1
                elif verdict == "Partially Supported / Misleading":
                    partial_count += 1
                elif verdict == "Insufficient Evidence":
                    insufficient_count += 1

        summary = {
            "total_extracted_claims": len(extracted_claims),
            "total_checkable_claims": total_checkable,
            "supported_count": supported_count,
            "contradicted_count": contradicted_count,
            "partial_count": partial_count,
            "insufficient_count": insufficient_count,
            "credibility_assessment": (
                "High Credibility" if total_checkable > 0 and contradicted_count == 0 and supported_count > 0
                else "Contains Misleading / Contradicted Claims" if contradicted_count > 0
                else "Unverified / Needs Investigation"
            ),
        }

        return {
            "summary": summary,
            "claims": verified_results,
        }

