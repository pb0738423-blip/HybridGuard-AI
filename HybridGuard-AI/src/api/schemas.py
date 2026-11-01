"""Pydantic v2 schemas for HybridGuard AI API request/response validation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ===================== HEALTH & SYSTEM =====================

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    model_loaded: bool = False
    search_provider: str = "wikipedia"
    active_features: List[str] = Field(default_factory=list)


# ===================== PREDICTION SCHEMAS =====================

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=150000, description="News headline or article text to classify")
    explain: bool = Field(default=True, description="Whether to include token feature attributions")
    top_n_words: int = Field(default=10, ge=3, le=50, description="Number of influential words to extract")


class BatchPredictRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=100, description="List of articles to classify")
    explain: bool = Field(default=False, description="Whether to include explanations for batch items")


class ModelContribution(BaseModel):
    p_real: float
    p_fake: float
    prediction: str
    confidence: float


class WordAttribution(BaseModel):
    word: str
    attribution: float
    tfidf_weight: float
    influence: str


class PredictResponse(BaseModel):
    prediction: str
    label: int
    confidence: float
    p_real: float
    p_fake: float
    uncertainty_score: float
    needs_review: bool
    agreement_ratio: float
    individual_models: Dict[str, ModelContribution]
    meta_weights: Dict[str, float]
    top_fake_words: List[WordAttribution] = Field(default_factory=list)
    top_real_words: List[WordAttribution] = Field(default_factory=list)
    explanation_scope: str = ""


# ===================== FACT CHECKING SCHEMAS =====================

class FactCheckRequest(BaseModel):
    claim: str = Field(..., min_length=5, max_length=2000, description="Factual claim or assertion to verify")
    max_evidence_results: int = Field(default=4, ge=1, le=10, description="Max web/knowledge search results to retrieve")


class ClaimExtractRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text from which to extract checkable claims")
    max_claims: int = Field(default=8, ge=1, le=25)


class Citation(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published_date: Optional[str] = None
    confidence_score: float = 0.8


class EvidenceExcerpt(BaseModel):
    source_title: str
    source_url: str
    excerpt: str
    relevance_score: float


class FactCheckResponse(BaseModel):
    claim: str
    verdict: str
    confidence: float
    explanation: str
    citations: List[Citation] = Field(default_factory=list)
    supporting_evidence: List[EvidenceExcerpt] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceExcerpt] = Field(default_factory=list)
    checkability_info: Optional[Dict[str, Any]] = None


# ===================== VIDEO & TRANSCRIPT SCHEMAS =====================

class VideoAnalyzeRequest(BaseModel):
    url: str = Field(..., description="YouTube video or Shorts URL")
    manual_transcript: Optional[str] = Field(default=None, description="Optional manual transcript if captions are unavailable")
    max_claims: int = Field(default=6, ge=1, le=15)


class TranscriptAnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=15, max_length=200000, description="Pasted transcript text with or without timestamps")
    video_id: Optional[str] = Field(default=None, description="Optional associated YouTube video ID")
    max_claims: int = Field(default=6, ge=1, le=15)


class TimestampedClaimResult(BaseModel):
    claim: str
    timestamp_seconds: float
    timestamp_formatted: str
    chunk_context: str
    is_checkable: bool
    checkability_category: str
    verdict: str
    confidence: float
    explanation: str
    citations: List[Citation] = Field(default_factory=list)
    supporting_evidence: List[EvidenceExcerpt] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceExcerpt] = Field(default_factory=list)


class VideoAnalysisResponse(BaseModel):
    video_id: Optional[str] = None
    is_shorts: bool = False
    embed_url: Optional[str] = None
    canonical_url: Optional[str] = None
    transcript_source: str
    summary: Dict[str, Any]
    timeline_chunks: List[Dict[str, Any]]
    timestamped_claims: List[TimestampedClaimResult]


# ===================== SPEECH SCHEMAS =====================

class SpeechChunkRequest(BaseModel):
    session_id: str
    text: str
    timestamp_sec: float
    is_final: bool = True
