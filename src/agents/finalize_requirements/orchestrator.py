"""Orchestration entrypoint for the finalize_requirements agent.

Task 1: structure-only stub. Later this will:
- Call the LLM client (once implemented) to get a raw payload.
- Use `validator.validate_and_normalize` to enforce the contract.
- Run contradiction detection and compute a FinalizeResult.
"""
from typing import Any, Dict, Optional

from .models import FinalizeResult


def run_finalize(raw_requirement_text: str, context: Optional[Dict[str, Any]] = None) -> FinalizeResult:
    """Run the finalize_requirements pipeline on raw text.

    For now this is a stub that defines the public interface only.
    Implementation will be added in a later task.
    """
    raise NotImplementedError("run_finalize is not implemented yet.")
