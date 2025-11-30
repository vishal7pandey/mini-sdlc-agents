from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

from src.agents.finalize_requirements.langsmith_sink import LangSmithSink
from src.agents.finalize_requirements.telemetry import build_finalize_trace_payload


def test_langsmith_sink_handles_missing_client_gracefully() -> None:
    """If the LangSmith client is missing, push_trace should be a no-op."""

    sink = LangSmithSink(enabled=False)
    # Even when enabled=False, push_trace should not raise.
    sink.push_trace("trace-id", {"step": "finalize_requirements"})


def test_langsmith_sink_push_trace_catches_exceptions() -> None:
    """Errors from the underlying client should be swallowed and logged."""

    fake_client = MagicMock()
    fake_client.create_run.side_effect = RuntimeError("boom")

    sink = LangSmithSink(enabled=True)
    object.__setattr__(sink, "_client", fake_client)  # type: ignore[arg-type]

    payload: Dict[str, Any] = {
        "step": "finalize_requirements",
        "inputs": {"raw_text_excerpt": "foo"},
        "outputs": {"status": "ok"},
    }

    # Should not raise even though the client throws.
    sink.push_trace("trace-id", payload)


@patch("src.agents.finalize_requirements.langsmith_sink._LangSmithClient", None)
def test_get_langsmith_sink_disabled_when_client_missing() -> None:
    from src.agents.finalize_requirements.langsmith_sink import get_langsmith_sink

    sink = get_langsmith_sink()
    assert sink is None


def _base_final_result() -> Dict[str, Any]:
    return {"status": "ok", "meta": {}}


def test_telemetry_includes_schema_when_enabled(monkeypatch: Any) -> None:
    monkeypatch.setenv("LANGSMITH_INCLUDE_SCHEMA", "true")

    payload = build_finalize_trace_payload(
        trace_id="t1",
        step="finalize_requirements",
        raw_text="hello",
        context={"foo": "bar"},
        model="gpt-test",
        usage={"total_tokens": 10},
        raw_model_response_excerpt=None,
        function_arguments=None,
        validation_status="passed",
        validation_errors=[],
        repair={},
        semantic_contradiction=None,
        final_result=_base_final_result(),
        include_raw=False,
        function_schema={"title": "test-schema"},
    )

    assert payload["function_schema"]["title"] == "test-schema"


def test_telemetry_raw_excerpt_masked_and_truncated(monkeypatch: Any) -> None:
    monkeypatch.setenv("LANGSMITH_RAW_TRUNCATE", "50")

    # Place email and token early so they survive truncation after masking.
    raw = "user@example.com token sk_ABCDEF0123456789 0123456789abcdef" * 2

    payload = build_finalize_trace_payload(
        trace_id="t1",
        step="finalize_requirements",
        raw_text="hello",
        context=None,
        model="gpt-test",
        usage=None,
        raw_model_response_excerpt=raw,
        function_arguments=None,
        validation_status="passed",
        validation_errors=[],
        repair={},
        semantic_contradiction=None,
        final_result=_base_final_result(),
        include_raw=True,
        function_schema=None,
    )

    excerpt = payload["raw_model_response_excerpt"]
    assert "[REDACTED_EMAIL]" in excerpt
    assert "[REDACTED_TOKEN]" in excerpt or "[REDACTED_HEX]" in excerpt
    assert len(excerpt) <= 53  # 50 chars + "..." suffix
