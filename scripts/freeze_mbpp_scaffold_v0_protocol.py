#!/usr/bin/env python3
"""Build and freeze the MBPP+ development Generic Code Scaffold v0 protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
P0_PLAN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
    "mbpp_qwen35_9b_ab1_dev_run_003/generation_plan.json"
)
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
FROZEN_SPLIT_RELATIVE = Path("artifacts/public_benchmark_governance/frozen_split.csv")
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
SCAFFOLD_RELATIVE = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0.txt")
MANIFEST_RELATIVE = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0_manifest.json")
PLAN_RELATIVE = Path("configs/mbpp_scaffold_v0_development_plan.json")
GUIDE_RELATIVE = Path("docs/experiments/mbpp_scaffold_v0_operator_guide_zh.md")
STORAGE_MAPPING_RELATIVE = Path("configs/mbpp_scaffold_v0_storage_mapping.json")
INCIDENT_MANIFEST_RELATIVE = Path(
    "artifacts/pbd/mbpp_sv0/incidents/run_001_windows_path_incident.json"
)
PHYSICAL_RUN_RELATIVE = Path("artifacts/pbd/mbpp_sv0/r002")
INVALIDATED_RUN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_scaffold_v0/runs/"
    "mbpp_qwen35_9b_scaffold_v0_dev_run_001"
)

RUN_ID = "mbpp_qwen35_9b_scaffold_v0_dev_run_002"
INVALIDATED_RUN_ID = "mbpp_qwen35_9b_scaffold_v0_dev_run_001"
P0_RUN_ID = "mbpp_qwen35_9b_ab1_dev_run_003"
MODEL = "qwen3.5:9b"
MODEL_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
QUANTIZATION = "Q4_K_M"
SEEDS = [11, 22, 33, 44, 55]
GENERATION_TIMEOUT_SECONDS = 600.0
SCAFFOLD_VERSION = "mbpp_generic_code_scaffold_v0"
WINDOWS_PATH_BUDGET = 240
WINDOWS_REPO_PREFIX = r"C:\Users\yehya\Documents\GitHub\MathProject_AST_Research_Stage2"
INVALIDATED_PLAN_SHA256 = "a7ea12662695deb0719b1696d95bd9706b73f1ae01be3382a75ea454b9862a33"
INVALIDATED_PLAN_SIZE_BYTES = 42452
INVALIDATED_FIRST_GENERATION_ID = (
    "5537b5e986263ee6fe7e8bc2c3f6b2cee1ecfe79da7c574916bc4ef0b62ecbb0"
)

SCAFFOLD_TEXT = (
    "Return exactly one complete Python source file.\n"
    "Do not use Markdown code fences.\n"
    "Do not include explanations, analysis, assertions, tests, print statements, example calls, or alternative implementations.\n"
    "Implement the exact function name and parameter list required by the task.\n"
    "Include every import required by the submitted program.\n"
    "Do not rename or redefine the requested public function.\n"
    "The response must begin with Python code and contain no text outside the source file.\n"
)
SCAFFOLD_BYTES = SCAFFOLD_TEXT.encode("utf-8")
SCAFFOLD_SHA256 = hashlib.sha256(SCAFFOLD_BYTES).hexdigest()

PROMPT_SEPARATOR = "\n\n--- GENERIC CODE SCAFFOLD V0 ---\n\n"
PROMPT_SEPARATOR_BYTES = PROMPT_SEPARATOR.encode("utf-8")
PROMPT_SEPARATOR_SHA256 = hashlib.sha256(PROMPT_SEPARATOR_BYTES).hexdigest()

EVIDENCE_RELATIVES = (
    P0_PLAN_RELATIVE,
    PROTOCOL_RELATIVE,
    Path("scripts/run_mbpp_development_baseline.py"),
    Path(
        "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
        "mbpp_qwen35_9b_ab1_dev_run_003/milestone_1d_evidence_review/"
        "scaffold_evidence_ledger.csv"
    ),
    Path(
        "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
        "mbpp_qwen35_9b_ab1_dev_run_003/milestone_1d_evidence_review/"
        "evidence_manifest.json"
    ),
)


class ScaffoldProtocolError(RuntimeError):
    """Raised when a frozen protocol input or output differs."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ScaffoldProtocolError(message)


def compose_prompt(official_prompt: str) -> str:
    """Compose official bytes, frozen separator, then scaffold bytes."""
    return official_prompt + PROMPT_SEPARATOR + SCAFFOLD_TEXT


def load_selected_task_records(
    repo_root: Path, task_ids: list[str]
) -> list[dict[str, str]]:
    """Retain only model-visible records for the permitted P0 task IDs."""
    selected = set(task_ids)
    found: dict[str, dict[str, str]] = {}
    with (repo_root / TASKS_RELATIVE).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in selected:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"{task_id}: model-visible task schema drift",
            )
            found[task_id] = record
    _require(set(found) == selected, "P0 task IDs missing from model-visible tasks")
    return [found[task_id] for task_id in task_ids]


def _load_inputs(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    p0_plan_path = repo_root / P0_PLAN_RELATIVE
    protocol_path = repo_root / PROTOCOL_RELATIVE
    p0 = json.loads(p0_plan_path.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    _require(p0["run_id"] == P0_RUN_ID, "P0 run ID mismatch")
    _require(p0["dataset"] == "MBPP+", "P0 dataset mismatch")
    _require(p0["task_count"] == 20 and len(p0["task_ids"]) == 20, "P0 task count mismatch")
    _require(len(set(p0["task_ids"])) == 20, "P0 task IDs are not unique")
    _require(p0["seeds"] == SEEDS and p0["expected_cells"] == 100, "P0 seed/cell schedule mismatch")
    _require(p0["frozen_split_sha256"] == sha256_bytes((repo_root / FROZEN_SPLIT_RELATIVE).read_bytes()), "frozen split hash mismatch")
    _require(p0["protocol_sha256"] == sha256_bytes(protocol_path.read_bytes()), "generation protocol hash mismatch")
    primary = protocol["models"]["primary_development_model"]
    generation = protocol["generation"]
    _require(primary["tag"] == p0["model"] == MODEL, "model tag mismatch")
    _require(primary["digest"] == p0["model_digest"] == MODEL_DIGEST, "model digest mismatch")
    _require(primary["quantization"] == QUANTIZATION, "model quantization mismatch")
    _require(generation["thinking"] is False, "think must be false")
    _require(protocol["samples_per_task"] == 5 and protocol["seeds"] == SEEDS, "protocol schedule drift")
    _require(protocol["policies"]["automatic_retry"] is False, "automatic retry must remain disabled")
    _require(protocol["policies"]["overwrite_existing_output"] is False, "overwrite must remain disabled")
    tasks = load_selected_task_records(repo_root, p0["task_ids"])
    return p0, protocol, tasks


def generation_id(task_id: str, seed: int, prompt_sha256: str) -> str:
    material = (
        f"{RUN_ID}|{task_id}|{seed}|{MODEL_DIGEST}|{SCAFFOLD_SHA256}|"
        f"{prompt_sha256}"
    )
    return sha256_text(material)


def build_incident_manifest() -> dict[str, Any]:
    windows_root = PureWindowsPath(WINDOWS_REPO_PREFIX)
    run_root = windows_root / PureWindowsPath(INVALIDATED_RUN_RELATIVE.as_posix())
    journal_dir = run_root / "generation_journal"
    failed_final = journal_dir / f"{INVALIDATED_FIRST_GENERATION_ID}.json"
    observed_temp_example = journal_dir / ".tmp-xxxxxxxx.tmp"
    return {
        "incident_version": "mbpp_scaffold_v0_windows_path_incident_v1",
        "logical_run_id": INVALIDATED_RUN_ID,
        "status": "permanently_invalidated",
        "invalidated_reason": "WinError 3 during temp-to-final rename after Windows MAX_PATH overflow",
        "incident_error": "WinError 3 during temp-to-final rename",
        "model_request_may_have_succeeded": True,
        "recoverable_saved_response_count": 0,
        "reuse_policy": {
            "delete": False,
            "modify": False,
            "resume": False,
            "overwrite": False,
            "selective_retry": False,
            "reuse_response": False,
        },
        "valid_generation_cells": 0,
        "evalplus_executed": False,
        "observed_windows_repo_prefix": WINDOWS_REPO_PREFIX,
        "observed_paths": {
            "run_directory": str(run_root),
            "journal_directory": str(journal_dir),
            "journal_directory_length": len(str(journal_dir)),
            "failed_final_path_example": str(failed_final),
            "failed_final_path_length": len(str(failed_final)),
            "observed_temp_path_shape": str(observed_temp_example),
            "observed_temp_path_length": len(str(observed_temp_example)),
        },
        "existing_artifacts": [
            {
                "path": (INVALIDATED_RUN_RELATIVE / "generation_plan.json").as_posix(),
                "type": "file",
                "size_bytes": INVALIDATED_PLAN_SIZE_BYTES,
                "sha256": INVALIDATED_PLAN_SHA256,
            },
            {
                "path": (INVALIDATED_RUN_RELATIVE / "generation_journal").as_posix(),
                "type": "empty_directory",
                "file_count": 0,
                "tree_content_sha256": sha256_bytes(b""),
                "repository_preservation": "metadata_only_git_does_not_track_empty_directories",
            },
        ],
        "absent_artifacts": [
            (INVALIDATED_RUN_RELATIVE / "raw_generations.jsonl").as_posix(),
            (INVALIDATED_RUN_RELATIVE / "pipeline_corrected.jsonl").as_posix(),
            (INVALIDATED_RUN_RELATIVE / "evaluation_results.csv").as_posix(),
            (INVALIDATED_RUN_RELATIVE / "evaluation_summary.md").as_posix(),
            (INVALIDATED_RUN_RELATIVE / "failure_census_summary.md").as_posix(),
        ],
        "successor_logical_run_id": RUN_ID,
        "successor_must_generate_all_cells_fresh": 100,
    }


def verify_invalidated_incident_artifacts(repo_root: Path = REPO_ROOT) -> None:
    """Fail closed if any preserved run_001 incident artifact has drifted."""
    repo_root = repo_root.resolve()
    run_root = repo_root / INVALIDATED_RUN_RELATIVE
    plan_path = run_root / "generation_plan.json"
    journal_dir = run_root / "generation_journal"
    _require(plan_path.is_file(), "invalidated run_001 generation plan is missing")
    _require(
        plan_path.stat().st_size == INVALIDATED_PLAN_SIZE_BYTES,
        "invalidated run_001 generation plan size drift",
    )
    _require(
        sha256_bytes(plan_path.read_bytes()) == INVALIDATED_PLAN_SHA256,
        "invalidated run_001 generation plan hash drift",
    )
    if journal_dir.exists():
        _require(journal_dir.is_dir(), "invalidated run_001 journal path is not a directory")
        _require(not any(journal_dir.iterdir()), "invalidated run_001 journal is no longer empty")
    for relative_path in build_incident_manifest()["absent_artifacts"]:
        _require(
            not (repo_root / relative_path).exists(),
            f"invalidated run_001 absent artifact unexpectedly exists: {relative_path}",
        )


def build_storage_mapping() -> dict[str, Any]:
    incident = build_incident_manifest()
    return {
        "mapping_version": "mbpp_scaffold_v0_logical_physical_mapping_v1",
        "windows_path_budget_chars": WINDOWS_PATH_BUDGET,
        "logical_run_id": RUN_ID,
        "physical_storage_directory": PHYSICAL_RUN_RELATIVE.as_posix(),
        "journal_directory_name": "j",
        "journal_filename_policy": "full_64_character_generation_id_plus_.json",
        "research_identifiers_shortened": False,
        "requires_windows_long_path_registry_change": False,
        "invalidated_logical_run_id": INVALIDATED_RUN_ID,
        "invalidated_physical_storage_directory": INVALIDATED_RUN_RELATIVE.as_posix(),
        "incident_manifest_path": INCIDENT_MANIFEST_RELATIVE.as_posix(),
        "incident_manifest_sha256": sha256_bytes(render_json(incident)),
    }


def build_manifest(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    verify_invalidated_incident_artifacts(repo_root)
    p0, protocol, _ = _load_inputs(repo_root)
    evidence = {
        path.as_posix(): sha256_bytes((repo_root / path).read_bytes())
        for path in EVIDENCE_RELATIVES
    }
    incident = build_incident_manifest()
    mapping = build_storage_mapping()
    return {
        "version": SCAFFOLD_VERSION,
        "status": "frozen_development_candidate",
        "encoding": "UTF-8",
        "line_endings": "LF",
        "final_newline": True,
        "exact_text_utf8": SCAFFOLD_TEXT,
        "exact_bytes_hex": SCAFFOLD_BYTES.hex(),
        "size_bytes": len(SCAFFOLD_BYTES),
        "sha256": SCAFFOLD_SHA256,
        "path": SCAFFOLD_RELATIVE.as_posix(),
        "prompt_composition_order": [
            "official_task_prompt_verbatim",
            "fixed_separator",
            SCAFFOLD_VERSION,
        ],
        "separator": {
            "exact_text_utf8": PROMPT_SEPARATOR,
            "exact_bytes_hex": PROMPT_SEPARATOR_BYTES.hex(),
            "size_bytes": len(PROMPT_SEPARATOR_BYTES),
            "sha256": PROMPT_SEPARATOR_SHA256,
        },
        "construction_evidence_sha256": evidence,
        "p0_run_id": p0["run_id"],
        "protocol_sha256": p0["protocol_sha256"],
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "quantization": QUANTIZATION,
        "contains_task_answers": False,
        "contains_test_answers": False,
        "contains_dataset_specific_solution_guidance": False,
        "scope_statement": (
            "Task-agnostic code-output constraints only; contains no task answer, "
            "test answer, canonical solution, or dataset-specific solution hint."
        ),
        "generation_parameters": protocol["generation"],
        "ollama_request_timeout_seconds": GENERATION_TIMEOUT_SECONDS,
        "ollama_request_timeout_source": (
            "P0 run_003 actual generation command (--timeout-seconds 600)"
        ),
        "logical_run_id": RUN_ID,
        "invalidated_predecessor_run_id": INVALIDATED_RUN_ID,
        "storage_mapping_path": STORAGE_MAPPING_RELATIVE.as_posix(),
        "storage_mapping_sha256": sha256_bytes(render_json(mapping)),
        "incident_manifest_path": INCIDENT_MANIFEST_RELATIVE.as_posix(),
        "incident_manifest_sha256": sha256_bytes(render_json(incident)),
    }


def build_plan(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    verify_invalidated_incident_artifacts(repo_root)
    p0, protocol, tasks = _load_inputs(repo_root)
    cells: list[dict[str, Any]] = []
    cell_index = 0
    for task in tasks:
        official_hash = sha256_text(task["prompt"])
        composed_hash = sha256_text(compose_prompt(task["prompt"]))
        for sample_index, seed in enumerate(SEEDS):
            cell_index += 1
            cells.append(
                {
                    "cell_index": cell_index,
                    "task_id": task["task_id"],
                    "seed": seed,
                    "sample_index": sample_index,
                    "official_prompt_sha256": official_hash,
                    "composed_prompt_sha256": composed_hash,
                    "generation_id": generation_id(task["task_id"], seed, composed_hash),
                }
            )
    _require(len(cells) == 100, "P1 plan must contain exactly 100 cells")
    mapping = build_storage_mapping()
    return {
        "plan_version": "mbpp_scaffold_v0_development_plan_v2_windows_path_recovery",
        "run_id": RUN_ID,
        "logical_run_id": RUN_ID,
        "invalidated_predecessor_run_id": INVALIDATED_RUN_ID,
        "physical_storage_directory": PHYSICAL_RUN_RELATIVE.as_posix(),
        "journal_directory_name": "j",
        "storage_mapping_path": STORAGE_MAPPING_RELATIVE.as_posix(),
        "storage_mapping_sha256": sha256_bytes(render_json(mapping)),
        "windows_path_budget_chars": WINDOWS_PATH_BUDGET,
        "p0_run_id": P0_RUN_ID,
        "dataset": "MBPP+",
        "dataset_version": p0["dataset_version"],
        "dataset_hash": p0["dataset_hash"],
        "frozen_split_sha256": p0["frozen_split_sha256"],
        "selection_policy": "P0 frozen MBPP+ active development task IDs only",
        "task_count": 20,
        "task_ids": p0["task_ids"],
        "samples_per_task": 5,
        "seeds": SEEDS,
        "expected_cells": 100,
        "cell_order": "P0 task order, then seeds [11,22,33,44,55]",
        "cells": cells,
        "treatment": "P1_Generic_Code_Scaffold_v0",
        "prompt_policy": "official_prompt_verbatim + fixed_separator + frozen_scaffold_v0",
        "scaffold_version": SCAFFOLD_VERSION,
        "scaffold_path": SCAFFOLD_RELATIVE.as_posix(),
        "scaffold_sha256": SCAFFOLD_SHA256,
        "separator_sha256": PROMPT_SEPARATOR_SHA256,
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "quantization": QUANTIZATION,
        "protocol_sha256": p0["protocol_sha256"],
        "generation_parameters": protocol["generation"],
        "ollama_request_timeout_seconds": GENERATION_TIMEOUT_SECONDS,
        "ollama_request_timeout_source": (
            "P0 run_003 actual generation command (--timeout-seconds 600)"
        ),
        "evaluation_engine": "evalplus_0.3.1_check_correctness_subset",
        "evaluation_timeout_policy": "same EvalPlus subset evaluator defaults as P0 run_003",
        "retry": False,
        "selective_retry": False,
        "resume": False,
        "overwrite": False,
        "scaffold": True,
        "healer": False,
        "post_healer_account": False,
        "pipeline_correction_spec": p0["pipeline_correction_spec"],
        "pipeline_correction_spec_commit": p0["pipeline_correction_spec_commit"],
        "accounts": ["observed", "pipeline_corrected"],
        "pipeline_correction_is_healer": False,
        "evaluator_feedback_to_model": False,
    }


def render_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def render_guide() -> bytes:
    text = f"""# MBPP+ Generic Code Scaffold v0 操作說明

## 凍結範圍

- P0：`{P0_RUN_ID}`
- P1：`{RUN_ID}`
- Permanently invalidated incident：`{INVALIDATED_RUN_ID}`（有效 generation=0，不得 delete/modify/resume/overwrite/selective retry）
- Physical storage：`{PHYSICAL_RUN_RELATIVE.as_posix()}`；journal directory：`j`
- Windows path budget：≤ {WINDOWS_PATH_BUDGET} characters；不依賴 registry long-path 設定。
- Cells：20 tasks × 5 seeds = 100
- Model：`{MODEL}` / `{MODEL_DIGEST}` / `{QUANTIZATION}`
- Scaffold SHA-256：`{SCAFFOLD_SHA256}`
- `think=false`；sampling parameters 與 P0 frozen protocol 完全相同。
- Retry、selective retry、resume、overwrite 與 Healer 全部禁止。
- Observed 與 Pipeline-corrected 是分離評估帳；Pipeline correction 不是 Healer。

本 Milestone 只凍結協定。以下命令本輪未執行，之後僅由使用者按順序手動執行。

## 唯一 generation command（Windows PowerShell）

```powershell
py -3.12 -B .\\scripts\\run_mbpp_scaffold_v0_development.py generate --run-id {RUN_ID} --base-url http://127.0.0.1:11434 --timeout-seconds 600
```

## WSL evaluation 正式環境

```powershell
wsl -d Ubuntu
```

進入後：

```bash
cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2

/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_scaffold_v0_development.py evaluate \\
  --run-id {RUN_ID} \\
  --parallel 4
```

Generation 成功且完整產生 100/100 cells 前，不得執行 evaluation。任何中斷或不完整 run 均不得 retry、resume、selective retry 或 overwrite；應停止並保留 journal 供稽核。
"""
    return text.encode("utf-8")


def frozen_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    incident = build_incident_manifest()
    mapping = build_storage_mapping()
    return {
        SCAFFOLD_RELATIVE: SCAFFOLD_BYTES,
        MANIFEST_RELATIVE: render_json(build_manifest(repo_root)),
        PLAN_RELATIVE: render_json(build_plan(repo_root)),
        STORAGE_MAPPING_RELATIVE: render_json(mapping),
        INCIDENT_MANIFEST_RELATIVE: render_json(incident),
        GUIDE_RELATIVE: render_guide(),
    }


def write_frozen_outputs(repo_root: Path = REPO_ROOT) -> None:
    repo_root = repo_root.resolve()
    for relative_path, content in frozen_outputs(repo_root).items():
        path = repo_root / relative_path
        if path.exists():
            _require(path.read_bytes() == content, f"refusing to alter frozen output: {relative_path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    write_frozen_outputs(args.repo_root)
    print(
        json.dumps(
            {
                "status": "frozen",
                "run_id": RUN_ID,
                "cells": 100,
                "scaffold_sha256": SCAFFOLD_SHA256,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
