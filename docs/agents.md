# Agents Overview

Each agent is defined by **two artifacts**:

- A canonical **prompt template** (`prompt.txt`).
- An **expected JSON output schema** (`schema.json`).

All agents should:

- Produce **valid JSON only** (no extra text).
- Conform to their schema so the orchestrator can validate and chain outputs.

---

## finalize_requirements

- **Goal**: Normalize and clarify raw user requirements.
- **Input**: Free-form problem statement from the user.
- **Output (summary)**:
  - `summary`: short text summary.
  - `clarified_requirements`: list of concrete requirements.
  - `assumptions`: list of explicit assumptions.
  - `open_questions`: questions for the user when requirements are ambiguous.

## generate_design

- **Goal**: Produce a lightweight technical design.
- **Input**: Clarified requirements from `finalize_requirements`.
- **Output (summary)**:
  - `system_context`: high-level description of the system.
  - `architecture_decisions`: list of design choices and trade-offs.
  - `components`: list of components with responsibilities and interfaces.

## plan_for_coding

- **Goal**: Turn design into an actionable implementation plan.
- **Input**: Design artifacts from `generate_design`.
- **Output (summary)**:
  - `milestones`: ordered milestones for implementation.
  - `tasks`: fine-grained tasks referencing files/modules.
  - `risks`: known risks and mitigation ideas.

## write_code

- **Goal**: Propose code artifacts consistent with the plan.
- **Input**: Plan from `plan_for_coding`.
- **Output (summary)**:
  - `files`: list of files with paths, descriptions, and code content.
  - `notes`: constraints and follow-up actions for a human to review.

## write_tests

- **Goal**: Propose tests aligned with requirements and code.
- **Input**: Requirements + plan + proposed code.
- **Output (summary)**:
  - `test_files`: test code artifacts.
  - `coverage_goals`: what behaviors and edge cases are covered.
  - `gaps`: known gaps or tests left for humans.
