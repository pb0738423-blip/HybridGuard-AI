"""Health and system status routes for HybridGuard AI."""

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter

from src.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Check system health, model availability, and active capabilities."""
    hybrid_model_path = Path("models/artifacts/hybrid_model.joblib")
    vectorizer_path = Path("models/artifacts/vectorizer.joblib")
    is_model_loaded = hybrid_model_path.exists() and vectorizer_path.exists()

    active_features = [
        "stylistic_fake_news_classification",
        "model_interpretability_and_attribution",
        "uncertainty_estimation_and_needs_review",
        "evidence_based_fact_checking",
        "youtube_video_and_shorts_analysis",
        "live_speech_verification_stream",
    ]

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=is_model_loaded,
        search_provider="wikipedia",
        active_features=active_features,
    )

