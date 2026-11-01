# HybridGuard AI — Architectural & Technical Decisions

## Decision 1: Model Architecture & Choice of Baselines
- **Context**: The project requires lightweight, CPU-compatible, highly explainable fake news classification without mandatory dependencies on paid APIs or heavy multi-gigabyte neural networks.
- **Decision**: Selected 3 complementary baseline models:
  1. *Logistic Regression*: Linear decision boundary, native calibrated probabilities, direct coefficient interpretability.
  2. *Linear Support Vector Classifier (LinearSVC)*: Maximum-margin hyperplane, robust against sparse high-dimensional TF-IDF vectors; calibrated via Platt scaling.
  3. *Multinomial Naive Bayes*: Probabilistic generative baseline, fast training, performs well with word occurrence counts/TF-IDF.
- **Ensemble Strategy**: Out-of-fold Stacking Classifier. Base models are trained across 5-fold cross-validation; their out-of-fold calibrated probability predictions serve as input features for a meta-estimator (Logistic Regression with L2 regularization). This eliminates in-sample leakage and provides an empirical performance boost.

## Decision 2: Feature Representation
- **Decision**: TF-IDF (Term Frequency - Inverse Document Frequency) with unigram and bigram tokens (`ngram_range=(1,2)`), sublinear TF scaling (`sublinear_tf=True`), and capped vocabulary (`max_features=25000`).
- **Rationale**: Captures both single-word semantic markers (e.g. sensationalist words like "shocking", "hoax") and critical bi-gram context (e.g. "not true", "breaking news", "conspiracy theory") while preserving low latency (< 15ms per document on standard CPU).

## Decision 3: Uncertainty Quantification & "Needs Review" Threshold
- **Context**: High-stakes news verification requires admitting uncertainty rather than forcing a binary classification on borderline claims.
- **Decision**: Implemented dual-sided probability calibration and a configurable uncertainty band around 0.50 (e.g., predicted probability between 0.40 and 0.60, or max class confidence < 0.65). Articles falling within this band are flagged with `Needs Review` and accompanied by a cautionary alert.
- **Expected Calibration Error (ECE)** is calculated across 10 reliability bins to measure discrepancy between predicted probabilities and true frequencies.

## Decision 4: Separation of Stylistic ML Detection vs. Factual Verification
- **Context**: Machine learning text classification analyzes lexical and stylistic patterns (sensationalism, emotive cues, syntax), but cannot know whether an empirical real-world claim (e.g. "The moon landing occurred in 1969") is factually true.
- **Decision**: Decoupled the ML classifier from the Fact-Checking Engine:
  - *ML Classifier*: Detects stylistic, lexical, and structural deception patterns.
  - *Fact-Checking Engine*: Extracts factual claims and verifies them against external reference knowledge (Wikipedia REST API, verified web sources) with authentic URLs and stance determination.

## Decision 5: Video & Shorts Transcript Architecture
- **Decision**: Support YouTube standard and Shorts URLs (`youtube.com/shorts/...`, `youtu.be/...`). Use `youtube-transcript-api` as primary caption extractor with graceful fallback to manual user input when captions are disabled or unavailable. Segments are mapped to timestamped ranges that seek the embedded YouTube iframe.

## Decision 6: Explainability Implementation
- **Decision**: Linear feature attribution mapping TF-IDF active terms to model weight vectors. Outputs the top 10 tokens pushing towards "Fake" (positive attribution) and top 10 tokens pushing towards "Real" (negative attribution), along with base model agreement percentages.

