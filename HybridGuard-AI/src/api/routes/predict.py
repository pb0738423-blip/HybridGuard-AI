"""Prediction and Model Evaluation API routes for HybridGuard AI.
Loads saved artifacts into memory at startup without retraining per request.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

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


@router.post("/predict", response_model=PredictResponse)
def predict_single(req: PredictRequest) -> PredictResponse:
    """Analyze a single news article with the hybrid stacking classifier,
    calibrated probabilities, uncertainty estimation, and influential word attributions.
    """
    vectorizer, hybrid_model, explainer = get_artifacts()

    # Transform text to sparse TF-IDF matrix
    X_sparse = vectorizer.transform([req.text])

    # Run inference with uncertainty & individual model breakdowns
    results = hybrid_model.predict_with_uncertainty(X_sparse)
    res = results[0]

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
    )


@router.post("/batch-predict")
def predict_batch(req: BatchPredictRequest) -> Dict[str, Any]:
    """Perform batch classification over multiple articles."""
    vectorizer, hybrid_model, explainer = get_artifacts()

    X_sparse = vectorizer.transform(req.texts)
    results = hybrid_model.predict_with_uncertainty(X_sparse)

    response_items = []
    for i, res in enumerate(results):
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

