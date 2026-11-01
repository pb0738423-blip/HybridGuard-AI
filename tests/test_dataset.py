"""Unit tests for dataset preparation, schema validation, and zero-leakage splitting."""

import numpy as np
import pandas as pd
import pytest

from src.ml.dataset import clean_and_prepare, create_stratified_splits, LABEL_MAPPING


def test_clean_and_prepare_validation():
    # Test valid dataframe with duplicates and empty records
    raw_data = {
        "title": ["Real News Headline", "Fake News Headline", "Real News Headline", "", None],
        "text": [
            "This is a legitimate news story regarding international events.",
            "Shocking secret alien conspiracy exposed by anonymous whistleblowers!",
            "This is a legitimate news story regarding international events.", # Duplicate
            "Short", # Too short (<30 chars)
            "",
        ],
        "label": [0, 1, 0, 1, 0],
    }
    df = pd.DataFrame(raw_data)
    cleaned = clean_and_prepare(df)

    assert len(cleaned) == 2, "Expected 2 valid unique records"
    assert "combined_text" in cleaned.columns
    assert set(cleaned["label"].unique()).issubset({0, 1})


def test_zero_leakage_stratified_splits():
    # Create synthetic dataset with 100 balanced records
    texts = [f"Unique article body number {i} with sufficient length for testing." for i in range(100)]
    labels = [i % 2 for i in range(100)]
    df = pd.DataFrame({"title": [f"Title {i}" for i in range(100)], "text": texts, "label": labels})
    cleaned = clean_and_prepare(df)

    train_df, val_df, test_df = create_stratified_splits(cleaned, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Check zero overlap (zero data leakage)
    train_set = set(train_df["combined_text"])
    val_set = set(val_df["combined_text"])
    test_set = set(test_df["combined_text"])

    assert len(train_set.intersection(val_set)) == 0
    assert len(train_set.intersection(test_set)) == 0
    assert len(val_set.intersection(test_set)) == 0


def test_label_mapping():
    assert LABEL_MAPPING[0] == "Real"
    assert LABEL_MAPPING[1] == "Fake"

