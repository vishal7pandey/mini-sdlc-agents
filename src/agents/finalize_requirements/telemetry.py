from __future__ import annotations

import datetime as _dt
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int = 2048) -> str:
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_HEX_RE = re.compile(r"\b[0-9a-fA-F]{32,}\b")
_TOKEN_RE = re.compile(r"\b(?:sk|lsv2)_[A-Za-z0-9]{16,}\b")


def _mask_text(text: str) -> str:
    """Best-effort, conservative masking of likely PII/secrets.

    Currently masks:
    - email addresses
    - long hex strings (32+ chars)
    - obvious token-like prefixes (sk_/lsv2_)
    """

    if not isinstance(text, str):
        text = str(text)

    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _TOKEN_RE.sub("[REDACTED_TOKEN]", text)
    text = _HEX_RE.sub("[REDACTED_HEX]", text)
    return text


def build_finalize_trace_payload(
    *,
    trace_id: Optional[str],
    step: str,
    raw_text: str,
    context: Optional[Dict[str, Any]],
    model: Optional[str],
    usage: Optional[Dict[str, Any]],
    raw_model_response_excerpt: Optional[str],
    function_arguments: Optional[Dict[str, Any]],
    validation_status: str,
    validation_errors: Optional[list[str]],
    repair: Optional[Dict[str, Any]],
    semantic_contradiction: Optional[Dict[str, Any]],
    final_result: Dict[str, Any],
    include_raw: bool = False,
    function_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct a LangSmith-ready trace payload for finalize_requirements.

    The payload is intentionally compact and focuses on high-value fields.
    Large text blobs are truncated; raw content can be omitted entirely by
    setting ``include_raw=False``.
    """

    # Use timezone-aware UTC and normalize to a simple Z-suffixed ISO string.
    now = _dt.datetime.now(_dt.timezone.utc)
    now_iso = now.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"

    user_excerpt = _truncate(_mask_text(raw_text or ""), 512)
    ctx_excerpt = _truncate(_mask_text(str(context or {})), 512)

    payload: Dict[str, Any] = {
        "trace_id": trace_id,
        "step": step,
        "timestamp": now_iso,
        "user_input_excerpt": user_excerpt,
        "context_excerpt": ctx_excerpt,
        "model": model,
        "usage": usage or {},
        "validation": {
            "status": validation_status,
            "errors": list(validation_errors or []),
        },
        "repair": repair or {},
        "semantic_contradiction": semantic_contradiction,
    }

    if raw_model_response_excerpt and include_raw:
        try:
            raw_limit = int(os.getenv("LANGSMITH_RAW_TRUNCATE", "800") or "800")
        except ValueError:  # pragma: no cover - defensive
            raw_limit = 800
        masked_raw = _mask_text(raw_model_response_excerpt)
        payload["raw_model_response_excerpt"] = _truncate(masked_raw, raw_limit)

    if function_arguments is not None:
        payload["function_arguments"] = function_arguments

    if include_raw:
        # Full final result can be large; still gate it behind include_raw.
        payload["final_result"] = final_result

    # Optionally include the function schema used for the finalize_requirements
    # call; gated behind LANGSMITH_INCLUDE_SCHEMA to keep traces small.
    include_schema_env = os.getenv("LANGSMITH_INCLUDE_SCHEMA", "false").strip().lower()
    if include_schema_env in {"1", "true", "yes", "on"} and function_schema is not None:
        payload["function_schema"] = function_schema

    # Simple structure for LangSmithSink.create_run inputs/outputs.
    payload["inputs"] = {
        "raw_text_excerpt": user_excerpt,
        "context_excerpt": ctx_excerpt,
    }
    payload["outputs"] = {
        "status": final_result.get("status"),
        "meta": final_result.get("meta"),
    }

    payload["extra"] = {
        "semantic_contradiction": semantic_contradiction,
        "repair": repair or {},
    }

    return payload
