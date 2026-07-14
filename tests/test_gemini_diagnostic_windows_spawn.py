"""Offline Windows-spawn regression checks for the Gemini diagnostic runner."""
from __future__ import annotations

import multiprocessing
import tempfile
import unittest
from pathlib import Path

from agent_tools.finals_rebuild.math_boundary_pilot import _execute_generate
from scripts import run_gemini_ab1_ab2d_diagnostic as runner


def _spawn_import(queue: multiprocessing.queues.Queue) -> None:
    from scripts import run_gemini_ab1_ab2d_diagnostic as child_runner

    queue.put(child_runner.API_LOOP_ENTERED)


class GeminiDiagnosticWindowsSpawnTest(unittest.TestCase):
    def test_import_and_spawn_do_not_enter_api_loop(self) -> None:
        self.assertFalse(runner.API_LOOP_ENTERED)
        context = multiprocessing.get_context("spawn")
        queue = context.Queue()
        child = context.Process(target=_spawn_import, args=(queue,))
        child.start()
        self.assertFalse(queue.get(timeout=10))
        child.join(timeout=10)
        self.assertEqual(child.exitcode, 0)

    def test_mock_calls_are_not_repeated_by_spawn_and_timeout_cleans_up(self) -> None:
        calls = 0

        class FakeResponse:
            text = "def generate(level=1, **kwargs):\n    return {}\n"
            prompt_tokens, completion_tokens, total_tokens, latency_ms = 1, 1, 2, 1

        def fake_call(_prompt, _preset):
            nonlocal calls
            calls += 1
            return FakeResponse()

        with tempfile.TemporaryDirectory(prefix="gemini_spawn_test_") as temp:
            rows = runner._run(Path(temp) / "rows.jsonl", fake_call)
        self.assertEqual(len(rows), 8)
        self.assertEqual(calls, 8)

        context = multiprocessing.get_context("spawn")
        queue = context.Queue()
        child = context.Process(target=_spawn_import, args=(queue,))
        child.start()
        self.assertFalse(queue.get(timeout=10))
        child.join(timeout=10)
        self.assertEqual(child.exitcode, 0)
        self.assertEqual(calls, 8)

        status, value, error = _execute_generate("def generate():\n    while True: pass\n", timeout=0.1)
        self.assertEqual((status, value), ("runtime_failure", None))
        self.assertIn("execution_timeout", error)
        self.assertEqual(_execute_generate("def generate():\n    return 1\n", timeout=0.5)[0], "passed")


if __name__ == "__main__":
    unittest.main()
