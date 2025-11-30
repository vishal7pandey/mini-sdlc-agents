# Architecture

This repo models a **mini SDLC agent pipeline**:

```text
user requirements
      |
      v
[ finalize_requirements ]
      |
      v
[ generate_design ]
      |
      v
[ plan_for_coding ]
      |
      v
[ write_code ]
      |
      v
[ write_tests ]
      |
      v
artifacts & reports
```

## 5-Step Flow (input → think → action → observe → output)

1. **Input**
   - User provides raw requirements (free-form text, issue, or doc).
2. **Think**
   - An agent interprets the input, applies its prompt + context, and plans its response.
3. **Action**
   - The agent calls an LLM via an adapter (e.g., OpenAI, LangChain) with a specific schema.
4. **Observe**
   - The orchestrator inspects the structured JSON output, validates it (schema), and stores artifacts.
5. **Output**
   - The pipeline passes structured artifacts to the next agent or returns final outputs (design/plan/code/tests).

## Components (high level)

- **Orchestrator** (`src/orchestrator/`)
  - Defines the pipeline ordering and shared types.
  - Calls agents in sequence, passing artifacts along.
- **Agents** (`src/agents/`)
  - One folder per logical agent.
  - Each agent has a `prompt.txt` and `schema.json` describing its contract.
- **Adapters** (`src/adapters/`)
  - Thin wrappers around LLM clients.
  - Responsible for enforcing "return JSON only" and mapping to/from schemas.
- **Utils & Safety** (`src/utils/`)
  - Helper utilities and safety checklists.
- **Docs, Templates, Infra, CI**
  - `docs/` for architecture + runbooks + agent descriptions.
  - `templates/` for issue/commit hygiene.
  - `infra/` + `ci/` for container and pipeline skeletons.
