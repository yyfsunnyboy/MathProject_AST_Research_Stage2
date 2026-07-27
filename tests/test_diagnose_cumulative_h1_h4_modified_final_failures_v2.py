"""Data-only focused tests for the 130-cell diagnostics plan.

Default tests never invoke a real candidate, journal selection, or 130-cell
execution.  Opt-in ``STAGE2_RUN_SANDBOX_SMOKE=1`` runs one fixed harmless
HumanEval/0 worker only.
"""

from __future__ import annotations

import json
import pathlib
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.diagnose_cumulative_h1_h4_modified_final_failures_v2 import (
    EXPECTED_COUNTS,
    EXPECTED_TOTAL,
    EXPECTED_EVALPLUS_VERSION,
    EvalPlusDatasetCache,
    EvalPlusRuntime,
    OUTCOME_CATEGORIES,
    SANDBOX_EVALPLUS_CACHE_DIR,
    SANDBOX_WORK_DIR,
    WORKER,
    WORKER_STDOUT_ISOLATION,
    _classify_execution,
    _final_category_summary,
    _run_sandbox_worker,
    build_bubblewrap_command,
    load_130_cell_manifest,
    resolve_evalplus_dataset_cache,
    resolve_evalplus_runtime,
    sandbox_evalplus_preflight,
)


class DiagnosisPlanFocusedTests(unittest.TestCase):
    SYNTHETIC_RUNTIME = EvalPlusRuntime("/usr/bin/python3", "/opt/evalplus/site-packages", EXPECTED_EVALPLUS_VERSION)
    SYNTHETIC_CACHE = EvalPlusDatasetCache(
        "/opt/evalplus/cache",
        "/opt/evalplus/cache/HumanEvalPlus-v0.1.10.jsonl",
        "/opt/evalplus/cache/MbppPlus-v0.2.0.jsonl",
    )

    def _protocol_result(self, *, returncode: int, stdout: str, stderr: str = "") -> dict:
        completed = subprocess.CompletedProcess(args=["synthetic"], returncode=returncode, stdout=stdout, stderr=stderr)
        with patch("scripts.diagnose_cumulative_h1_h4_modified_final_failures_v2.subprocess.run", return_value=completed):
            return _run_sandbox_worker(
                runtime=self.SYNTHETIC_RUNTIME,
                worker_text="print('never executed')",
                request={"synthetic": True},
                timeout_seconds=1,
                dataset_cache=self.SYNTHETIC_CACHE,
            )

    @unittest.skip("130-cell journal/manifest validation is intentionally excluded from protocol-only tests")
    def test_real_journal_manifest_has_exact_130_cell_scope(self) -> None:
        # Retained for the separate data-only audit workflow; never run here.
        rows, audit = load_130_cell_manifest(pathlib.Path.cwd())
        self.assertEqual(len(rows), EXPECTED_TOTAL)
        self.assertEqual({model: sum(row["model"] == model for row in rows) for model in EXPECTED_COUNTS}, EXPECTED_COUNTS)
        self.assertEqual(len({(row["model"], row["cell_identity"]) for row in rows}), EXPECTED_TOTAL)
        self.assertEqual(audit["combined"]["duplicates"], 0)
        self.assertEqual(audit["combined"]["missing"], 0)
        self.assertEqual(audit["combined"]["transition_counts"], {"blocker_removed_but_incorrect": 12, "modified_but_still_failed": 118})

    def test_sandbox_command_has_required_os_controls(self) -> None:
        command = build_bubblewrap_command(
            runtime=self.SYNTHETIC_RUNTIME,
            worker_path="/host/worker.py",
            request_path="/host/request.json",
            dataset_cache=self.SYNTHETIC_CACHE,
        )
        joined = " ".join(command)
        for required in (
            "systemd-run",
            "CPUQuota=100%",
            "MemoryMax=512M",
            "MemorySwapMax=0",
            "TasksMax=64",
            "--unshare-all",
            "--cap-drop ALL",
            "--ro-bind / /",
            "--tmpfs /tmp",
            f"--tmpfs {SANDBOX_WORK_DIR}",
            f"--ro-bind {self.SYNTHETIC_CACHE.host_cache_dir} {SANDBOX_EVALPLUS_CACHE_DIR}",
            f"--chdir {SANDBOX_WORK_DIR}",
            "--new-session",
            "setpriv --no-new-privs",
            "/usr/bin/python3 -I -c",
            "/opt/evalplus/site-packages",
        ):
            with self.subTest(required=required):
                self.assertIn(required, joined)

    def test_sandbox_command_does_not_mkdir_work_on_readonly_root(self) -> None:
        """Regression: bwrap must not create /work on the read-only host root."""
        command = build_bubblewrap_command(
            runtime=self.SYNTHETIC_RUNTIME,
            worker_path="/host/worker.py",
            request_path="/host/request.json",
            dataset_cache=self.SYNTHETIC_CACHE,
        )
        joined = " ".join(command)
        self.assertNotIn("--tmpfs /work", joined)
        self.assertNotIn("--chdir /work", joined)
        self.assertNotIn("/work/worker.py", joined)
        self.assertNotIn("/work/request.json", joined)
        self.assertNotIn("HOME=/work", joined.replace("--setenv HOME ", "HOME="))
        # Work area must be nested under the writable /tmp tmpfs mount.
        self.assertTrue(SANDBOX_WORK_DIR.startswith("/tmp/"))
        self.assertIn(f"--tmpfs {SANDBOX_WORK_DIR}", joined)
        self.assertIn(f"{SANDBOX_WORK_DIR}/worker.py", joined)
        self.assertIn(f"{SANDBOX_WORK_DIR}/request.json", joined)
        # Mount order: /tmp before the nested work tmpfs before EvalPlus cache bind.
        tmp_idx = command.index("/tmp")
        work_idx = command.index(SANDBOX_WORK_DIR)
        cache_idx = command.index(SANDBOX_EVALPLUS_CACHE_DIR)
        self.assertLess(tmp_idx, work_idx)
        self.assertLess(work_idx, cache_idx)

    def test_only_structured_actual_test_result_can_be_wrong_answer(self) -> None:
        self.assertEqual(_classify_execution({"phase": "evalplus_tests", "base_status": "fail", "plus_status": "pass"}), "test_assertion_wrong_answer")
        self.assertEqual(_classify_execution({"phase": "evalplus_tests", "base_status": "timeout", "plus_status": "fail"}), "timeout")
        self.assertEqual(_classify_execution({"phase": "unknown", "base_status": "fail", "plus_status": "fail"}), "other_unclassifiable")
        self.assertEqual(set(OUTCOME_CATEGORIES), {
            "parse_failure", "entrypoint_callability_signature_failure", "runtime_exception", "timeout", "test_assertion_wrong_answer", "pass", "evaluator_or_infrastructure_error", "other_unclassifiable",
        })

    def test_nonzero_return_preserves_return_code_and_stderr(self) -> None:
        result = self._protocol_result(returncode=17, stdout="partial output\n", stderr="worker import failure\n")
        self.assertEqual(result["protocol_error_kind"], "nonzero_return")
        self.assertEqual(result["return_code"], 17)
        self.assertEqual(result["worker_stderr"], "worker import failure\n")
        self.assertEqual(result["nonempty_stdout_line_count"], 1)
        self.assertEqual(_classify_execution(result), "evaluator_or_infrastructure_error")

    def test_empty_multiple_and_invalid_json_are_distinct(self) -> None:
        cases = [("", "empty_stdout"), ("{}\n{}\n", "multiple_records"), ("not-json\n", "invalid_json")]
        for stdout, expected_kind in cases:
            with self.subTest(kind=expected_kind):
                result = self._protocol_result(returncode=0, stdout=stdout)
                self.assertEqual(result["protocol_error_kind"], expected_kind)
                self.assertEqual(result["phase"], "sandbox_or_worker_error")
                if expected_kind == "invalid_json":
                    self.assertIn("line 1", result["json_decode_error"])

    def test_single_legal_json_record_reaches_evalplus_tests(self) -> None:
        result = self._protocol_result(returncode=0, stdout='{"phase":"evalplus_tests","base_status":"pass","plus_status":"fail"}\n')
        self.assertIsNone(result["protocol_error_kind"])
        self.assertEqual(result["phase"], "evalplus_tests")
        self.assertEqual(_classify_execution(result), "test_assertion_wrong_answer")

    def test_third_party_stdout_noise_still_emits_one_legal_json_record(self) -> None:
        """WORKER isolation must keep stdout as exactly one JSON when libraries print tips."""
        worker = WORKER_STDOUT_ISOLATION + """
print("Downloading dataset from https://example.invalid/HumanEvalPlus.jsonl.gz")
print("100%")
emit({"phase":"evalplus_tests","exception_class":"NONE","parse_result":"success","base_status":"fail","plus_status":"fail","detail":"synthetic"})
"""
        with tempfile.TemporaryDirectory(prefix="worker_stdout_isolation_") as temp_dir:
            path = pathlib.Path(temp_dir) / "worker.py"
            path.write_text(worker, encoding="utf-8")
            completed = subprocess.run(
                [os.environ.get("PYTHON", "python3"), str(path), str(pathlib.Path(temp_dir) / "unused.json")],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, completed.stdout)
        payload = json.loads(lines[0])
        self.assertEqual(payload["phase"], "evalplus_tests")
        self.assertIn("Downloading dataset from", payload["third_party_stdout"])
        self.assertIn("Downloading dataset from", completed.stderr)

    def test_all_summary_uses_entire_population(self) -> None:
        rows = ([{"model": "qwen3.5:4b", "final_category": "pass"}] * 78 + [{"model": "qwen3.5:9b", "final_category": "timeout"}] * 52)
        summary = {row["model"]: row for row in _final_category_summary(rows)}
        self.assertEqual(summary["qwen3.5:4b"]["total"], 78)
        self.assertEqual(summary["qwen3.5:9b"]["total"], 52)
        self.assertEqual(summary["ALL"]["total"], 130)
        self.assertEqual(summary["ALL"]["total"], summary["qwen3.5:4b"]["total"] + summary["qwen3.5:9b"]["total"])

    @unittest.skipUnless(os.environ.get("STAGE2_RUN_SANDBOX_SMOKE") == "1", "run explicitly as the approved harmless sandbox smoke")
    def test_harmless_actual_worker_e2e(self) -> None:
        """Uses a fixed harmless source only; never reads journals or any 130-cell source."""
        request = {
            "dataset": "humaneval",
            "task_id": "HumanEval/0",
            "entry_point": "has_close_elements",
            "source": "def has_close_elements(numbers, threshold):\n    return False\n",
        }
        runtime = resolve_evalplus_runtime()
        cache = resolve_evalplus_dataset_cache()
        self.assertTrue(pathlib.Path(cache.humaneval_plus_jsonl).is_file(), cache)
        self.assertTrue(pathlib.Path(cache.mbpp_plus_jsonl).is_file(), cache)
        probe = sandbox_evalplus_preflight(runtime=runtime, timeout_seconds=10)
        self.assertEqual(probe["evalplus_version"], EXPECTED_EVALPLUS_VERSION, probe)
        self.assertEqual(probe["python_executable"], runtime.python_executable, probe)
        result = _run_sandbox_worker(
            runtime=runtime,
            worker_text=WORKER,
            request=request,
            timeout_seconds=30,
            dataset_cache=cache,
        )
        self.assertEqual(result["return_code"], 0, result)
        self.assertEqual(result["nonempty_stdout_line_count"], 1, result)
        self.assertEqual(result["phase"], "evalplus_tests", result)
        self.assertIsNone(result["protocol_error_kind"], result)
        combined = f"{result.get('worker_stdout', '')}\n{result.get('worker_stderr', '')}\n{result.get('third_party_stdout', '')}"
        self.assertNotIn("Downloading dataset from", combined, result)
        self.assertNotIn("URLError", combined, result)


if __name__ == "__main__":
    unittest.main()
