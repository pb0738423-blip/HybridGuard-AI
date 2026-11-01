"""Unit tests for evidence retrieval, stance detection, and zero-hallucination citations."""

import pytest

from src.fact_check.evidence_evaluator import (
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_NOT_CHECKABLE,
    VERDICT_SUPPORTED,
    evaluate_claim_against_evidence,
)
from src.fact_check.pipeline import FactCheckPipeline
from src.fact_check.search_provider import EvidenceDocument, MockSearchProvider


def test_uncheckable_claim_verdict():
    res = evaluate_claim_against_evidence(
        claim_text="I feel that summer is more enjoyable than winter.",
        evidence_docs=[],
        is_checkable=False,
    )
    assert res["verdict"] == VERDICT_NOT_CHECKABLE
    assert len(res["citations"]) == 0


def test_insufficient_evidence_verdict():
    res = evaluate_claim_against_evidence(
        claim_text="An obscure comet was spotted by an amateur astronomer in Ohio.",
        evidence_docs=[],
        is_checkable=True,
    )
    assert res["verdict"] == VERDICT_INSUFFICIENT
    assert "no authoritative sources" in res["explanation"]


def test_supported_verdict_with_mock_provider():
    doc = EvidenceDocument(
        title="Apollo 11",
        url="https://en.wikipedia.org/wiki/Apollo_11",
        snippet="The Apollo 11 mission landed humans on the Moon in July 1969. Neil Armstrong and Buzz Aldrin walked on the lunar surface.",
        source="Wikipedia",
        published_date="2024-01-01",
    )
    mock_provider = MockSearchProvider([doc])
    pipeline = FactCheckPipeline(search_provider=mock_provider)

    res = pipeline.verify_single_claim("Apollo 11 landed humans on the Moon in July 1969.")
    assert res["verdict"] == VERDICT_SUPPORTED
    assert len(res["citations"]) == 1
    assert res["citations"][0]["url"] == "https://en.wikipedia.org/wiki/Apollo_11"


def test_contradicted_verdict_with_debunking_evidence():
    doc = EvidenceDocument(
        title="Fact Check: Earth Darkness Hoax",
        url="https://example.org/factcheck-darkness",
        snippet="Reports claiming NASA confirmed 6 days of total darkness are completely false and debunked. NASA denied this hoax.",
        source="FactCheck Org",
    )
    mock_provider = MockSearchProvider([doc])
    pipeline = FactCheckPipeline(search_provider=mock_provider)

    res = pipeline.verify_single_claim("NASA confirmed 6 days of total darkness across Earth.")
    assert res["verdict"] == VERDICT_CONTRADICTED
    assert len(res["contradicting_evidence"]) > 0

