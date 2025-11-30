#!/usr/bin/env bash

# Simple local test runner for mini-sdlc-agents
set -euo pipefail

uv sync
uv run python -m pytest -q
