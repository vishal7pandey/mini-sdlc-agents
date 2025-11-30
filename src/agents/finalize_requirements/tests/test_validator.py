"""Tests for the finalize_requirements.validator module."""

import unittest

from src.agents.finalize_requirements.models import Requirements
from src.agents.finalize_requirements.validator import validate_and_normalize


class TestValidator(unittest.TestCase):
    def test_validate_happy_payload(self) -> None:
        """Happy path: payload conforms and is normalized."""

        payload = {
            "title": "CLI Todo App (in-memory)",
            "summary": "A simple CLI todo app.",
            "stakeholders": ["product", "end-user"],
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "description": "Add creates a task visible in list",
                    "priority": "URGENT",
                    "type": "functional",
                }
            ],
            "functional_requirements": [
                {
                    "id": "FR-1",
                    "description": "User can add items via CLI.",
                    "priority": "high",
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-1",
                    "description": "Startup in under 1 second.",
                    "metric": "startup_seconds",
                    "target": 1,
                }
            ],
            "dependencies": ["python>=3.11"],
            "constraints": ["no external network"],
            "clarifications": [],
            "confidence": 0.9,
            "meta": {
                "prompt_version": "v1",
                "model": "gpt-4o",
                "timestamp": "2025-11-30T08:00:00Z",
                "trace_id": "trace-happy",
                "schema_version": "v1",
                "repair_attempted": False,
            },
        }

        req, errors = validate_and_normalize(payload)

        self.assertEqual(errors, [])
        self.assertIsInstance(req, Requirements)
        # Priority should be normalized
        self.assertEqual(req.acceptance_criteria[0].priority, "high")
        # Metric should be canonicalized
        self.assertEqual(
            req.non_functional_requirements[0].metric,
            "startup_s",
        )

    def test_validate_missing_required(self) -> None:
        """Missing required fields should yield human-friendly errors."""

        payload = {
            # title is present, but summary and acceptance_criteria are missing
            "title": "Incomplete payload",
            "functional_requirements": [],
            "confidence": 0.5,
            "meta": {
                "prompt_version": "v1",
                "model": "gpt-4o",
                "timestamp": "2025-11-30T08:00:00Z",
                "trace_id": "trace-missing",
                "schema_version": "v1",
                "repair_attempted": False,
            },
        }

        req, errors = validate_and_normalize(payload)

        self.assertIsNone(req)
        joined = "\n".join(errors)
        self.assertIn("summary", joined)
        self.assertIn("acceptance_criteria", joined)

    def test_validation_trim_and_dedup(self) -> None:
        """Long strings are trimmed and list fields deduplicated."""

        long_title = "A" * 500
        payload = {
            "title": long_title,
            "summary": "B" * 500,
            "stakeholders": ["product", "product", "infra"],
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "description": "desc",
                    "priority": "high",
                    "type": "functional",
                }
            ],
            "functional_requirements": [],
            "dependencies": ["postgres", "postgres", "redis"],
            "confidence": 0.8,
            "meta": {
                "prompt_version": "v1",
                "model": "gpt-4o",
                "timestamp": "2025-11-30T08:00:00Z",
                "trace_id": "trace-trim",
                "schema_version": "v1",
                "repair_attempted": False,
            },
        }

        req, errors = validate_and_normalize(payload)

        self.assertEqual(errors, [])
        assert req is not None

        self.assertLessEqual(len(req.title), 200)
        self.assertLessEqual(len(req.summary), 200)
        # Deduplication while preserving order
        self.assertEqual(req.stakeholders, ["product", "infra"])
        self.assertEqual(req.dependencies, ["postgres", "redis"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
