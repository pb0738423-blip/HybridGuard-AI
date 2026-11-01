# HybridGuard AI — REST API Reference

The HybridGuard AI backend exposes a high-performance RESTful API powered by FastAPI, featuring input validation (Pydantic v2), structured logging, and automated OpenAPI documentation (`/docs` and `/redoc`).

---

## 1. Health & Metadata

### `GET /health`
Returns the operational health, model availability, and active capabilities of the server.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "search_provider": "wikipedia",
  "active_features": [
    "stylistic_fake_news_classification",
    "model_interpretability_and_attribution",
    "uncertainty_estimation_and_needs_review",
    "evidence_based_fact_checking",
    "youtube_video_and_shorts_analysis",
    "live_speech_verification_stream"
  ]
}
```

### `GET /api/model-info`
Returns configuration parameters, sample counts, feature engineering settings, and label mappings of the trained models.

### `GET /api/metrics`
Returns actual empirical metrics evaluated on the 3,750-sample held-out test split, including confusion matrices, ROC/PR curve points, calibration curve bins, and inference latencies.

---

## 2. Machine Learning Prediction

### `POST /api/predict`
Evaluates text for stylistic deception and sensationalism using the hybrid stacking ensemble.

**Request Body:**
```json
{
  "text": "BREAKING: NASA announces sensational discovery of ancient civilization on Mars!",
  "explain": true,
  "top_n_words": 10
}
```

**Response (200 OK):**
```json
{
  "prediction": "Fake",
  "label": 1,
  "confidence": 0.9897,
  "p_real": 0.0103,
  "p_fake": 0.9897,
  "uncertainty_score": 0.0821,
  "needs_review": false,
  "agreement_ratio": 1.0,
  "individual_models": {
    "logistic_regression": { "prediction": "Fake", "confidence": 0.985, "p_real": 0.015, "p_fake": 0.985 },
    "linear_svm": { "prediction": "Fake", "confidence": 0.992, "p_real": 0.008, "p_fake": 0.992 },
    "multinomial_nb": { "prediction": "Fake", "confidence": 0.912, "p_real": 0.088, "p_fake": 0.912 }
  },
  "meta_weights": {
    "logistic_regression": 3.3489,
    "linear_svm": 6.9960,
    "multinomial_nb": -0.8595
  },
  "top_fake_words": [
    { "word": "breaking", "attribution": 0.284, "tfidf_weight": 0.142, "influence": "Pushes towards Fake" },
    { "word": "secret", "attribution": 0.198, "tfidf_weight": 0.098, "influence": "Pushes towards Fake" }
  ],
  "top_real_words": [],
  "explanation_scope": "Model explanations identify lexical, stylistic, and emotional terms..."
}
```

### `POST /api/batch-predict`
Performs batch classification for up to 100 articles.

---

## 3. Evidence-Based Fact-Checking

### `POST /api/fact-check`
Verifies an individual factual assertion against live encyclopedia and web knowledge.

**Request Body:**
```json
{
  "claim": "The Apollo 11 mission landed humans on the Moon in July 1969.",
  "max_evidence_results": 4
}
```

**Response (200 OK):**
```json
{
  "claim": "The Apollo 11 mission landed humans on the Moon in July 1969.",
  "verdict": "Supported",
  "confidence": 0.90,
  "explanation": "Retrieved authoritative reference materials corroborate the claim. 4 verified excerpt(s) confirm the key factual assertions.",
  "citations": [
    {
      "title": "Apollo 11",
      "url": "https://en.wikipedia.org/wiki/Apollo_11",
      "snippet": "Apollo 11 was the American spaceflight that first landed humans on the Moon...",
      "source": "Wikipedia (Verified Wikimedia API)",
      "published_date": "2024-01-15T00:00:00Z"
    }
  ],
  "supporting_evidence": [
    {
      "source_title": "Apollo 11",
      "source_url": "https://en.wikipedia.org/wiki/Apollo_11",
      "excerpt": "Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969.",
      "relevance_score": 0.95
    }
  ],
  "contradicting_evidence": []
}
```

### `POST /api/claims/extract`
Deconstructs a text block into candidate factual claims and flags subjective opinions, rhetoric, or predictions.

### `POST /api/fact-check/article`
Deconstructs an article and fact-checks each extracted claim in a single request.

---

## 4. Video & YouTube Shorts Analysis

### `POST /api/video/analyze`
Extracts transcript from a YouTube standard or Shorts URL, groups timeline chunks, extracts timestamped claims, and verifies them.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/shorts/aUyVATJqEoQ",
  "manual_transcript": null,
  "max_claims": 6
}
```

### `POST /api/transcript/analyze`
Analyzes a manually provided transcript (with or without timestamps) and verifies extracted propositions.

---

## 5. Live Speech Fact-Checking

### `POST /api/speech/session`
Initializes a new real-time speech verification session.

### `POST /api/speech/chunk`
Ingests an incremental transcript segment from speech recognition.

### `GET /api/speech/status/{session_id}`
Returns the active transcript buffer, detected claims, and verification verdicts with latency metrics.

### `DELETE /api/speech/session/{session_id}`
Closes an active speech session.

