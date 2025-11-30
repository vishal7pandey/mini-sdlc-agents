# tests/test_repair.py
import json
from unittest.mock import patch


from src.agents.finalize_requirements import orchestrator


# Helper to build a fake model completion payload that includes function-call arguments
# in a shape that the repair helper can understand.
def _build_fake_completion_args(arguments: dict) -> dict:
    # Emulate an OpenAI-like response with choices[0].message.tool_call.arguments (string)
    return {
        "choices": [
            {
                "message": {
                    "tool_call": {
                        "arguments": json.dumps(arguments),
                    }
                }
            }
        ]
    }


def test_repair_accepts_fix():
    """Simulate LLM repair returning a valid payload.

    The orchestrator should accept it and continue the normal flow
    (status != needs_human_review).
    """

    # craft a raw_payload that will fail validation (missing required fields)
    bad_payload = {"title": "Incomplete"}  # missing summary, acceptance_criteria, etc.

    # define repaired payload that should validate (simple happy-path fixture)
    repaired_payload = {
        "id": "req-xyz",
        "title": "CLI Todo App",
        "summary": "A simple CLI todo app",
        "stakeholders": ["product"],
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "Add works",
                "priority": "high",
                "type": "functional",
            }
        ],
        "functional_requirements": [
            {
                "id": "FR-1",
                "description": "add command",
                "rationale": "user",
                "priority": "high",
            }
        ],
        "non_functional_requirements": [],
        "dependencies": [],
        "constraints": [],
        "clarifications": [],
        "contradiction": None,
        "confidence": 0.9,
        "meta": {
            "prompt_version": "v1",
            "model": "gpt-5-nano",
            "timestamp": "2025-11-30T00:00:00Z",
            "trace_id": "t1",
            "schema_version": "1.0",
            "repair_attempted": False,
        },
    }

    fake_completion = _build_fake_completion_args(repaired_payload)
    fake_client_return = {
        "response": fake_completion,
        "model": "gpt-5-nano",
        "usage": {"total_tokens": 1000},
    }

    # patch the LLM client call used by attempt_repair
    with patch(
        "src.agents.finalize_requirements.client.call_finalize_requirements",
        return_value=fake_client_return,
    ):
        # call orchestrator with bad payload injected as raw_payload so it tries
        # validation -> repair
        result = orchestrator.run_finalize(
            raw_text="",
            raw_payload=bad_payload,
            use_llm=True,
            trace_id="t1",
        )

    # Expect status to be not needs_human_review (repaired)
    assert result["status"] != "needs_human_review"
    assert "requirements" in result and result["requirements"] is not None
    assert result["requirements"]["title"] == "CLI Todo App"

    # Check repair metadata present either at top-level or nested meta
    meta = result.get("meta", {})
    req_meta = (result.get("requirements") or {}).get("meta", {})
    assert (
        meta.get("repair_attempted") is True or req_meta.get("repair_attempted") is True
    )


def test_repair_fails_then_needs_human():
    """Simulate LLM repair returning still-invalid payload.

    Orchestrator should return needs_human_review and record that repair was
    attempted.
    """

    bad_payload = {"title": "StillBad"}  # invalid

    # LLM returns something but still missing required fields
    still_bad = {"some": "value"}
    fake_completion = _build_fake_completion_args(still_bad)
    fake_client_return = {
        "response": fake_completion,
        "model": "gpt-5-nano",
        "usage": {"total_tokens": 50},
    }

    with patch(
        "src.agents.finalize_requirements.client.call_finalize_requirements",
        return_value=fake_client_return,
    ):
        result = orchestrator.run_finalize(
            raw_text="",
            raw_payload=bad_payload,
            use_llm=True,
            trace_id="t2",
        )

    assert result["status"] == "needs_human_review"
    assert (
        "repair_attempted" in result["meta"]
        and result["meta"]["repair_attempted"] is True
    )
