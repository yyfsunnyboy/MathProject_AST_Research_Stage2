from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as freeze
from scripts import preflight_candidate_b_4b_development_failure_supply_pilot_v1 as preflight
from scripts import run_candidate_b_4b_development_failure_supply_pilot_v1 as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
GOV_DIR = REPO_ROOT / freeze.OUTPUT_RELATIVE


def _csv_rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_freeze_is_deterministic_200_cells() -> None:
    first = freeze.build_outputs(REPO_ROOT)
    second = freeze.build_outputs(REPO_ROOT)
    assert first == second
    cells = _csv_rows(first["generation_cells.csv"])
    manifest = json.loads(first["manifest.json"])
    assert len(cells) == 200
    assert len({row["generation_id"] for row in cells}) == 200
    assert len({row["cell_identity"] for row in cells}) == 200
    assert len({row["task_id"] for row in cells}) == 20
    assert sorted({row["task_id"] for row in cells}) == sorted(freeze.ACTIVE_TASK_IDS)
    assert sorted({int(row["seed"]) for row in cells}) == list(freeze.SEEDS)
    assert sorted({row["condition_id"] for row in cells}) == ["Ab1_H0", "Ab2g_H1"]
    assert sum(row["condition_id"] == "Ab1_H0" for row in cells) == 100
    assert sum(row["condition_id"] == "Ab2g_H1" for row in cells) == 100
    assert all(row["development_only"] == "true" for row in cells)
    assert all(row["model_tag"] == freeze.MODEL_TAG for row in cells)
    assert all(row["model_digest"] == freeze.MODEL_DIGEST for row in cells)
    assert all(row["completion_flag"] == "pending" for row in cells)
    assert manifest["design"]["raw_program_cells"] == 200
    assert manifest["execution_state"]["model_calls"] == 0
    assert manifest["execution_state"]["preregistered_not_executed"] is True
    assert manifest["model"]["digest"] == freeze.MODEL_DIGEST
    assert len(manifest["model"]["digest"]) == 64
    assert manifest["model"]["public_benchmark_general_execution_allowed"] is False
    assert manifest["parity_with_9b"]["healer_modification_allowed"] is False
    assert manifest["stop_and_expansion_gates"]["auto_expand_to_60_forbidden"] is True


def test_written_artifacts_match_rebuild_and_preflight() -> None:
    rebuilt = freeze.build_outputs(REPO_ROOT)
    for name, payload in rebuilt.items():
        path = GOV_DIR / name
        assert path.is_file(), name
        assert path.read_bytes() == payload
    receipt = preflight.zero_model_preflight(
        repo_root=REPO_ROOT,
        manifest_sha256=_sha256(rebuilt["manifest.json"]),
        require_output_absent=True,
    )
    assert receipt["status"] == "zero_model_preflight_passed"
    assert receipt["cell_count"] == 200
    assert receipt["task_count"] == 20
    assert receipt["condition_count"] == 2
    assert receipt["model_calls"] == receipt["ollama_generation_calls"] == 0
    assert receipt["candidate_code_executions"] == 0
    assert receipt["evalplus_executions"] == 0
    assert receipt["healer_modifications"] == 0


def test_manifest_sha_mismatch_fail_closed() -> None:
    with pytest.raises(preflight.PilotPreflightError, match="manifest SHA mismatch"):
        preflight.zero_model_preflight(
            repo_root=REPO_ROOT,
            manifest_sha256="0" * 64,
            require_output_absent=False,
        )


def test_development_only_and_forbidden_splits() -> None:
    manifest = json.loads((GOV_DIR / "manifest.json").read_text(encoding="utf-8"))
    policy = manifest["split_policy"]
    assert policy["forbid_validation"] is True
    assert policy["forbid_confirmatory"] is True
    assert policy["forbid_sealed_reserve"] is True
    assert policy["forbid_humaneval_plus_external"] is True
    assert policy["task_ids"] == list(freeze.ACTIVE_TASK_IDS)
    assert policy["frozen_split_sha256"] == freeze.EXPECTED_FROZEN_SPLIT_SHA256


def test_output_isolation_from_9b_paths() -> None:
    manifest = json.loads((GOV_DIR / "manifest.json").read_text(encoding="utf-8"))
    pilot = freeze.RUN_OUTPUT_RELATIVE.as_posix()
    for relative in manifest["parity_with_9b"]["isolated_from_9b_output_dirs"]:
        assert relative != pilot
        assert "qwen35_4b_failure_supply_pilot" not in relative
    assert "mbpp_qwen35_4b_failure_supply_pilot" in pilot


def _local_tmpdir(name: str) -> Path:
    root = REPO_ROOT / ".tmp_pilot_tests" / name
    if root.exists():
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_existing_output_refused_by_default_preflight() -> None:
    out_dir = REPO_ROOT / freeze.RUN_OUTPUT_RELATIVE
    if out_dir.exists() and any(out_dir.iterdir()):
        with pytest.raises(preflight.PilotPreflightError, match="already present"):
            preflight.zero_model_preflight(require_output_absent=True)
    else:
        receipt = preflight.zero_model_preflight(require_output_absent=True)
        assert receipt["require_output_absent"] is True


def test_resume_mismatch_fail_closed() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_mismatch") / "run"
    journal_dir = run_dir / "j"
    journal_dir.mkdir(parents=True)
    bad = {
        "cell_identity": cell["cell_identity"],
        "model_tag": cell["model_tag"],
        "model_digest": "deadbeef" * 8,
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "condition_id": cell["condition_id"],
        "seed": int(cell["seed"]),
        "completion_flag": "success",
        "generation_status": "success",
        "raw_response": "print(1)\n",
    }
    (journal_dir / f"{cell['generation_id']}.json").write_text(
        json.dumps(bad),
        encoding="utf-8",
    )
    with pytest.raises(runner.PilotRunError, match="resume identity mismatch on model_digest"):
        runner.decide_resume_action(cell, run_dir)


def test_resume_exact_match_skips() -> None:
    cells = runner.load_frozen_cells()
    cell = cells[0]
    run_dir = _local_tmpdir("resume_match") / "run"
    journal_dir = run_dir / "j"
    journal_dir.mkdir(parents=True)
    good = {
        "cell_identity": cell["cell_identity"],
        "model_tag": cell["model_tag"],
        "model_digest": cell["model_digest"],
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "condition_id": cell["condition_id"],
        "seed": int(cell["seed"]),
        "completion_flag": "success",
        "generation_status": "success",
        "raw_response": "def f():\n    return 1\n",
    }
    (journal_dir / f"{cell['generation_id']}.json").write_text(
        json.dumps(good),
        encoding="utf-8",
    )
    assert runner.decide_resume_action(cell, run_dir) == "skip"
    assert runner.decide_resume_action(cells[1], run_dir) == "generate"


def test_generate_command_refuses_without_gates() -> None:
    with pytest.raises(runner.PilotRunError, match="generate refused"):
        runner.main(["generate"])


def test_generate_remains_disabled_even_with_gates() -> None:
    with pytest.raises(runner.PilotRunError, match="not enabled in this packaging commit"):
        runner.main(
            [
                "generate",
                "--i-understand-this-calls-the-model",
                "--execute-model",
                "--manifest-sha256",
                _sha256((GOV_DIR / "manifest.json").read_bytes()),
            ]
        )


def test_source_scripts_do_not_call_models_or_evalplus_or_healer_writes() -> None:
    texts = [
        (REPO_ROOT / "scripts/freeze_candidate_b_4b_development_failure_supply_pilot_v1.py").read_text(
            encoding="utf-8"
        ),
        (REPO_ROOT / "scripts/preflight_candidate_b_4b_development_failure_supply_pilot_v1.py").read_text(
            encoding="utf-8"
        ),
        (REPO_ROOT / "scripts/run_candidate_b_4b_development_failure_supply_pilot_v1.py").read_text(
            encoding="utf-8"
        ),
    ]
    joined = "\n".join(texts)
    assert "run_attempt(" not in joined
    assert "check_correctness" not in joined
    assert "import evalplus" not in joined
    assert "from evalplus" not in joined
    assert "mbpp_evaluator_blind_healer" in joined  # SHA pin only
    assert "apply_healer" not in joined
    assert "heal(" not in joined


def test_preregistration_document_claims() -> None:
    text = (GOV_DIR / "preregistration.md").read_text(encoding="utf-8")
    assert "尚未呼叫模型" in text
    assert "尚未產生任何 4B raw program" in text
    assert "尚未修改 Healer" in text
    assert freeze.MODEL_DIGEST in text
    assert "不得自動擴展至 60 題" in text
    assert "不宣稱已找到新的通用 Healer 規則" in text


def test_report_coverage_numbers_are_consistent() -> None:
    report = (
        REPO_ROOT
        / "docs/決賽文件/7月23Candidate_B_r003_198格失敗分類與Healer安全邊界報告.md"
    )
    text = report.read_text(encoding="utf-8")
    assert "| 合法 development task 母體 | **116** |" in text
    assert "| development60 實際涵蓋 distinct tasks | **60** |" in text
    assert "| H0 總格數 | **300** |" in text
    assert "| H0 失敗格數（EvalPlus plus=fail） | **224** |" in text
    assert "| Conditional 23 實際 coverage | **23** |" in text
    assert "不得把總格數寫成失敗格數" in text
    assert "GENERAL_HEALER_ABSTAIN" in text
    assert "不得宣稱已窮盡所有可能 Healer 機制" in text
    assert "public test 或修後 PASS 不得作為 Healer 接受修改的 oracle gate" in text
    # Must not still claim all 300 H0 cells are failures.
    assert "這 300 個 H0 cells 均為失敗案例" not in text
