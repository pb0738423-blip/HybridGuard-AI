# HybridGuard AI — Experiment Log

This document records the exact experiments, hyperparameter configurations, validation results, and test metrics obtained during model training and evaluation.

## Log Format
- **Experiment ID**: EXP-{Number}
- **Date / Timestamp**: UTC / Local
- **Dataset Split**: Training (70%), Validation (15%), Test (15%)
- **Feature Extraction**: TF-IDF Unigrams + Bigrams (`max_features=25000`)
- **Evaluated Models**: Logistic Regression, Linear SVM (Calibrated), Multinomial Naive Bayes, Stacking Ensemble

---

## Log Entries

### EXP-001: Initial Setup & Environment Verification
- **Status**: Completed
- **Notes**: Verified Python 3.11, scikit-learn 1.9.1, pandas 3.1.0, pyarrow 26.0.0. Raw dataset source identified (`davanstrien/WELFake`).

### EXP-002: Baseline & Hybrid Model Training on WELFake Benchmark
- **Date**: 2026-10-29
- **Dataset**: WELFake (25,000 stratified samples, 17,500 train, 3,750 validation, 3,750 test)
- **Features**: TF-IDF Unigrams + Bigrams, `max_features=25000`, `min_df=3`, `sublinear_tf=True`
- **CV Strategy**: 5-Fold Stratified Out-of-Fold (OOF) cross-validation for stacking meta-model

#### Empirical Evaluation Results on Untouched Test Split (N=3,750)
| Model | Accuracy | Precision | Recall | F1-Score | Macro F1 | ROC-AUC | Brier Score | Log Loss | ECE | Latency (mean) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Linear SVM (Calibrated)** | **96.96%** | **96.87%** | **96.41%** | **0.9664** | **0.9693** | **0.9958** | **0.0230** | **0.0818** | **0.0082** | 14.68 ms |
| **Hybrid Stacking Classifier** | 96.91% | 96.86% | 96.29% | 0.9658 | 0.9688 | 0.9953 | 0.0241 | 0.0906 | 0.0083 | 20.39 ms |
| **Logistic Regression** | 95.84% | 95.79% | 95.00% | 0.9539 | 0.9580 | 0.9926 | 0.0421 | 0.1730 | 0.0870 | **1.46 ms** |
| **Multinomial Naive Bayes** | 87.68% | 84.61% | 88.99% | 0.8675 | 0.8762 | 0.9491 | 0.0894 | 0.3090 | 0.0402 | 2.65 ms |

#### Key Empirical Insights
1. **Calibration**: Calibrated Linear SVM and the Hybrid Stacking ensemble both demonstrate superior probability calibration with an Expected Calibration Error (ECE) under 0.009 (0.83%), compared to uncalibrated Logistic Regression (ECE = 8.70%).
2. **Ensemble vs. Single Model**: The stacking ensemble achieved virtually identical performance to the strongest single baseline (Linear SVM, 96.96% vs 96.91%), while offering consensus verification across 3 distinct paradigms (linear margin, probabilistic generative, and logistic sigmoid).
3. **Inference Latency**: Logistic Regression offers the fastest single-item inference (1.46 ms), while the full stacking pipeline takes ~20 ms on CPU, well within real-time thresholds.
4. **Learned Meta-Model Weights**: `[Linear SVM: 6.996, Logistic Regression: 3.349, Multinomial NB: -0.859]`. The stacking meta-learner placed heaviest confidence on the calibrated margin classifier.
