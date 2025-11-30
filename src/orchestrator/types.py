"""Lightweight data models for orchestrator inputs/outputs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FinalizeRequirementsOutput:
    summary: str
    clarified_requirements: List[str]
    assumptions: List[str]
    open_questions: List[str]


@dataclass
class GenerateDesignOutput:
    system_context: str
    architecture_decisions: List[Dict[str, Any]]
    components: List[Dict[str, Any]]


@dataclass
class PlanForCodingOutput:
    milestones: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    risks: List[str]


@dataclass
class WriteCodeOutput:
    files: List[Dict[str, Any]]
    notes: List[str]


@dataclass
class WriteTestsOutput:
    test_files: List[Dict[str, Any]]
    coverage_goals: List[str]
    gaps: List[str]


@dataclass
class PipelineContext:
    """Container for all artifacts that flow through the pipeline."""

    raw_requirements: str
    finalized: Optional[FinalizeRequirementsOutput] = None
    design: Optional[GenerateDesignOutput] = None
    plan: Optional[PlanForCodingOutput] = None
    code: Optional[WriteCodeOutput] = None
    tests: Optional[WriteTestsOutput] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
