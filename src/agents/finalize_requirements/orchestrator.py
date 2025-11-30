"""Orchestration entrypoint for the finalize_requirements agent.

Task 1: structure-only stub. Later this will:
- Call the LLM client (once implemented) to get a raw payload.
- Use `validator.validate_and_normalize` to enforce the contract.
- Run contradiction detection and compute a FinalizeResult.
"""
import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .client import call_finalize_requirements
from .contradiction import detect_contradictions
from .models import FinalizeResult, Meta, Requirements
from .validator import validate_and_normalize


PROMPT_VERSION = "v1"
SCHEMA_VERSION = "v1"

logger = logging.getLogger(__name__)

_USAGE_FILE = Path(__file__).resolve().parents[3] / "runs" / "usage.json"


def _get_price_per_mtokens(name: str) -> float:
    """Read a per-million-token USD price from env, or 0.0 if unset/invalid.

    These values are expected to come from the official OpenAI pricing page
    for the configured model (e.g. gpt-5-nano) and are deliberately kept out
    of code so they can be updated without a deploy.
    """

    raw = os.getenv(name)
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _estimate_cost_usd(usage: Optional[Dict[str, Any]]) -> Optional[float]:
    """Estimate cost in USD from token usage and env-configured prices.

    Prices are read from:
    - FINALIZE_INPUT_PRICE_PER_MTOKENS  (USD per 1M prompt tokens)
    - FINALIZE_OUTPUT_PRICE_PER_MTOKENS (USD per 1M completion tokens)
    """

    if not usage:
        return None

    try:
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None

    if prompt_tokens == 0 and completion_tokens == 0:
        return None

    input_price = _get_price_per_mtokens("FINALIZE_INPUT_PRICE_PER_MTOKENS")
    output_price = _get_price_per_mtokens("FINALIZE_OUTPUT_PRICE_PER_MTOKENS")

    if input_price <= 0.0 and output_price <= 0.0:
        return None

    cost = (
        prompt_tokens * (input_price / 1_000_000.0)
        + completion_tokens * (output_price / 1_000_000.0)
    )
    return round(cost, 8)


def _get_int_env(name: str) -> Optional[int]:
    """Return an integer value from an env var, or ``None`` if unset/invalid."""

    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:  # pragma: no cover - defensive
        return None


def _get_env_float(name: str) -> Optional[float]:
    """Return a float value from an env var, or ``None`` if unset/invalid."""

    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:  # pragma: no cover - defensive
        return None


def _today_str() -> str:
    """Return today's date as an ISO string (UTC)."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_usage_state() -> Dict[str, Any]:
    """Load per-day usage counters from ``runs/usage.json`` if present."""

    if not _USAGE_FILE.exists():
        return {"days": {}}

    try:
        with _USAGE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:  # pragma: no cover - defensive
        return {"days": {}}

    if not isinstance(data, dict):
        return {"days": {}}

    days = data.get("days")
    if not isinstance(days, dict):
        data["days"] = {}
    return data


def _save_usage_state(state: Dict[str, Any]) -> None:
    """Persist per-day usage counters to ``runs/usage.json``."""

    _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _USAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _get_daily_totals(state: Dict[str, Any], day: str) -> tuple[int, float]:
    """Return (tokens, cost_usd) totals for the given day key."""

    days = state.get("days") or {}
    info = days.get(day) or {}
    try:
        tokens = int(info.get("tokens") or 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        tokens = 0
    try:
        cost_usd = float(info.get("cost_usd") or 0.0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        cost_usd = 0.0
    return tokens, cost_usd


def _update_usage_counters(usage: Optional[Dict[str, Any]], cost: Optional[float]) -> None:
    """Update the per-day token and cost counters for this call.

    This is intentionally simple and file-based for local dev/testing; it is
    not intended as a production-grade accounting system.
    """

    if not usage:
        return

    try:
        total_tokens = int(usage.get("total_tokens") or 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return

    if total_tokens <= 0:
        return

    today = _today_str()
    state = _load_usage_state()
    days = state.setdefault("days", {})
    info = dict(days.get(today) or {})

    try:
        prev_tokens = int(info.get("tokens") or 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        prev_tokens = 0
    try:
        prev_cost = float(info.get("cost_usd") or 0.0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        prev_cost = 0.0

    info["tokens"] = prev_tokens + total_tokens
    if cost is not None:
        info["cost_usd"] = prev_cost + float(cost)
    else:
        info["cost_usd"] = prev_cost

    try:
        prev_calls = int(info.get("calls") or 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        prev_calls = 0
    info["calls"] = prev_calls + 1

    days[today] = info
    _save_usage_state(state)


def _extract_function_payload(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the finalize_requirements function arguments from a tool call.

    The response is expected to be the raw OpenAI chat completion payload
    returned by :func:`call_finalize_requirements`.
    """

    choices = response.get("choices") or []
    if not choices:
        raise ValueError("Model response contained no choices.")

    message = choices[0].get("message") or {}
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        raise ValueError("Model response contained no tool_calls for finalize_requirements.")

    for tool_call in tool_calls:
        function = tool_call.get("function") or {}
        if function.get("name") != "finalize_requirements":
            continue
        args_str = function.get("arguments")
        if not isinstance(args_str, str):
            raise ValueError("Tool call arguments were not a string as expected.")
        try:
            return json.loads(args_str)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Tool call arguments were not valid JSON: {exc}") from exc

    raise ValueError("No finalize_requirements function tool call found in model response.")


def run_finalize(
    raw_text: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    *,
    use_llm: bool = True,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the finalize_requirements pipeline on raw text.

    When ``use_llm`` is True and ``raw_payload`` is not provided, this function
    will call the OpenAI client to obtain a structured requirements payload via
    function-calling before running local validation and contradiction
    detection. When ``use_llm`` is False, it falls back to a local stub that
    derives a minimal payload directly from ``raw_text`` + ``context``.
    """

    context = context or {}
    raw = (raw_text or "").strip()

    if trace_id is None:
        trace_id = context.get("trace_id", "local-demo")  # type: ignore[assignment]

    # Guardrail: approximate per-call input token cap for LLM path.
    max_input_tokens = _get_int_env("FINALIZE_MAX_INPUT_TOKENS")
    if use_llm and max_input_tokens is not None and max_input_tokens > 0 and raw:
        approx_tokens = max(1, len(raw.split()))
        if approx_tokens > max_input_tokens:
            logger.warning(
                "Refusing finalize_requirements LLM call: approx %d tokens exceeds cap %d",
                approx_tokens,
                max_input_tokens,
            )
            result = FinalizeResult(
                status="needs_human_review",
                requirements=None,
                errors=[
                    "Input too long for finalize_requirements: "
                    f"approx {approx_tokens} tokens exceeds cap {max_input_tokens}. "
                    "Consider chunking or summarizing before calling this agent.",
                ],
                meta={
                    "trace_id": trace_id,
                    "prompt_version": PROMPT_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "source": "orchestrator-llm",
                },
            )
            return json.loads(result.model_dump_json(exclude_none=True))

    # Guardrail: simple daily token quota based on runs/usage.json.
    daily_quota = _get_int_env("FINALIZE_DAILY_TOKEN_QUOTA")
    if use_llm and daily_quota is not None and daily_quota > 0:
        state = _load_usage_state()
        today = _today_str()
        used_tokens, _ = _get_daily_totals(state, today)
        if used_tokens >= daily_quota:
            logger.warning(
                "Daily token quota exceeded for finalize_requirements: used=%d quota=%d; refusing LLM call",
                used_tokens,
                daily_quota,
            )
            result = FinalizeResult(
                status="needs_human_review",
                requirements=None,
                errors=[
                    "Daily token quota exceeded for finalize_requirements: "
                    f"used={used_tokens} tokens, quota={daily_quota}.",
                ],
                meta={
                    "trace_id": trace_id,
                    "prompt_version": PROMPT_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "source": "orchestrator-llm",
                },
            )
            return json.loads(result.model_dump_json(exclude_none=True))

    model_name: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None

    # Determine the raw payload to validate: either from the LLM function
    # call, from the caller, or from the local stub.
    if raw_payload is None and use_llm:
        try:
            client_result = call_finalize_requirements(
                raw_requirement_text=raw_text,
                context=context,
                trace_id=trace_id,
            )
            completion_payload = client_result.get("response") or {}
            model_name = client_result.get("model")
            usage_value = client_result.get("usage")
            if isinstance(usage_value, dict):
                usage = usage_value
            raw_payload = _extract_function_payload(completion_payload)
        except Exception as exc:  # pragma: no cover - defensive
            # If the model call fails or the payload cannot be extracted,
            # return a needs_human_review result.
            result = FinalizeResult(
                status="needs_human_review",
                requirements=None,
                errors=[f"LLM call or payload extraction failed: {exc}"],
                meta={
                    "trace_id": trace_id,
                    "prompt_version": PROMPT_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "source": "orchestrator-llm",
                },
            )
            return json.loads(result.model_dump_json(exclude_none=True))

    if raw_payload is None:
        # Local stub path: construct a minimal payload from raw text.
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

        raw_payload = {
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
        model_name = meta_mapping.get("model")  # type: ignore[assignment]

    requirements, validation_errors = validate_and_normalize(raw_payload)

    if requirements is not None:
        try:
            if model_name is not None:
                requirements.meta.model = model_name
            if usage is not None:
                total_tokens_val = usage.get("total_tokens")
                if total_tokens_val is not None:
                    requirements.meta.token_usage = int(total_tokens_val)
        except Exception:  # pragma: no cover - defensive
            pass

    status = "needs_clarification"
    errors = list(validation_errors)

    if errors:
        status = "needs_human_review"

    if requirements is not None:
        contradiction = detect_contradictions(requirements)
        if contradiction is not None:
            requirements = requirements.model_copy(update={"contradiction": contradiction})

    # Derive top-level model + token usage + cost metadata.
    model_from_requirements: Optional[str] = None
    token_usage_from_requirements: Optional[int] = None
    if requirements is not None:
        try:
            model_from_requirements = requirements.meta.model
            token_usage_from_requirements = requirements.meta.token_usage
        except AttributeError:  # pragma: no cover - defensive
            model_from_requirements = None
            token_usage_from_requirements = None

    meta_model = model_name or model_from_requirements

    meta_token_usage: Optional[int] = None
    if usage is not None:
        try:
            total_tokens_val = usage.get("total_tokens")
            if total_tokens_val is not None:
                meta_token_usage = int(total_tokens_val)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            meta_token_usage = None

    if meta_token_usage is None:
        meta_token_usage = token_usage_from_requirements

    cost_estimate = _estimate_cost_usd(usage)

    # Update simple local usage counters and log cost alerts.
    if usage is not None:
        _update_usage_counters(usage, cost_estimate)

    # Threshold for logging warnings.
    log_alert_threshold = _get_env_float("FINALIZE_SINGLE_CALL_COST_ALERT_USD")
    # Threshold for setting a structured cost_alert flag on the result meta.
    meta_alert_threshold = _get_env_float("FINALIZE_COST_ALERT_USD") or log_alert_threshold

    meta_cost_alert: Optional[bool] = None

    if cost_estimate is not None:
        if log_alert_threshold is not None and log_alert_threshold > 0.0 and cost_estimate > log_alert_threshold:
            logger.warning(
                "finalize_requirements single-call cost %.8f USD exceeds alert threshold %.8f (model=%s, trace_id=%s)",
                cost_estimate,
                log_alert_threshold,
                meta_model,
                trace_id,
            )
        else:
            logger.info(
                "finalize_requirements cost_estimate_usd=%.8f tokens=%s model=%s trace_id=%s",
                cost_estimate,
                meta_token_usage,
                meta_model,
                trace_id,
            )

        if meta_alert_threshold is not None and meta_alert_threshold > 0.0:
            meta_cost_alert = cost_estimate > meta_alert_threshold

    result = FinalizeResult(
        status=status,
        requirements=requirements,
        errors=errors,
        meta={
            "trace_id": trace_id,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "source": "orchestrator-llm" if use_llm else "orchestrator-local-stub",
            "model": meta_model,
            "token_usage": meta_token_usage,
            "cost_estimate_usd": cost_estimate,
            "usage": usage,
            "cost_alert": meta_cost_alert,
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
        # Demo stays LLM-free by forcing use_llm=False so it can be run
        # without network access.
        result = run_finalize(raw_text, context={"fixture_name": path.name}, use_llm=False)

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
