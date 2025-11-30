# Runbooks

This project is currently **scaffolding only**. The following runbooks describe how it is intended to be used once the orchestrator and adapters are implemented.

## Local Testing (future state)

1. **Prepare environment**
   - Create and activate a Python virtualenv.
   - Copy `.env.sample` to `.env` and fill in secrets (e.g., `OPENAI_API_KEY`).
2. **Install dependencies**
   - `pip install -r requirements.txt`
3. **Run dry-run pipeline**
   - A future CLI or script (e.g., `python -m src.cli run-pipeline`):
     - Reads an input file from `examples/examples/`.
     - Calls each agent in sequence using adapters.
     - Writes JSON artifacts to `examples/expected/`.
4. **Inspect artifacts**
   - Validate that outputs match `schema.json` for each agent.
   - Compare against stored examples under `examples/expected/`.

## Sandboxing Notes

- Use **non-production** API keys and test projects.
- Limit agents to **non-destructive actions** (no direct deployment, no repo writes) unless gated by humans.
- Keep all network calls **observable** (logging, traces, or mock adapters during tests).
- Consider a **"replay" mode** with canned LLM responses for deterministic CI runs.

## Security Checklist (high level)

- **Secrets handling**
  - Never commit real secrets; use `.env` and secret managers.
  - Rotate keys that are accidentally exposed.
- **Prompt & data hygiene**
  - Avoid injecting raw untrusted content into prompts without sanitization.
  - Redact or anonymize sensitive fields where possible.
- **LLM output validation**
  - Enforce JSON schema validation.
  - Reject or re-ask on invalid or incomplete outputs.
- **Logging & PII**
  - Avoid logging full raw payloads that may contain PII.
  - Provide clear configuration for log redaction.
- **Dependency & supply chain**
  - Pin dependency versions once the project stabilizes.
  - Use scanning tools (SAST/Dependabot/etc.) in CI.
