from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.agents.finalize_requirements import contradiction as contradiction_mod
from src.agents.finalize_requirements.models import Meta, Requirements


def _make_requirements(summary: str = "") -> Requirements:
    meta = Meta.new(
        prompt_version="v1",
        schema_version="v1",
        model="gpt-5-nano",
        trace_id="t-semantic",
        repair_attempted=False,
    )
    return Requirements(
        id="req-1",
        title="Demo requirements",
        summary=summary or "Demo summary",
        non_goals=["no DB persistence"],
        dependencies=["Postgres 14"],
        confidence=0.9,
        meta=meta,
    )


def _suspicious_pairs(req: Requirements) -> List[Dict[str, str]]:
    return [
        {
            "pair_id": "p-1",
            "rule_id": "R_no_db_vs_dep",
            "field_a": "non_goals[0]",
            "text_a": "no DB persistence",
            "field_b": "dependencies[0]",
            "text_b": "Postgres 14",
            "context": req.summary,
        }
    ]


@patch("src.agents.finalize_requirements.client.call_semantic_check")
def test_semantic_contradiction_confirmed(mock_call: Any) -> None:
    """LLM confirms a contradiction -> one issue, status ok."""

    req = _make_requirements("no DB but depends on Postgres")
    pairs = _suspicious_pairs(req)

    response_payload = [
        {
            "pair_id": "p-1",
            "conflict": True,
            "reason": "Postgres implies persistence while non-goal forbids DB",
            "confidence": 0.9,
        }
    ]

    mock_call.return_value = {
        "response": response_payload,
        "model": "gpt-5-nano",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    issues, meta = contradiction_mod.semantic_check(req, pairs, trace_id="t-sem-1")

    assert len(issues) == 1
    assert "Postgres implies persistence" in issues[0].explanation
    assert meta["pairs_checked"] == 1
    assert meta["pairs_confirmed"] == 1
    assert meta["status"] == "ok"
    assert meta["model"] == "gpt-5-nano"
    assert isinstance(meta["usage"], dict)


@patch("src.agents.finalize_requirements.client.call_semantic_check")
def test_semantic_contradiction_denied(mock_call: Any) -> None:
    """LLM denies contradiction -> no issues, status ok."""

    req = _make_requirements("no DB but depends on Postgres")
    pairs = _suspicious_pairs(req)

    response_payload = [
        {
            "pair_id": "p-1",
            "conflict": False,
            "reason": "They can be compatible",
            "confidence": 0.4,
        }
    ]

    mock_call.return_value = {
        "response": response_payload,
        "model": "gpt-5-nano",
        "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
    }

    issues, meta = contradiction_mod.semantic_check(req, pairs, trace_id="t-sem-2")

    assert issues == []
    assert meta["pairs_checked"] == 1
    assert meta["pairs_confirmed"] == 0
    assert meta["status"] == "ok"


@patch("src.agents.finalize_requirements.client.call_semantic_check")
def test_semantic_contradiction_malformed_response(mock_call: Any) -> None:
    """Malformed LLM response should mark semantic check as failed."""

    req = _make_requirements("no DB but depends on Postgres")
    pairs = _suspicious_pairs(req)

    # Return a non-JSON string to trigger parse failure.
    completion_payload = {
        "choices": [
            {
                "message": {
                    "content": "this is not JSON",
                }
            }
        ]
    }

    mock_call.return_value = {
        "response": completion_payload,
        "model": "gpt-5-nano",
        "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
    }

    issues, meta = contradiction_mod.semantic_check(req, pairs, trace_id="t-sem-3")

    assert issues == []
    assert meta["status"] == "failed"
    assert "error" in meta
