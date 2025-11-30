# mini-sdlc-agents

A minimal SDLC agent pipeline focused (for now) on the
`finalize_requirements` agent: turning raw requirements text into a
validated, contradiction-checked requirements object.

## Goals

- Capture a clear, composable agent pipeline for software delivery.
- Keep the orchestrator lightweight and framework-agnostic.
- Make prompts, schemas, and runbooks explicit and versioned.

## Getting Started

For a complete, copy-paste friendly setup guide (Python/uv, `.env`, tests,
optional Docker and CI), see:

- `docs/SETUP.md`

Quick start (Unix-like shells):

1. Clone and install deps:
   - `git clone <YOUR-REPO-URL> mini-sdlc-agents`
   - `cd mini-sdlc-agents`
   - `uv sync`
2. Create and fill your environment file:
   - `cp .env.sample .env`
   - Edit `.env` and set `OPENAI_API_KEY`, `FINALIZE_MODEL`, etc.
3. Run tests and a local smoke:
   - `uv run python -m pytest`
   - `uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm`

See `docs/agents.md` and `docs/runbooks.md` for more details on how the
`finalize_requirements` agent and orchestrator are intended to be used.
