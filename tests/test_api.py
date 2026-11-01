"""Integration tests for all FastAPI endpoints using TestClient."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "stylistic_fake_news_classification" in data["active_features"]


def test_model_info_endpoint(client):
    res = client.get("/api/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_name"] == "WELFake"
    assert "models" in data


def test_metrics_endpoint(client):
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "hybrid_stacking" in data
    assert "logistic_regression" in data
    assert "accuracy" in data["hybrid_stacking"]["metrics"]


def test_predict_endpoint_valid(client):
    payload = {
        "text": "BREAKING: NASA announces sensational discovery of ancient civilization on Mars using secret military equipment!",
        "explain": True,
        "top_n_words": 5,
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["prediction"] in ("Fake", "Real")
    assert 0.0 <= data["confidence"] <= 1.0
    assert len(data["individual_models"]) == 3
    assert len(data["top_fake_words"]) > 0 or len(data["top_real_words"]) > 0


def test_predict_endpoint_short_text_validation(client):
    payload = {"text": "Too short"}
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 422  # Pydantic validation error


def test_batch_predict_endpoint(client):
    payload = {
        "texts": [
            "Senate approves bipartisan funding measure following lengthy floor debate.",
            "SHOCKING: Aliens captured in underground bunker by secret military agents!",
        ],
        "explain": False,
    }
    res = client.post("/api/batch-predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2
    assert len(data["results"]) == 2


def test_fact_check_claim_extraction(client):
    payload = {
        "text": "Alexander Fleming discovered penicillin in 1928. Many people believe coffee is wonderful.",
        "max_claims": 5,
    }
    res = client.post("/api/claims/extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_extracted"] >= 1


def test_video_analysis_invalid_url(client):
    payload = {"url": "https://not-youtube.com/watch?v=123"}
    res = client.post("/api/video/analyze", json=payload)
    assert res.status_code == 400


def test_transcript_analyze_endpoint(client):
    payload = {
        "transcript": "[00:00] NASA confirmed that the Apollo 11 mission reached the Moon in 1969.",
        "max_claims": 2,
    }
    res = client.post("/api/transcript/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "timestamped_claims" in data


def test_speech_session_flow(client):
    # 1. Start Session
    res_sess = client.post("/api/speech/session")
    assert res_sess.status_code == 200
    session_id = res_sess.json()["session_id"]

    # 2. Ingest Chunk
    chunk_payload = {
        "session_id": session_id,
        "text": "The United Nations General Assembly was established in 1945.",
        "timestamp_sec": 5.0,
        "is_final": True,
    }
    res_chunk = client.post("/api/speech/chunk", json=chunk_payload)
    assert res_chunk.status_code == 200

    # 3. Get Status
    res_status = client.get(f"/api/speech/status/{session_id}")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["is_active"] is True
    assert status_data["transcript_segment_count"] >= 1




def test_headline_only_prediction_requires_review(client):
    payload = {
        "text": "Karnataka SIR: 64.5 lakh voters potentially missing in rolls, majority of them young",
        "explain": False,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_model"] == "linear_svm"
    assert data["input_word_count"] < 80
    assert data["needs_review"] is True
    assert "trained on full news articles" in data["input_warning"]


def test_full_article_prediction_includes_scope_warning(client):
    article = (
        "The Karnataka electoral roll revision process has prompted questions about "
        "the number of eligible voters who may not appear in the updated rolls. "
        "Officials and researchers have discussed the methodology used to estimate "
        "the eligible population. The estimate depends on population projections "
        "and elector-to-population ratios, so it should not be interpreted as a "
        "confirmed count of deleted voters. Independent reporting has examined "
        "the figures and explained the limitations of the estimate. "
    ) * 5
    response = client.post("/api/predict", json={"text": article, "explain": False})
    assert response.status_code == 200
    data = response.json()
    assert data["input_word_count"] >= 80
    assert "not proof of factual accuracy" in data["input_warning"]
