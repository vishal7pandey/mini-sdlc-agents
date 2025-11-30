#!/usr/bin/env python
"""Simple cost report for finalize_requirements runs.

Usage (from repo root):

    uv run python scripts/cost_report.py            # last 7 days (default)
    uv run python scripts/cost_report.py --days 30  # last 30 days
    uv run python scripts/cost_report.py --all      # all recorded days

This script reads ``runs/usage.json`` (maintained by the orchestrator) and
summarizes token usage and cost over a recent window. It is intended for local
cost awareness, not as a billing source of truth.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


_USAGE_FILE = Path(__file__).resolve().parents[1] / "runs" / "usage.json"


def _parse_days_arg(days: int) -> int:
    if days <= 0:
        raise argparse.ArgumentTypeError("--days must be a positive integer")
    return days


def _load_usage() -> Dict[str, Any]:
    if not _USAGE_FILE.exists():
        return {"days": {}}

    try:
        raw = _USAGE_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return {"days": {}}

    if not isinstance(data, dict):
        return {"days": {}}

    days = data.get("days")
    if not isinstance(days, dict):
        data["days"] = {}
    return data


def _iter_window(days_data: Dict[str, Any], *, days: int | None) -> Tuple[str, Dict[str, Any]]:
    """Yield (day_key, info) pairs within the selected window.

    If ``days`` is None, all days are yielded.
    Otherwise, only days within the last ``days`` days (inclusive) are yielded.
    """

    if not days_data:
        return

    if days is None:
        for day_key, info in sorted(days_data.items()):
            yield day_key, dict(info or {})
        return

    today = date.today()
    cutoff = today - timedelta(days=days - 1)

    for day_key, info in sorted(days_data.items()):
        try:
            d = datetime.strptime(day_key, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < cutoff or d > today:
            continue
        yield day_key, dict(info or {})


def _format_usd(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:.6f}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Summarize finalize_requirements token usage and cost from runs/usage.json",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--days",
        type=_parse_days_arg,
        default=7,
        help="Number of days back from today to include (default: 7)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Include all recorded days (ignores --days)",
    )

    args = parser.parse_args(argv)

    usage_data = _load_usage()
    days_data = usage_data.get("days", {})

    if not days_data:
        print("No usage data found in runs/usage.json yet.")
        return

    window_days: int | None = None if args.all else args.days

    print("Cost report for finalize_requirements")
    if window_days is None:
        print("Window: ALL days recorded")
    else:
        print(f"Window: last {window_days} day(s)")
    print()

    total_tokens = 0
    total_cost = 0.0
    any_cost = False

    print("Per-day totals:")
    print("  date        tokens     cost_usd   calls")

    for day_key, info in _iter_window(days_data, days=window_days):
        try:
            tokens = int(info.get("tokens") or 0)
        except (TypeError, ValueError):
            tokens = 0
        try:
            cost_usd = float(info.get("cost_usd") or 0.0)
        except (TypeError, ValueError):
            cost_usd = 0.0
        try:
            calls = int(info.get("calls") or 0)
        except (TypeError, ValueError):
            calls = 0

        total_tokens += tokens
        total_cost += cost_usd
        if cost_usd > 0.0:
            any_cost = True

        print(f"  {day_key}  {tokens:7d}  {_format_usd(cost_usd):>9}  {calls:5d}")

    print()
    print("Summary:")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Total cost:   {_format_usd(total_cost)}")

    if not any_cost:
        print()
        print(
            "NOTE: All recorded cost_usd values are zero. This usually means "
            "FINALIZE_INPUT_PRICE_PER_MTOKENS / FINALIZE_OUTPUT_PRICE_PER_MTOKENS "
            "were not set when calls were made. Set them in your environment "
            "(or .env) and future runs will include cost estimates."
        )


if __name__ == "__main__":  # pragma: no cover
    main()
