"""Text preprocessing and TF-IDF feature extraction pipeline for HybridGuard AI.
Strictly ensures vocabulary is learned on training split only.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger("hybridguard.preprocessor")


def clean_text_for_nlp(text: str, lower: bool = True, strip_urls: bool = True) -> str:
    """Preprocess raw text string for TF-IDF feature extraction.
    
    Normalizes whitespace, removes HTML tags, removes/normalizes URLs,
    and strips noise while preserving lexical indicators of sensationalism.
    """
    if not isinstance(text, str):
        return ""

    # Remove HTML tags if present
    cleaned = re.sub(r"<[^>]+>", " ", text)

    # Normalize or strip URLs
    if strip_urls:
        cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)

    # Normalize unicode quotes and dashes
    cleaned = re.sub(r"[‘’‚‛‹›]", "'", cleaned)
    cleaned = re.sub(r"[“”„‟«»]", '"', cleaned)
    cleaned = re.sub(r"[–—]", "-", cleaned)

    # Conditionally lowercase
    if lower:
        cleaned = cleaned.lower()

    # Collapse multiple whitespace/newlines into clean single spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class TextFeaturePipeline:
    """Encapsulates the TF-IDF feature extractor with serialization support."""

    def __init__(
        self,
        max_features: int = 25000,
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 3,
        max_df: float = 0.90,
        sublinear_tf: bool = True,
    ):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self.sublinear_tf = sublinear_tf

        self.vectorizer = TfidfVectorizer(
            preprocessor=clean_text_for_nlp,
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            sublinear_tf=self.sublinear_tf,
            token_pattern=r"(?u)\b\w[\w'-]+\b",  # include words with hyphens and apostrophes
        )
        self.is_fitted = False

    def fit(self, texts: List[str] | np.ndarray) -> TextFeaturePipeline:
        """Fit vectorizer on training texts only."""
        logger.info("Fitting TF-IDF vectorizer (max_features=%d, ngrams=%s)...", self.max_features, self.ngram_range)
        self.vectorizer.fit(texts)
        self.is_fitted = True
        logger.info("Fitted TF-IDF vocabulary size: %d terms", len(self.vectorizer.vocabulary_))
        return self

    def transform(self, texts: List[str] | np.ndarray) -> csr_matrix:
        """Transform texts into sparse TF-IDF feature matrix."""
        if not self.is_fitted:
            raise RuntimeError("Vectorizer is not fitted! Fit on training data first.")
        return self.vectorizer.transform(texts)

    def fit_transform(self, texts: List[str] | np.ndarray) -> csr_matrix:
        """Fit and transform on training data."""
        self.fit(texts)
        return self.vectorizer.transform(texts)

    def get_feature_names(self) -> np.ndarray:
        """Return array of feature/token names."""
        if not self.is_fitted:
            raise RuntimeError("Vectorizer is not fitted!")
        return self.vectorizer.get_feature_names_out()

    def save(self, filepath: str | Path = "models/artifacts/vectorizer.joblib") -> None:
        """Serialize fitted vectorizer and configuration."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Serialized TextFeaturePipeline to: %s", path)

    @classmethod
    def load(cls, filepath: str | Path = "models/artifacts/vectorizer.joblib") -> TextFeaturePipeline:
        """Load serialized vectorizer."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Vectorizer artifact not found at {path}")
        pipeline = joblib.load(path)
        logger.info("Loaded TextFeaturePipeline from %s (fitted=%s)", path, pipeline.is_fitted)
        return pipeline

