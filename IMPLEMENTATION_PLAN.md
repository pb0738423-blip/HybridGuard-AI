# HybridGuard AI — Implementation Plan

## Overview
HybridGuard AI is an enterprise-grade, explainable hybrid fake news detection and real-time evidence-based fact-checking system. This document outlines the roadmap across 10 structured execution phases.

---

## Phase 1: Workspace Inspection & Dataset Audit (COMPLETED)
- Inspect environment, tool versions, and disk capabilities.
- Audit genuine datasets (WELFake selected from HuggingFace `davanstrien/WELFake`).
- Establish project directory structure, requirements, and state files.

## Phase 2: Data Pipeline & Baseline Classifiers
- **Dataset Handler (`src/ml/dataset.py`)**:
  - Securely fetch WELFake dataset into `data/raw/`.
  - Validate schema (`title`, `text`, `label`).
  - Drop null/empty records, deduplicate text to avoid test leakage.
  - Stratified 70/15/15 train-val-test split saved as CSV/parquet.
- **Preprocessor (`src/ml/preprocessor.py`)**:
  - Text normalization: lowercase, URL strip, special token normalization, contraction expansion.
  - TF-IDF Vectorizer with unigrams & bigrams (`ngram_range=(1,2)`), `max_features=25000`, `min_df=3`, `sublinear_tf=True`.
  - Strictly fit on training set only.
- **Baseline Models (`src/ml/baselines.py`)**:
  - Model 1: Logistic Regression (`C=1.0`, `solver='lbfgs'`, `max_iter=1000`).
  - Model 2: Linear Support Vector Machine (`LinearSVC` calibrated via Platt scaling or CalibratedClassifierCV).
  - Model 3: Multinomial Naive Bayes (`alpha=0.5`).
- **Artifact Serialization**:
  - Save fitted models and vectorizer into `models/artifacts/` with version tags.

## Phase 3: Hybrid Stacking Ensemble, Calibration, & Explainability
- **Stacking Meta-Classifier (`src/ml/hybrid.py`)**:
  - Out-of-fold cross-validation (`cv=5`) to generate out-of-sample prediction probabilities from base models.
  - Meta-learner: Logistic Regression or Ridge Classifier trained strictly on out-of-fold probability vectors to avoid overfitting.
- **Probability Calibration & Uncertainty Estimation**:
  - Isotonic / Sigmoid Platt calibration.
  - Expected Calibration Error (ECE) with 10 equal-frequency or equal-width bins.
  - Brier score, Negative Log-Likelihood (log loss).
  - Configurable `Needs Review` threshold (e.g. prediction confidence within margin of 0.50).
- **Explainable AI (`src/ml/explainability.py`)**:
  - Exact linear feature attribution based on model coefficients and TF-IDF term weights.
  - Signed contribution breakdown: words pulling toward "Fake" vs "Real".
  - Base model agreement / variance metric.
- **Evaluation Engine (`src/ml/evaluate.py`)**:
  - Test set metrics: Accuracy, Precision, Recall, F1, Macro F1, ROC-AUC, PR-AUC, Confusion Matrix, Latency per sample.
  - Save evaluation reports into `models/evaluation/metrics.json` and `models/evaluation/confusion_matrix.json`.

## Phase 4: Evidence-Based Fact-Checking Engine
- **Claim Extractor (`src/fact_check/claim_extractor.py`)**:
  - Decompose paragraph into candidate sentences.
  - Filter subjective statements, questions, predictions, and personal opinions using grammatical markers and linguistic cues.
  - Output clean, testable factual claims.
- **Web Evidence Search Provider (`src/fact_check/search_provider.py`)**:
  - Pluggable interface: `SearchProvider` base class.
  - Wikipedia Search & Summary API: Retrieves genuine Wikipedia article summaries, references, and URLs.
  - DuckDuckGo Instant Answer / HTML Search Provider: Queries live web for factual assertions.
  - Robust error handling, rate limiting, and zero hallucinated citations.
- **Stance & Verdict Synthesizer (`src/fact_check/evidence_evaluator.py`)**:
  - Compare retrieved evidence text against claim text using token overlap, semantic cosine similarity, and contradiction indicators.
  - Assign standardized verdicts:
    - `Supported`
    - `Contradicted`
    - `Partially Supported / Misleading`
    - `Insufficient Evidence`
    - `Not a Checkable Factual Claim`
  - Output verified citation links, publication sources, and contextual explanations.

## Phase 5: YouTube Video & Shorts Analysis
- **URL Parser & Validator (`src/video/url_validator.py`)**:
  - Handle standard YouTube URLs (`youtube.com/watch?v=...`), shortlinks (`youtu.be/...`), and Shorts (`youtube.com/shorts/...`).
  - Extract sanitized 11-character video ID.
- **Transcript Extraction (`src/video/transcript.py`)**:
  - Attempt retrieval via `youtube-transcript-api` and `yt-dlp`.
  - Fallback to user-provided manual transcript or pasted text if captions are disabled or rate-limited.
- **Transcript Segmentation & Timeline (`src/video/segmenter.py`)**:
  - Segment captions into coherent chunks with start/end timestamps.
  - Extract claims per segment with direct timestamp references.
  - Pass timestamped claims into evidence engine.

## Phase 6: Real-Time Speech Verification Extension
- **Speech Ingestion & Queue (`src/speech/realtime.py`)**:
  - WebSocket or streaming chunk receiver.
  - Speech-to-text integration (Web Speech API in frontend, with local backend buffer and worker queue).
  - Claim detection on rolling transcript window.
  - Asynchronous background task verification with real-time status updates and latency tracking.

## Phase 7: FastAPI Backend Implementation
- Implement REST API endpoints:
  - `GET /health`
  - `GET /api/model-info`
  - `GET /api/metrics`
  - `POST /api/predict`
  - `POST /api/batch-predict`
  - `POST /api/fact-check`
  - `POST /api/claims/extract`
  - `POST /api/video/analyze`
  - `POST /api/transcript/analyze`
  - `GET /api/analysis/{analysis_id}`
- Pydantic v2 schemas, CORS middleware, structured logging, request size limit, exception handlers.

## Phase 8: Polished React + Vite Frontend
- Vite + React + Tailwind CSS single-page application with 6 core navigation views:
  1. **Dashboard**: High-level system overview, quick action cards, stats.
  2. **News Detection**: Live text classifier, character counter, model comparison cards, confidence gauge, word attribution pills, uncertainty alert.
  3. **Fact-Checking**: Claim verification engine, claim extractor, evidence cards, citations with clickable source links, stance indicators.
  4. **Video Analysis**: YouTube URL & Shorts input, embedded responsive video player, interactive transcript timeline, timestamp seeking, verdict cards.
  5. **Model Dashboard**: Recharts interactive visualizations (ROC curves, PR curves, Confusion Matrix, ECE reliability diagrams, latency benchmarks).
  6. **About & Methodology**: System architecture, mathematical formulation, dataset card, known limitations, academic citations.
  7. **Live Speech Fact-Check**: Microphone activation, live streaming transcript, incremental claim cards.

## Phase 9: Testing & Verification
- Unit and integration tests covering:
  - Data loading, cleaning, and zero-leakage split verification.
  - Model serialization and loading.
  - Inference correctness and probability calibration.
  - Explainability attribution sign and magnitude.
  - All FastAPI endpoints using `TestClient`.
  - YouTube URL parsing and transcript fallback.
  - Fact-checking evidence retrieval and citation validation.
  - Frontend production build verification (`npm run build`).

## Phase 10: Complete Documentation & Project Delivery
- Create comprehensive documentation:
  - `README.md`
  - `DATASET_CARD.md`
  - `DECISIONS.md`
  - `EXPERIMENT_LOG.md`
  - `docs/ARCHITECTURE.md`
  - `docs/API.md`
  - `docs/METHODOLOGY.md`
  - `docs/TROUBLESHOOTING.md`
  - `docs/VIVA_QUESTIONS.md`

