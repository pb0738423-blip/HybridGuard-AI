"""Hybrid Stacking Classifier with Out-of-Fold Cross-Validation, Probability Calibration,
and Uncertainty Quantification with "Needs Review" determination.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

logger = logging.getLogger("hybridguard.hybrid")


class HybridStackingClassifier(BaseEstimator, ClassifierMixin):
    """Stacking classifier that uses out-of-fold cross-validation to train the meta-model,
    strictly preventing in-sample overfitting.
    
    Includes calibrated probability outputs and uncertainty quantification.
    """

    def __init__(
        self,
        cv_folds: int = 5,
        uncertainty_threshold: float = 0.65,
        uncertainty_margin: float = 0.15,
        random_state: int = 42,
    ):
        self.cv_folds = cv_folds
        self.uncertainty_threshold = uncertainty_threshold
        self.uncertainty_margin = uncertainty_margin
        self.random_state = random_state

        # Base estimators
        self.base_estimators = {
            "logistic_regression": LogisticRegression(C=1.0, max_iter=1000, random_state=random_state),
            "linear_svm": CalibratedClassifierCV(
                estimator=LinearSVC(C=1.0, random_state=random_state, dual=False, max_iter=2000),
                method="sigmoid",
                cv=3,
            ),
            "multinomial_nb": MultinomialNB(alpha=0.5),
        }

        # Meta estimator
        self.meta_estimator = LogisticRegression(C=0.5, random_state=random_state)

        # Fitted base models for production inference
        self.fitted_base_models: Dict[str, Any] = {}
        self.is_fitted = False
        self.meta_weights_: Optional[np.ndarray] = None

    def fit(self, X: csr_matrix, y: np.ndarray) -> HybridStackingClassifier:
        """Fit stacking ensemble using strict Out-Of-Fold (OOF) cross-validation."""
        logger.info("Training Hybrid Stacking Classifier with %d-fold OOF cross-validation...", self.cv_folds)
        n_samples = X.shape[0]
        n_estimators = len(self.base_estimators)
        estimator_keys = list(self.base_estimators.keys())

        # Array to hold out-of-fold probability predictions: shape (n_samples, n_estimators)
        # Each column stores P(Fake) [class 1] predicted out-of-fold
        oof_predictions = np.zeros((n_samples, n_estimators), dtype=np.float64)

        skf = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            logger.info("Processing CV fold %d/%d for meta-learner training...", fold_idx + 1, self.cv_folds)
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train = y[train_idx]

            for model_idx, (name, base_est) in enumerate(self.base_estimators.items()):
                fold_model = clone(base_est)
                fold_model.fit(X_fold_train, y_fold_train)
                # Store probability of Fake (class 1)
                proba_val = fold_model.predict_proba(X_fold_val)[:, 1]
                oof_predictions[val_idx, model_idx] = proba_val

        # Train meta-estimator strictly on out-of-fold predictions
        logger.info("Fitting meta-estimator on OOF prediction matrix of shape %s...", oof_predictions.shape)
        self.meta_estimator.fit(oof_predictions, y)
        self.meta_weights_ = self.meta_estimator.coef_[0]
        logger.info("Learned meta-model component weights: %s -> %s", estimator_keys, self.meta_weights_)

        # Now fit base models on FULL training data for test-time inference
        logger.info("Refitting base models on full training data...")
        self.fitted_base_models = {}
        for name, base_est in self.base_estimators.items():
            full_model = clone(base_est)
            full_model.fit(X, y)
            self.fitted_base_models[name] = full_model

        self.is_fitted = True
        return self

    def _get_base_probabilities(self, X: csr_matrix) -> np.ndarray:
        """Collect P(Fake) from all base models: shape (n_samples, n_estimators)."""
        estimator_keys = list(self.base_estimators.keys())
        base_probas = []
        for name in estimator_keys:
            model = self.fitted_base_models[name]
            p_fake = model.predict_proba(X)[:, 1]
            base_probas.append(p_fake)
        return np.column_stack(base_probas)

    def predict_proba(self, X: csr_matrix) -> np.ndarray:
        """Predict calibrated class probabilities [P(Real), P(Fake)] using stacking meta-model."""
        if not self.is_fitted:
            raise RuntimeError("HybridStackingClassifier is not fitted!")
        meta_features = self._get_base_probabilities(X)
        return self.meta_estimator.predict_proba(meta_features)

    def predict(self, X: csr_matrix) -> np.ndarray:
        """Predict binary class (0=Real, 1=Fake)."""
        probas = self.predict_proba(X)
        return np.argmax(probas, axis=1)

    def predict_with_uncertainty(self, X: csr_matrix) -> List[Dict[str, Any]]:
        """Perform inference with detailed uncertainty, individual model breakdowns,
        and 'Needs Review' flagging.
        """
        if not self.is_fitted:
            raise RuntimeError("HybridStackingClassifier is not fitted!")

        meta_features = self._get_base_probabilities(X)
        hybrid_probas = self.meta_estimator.predict_proba(meta_features)
        estimator_keys = list(self.base_estimators.keys())

        results = []
        for i in range(X.shape[0]):
            p_real = float(hybrid_probas[i, 0])
            p_fake = float(hybrid_probas[i, 1])
            pred_class = int(p_fake >= 0.5)
            confidence = max(p_real, p_fake)

            # Normalized margin distance from decision boundary (0.50)
            margin_dist = abs(p_fake - 0.50)

            # Shannon entropy uncertainty: - sum(p * log2(p))
            # Normalized to [0.0, 1.0] where 1.0 is maximum uncertainty (50/50)
            eps = 1e-12
            entropy = -(p_real * np.log2(p_real + eps) + p_fake * np.log2(p_fake + eps))
            uncertainty_score = float(np.clip(entropy, 0.0, 1.0))

            # Needs Review trigger: confidence below threshold or within margin
            needs_review = bool(
                confidence < self.uncertainty_threshold or margin_dist < self.uncertainty_margin
            )

            # Individual model outputs
            individual_models = {}
            agree_count = 0
            for col_idx, name in enumerate(estimator_keys):
                base_p_fake = float(meta_features[i, col_idx])
                base_p_real = 1.0 - base_p_fake
                base_pred = int(base_p_fake >= 0.5)
                if base_pred == pred_class:
                    agree_count += 1
                individual_models[name] = {
                    "p_real": round(base_p_real, 4),
                    "p_fake": round(base_p_fake, 4),
                    "prediction": "Fake" if base_pred == 1 else "Real",
                    "confidence": round(max(base_p_real, base_p_fake), 4),
                }

            agreement_ratio = round(agree_count / len(estimator_keys), 2)

            results.append({
                "prediction": "Fake" if pred_class == 1 else "Real",
                "label": pred_class,
                "confidence": round(confidence, 4),
                "p_real": round(p_real, 4),
                "p_fake": round(p_fake, 4),
                "uncertainty_score": round(uncertainty_score, 4),
                "needs_review": needs_review,
                "agreement_ratio": agreement_ratio,
                "individual_models": individual_models,
                "meta_weights": {k: round(float(w), 4) for k, w in zip(estimator_keys, self.meta_weights_)}
                if self.meta_weights_ is not None else {},
            })

        return results

    def save(self, filepath: str | Path = "models/artifacts/hybrid_model.joblib") -> None:
        """Serialize trained hybrid model to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Serialized HybridStackingClassifier to %s", path)

    @classmethod
    def load(cls, filepath: str | Path = "models/artifacts/hybrid_model.joblib") -> HybridStackingClassifier:
        """Load trained hybrid model from disk."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found at {path}")
        model = joblib.load(path)
        logger.info("Loaded HybridStackingClassifier from %s (fitted=%s)", path, model.is_fitted)
        return model

