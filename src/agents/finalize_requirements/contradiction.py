"""Contradiction detection helpers for finalize_requirements.

Task 1: stub only. Later this module will:
- Apply deterministic contradiction rules (e.g., stateless vs session).
- Optionally call an LLM for semantic re-checks (in a later iteration).
"""
from __future__ import annotations

import string
from typing import Dict, List, Optional, Sequence, Tuple

from .models import Contradiction, ContradictionIssue, Requirements


_PUNCT_TO_SPACE = str.maketrans({ch: " " for ch in string.punctuation})

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


def _fields_with_token(sources: Sequence[Tuple[str, str, List[str]]], token: str) -> List[str]:
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
                issues.append(ContradictionIssue(field=field_ref, explanation=explanation))

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
