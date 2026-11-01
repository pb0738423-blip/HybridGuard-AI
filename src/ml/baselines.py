"""Baseline models for Fake News Detection:
1. Logistic Regression
2. Linear Support Vector Machine (LinearSVC with Platt/Sigmoid Calibration)
3. Multinomial Naive Bayes
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

logger = logging.getLogger("hybridguard.baselines")


def build_logistic_regression(c: float = 1.0, max_iter: int = 1000, random_state: int = 42) -> LogisticRegression:
    """Build Logistic Regression classifier."""
    return LogisticRegression(
        C=c,
        max_iter=max_iter,
        solver="lbfgs",
        random_state=random_state,
        n_jobs=-1,
    )


def build_calibrated_linear_svm(c: float = 1.0, cv: int = 3, random_state: int = 42) -> CalibratedClassifierCV:
    """Build Linear SVM wrapped in CalibratedClassifierCV for probability estimation."""
    base_svm = LinearSVC(
        C=c,
        random_state=random_state,
        dual=False,
        max_iter=2000,
    )
    return CalibratedClassifierCV(
        estimator=base_svm,
        method="sigmoid",
        cv=cv,
        n_jobs=-1,
    )


def build_multinomial_nb(alpha: float = 0.5) -> MultinomialNB:
    """Build Multinomial Naive Bayes classifier."""
    return MultinomialNB(alpha=alpha)


class BaselineModelSuite:
    """Manages training, inference, and serialization of all 3 baseline classifiers."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, Any] = {
            "logistic_regression": build_logistic_regression(random_state=self.random_state),
            "linear_svm": build_calibrated_linear_svm(random_state=self.random_state),
            "multinomial_nb": build_multinomial_nb(),
        }
        self.is_fitted = False

    def fit(self, X_train: csr_matrix, y_train: np.ndarray) -> BaselineModelSuite:
        """Fit all 3 baseline models on the training feature matrix."""
        for name, model in self.models.items():
            logger.info("Training baseline model: %s...", name)
            model.fit(X_train, y_train)
            logger.info("Trained %s successfully.", name)
        self.is_fitted = True
        return self

    def predict_proba(self, X: csr_matrix) -> Dict[str, np.ndarray]:
        """Return class probability distributions [P(Real), P(Fake)] for each baseline."""
        if not self.is_fitted:
            raise RuntimeError("Baseline models are not fitted!")
        results = {}
        for name, model in self.models.items():
            results[name] = model.predict_proba(X)
        return results

    def predict(self, X: csr_matrix) -> Dict[str, np.ndarray]:
        """Return binary predictions (0=Real, 1=Fake) for each baseline."""
        if not self.is_fitted:
            raise RuntimeError("Baseline models are not fitted!")
        results = {}
        for name, model in self.models.items():
            results[name] = model.predict(X)
        return results

    def save(self, output_dir: str | Path = "models/artifacts") -> None:
        """Serialize baseline models to disk."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            model_path = out / f"{name}.joblib"
            joblib.dump(model, model_path)
            logger.info("Saved %s to %s", name, model_path)

    @classmethod
    def load(cls, artifacts_dir: str | Path = "models/artifacts") -> BaselineModelSuite:
        """Load fitted baseline models from disk."""
        suite = cls()
        art_dir = Path(artifacts_dir)
        for name in list(suite.models.keys()):
            model_path = art_dir / f"{name}.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"Artifact {model_path} not found")
            suite.models[name] = joblib.load(model_path)
            logger.info("Loaded baseline model: %s from %s", name, model_path)
        suite.is_fitted = True
        return suite

