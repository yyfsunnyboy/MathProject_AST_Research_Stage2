"""Targeted tests for Validation20 Scaffold × Healer v3 runners (no live model/EvalPlus)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze
from scripts import merge_mbpp_validation20_cross_machine_results_v1 as merge
from scripts import preflight_mbpp_validation20_generation_v1 as gen_preflight
from scripts import run_mbpp_validation20_derivatives_v1 as derivatives
from scripts import run_mbpp_validation20_evalplus_qualification_v1 as qual
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
    receipt = gen_preflight.zero_model_preflight(
        model="qwen3.5:4b",
        require_verified_identity=True,
        require_output_absent=True,
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
    receipt = qual.zero_candidate_execution_preflight(model="qwen3.5:9b")
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
    receipt = derivatives.zero_execution_preflight(model="qwen3.5:4b")
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
    report = merge.verify_model_bundle(model_tag="qwen3.5:4b", repo_root=REPO)
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
