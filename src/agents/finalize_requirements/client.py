"""OpenAI client for the finalize_requirements agent.

This module is intentionally **side-effectful**:
- loads the JSON schema and prompt template from disk
- calls OpenAI's chat completions API with function-calling enabled
- returns the raw model response plus lightweight metadata

All parsing/validation of the returned JSON into domain models is handled by
``validator.validate_and_normalize`` and the Pydantic models in ``models.py``.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI


logger = logging.getLogger(__name__)

load_dotenv()

_BASE_DIR = Path(__file__).parent
_SCHEMA_PATH = _BASE_DIR / "schema.json"
_PROMPT_PATH = _BASE_DIR / "prompt.txt"
_PROMPT_SEMANTIC_PATH = _BASE_DIR / "prompt_semantic.txt"


def _load_function_schema() -> Dict[str, Any]:
    """Load the JSON schema for the finalize_requirements function.

    The schema is defined in ``schema.json`` and is used as the ``parameters``
    object for OpenAI function-calling.
    """

    with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_prompt_template() -> str:
    """Load the canonical prompt template from ``prompt.txt``."""

    return _PROMPT_PATH.read_text(encoding="utf-8")


def _load_semantic_prompt_template() -> str:
    """Load the semantic contradiction prompt template from ``prompt_semantic.txt``."""

    return _PROMPT_SEMANTIC_PATH.read_text(encoding="utf-8")


_FUNCTION_SCHEMA: Dict[str, Any] = _load_function_schema()
_PROMPT_TEMPLATE: str = _load_prompt_template()
_PROMPT_SEMANTIC_TEMPLATE: str = _load_semantic_prompt_template()


class OpenAIAdapter:
    def __init__(self, model: Optional[str] = None, api_base: Optional[str] = None) -> None:
        self.model = model or os.getenv("FINALIZE_MODEL", "gpt-5-nano")
        base = api_base or os.getenv("OPENAI_API_BASE")
        if base:
            self._client = OpenAI(base_url=base)
        else:
            self._client = OpenAI()

    def call(
        self,
        raw_requirement_text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = context or {}

        system_message = {
            "role": "system",
            "content": _PROMPT_TEMPLATE.format(model_name=self.model),
        }

        user_payload = {
            "raw_requirement_text": raw_requirement_text,
            "context": context,
            "trace_id": trace_id,
        }

        user_message = {
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False),
        }

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "finalize_requirements",
                    "description": "Finalize and normalize software requirements.",
                    "parameters": _FUNCTION_SCHEMA,
                },
            }
        ]

        tool_choice = {
            "type": "function",
            "function": {"name": "finalize_requirements"},
        }

        logger.debug("Calling OpenAI %s with function finalize_requirements", self.model)

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=[system_message, user_message],
            tools=tools,
            tool_choice=tool_choice,
        )

        response_dict = completion.model_dump()

        usage = None
        if getattr(completion, "usage", None) is not None:
            usage = completion.usage.model_dump()

        return {
            "response": response_dict,
            "model": completion.model,
            "usage": usage,
        }

    def call_semantic_check(
        self,
        pairs_payload: List[Dict[str, Any]],
        *,
        trace_id: Optional[str] = None,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        """Run a small semantic contradiction check over suspicious pairs.

        This uses a lightweight prompt that asks the model for a JSON array of
        {pair_id, conflict, reason, confidence} objects.
        """

        if not pairs_payload:
            return {"response": [], "model": self.model, "usage": None}

        context_text = pairs_payload[0].get("context") or ""

        lines: List[str] = []
        if context_text:
            lines.append(f"Context: {context_text}")
        else:
            lines.append("Context: (not provided)")
        lines.append("")
        lines.append("Pairs:")

        for idx, pair in enumerate(pairs_payload, start=1):
            pair_id = pair.get("pair_id", f"p-{idx}")
            field_a = pair.get("field_a", "A")
            text_a = pair.get("text_a", "")
            field_b = pair.get("field_b", "B")
            text_b = pair.get("text_b", "")

            lines.append(f"{idx}) pair_id: {pair_id}")
            lines.append(f"   A ({field_a}): \"{text_a}\"")
            lines.append(f"   B ({field_b}): \"{text_b}\"")
            lines.append("")

        system_message = {
            "role": "system",
            "content": _PROMPT_SEMANTIC_TEMPLATE.format(model_name=self.model),
        }

        user_message = {
            "role": "user",
            "content": "\n".join(lines),
        }

        logger.debug(
            "Calling OpenAI %s for semantic contradiction check on %d pairs",
            self.model,
            len(pairs_payload),
        )

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=[system_message, user_message],
            max_tokens=max_tokens,
            temperature=0,
        )

        response_dict = completion.model_dump()

        usage = None
        if getattr(completion, "usage", None) is not None:
            usage = completion.usage.model_dump()

        return {
            "response": response_dict,
            "model": completion.model,
            "usage": usage,
        }


class MockAdapter:
    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("FINALIZE_MODEL", "gpt-5-nano")

    def call(
        self,
        raw_requirement_text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = context or {}

        function_args: Dict[str, Any] = {
            "title": (raw_requirement_text or "Draft requirements")[:80],
            "summary": (raw_requirement_text or "").strip()[:200] or "No requirements text provided.",
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
            "meta": {
                "prompt_version": "v1",
                "model": self.model,
                "timestamp": "1970-01-01T00:00:00Z",
                "trace_id": trace_id or "mock-trace",
                "schema_version": "v1",
                "repair_attempted": False,
                "token_usage": 0,
            },
        }

        completion_payload: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "finalize_requirements",
                                    "arguments": json.dumps(function_args),
                                }
                            }
                        ]
                    }
                }
            ]
        }

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        return {
            "response": completion_payload,
            "model": self.model,
            "usage": usage,
        }

    def call_semantic_check(
        self,
        pairs_payload: List[Dict[str, Any]],
        *,
        trace_id: Optional[str] = None,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        """Mock semantic contradiction check returning no conflicts.

        Tests that care about the exact semantic behavior should patch
        ``client.call_semantic_check`` directly.
        """

        results: List[Dict[str, Any]] = []
        for idx, pair in enumerate(pairs_payload, start=1):
            pair_id = pair.get("pair_id", f"p-{idx}")
            results.append(
                {
                    "pair_id": pair_id,
                    "conflict": False,
                    "reason": "mock: no conflict",
                    "confidence": 0.0,
                }
            )

        completion_payload: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(results),
                    }
                }
            ]
        }

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        return {
            "response": completion_payload,
            "model": self.model,
            "usage": usage,
        }


class FinalizeClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None) -> None:
        provider_name = provider or os.getenv("FINALIZE_PROVIDER", "openai")
        model_name = model or os.getenv("FINALIZE_MODEL", "gpt-5-nano")

        self.provider = provider_name
        self.model = model_name

        if provider_name == "openai":
            self._adapter = OpenAIAdapter(model=model_name)
        elif provider_name == "mock":
            self._adapter = MockAdapter(model=model_name)
        else:
            raise ValueError(f"Unsupported finalize_requirements provider: {provider_name}")

    def call(
        self,
        raw_requirement_text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._adapter.call(
            raw_requirement_text,
            context=context,
            trace_id=trace_id,
        )

    def call_semantic_check(
        self,
        pairs_payload: List[Dict[str, Any]],
        *,
        trace_id: Optional[str] = None,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        return self._adapter.call_semantic_check(
            pairs_payload,
            trace_id=trace_id,
            max_tokens=max_tokens,
        )


_DEFAULT_CLIENT = FinalizeClient()


def call_finalize_requirements(
    raw_requirement_text: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    temperature: float = 1.0,
) -> Dict[str, Any]:
    return _DEFAULT_CLIENT.call(
        raw_requirement_text,
        context=context,
        trace_id=trace_id,
    )


def call_semantic_check(
    pairs_payload: List[Dict[str, Any]],
    trace_id: Optional[str] = None,
    *,
    model: Optional[str] = None,
    max_tokens: int = 256,
) -> Dict[str, Any]:
    """Public API for semantic contradiction checks.

    The ``model`` argument is currently ignored; the configured
    ``FINALIZE_MODEL`` is used instead, keeping behavior consistent with the
    main finalize_requirements call. Tests may patch this function directly.
    """

    # For now, reuse the default client; if different models are needed for
    # semantic checks, this function can be extended to construct a dedicated
    # client instance.
    return _DEFAULT_CLIENT.call_semantic_check(
        pairs_payload,
        trace_id=trace_id,
        max_tokens=max_tokens,
    )
