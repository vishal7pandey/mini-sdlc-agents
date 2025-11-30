.PHONY: install test smoke run-orch

install:
	uv sync

test:
	uv run python -m pytest -q

smoke:
	uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm

run-orch:
	uv run python - <<'PY'
from src.agents.finalize_requirements.orchestrator import run_finalize
import json

res = run_finalize("Build a todo CLI", use_llm=False)
print(json.dumps(res, indent=2))
PY
