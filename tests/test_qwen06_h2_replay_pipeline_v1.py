from __future__ import annotations

import ast
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from scripts import run_qwen06_h2_replay_pipeline_v1 as pipeline


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / pipeline.OUTPUT_RELATIVE
H2_PATH = ROOT / pipeline.RULE_RELATIVE
AB3_PATHS = [ROOT / relative for relative in pipeline.AB3_BASELINES.values()]
LOCAL_TMP = ROOT / "artifacts" / "_tmp_qwen06_h2_replay_tests"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fresh_dir(label: str) -> Path:
    LOCAL_TMP.mkdir(parents=True, exist_ok=True)
    return LOCAL_TMP / f"{label}_{uuid.uuid4().hex}"


def _cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_h2_rule_sha_and_status_unchanged() -> None:
    assert pipeline.verify_h2_rule(ROOT) == pipeline.EXPECTED_RULE_SHA256
    assert pipeline.RULE_STATUS == "development_candidate_not_frozen"


def test_synthetic_smoke_trigger_transform_abstain_matrix() -> None:
    records = {row["smoke_name"]: row for row in pipeline.build_synthetic_smoke_records()}

    transformed = records["unique_module_selftest_transform"]
    assert transformed["triggered"] is True
    assert transformed["transformed"] is True
    assert transformed["abstained"] is False
    assert transformed["reason"] == "transformed_module_assert_quarantined"
    ast.parse(transformed["output_source"])
    assert pipeline.module_level_assert_count(transformed["output_source"]) == 0
    assert pipeline.function_segment_hashes(
        "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    ) == pipeline.function_segment_hashes(transformed["output_source"])

    noop = records["no_module_assert_noop"]
    assert noop["transformed"] is False
    assert noop["abstained"] is True
    assert noop["reason"] == "no_module_level_assert"
    assert noop["byte_identical_to_input"] is True

    multi = records["multiple_module_asserts_abstain"]
    assert multi["abstained"] is True
    assert multi["reason"] == "module_assert_count_not_one"

    missing_ep = records["entry_point_missing_abstain"]
    assert missing_ep["abstained"] is True
    assert missing_ep["reason"] == "entry_point_missing"

    ambiguous = records["ambiguous_extraction_abstain"]
    assert ambiguous["abstained"] is True
    assert ambiguous["reason"] == "extraction_ambiguous_or_unknown"
    assert ambiguous["extraction_unambiguous"] is False

    unknown = records["source_complete_unknown_abstain"]
    assert unknown["abstained"] is True
    assert unknown["reason"] == "source_truncated_or_completion_unknown"
    assert unknown["source_complete"] is None

    missing = records["missing_completion_itt_retained"]
    assert missing["missing_extracted_completion"] is True
    assert missing["reason"] == "missing_extracted_completion"
    assert missing["abstained"] is True


def test_idempotence_and_byte_identical_abstain() -> None:
    source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    first = pipeline.apply_h2_to_completion(
        completion=source,
        entry_point="solve",
        extraction_unambiguous=True,
        source_complete=True,
    )
    second = pipeline.apply_h2_to_completion(
        completion=first["output_source"],
        entry_point="solve",
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert first["transformed"] is True
    assert second["output_source"] == first["output_source"]
    assert second["output_sha256"] == first["output_sha256"]

    noop_source = "def solve(x):\n    return x\n"
    noop = pipeline.apply_h2_to_completion(
        completion=noop_source,
        entry_point="solve",
        extraction_unambiguous=True,
        source_complete=True,
    )
    assert noop["output_source"] == noop_source
    assert noop["input_sha256"] == noop["output_sha256"]


def test_ab1_and_ab2g_conditions_do_not_cross_contaminate() -> None:
    task = {"task_id": "Synthetic/cross", "entry_point": "solve"}
    completions = {
        "ab1": {
            "Synthetic/cross": {
                "task_id": "Synthetic/cross",
                "completion": "def solve(x):\n    return 1\n\nassert solve(0) == 1\n",
            }
        },
        "ab2g": {
            "Synthetic/cross": {
                "task_id": "Synthetic/cross",
                "completion": "def solve(x):\n    return 2\n",
            }
        },
    }
    attempts = {
        ("Synthetic/cross", "ab1"): {
            "task_id": "Synthetic/cross",
            "treatment": "ab1",
            "extraction_status": "extracted",
            "ollama_response_metadata": {
                "raw_body": '{"done_reason":"stop"}',
            },
        },
        ("Synthetic/cross", "ab2g"): {
            "task_id": "Synthetic/cross",
            "treatment": "ab2g",
            "extraction_status": "extracted",
            "ollama_response_metadata": {
                "raw_body": '{"done_reason":"stop"}',
            },
        },
    }
    records = {
        row["condition"]: row
        for row in pipeline.build_four_conditions_for_task(
            dataset="synthetic",
            task=task,
            completions=completions,
            attempts=attempts,
        )
    }
    assert set(records) == set(pipeline.CONDITIONS)
    assert records["Ab1-Raw"]["output_source"].startswith("def solve(x):\n    return 1")
    assert records["Ab2g-Raw"]["output_source"].startswith("def solve(x):\n    return 2")
    assert records["Ab1-H2"]["transformed"] is True
    assert records["Ab2g-H2"]["transformed"] is False
    assert records["Ab2g-H2"]["reason"] == "no_module_level_assert"
    assert "return 1" in records["Ab1-H2"]["output_source"]
    assert "return 2" in records["Ab2g-H2"]["output_source"]


def test_missing_completion_stays_in_full_itt_roster() -> None:
    task = {"task_id": "HumanEval/0", "entry_point": "has_close_elements"}
    records = pipeline.build_four_conditions_for_task(
        dataset="humaneval",
        task=task,
        completions={"ab1": {}, "ab2g": {}},
        attempts={},
    )
    assert len(records) == 4
    assert all(row["task_id"] == "HumanEval/0" for row in records)
    assert all(row["missing_extracted_completion"] is True for row in records)
    assert all(row["reason"] == "missing_extracted_completion" for row in records)


def test_provenance_flags_never_hardcoded_true_without_evidence() -> None:
    assert pipeline.provenance_flags_from_attempt(None) == (None, None)
    ambiguous, complete = pipeline.provenance_flags_from_attempt(
        {
            "extraction_status": "ambiguous",
            "ollama_response_metadata": {"raw_body": '{"done_reason":"length"}'},
        }
    )
    assert ambiguous is False
    assert complete is False


def test_preflight_and_smoke_artifacts_deterministic() -> None:
    preflight = pipeline.preflight(ROOT)
    assert preflight["model_calls"] == 0
    assert preflight["h2_rule_sha256"] == pipeline.EXPECTED_RULE_SHA256

    first = pipeline.build_smoke_artifact_bytes(ROOT)
    second = pipeline.build_smoke_artifact_bytes(ROOT)
    assert first == second
    written = pipeline.write_smoke_outputs(ROOT)
    assert written.keys() == first.keys()
    for name, payload in first.items():
        assert (OUTPUT / name).read_bytes() == payload

    manifest = __import__("json").loads(first["pipeline_manifest.json"])
    assert manifest["model_calls"] == 0
    assert manifest["full_itt_replay_executed"] is False
    assert manifest["evalplus_executed"] is False
    assert manifest["h2_rule"]["sha256"] == pipeline.EXPECTED_RULE_SHA256
    assert manifest["h2_rule"]["label"] == "development_candidate_not_frozen"


def test_old_ab3_and_existing_runs_untouched_by_smoke() -> None:
    before = {_sha(path): path for path in AB3_PATHS}
    run_files = [
        ROOT / "runs/he_qwen06/ab1.jsonl",
        ROOT / "runs/he_qwen06/ab2g.jsonl",
        ROOT / "runs/mb_qwen06/ab1.jsonl",
        ROOT / "runs/mb_qwen06/ab2g.jsonl",
        H2_PATH,
    ]
    before_runs = {path: _sha(path) for path in run_files}
    pipeline.write_smoke_outputs(ROOT)
    assert {_sha(path): path for path in AB3_PATHS} == before
    assert {path: _sha(path) for path in run_files} == before_runs


def test_replay_helper_exists_but_default_smoke_is_not_full_itt() -> None:
    # Wiring exists for full ITT rebuild, but this packaging round must not
    # silently execute the 542-task replay.
    assert callable(pipeline.replay_itt_roster)
    assert callable(pipeline.run_full_benchmark)
    manifest = __import__("json").loads(
        pipeline.build_smoke_artifact_bytes(ROOT)["pipeline_manifest.json"]
    )
    assert manifest["status"] == pipeline.PIPELINE_STATUS
    assert "full_0.6B_H2_ITT_not_executed" in manifest["non_claims"]


def test_classify_paired_outcomes() -> None:
    assert (
        pipeline.classify_paired_outcome(
            raw_strict="fail", h2_strict="pass", missing=False
        )
        == "verified_rescue"
    )
    assert (
        pipeline.classify_paired_outcome(
            raw_strict="pass", h2_strict="fail", missing=False
        )
        == "regression"
    )
    assert (
        pipeline.classify_paired_outcome(
            raw_strict="fail", h2_strict="fail", missing=True
        )
        == "missing_extracted_completion"
    )


def test_run_full_benchmark_dry_run_materializes_2168_itt_states() -> None:
    out = _fresh_dir("dry_run_all")
    try:
        before = pipeline.snapshot_protected_inputs(ROOT)
        result = pipeline.run_full_benchmark(
            dataset="all",
            output_dir=out,
            parallel=1,
            dry_run=True,
            repo_root=ROOT,
        )
        assert result["status"] == "dry_run_materialized_not_evaluated"
        assert result["evalplus_executed"] is False
        assert result["model_calls"] == 0
        assert result["itt_states"] == pipeline.EXPECTED_ITT_STATES_ALL

        ledger = [
            json.loads(line)
            for line in (out / "cell_ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert len(ledger) == 2168
        assert {row["condition"] for row in ledger} == set(pipeline.CONDITIONS)
        assert sum(1 for row in ledger if row["dataset"] == "humaneval") == 164 * 4
        assert sum(1 for row in ledger if row["dataset"] == "mbpp") == 378 * 4
        assert any(row["missing_extracted_completion"] for row in ledger)

        he_ab1 = [
            json.loads(line)
            for line in (out / "samples/humaneval/Ab1-Raw.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert len(he_ab1) == 164
        missing_rows = [row for row in he_ab1 if row.get("solution") == ""]
        assert len(missing_rows) == 149
        assert all("completion" not in row for row in missing_rows)

        plan = json.loads((out / "execution_plan.json").read_text(encoding="utf-8"))
        assert plan["parallel"] == 1
        assert len(plan["sample_files"]) == 8
        pipeline.assert_protected_inputs_unchanged(before, ROOT)
    finally:
        _cleanup_dir(out)


def test_run_full_benchmark_mock_evalplus_builds_paired_ledger() -> None:
    def _fake_evaluate(
        *,
        dataset: str,
        condition: str,
        samples_path: Path,
        eval_output_dir: Path,
        parallel: int,
    ) -> dict[str, dict[str, str]]:
        assert parallel == 1
        eval_output_dir.mkdir(parents=True, exist_ok=True)
        parsed: dict[str, dict[str, str]] = {}
        for line in samples_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            task_id = json.loads(line)["task_id"]
            if (
                dataset == "humaneval"
                and task_id == "HumanEval/0"
                and condition == "Ab1-H2"
            ):
                status = {
                    "base_status": "pass",
                    "plus_status": "pass",
                    "strict_status": "pass",
                }
            elif (
                dataset == "humaneval"
                and task_id == "HumanEval/0"
                and condition == "Ab1-Raw"
            ):
                status = {
                    "base_status": "fail",
                    "plus_status": "fail",
                    "strict_status": "fail",
                }
            else:
                status = {
                    "base_status": "fail",
                    "plus_status": "fail",
                    "strict_status": "fail",
                }
            parsed[task_id] = status
        return parsed

    out = _fresh_dir("mock_full_run")
    try:
        before = pipeline.snapshot_protected_inputs(ROOT)
        result = pipeline.run_full_benchmark(
            dataset="all",
            output_dir=out,
            parallel=1,
            dry_run=False,
            repo_root=ROOT,
            evaluate_fn=_fake_evaluate,
        )
        assert result["status"] == "full_benchmark_evalplus_complete"
        assert result["model_calls"] == 0
        assert result["itt_states"] == 2168
        assert result["paired_rows"] == 1084

        paired = [
            json.loads(line)
            for line in (out / "paired_cell_ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert len(paired) == 1084
        summary = json.loads(
            (out / "aggregate_summary.json").read_text(encoding="utf-8")
        )
        assert summary["verified_rescue"] >= 0
        assert "regression" in summary
        assert "triggered" in summary
        assert "transformed" in summary
        assert "abstained" in summary
        assert summary["model_calls"] == 0
        assert summary["missing_extracted_completion"] > 0
        pipeline.assert_protected_inputs_unchanged(before, ROOT)
    finally:
        _cleanup_dir(out)


def test_run_full_benchmark_rejects_parallel_not_one() -> None:
    import pytest

    out = _fresh_dir("bad_parallel")
    _cleanup_dir(out)
    with pytest.raises(pipeline.H2ReplayError, match="parallel must equal 1"):
        pipeline.run_full_benchmark(
            dataset="humaneval",
            output_dir=out,
            parallel=2,
            dry_run=True,
            repo_root=ROOT,
        )


def test_cli_formal_command_dry_run() -> None:
    out = _fresh_dir("cli_dry")
    try:
        argv = [
            "run-full-benchmark",
            "--dataset",
            "humaneval",
            "--output-dir",
            str(out),
            "--parallel",
            "1",
            "--dry-run",
        ]
        parser = pipeline.build_parser()
        args = parser.parse_args(argv)
        result = args.func(args)
        assert result["itt_states"] == 164 * 4
        assert result["evalplus_executed"] is False
        assert (out / "samples/humaneval/Ab2g-H2.jsonl").is_file()
        assert not (out / "paired_cell_ledger.jsonl").exists()
        plan = json.loads((out / "execution_plan.json").read_text(encoding="utf-8"))
        assert plan["dataset_arg"] == "humaneval"
    finally:
        _cleanup_dir(out)


def test_full_eval_package_stub_and_formal_entrypoint_string() -> None:
    hashes = pipeline.write_full_eval_package_stub(ROOT)
    assert "README.md" in hashes
    status = json.loads(
        (
            ROOT
            / pipeline.FULL_EVAL_PACKAGE_RELATIVE
            / "runner_status.json"
        ).read_text(encoding="utf-8")
    )
    assert status["status"] == "RUNNER_ENABLED_NOT_EXECUTED"
    assert status["manual_run_001_executed"] is False
    assert status["itt_states_expected"] == 2168
    assert status["model_calls"] == 0
    assert (
        "--dataset all" in status["entrypoint"]
        and "--parallel 1" in status["entrypoint"]
        and "manual_run_001" in status["entrypoint"]
    )
