"""Data-only focused tests for the 130-cell diagnostics plan.

No test invokes WORKER, EvalPlus, or a candidate source.  These tests cover
selection/manifest invariants and the future sandbox command contract only.
"""

from __future__ import annotations

import pathlib
import unittest

from scripts.diagnose_cumulative_h1_h4_modified_final_failures_v2 import (
    EXPECTED_COUNTS,
    EXPECTED_TOTAL,
    OUTCOME_CATEGORIES,
    _classify_execution,
    build_bubblewrap_command,
    load_130_cell_manifest,
)


class DiagnosisPlanFocusedTests(unittest.TestCase):
    def test_real_journal_manifest_has_exact_130_cell_scope(self) -> None:
        # Reads JSON only.  Candidate source strings are never compiled/imported.
        rows, audit = load_130_cell_manifest(pathlib.Path.cwd())
        self.assertEqual(len(rows), EXPECTED_TOTAL)
        self.assertEqual({model: sum(row["model"] == model for row in rows) for model in EXPECTED_COUNTS}, EXPECTED_COUNTS)
        self.assertEqual(len({(row["model"], row["cell_identity"]) for row in rows}), EXPECTED_TOTAL)
        self.assertEqual(audit["combined"]["duplicates"], 0)
        self.assertEqual(audit["combined"]["missing"], 0)
        self.assertEqual(audit["combined"]["transition_counts"], {"blocker_removed_but_incorrect": 12, "modified_but_still_failed": 118})

    def test_sandbox_command_has_required_os_controls(self) -> None:
        command = build_bubblewrap_command(python_executable="/usr/bin/python3", worker_path="/host/worker.py", request_path="/host/request.json")
        joined = " ".join(command)
        for required in ("systemd-run", "CPUQuota=100%", "MemoryMax=512M", "TasksMax=64", "--unshare-all", "--cap-drop ALL", "--ro-bind / /", "--tmpfs /tmp", "--tmpfs /work", "--new-session", "setpriv --no-new-privs"):
            with self.subTest(required=required):
                self.assertIn(required, joined)

    def test_only_structured_actual_test_result_can_be_wrong_answer(self) -> None:
        self.assertEqual(_classify_execution({"phase": "evalplus_tests", "base_status": "fail", "plus_status": "pass"}), "test_assertion_wrong_answer")
        self.assertEqual(_classify_execution({"phase": "evalplus_tests", "base_status": "timeout", "plus_status": "fail"}), "timeout")
        self.assertEqual(_classify_execution({"phase": "unknown", "base_status": "fail", "plus_status": "fail"}), "other_unclassifiable")
        self.assertEqual(set(OUTCOME_CATEGORIES), {
            "parse_failure", "entrypoint_callability_signature_failure", "runtime_exception", "timeout", "test_assertion_wrong_answer", "pass", "other_unclassifiable",
        })


if __name__ == "__main__":
    unittest.main()
