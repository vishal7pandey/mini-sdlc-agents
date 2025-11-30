from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from tenacity import (  # type: ignore
        retry,
        stop_after_attempt,
        wait_exponential,
    )
except Exception:  # pragma: no cover - defensive
    retry = None  # type: ignore[misc]
    stop_after_attempt = None  # type: ignore[misc]
    wait_exponential = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
except Exception:  # pragma: no cover - defensive
    HumanMessage = None  # type: ignore[misc]
    SystemMessage = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from langchain_openai import ChatOpenAI as _ChatOpenAI  # type: ignore
except Exception:  # pragma: no cover - defensive
    try:  # Legacy import path for older langchain versions.
        from langchain.chat_models import ChatOpenAI as _ChatOpenAI  # type: ignore
    except Exception:  # pragma: no cover - defensive
        _ChatOpenAI = None  # type: ignore[misc]


class LangChainNotAvailable(RuntimeError):
    """Raised when LangChain or its OpenAI chat model is not available."""


def _build_retry_decorator() -> Optional[Any]:
    """Construct a tenacity retry decorator from env, or ``None`` if disabled.

    This helper is intentionally small and defensive; if tenacity is not
    installed, or the env configuration is invalid, it returns ``None`` and
    calls will proceed without retries.
    """

    if retry is None or stop_after_attempt is None or wait_exponential is None:
        return None

    max_retries_raw = os.getenv("FINALIZE_LLM_MAX_RETRIES", "2").strip() or "2"
    base_raw = os.getenv("FINALIZE_LLM_BACKOFF_BASE_S", "0.5").strip() or "0.5"
    max_raw = os.getenv("FINALIZE_LLM_BACKOFF_MAX_S", "4").strip() or "4"

    try:
        max_retries = max(1, int(max_retries_raw))
        base_s = max(0.0, float(base_raw)) or 0.5
        max_s = max(base_s, float(max_raw))
    except ValueError:  # pragma: no cover - defensive
        max_retries = 2
        base_s = 0.5
        max_s = 4.0

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=base_s, max=max_s),
    )


def _extract_usage_from_ai_message(message: Any) -> Optional[Dict[str, int]]:
    """Best-effort extraction of token usage from a LangChain AIMessage.

    LangChain typically exposes usage via ``message.usage_metadata`` as a
    mapping containing ``input_tokens``, ``output_tokens``, and optionally
    ``total_tokens``. This helper normalizes that into the OpenAI-style
    ``{"prompt_tokens", "completion_tokens", "total_tokens"}`` dict
    expected by the rest of this codebase.
    """

    usage_meta = getattr(message, "usage_metadata", None)
    if not isinstance(usage_meta, dict):  # pragma: no cover - defensive
        return None

    try:
        prompt_tokens = int(
            usage_meta.get("input_tokens")
            or usage_meta.get("prompt_tokens")
            or 0
        )
    except (TypeError, ValueError):  # pragma: no cover - defensive
        prompt_tokens = 0

    try:
        completion_tokens = int(
            usage_meta.get("output_tokens")
            or usage_meta.get("completion_tokens")
            or 0
        )
    except (TypeError, ValueError):  # pragma: no cover - defensive
        completion_tokens = 0

    try:
        total_tokens = int(
            usage_meta.get("total_tokens")
            or (prompt_tokens + completion_tokens)
        )
    except (TypeError, ValueError):  # pragma: no cover - defensive
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


class LangChainWrapper:
    """Thin helper around LangChain ChatOpenAI for function-calls and text.

    This wrapper is intentionally minimal and defensive. If LangChain or its
    OpenAI integration is not installed, constructing this class will raise
    :class:`LangChainNotAvailable`. Callers should catch that and gracefully
    fall back to the direct OpenAI SDK path.
    """

    def __init__(self, model_name: str, api_base: Optional[str] = None, **kwargs: Any) -> None:
        if _ChatOpenAI is None or HumanMessage is None or SystemMessage is None:
            raise LangChainNotAvailable(
                "LangChain ChatOpenAI is not available; install langchain and "
                "langchain-openai to enable the LangChain wrapper."
            )

        self.model_name = model_name

        client_kwargs: Dict[str, Any] = {
            "model": model_name,
            "temperature": 0,
        }
        if api_base:
            # For langchain_openai this is ``base_url``; for legacy ChatOpenAI it
            # is usually forwarded to the underlying OpenAI client.
            client_kwargs["base_url"] = api_base

        client_kwargs.update(kwargs)

        self._llm = _ChatOpenAI(**client_kwargs)  # type: ignore[call-arg]
        self._retry_decorator = _build_retry_decorator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call_function(
        self,
        messages: List[Dict[str, Any]],
        tool_def: Dict[str, Any],
        timeout_s: int = 20,
    ) -> Dict[str, Any]:
        """Call the model with function-calling enabled.

        ``tool_def`` is the OpenAI-style function definition:

        .. code-block:: json

           {
             "name": "finalize_requirements",
             "description": "...",
             "parameters": { ... JSON schema ... }
           }

        Returns a dict with keys:

        - ``raw``: dict shaped like an OpenAI chat completion payload.
        - ``function_args``: currently ``None`` (callers parse from ``raw``).
        - ``model``: model name string.
        - ``usage``: OpenAI-style usage dict, or ``None``.
        """

        if self._retry_decorator is not None:
            @self._retry_decorator  # type: ignore[misc]
            def _call() -> Dict[str, Any]:
                return self._call_function_once(messages, tool_def, timeout_s)

            return _call()

        return self._call_function_once(messages, tool_def, timeout_s)

    def call_text(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        timeout_s: int = 12,
    ) -> Dict[str, Any]:
        """Call the model for a plain-text completion (no tools).

        Returns a dict with keys:

        - ``raw``: dict shaped like an OpenAI chat completion payload.
        - ``model``: model name string.
        - ``usage``: OpenAI-style usage dict, or ``None``.
        """

        if self._retry_decorator is not None:
            @self._retry_decorator  # type: ignore[misc]
            def _call() -> Dict[str, Any]:
                return self._call_text_once(messages, max_tokens, timeout_s)

            return _call()

        return self._call_text_once(messages, max_tokens, timeout_s)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_lc_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        lc_messages: List[Any] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))  # type: ignore[arg-type]
            else:
                # Treat everything else as a human message (user/assistant).
                lc_messages.append(HumanMessage(content=content))  # type: ignore[arg-type]
        return lc_messages

    def _call_function_once(
        self,
        messages: List[Dict[str, Any]],
        tool_def: Dict[str, Any],
        timeout_s: int,
    ) -> Dict[str, Any]:
        lc_messages = self._to_lc_messages(messages)

        name = tool_def.get("name", "finalize_requirements")
        tools = [
            {
                "type": "function",
                "function": tool_def,
            }
        ]
        tool_choice = {
            "type": "function",
            "function": {"name": name},
        }

        logger.debug("LangChainWrapper.call_function using model %s", self.model_name)

        # LangChain passes through any extra kwargs to the underlying OpenAI
        # client. We rely on that here for tools/tool_choice.
        ai_message = self._llm.invoke(  # type: ignore[call-arg]
            lc_messages,
            tools=tools,
            tool_choice=tool_choice,
            timeout=timeout_s,
        )

        tool_calls = getattr(ai_message, "additional_kwargs", {}).get("tool_calls") or []
        raw_response: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "tool_calls": tool_calls,
                    }
                }
            ]
        }

        usage = _extract_usage_from_ai_message(ai_message)

        return {
            "raw": raw_response,
            "function_args": None,
            "model": self.model_name,
            "usage": usage,
        }

    def _call_text_once(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        timeout_s: int,
    ) -> Dict[str, Any]:
        lc_messages = self._to_lc_messages(messages)

        logger.debug("LangChainWrapper.call_text using model %s", self.model_name)

        ai_message = self._llm.invoke(  # type: ignore[call-arg]
            lc_messages,
            max_tokens=max_tokens,
            timeout=timeout_s,
            temperature=0,
        )

        content = getattr(ai_message, "content", "")
        raw_response: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "content": content,
                    }
                }
            ]
        }

        usage = _extract_usage_from_ai_message(ai_message)

        return {
            "raw": raw_response,
            "model": self.model_name,
            "usage": usage,
        }
