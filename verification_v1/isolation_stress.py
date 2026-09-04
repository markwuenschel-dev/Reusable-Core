"""Repeat fixture evaluation in one interpreter and report leftover workers."""

from __future__ import annotations

import multiprocessing
import sys
import time
from pathlib import Path
from typing import Any

from .evaluation import evaluate_fixture_set


def stress_fixture_evaluation(fixture_set: Path, iterations: int) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    runs: list[dict[str, Any]] = []
    started = time.perf_counter()
    for index in range(iterations):
        before = len(multiprocessing.active_children())
        run_started = time.perf_counter()
        report = evaluate_fixture_set(fixture_set)
        elapsed = time.perf_counter() - run_started
        after = [child.pid for child in multiprocessing.active_children()]
        runs.append(
            {
                "iteration": index + 1,
                "task_count": report.task_count,
                "elapsed_seconds": elapsed,
                "children_before": before,
                "children_after": after,
            }
        )
        if after:
            return {
                "ok": False,
                "iterations": iterations,
                "python": ".".join(str(part) for part in sys.version_info[:3]),
                "platform": sys.platform,
                "start_method": multiprocessing.get_start_method(allow_none=True),
                "runs": runs,
                "error": "surviving child processes after evaluation",
            }
    return {
        "ok": True,
        "iterations": iterations,
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "platform": sys.platform,
        "start_method": multiprocessing.get_start_method(allow_none=True),
        "elapsed_seconds": time.perf_counter() - started,
        "runs": runs,
    }
