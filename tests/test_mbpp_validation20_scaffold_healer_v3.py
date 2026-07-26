"""Targeted tests for Validation20 Scaffold × Healer v3 runners (no live model/EvalPlus)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze
from scripts import merge_mbpp_validation20_cross_machine_results_v1 as merge
from scripts import preflight_mbpp_validation20_generation_v1 as gen_preflight
from scripts import run_mbpp_validation20_derivatives_v1 as derivatives
from scripts import run_mbpp_validation20_evalplus_qualification_v1 as qual
from scripts import run_mbpp_validation20_execution_diagnostics_v1 as diagnostics
from scripts import run_mbpp_validation20_generation_v1 as gen


REPO = Path(__file__).resolve().parents[1]


def test_freeze_check_deterministic() -> None:
    outputs = freeze.build_outputs(REPO)
    assert len(outputs) >= 12
    for relative, payload in outputs.items():
        path = REPO / relative
        assert path.is_file()
        assert path.read_bytes() == payload


def test_h4_rule_matches_8954a257_archive() -> None:
    digest = freeze.source_hashes(REPO)[freeze.H4_RELATIVE.as_posix()]
    assert digest == freeze.H4_RULE_SHA256
    assert freeze.H4_ARCHIVE_COMMIT.startswith("8954a257")


def test_no_2b_in_allowed_models() -> None:
    assert all("2b" not in tag.lower() for tag in freeze.ALLOWED_MODEL_TAGS)
    assert set(freeze.ALLOWED_MODEL_TAGS) == {
        "qwen3.5:4b",
        "qwen3.5:9b",
        "qwen3:0.6b",
    }


def test_validation20_task_roster() -> None:
    tasks = freeze.load_validation_tasks(REPO)
    assert [row["task_id"] for row in tasks] == list(freeze.VALIDATION_TASK_IDS)
    assert len(tasks) == 20


def test_per_model_cells_are_400_and_isolated() -> None:
    tasks = freeze.load_validation_tasks(REPO)
    ab2g = freeze.load_ab2g_text(REPO)
    for tag in freeze.ALLOWED_MODEL_TAGS:
        cells = freeze.build_generation_cells(model_tag=tag, tasks=tasks, ab2g_text=ab2g)
        assert len(cells) == 400
        assert {row["model_tag"] for row in cells} == {tag}
        assert all(row["validation_only"] == "true" for row in cells)


def test_generation_preflight_zero_model_call_4b() -> None:
    out_dir = REPO / freeze.MODEL_SPECS["qwen3.5:4b"]["run_output_relative"]
    receipt = gen_preflight.zero_model_preflight(
        model="qwen3.5:4b",
        require_verified_identity=True,
        require_output_absent=not out_dir.exists(),
    )
    assert receipt["model_calls"] == 0
    assert receipt["ollama_generation_calls"] == 0
    assert receipt["candidate_program_executed"] is False
    assert receipt["evalplus_executed"] is False
    assert receipt["cell_count"] == 400


def test_generation_preflight_06b_allows_pending_identity() -> None:
    receipt = gen_preflight.zero_model_preflight(
        model="qwen3:0.6b",
        require_verified_identity=False,
        require_output_absent=True,
    )
    assert receipt["identity_status"] == "pending_machine_verification"
    with pytest.raises(gen_preflight.PreflightError):
        gen_preflight.zero_model_preflight(
            model="qwen3:0.6b",
            require_verified_identity=True,
            require_output_absent=True,
        )


def test_reject_foreign_model_tag() -> None:
    with pytest.raises(gen_preflight.PreflightError):
        gen_preflight.resolve_model_tag("qwen3.5:2b")


def test_sha_mismatch_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    rel = freeze.model_dir("qwen3.5:4b") / "model_manifest.json"
    path = REPO / rel
    original = path.read_bytes()
    corrupted = bytearray(original)
    corrupted[-2] ^= 0x01

    real_build = freeze.build_outputs

    def _build_with_corrupt_expectation(repo_root: Path = REPO):
        outputs = real_build(repo_root)
        outputs[rel.as_posix()] = bytes(corrupted)
        return outputs

    monkeypatch.setattr(freeze, "build_outputs", _build_with_corrupt_expectation)
    with pytest.raises(gen_preflight.PreflightError, match="model manifest drift"):
        gen_preflight.zero_model_preflight(model="qwen3.5:4b")


def test_manifest_rebuild_detects_byte_identity() -> None:
    rebuilt = freeze.build_outputs(REPO)
    rel = (freeze.model_dir("qwen3.5:9b") / "generation_cells.csv").as_posix()
    assert (REPO / rel).read_bytes() == rebuilt[rel]
    assert hashlib.sha256(rebuilt[rel]).hexdigest() == hashlib.sha256(
        (REPO / rel).read_bytes()
    ).hexdigest()


def test_evalplus_preflight_zero_candidate_execution() -> None:
    eval_dir = REPO / freeze.MODEL_SPECS["qwen3.5:9b"]["evalplus_output_relative"]
    receipt = qual.zero_candidate_execution_preflight(
        model="qwen3.5:9b", require_output_absent=not eval_dir.exists()
    )
    assert receipt["planned_eval_cells"] == 1200
    assert receipt["candidate_program_executed"] is False
    assert receipt["candidate_program_imported"] is False
    assert receipt["candidate_program_compiled"] is False
    assert receipt["evalplus_executed"] is False
    assert receipt["model_calls"] == 0


def test_evalplus_output_must_not_point_at_existing_formal_run() -> None:
    banned = REPO / "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1"
    with pytest.raises(qual.QualificationError):
        qual.assert_not_existing_formal_run(banned, REPO)


def test_raw_final_pairing_plan() -> None:
    planned = qual.build_eval_cells_plan("qwen3.5:4b")
    assert len(planned) == 1200
    by_gen: dict[str, set[str]] = {}
    for row in planned:
        by_gen.setdefault(row["generation_id"], set()).add(row["stage"])
    assert len(by_gen) == 400
    assert all(stages == set(freeze.STAGES) for stages in by_gen.values())


def test_derivatives_preflight_zero_execution() -> None:
    eval_dir = REPO / freeze.MODEL_SPECS["qwen3.5:4b"]["evalplus_output_relative"]
    receipt = derivatives.zero_execution_preflight(
        model="qwen3.5:4b", require_output_absent=not eval_dir.exists()
    )
    assert receipt["candidate_program_executed"] is False
    assert receipt["evalplus_executed"] is False
    assert receipt["model_calls"] == 0
    assert receipt["healer_uses_pass_fail"] is False


def test_h1_to_h4_order_fixed_on_sample() -> None:
    source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    result = derivatives.derive_one_cell(
        cell={
            "generation_id": "x",
            "cell_identity": "y",
            "task_id": "Mbpp/4",
            "seed": "11",
            "prompt_condition": "Ab1",
            "model_tag": "qwen3.5:4b",
            "expected_entry_point": "solve",
            "expected_positional_arities": "1",
        },
        raw_response=source,
        official_prompt="assert solve(1) == 2\n",
    )
    assert list(result["stages"]) == list(freeze.STAGES)
    assert result["evalplus_executed"] is False
    assert result["candidate_program_executed"] is False


def test_derivatives_persisted_incomplete_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Build a dummy repo layout
    run_dir = tmp_path / "artifacts/public_benchmark_development/mbpp_validation20/qwen35_4b/runs/mbpp_validation20_qwen35_4b_r001"
    j_dir = run_dir / "j"
    j_dir.mkdir(parents=True, exist_ok=True)
    
    # Create cell CSV and task structure
    cell = {
        "cell_identity": "c1",
        "generation_id": "gen_incomplete",
        "task_id": "Mbpp/4",
        "seed": "11",
        "prompt_condition": "Ab1",
        "model_tag": "qwen3.5:4b",
        "model_key": "qwen35_4b",
        "operator_role": "local_team",
        "sample_index": "0",
        "composed_prompt_sha256": "p" * 64,
        "expected_entry_point": "heap_queue_clean",
        "expected_positional_arities": "1",
        "validation_only": "true",
        "forbid_development_substitute": "true",
    }
    
    # Mock journal with persisted_complete = False
    incomplete_journal = {
        "generation_id": "gen_incomplete",
        "completion_flag": "failed",
        "persisted_complete": False,
        "raw_response": "some text",
        "raw_response_sha256": hashlib.sha256(b"some text").hexdigest(),
    }
    (j_dir / "gen_incomplete.json").write_text(json.dumps(incomplete_journal), encoding="utf-8")

    # Mock freeze.model_dir and freeze.load_validation_tasks
    monkeypatch.setattr(freeze, "load_validation_tasks", lambda repo_root: [{"task_id": "Mbpp/4", "prompt": "assert heap_queue_clean([1]) == [1]\n", "entry_point": "heap_queue_clean"}])

    def mock_read_csv(p: Path):
        if "generation_cells.csv" in p.name:
            return [cell]
        return []

    monkeypatch.setattr(derivatives, "_read_csv", mock_read_csv)
    monkeypatch.setattr(derivatives, "zero_execution_preflight", lambda **kw: None)

    with pytest.raises(derivatives.DerivativeError, match="raw journal not persisted_complete"):
        derivatives.materialize(
            model="qwen3.5:4b",
            acknowledgement=derivatives.DERIVATIVE_ACK,
            repo_root=tmp_path,
        )


def test_derivatives_ambiguous_extraction_legally_abstains() -> None:
    # Ambiguous response with two code blocks
    ambiguous_response = (
        "Here is first idea:\n```python\ndef solve(x):\n    return x\n```\n"
        "Here is second idea:\n```python\ndef solve(x):\n    return x + 1\n```\n"
    )
    cell = {
        "generation_id": "gen_ambiguous",
        "cell_identity": "c_ambiguous",
        "task_id": "Mbpp/4",
        "seed": "11",
        "prompt_condition": "Ab1",
        "model_tag": "qwen3.5:4b",
        "expected_entry_point": "solve",
        "expected_positional_arities": "1",
    }
    result = derivatives.derive_one_cell(
        cell=cell,
        raw_response=ambiguous_response,
        official_prompt="assert solve(1) == 2\n",
    )
    pipeline_stage = result["stages"]["pipeline_corrected"]
    post_stage = result["stages"]["post_h1_h2_h3_h4"]
    
    assert pipeline_stage["source"] is None
    assert pipeline_stage["extraction_status"] == "ambiguous"
    assert post_stage["source"] is None
    assert post_stage["decision"] == "abstained"


def test_derivatives_success_normal_materialize() -> None:
    clean_response = "```python\ndef solve(x):\n    return x + 1\n```"
    cell = {
        "generation_id": "gen_clean",
        "cell_identity": "c_clean",
        "task_id": "Mbpp/4",
        "seed": "11",
        "prompt_condition": "Ab1",
        "model_tag": "qwen3.5:4b",
        "expected_entry_point": "solve",
        "expected_positional_arities": "1",
    }
    result = derivatives.derive_one_cell(
        cell=cell,
        raw_response=clean_response,
        official_prompt="assert solve(1) == 2\n",
    )
    pipeline_stage = result["stages"]["pipeline_corrected"]
    post_stage = result["stages"]["post_h1_h2_h3_h4"]

    assert pipeline_stage["source"].strip() == "def solve(x):\n    return x + 1"
    assert pipeline_stage["extraction_status"] == "extracted"
    assert post_stage["source"] is not None


def test_raw_journal_not_modified_during_derivatives() -> None:
    journal_path = (
        REPO
        / "artifacts/public_benchmark_development/mbpp_validation20/qwen35_4b/runs/mbpp_validation20_qwen35_4b_r001/j/377c4fea1200c812d952c374d0589a2212c55a98c1a54bcab220944a6c57397b.json"
    )
    if journal_path.is_file():
        before_bytes = journal_path.read_bytes()
        journal_data = json.loads(before_bytes.decode("utf-8"))
        cell = {
            "generation_id": journal_data["generation_id"],
            "cell_identity": journal_data["cell_identity"],
            "task_id": journal_data["task_id"],
            "seed": str(journal_data["seed"]),
            "prompt_condition": journal_data["prompt_condition"],
            "model_tag": journal_data["model_tag"],
            "expected_entry_point": "lps",
            "expected_positional_arities": "1",
        }
        _ = derivatives.derive_one_cell(
            cell=cell,
            raw_response=journal_data["raw_response"],
            official_prompt="assert lps('TENS FOR TENS') == 5\n",
        )
        after_bytes = journal_path.read_bytes()
        assert before_bytes == after_bytes



def test_derived_summary_priority_and_partial_not_rescue() -> None:
    assert freeze.DERIVED_SUMMARY_PRIORITY[0] == "invalid_or_missing_candidate"
    assert freeze.DERIVED_SUMMARY_PRIORITY[2] == "verified_rescue"
    assert (
        qual.derive_mutex_summary(
            raw_pass=False,
            final_pass=False,
            decision="transformed",
            repair_depth=["partial_repair"],
            invalid=False,
            infra_failure=False,
        )
        == "partial_repair"
    )
    assert (
        qual.derive_mutex_summary(
            raw_pass=False,
            final_pass=True,
            decision="transformed",
            repair_depth=["partial_repair"],
            invalid=False,
            infra_failure=False,
        )
        == "verified_rescue"
    )
    assert (
        qual.derive_mutex_summary(
            raw_pass=True,
            final_pass=False,
            decision="transformed",
            repair_depth=[],
            invalid=False,
            infra_failure=False,
        )
        == "execution_regression"
    )
    assert (
        qual.derive_mutex_summary(
            raw_pass=False,
            final_pass=False,
            decision="abstained",
            repair_depth=[],
            invalid=False,
            infra_failure=True,
        )
        == "evaluator_infrastructure_failure"
    )


def test_resume_skip_requires_full_identity() -> None:
    cell = {
        "cell_identity": "c1",
        "generation_id": "g1",
        "model_tag": "qwen3.5:4b",
        "composed_prompt_sha256": "p" * 64,
        "prompt_condition": "Ab1",
        "seed": "11",
    }
    good = {
        "cell_identity": "c1",
        "generation_id": "g1",
        "model_tag": "qwen3.5:4b",
        "model_digest": "d" * 64,
        "composed_prompt_sha256": "p" * 64,
        "prompt_condition": "Ab1",
        "seed": 11,
        "completion_flag": "success",
        "persisted_complete": True,
        "manifest_sha256": "m" * 64,
    }
    assert gen.resume_skip_eligible(
        good, cell=cell, model_digest="d" * 64, manifest_sha256="m" * 64
    )
    bad = dict(good)
    bad["persisted_complete"] = False
    assert not gen.resume_skip_eligible(
        bad, cell=cell, model_digest="d" * 64, manifest_sha256="m" * 64
    )


def test_merge_reports_incomplete_without_runs() -> None:
    report = merge.verify_model_bundle(model_tag="qwen3:0.6b", repo_root=REPO)
    assert report["complete"] is False
    assert report["missing_artifacts"]


def test_counts_1200_and_3600() -> None:
    master = json.loads(
        (REPO / freeze.ARTIFACT_RELATIVE / "master_manifest.json").read_text(encoding="utf-8")
    )
    assert master["counts"]["immutable_candidates"] == 1200
    assert master["counts"]["evalplus_stage_evaluations"] == 3600
    assert master["counts"]["local_team_candidates"] == 800
    assert master["counts"]["classmate_candidates"] == 400
    assert master["2b_forbidden"] is True


def test_execution_diagnostics_preflight() -> None:
    receipt = diagnostics.zero_candidate_execution_preflight(
        model="qwen3.5:4b", require_output_absent=False
    )
    assert receipt["status"] == "zero_candidate_execution_diagnostics_preflight_passed"
    assert receipt["candidate_program_executed"] is False
    assert receipt["evalplus_executed"] is False
    assert receipt["model_calls"] == 0
    assert receipt["stages_analyzed"] == ["pipeline_corrected", "post_h1_h2_h3_h4"]


def test_classify_candidate_execution_categories() -> None:
    inputs = [[[1, 2], 1]]
    outputs = [[1]]

    # 1. missing_candidate
    res1 = diagnostics.run_isolated_stage_eval(source=None, entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res1["category"] == "missing_candidate"

    # 2. syntax_blocked
    res2 = diagnostics.run_isolated_stage_eval(source="def foo(:", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res2["category"] == "syntax_blocked"

    # 3. import_or_load_blocked
    res3 = diagnostics.run_isolated_stage_eval(source="import non_existent_package_xyz", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res3["category"] == "import_or_load_blocked"

    # 4. entry_point_blocked
    res4 = diagnostics.run_isolated_stage_eval(source="def wrong_name(): pass", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res4["category"] == "entry_point_blocked"

    # 5. runtime_exception
    res5 = diagnostics.run_isolated_stage_eval(source="def foo(a, b):\n    raise ValueError('err')", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res5["category"] == "runtime_exception"

    # 6. executed_but_incorrect
    res6 = diagnostics.run_isolated_stage_eval(source="def foo(a, b):\n    return [99]", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res6["category"] == "executed_but_incorrect"

    # 7. passed
    res7 = diagnostics.run_isolated_stage_eval(source="def foo(a, b):\n    return [1]", entry_point="foo", arities=(1,), inputs=inputs, outputs=outputs)
    assert res7["category"] == "passed"


def test_classify_transition_categories() -> None:
    # verified_rescue
    t1 = diagnostics.classify_transition("syntax_blocked", "passed")
    assert t1["transition_category"] == "verified_rescue"
    assert t1["verified_rescue"] == "true"

    # blocker_removed_but_incorrect
    t2 = diagnostics.classify_transition("syntax_blocked", "executed_but_incorrect")
    assert t2["transition_category"] == "blocker_removed_but_incorrect"

    # preserved_executable
    t3 = diagnostics.classify_transition("passed", "passed")
    assert t3["transition_category"] == "preserved_executable"

    # unchanged_blocked
    t4 = diagnostics.classify_transition("syntax_blocked", "syntax_blocked")
    assert t4["transition_category"] == "unchanged_blocked"

    # abstained
    t5 = diagnostics.classify_transition("missing_candidate", "missing_candidate")
    assert t5["transition_category"] == "abstained"


def test_isolated_eval_infinite_loop_timeout() -> None:
    source = "def solve(x):\n    while True:\n        pass\n"
    res = diagnostics.run_isolated_stage_eval(
        source=source,
        entry_point="solve",
        arities=(1,),
        inputs=[[[1]]],
        outputs=[[1]],
        timeout=0.5,
    )
    assert res["category"] == "timeout"
    assert "timeout" in res["detail"]


def test_isolated_eval_input_non_blocking() -> None:
    source = "def solve(x):\n    val = input('enter:')\n    return int(val)\n"
    res = diagnostics.run_isolated_stage_eval(
        source=source,
        entry_point="solve",
        arities=(1,),
        inputs=[[[1]]],
        outputs=[[1]],
        timeout=2.0,
    )
    assert res["category"] in ("runtime_exception", "import_or_load_blocked")
    assert "EOFError" in res["detail"]


def test_isolated_eval_large_stdout_captured() -> None:
    source = "def solve(x):\n    print('A' * 50000)\n    return x\n"
    res = diagnostics.run_isolated_stage_eval(
        source=source,
        entry_point="solve",
        arities=(1,),
        inputs=[[[1]]],
        outputs=[[1]],
        timeout=2.0,
    )
    assert res["category"] == "passed"
    assert len(res.get("stdout_snippet", "")) <= 1000


def test_isolated_eval_runtime_exception_classified() -> None:
    source = "def solve(x):\n    return x[999]\n"
    res = diagnostics.run_isolated_stage_eval(
        source=source,
        entry_point="solve",
        arities=(1,),
        inputs=[[[1]]],
        outputs=[[1]],
        timeout=2.0,
    )
    assert res["category"] == "runtime_exception"
    assert "IndexError" in res["detail"]


def test_isolated_eval_distinct_pid() -> None:
    source = "def solve(x):\n    return x\n"
    res = diagnostics.run_isolated_stage_eval(
        source=source,
        entry_point="solve",
        arities=(1,),
        inputs=[[[1]]],
        outputs=[[1]],
        timeout=2.0,
    )
    assert res["worker_pid"] is not None
    assert res["worker_pid"] != os.getpid()


def test_preflight_does_not_create_output_dir() -> None:
    target_dir = REPO / freeze.ARTIFACT_RELATIVE / "diagnostics/qwen35_4b"
    receipt = diagnostics.zero_candidate_execution_preflight(
        model="qwen3.5:4b", require_output_absent=False
    )
    assert receipt["status"] == "zero_candidate_execution_diagnostics_preflight_passed"
    assert receipt["output_directory"] == target_dir.as_posix()

