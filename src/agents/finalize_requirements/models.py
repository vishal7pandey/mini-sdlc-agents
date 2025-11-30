"""Pydantic models for the finalize_requirements agent.

These models mirror ``schema.json`` and the design in ``01_code_plan.txt``.

They are deliberately **pure types**:
- no network calls
- normalization helpers only (for priorities, metrics, and IDs)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Union

from pydantic import BaseModel, Field


Priority = str  # normalized to "low" | "medium" | "high" by helpers


def normalize_priority(value: str) -> Priority:
    """Normalize a free-form priority string to ``low|medium|high``.

    Examples::

        normalize_priority("urgent") -> "high"
        normalize_priority("MED") -> "medium"
        normalize_priority("low priority") -> "low"
    """

    text = (value or "").strip().lower()

    if not text:
        return "medium"

    # Simple numeric mapping
    if text in {"1", "p0", "p1"}:
        return "high"
    if text in {"2", "p2"}:
        return "medium"
    if text in {"3", "4", "p3", "p4"}:
        return "low"

    # Keyword-based mapping
    high_markers = {"high", "urgent", "critical", "blocker", "highest"}
    low_markers = {"low", "minor", "trivial"}
    medium_markers = {"medium", "med", "normal"}

    if any(marker in text for marker in high_markers):
        return "high"
    if any(marker in text for marker in low_markers):
        return "low"
    if any(marker in text for marker in medium_markers):
        return "medium"

    # Default to medium when unclear.
    return "medium"


def canonicalize_metric(metric: str) -> str:
    """Return a canonical representation of a metric name.

    This keeps semantics simple for now:
    - trims whitespace
    - lowercases
    - normalizes a couple of common suffixes (``seconds``/``sec`` -> ``s``)
    """

    text = (metric or "").strip().lower()
    if not text:
        return ""

    if text.endswith("seconds"):
        return text[: -len("seconds")] + "s"
    if text.endswith("sec"):
        return text[: -len("sec")] + "s"
    return text


def compute_requirements_id(data: Mapping[str, Any], trace_id: Optional[str] = None) -> str:
    """Compute a deterministic requirements ID from normalized data + trace id.

    The ``data`` mapping is expected to be close to the final Requirements
    object, but this helper deliberately ignores ``id`` and ``meta`` keys so
    that IDs remain stable across re-computations.
    """

    # Shallow copy without self-referential fields.
    trimmed: Dict[str, Any] = {
        key: value
        for key, value in data.items()
        if key not in {"id", "meta"}
    }

    canonical = json.dumps(trimmed, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(canonical.encode("utf-8"))
    if trace_id:
        hasher.update(b"|")
        hasher.update(trace_id.encode("utf-8"))
    digest = hasher.hexdigest()[:10]
    return f"req-{digest}"


class AcceptanceCriteria(BaseModel):
    """Acceptance criteria for the feature or system.

    Priority will typically be normalized to ``low|medium|high`` using
    :func:`normalize_priority`.
    """

    id: str
    description: str
    priority: Priority = Field(..., description="low | medium | high")
    type: str = Field(..., description="functional | non-functional | regression")

    @classmethod
    def normalize_priority(cls, value: str) -> Priority:
        """Helper for tests and validators to normalize a priority value."""

        return normalize_priority(value)


class FunctionalRequirement(BaseModel):
    """Functional requirement describing behavior and rationale."""

    id: str
    description: str
    rationale: Optional[str] = None
    priority: Priority = Field(..., description="low | medium | high")

    @classmethod
    def normalize_priority(cls, value: str) -> Priority:
        return normalize_priority(value)


class NonFunctionalRequirement(BaseModel):
    """Non-functional requirement, usually with a metric and target."""

    id: str
    description: str
    metric: Optional[str] = None
    target: Optional[Union[int, float, str]] = None

    @classmethod
    def canonicalize_metric(cls, metric: str) -> str:
        """Normalize a metric label to a canonical form."""

        return canonicalize_metric(metric)


class Clarification(BaseModel):
    """Clarifying question the agent wants answered."""

    id: str
    question: str
    context: Optional[str] = None
    severity: str  # blocking | important | nice_to_have


class ContradictionIssue(BaseModel):
    """Single contradiction instance linking a field and explanation."""

    field: str
    explanation: str


class Contradiction(BaseModel):
    """Container for contradictions detected in the requirements."""

    flag: bool
    issues: List[ContradictionIssue]


class Meta(BaseModel):
    """Metadata about how the requirements were produced."""

    prompt_version: str
    model: str
    timestamp: datetime
    trace_id: str
    schema_version: str
    repair_attempted: bool
    token_usage: Optional[int] = None

    @classmethod
    def new(
        cls,
        *,
        prompt_version: str,
        schema_version: str,
        model: str,
        trace_id: str,
        repair_attempted: bool = False,
        token_usage: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ) -> "Meta":
        """Create a new Meta instance with sensible defaults.

        ``timestamp`` defaults to ``datetime.now(timezone.utc)``.
        """

        return cls(
            prompt_version=prompt_version,
            model=model,
            timestamp=timestamp or datetime.now(timezone.utc),
            trace_id=trace_id,
            schema_version=schema_version,
            repair_attempted=repair_attempted,
            token_usage=token_usage,
        )


class Requirements(BaseModel):
    """Canonical requirements object returned by the agent."""

    id: str
    title: str
    summary: str
    stakeholders: List[str] = []
    assumptions: List[str] = []
    non_goals: List[str] = []
    acceptance_criteria: List[AcceptanceCriteria] = []
    functional_requirements: List[FunctionalRequirement] = []
    non_functional_requirements: List[NonFunctionalRequirement] = []
    dependencies: List[str] = []
    constraints: List[str] = []
    clarifications: List[Clarification] = []
    contradiction: Optional[Contradiction] = None
    confidence: float
    meta: Meta

    @classmethod
    def normalize(
        cls,
        data: Mapping[str, Any],
        *,
        trace_id: Optional[str] = None,
    ) -> "Requirements":
        """Create a normalized ``Requirements`` instance from raw data.

        This helper:
        - normalizes priorities in acceptance_criteria and functional_requirements
        - canonicalizes metrics in non_functional_requirements
        - computes an ``id`` if one is not provided
        """

        # Shallow copy so we can mutate without affecting the caller.
        working: Dict[str, Any] = dict(data)

        ac_list = working.get("acceptance_criteria") or []
        normalized_ac = []
        for item in ac_list:
            if isinstance(item, AcceptanceCriteria):
                normalized_ac.append(
                    item.copy(
                        update={
                            "priority": normalize_priority(item.priority),
                        }
                    )
                )
            else:
                d = dict(item)
                d["priority"] = normalize_priority(str(d.get("priority", "")))
                normalized_ac.append(d)
        working["acceptance_criteria"] = normalized_ac

        fr_list = working.get("functional_requirements") or []
        normalized_fr = []
        for item in fr_list:
            if isinstance(item, FunctionalRequirement):
                normalized_fr.append(
                    item.copy(
                        update={
                            "priority": normalize_priority(item.priority),
                        }
                    )
                )
            else:
                d = dict(item)
                d["priority"] = normalize_priority(str(d.get("priority", "")))
                normalized_fr.append(d)
        working["functional_requirements"] = normalized_fr

        nfr_list = working.get("non_functional_requirements") or []
        normalized_nfr = []
        for item in nfr_list:
            if isinstance(item, NonFunctionalRequirement):
                normalized_nfr.append(
                    item.copy(
                        update={
                            "metric": canonicalize_metric(item.metric or ""),
                        }
                    )
                )
            else:
                d = dict(item)
                metric_value = str(d.get("metric", "")) if d.get("metric") is not None else ""
                d["metric"] = canonicalize_metric(metric_value)
                normalized_nfr.append(d)
        working["non_functional_requirements"] = normalized_nfr

        if "id" not in working or not working["id"]:
            working["id"] = compute_requirements_id(working, trace_id)

        return cls(**working)


class FinalizeResult(BaseModel):
    """Wrapper for the public result of ``run_finalize``."""

    status: str
    requirements: Optional[Requirements] = None
    errors: List[str] = []
    meta: Dict[str, Any] = {}

