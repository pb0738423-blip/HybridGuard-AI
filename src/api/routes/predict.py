"""Prediction and Model Evaluation API routes for HybridGuard AI.
Loads saved artifacts into memory at startup without retraining per request.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
import numpy as np

from src.api.schemas import (
    BatchPredictRequest,
    ModelContribution,
    PredictRequest,
    PredictResponse,
    WordAttribution,
)
from src.ml.baselines import BaselineModelSuite
from src.ml.explainability import EXPLANATION_SCOPE_DISCLAIMER, ModelExplainer
from src.ml.hybrid import HybridStackingClassifier
from src.ml.preprocessor import TextFeaturePipeline

logger = logging.getLogger("hybridguard.api_predict")
router = APIRouter(prefix="/api", tags=["Machine Learning Prediction"])

# Global artifact cache
_VECTORIZER: Optional[TextFeaturePipeline] = None
_HYBRID_MODEL: Optional[HybridStackingClassifier] = None
_BASELINES: Optional[BaselineModelSuite] = None
_EXPLAINER: Optional[ModelExplainer] = None
_METADATA: Optional[Dict[str, Any]] = None
_METRICS: Optional[Dict[str, Any]] = None


def get_artifacts():
    """Lazy-load and cache serialized models and vectorizer."""
    global _VECTORIZER, _HYBRID_MODEL, _BASELINES, _EXPLAINER, _METADATA, _METRICS

    if _HYBRID_MODEL is not None and _VECTORIZER is not None:
        return _VECTORIZER, _HYBRID_MODEL, _EXPLAINER

    artifacts_dir = Path("models/artifacts")
    eval_dir = Path("models/evaluation")

    if not (artifacts_dir / "hybrid_model.joblib").exists() or not (artifacts_dir / "vectorizer.joblib").exists():
        raise HTTPException(
            status_code=503,
            detail="Model artifacts not yet trained or loaded. Please verify models/artifacts exists."
        )

    try:
        logger.info("Loading model artifacts from %s...", artifacts_dir)
        _VECTORIZER = TextFeaturePipeline.load(artifacts_dir / "vectorizer.joblib")
        _HYBRID_MODEL = HybridStackingClassifier.load(artifacts_dir / "hybrid_model.joblib")
        
        # Load baselines if present
        try:
            _BASELINES = BaselineModelSuite.load(artifacts_dir)
        except Exception as e:
            logger.warning("Could not load separate baseline suite: %s", e)

        # Initialize explainer
        feature_names = _VECTORIZER.get_feature_names()
        lr_model = _HYBRID_MODEL.fitted_base_models.get("logistic_regression")
        svm_model = _HYBRID_MODEL.fitted_base_models.get("linear_svm")
        
        meta_weights = None
        if _HYBRID_MODEL.meta_weights_ is not None:
            keys = list(_HYBRID_MODEL.base_estimators.keys())
            meta_weights = {k: float(w) for k, w in zip(keys, _HYBRID_MODEL.meta_weights_)}

        _EXPLAINER = ModelExplainer(
            feature_names=feature_names,
            lr_model=lr_model,
            svm_model=svm_model,
            meta_weights=meta_weights,
            selected_model=(_METADATA or {}).get("best_model_by_f1", "hybrid_stacking"),
        )

        # Load metadata
        meta_path = artifacts_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                _METADATA = json.load(f)

        # Load metrics
        eval_path = eval_dir / "evaluation_report.json"
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                _METRICS = json.load(f)

        logger.info("All artifacts loaded successfully into memory.")
        return _VECTORIZER, _HYBRID_MODEL, _EXPLAINER

    except Exception as e:
        logger.error("Failed loading artifacts: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed loading model artifacts: {str(e)}")


@router.get("/model-info")
def get_model_info() -> Dict[str, Any]:
    """Retrieve model metadata, architecture details, and training configuration."""
    get_artifacts()
    meta_path = Path("models/artifacts/metadata.json")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "Model loaded, metadata file not found"}


@router.get("/metrics")
def get_model_metrics() -> Dict[str, Any]:
    """Retrieve actual evaluation metrics, ROC/PR curves, and confusion matrices."""
    get_artifacts()
    eval_path = Path("models/evaluation/evaluation_report.json")
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Evaluation metrics report not found.")


def _predict_using_selected_model(X_sparse, text: str) -> Dict[str, Any]:
    """Use the best held-out model recorded in metadata, and flag headline-only inputs.

    The WELFake model was trained on title + article body. A short headline is
    therefore out-of-distribution and must not be presented as a definitive verdict.
    """
    vectorizer, hybrid_model, _ = get_artifacts()
    selected_name = (_METADATA or {}).get("best_model_by_f1", "linear_svm")
    if _BASELINES is not None and selected_name in _BASELINES.models:
        model = _BASELINES.models[selected_name]
        probabilities = model.predict_proba(X_sparse)[0]
        p_real, p_fake = float(probabilities[0]), float(probabilities[1])
        individual = {}
        votes = []
        for name, base_model in _BASELINES.models.items():
            probs = base_model.predict_proba(X_sparse)[0]
            pred = "Fake" if int(np.argmax(probs)) == 1 else "Real"
            votes.append(pred)
            individual[name] = {
                "p_real": round(float(probs[0]), 4),
                "p_fake": round(float(probs[1]), 4),
                "prediction": pred,
                "confidence": round(float(np.max(probs)), 4),
            }
        prediction = "Fake" if p_fake >= 0.5 else "Real"
        confidence = max(p_real, p_fake)
        agreement_ratio = sum(v == prediction for v in votes) / max(1, len(votes))
        meta_weights = {}
    else:
        # Backward-compatible fallback if baseline artifacts are unavailable.
        raw = hybrid_model.predict_with_uncertainty(X_sparse)[0]
        p_real, p_fake = raw["p_real"], raw["p_fake"]
        prediction, confidence = raw["prediction"], raw["confidence"]
        agreement_ratio, individual, meta_weights = (
            raw["agreement_ratio"], raw["individual_models"], raw["meta_weights"]
        )

    # Entropy is an uncertainty indicator, not a factuality score.
    eps = 1e-12
    entropy = -(p_real * np.log2(p_real + eps) + p_fake * np.log2(p_fake + eps))
    word_count = len(text.split())
    headline_only = word_count < 80
    needs_review = bool(
        headline_only or confidence < 0.65 or abs(p_fake - 0.5) < 0.15
        or agreement_ratio < 1.0
    )
    warning = (
        "Headline/short-text input: this model was trained on full news articles "
        "(headline plus article body). Treat the ML result as a weak stylistic signal, "
        "not a fact-check. Paste the full article and verify its claims against reliable sources."
        if headline_only else
        "ML classification is not proof of factual accuracy. Verify important claims using independent sources."
    )
    return {
        "prediction": prediction,
        "label": 1 if prediction == "Fake" else 0,
        "confidence": round(confidence, 4),
        "p_real": round(p_real, 4),
        "p_fake": round(p_fake, 4),
        "uncertainty_score": round(float(np.clip(entropy, 0.0, 1.0)), 4),
        "needs_review": needs_review,
        "agreement_ratio": round(float(agreement_ratio), 2),
        "individual_models": individual,
        "meta_weights": meta_weights,
        "selected_model": selected_name,
        "input_word_count": word_count,
        "input_warning": warning,
    }


@router.post("/predict", response_model=PredictResponse)
def predict_single(req: PredictRequest) -> PredictResponse:
    """Analyze a single news article with the hybrid stacking classifier,
    calibrated probabilities, uncertainty estimation, and influential word attributions.
    """
    vectorizer, hybrid_model, explainer = get_artifacts()

    # Transform text to sparse TF-IDF matrix
    X_sparse = vectorizer.transform([req.text])

    # Select the best model on the held-out evaluation report. Short headline-only
    # inputs are explicitly marked for review because training used full articles.
    res = _predict_using_selected_model(X_sparse, req.text)

    top_fake_words = []
    top_real_words = []
    if req.explain and explainer is not None:
        explanation = explainer.explain_instance(X_sparse, top_n=req.top_n_words)
        top_fake_words = [WordAttribution(**w) for w in explanation["top_fake_words"]]
        top_real_words = [
            WordAttribution(
                word=w["word"],
                attribution=w["attribution"],
                tfidf_weight=w["tfidf_weight"],
                influence=w["influence"],
            )
            for w in explanation["top_real_words"]
        ]

    individual_models = {
        name: ModelContribution(**details)
        for name, details in res["individual_models"].items()
    }

    return PredictResponse(
        prediction=res["prediction"],
        label=res["label"],
        confidence=res["confidence"],
        p_real=res["p_real"],
        p_fake=res["p_fake"],
        uncertainty_score=res["uncertainty_score"],
        needs_review=res["needs_review"],
        agreement_ratio=res["agreement_ratio"],
        individual_models=individual_models,
        meta_weights=res["meta_weights"],
        top_fake_words=top_fake_words,
        top_real_words=top_real_words,
        explanation_scope=EXPLANATION_SCOPE_DISCLAIMER,
        selected_model=res["selected_model"],
        input_word_count=res["input_word_count"],
        input_warning=res["input_warning"],
    )


@router.post("/batch-predict")
def predict_batch(req: BatchPredictRequest) -> Dict[str, Any]:
    """Perform batch classification over multiple articles."""
    vectorizer, hybrid_model, explainer = get_artifacts()

    X_sparse = vectorizer.transform(req.texts)

    response_items = []
    for i, text in enumerate(req.texts):
        res = _predict_using_selected_model(X_sparse[i : i + 1], text)
        item = {
            "index": i,
            "prediction": res["prediction"],
            "label": res["label"],
            "confidence": res["confidence"],
            "p_real": res["p_real"],
            "p_fake": res["p_fake"],
            "uncertainty_score": res["uncertainty_score"],
            "needs_review": res["needs_review"],
            "agreement_ratio": res["agreement_ratio"],
            "individual_models": res["individual_models"],
            "selected_model": res["selected_model"],
            "input_word_count": res["input_word_count"],
            "input_warning": res["input_warning"],
        }
        if req.explain and explainer is not None:
            single_x = X_sparse[i : i + 1]
            exp = explainer.explain_instance(single_x, top_n=5)
            item["top_fake_words"] = exp["top_fake_words"]
            item["top_real_words"] = exp["top_real_words"]
        response_items.append(item)

    return {
        "count": len(response_items),
        "results": response_items,
    }

