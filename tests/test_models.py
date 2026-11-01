"""Unit tests for baseline models, hybrid stacking, probability calibration, and uncertainty."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from sklearn.datasets import make_classification

from src.ml.baselines import BaselineModelSuite
from src.ml.hybrid import HybridStackingClassifier


def test_baseline_model_suite(tmp_path):
    X, y = make_classification(n_samples=120, n_features=30, random_state=42)
    X_sparse = csr_matrix(np.abs(X))  # Non-negative for MultinomialNB

    suite = BaselineModelSuite(random_state=42)
    suite.fit(X_sparse, y)
    assert suite.is_fitted

    probas = suite.predict_proba(X_sparse[:5])
    assert "logistic_regression" in probas
    assert "linear_svm" in probas
    assert "multinomial_nb" in probas

    for name, p in probas.items():
        assert p.shape == (5, 2)
        assert np.allclose(p.sum(axis=1), 1.0)

    # Test serialization
    suite.save(tmp_path)
    reloaded = BaselineModelSuite.load(tmp_path)
    assert reloaded.is_fitted


def test_hybrid_stacking_classifier(tmp_path):
    X, y = make_classification(n_samples=150, n_features=35, random_state=42)
    X_sparse = csr_matrix(np.abs(X))

    hybrid = HybridStackingClassifier(
        cv_folds=3,
        uncertainty_threshold=0.65,
        uncertainty_margin=0.15,
        random_state=42,
    )
    hybrid.fit(X_sparse, y)
    assert hybrid.is_fitted
    assert hybrid.meta_weights_ is not None

    probas = hybrid.predict_proba(X_sparse[:10])
    assert probas.shape == (10, 2)
    assert np.allclose(probas.sum(axis=1), 1.0)

    # Uncertainty inference
    results = hybrid.predict_with_uncertainty(X_sparse[:5])
    assert len(results) == 5
    for r in results:
        assert "prediction" in r
        assert "confidence" in r
        assert "uncertainty_score" in r
        assert "needs_review" in r
        assert "individual_models" in r
        assert 0.0 <= r["confidence"] <= 1.0
        assert 0.0 <= r["uncertainty_score"] <= 1.0

    # Save and reload
    model_file = tmp_path / "hybrid.joblib"
    hybrid.save(model_file)
    reloaded = HybridStackingClassifier.load(model_file)
    assert reloaded.is_fitted

