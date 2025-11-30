# OpenAI Adapter Notes

This adapter is responsible for:

- Wrapping OpenAI (or compatible) chat / function-calling APIs.
- Enforcing structured JSON responses that match each agent's `schema.json`.
- Handling retries, timeouts, and basic error reporting.

## Expected Usage (future)

- Provide a small function, e.g. `call_agent(prompt, schema, model, settings)`.
- Use "JSON-only" responses (e.g., `response_format` or similar features) when available.
- Validate responses against the JSON schema before returning to the orchestrator.

## Design Considerations

- Allow injection of model name, temperature, and other tunables via config/env.
- Keep the surface area minimal so other adapters can match it (LangChain, mocks, etc.).
- Support a mock mode for tests to avoid real API calls in CI.
