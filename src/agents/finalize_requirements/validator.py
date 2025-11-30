"""Validation and normalization helpers for finalize_requirements.

Task 1: stub signatures only. Later tasks will:
- Validate raw payloads against `schema.json` / models.
- Normalize priorities, metrics, and other fields.
"""
import json
import logging
from typing import Any, Dict, List, Mapping, Optional, Tuple

from pydantic import ValidationError

from . import client
from .models import Meta, Requirements


MAX_STRING_LENGTH = 200

logger = logging.getLogger(__name__)


def _trim_strings(obj: Any, max_length: int = MAX_STRING_LENGTH) -> Any:
    """Recursively trim all string values in a nested structure.

    Supports dicts, lists, tuples, and primitive values. Strings longer than
    ``max_length`` are truncated to that length.
    """

    if isinstance(obj, str):
        if len(obj) <= max_length:
            return obj
        return obj[:max_length]
    if isinstance(obj, Mapping):
        return {k: _trim_strings(v, max_length) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_trim_strings(v, max_length) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_trim_strings(v, max_length) for v in obj)
    return obj


def _dedupe_string_list(values: Any) -> Any:
    """Deduplicate a list of strings while preserving order.

    If ``values`` is not a list, it is returned unchanged.
    """

    if not isinstance(values, list):
        return values
    seen = set()
    result: List[str] = []
    for item in values:
        if not isinstance(item, str):
            # Keep non-string items as-is; this function is focused on strings.
            result.append(item)
            continue
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _prepare_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make a normalized, pre-validated copy of the incoming payload.

    - Accepts an existing Requirements instance or a raw dict-like payload.
    - Trims long strings.
    - Deduplicates certain list fields.
    """

    if isinstance(payload, Requirements):
        data: Dict[str, Any] = payload.model_dump()
    else:
        data = dict(payload)

    data = _trim_strings(data, MAX_STRING_LENGTH)

    # Deduplicate specific list fields where order matters but duplicates do not.
    for list_field in ("stakeholders", "dependencies"):
        if list_field in data:
            data[list_field] = _dedupe_string_list(data[list_field])

    return data


def validate_and_normalize(payload: Dict[str, Any]) -> Tuple[Optional[Requirements], List[str]]:
    """Validate and normalize a raw requirements payload.

    The function:
    - Accepts either a raw dict or an existing Requirements instance.
    - Trims long strings to ``MAX_STRING_LENGTH``.
    - Deduplicates selected list fields.
    - Uses ``Requirements.normalize`` (Pydantic) for schema validation and
      further normalization.

    Returns ``(Requirements instance, [])`` on success, or ``(None, [errors])``
    if validation fails.
    """

    errors: List[str] = []

    try:
        prepared = _prepare_payload(payload)
    except Exception as exc:  # pragma: no cover - defensive
        return None, [f"Invalid payload type: {exc}"]

    # Explicitly enforce presence of certain top-level required fields before
    # we add any defaults via ``Requirements.normalize``. This ensures missing
    # fields like ``acceptance_criteria`` are surfaced clearly.
    missing_required: List[str] = []
    for field in ("summary", "acceptance_criteria"):
        if field not in prepared:
            missing_required.append(f"{field}: Field required")

    if missing_required:
        return None, missing_required

    trace_id: Optional[str] = None
    meta = prepared.get("meta")
    if isinstance(meta, Mapping):
        trace_id = meta.get("trace_id")  # type: ignore[assignment]

    try:
        requirements = Requirements.normalize(prepared, trace_id=trace_id)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", ()))
            msg = err.get("msg", "Invalid value")
            if loc:
                errors.append(f"{loc}: {msg}")
            else:
                errors.append(msg)
        return None, errors
    except Exception as exc:  # pragma: no cover - defensive
        return None, [f"Unexpected validation error: {exc}"]

    return requirements, []


def _extract_function_args_from_model_response(raw_model_resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Try several common response shapes to extract function-calling arguments.

    Returns a dict (parsed JSON) or ``None`` if nothing usable is found.
    """

    try:
        choices = raw_model_resp.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}

            # Primary: OpenAI tools API shape: message.tool_calls[0].function.arguments
            tool_calls = message.get("tool_calls") or []
            if isinstance(tool_calls, list) and tool_calls:
                function_info = tool_calls[0].get("function") or {}
                args_raw = function_info.get("arguments")
                if isinstance(args_raw, dict):
                    return args_raw
                if isinstance(args_raw, str):
                    try:
                        return json.loads(args_raw)
                    except Exception:  # pragma: no cover - defensive
                        pass

            # Fallback: some SDKs expose a single "tool_call" or "function_call" mapping.
            tool_call = message.get("tool_call") or message.get("function_call")
            if tool_call and "arguments" in tool_call:
                args_raw = tool_call["arguments"]
                if isinstance(args_raw, dict):
                    return args_raw
                try:
                    return json.loads(args_raw)
                except Exception:  # pragma: no cover - defensive
                    try:
                        return json.loads(str(args_raw))
                    except Exception:
                        return None

        # Fallback: rarely, tool_calls may appear at the top level of the response.
        if "tool_calls" in raw_model_resp:
            tc = raw_model_resp["tool_calls"]
            if isinstance(tc, list) and tc:
                args = tc[0].get("arguments")
                if isinstance(args, str):
                    try:
                        return json.loads(args)
                    except Exception:  # pragma: no cover - defensive
                        return None
                if isinstance(args, dict):
                    return args
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("extract_function_args fallback failure: %s", exc)

    return None


def attempt_repair(
    raw_payload: Dict[str, Any],
    validation_errors: List[str],
    trace_id: Optional[str] = None,
) -> Tuple[Optional[Requirements], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Attempt a single automated repair using the LLM client.

    The model is asked to return a corrected ``finalize_requirements`` function
    arguments JSON that satisfies the schema, given the original payload and the
    validation errors.

    Returns ``(requirements_instance_or_None, repaired_payload_or_None, repair_meta)``.
    ``repair_meta`` contains model/usage or error information for auditing.
    """

    try:
        # Build concise repair context; keep it small to reduce tokens.
        repair_context: Dict[str, Any] = {
            "repair": True,
            "validation_errors": list(validation_errors),
            "original_payload_summary": {
                "top_keys": list(raw_payload.keys())[:10],
                "short_preview": json.dumps(
                    {
                        k: raw_payload.get(k)
                        for k in list(raw_payload.keys())[:5]
                    },
                    default=str,
                )[:1000],
            },
            # Include full original payload so the model can correct it if necessary.
            "original_payload": raw_payload,
            "instructions": (
                "You previously returned a JSON payload that failed schema validation. "
                "Please return a corrected `finalize_requirements` function argument "
                "JSON that conforms exactly to the schema. Preserve meaning where "
                "possible; only change fields necessary to satisfy the schema "
                "constraints. Return JSON only."
            ),
        }

        client_result = client.call_finalize_requirements(
            raw_requirement_text="",
            context=repair_context,
            trace_id=trace_id,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Repair attempt failed to call LLM client: %s", exc)
        return None, None, {"error": str(exc)}

    repair_meta: Dict[str, Any] = {
        "model": client_result.get("model"),
        "usage": client_result.get("usage"),
    }

    raw_model_resp = client_result.get("response") or {}
    repaired_candidate = _extract_function_args_from_model_response(raw_model_resp)

    if not repaired_candidate:
        logger.debug(
            "Repair attempt did not return parsable function args; raw response keys: %s",
            list(raw_model_resp.keys())[:10],
        )
        return None, None, repair_meta

    repaired_requirements, repaired_errors = validate_and_normalize(repaired_candidate)
    if repaired_requirements is not None:
        # Best-effort: mark repair in meta and merge model/usage.
        try:
            repaired_requirements.meta.repair_attempted = True
            model_name = repair_meta.get("model")
            if isinstance(model_name, str):
                repaired_requirements.meta.model = model_name

            usage_info = repair_meta.get("usage")
            if isinstance(usage_info, dict):
                total_tokens = usage_info.get("total_tokens")
                if total_tokens is not None:
                    repaired_requirements.meta.token_usage = int(total_tokens)
        except Exception:  # pragma: no cover - defensive
            # Meta updates are best-effort; do not fail repair.
            pass

        return repaired_requirements, repaired_candidate, repair_meta

    # Still invalid after repair.
    return None, repaired_candidate, repair_meta
