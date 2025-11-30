"""Contradiction detection helpers for finalize_requirements.

Task 1: stub only. Later this module will:
- Apply deterministic contradiction rules (e.g., stateless vs session).
- Optionally call an LLM for semantic re-checks (in a later iteration).
"""

from __future__ import annotations

import json
import logging
import os
import string
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import client
from .models import Contradiction, ContradictionIssue, Requirements


_PUNCT_TO_SPACE = str.maketrans({ch: " " for ch in string.punctuation})

logger = logging.getLogger(__name__)

_SYNONYMS: Dict[str, str] = {
    "db": "database",
    "database": "database",
    "databases": "database",
    "session": "session",
    "sessions": "session",
}


def _normalize_text(text: str) -> str:
    """Lowercase and replace punctuation with spaces, squashing runs of spaces."""

    lowered = (text or "").lower()
    no_punct = lowered.translate(_PUNCT_TO_SPACE)
    return " ".join(no_punct.split())


def _tokenize(text: str) -> List[str]:
    """Tokenize normalized text and apply simple synonym mapping."""

    norm = _normalize_text(text)
    raw_tokens = norm.split()
    return [_SYNONYMS.get(tok, tok) for tok in raw_tokens]


def _collect_sources(req: Requirements) -> List[Tuple[str, str, List[str]]]:
    """Collect textual sources from the requirements for rule evaluation.

    Returns a list of ``(field_path, normalized_text, tokens)``.
    """

    sources: List[Tuple[str, str, List[str]]] = []

    def add(field: str, text: Optional[str]) -> None:
        if not text:
            return
        norm = _normalize_text(text)
        tokens = _tokenize(text)
        sources.append((field, norm, tokens))

    add("title", req.title)
    add("summary", req.summary)

    for idx, value in enumerate(req.non_goals):
        add(f"non_goals[{idx}]", value)
    for idx, value in enumerate(req.dependencies):
        add(f"dependencies[{idx}]", value)
    for idx, value in enumerate(req.constraints):
        add(f"constraints[{idx}]", value)

    for idx, fr in enumerate(req.functional_requirements):
        add(f"functional_requirements[{idx}].description", fr.description)
        if fr.rationale:
            add(f"functional_requirements[{idx}].rationale", fr.rationale)

    for idx, nfr in enumerate(req.non_functional_requirements):
        add(f"non_functional_requirements[{idx}].description", nfr.description)

    return sources


def _fields_with_token(
    sources: Sequence[Tuple[str, str, List[str]]], token: str
) -> List[str]:
    fields: List[str] = []
    for field, _norm, tokens in sources:
        if token in tokens:
            fields.append(field)
    return fields


def _rule_stateless_vs_session(
    sources: Sequence[Tuple[str, str, List[str]]],
) -> List[ContradictionIssue]:
    """Detect contradictions between 'stateless' and 'session' concepts."""

    issues: List[ContradictionIssue] = []
    stateless_fields = _fields_with_token(sources, "stateless")
    session_fields = _fields_with_token(sources, "session")

    if stateless_fields and session_fields:
        field_ref = f"{stateless_fields[0]} & {session_fields[0]}"
        explanation = (
            "Requirements mention 'stateless' but also refer to 'session' or "
            "session state, which implies stateful behavior."
        )
        issues.append(ContradictionIssue(field=field_ref, explanation=explanation))

    return issues


def _has_no_db(normalized_text: str) -> bool:
    return "no db" in normalized_text or "no database" in normalized_text


def _has_persistence(normalized_text: str) -> bool:
    return (
        "persistence" in normalized_text
        or "persistent" in normalized_text
        or "store data" in normalized_text
        or "database" in normalized_text
    )


def _rule_no_db_vs_persistence(
    sources: Sequence[Tuple[str, str, List[str]]],
) -> List[ContradictionIssue]:
    issues: List[ContradictionIssue] = []
    no_db_fields: List[str] = []
    persistence_fields: List[str] = []

    for field, norm, _tokens in sources:
        if _has_no_db(norm):
            no_db_fields.append(field)
        if _has_persistence(norm):
            persistence_fields.append(field)

    if no_db_fields and persistence_fields:
        field_ref = f"{no_db_fields[0]} & {persistence_fields[0]}"
        explanation = (
            "Requirements state there should be no database but also imply "
            "data persistence or database usage."
        )
        issues.append(ContradictionIssue(field=field_ref, explanation=explanation))

    return issues


def _has_single_user(normalized_text: str) -> bool:
    return "single user" in normalized_text


def _has_multi_tenant(normalized_text: str) -> bool:
    return "multi tenant" in normalized_text or "multitenant" in normalized_text


def _rule_single_user_vs_multi_tenant(
    sources: Sequence[Tuple[str, str, List[str]]],
) -> List[ContradictionIssue]:
    issues: List[ContradictionIssue] = []
    single_fields: List[str] = []
    multi_fields: List[str] = []

    for field, norm, _tokens in sources:
        if _has_single_user(norm):
            single_fields.append(field)
        if _has_multi_tenant(norm):
            multi_fields.append(field)

    if single_fields and multi_fields:
        field_ref = f"{single_fields[0]} & {multi_fields[0]}"
        explanation = (
            "Requirements describe both single-user and multi-tenant behavior, "
            "which are typically mutually exclusive deployment models."
        )
        issues.append(ContradictionIssue(field=field_ref, explanation=explanation))

    return issues


def _has_no_external_network(normalized_text: str) -> bool:
    return (
        "no external network" in normalized_text
        or "no external access" in normalized_text
        or "offline only" in normalized_text
    )


def _has_external_api(normalized_text: str) -> bool:
    return "external api" in normalized_text or "third party api" in normalized_text


def _rule_no_external_vs_external_api(
    sources: Sequence[Tuple[str, str, List[str]]],
) -> List[ContradictionIssue]:
    issues: List[ContradictionIssue] = []
    no_ext_fields: List[str] = []
    api_fields: List[str] = []

    for field, norm, _tokens in sources:
        if _has_no_external_network(norm):
            no_ext_fields.append(field)
        if _has_external_api(norm):
            api_fields.append(field)

    if no_ext_fields and api_fields:
        field_ref = f"{no_ext_fields[0]} & {api_fields[0]}"
        explanation = (
            "Requirements forbid external network access but also reference "
            "an external API, which requires such access."
        )
        issues.append(ContradictionIssue(field=field_ref, explanation=explanation))

    return issues


def _rule_non_goals_vs_dependencies(req: Requirements) -> List[ContradictionIssue]:
    """Detect when a non-goal string matches a dependency string."""

    issues: List[ContradictionIssue] = []

    normalized_non_goals = [
        (_normalize_text(value), f"non_goals[{idx}]")
        for idx, value in enumerate(req.non_goals)
        if value
    ]
    normalized_deps = [
        (_normalize_text(value), f"dependencies[{idx}]")
        for idx, value in enumerate(req.dependencies)
        if value
    ]

    for ng_text, ng_field in normalized_non_goals:
        for dep_text, dep_field in normalized_deps:
            if ng_text and dep_text and ng_text == dep_text:
                field_ref = f"{ng_field} & {dep_field}"
                explanation = (
                    "An item appears both as a non-goal and as a dependency, "
                    "which is contradictory."
                )
                issues.append(
                    ContradictionIssue(field=field_ref, explanation=explanation)
                )

    return issues


def detect_contradictions(requirements: Requirements) -> Optional[Contradiction]:
    """Analyze requirements and return a Contradiction or None.

    This is a deterministic first pass that looks for obvious textual
    contradictions using simple string rules and synonyms. No LLM calls are
    performed here.
    """

    sources = _collect_sources(requirements)

    issues: List[ContradictionIssue] = []
    issues.extend(_rule_stateless_vs_session(sources))
    issues.extend(_rule_no_db_vs_persistence(sources))
    issues.extend(_rule_single_user_vs_multi_tenant(sources))
    issues.extend(_rule_no_external_vs_external_api(sources))
    issues.extend(_rule_non_goals_vs_dependencies(requirements))

    if not issues:
        return None

    return Contradiction(flag=True, issues=issues)


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


def _get_env_int(name: str) -> Optional[int]:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:  # pragma: no cover - defensive
        return None


def _get_env_float(name: str) -> Optional[float]:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:  # pragma: no cover - defensive
        return None


def _estimate_cost_usd(usage: Optional[Dict[str, Any]]) -> Optional[float]:
    """Estimate cost in USD from token usage and env-configured prices.

    This mirrors the logic in the orchestrator but is kept local here to avoid
    circular imports.
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

    input_price = _get_env_float("FINALIZE_INPUT_PRICE_PER_MTOKENS") or 0.0
    output_price = _get_env_float("FINALIZE_OUTPUT_PRICE_PER_MTOKENS") or 0.0

    if input_price <= 0.0 and output_price <= 0.0:
        return None

    cost = prompt_tokens * (input_price / 1_000_000.0) + completion_tokens * (
        output_price / 1_000_000.0
    )
    return round(cost, 8)


def _merge_usage(
    base: Optional[Dict[str, Any]], extra: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    if extra is None:
        return base
    if base is None:
        return dict(extra)

    merged = dict(base)
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        try:
            merged[key] = int(base.get(key, 0) or 0) + int(extra.get(key, 0) or 0)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            merged[key] = base.get(key) or extra.get(key)
    return merged


def _extract_semantic_results(raw_response: Any) -> List[Dict[str, Any]]:
    """Extract a list of semantic contradiction results from a raw response.

    Supports both direct JSON (list of dicts) and OpenAI chat completions where
    the JSON is stored in ``choices[0].message.content``.
    """

    # If the response is already a list of dicts, return it directly.
    if isinstance(raw_response, list):
        return [item for item in raw_response if isinstance(item, dict)]

    if not isinstance(raw_response, dict):
        return []

    choices = raw_response.get("choices") or []
    if not choices:
        return []

    message = choices[0].get("message") or {}
    content = message.get("content")

    text: str
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        # Handle the newer "content" list shape; gather text segments.
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                value = part.get("text") or part.get("value") or ""
                if isinstance(value, str):
                    parts.append(value)
        text = "".join(parts).strip()
    else:
        return []

    if not text:
        return []

    last_error: Optional[Exception] = None

    # First attempt: direct JSON parse.
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            return [item for item in data["results"] if isinstance(item, dict)]
    except json.JSONDecodeError as exc:
        last_error = exc

    # Fallback: try to extract the first JSON array substring.
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            data = json.loads(snippet)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            last_error = exc
            logger.debug(
                "Failed to parse semantic JSON array from snippet: %s", snippet[:200]
            )

    if last_error is not None:
        # Signal malformed JSON to the caller so it can be surfaced in meta.
        raise ValueError(
            f"Failed to parse semantic contradiction JSON response: {last_error}"
        ) from last_error

    return []


def semantic_check(
    requirements: Requirements,
    suspicious_pairs: List[Dict[str, str]],
    trace_id: Optional[str] = None,
    *,
    max_pairs: int = 5,
    timeout_s: int = 8,
) -> Tuple[List[ContradictionIssue], Dict[str, Any]]:
    """Confirm/dismiss contradiction candidates with the LLM.

    Returns (issues_confirmed, meta) where meta contains model, usage,
    elapsed_ms, pairs_checked, pairs_confirmed, status, and optional error.
    """

    meta: Dict[str, Any] = {
        "model": None,
        "usage": None,
        "pairs_checked": 0,
        "pairs_confirmed": 0,
        "elapsed_ms": 0,
        "status": "skipped" if not suspicious_pairs else "pending",
    }

    if not suspicious_pairs:
        return [], meta

    enabled = _get_env_bool("FINALIZE_SEMANTIC_CONTRADICTION_ENABLED", True)
    if not enabled:
        meta["status"] = "disabled"
        meta["skipped_due_to_config"] = True
        return [], meta

    max_pairs_env = _get_env_int("FINALIZE_SEMANTIC_CONTRADICTION_MAX_PAIRS")
    if max_pairs_env and max_pairs_env > 0:
        max_pairs = max_pairs_env

    max_tokens_env = _get_env_int("FINALIZE_SEMANTIC_CONTRADICTION_MAX_TOKENS")
    max_tokens = max_tokens_env or 256

    start = time.perf_counter()

    confirmed_issues: List[ContradictionIssue] = []
    aggregated_usage: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    total_pairs_checked = 0
    confirmed_count = 0
    raw_excerpt: Optional[str] = None

    try:
        for offset in range(0, len(suspicious_pairs), max_pairs):
            batch = suspicious_pairs[offset : offset + max_pairs]
            if not batch:
                continue

            total_pairs_checked += len(batch)

            result = client.call_semantic_check(
                batch,
                trace_id=trace_id,
                max_tokens=max_tokens,
            )

            if model_name is None:
                model_name = result.get("model")

            usage = result.get("usage")
            if isinstance(usage, dict):
                aggregated_usage = _merge_usage(aggregated_usage, usage)

            raw_response = result.get("response")
            if raw_excerpt is None:
                raw_excerpt = str(raw_response)[:400]

            results = _extract_semantic_results(raw_response)

            pair_index = {str(p.get("pair_id")): p for p in batch}

            for item in results:
                pair_id = str(item.get("pair_id", ""))
                conflict = bool(item.get("conflict"))
                if not conflict:
                    continue

                pair = pair_index.get(pair_id)
                if not pair:
                    continue

                field_a = pair.get("field_a", "A")
                field_b = pair.get("field_b", "B")
                field_ref = f"{field_a} & {field_b}".strip()
                reason = str(
                    item.get("reason") or "Semantic contradiction between A and B."
                )

                confirmed_issues.append(
                    ContradictionIssue(field=field_ref, explanation=reason)
                )
                confirmed_count += 1

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        meta["model"] = model_name
        meta["usage"] = aggregated_usage
        meta["pairs_checked"] = total_pairs_checked
        meta["pairs_confirmed"] = confirmed_count
        meta["elapsed_ms"] = elapsed_ms
        meta["raw_response_excerpt"] = raw_excerpt

        cost_estimate = _estimate_cost_usd(aggregated_usage)
        if cost_estimate is not None:
            meta["cost_estimate_usd"] = cost_estimate
            cutoff = _get_env_float("FINALIZE_SINGLE_CALL_COST_ALERT_USD")
            if cutoff is not None and cutoff > 0.0 and cost_estimate > cutoff:
                # Treat as unresolved due to cost; do not flip to conflict.
                meta["skipped_due_to_cost"] = True
                meta["status"] = "failed"
                return [], meta

        meta["status"] = "ok"
        return confirmed_issues, meta
    except Exception as exc:  # pragma: no cover - defensive
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        meta["status"] = "failed"
        meta["error"] = str(exc)
        meta["elapsed_ms"] = elapsed_ms
        meta["model"] = model_name
        meta["usage"] = aggregated_usage
        meta["pairs_checked"] = total_pairs_checked
        meta["pairs_confirmed"] = confirmed_count
        return [], meta
