#!/usr/bin/env python
"""Manual smoke test for the finalize_requirements agent.

Usage (from repo root):

    uv run python scripts/smoke_finalize.py "Build a todo CLI"

This will:
- Call the LLM client (gpt-5-nano with function-calling)
- Run the local validator + contradiction detection
- Print the final `FinalizeResult` JSON to stdout

This script is intentionally **not** wired into CI to avoid token costs.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.agents.finalize_requirements.orchestrator import run_finalize


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Manual smoke test for finalize_requirements (LLM-on)",
    )
    parser.add_argument(
        "text",
        nargs="+",
        help="Raw requirements text (e.g. 'Build a todo CLI')",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Run using the local stub only (no OpenAI call)",
    )

    args = parser.parse_args(argv)

    raw_text = " ".join(args.text)
    use_llm = not args.no_llm

    trace_id = f"smoke-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    result: Dict[str, Any] = run_finalize(raw_text, use_llm=use_llm, trace_id=trace_id)

    print(json.dumps(result, indent=2))

    meta = result.get("meta") or {}
    trace_id = meta.get("trace_id") or "unknown-trace"

    runs_dir = Path(__file__).resolve().parents[1] / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    out_path = runs_dir / f"{trace_id}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
