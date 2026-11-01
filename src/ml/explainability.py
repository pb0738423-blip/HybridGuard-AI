"""Explainable AI (XAI) module for HybridGuard AI.
Computes feature attributions, influential words/tokens, and ensemble component contributions.
Includes strict scientific scoping to prevent misrepresenting stylistic correlation as real-world truth.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger("hybridguard.explainability")

EXPLANATION_SCOPE_DISCLAIMER = (
    "Model explanations identify lexical, stylistic, and emotional terms strongly correlated with "
    "fabricated vs. verified news within the training distribution. Feature attributions indicate "
    "stylistic influence on the ML classification score, not empirical truth or real-world verification."
)


def extract_top_features(
    feature_names: np.ndarray,
    coefficients: np.ndarray,
    x_sparse: csr_matrix,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Calculate token-level feature attribution for a single text instance.
    
    contribution_j = x_j * w_j
    Positive values push toward 'Fake' (Class 1).
    Negative values push toward 'Real' (Class 0).
    """
    # Extract non-zero column indices and their TF-IDF values
    row = x_sparse.getrow(0)
    col_indices = row.indices
    tfidf_values = row.data

    if len(col_indices) == 0:
        return {
            "top_fake_words": [],
            "top_real_words": [],
            "attribution_summary": "No active vocabulary terms detected in input text.",
        }

    # Word weights for active features
    weights = coefficients[col_indices]
    attributions = tfidf_values * weights

    # Pair features with their attribution scores
    tokens = feature_names[col_indices]
    items = list(zip(tokens, attributions, tfidf_values))

    # Sort descending for Fake-oriented (highest positive)
    items_fake = sorted([it for it in items if it[1] > 0], key=lambda x: x[1], reverse=True)[:top_n]
    # Sort ascending for Real-oriented (most negative)
    items_real = sorted([it for it in items if it[1] < 0], key=lambda x: x[1])[:top_n]

    top_fake_words = [
        {
            "word": str(token),
            "attribution": round(float(attr), 4),
            "tfidf_weight": round(float(tfidf), 4),
            "influence": "Pushes towards Fake",
        }
        for token, attr, tfidf in items_fake
    ]

    top_real_words = [
        {
            "word": str(token),
            "attribution": round(float(abs(attr)), 4),  # positive magnitude
            "raw_attribution": round(float(attr), 4),
            "tfidf_weight": round(float(tfidf), 4),
            "influence": "Pushes towards Real",
        }
        for token, attr, tfidf in items_real
    ]

    return {
        "top_fake_words": top_fake_words,
        "top_real_words": top_real_words,
        "active_tokens_count": int(len(col_indices)),
    }


class ModelExplainer:
    """Provides unified explanations for baseline models and the hybrid stacking ensemble."""

    def __init__(
        self,
        feature_names: np.ndarray,
        lr_model: Any,
        svm_model: Any,
        meta_weights: Optional[Dict[str, float]] = None,
        selected_model: str = "hybrid_stacking",
    ):
        self.feature_names = feature_names
        self.selected_model = selected_model
        self.lr_coef = lr_model.coef_[0] if hasattr(lr_model, "coef_") else None
        self.meta_weights = meta_weights or {"logistic_regression": 1.0}

        # For calibrated LinearSVC, extract base estimator coef if possible
        if hasattr(svm_model, "calibrated_classifiers_"):
            base_svm = svm_model.calibrated_classifiers_[0].estimator
            self.svm_coef = base_svm.coef_[0] if hasattr(base_svm, "coef_") else None
        elif hasattr(svm_model, "coef_"):
            self.svm_coef = svm_model.coef_[0]
        else:
            self.svm_coef = None

        # Build composite ensemble coefficients
        self.composite_coef = self._build_composite_coef()

    def _build_composite_coef(self) -> np.ndarray:
        """Return coefficients matching the model selected for prediction."""
        if self.selected_model == "linear_svm":
            if self.svm_coef is not None:
                return self.svm_coef
            return np.zeros(len(self.feature_names))
        if self.selected_model == "logistic_regression":
            return self.lr_coef if self.lr_coef is not None else np.zeros(len(self.feature_names))
        if self.lr_coef is None:
            return np.zeros(len(self.feature_names))

        lr_w = float(self.meta_weights.get("logistic_regression", 1.0))
        svm_w = float(self.meta_weights.get("linear_svm", 0.0))

        composite = lr_w * self.lr_coef
        if self.svm_coef is not None:
            composite += svm_w * self.svm_coef

        return composite

    def explain_instance(self, x_sparse: csr_matrix, top_n: int = 10) -> Dict[str, Any]:
        """Explain model prediction for a single sparse input instance."""
        coef_to_use = self.composite_coef if self.composite_coef is not None else self.lr_coef
        feature_data = extract_top_features(self.feature_names, coef_to_use, x_sparse, top_n=top_n)

        return {
            "top_fake_words": feature_data["top_fake_words"],
            "top_real_words": feature_data["top_real_words"],
            "active_tokens_count": feature_data["active_tokens_count"],
            "scope_disclaimer": EXPLANATION_SCOPE_DISCLAIMER,
            "meta_contributions": self.meta_weights,
        }

