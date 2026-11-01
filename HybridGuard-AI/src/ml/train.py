"""End-to-end training and evaluation pipeline for HybridGuard AI.
Executes data preparation, feature extraction, baseline model training,
out-of-fold stacking, probability calibration, evaluation on held-out test split,
and artifact serialization.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml.baselines import BaselineModelSuite
from src.ml.dataset import (
    clean_and_prepare,
    create_stratified_splits,
    export_sample_articles,
    load_raw_dataset,
    save_processed_splits,
    LABEL_MAPPING,
)
from src.ml.evaluate import evaluate_single_model, save_evaluation_reports
from src.ml.explainability import ModelExplainer
from src.ml.hybrid import HybridStackingClassifier
from src.ml.preprocessor import TextFeaturePipeline

logger = logging.getLogger("hybridguard.train")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_training_pipeline(
    raw_path: str = "data/raw/welfake.parquet",
    subsample_max: int | None = 25000,
    max_features: int = 25000,
    cv_folds: int = 5,
    random_state: int = 42,
    artifacts_dir: str = "models/artifacts",
    evaluation_dir: str = "models/evaluation",
) -> None:
    """Execute complete training and evaluation."""
    art_path = Path(artifacts_dir)
    eval_path = Path(evaluation_dir)
    art_path.mkdir(parents=True, exist_ok=True)
    eval_path.mkdir(parents=True, exist_ok=True)

    # 1. Ingest & Prepare Dataset
    logger.info("=== STEP 1: Ingesting & Preparing Dataset ===")
    raw_df = load_raw_dataset(raw_path)
    clean_df = clean_and_prepare(raw_df)

    # 2. Stratified Splits (Train 70%, Val 15%, Test 15%)
    logger.info("=== STEP 2: Creating Stratified Splits ===")
    train_df, val_df, test_df = create_stratified_splits(
        clean_df,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=random_state,
        subsample_max=subsample_max,
    )
    save_processed_splits(train_df, val_df, test_df)
    export_sample_articles(test_df)

    # 3. Fit Preprocessing & TF-IDF Vectorizer on Train Split ONLY
    logger.info("=== STEP 3: Fitting TF-IDF Feature Extractor ===")
    feature_pipeline = TextFeaturePipeline(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
    )
    X_train = feature_pipeline.fit_transform(train_df["combined_text"].values)
    y_train = train_df["label"].values

    # Transform Validation and Test splits
    X_val = feature_pipeline.transform(val_df["combined_text"].values)
    y_val = val_df["label"].values

    X_test = feature_pipeline.transform(test_df["combined_text"].values)
    y_test = test_df["label"].values

    feature_pipeline.save(art_path / "vectorizer.joblib")

    # 4. Train Baseline Classifiers
    logger.info("=== STEP 4: Training Baseline Models ===")
    baseline_suite = BaselineModelSuite(random_state=random_state)
    baseline_suite.fit(X_train, y_train)
    baseline_suite.save(art_path)

    # 5. Train Hybrid Stacking Classifier (Out-of-Fold)
    logger.info("=== STEP 5: Training Hybrid Stacking Classifier ===")
    hybrid_model = HybridStackingClassifier(
        cv_folds=cv_folds,
        uncertainty_threshold=0.65,
        uncertainty_margin=0.15,
        random_state=random_state,
    )
    hybrid_model.fit(X_train, y_train)
    hybrid_model.save(art_path / "hybrid_model.joblib")

    # 6. Evaluate All Models on Held-out Test Split
    logger.info("=== STEP 6: Evaluating Models on Held-out Test Split ===")
    evaluation_reports = {}

    # Evaluate individual baselines
    for model_name, model in baseline_suite.models.items():
        report = evaluate_single_model(
            model_name=model_name,
            model=model,
            X_test=X_test,
            y_test=y_test,
            test_df=test_df,
        )
        evaluation_reports[model_name] = report

    # Evaluate hybrid stacking ensemble
    hybrid_report = evaluate_single_model(
        model_name="hybrid_stacking",
        model=hybrid_model,
        X_test=X_test,
        y_test=y_test,
        test_df=test_df,
    )
    evaluation_reports["hybrid_stacking"] = hybrid_report

    # Save comprehensive evaluation reports
    save_evaluation_reports(evaluation_reports, eval_path)

    # 7. Save Model Metadata & Configuration
    metadata = {
        "dataset_name": "WELFake",
        "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
        "sample_counts": {
            "total_cleaned": int(len(clean_df)),
            "train": int(len(train_df)),
            "val": int(len(val_df)),
            "test": int(len(test_df)),
        },
        "feature_extraction": {
            "type": "TF-IDF (unigram + bigram)",
            "vocabulary_size": int(len(feature_pipeline.get_feature_names())),
            "max_features": max_features,
            "min_df": 3,
            "sublinear_tf": True,
        },
        "label_mapping": LABEL_MAPPING,
        "models": {
            "baseline_models": list(baseline_suite.models.keys()),
            "hybrid_model": "HybridStackingClassifier",
            "meta_weights": {k: float(w) for k, w in zip(baseline_suite.models.keys(), hybrid_model.meta_weights_)},
        },
        "uncertainty_config": {
            "uncertainty_threshold": hybrid_model.uncertainty_threshold,
            "uncertainty_margin": hybrid_model.uncertainty_margin,
        },
        "best_model_by_f1": max(
            evaluation_reports.items(),
            key=lambda item: item[1]["metrics"]["f1"]
        )[0],
    }

    metadata_path = art_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Saved model metadata to: %s", metadata_path)

    logger.info("=== Pipeline Execution Complete! ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train HybridGuard AI models")
    parser.add_argument("--subsample", type=int, default=25000, help="Max total samples to use (default: 25000 for balanced speed & accuracy)")
    parser.add_argument("--cv", type=int, default=5, help="OOF CV folds (default: 5)")
    parser.add_argument("--eval-only", action="store_true", help="Only run evaluation using saved artifacts and test split")
    args = parser.parse_args()

    if args.eval_only:
        logger.info("Running evaluation on existing test split with saved artifacts...")
        test_df = pd.read_parquet("data/processed/test.parquet")
        clean_df = pd.read_parquet("data/processed/train.parquet")
        feature_pipeline = TextFeaturePipeline.load("models/artifacts/vectorizer.joblib")
        X_test = feature_pipeline.transform(test_df["combined_text"].values)
        y_test = test_df["label"].values

        baseline_suite = BaselineModelSuite.load("models/artifacts")
        hybrid_model = HybridStackingClassifier.load("models/artifacts/hybrid_model.joblib")

        eval_path = Path("models/evaluation")
        art_path = Path("models/artifacts")
        evaluation_reports = {}

        for model_name, model in baseline_suite.models.items():
            report = evaluate_single_model(
                model_name=model_name,
                model=model,
                X_test=X_test,
                y_test=y_test,
                test_df=test_df,
            )
            evaluation_reports[model_name] = report

        hybrid_report = evaluate_single_model(
            model_name="hybrid_stacking",
            model=hybrid_model,
            X_test=X_test,
            y_test=y_test,
            test_df=test_df,
        )
        evaluation_reports["hybrid_stacking"] = hybrid_report

        save_evaluation_reports(evaluation_reports, eval_path)

        metadata = {
            "dataset_name": "WELFake",
            "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
            "sample_counts": {
                "total_cleaned": int(len(clean_df) + len(test_df)),
                "test": int(len(test_df)),
            },
            "feature_extraction": {
                "type": "TF-IDF (unigram + bigram)",
                "vocabulary_size": int(len(feature_pipeline.get_feature_names())),
                "max_features": 25000,
                "min_df": 3,
                "sublinear_tf": True,
            },
            "label_mapping": LABEL_MAPPING,
            "models": {
                "baseline_models": list(baseline_suite.models.keys()),
                "hybrid_model": "HybridStackingClassifier",
                "meta_weights": {k: float(w) for k, w in zip(baseline_suite.models.keys(), hybrid_model.meta_weights_)},
            },
            "uncertainty_config": {
                "uncertainty_threshold": hybrid_model.uncertainty_threshold,
                "uncertainty_margin": hybrid_model.uncertainty_margin,
            },
            "best_model_by_f1": max(
                evaluation_reports.items(),
                key=lambda item: item[1]["metrics"]["f1"]
            )[0],
        }

        with open(art_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info("Saved metadata and evaluation report successfully!")
    else:
        run_training_pipeline(subsample_max=args.subsample, cv_folds=args.cv)
