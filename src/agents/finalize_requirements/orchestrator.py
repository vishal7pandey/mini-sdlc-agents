"""Orchestration entrypoint for the finalize_requirements agent.

Task 1: structure-only stub. Later this will:
- Call the LLM client (once implemented) to get a raw payload.
- Use `validator.validate_and_normalize` to enforce the contract.
- Run contradiction detection and compute a FinalizeResult.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .contradiction import detect_contradictions
from .models import FinalizeResult, Meta, Requirements
from .validator import validate_and_normalize


PROMPT_VERSION = "v1"
SCHEMA_VERSION = "v1"


def run_finalize(
    raw_text: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the finalize_requirements pipeline on raw text.

    This stub is **LLM-free**:
    - It constructs a minimal payload from ``raw_text`` + ``context``.
    - It runs local validation/normalization and contradiction detection.
    - It always returns a dict shaped like ``FinalizeResult`` but with
      ``status`` set to ``needs_clarification`` or ``needs_human_review``
      because the LLM step is not yet wired.
    """

    context = context or {}
    raw = (raw_text or "").strip()

    if trace_id is None:
        trace_id = context.get("trace_id", "local-demo")  # type: ignore[assignment]

    if raw:
        first_line = raw.splitlines()[0].strip()
        title = (context.get("title") or first_line or "Draft requirements")[:80]
        summary = raw[:200]
    else:
        title = context.get("title") or "Draft requirements (empty input)"
        summary = "No requirements text provided."

    meta_mapping = Meta.new(
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        model="finalize-requirements-local",
        trace_id=trace_id,
        repair_attempted=False,
    ).model_dump()

    payload: Dict[str, Any] = {
        "title": title,
        "summary": summary,
        "stakeholders": context.get("stakeholders", []),
        "assumptions": [],
        "non_goals": [],
        "acceptance_criteria": [],
        "functional_requirements": [],
        "non_functional_requirements": [],
        "dependencies": context.get("dependencies", []),
        "constraints": context.get("constraints", []),
        "clarifications": [],
        "confidence": 0.0,
        "meta": meta_mapping,
    }

    requirements, validation_errors = validate_and_normalize(payload)

    status = "needs_clarification"
    errors = list(validation_errors)

    if errors:
        status = "needs_human_review"

    if requirements is not None:
        contradiction = detect_contradictions(requirements)
        if contradiction is not None:
            requirements = requirements.copy(update={"contradiction": contradiction})

    result = FinalizeResult(
        status=status,
        requirements=requirements,
        errors=errors,
        meta={
            "trace_id": trace_id,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "source": "orchestrator-local-stub",
        },
    )

    # Return a JSON-safe dict (datetimes, etc. converted to strings).
    return json.loads(result.model_dump_json(exclude_none=True))


def run_finalize_local_demo(fixtures_dir: Optional[str] = None) -> None:
    """Run the orchestrator against local fixture files and print results.

    This provides a simple end-to-end demo without any LLM calls. It reads
    ``*.txt`` files from the ``tests/fixtures`` directory, treats each file as
    raw requirements text, and prints the structured result.
    """

    base_dir = Path(fixtures_dir) if fixtures_dir else Path(__file__).parent / "tests" / "fixtures"

    for path in sorted(base_dir.glob("*.txt")):
        raw_text = path.read_text(encoding="utf-8")
        result = run_finalize(raw_text, context={"fixture_name": path.name})

        print("=" * 80)
        print(f"Fixture: {path.name}")
        print(json.dumps(result, indent=2))


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Local orchestrator stub for finalize_requirements",
    )
    parser.add_argument(
        "--demo",
        "--fixtures",
        action="store_true",
        dest="demo",
        help="Run the local demo over tests/fixtures/*.txt",
    )

    args = parser.parse_args(argv)

    if args.demo:
        run_finalize_local_demo()
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
