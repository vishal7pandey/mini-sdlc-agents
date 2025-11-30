"""Validation and normalization helpers for finalize_requirements.

Task 1: stub signatures only. Later tasks will:
- Validate raw payloads against `schema.json` / models.
- Normalize priorities, metrics, and other fields.
"""
from typing import Any, Dict, List, Tuple, Optional

from .models import Requirements


def validate_and_normalize(payload: Dict[str, Any]) -> Tuple[Optional[Requirements], List[str]]:
    """Validate and normalize a raw requirements payload.

    For now this is a stub. Later it will:
    - Enforce the JSON schema / Pydantic model.
    - Apply normalization rules (priorities, metrics, deduping, etc.).
    """
    raise NotImplementedError("validate_and_normalize is not implemented yet.")
