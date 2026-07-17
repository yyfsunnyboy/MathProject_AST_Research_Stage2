from __future__ import annotations

import json
import hashlib
from collections import Counter
from pathlib import Path

import pytest

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask
from scripts import freeze_mbpp_scaffold_v0_protocol as frozen
from scripts import run_mbpp_scaffold_v0_development as driver


REPO_ROOT = Path(__file__).resolve().parents[2]


EXPECTED_SCAFFOLD = (
    "Return exactly one complete Python source file.\n"
    "Do not use Markdown code fences.\n"
    "Do not include explanations, analysis, assertions, tests, print statements, example calls, or alternative implementations.\n"
    "Implement the exact function name and parameter list required by the task.\n"
    "Include every import required by the submitted program.\n"
    "Do not rename or redefine the requested public function.\n"
    "The response must begin with Python code and contain no text outside the source file.\n"
)


def test_scaffold_exact_bytes_and_hash_are_frozen():
    path = REPO_ROOT / frozen.SCAFFOLD_RELATIVE

    assert frozen.SCAFFOLD_TEXT == EXPECTED_SCAFFOLD
    assert path.read_bytes() == EXPECTED_SCAFFOLD.encode("utf-8")
    assert frozen.SCAFFOLD_SHA256 == (
        "31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305"
    )
    assert frozen.sha256_bytes(path.read_bytes()) == frozen.SCAFFOLD_SHA256


def test_manifest_contains_exact_bytes_and_no_solution_material():
    manifest = frozen.build_manifest(REPO_ROOT)
    committed = json.loads((REPO_ROOT / frozen.MANIFEST_RELATIVE).read_text(encoding="utf-8"))

    assert manifest == committed
    assert bytes.fromhex(manifest["exact_bytes_hex"]) == frozen.SCAFFOLD_BYTES
    assert manifest["exact_text_utf8"].encode("utf-8") == frozen.SCAFFOLD_BYTES
    assert manifest["contains_task_answers"] is False
    assert manifest["contains_test_answers"] is False
    assert manifest["contains_dataset_specific_solution_guidance"] is False
    assert manifest["prompt_composition_order"] == [
        "official_task_prompt_verbatim",
        "fixed_separator",
        frozen.SCAFFOLD_VERSION,
    ]


def test_p1_plan_is_exact_p0_twenty_by_five_schedule():
    plan = frozen.build_plan(REPO_ROOT)
    committed = json.loads((REPO_ROOT / frozen.PLAN_RELATIVE).read_text(encoding="utf-8"))
    p0 = json.loads((REPO_ROOT / frozen.P0_PLAN_RELATIVE).read_text(encoding="utf-8"))

    assert plan == committed
    assert plan["run_id"] == frozen.RUN_ID
    assert plan["run_id"] != p0["run_id"]
    assert plan["task_ids"] == p0["task_ids"]
    assert len(plan["task_ids"]) == len(set(plan["task_ids"])) == 20
    assert plan["seeds"] == [11, 22, 33, 44, 55]
    assert len(plan["cells"]) == plan["expected_cells"] == 100
    assert Counter(cell["task_id"] for cell in plan["cells"]) == {
        task_id: 5 for task_id in p0["task_ids"]
    }
    assert all(
        [cell["seed"] for cell in plan["cells"] if cell["task_id"] == task_id]
        == frozen.SEEDS
        for task_id in p0["task_ids"]
    )


def test_every_composed_prompt_hash_is_byte_reproducible():
    plan = frozen.build_plan(REPO_ROOT)
    tasks = {
        row["task_id"]: row
        for row in frozen.load_selected_task_records(REPO_ROOT, plan["task_ids"])
    }

    for cell in plan["cells"]:
        task = tasks[cell["task_id"]]
        composed = task["prompt"] + frozen.PROMPT_SEPARATOR + frozen.SCAFFOLD_TEXT
        assert frozen.compose_prompt(task["prompt"]) == composed
        assert frozen.sha256_text(task["prompt"]) == cell["official_prompt_sha256"]
        assert frozen.sha256_text(composed) == cell["composed_prompt_sha256"]
        assert (
            frozen.generation_id(cell["task_id"], cell["seed"], cell["composed_prompt_sha256"])
            == cell["generation_id"]
        )
    assert len({cell["generation_id"] for cell in plan["cells"]}) == 100


def test_model_protocol_timeout_and_no_healer_are_frozen_to_p0():
    plan = driver.load_frozen_plan(REPO_ROOT)
    p0 = json.loads((REPO_ROOT / frozen.P0_PLAN_RELATIVE).read_text(encoding="utf-8"))
    protocol = json.loads((REPO_ROOT / frozen.PROTOCOL_RELATIVE).read_text(encoding="utf-8"))

    assert plan["model"] == p0["model"] == "qwen3.5:9b"
    assert plan["model_digest"] == p0["model_digest"] == frozen.MODEL_DIGEST
    assert plan["quantization"] == protocol["models"]["primary_development_model"]["quantization"] == "Q4_K_M"
    assert plan["generation_parameters"] == protocol["generation"]
    assert plan["generation_parameters"]["thinking"] is False
    assert plan["ollama_request_timeout_seconds"] == 600.0
    assert plan["ollama_request_timeout_source"] == (
        "P0 run_003 actual generation command (--timeout-seconds 600)"
    )
    assert not any(plan[key] for key in ("retry", "selective_retry", "resume", "overwrite", "healer"))
    assert plan["accounts"] == ["observed", "pipeline_corrected"]
    assert plan["pipeline_correction_is_healer"] is False


def test_plan_scope_uses_only_p0_active_development_ids():
    plan = frozen.build_plan(REPO_ROOT)
    p0 = json.loads((REPO_ROOT / frozen.P0_PLAN_RELATIVE).read_text(encoding="utf-8"))

    assert set(plan["task_ids"]) == set(p0["task_ids"])
    assert {cell["task_id"] for cell in plan["cells"]} == set(p0["task_ids"])
    assert set(frozen.load_selected_task_records(REPO_ROOT, plan["task_ids"])[0]) == {
        "task_id",
        "prompt",
        "entry_point",
    }


def test_frozen_rendering_is_byte_deterministic():
    first = frozen.frozen_outputs(REPO_ROOT)
    second = frozen.frozen_outputs(REPO_ROOT)

    assert first == second
    for relative_path, expected in first.items():
        assert (REPO_ROOT / relative_path).read_bytes() == expected


def test_generation_rejects_wrong_timeout_before_any_model_call(monkeypatch):
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("model provenance must not be called")

    monkeypatch.setattr(driver, "fetch_ollama_provenance", forbidden)
    with pytest.raises(driver.ScaffoldRunError, match="timeout"):
        driver.generate(
            run_id=frozen.RUN_ID,
            base_url="http://127.0.0.1:1",
            timeout_seconds=300.0,
        )
    assert called is False


def test_driver_has_no_retry_resume_or_overwrite_cli_flags():
    parser = driver.build_parser()
    generation = parser.parse_args(
        ["generate", "--run-id", frozen.RUN_ID, "--timeout-seconds", "600"]
    )
    evaluation = parser.parse_args(["evaluate", "--run-id", frozen.RUN_ID])

    assert generation.command == "generate"
    assert generation.timeout_seconds == 600.0
    assert evaluation.command == "evaluate"
    for name in ("retry", "selective_retry", "resume", "overwrite", "healer"):
        assert not hasattr(generation, name)
        assert not hasattr(evaluation, name)


def test_synthetic_per_cell_journal_is_durable_and_immutable(tmp_path):
    cell = {
        "generation_id": "a" * 64,
        "cell_index": 1,
        "task_id": "Synthetic/1",
        "seed": 11,
        "sample_index": 0,
    }
    record = {
        "generation_id": "a" * 64,
        "status": "synthetic_no_model_call",
        "raw_response": "def synthetic():\n    return 1\n",
    }
    journal = tmp_path / "journal"

    driver._persist_attempt_journal(journal, cell=cell, record=record)
    assert json.loads((journal / (("a" * 64) + ".json")).read_text(encoding="utf-8")) == record
    with pytest.raises(driver.PersistenceError, match="refusing to overwrite"):
        driver._persist_attempt_journal(journal, cell=cell, record=record)


def test_synthetic_complete_record_preserves_composed_request_without_calling_model():
    task = PublicBenchmarkTask(
        benchmark="mbpp",
        task_id="Synthetic/1",
        prompt="def requested(x):\n",
        entry_point="requested",
        canonical_solution=None,
    )
    composed = frozen.compose_prompt(task.prompt)
    raw = "def requested(x):\n    return x\n"
    body = {
        "model": frozen.MODEL,
        "created_at": "synthetic",
        "message": {"role": "assistant", "content": raw},
        "done": True,
        "done_reason": "stop",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
    }
    cell = {
        "generation_id": "b" * 64,
        "cell_index": 1,
        "task_id": task.task_id,
        "seed": 11,
        "sample_index": 0,
    }
    attempt = {
        "status": "success",
        "raw_response": raw,
        "generation_latency": 0.0,
        "ollama_response_metadata": {
            "request_payload": {
                "model": frozen.MODEL,
                "messages": [{"role": "user", "content": composed}],
                "think": False,
            },
            "raw_body": json.dumps(body),
        },
    }

    record = driver._complete_raw_record(
        cell=cell,
        task=task,
        official_prompt=task.prompt,
        composed_prompt=composed,
        attempt=attempt,
    )
    assert record is not None
    assert record["request"]["messages"][0]["content"] == composed
    assert record["retry_count"] == 0
    assert record["healer"] is False
    assert record["pipeline_correction_applied_during_generation"] is False


def test_operator_guide_has_one_generation_and_one_wsl_evaluation_command():
    guide = (REPO_ROOT / frozen.GUIDE_RELATIVE).read_text(encoding="utf-8")

    windows_command = (
        "py -3.12 -B .\\scripts\\run_mbpp_scaffold_v0_development.py generate "
        "--run-id mbpp_qwen35_9b_scaffold_v0_dev_run_001 "
        "--base-url http://127.0.0.1:11434 --timeout-seconds 600"
    )
    assert guide.count(windows_command) == 1
    assert guide.count("wsl -d Ubuntu") == 1
    assert guide.count("cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2") == 1
    assert guide.count(
        "/home/yehya/.venvs/ast_evalplus/bin/python "
        "scripts/run_mbpp_scaffold_v0_development.py evaluate \\\n"
        "  --run-id mbpp_qwen35_9b_scaffold_v0_dev_run_001 \\\n"
        "  --parallel 4"
    ) == 1
    assert ".venv\\Scripts\\python.exe" not in guide
    assert "python3 scripts/run_mbpp_scaffold_v0_development.py" not in guide
    assert guide.count(frozen.RUN_ID) >= 3
    assert "本輪未執行" in guide
    assert "Pipeline correction 不是 Healer" in guide


def test_protocol_freeze_did_not_create_a_p1_run_directory():
    assert not driver.resolve_run_dir(frozen.RUN_ID).exists()


def test_corrective_revision_preserves_all_research_identity_fields():
    plan = frozen.build_plan(REPO_ROOT)
    invariant_keys = (
        "task_ids",
        "seeds",
        "model",
        "model_digest",
        "quantization",
        "generation_parameters",
        "scaffold_sha256",
        "separator_sha256",
        "cells",
    )
    invariant = {key: plan[key] for key in invariant_keys}
    material = (
        json.dumps(invariant, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")

    assert hashlib.sha256(material).hexdigest() == (
        "b3a00ead7295a455686aa157a847622ef99a6093e7c3f397ed112de59d1a5dd9"
    )
    assert frozen.SCAFFOLD_SHA256 == (
        "31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305"
    )
