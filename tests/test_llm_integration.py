"""Integration-style tests for the finalize_requirements orchestrator.

These tests mock the LLM client so we can exercise the full pipeline
(orchestrator -> validator -> contradiction detection) without making
real OpenAI calls.
"""

from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import patch

from src.agents.finalize_requirements.orchestrator import run_finalize


def _make_completion_response(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a minimal chat completion payload with a tool call.

    Only the fields used by ``_extract_function_payload`` are populated.
    """

    return {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "finalize_requirements",
                                "arguments": json.dumps(arguments),
                            }
                        }
                    ]
                }
            }
        ]
    }


def _base_meta(trace_id: str) -> Dict[str, Any]:
    return {
        "prompt_version": "v1",
        "model": "gpt-5-nano",
        "timestamp": "2025-11-30T08:00:00Z",
        "trace_id": trace_id,
        "schema_version": "v1",
        "repair_attempted": False,
    }


@patch("src.agents.finalize_requirements.orchestrator.call_finalize_requirements")
def test_llm_integration_happy_path(mock_call: Any) -> None:
    """Happy path: LLM returns a valid requirements payload that validates."""

    function_args = {
        "title": "CLI Todo App (in-memory)",
        "summary": "A simple CLI todo app.",
        "stakeholders": ["product", "end-user"],
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [],
        "functional_requirements": [],
        "non_functional_requirements": [],
        "dependencies": ["python>=3.11"],
        "constraints": ["no external network"],
        "clarifications": [],
        "confidence": 0.9,
        "meta": _base_meta("trace-happy"),
    }

    mock_call.return_value = {
        "response": _make_completion_response(function_args),
        "model": "gpt-5-nano",
        "usage": {"total_tokens": 42},
    }

    result = run_finalize("Build a simple CLI todo app", use_llm=True)

    assert result["status"] == "needs_clarification"
    requirements = result["requirements"]
    assert requirements["title"] == "CLI Todo App (in-memory)"
    assert requirements["meta"]["model"] == "gpt-5-nano"


@patch("src.agents.finalize_requirements.orchestrator.call_finalize_requirements")
def test_llm_integration_malformed_payload(mock_call: Any) -> None:
    """Malformed tool arguments should lead to needs_human_review."""

    # Tool call contains arguments that are not valid JSON, triggering the
    # defensive error path in ``_extract_function_payload``.
    bad_completion = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "finalize_requirements",
                                "arguments": "{this is not valid json}",
                            }
                        }
                    ]
                }
            }
        ]
    }

    mock_call.return_value = {
        "response": bad_completion,
        "model": "gpt-5-nano",
        "usage": {"total_tokens": 10},
    }

    result = run_finalize("Build a simple CLI todo app", use_llm=True)

    assert result["status"] == "needs_human_review"
    errors = "\n".join(result.get("errors", []))
    assert "LLM call or payload extraction failed" in errors


@patch("src.agents.finalize_requirements.orchestrator.call_finalize_requirements")
def test_llm_integration_contradictory_payload(mock_call: Any) -> None:
    """Contradictory payload should surface as needs_clarification."""

    # This payload matches the conflicting fixture: stateless vs session and
    # no database vs persistence.
    function_args = {
        "title": "We need a multi-tenant SaaS todo service that must be completely stateless",
        "summary": (
            "We need a multi-tenant SaaS todo service that must be completely stateless "
            "and must maintain a persistent session store for each logged-in user. "
            "The product owner also insists that we use no database of any kind."
        ),
        "stakeholders": [],
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [],
        "functional_requirements": [],
        "non_functional_requirements": [],
        "dependencies": [],
        "constraints": [],
        "clarifications": [],
        "confidence": 0.8,
        "meta": _base_meta("trace-contradictory"),
    }

    mock_call.return_value = {
        "response": _make_completion_response(function_args),
        "model": "gpt-5-nano",
        "usage": {"total_tokens": 64},
    }

    result = run_finalize("Conflicting requirements", use_llm=True)

    assert result["status"] == "needs_clarification"
    requirements = result["requirements"]
    contradiction = requirements.get("contradiction")
    assert contradiction is not None
    assert contradiction["flag"] is True
    assert len(contradiction.get("issues", [])) >= 1
