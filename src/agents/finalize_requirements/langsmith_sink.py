from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from langsmith import Client as _LangSmithClient  # type: ignore
except Exception:  # pragma: no cover - defensive
    try:
        from langsmith.client import Client as _LangSmithClient  # type: ignore
    except Exception:  # pragma: no cover - defensive
        _LangSmithClient = None  # type: ignore[misc]


def _get_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    text = raw.strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


class LangSmithSink:
    """Small helper to push traces to LangSmith when enabled.

    The sink is intentionally resilient: if the LangSmith client is not
    installed or any call fails, it logs a warning and continues without
    raising.
    """

    def __init__(self, enabled: bool = False, client_config: Optional[Dict[str, Any]] = None) -> None:
        self.enabled = bool(enabled) and _LangSmithClient is not None
        self._client_config = client_config or {}
        self._client: Optional[_LangSmithClient] = None  # type: ignore[assignment]

        if not self.enabled:
            return

        try:
            api_key = self._client_config.get("api_key") or os.getenv("LANGSMITH_API_KEY")
            api_url = self._client_config.get("api_url") or os.getenv("LANGSMITH_API_BASE")

            kwargs: Dict[str, Any] = {}
            if api_key:
                kwargs["api_key"] = api_key
            if api_url:
                kwargs["api_url"] = api_url

            self._client = _LangSmithClient(**kwargs)  # type: ignore[call-arg]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("LangSmithSink initialization failed: %s", exc)
            self.enabled = False

    def push_trace(self, trace_id: str, payload: Dict[str, Any]) -> None:
        """Push a single trace document to LangSmith.

        ``payload`` is expected to be a JSON-serializable dict. The sink does
        not enforce a particular schema; that is handled by the caller.
        """

        if not self.enabled or self._client is None:
            return

        try:
            step = payload.get("step", "finalize_requirements")
            inputs = payload.get("inputs") or {}
            outputs = payload.get("outputs") or {}
            extra = payload.get("extra") or payload

            self._client.create_run(  # type: ignore[call-arg]
                name=step,
                run_type="chain",
                id=trace_id,
                inputs=inputs,
                outputs=outputs,
                extra=extra,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("LangSmithSink.push_trace failed: %s", exc)


def get_langsmith_sink() -> Optional[LangSmithSink]:
    """Factory that returns a configured sink, or ``None`` if disabled."""

    enabled = _get_env_bool("FINALIZE_LANGSMITH_ENABLED", False)
    if not enabled:
        return None

    if _LangSmithClient is None:  # pragma: no cover - defensive
        logger.warning("LangSmith SDK is not installed; disabling LangSmith tracing.")
        return None

    return LangSmithSink(enabled=True)
