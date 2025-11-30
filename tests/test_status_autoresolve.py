from __future__ import annotations

from typing import Any, Dict

from src.agents.finalize_requirements.models import Meta
from src.agents.finalize_requirements.orchestrator import run_finalize


def _base_meta(trace_id: str) -> Dict[str, Any]:
    return Meta.new(
        prompt_version="v1",
        schema_version="v1",
        model="finalize-requirements-local",
        trace_id=trace_id,
        repair_attempted=False,
    ).model_dump()


def test_autoresolve_sets_partially_ok() -> None:
    """High-confidence auto assumptions should lead to partially_ok status."""

    raw_text = (
        "Create a local CLI notes app that lets a single user add, list, and delete notes "
        "from the command line."
    )

    payload: Dict[str, Any] = {
        "id": "req-auto-1",
        "title": "Local CLI notes app",
        "summary": raw_text,
        "stakeholders": [],
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "User can add a note",
                "priority": "medium",
                "type": "functional",
            }
        ],
        "functional_requirements": [
            {
                "id": "FR-1",
                "description": "Add/list/delete notes from the CLI",
                "rationale": "Basic CRUD for notes",
                "priority": "medium",
            }
        ],
        "non_functional_requirements": [],
        "dependencies": [],
        "constraints": [],
        "clarifications": [],
        "confidence": 0.9,
        "meta": _base_meta("trace-auto-partial"),
    }

    result = run_finalize(raw_text=raw_text, use_llm=False, raw_payload=payload)

    assert result["status"] == "partially_ok"

    requirements = result["requirements"]
    auto_assumptions = requirements.get("auto_assumptions", [])
    assert auto_assumptions, "Expected at least one auto_assumption"

    confidences = [a["confidence"] for a in auto_assumptions]
    avg_conf = sum(confidences) / float(len(confidences))
    assert avg_conf > 0.6


def test_ok_when_no_clarifications() -> None:
    """Explicit payload with no clarifications and no auto assumptions -> ok."""

    raw_text = (
        "Build a multi-user web app for note taking. Use Postgres for persistence and "
        "support user login and authentication."
    )

    payload: Dict[str, Any] = {
        "id": "req-auto-2",
        "title": "Multi-user notes web app",
        "summary": raw_text,
        "stakeholders": ["product", "engineering"],
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "Users can sign up and log in",
                "priority": "high",
                "type": "functional",
            }
        ],
        "functional_requirements": [
            {
                "id": "FR-1",
                "description": "Users can create, edit, and delete notes",
                "rationale": "Core functionality",
                "priority": "high",
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-1",
                "description": "Persist notes to Postgres with basic durability",
                "metric": "",
                "target": "",
            }
        ],
        "dependencies": ["Postgres 14", "FastAPI"],
        "constraints": [],
        "clarifications": [],
        "confidence": 0.95,
        "meta": _base_meta("trace-auto-ok"),
    }

    result = run_finalize(raw_text=raw_text, use_llm=False, raw_payload=payload)

    assert result["status"] == "ok"

    requirements = result["requirements"]
    assert requirements.get("clarifications") == []
    assert requirements.get("auto_assumptions", []) == []
