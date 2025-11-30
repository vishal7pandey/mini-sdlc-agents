"""Unit tests for Pydantic models and helpers in finalize_requirements.models."""

import unittest

from src.agents.finalize_requirements.models import (
    AcceptanceCriteria,
    Requirements,
    compute_requirements_id,
    normalize_priority,
)


class TestModelsPriorityAndId(unittest.TestCase):
    def test_models_priority_normalize(self) -> None:
        # High-like values
        self.assertEqual(normalize_priority("urgent"), "high")
        self.assertEqual(normalize_priority("HIGH"), "high")
        self.assertEqual(AcceptanceCriteria.normalize_priority("p0"), "high")

        # Medium-like values
        self.assertEqual(normalize_priority("med"), "medium")
        self.assertEqual(normalize_priority("normal"), "medium")

        # Low-like values
        self.assertEqual(normalize_priority("low"), "low")
        self.assertEqual(normalize_priority("minor issue"), "low")

    def test_models_id_generation(self) -> None:
        payload = {
            "title": "CLI Todo App (in-memory)",
            "summary": "A simple CLI todo app.",
            "acceptance_criteria": [],
            "functional_requirements": [],
            "confidence": 0.9,
            "meta": {
                "prompt_version": "v1",
                "model": "gpt-4o",
                "timestamp": "2025-11-30T08:00:00Z",
                "trace_id": "trace-123",
                "schema_version": "v1",
                "repair_attempted": False,
            },
        }

        id1 = compute_requirements_id(payload, trace_id="trace-123")
        id2 = compute_requirements_id(payload, trace_id="trace-123")
        id3 = compute_requirements_id(payload, trace_id="trace-xyz")

        self.assertTrue(id1.startswith("req-"))
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

        # Ensure Requirements.normalize uses the same helper when id is missing.
        req = Requirements.normalize(payload, trace_id="trace-abc")
        self.assertTrue(req.id.startswith("req-"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
