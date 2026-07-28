"""Focused data-selection tests; these never load or execute candidate source."""

from __future__ import annotations

import pathlib
import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.diagnose_mbpp_external94_modified_final_failures_v1 import (
    EXPECTED_LAYERS,
    EXPECTED_MODELS,
    EXPECTED_STATUS_PAIRS,
    EXPECTED_TOTAL,
    FROZEN_ROSTER,
    BWRAP,
    BWRAP_GUEST_OUTPUT,
    SYSTEMD_RUN,
    bwrap_preflight,
    build_bwrap_command,
    build_roster,
    classify_execution,
    load_external_task_scope,
    load_frozen_final_sources,
    run_execution_loop,
)


class MbppExternal94PreflightTests(unittest.TestCase):
    def _fixture_loaded(self, count=94):
        rows = []
        for index in range(count):
            source = "def solve():\n    return 1\n"
            digest = __import__("hashlib").sha256(source.encode()).hexdigest()
            rows.append({
                "model": "qwen3.5:4b" if index < 58 else "qwen3.5:9b",
                "condition": "Ab1", "task_id": f"Mbpp/{index}",
                "cell_identity": f"{index:064x}", "source_journal_path": f"fixture/{index}.json",
                "source_row_key": f"fixture|{index}", "source_field": "final_source",
                "source_sha256": digest, "final_source_sha256": digest,
                "entry_point": "solve", "_final_source": source,
            })
        return rows

    @staticmethod
    def _pass_executor(row, **_kwargs):
        return {
            "phase": "evalplus_tests", "sandbox_started": True,
            "sandbox_completed": True, "parse_status": "pass",
            "compile_status": "pass", "runtime_status": "pass",
            "entry_point_status": "callable", "base_status": "pass",
            "plus_status": "pass", "timeout": False,
            "exception_class": "NONE", "exception_summary": "NONE",
        }

    def test_execution_classifications_cover_required_terminal_states(self):
        cases = [
            ({"phase": "evalplus_tests", "base_status": "pass", "plus_status": "pass"}, "executable_and_base_plus_pass"),
            ({"phase": "evalplus_tests", "base_status": "fail", "plus_status": "fail"}, "executable_but_base_fail"),
            ({"phase": "evalplus_tests", "base_status": "pass", "plus_status": "fail"}, "executable_base_pass_plus_fail"),
            ({"phase": "parse_or_compile"}, "parse_or_compile_failure"),
            ({"phase": "module_load"}, "import_or_runtime_failure"),
            ({"phase": "entry_point"}, "missing_entry_point"),
            ({"phase": "timeout", "timeout": True}, "timeout"),
            ({"phase": "sandbox_failure"}, "sandbox_failure"),
            ({"phase": "diagnostic_infrastructure"}, "diagnostic_infrastructure_failure"),
        ]
        for result, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_execution(result), expected)

    def test_execution_loop_completes_94_and_emits_no_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            completion = run_execution_loop(
                self._fixture_loaded(), output_dir=pathlib.Path(temp_dir),
                timeout_seconds=1, cell_executor=self._pass_executor,
                evalplus_site_packages=pathlib.Path("/fixture/site-packages"),
            )
            self.assertEqual(completion["status"], "CANDIDATE_EXECUTION_COMPLETED")
            manifest = (pathlib.Path(temp_dir) / "execution_manifest.json").read_text()
            self.assertNotIn("def solve", manifest)
            self.assertTrue((pathlib.Path(temp_dir) / "execution_completion.json").is_file())

    def test_resume_skips_completed_hash_matching_cells(self):
        calls = []
        def executor(row, **kwargs):
            calls.append(row["source_row_key"])
            return self._pass_executor(row, **kwargs)
        with tempfile.TemporaryDirectory() as temp_dir:
            out = pathlib.Path(temp_dir)
            loaded = self._fixture_loaded()
            run_execution_loop(loaded, output_dir=out, timeout_seconds=1, cell_executor=executor, evalplus_site_packages=pathlib.Path("/fixture"))
            self.assertEqual(len(calls), 94)
            calls.clear()
            run_execution_loop(loaded, output_dir=out, timeout_seconds=1, cell_executor=executor, evalplus_site_packages=pathlib.Path("/fixture"))
            self.assertEqual(calls, [])

    def test_resume_blocks_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out = pathlib.Path(temp_dir)
            loaded = self._fixture_loaded()
            run_execution_loop(loaded, output_dir=out, timeout_seconds=1, cell_executor=self._pass_executor, evalplus_site_packages=pathlib.Path("/fixture"))
            loaded[0]["source_sha256"] = "f" * 64
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                run_execution_loop(loaded, output_dir=out, timeout_seconds=1, cell_executor=self._pass_executor, evalplus_site_packages=pathlib.Path("/fixture"))

    def test_host_never_executes_fixture_source(self):
        loaded = self._fixture_loaded()
        loaded[0]["_final_source"] = "raise AssertionError('must not execute on host')"
        with tempfile.TemporaryDirectory() as temp_dir:
            run_execution_loop(loaded, output_dir=pathlib.Path(temp_dir), timeout_seconds=1, cell_executor=self._pass_executor, evalplus_site_packages=pathlib.Path("/fixture"))

    def test_less_than_94_cannot_complete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "exactly 94"):
                run_execution_loop(self._fixture_loaded(93), output_dir=pathlib.Path(temp_dir), timeout_seconds=1, cell_executor=self._pass_executor, evalplus_site_packages=pathlib.Path("/fixture"))
    def _mutated_roster(self, mutate):
        source = REPO_ROOT / FROZEN_ROSTER
        with source.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fields = list(rows[0])
        mutate(rows)
        temp = tempfile.TemporaryDirectory()
        path = pathlib.Path(temp.name) / "roster.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return temp, path

    def test_frozen_loader_loads_exactly_94_final_sources(self) -> None:
        rows, audit = load_frozen_final_sources(REPO_ROOT)
        self.assertEqual(len(rows), 94)
        self.assertEqual(audit["missing"], 0)
        self.assertEqual(audit["duplicates"], 0)
        self.assertEqual(audit["hash_verified"], 94)
        self.assertTrue(all(row["source_field"] == "final_source" for row in rows))
        self.assertTrue(all(row["source_sha256"] == row["final_source_sha256"] for row in rows))

    def test_frozen_loader_blocks_missing_row(self) -> None:
        temp, path = self._mutated_roster(lambda rows: rows.pop())
        with temp, self.assertRaisesRegex(RuntimeError, "94 rows"):
            load_frozen_final_sources(REPO_ROOT, roster_path=path)

    def test_frozen_loader_blocks_duplicate_identity(self) -> None:
        temp, path = self._mutated_roster(lambda rows: rows.__setitem__(-1, dict(rows[0])))
        with temp, self.assertRaisesRegex(RuntimeError, "duplicate"):
            load_frozen_final_sources(REPO_ROOT, roster_path=path)

    def test_frozen_loader_blocks_wrong_condition(self) -> None:
        def mutate(rows):
            rows[0]["condition"] = "Ab1" if rows[0]["condition"] == "Ab2g" else "Ab2g"
        temp, path = self._mutated_roster(mutate)
        with temp, self.assertRaisesRegex(RuntimeError, "condition mismatch"):
            load_frozen_final_sources(REPO_ROOT, roster_path=path)

    def test_frozen_loader_blocks_wrong_source_hash(self) -> None:
        def mutate(rows):
            rows[0]["final_source_sha256"] = "0" * 64
        temp, path = self._mutated_roster(mutate)
        with temp, self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            load_frozen_final_sources(REPO_ROOT, roster_path=path)

    def test_frozen_loader_rejects_raw_source_field(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must be final_source"):
            load_frozen_final_sources(REPO_ROOT, source_field="raw_source")

    def test_bwrap_command_uses_native_fail_closed_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host_output = pathlib.Path(temp_dir)
            command = build_bwrap_command(
                host_output_dir=host_output,
                worker_name="probe.py",
                request_name="request.json",
            )
        joined = " ".join(command)
        self.assertEqual(command[0], "/usr/bin/systemd-run")
        self.assertIn("/usr/bin/bwrap", command)
        for required in (
            "--unshare-user", "--unshare-ipc", "--unshare-pid",
            "--unshare-net", "--unshare-uts",
            "--uid 65534", "--gid 65534", "--cap-drop ALL",
            "--ro-bind / /", "--tmpfs /tmp",
            f"--dir {BWRAP_GUEST_OUTPUT}",
            f"--bind {host_output} {BWRAP_GUEST_OUTPUT}",
            "CPUQuota=100%", "MemoryMax=512M", "MemorySwapMax=0", "TasksMax=64",
        ):
            self.assertIn(required, joined)
        for forbidden in ("wsl.exe", "powershell", "docker", "--share-net"):
            self.assertNotIn(forbidden, joined.lower())
        self.assertNotIn("--unshare-all", joined)
        self.assertLess(command.index("--tmpfs"), command.index("--dir"))
        self.assertLess(command.index("--dir"), command.index("--bind"))

    @unittest.skipUnless(
        os.name == "posix"
        and pathlib.Path(BWRAP).is_file()
        and pathlib.Path(SYSTEMD_RUN).is_file(),
        "requires native Linux bwrap and systemd-run",
    )
    def test_bwrap_probe_integration(self) -> None:
        result = bwrap_preflight(timeout_seconds=3)
        self.assertEqual(result["status"], "READY", result)
        self.assertTrue(all(result["checks"].values()), result)
        self.assertEqual(result["evidence"]["marker"], "BWRAP_PROBE_OK")

    def test_external_scope_is_exactly_318_mbpp_tasks(self) -> None:
        external_ids, _manifest, audit = load_external_task_scope(pathlib.Path.cwd())
        self.assertEqual(len(external_ids), 318)
        self.assertEqual(audit["mbpp_task_count"], 378)
        self.assertEqual(audit["development_task_count"], 60)
        self.assertEqual(audit["external_task_count"], 318)
        self.assertTrue(all(task_id.startswith("Mbpp/") for task_id in external_ids))

    def test_roster_has_fixed_counts_and_unique_model_cells(self) -> None:
        rows, audit = build_roster(pathlib.Path.cwd())
        self.assertEqual(len(rows), EXPECTED_TOTAL)
        self.assertEqual(audit["model_counts"], EXPECTED_MODELS)
        self.assertEqual(audit["layer_counts"], EXPECTED_LAYERS)
        self.assertEqual(
            audit["status_pair_counts"],
            {"base_PASS_plus_FAIL": 45, "base_FAIL_plus_PASS": 1, "base_FAIL_plus_FAIL": 48},
        )
        self.assertEqual(audit["unique_model_cell_identity_count"], EXPECTED_TOTAL)
        self.assertTrue(all(row["final_phase"] == "preflight_only_no_candidate_load_or_execution" for row in rows))
        self.assertEqual({(row["base_status"], row["plus_status"]) for row in rows}, set(EXPECTED_STATUS_PAIRS))


if __name__ == "__main__":
    unittest.main()
