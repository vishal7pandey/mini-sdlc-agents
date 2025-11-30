# LangChain Adapter Notes

This adapter is **optional**.

Goals:

- Provide a thin wrapper that maps LangChain abstractions to the same interface as the OpenAI adapter.
- Make it easy to swap between direct OpenAI calls and LangChain-based chains/tools.

Guidelines:

- Keep orchestration logic in `src/orchestrator/`, not in the adapter.
- Use LangChain for convenience (prompt templates, tools) without coupling the core design to it.
- Mirror the same contract used by the OpenAI adapter (inputs, outputs, and error semantics).
