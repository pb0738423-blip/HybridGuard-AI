"""Claim Extraction and Checkability Filter for HybridGuard AI.
Distinguishes checkable factual statements from opinions, predictions, and rhetoric.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("hybridguard.claim_extractor")

# Subjective & non-checkable indicators
OPINION_MARKERS = [
    r"\bi think\b", r"\bi feel\b", r"\bi believe\b", r"\bin my opinion\b",
    r"\bmy view is\b", r"\bit seems to me\b", r"\bprobably\b", r"\bmaybe\b",
    r"\bmight be\b", r"\bcould possibly\b", r"\barguably\b", r"\bpersonally\b",
    r"\bi hope\b", r"\bi wish\b", r"\bi suspect\b", r"\bto me\b",
]

PREDICTION_MARKERS = [
    r"\bwill happen in\b", r"\bwill likely\b", r"\bpredicted to\b",
    r"\bforecasted to\b", r"\bwill eventually\b", r"\bgoing to happen\b",
    r"\bby 2030\b", r"\bby 2050\b", r"\bin the coming years\b",
]

FACTUAL_CUES = [
    r"\b\d{4}\b",  # year
    r"\b\d+%\b",   # percentage
    r"\b\$?\d+[\d,.]*\b", # quantities / numbers
    r"\bpresident\b", r"\bminister\b", r"\bgovernment\b", r"\bnasa\b", r"\bwho\b",
    r"\bcdc\b", r"\bunited nations\b", r"\bstudy finds\b", r"\bresearch shows\b",
    r"\bconfirmed that\b", r"\breported that\b", r"\bannounced that\b",
    r"\bpassed the law\b", r"\bsigned an executive order\b", r"\bdiscovered\b",
]


def split_into_candidate_sentences(text: str) -> List[str]:
    """Segment raw text into sentences while respecting abbreviations and numbers."""
    if not text or not text.strip():
        return []

    # Clean redundant whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split on sentence terminals followed by space and capital letter or end of string
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])", text)
    candidates = []
    for s in raw_sentences:
        s = s.strip()
        if len(s) >= 15:  # Minimum length for a meaningful claim
            candidates.append(s)
    return candidates


def classify_sentence_checkability(sentence: str) -> Dict[str, Any]:
    """Analyze whether a sentence represents a checkable factual claim or subjective opinion/prediction."""
    lower_s = sentence.lower()

    # Check for questions
    if sentence.endswith("?") or lower_s.startswith(("what ", "why ", "how ", "is it ", "are they ", "can we ")):
        return {
            "text": sentence,
            "is_checkable": False,
            "category": "Question / Rhetorical",
            "reason": "Questions and rhetorical inquiries cannot be verified as factual assertions.",
            "checkability_score": 0.05,
        }

    # Check for exclamations / conversational rhetoric
    if sentence.endswith("!") and len(sentence.split()) <= 4:
        return {
            "text": sentence,
            "is_checkable": False,
            "category": "Interjection / Emotional Exclamation",
            "reason": "Short conversational interjections lack factual propositions.",
            "checkability_score": 0.10,
        }

    # Check for opinion markers
    opinion_hits = [m for m in OPINION_MARKERS if re.search(m, lower_s)]
    if opinion_hits:
        return {
            "text": sentence,
            "is_checkable": False,
            "category": "Subjective Opinion / Belief",
            "reason": f"Contains subjective framing markers: {', '.join(opinion_hits)}.",
            "checkability_score": 0.20,
        }

    # Check for forward-looking predictions
    prediction_hits = [m for m in PREDICTION_MARKERS if re.search(m, lower_s)]
    if prediction_hits:
        return {
            "text": sentence,
            "is_checkable": False,
            "category": "Future Prediction",
            "reason": "Forward-looking forecasts cannot be empirically verified at present.",
            "checkability_score": 0.25,
        }

    # Score factual markers
    factual_hits = [m for m in FACTUAL_CUES if re.search(m, lower_s)]
    has_verbs = bool(re.search(r"\b(is|was|were|are|became|signed|claimed|died|won|lost|passed|stated|funded|created|banned|invented|caused)\b", lower_s))

    score = 0.50
    if factual_hits:
        score += min(0.35, 0.10 * len(factual_hits))
    if has_verbs:
        score += 0.10

    # Ensure length isn't too short or too long
    words = sentence.split()
    if 5 <= len(words) <= 50:
        score += 0.05

    score = min(0.98, max(0.10, score))

    is_checkable = score >= 0.55

    return {
        "text": sentence,
        "is_checkable": is_checkable,
        "category": "Checkable Factual Assertion" if is_checkable else "Unverified Statement",
        "reason": "Empirically verifiable statement specifying entities, actions, or events." if is_checkable else "Lacks distinct verifiable factual assertions.",
        "checkability_score": round(score, 2),
    }


def extract_claims_from_text(text: str, max_claims: int = 10) -> List[Dict[str, Any]]:
    """Extract checkable factual claims from arbitrary text, articles, or transcripts."""
    sentences = split_into_candidate_sentences(text)
    if not sentences and text.strip():
        # Fallback to single text if no punctuation split occurred
        sentences = [text.strip()]

    extracted = []
    for s in sentences:
        analysis = classify_sentence_checkability(s)
        extracted.append(analysis)

    # Sort so checkable claims appear first
    sorted_claims = sorted(extracted, key=lambda c: (c["is_checkable"], c["checkability_score"]), reverse=True)
    return sorted_claims[:max_claims]

