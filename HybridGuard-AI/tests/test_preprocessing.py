"""Unit tests for text preprocessing, regex normalization, and TF-IDF pipeline."""

import numpy as np
import pytest

from src.ml.preprocessor import clean_text_for_nlp, TextFeaturePipeline


def test_clean_text_for_nlp():
    dirty = "   <p>BREAKING: Check this out at https://example.com/test! It's “huge” – indeed!   "
    cleaned = clean_text_for_nlp(dirty, lower=True, strip_urls=True)

    assert "<p>" not in cleaned
    assert "https://" not in cleaned
    assert "“" not in cleaned and "”" not in cleaned
    assert cleaned.startswith("breaking:")
    assert "it's" in cleaned


def test_text_feature_pipeline_fit_transform(tmp_path):
    pipeline = TextFeaturePipeline(max_features=100, ngram_range=(1, 2), min_df=1)
    texts = [
        "Government announces new economic policy today.",
        "Breaking news: aliens landed in the desert!",
        "Economic policy debate continues in senate hearings.",
        "Aliens discovered using secret military frequencies.",
    ]

    X = pipeline.fit_transform(texts)
    assert X.shape[0] == 4
    assert X.shape[1] <= 100
    assert pipeline.is_fitted

    # Save and reload test
    save_file = tmp_path / "vec.joblib"
    pipeline.save(save_file)
    reloaded = TextFeaturePipeline.load(save_file)

    assert reloaded.is_fitted
    X_reloaded = reloaded.transform(texts)
    assert np.allclose(X.toarray(), X_reloaded.toarray())

