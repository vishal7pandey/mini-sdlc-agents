# mini-sdlc-agents — Development Setup

This guide describes how to get a local development environment running for
`mini-sdlc-agents`, using **uv** for Python dependency management, optional
LangChain tooling, and Docker for containerized workflows.

The examples below assume a repo root of:
- Windows / PowerShell: `C:\Dev\mini-sdlc-agents`
- macOS / Linux: `~/Dev/mini-sdlc-agents`

Adjust paths and commands to match your system.

---

## 1. System prerequisites

You will need:

- Python **3.11+**
- **uv** (https://astral.sh/uv) v0.4+
- Git
- Docker & Docker Compose (optional, for container runs)
- Node.js 18+ (only if you later add a frontend; **not required now**)

### Install hints

**macOS (Homebrew)**

```bash
brew install python@3.11
brew install astral-sh/uv/uv
brew install --cask docker      # optional, for Docker Desktop
# Node only if you build a UI later
brew install node@18
```

**Ubuntu / WSL2**

```bash
# Python (example)
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git curl

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
python3 --version      # expect 3.11.x
uv --version
git --version
docker --version       # optional
```

On Windows, we recommend **WSL2** for a smoother Docker and tooling experience,
though PowerShell works fine for Python-only development.

---

## 2. Clone the repo

```bash
# macOS / Linux
mkdir -p ~/Dev
cd ~/Dev
git clone <YOUR-REPO-URL> mini-sdlc-agents
cd mini-sdlc-agents
```

```powershell
# Windows / PowerShell
New-Item -ItemType Directory -Force -Path C:\Dev | Out-Null
Set-Location C:\Dev
git clone <YOUR-REPO-URL> mini-sdlc-agents
Set-Location C:\Dev\mini-sdlc-agents
```

If the repo already exists, make sure you are on the right branch and up to
date:

```bash
git fetch --all --prune
git checkout main   # or the feature branch you are working on
git pull
```

(Configure your user details once per machine with `git config user.name` and
`git config user.email`.)

---

## 3. Project layout (quick view)

From the repo root you should see something like:

```text
mini-sdlc-agents/
├── pyproject.toml
├── uv.lock
├── .env.sample
├── .env              # local only; not committed
├── src/
│   └── agents/
│       └── finalize_requirements/
│           ├── client.py
│           ├── orchestrator.py
│           ├── validator.py
│           ├── contradiction.py
│           ├── models.py
│           ├── prompt.txt
│           ├── schema.json
│           └── tests/fixtures/...
├── tests/
├── scripts/
│   └── smoke_finalize.py
├── docs/
│   ├── SETUP.md
│   ├── agents.md
│   ├── architecture.md
│   └── runbooks.md
├── infra/
│   ├── Dockerfile.sample
│   └── docker-compose.sample.yml
├── ci/
│   └── pipeline.yaml.sample
├── Makefile           # convenience targets (install, test, smoke, run-orch)
└── .github/workflows/ci.yml   # GitHub Actions (if enabled)
```

The exact tree may evolve, but the above gives you the main entry points.

---

## 4. Python env + dependencies (uv)

This project is managed with **uv** and `pyproject.toml`.

From the repo root:

```bash
uv sync
```

This will:

- Create a `.venv/` virtualenv (by default).
- Install all dependencies defined in `pyproject.toml`.

### Activating the virtualenv

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Quick check:

```bash
python -c "import sys; print(sys.version)"
```

If you need to add a package, use `uv add` from the repo root. Example:

```bash
uv add "langsmith>=0.1,<0.3"
uv sync
```

(Those dependencies are already present in this branch.)

---

## 5. Environment variables — .env

The repo includes a **`.env.sample`** with all the relevant keys. To get
started:

```bash
cp .env.sample .env
```

Edit `.env` and fill in real values (especially keys). Key variables:

### LLM / finalize agent

```text
FINALIZE_PROVIDER=openai
FINALIZE_MODEL=gpt-5-nano
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1   # or your custom base
```

### Repair / cost / guardrails

```text
FINALIZE_INPUT_PRICE_PER_MTOKENS=0.10
FINALIZE_OUTPUT_PRICE_PER_MTOKENS=0.20
FINALIZE_SINGLE_CALL_COST_ALERT_USD=0.001
FINALIZE_MAX_INPUT_TOKENS=4000
FINALIZE_DAILY_TOKEN_QUOTA=20000
FINALIZE_COST_ALERT_USD=0.005
```

### Auto-assumptions

```text
FINALIZE_AUTOASSUME_ENABLED=true
FINALIZE_AUTOASSUME_CONFIDENCE_THRESHOLD=0.6
```

### Semantic contradiction

```text
FINALIZE_SEMANTIC_CONTRADICTION_ENABLED=true
FINALIZE_SEMANTIC_CONTRADICTION_MAX_PAIRS=5
FINALIZE_SEMANTIC_CONTRADICTION_MAX_TOKENS=256
```

### LangChain / LangSmith (optional)

```text
FINALIZE_USES_LANGCHAIN=true
FINALIZE_LANGCHAIN_MODEL=gpt-5-nano     # falls back to FINALIZE_MODEL if empty

FINALIZE_LANGSMITH_ENABLED=false        # leave false unless you really want traces
LANGSMITH_API_KEY=ls_...
LANGSMITH_API_BASE=
LANGSMITH_INCLUDE_RAW=false             # keep false by default
LANGSMITH_INCLUDE_SCHEMA=false
LANGSMITH_RAW_TRUNCATE=800

FINALIZE_LLM_MAX_RETRIES=2
FINALIZE_LLM_BACKOFF_BASE_S=0.5
FINALIZE_LLM_BACKOFF_MAX_S=4
```

### Dev server (future use)

These are placeholders for when/if you wire a FastAPI/HTTP surface:

```text
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
LOG_LEVEL=INFO
```

### Quick .env sanity check

With the venv active:

```bash
uv run python - <<'PY'
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
print("OPENAI key present:", bool(os.getenv("OPENAI_API_KEY")))
print("FINALIZE_MODEL:", os.getenv("FINALIZE_MODEL"))
PY
```

---

## 6. Run tests & smoke scripts

Run the full test suite:

```bash
uv run python -m pytest
```

Or target an individual test module, e.g. status auto-resolve:

```bash
uv run python -m pytest tests/test_status_autoresolve.py -q
```

### Smoke test script

There is a convenience script at `scripts/smoke_finalize.py`.

No-LLM path (fast, offline):

```bash
uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm
```

LLM path (calls OpenAI; ensure keys are set):

```bash
uv run python scripts/smoke_finalize.py "Build a todo CLI"
```

Both modes will print a JSON `FinalizeResult` to stdout and write a copy into
`runs/<trace_id>.json`.

---

## 7. Orchestrator / CLI usage

You can also call the orchestrator directly from Python.

No-LLM path (uses local stub):

```bash
uv run python - <<'PY'
from src.agents.finalize_requirements.orchestrator import run_finalize
import json

res = run_finalize("Make a CLI todo app", use_llm=False)
print(json.dumps(res, indent=2))
PY
```

This exercises validation, contradiction detection, and auto-assumptions
without hitting the network.

---

## 8. Docker (optional) — local container dev

This repo includes **sample** Docker assets under `infra/`:

- `infra/Dockerfile.sample`
- `infra/docker-compose.sample.yml`

A simple dev flow is:

```bash
cd infra
docker compose -f docker-compose.sample.yml up --build
```

This will:

- Build an image using `infra/Dockerfile.sample`.
- Mount the repo into `/app` inside the container.
- Drop you into a shell (`bash`) where you can run:

```bash
uv sync
uv run python -m pytest
uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm
```

These files are intentionally minimal and can be evolved as the project grows.

---

## 9. CI / GitHub Actions

A basic GitHub Actions workflow is provided at `.github/workflows/ci.yml` (see
repo). It:

- Checks out the code.
- Installs Python 3.11.
- Installs **uv**.
- Runs `uv sync`.
- Runs `uv run python -m pytest`.

Extend this to add lint (ruff/black) and type checking (mypy/pyright) as you
introduce those tools into `pyproject.toml`.

If you prefer another CI (GitLab, Azure, etc.), the `ci/pipeline.yaml.sample`
file shows a generic skeleton you can adapt.

---

## 10. Makefile shortcuts

For macOS/Linux devs, a small `Makefile` is provided with common tasks:

- `make install` → `uv sync`
- `make test` → `uv run python -m pytest -q`
- `make smoke` → `uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm`
- `make run-orch` → one-off orchestrator call with `use_llm=False`.

From the repo root:

```bash
make install
make test
make smoke
```

On Windows, you can either use `make` via WSL or just copy the uv commands.

---

## 11. Telemetry & LangSmith (optional)

If you set `FINALIZE_LANGSMITH_ENABLED=true` and provide a `LANGSMITH_API_KEY`,
`run_finalize` will:

- Build a **masked, truncated** telemetry payload (user/context excerpts,
  validation status, repair metadata, etc.).
- Optionally include:
  - The JSON tool/function schema (`LANGSMITH_INCLUDE_SCHEMA=true`).
  - A masked, truncated excerpt of the raw model response
    (`LANGSMITH_INCLUDE_RAW=true`).
- Push a single trace to LangSmith using a small, defensive sink.

Failures in telemetry **never** affect the main control flow.

For safety, keep `LANGSMITH_INCLUDE_RAW=false` by default and only enable it for
internal debugging.

---

## 12. Quick checklist

You should be "good to go" when:

- Python 3.11+ is installed.
- `uv --version` works.
- `git clone` of `mini-sdlc-agents` is present.
- `.env` exists (copied from `.env.sample`) and contains your secrets.
- `uv sync` completes and `.venv` exists.
- `uv run python -m pytest` passes locally.
- `uv run python scripts/smoke_finalize.py "Build a todo CLI" --no-llm` works.
- (Optional) Docker dev container builds and runs.
- (Optional) LangSmith sink is configured and traces show up where expected.

---

## 13. Notes for new contributors

- Never commit real API keys. Only `.env.sample` is versioned.
- Prefer `uv add` over editing `pyproject.toml` by hand when adding new deps.
- Keep tests fast; long-running or costful tests should be explicitly marked and
  excluded from CI by default.
- When touching the finalize agent, consider:
  - Schema and models under `src/agents/finalize_requirements/`.
  - The orchestrator entrypoint `run_finalize`.
  - Tests under `src/agents/finalize_requirements/tests/` and `tests/`.
