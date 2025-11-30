from __future__ import annotations

from typing import Any, Dict, List

import pytest

from src.agents.finalize_requirements import langchain_wrapper as lw


def _make_messages() -> List[Dict[str, Any]]:
    return [{"role": "user", "content": "hello"}]


def test_langchain_wrapper_retries_on_transient_error(monkeypatch: Any) -> None:
    """LangChainWrapper.call_text should retry once on a transient error."""

    pytest.importorskip("tenacity")

    # Ensure the wrapper can be constructed without real LangChain installed by
    # providing lightweight stand-ins for the required classes.
    class DummyChat:
        def __init__(
            self, *args: Any, **kwargs: Any
        ) -> None:  # pragma: no cover - simple stub
            pass

    monkeypatch.setattr(lw, "_ChatOpenAI", DummyChat)
    monkeypatch.setattr(lw, "HumanMessage", object)
    monkeypatch.setattr(lw, "SystemMessage", object)

    wrapper = lw.LangChainWrapper(model_name="gpt-test")

    calls = {"count": 0}

    def fake_call_text_once(
        messages: List[Dict[str, Any]], max_tokens: int, timeout_s: int
    ) -> Dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("transient error")
        return {
            "raw": {"choices": [{"message": {"content": "ok"}}]},
            "model": wrapper.model_name,
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 2,
                "total_tokens": 3,
            },
        }

    monkeypatch.setattr(wrapper, "_call_text_once", fake_call_text_once)

    result = wrapper.call_text(messages=_make_messages(), max_tokens=16, timeout_s=5)

    assert calls["count"] == 2
    assert result["raw"]["choices"][0]["message"]["content"] == "ok"
    assert result["usage"]["total_tokens"] == 3
    assert result["model"] == "gpt-test"
