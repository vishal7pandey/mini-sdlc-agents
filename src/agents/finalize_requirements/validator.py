"""Validation and normalization helpers for finalize_requirements.

Task 1: stub signatures only. Later tasks will:
- Validate raw payloads against `schema.json` / models.
- Normalize priorities, metrics, and other fields.
"""
from typing import Any, Dict, List, Mapping, Optional, Tuple

from pydantic import ValidationError

from .models import Requirements


MAX_STRING_LENGTH = 200


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
