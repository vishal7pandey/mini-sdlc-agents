"""Contradiction detection helpers for finalize_requirements.

Task 1: stub only. Later this module will:
- Apply deterministic contradiction rules (e.g., stateless vs session).
- Optionally call an LLM for semantic re-checks (in a later iteration).
"""
from typing import Optional

from .models import Requirements


def detect_contradictions(requirements: Requirements) -> Optional[dict]:
    """Analyze requirements and return a contradiction object or None.

    The returned object will match the `contradiction` shape in `schema.json`.
    """
    raise NotImplementedError("detect_contradictions is not implemented yet.")
