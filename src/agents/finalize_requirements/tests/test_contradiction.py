"""Tests for deterministic contradiction detection in contradiction.py."""

import unittest

from src.agents.finalize_requirements.contradiction import detect_contradictions
from src.agents.finalize_requirements.models import Requirements


def _base_payload() -> dict:
    """Return a minimal payload that satisfies required fields."""

    return {
        "title": "Example requirements",
        "summary": "Example summary",
        "acceptance_criteria": [],
        "functional_requirements": [],
        "confidence": 0.9,
        "meta": {
            "prompt_version": "v1",
            "model": "gpt-5-nano",
            "timestamp": "2025-11-30T08:00:00Z",
            "trace_id": "trace-base",
            "schema_version": "v1",
            "repair_attempted": False,
        },
    }


class TestContradictionDetection(unittest.TestCase):
    def test_detect_contradictions_stateless_session(self) -> None:
        """Detect stateless vs session contradiction across fields."""

        payload = _base_payload()
        payload.update(
            {
                "non_goals": ["Service must remain stateless"],
                "functional_requirements": [
                    {
                        "id": "FR-1",
                        "description": "Maintain user sessions in a session store.",
                        "priority": "high",
                    }
                ],
            }
        )

        req = Requirements.normalize(payload, trace_id="trace-contradiction")
        contradiction = detect_contradictions(req)

        self.assertIsNotNone(contradiction)
        assert contradiction is not None
        self.assertTrue(contradiction.flag)
        self.assertGreaterEqual(len(contradiction.issues), 1)

        explanations = "\n".join(issue.explanation for issue in contradiction.issues)
        self.assertIn("stateless", explanations)
        self.assertIn("session", explanations)

    def test_no_contradictions_happy_case(self) -> None:
        """A simple happy case should produce no contradictions."""

        payload = _base_payload()
        payload.update(
            {
                "functional_requirements": [
                    {
                        "id": "FR-1",
                        "description": "User can add items via CLI.",
                        "priority": "high",
                    }
                ],
                "non_goals": ["No multi-tenant support in v1"],
                "dependencies": ["python>=3.11"],
            }
        )

        req = Requirements.normalize(payload, trace_id="trace-happy")
        contradiction = detect_contradictions(req)

        self.assertIsNone(contradiction)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
