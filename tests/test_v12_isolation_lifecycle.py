import multiprocessing
import os
import time
import unittest
from pathlib import Path

from verification_v1.evaluation import evaluate_fixture_set


FIXTURE_SET = Path(__file__).resolve().parents[1] / "evals" / "verification_v1" / "engineering_fixture_set.json"


class IsolationLifecycleTests(unittest.TestCase):
    def test_repeated_fixture_evaluation_terminates_without_orphaned_children(self) -> None:
        started = time.perf_counter()
        first = evaluate_fixture_set(FIXTURE_SET)
        self.assertGreaterEqual(first.task_count, 1)
        self.assertEqual([], multiprocessing.active_children())
        second = evaluate_fixture_set(FIXTURE_SET)
        self.assertEqual(first.task_count, second.task_count)
        self.assertEqual([], multiprocessing.active_children())
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 120.0, f"repeated fixture evaluation ran for {elapsed:.1f}s")
        if os.name == "posix":
            self.assertEqual([], _tracker_semaphores())


def _tracker_semaphores() -> list[str]:
    try:
        import multiprocessing.resource_tracker as tracker

        cache = getattr(tracker._resource_tracker, "_cache", {})
    except Exception:
        return []
    if not isinstance(cache, dict):
        return []
    leftover: list[str] = []
    for key, value in cache.items():
        if isinstance(value, (set, list, tuple, frozenset)):
            if str(key) in {"semaphore", "semlock"} and value:
                leftover.extend(str(item) for item in value)
        elif str(value) in {"semaphore", "semlock"}:
            leftover.append(str(key))
    return leftover
