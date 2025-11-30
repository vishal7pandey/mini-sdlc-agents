# finalize_requirements Agent

This agent turns **raw requirement text** into a structured **requirements object**
that downstream agents (design, planning, coding, tests) can rely on.

This folder currently contains **skeletons only**:

- `schema.json` and `prompt.txt` define the contract with the LLM.
- `models.py` will hold Pydantic models mirroring `schema.json`.
- `validator.py` will validate and normalize raw payloads.
- `contradiction.py` will detect obvious requirement conflicts.
- `orchestrator.py` will expose the `run_finalize(...)` entrypoint.
- `langgraph_block.yaml` sketches how this agent fits into a LangGraph flow.

Implementation will be added incrementally so that we can:

- Keep a clear contract between agents.
- Test validation and normalization locally without calling OpenAI.
- Add LLM + LangChain/LangSmith integration in a later iteration.
