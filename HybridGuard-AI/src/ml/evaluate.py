"""Comprehensive Evaluation Engine for HybridGuard AI.
Calculates Accuracy, Precision, Recall, F1, Macro-F1, ROC-AUC, PR-AUC,
Brier score, Log Loss, Expected Calibration Error (ECE), Latency benchmarks,
Confusion Matrices, and Error Analysis (FP/FN examples).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger("hybridguard.evaluate")


def compute_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> Tuple[float, List[Dict[str, Any]]]:
    """Calculate Expected Calibration Error (ECE) and reliability curve bins.
    
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    ece = 0.0
    n_total = len(y_true)
    calibration_curve_data = []

    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        if i == n_bins - 1:
            mask = (y_prob >= low) & (y_prob <= high)
        else:
            mask = (y_prob >= low) & (y_prob < high)

        bin_count = int(np.sum(mask))
        if bin_count > 0:
            bin_preds = (y_prob[mask] >= 0.5).astype(int)
            # Binary accuracy in this probability slice
            bin_acc = float(np.mean(y_true[mask] == bin_preds))
            # Average confidence
            bin_conf = float(np.mean(np.maximum(y_prob[mask], 1.0 - y_prob[mask])))
            bin_weight = bin_count / n_total
            ece += bin_weight * abs(bin_acc - bin_conf)

            calibration_curve_data.append({
                "bin_index": i,
                "bin_range": f"{low:.1f}-{high:.1f}",
                "bin_center": round(float(bin_centers[i]), 3),
                "count": bin_count,
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
                "gap": round(abs(bin_acc - bin_conf), 4),
            })
        else:
            calibration_curve_data.append({
                "bin_index": i,
                "bin_range": f"{low:.1f}-{high:.1f}",
                "bin_center": round(float(bin_centers[i]), 3),
                "count": 0,
                "accuracy": 0.0,
                "confidence": round(float(bin_centers[i]), 3),
                "gap": 0.0,
            })

    return round(float(ece), 4), calibration_curve_data


def benchmark_inference_latency(
    model: Any,
    X_sample: csr_matrix,
    n_runs: int = 200,
) -> Dict[str, float]:
    """Measure single-item inference latency in milliseconds (mean, median, p95)."""
    latencies = []
    # Warm-up
    _ = model.predict_proba(X_sample[:1])

    sample_size = min(X_sample.shape[0], n_runs)
    for i in range(sample_size):
        single_x = X_sample[i : i + 1]
        t0 = time.perf_counter()
        _ = model.predict_proba(single_x)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    return {
        "mean_ms": round(float(np.mean(latencies)), 3),
        "median_ms": round(float(np.median(latencies)), 3),
        "p95_ms": round(float(np.percentile(latencies, 95)), 3),
    }


def sample_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, max_points: int = 35) -> List[Dict[str, float]]:
    """Downsample ROC curve coordinates for frontend Recharts visualization."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    indices = np.linspace(0, len(fpr) - 1, max_points).astype(int)
    points = []
    for idx in indices:
        points.append({
            "fpr": round(float(fpr[idx]), 4),
            "tpr": round(float(tpr[idx]), 4),
        })
    # Ensure (0,0) and (1,1) boundaries
    if points[0]["fpr"] != 0.0:
        points.insert(0, {"fpr": 0.0, "tpr": 0.0})
    if points[-1]["fpr"] != 1.0:
        points.append({"fpr": 1.0, "tpr": 1.0})
    return points


def sample_pr_curve(y_true: np.ndarray, y_prob: np.ndarray, max_points: int = 35) -> List[Dict[str, float]]:
    """Downsample Precision-Recall curve coordinates for frontend visualization."""
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    indices = np.linspace(0, len(precision) - 1, max_points).astype(int)
    points = []
    for idx in indices:
        points.append({
            "recall": round(float(recall[idx]), 4),
            "precision": round(float(precision[idx]), 4),
        })
    return points


def extract_error_examples(
    test_df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    max_examples: int = 4,
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract concrete False Positive and False Negative cases from test set."""
    false_positives = []
    false_negatives = []

    for i in range(len(y_true)):
        true_val = y_true[i]
        pred_val = y_pred[i]
        prob_fake = float(y_prob[i])

        row = test_df.iloc[i]
        title = str(row.get("title", ""))
        text_snippet = str(row.get("text", ""))[:400]

        item = {
            "index": int(i),
            "title": title if title else "No Headline Provided",
            "snippet": text_snippet + "...",
            "true_label": "Real" if true_val == 0 else "Fake",
            "pred_label": "Fake" if pred_val == 1 else "Real",
            "p_fake": round(prob_fake, 4),
            "p_real": round(1.0 - prob_fake, 4),
        }

        if true_val == 0 and pred_val == 1 and len(false_positives) < max_examples:
            false_positives.append(item)
        elif true_val == 1 and pred_val == 0 and len(false_negatives) < max_examples:
            false_negatives.append(item)

        if len(false_positives) >= max_examples and len(false_negatives) >= max_examples:
            break

    return {
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def evaluate_single_model(
    model_name: str,
    model: Any,
    X_test: csr_matrix,
    y_test: np.ndarray,
    test_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Execute complete rigorous evaluation on a model using test data."""
    logger.info("Evaluating model: %s on %d test samples...", model_name, len(y_test))

    # Inference probabilities
    probas = model.predict_proba(X_test)
    y_prob_fake = probas[:, 1]
    y_pred = (y_prob_fake >= 0.5).astype(int)

    # Core classification metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="binary", zero_division=0)
    rec = recall_score(y_test, y_pred, average="binary", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="binary", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    # Area metrics
    roc_auc = roc_auc_score(y_test, y_prob_fake)

    # Calibration & probability metrics
    brier = brier_score_loss(y_test, y_prob_fake)
    ce_loss = log_loss(y_test, probas)
    ece, cal_curve = compute_expected_calibration_error(y_test, y_prob_fake)

    # Confusion matrix: [[TN, FP], [FN, TP]]
    cm = confusion_matrix(y_test, y_pred)
    cm_dict = {
        "true_negatives": int(cm[0, 0]),
        "false_positives": int(cm[0, 1]),
        "false_negatives": int(cm[1, 0]),
        "true_positives": int(cm[1, 1]),
    }

    # Latency
    latency = benchmark_inference_latency(model, X_test)

    # Curves for UI
    roc_curve_data = sample_roc_curve(y_test, y_prob_fake)
    pr_curve_data = sample_pr_curve(y_test, y_prob_fake)

    # Error examples
    errors = extract_error_examples(test_df, y_test, y_pred, y_prob_fake)

    report = {
        "model_name": model_name,
        "test_sample_count": int(len(y_test)),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "macro_f1": round(float(macro_f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "brier_score": round(float(brier), 4),
            "log_loss": round(float(ce_loss), 4),
            "ece": round(float(ece), 4),
        },
        "latency": latency,
        "confusion_matrix": cm_dict,
        "calibration_curve": cal_curve,
        "roc_curve": roc_curve_data,
        "pr_curve": pr_curve_data,
        "error_analysis": errors,
    }

    logger.info(
        "Results for %s -> Acc: %.4f | F1: %.4f | Macro-F1: %.4f | ROC-AUC: %.4f | ECE: %.4f",
        model_name, acc, f1, macro_f1, roc_auc, ece
    )
    return report


def save_evaluation_reports(
    reports: Dict[str, Dict[str, Any]],
    output_dir: str | Path = "models/evaluation",
) -> None:
    """Save evaluation reports as JSON and CSV."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Save detailed JSON report
    json_path = out / "evaluation_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)

    # Build comparison CSV table
    comparison_rows = []
    for name, rep in reports.items():
        row = {"model": name}
        row.update(rep["metrics"])
        row.update({f"latency_{k}": v for k, v in rep["latency"].items()})
        row.update(rep["confusion_matrix"])
        comparison_rows.append(row)

    df_comp = pd.DataFrame(comparison_rows)
    csv_path = out / "model_comparison.csv"
    df_comp.to_csv(csv_path, index=False)

    logger.info("Saved evaluation JSON to: %s", json_path)
    logger.info("Saved comparison CSV to: %s", csv_path)
