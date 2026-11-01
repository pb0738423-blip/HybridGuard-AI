"""Dataset preparation, cleaning, deduplication, and stratified splitting for HybridGuard AI.
Strictly adheres to leak-free practices: fit transformations on train split only.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger("hybridguard.dataset")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

LABEL_MAPPING = {
    0: "Real",
    1: "Fake",
}

LABEL_DESCRIPTIONS = {
    0: "Reliable, fact-checked reporting adhering to journalistic standards",
    1: "Fabricated, unsubstantiated, or intentionally misleading content",
}


def load_raw_dataset(raw_path: str | Path = "data/raw/welfake.parquet") -> pd.DataFrame:
    """Load raw dataset from parquet or csv file."""
    path = Path(raw_path)
    if not path.exists():
        csv_path = path.with_suffix(".csv")
        if csv_path.exists():
            logger.info("Loading raw dataset from CSV: %s", csv_path)
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Raw dataset not found at {path} or {csv_path}")

    logger.info("Loading raw dataset from Parquet: %s", path)
    return pd.read_parquet(path)


def clean_and_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Clean missing values, normalize text, resolve duplicate/conflicting records.
    
    Returns a sanitized dataframe with columns: ['title', 'text', 'combined_text', 'label']
    """
    initial_count = len(df)
    logger.info("Initial record count: %d", initial_count)

    # Validate required columns
    required_cols = {"title", "text", "label"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Dataset missing required columns. Expected at least {required_cols}, found {df.columns.tolist()}")

    # Normalize column types
    df = df.copy()
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    
    # Cast label to integer, dropping non-binary values if any
    df = df[df["label"].isin([0, 1, "0", "1"])].copy()
    df["label"] = df["label"].astype(int)

    # Combine title and text
    df["combined_text"] = df.apply(
        lambda row: f"{row['title']}\n\n{row['text']}".strip() if row["title"] else row["text"],
        axis=1
    )

    # Filter out empty or trivially short articles (< 30 characters)
    df = df[df["combined_text"].str.len() >= 30].copy()
    logger.info("Records after filtering short text (<30 chars): %d", len(df))

    # Check and remove conflicting duplicate texts (same text with opposing labels)
    conflicts = df.groupby("combined_text")["label"].nunique()
    conflicting_texts = conflicts[conflicts > 1].index
    if len(conflicting_texts) > 0:
        logger.warning("Found %d articles with conflicting labels. Dropping them to preserve integrity.", len(conflicting_texts))
        df = df[~df["combined_text"].isin(conflicting_texts)].copy()

    # Deduplicate based on combined_text to prevent split leakage
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["combined_text"], keep="first").copy()
    logger.info("Deduplication removed %d duplicate articles (%d remaining)", before_dedup - len(df), len(df))

    # Class balance check
    class_counts = df["label"].value_counts().to_dict()
    logger.info("Cleaned dataset label distribution: %s (0=Real, 1=Fake)", class_counts)

    return df.reset_index(drop=True)


def create_stratified_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
    subsample_max: int | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataset into reproducible, stratified Train, Validation, and Test partitions.
    
    Guarantees no data leakage across partitions.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1.0"

    if subsample_max is not None and len(df) > subsample_max:
        logger.info("Subsampling dataset to %d records while preserving stratification...", subsample_max)
        df, _ = train_test_split(
            df,
            train_size=subsample_max,
            stratify=df["label"],
            random_state=random_state,
        )

    # Split into train + temp (val + test)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        stratify=df["label"],
        random_state=random_state,
    )

    # Split temp into val and test
    relative_test_ratio = test_ratio / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_ratio,
        stratify=temp_df["label"],
        random_state=random_state,
    )

    # Verify zero text overlap between splits
    train_texts = set(train_df["combined_text"])
    val_texts = set(val_df["combined_text"])
    test_texts = set(test_df["combined_text"])

    assert len(train_texts.intersection(val_texts)) == 0, "Leakage detected between train and val!"
    assert len(train_texts.intersection(test_texts)) == 0, "Leakage detected between train and test!"
    assert len(val_texts.intersection(test_texts)) == 0, "Leakage detected between val and test!"

    logger.info(
        "Splits created successfully: Train=%d (Fake=%d, Real=%d), Val=%d (Fake=%d, Real=%d), Test=%d (Fake=%d, Real=%d)",
        len(train_df), (train_df['label'] == 1).sum(), (train_df['label'] == 0).sum(),
        len(val_df), (val_df['label'] == 1).sum(), (val_df['label'] == 0).sum(),
        len(test_df), (test_df['label'] == 1).sum(), (test_df['label'] == 0).sum(),
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def save_processed_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str | Path = "data/processed",
) -> Dict[str, str]:
    """Save processed splits to parquet files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "train": str(out / "train.parquet"),
        "val": str(out / "val.parquet"),
        "test": str(out / "test.parquet"),
    }

    train_df.to_parquet(paths["train"], index=False)
    val_df.to_parquet(paths["val"], index=False)
    test_df.to_parquet(paths["test"], index=False)

    logger.info("Saved processed splits to: %s", paths)
    return paths


def export_sample_articles(
    test_df: pd.DataFrame,
    output_path: str | Path = "data/samples/sample_articles.json",
    num_samples_per_class: int = 5,
) -> None:
    """Export clean sample articles for UI quick-testing and verification."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    samples = []
    for label in [0, 1]:
        subset = test_df[test_df["label"] == label].head(num_samples_per_class)
        for _, row in subset.iterrows():
            samples.append({
                "title": row["title"],
                "text": row["text"][:1200],  # truncated snippet
                "label": int(row["label"]),
                "ground_truth": LABEL_MAPPING[int(row["label"])],
                "char_length": len(row["combined_text"]),
            })

    import json
    with open(out, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
    logger.info("Saved %d sample articles to %s", len(samples), out)


if __name__ == "__main__":
    raw_df = load_raw_dataset()
    clean_df = clean_and_prepare(raw_df)
    train_df, val_df, test_df = create_stratified_splits(clean_df)
    save_processed_splits(train_df, val_df, test_df)
    export_sample_articles(test_df)

