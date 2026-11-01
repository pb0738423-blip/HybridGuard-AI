"""Unit tests for explainable AI token attribution and scientific scope disclaimers."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

from src.ml.explainability import (
    EXPLANATION_SCOPE_DISCLAIMER,
    ModelExplainer,
    extract_top_features,
)


def test_feature_attribution_extraction():
    feature_names = np.array(["breaking", "secret", "alien", "senate", "committee", "diplomatic"])
    # Coefficients: positive -> Fake, negative -> Real
    coefficients = np.array([2.5, 3.1, 4.0, -2.8, -3.2, -1.9])

    # Sample TF-IDF with active tokens
    data = np.array([0.5, 0.4, 0.6, 0.3])
    indices = np.array([0, 1, 3, 4])
    indptr = np.array([0, 4])
    x_sparse = csr_matrix((data, indices, indptr), shape=(1, 6))

    res = extract_top_features(feature_names, coefficients, x_sparse, top_n=2)
    assert len(res["top_fake_words"]) == 2
    assert len(res["top_real_words"]) == 2

    # Verify signs
    assert res["top_fake_words"][0]["attribution"] > 0
    assert "Real" in res["top_real_words"][0]["influence"]


def test_model_explainer():
    feature_names = np.array(["hoax", "official", "confirmed"])
    lr = LogisticRegression()
    lr.coef_ = np.array([[2.0, -1.5, -2.0]])
    lr.intercept_ = np.array([0.0])

    explainer = ModelExplainer(
        feature_names=feature_names,
        lr_model=lr,
        svm_model=lr,
        meta_weights={"logistic_regression": 1.0},
    )

    x_sparse = csr_matrix(([0.5, 0.8], [0, 2], [0, 2]), shape=(1, 3))
    explanation = explainer.explain_instance(x_sparse, top_n=2)

    assert "top_fake_words" in explanation
    assert "top_real_words" in explanation
    assert explanation["scope_disclaimer"] == EXPLANATION_SCOPE_DISCLAIMER

