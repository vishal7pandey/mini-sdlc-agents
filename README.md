# mini-sdlc-agents

High-level scaffold for a small SDLC agent pipeline (requirements → design → plan → code → tests).

This repo currently contains **structure only** (no real implementation yet). It is intended to evolve incrementally.

## Goals

- Capture a clear, composable agent pipeline for software delivery.
- Keep the orchestrator lightweight and framework-agnostic at first.
- Make prompts, schemas, and runbooks explicit and versioned.

## Getting Started (very early stage)

1. Create a virtualenv (optional but recommended):
   - `python -m venv .venv`
   - Activate it per your OS.
2. Install dependencies (none are required yet, this will evolve):
   - `pip install -r requirements.txt`
3. Explore the structure:
   - `docs/` for architecture, agents, and runbooks.
   - `src/` for orchestrator glue, agents, adapters, and utils.
   - `examples/` for sample inputs/outputs.

No CLIs or libraries are exposed yet; this is an **architecture + prompts + schemas** starting point.
