# HybridGuard AI — System Architecture Document

## 1. High-Level Architectural Overview

HybridGuard AI is designed as a decoupled, multi-engine verification platform that explicitly separates **stylistic statistical deception detection** from **grounded empirical fact-checking**.

```
                           ┌───────────────────────────────────────────────┐
                           │          React + Vite + Tailwind UI           │
                           │   (Dashboard, Detector, FactCheck, Video,     │
                           │    Model Benchmarks, Speech Stream, Method)   │
                           └───────────────────────┬───────────────────────┘
                                                   │ HTTP / REST / JSON
                                                   ▼
                           ┌───────────────────────────────────────────────┐
                           │         FastAPI Backend Application           │
                           │    • Input Validation & Size Limit Guard      │
                           │    • Structured Request Logging & CORS        │
                           │    • Asynchronous Speech & Video Handlers     │
                           └───────────────┬───────────────────────┬───────┘
                                           │                       │
                 ┌─────────────────────────┴─────────┐   ┌─────────┴───────────────────────┐
                 │                                   │   │                                 │
                 ▼                                   ▼   ▼                                 ▼
   ┌───────────────────────────┐       ┌───────────────────────────┐     ┌───────────────────────────┐
   │ Machine Learning Pipeline │       │ Evidence Fact-Checker     │     │ Video & Speech Pipelines  │
   ├───────────────────────────┤       ├───────────────────────────┤     ├───────────────────────────┤
   │ • TF-IDF (1,2 ngrams)     │       │ • Claim Extractor         │     │ • YouTube URL & Shorts    │
   │ • Logistic Regression     │       │ • Search Providers:       │     │   Identifier (11-char)    │
   │ • Linear SVM (Calibrated) │       │   - Wikipedia REST API    │     │ • youtube-transcript-api  │
   │ • Multinomial Naive Bayes │       │   - DuckDuckGo Instant    │     │ • Manual Fallback Parser  │
   │ • 5-Fold Stacking Meta    │       │ • Stance Evaluator        │     │ • Timeline Segmenter      │
   │ • Platt Sigmoid Scaling   │       │ • Genuine Source Links    │     │ • Live Audio Stream Queue │
   │ • Linear Feature Attrib   │       │ • Zero Hallucination      │     │ • Latency Counter         │
   └───────────────────────────┘       └───────────────────────────┘     └───────────────────────────┘
```

---

## 2. Component Deconstruction

### 2.1 Machine Learning Classification Engine (`src/ml/`)
- **Preprocessor (`src/ml/preprocessor.py`)**:
  - Text normalization: HTML removal, URL stripping, contraction normalization.
  - TF-IDF Vectorizer with unigrams & bigrams (`ngram_range=(1,2)`), `max_features=25000`, `min_df=3`, `sublinear_tf=True`.
  - Strictly fitted only on the training split to guarantee zero data leakage.
- **Baseline Models (`src/ml/baselines.py`)**:
  - *Logistic Regression*: L2 penalty, lbfgs solver, max_iter=1000.
  - *Linear SVM (Calibrated)*: LinearSVC calibrated via Platt Sigmoid scaling (`CalibratedClassifierCV(method='sigmoid', cv=3)`).
  - *Multinomial Naive Bayes*: Laplace smoothing `alpha=0.5`.
- **Hybrid Stacking Classifier (`src/ml/hybrid.py`)**:
  - Out-of-fold cross-validation (`cv=5`) meta-model training.
  - Meta-learner: L2-regularized Logistic Regression trained strictly on out-of-fold probability vectors.
  - Uncertainty thresholding: Articles with prediction confidence $< 0.65$ or $|P(\text{Fake}) - 0.50| < 0.15$ are flagged with `Needs Review`.
- **Explainability (`src/ml/explainability.py`)**:
  - Token-level linear feature attribution: $\text{attribution}_j = x_j \cdot w_{\text{composite}, j}$.
  - Identifies top tokens pushing toward `Fake` (positive weights) and `Real` (negative weights).
  - Explicit scientific scope disclaimer preventing conflation of stylistic correlation with empirical truth.

### 2.2 Evidence-Based Fact-Checking Engine (`src/fact_check/`)
- **Claim Extractor (`src/fact_check/claim_extractor.py`)**:
  - Splits input text into candidate propositions.
  - Linguistic checkability filter: Rejects rhetorical questions, future predictions, and subjective opinion markers.
- **Search Provider (`src/fact_check/search_provider.py`)**:
  - Pluggable `SearchProvider` interface.
  - `WikipediaSearchProvider`: Queries MediaWiki Search API and Wikipedia REST summary endpoints.
  - `DuckDuckGoSearchProvider`: Queries DuckDuckGo Instant Answer API.
  - Zero hallucination policy: If external evidence is missing, the system outputs `Insufficient Evidence` instead of inventing citations.
- **Evidence Evaluator (`src/fact_check/evidence_evaluator.py`)**:
  - Analyzes lexical and semantic overlap between claims and retrieved excerpts.
  - Detects contradiction/debunking markers vs. corroboration markers.
  - Assigns one of 5 standardized verdicts:
    1. `Supported`
    2. `Contradicted`
    3. `Partially Supported / Misleading`
    4. `Insufficient Evidence`
    5. `Not a Checkable Factual Claim`

### 2.3 YouTube Video & Shorts Analysis (`src/video/`)
- **URL Validator (`src/video/url_validator.py`)**:
  - Extracts 11-character video IDs from YouTube desktop URLs, mobile links, shortlinks, and YouTube Shorts (`/shorts/aUyVATJqEoQ`).
  - Generates embed links with YouTube IFrame API parameters (`enablejsapi=1`).
- **Transcript Ingestion (`src/video/transcript.py`)**:
  - Primary retrieval via `youtube-transcript-api`.
  - Robust fallback parser for user-pasted transcripts with explicit (`[01:23]`) or estimated pacing.
- **Timeline Segmenter (`src/video/segmenter.py`)**:
  - Chunks transcripts into timeline intervals.
  - Associates extracted claims with video timestamps for one-click seeking.

### 2.4 Live Speech Fact-Checking Stream (`src/speech/`)
- **Session Manager (`src/speech/realtime.py`)**:
  - Ingests streaming speech chunks via Web Speech API or simulated broadcast feed.
  - Deduplicates claims using cryptographic hashing to prevent redundant external queries.
  - Bounded verification queue with asynchronous latency tracking.

---

## 3. Data Flow Pipelines

### 3.1 Text Classification Pipeline
$$\text{Raw Text} \xrightarrow{\text{Clean}} \text{Normalized String} \xrightarrow{\text{TF-IDF}} \mathbf{x} \in \mathbb{R}^{25000} \xrightarrow{\text{Base Models}} [P_{\text{lr}}, P_{\text{svm}}, P_{\text{nb}}] \xrightarrow{\text{Meta Estimator}} [P_{\text{Real}}, P_{\text{Fake}}] \xrightarrow{\text{Uncertainty Engine}} \text{Verdict + Needs Review}$$

### 3.2 Fact-Checking Pipeline
$$\text{Claim / Article} \xrightarrow{\text{Extract}} \{\text{Proposition}_i\} \xrightarrow{\text{Web Search}} \{\text{Evidence}_j\} \xrightarrow{\text{Stance Synthesizer}} \text{Verdict} + \{\text{Authentic URLs, Excerpts}\}$$

