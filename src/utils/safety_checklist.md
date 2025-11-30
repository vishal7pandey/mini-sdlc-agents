# Safety Checklist (LLM + SDLC Agents)

- **Secrets**
  - Never log or commit API keys or credentials.
  - Use `.env` + a secrets manager for real deployments.

- **Prompt Hygiene**
  - Avoid injecting untrusted content directly into prompts without sanitization.
  - Redact or anonymize PII where feasible.

- **Output Validation**
  - Enforce JSON schema validation for every agent.
  - On invalid JSON, either:
    - Ask the LLM to repair the output, or
    - Fail fast and surface a clear error.

- **Permissions & Effects**
  - Keep agents read-only with respect to external systems (no direct deploys, no destructive actions) unless guarded by explicit human approval.

- **Testing**
  - Provide replayable fixtures for LLM outputs.
  - Add smoke tests that ensure the end-to-end pipeline still returns valid JSON artifacts.
