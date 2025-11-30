from __future__ import annotations

from unittest.mock import patch

from src.agents.finalize_requirements.client import OpenAIAdapter


@patch("src.agents.finalize_requirements.client.LangChainWrapper")
def test_openai_adapter_uses_langchain_model_env(mock_wrapper, monkeypatch) -> None:
    """LangChainWrapper should be constructed with FINALIZE_LANGCHAIN_MODEL when set."""

    monkeypatch.setenv("FINALIZE_USES_LANGCHAIN", "true")
    monkeypatch.setenv("FINALIZE_LANGCHAIN_MODEL", "gpt-5-langchain-special")
    monkeypatch.setenv("FINALIZE_MODEL", "gpt-5-default")

    # Instantiate the adapter; this should try to construct LangChainWrapper
    adapter = OpenAIAdapter()  # noqa: F841

    mock_wrapper.assert_called_once()
    called_model = mock_wrapper.call_args[0][0]
    assert called_model == "gpt-5-langchain-special"
