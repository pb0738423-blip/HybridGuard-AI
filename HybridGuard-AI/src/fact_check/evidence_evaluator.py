"""Evidence Evaluation and Stance Determination Engine for HybridGuard AI.
Analyzes retrieved evidence against checkable claims to determine authentic verdicts,
citations, and stance breakdowns without hallucinated sources.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.fact_check.search_provider import EvidenceDocument

logger = logging.getLogger("hybridguard.evidence_evaluator")

# Standard Verdict Constants
VERDICT_SUPPORTED = "Supported"
VERDICT_CONTRADICTED = "Contradicted"
VERDICT_PARTIAL = "Partially Supported / Misleading"
VERDICT_INSUFFICIENT = "Insufficient Evidence"
VERDICT_NOT_CHECKABLE = "Not a Checkable Factual Claim"

# Refutation & Debunking lexical cues
CONTRADICTION_PATTERNS = [
    r"\bfalse\b", r"\bdebunked\b", r"\bhoax\b", r"\bno evidence\b", r"\bunproven\b",
    r"\brefuted\b", r"\bdenied\b", r"\bincorrect\b", r"\bmyth\b", r"\bnever happened\b",
    r"\bfabricated\b", r"\buntrue\b", r"\bnot true\b", r"\bdisproved\b", r"\bmisinformation\b",
    r"\bdiscredited\b", r"\bconspiracy theory\b", r"\bno basis in fact\b",
]

# Nuance & distortion cues
PARTIAL_PATTERNS = [
    r"\bpartially\b", r"\bpartly\b", r"\bmisleading\b", r"\bout of context\b",
    r"\blacks context\b", r"\bexaggerated\b", r"\bhalf truth\b", r"\bdisputed\b",
    r"\bmixed\b", r"\bselective\b", r"\bdistorted\b",
]

# Corroboration cues
SUPPORT_PATTERNS = [
    r"\bconfirmed\b", r"\bverified\b", r"\bofficial\b", r"\bdemonstrated\b",
    r"\bconcluded that\b", r"\bestablished that\b", r"\bpassed\b", r"\bsigned into law\b",
    r"\bproved\b", r"\bagreed that\b", r"\bdocumented that\b",
]

STOPWORDS = {
    "the", "a", "an", "is", "was", "are", "were", "and", "or", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "that", "this", "it", "as", "be",
}


def tokenize_clean(text: str) -> List[str]:
    """Tokenize and remove common stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9'-]+\b", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def calculate_lexical_overlap(text_a: str, text_b: str) -> float:
    """Calculate token Jaccard overlap between two texts."""
    tokens_a = set(tokenize_clean(text_a))
    tokens_b = set(tokenize_clean(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a.intersection(tokens_b)) / len(tokens_a.union(tokens_b))


def evaluate_claim_against_evidence(
    claim_text: str,
    evidence_docs: List[EvidenceDocument],
    is_checkable: bool = True,
) -> Dict[str, Any]:
    """Synthesize evidence documents into a grounded fact-checking verdict."""
    if not is_checkable:
        return {
            "claim": claim_text,
            "verdict": VERDICT_NOT_CHECKABLE,
            "confidence": 0.90,
            "explanation": (
                "The statement does not constitute an empirical factual claim. It represents "
                "a subjective opinion, value judgment, future forecast, or rhetorical question."
            ),
            "citations": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }

    if not evidence_docs:
        return {
            "claim": claim_text,
            "verdict": VERDICT_INSUFFICIENT,
            "confidence": 0.85,
            "explanation": (
                "Web and encyclopedic knowledge search yielded no authoritative sources directly addressing "
                "this claim. Verification cannot be confirmed without external reference evidence."
            ),
            "citations": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }

    claim_tokens = set(tokenize_clean(claim_text))
    supporting = []
    contradicting = []
    citations = []

    best_overlap = 0.0

    for doc in evidence_docs:
        doc_dict = doc.to_dict()
        citations.append(doc_dict)

        doc_text = f"{doc.title} {doc.snippet}".lower()
        overlap = calculate_lexical_overlap(claim_text, doc.snippet)
        if overlap > best_overlap:
            best_overlap = overlap

        # Break snippet into sentences
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", doc.snippet) if s.strip()]

        for sent in sentences:
            sent_lower = sent.lower()
            sent_tokens = set(tokenize_clean(sent))
            token_match_count = len(claim_tokens.intersection(sent_tokens))

            # Only consider sentences with semantic relevance to the claim
            if token_match_count < 2 and overlap < 0.10:
                continue

            # Check for contradiction patterns
            has_contradiction = any(re.search(p, sent_lower) for p in CONTRADICTION_PATTERNS)
            has_partial = any(re.search(p, sent_lower) for p in PARTIAL_PATTERNS)
            has_support = any(re.search(p, sent_lower) for p in SUPPORT_PATTERNS)

            evidence_item = {
                "source_title": doc.title,
                "source_url": doc.url,
                "excerpt": sent,
                "relevance_score": round(min(1.0, token_match_count / max(1, len(claim_tokens)) + 0.3), 2),
            }

            if has_contradiction:
                contradicting.append(evidence_item)
            elif has_partial:
                contradicting.append(evidence_item)
            elif has_support or token_match_count >= 3:
                supporting.append(evidence_item)

    # Decision logic based on retrieved evidence
    if best_overlap < 0.08 and not supporting and not contradicting:
        verdict = VERDICT_INSUFFICIENT
        confidence = 0.80
        explanation = (
            "Retrieved search results were tangential and did not provide sufficient specific detail "
            "to substantiate or disprove the factual assertions in this claim."
        )
    elif len(contradicting) > 0 and len(contradicting) >= len(supporting):
        verdict = VERDICT_CONTRADICTED
        confidence = 0.88
        explanation = (
            f"Retrieved authoritative sources indicate this claim is debunked, refuted, or factually contradicted. "
            f"Evidence from {len(contradicting)} source excerpt(s) directly disputes the statement."
        )
    elif len(contradicting) > 0 and len(supporting) > 0:
        verdict = VERDICT_PARTIAL
        confidence = 0.82
        explanation = (
            "Evidence indicates mixed or nuanced findings. Portions of the statement may be grounded in real "
            "events, but context is disputed, partially exaggerated, or conflicting across sources."
        )
    elif len(supporting) > 0:
        verdict = VERDICT_SUPPORTED
        confidence = 0.90
        explanation = (
            f"Retrieved authoritative reference materials corroborate the claim. "
            f"{len(supporting)} verified excerpt(s) confirm the key factual assertions."
        )
    else:
        verdict = VERDICT_INSUFFICIENT
        confidence = 0.75
        explanation = (
            "Available reference documents do not contain definitive confirmation or refutation "
            "for the precise factual proposition stated."
        )

    return {
        "claim": claim_text,
        "verdict": verdict,
        "confidence": confidence,
        "explanation": explanation,
        "citations": citations,
        "supporting_evidence": supporting[:4],
        "contradicting_evidence": contradicting[:4],
    }

