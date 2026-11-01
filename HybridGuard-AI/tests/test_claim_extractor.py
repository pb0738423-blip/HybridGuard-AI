"""Unit tests for sentence segmentation, opinion filtering, and checkability scoring."""

import pytest

from src.fact_check.claim_extractor import (
    classify_sentence_checkability,
    extract_claims_from_text,
    split_into_candidate_sentences,
)


def test_split_into_candidate_sentences():
    text = "NASA confirmed the launch of Artemis I in 2022. The mission carried the Orion spacecraft. It was successful."
    sentences = split_into_candidate_sentences(text)
    assert len(sentences) == 3


def test_classify_sentence_checkability():
    # 1. Factual statement with numbers/entities
    res1 = classify_sentence_checkability("The World Health Organization confirmed 500 cases in 2023.")
    assert res1["is_checkable"] is True
    assert "Factual" in res1["category"]

    # 2. Subjective opinion statement
    res2 = classify_sentence_checkability("In my opinion, pizza is the best meal in the entire world.")
    assert res2["is_checkable"] is False
    assert "Opinion" in res2["category"]

    # 3. Future prediction statement
    res3 = classify_sentence_checkability("Artificial intelligence will likely replace all doctors by 2050.")
    assert res3["is_checkable"] is False
    assert "Prediction" in res3["category"]

    # 4. Rhetorical question
    res4 = classify_sentence_checkability("Why are politicians always arguing on television?")
    assert res4["is_checkable"] is False
    assert "Question" in res4["category"]


def test_extract_claims_from_text():
    paragraph = (
        "In my opinion modern movies are terrible. However, the Apollo 11 mission landed on the Moon in July 1969. "
        "Will humans reach Mars soon? The global average temperature rose by 1.1 degrees Celsius."
    )
    claims = extract_claims_from_text(paragraph, max_claims=5)
    assert len(claims) >= 2

    checkable_claims = [c for c in claims if c["is_checkable"]]
    assert len(checkable_claims) >= 2

