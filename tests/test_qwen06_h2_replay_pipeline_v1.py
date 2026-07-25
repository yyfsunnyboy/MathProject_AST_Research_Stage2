from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from scripts import run_qwen06_h2_replay_pipeline_v1 as pipeline


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / pipeline.OUTPUT_RELATIVE
H2_PATH = ROOT / pipeline.RULE_RELATIVE
AB3_PATHS = [ROOT / relative for relative in pipeline.AB3_BASELINES.values()]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    manifest = __import__("json").loads(
        pipeline.build_smoke_artifact_bytes(ROOT)["pipeline_manifest.json"]
    )
    assert manifest["status"] == pipeline.PIPELINE_STATUS
    assert "full_0.6B_H2_ITT_not_executed" in manifest["non_claims"]
