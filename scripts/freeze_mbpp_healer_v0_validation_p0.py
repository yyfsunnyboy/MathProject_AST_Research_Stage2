#!/usr/bin/env python3
"""Freeze the identity-only MBPP+ validation P0 x Healer-v0 execution plan.

This is an offline, zero-model materializer.  It mechanically reads only the
model-visible prompt records needed to hash the frozen validation prompts; it
never prints task identities or prompt content and never imports EvalPlus.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_v0_validation_p0_v1"
)
FROZEN_SPLIT_RELATIVE = Path("artifacts/public_benchmark_governance/frozen_split.csv")
CONTAMINATION_RELATIVE = Path(
    "artifacts/public_benchmark_governance/contamination_manifest.csv"
)
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
DATASET_MANIFEST_RELATIVE = Path("data/mbpp_plus/dataset_manifest.json")
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
HEALER_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
PIPELINE_RELATIVE = Path("agent_tools/finals_rebuild/extraction.py")
DEVELOPMENT_CELLS_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
    "paired_analysis_run_001/paired_cell_results.csv"
)
DEVELOPMENT_MANIFEST_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
    "paired_analysis_run_001/paired_analysis_manifest.json"
)

RUN_ID = "mbpp_q35_9b_healer_v0_validation_p0_r001"
RUN_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_validation/mbpp_healer_v0_p0/"
    f"runs/{RUN_ID}"
)
EXPECTED_START_COMMIT = "733aa2b4cf8ea98f689a7412ecbf6f4ec063707c"
EXPECTED_HEALER_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_PIPELINE_SHA256 = "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
EXPECTED_RULE_ID = "entrypoint_alias_unique_arity_compatible_v0"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EXPECTED_MODEL = "qwen3.5:9b"
EXPECTED_MODEL_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
EXPECTED_QUANTIZATION = "Q4_K_M"
EXPECTED_SEEDS = (11, 22, 33, 44, 55)
EXPECTED_TASKS = 20
EXPECTED_GENERATIONS = 100
EXPECTED_ACCOUNTS = 200
EXPECTED_GENERATION_OPTIONS = {
    "num_ctx": 8192,
    "num_predict": 2048,
    "stream": False,
    "temperature": 0.2,
    "thinking": False,
    "top_k": 20,
    "top_p": 0.95,
}

CELL_FIELDS = (
    "cell_index", "task_rank", "task_id", "seed", "sample_index",
    "generation_id", "program_id", "prompt_sha256", "prompt_contract_sha256",
    "run_id", "model", "model_digest", "quantization", "thinking",
    "num_ctx", "num_predict", "temperature", "top_k", "top_p",
)
ACCOUNT_FIELDS = (
    "account_index", "cell_index", "program_id", "evaluation_account_id",
    "healer_account", "task_id", "seed", "generation_id", "run_id",
    "pipeline_sha256", "healer_sha256", "healer_rule_id",
    "same_raw_generation_h0_h1", "same_pipeline_normalized_input_h0_h1",
    "h1_requires_regeneration", "evaluation_status",
)

_BUILTIN_CALLS = {
    "abs", "all", "any", "isinstance", "len", "list", "max", "min",
    "round", "set", "sorted", "sum", "tuple",
}


class ValidationFreezeError(RuntimeError):
    """Raised before writes when validation governance or identity drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFreezeError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _identity_hash(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def prompt_contract(prompt: str) -> tuple[str, tuple[int, ...]]:
    calls: list[ast.Call] = []
    for line in prompt.splitlines():
        if not line.strip().startswith("assert "):
            continue
        try:
            tree = ast.parse(line.strip())
        except SyntaxError:
            continue
        calls.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id not in _BUILTIN_CALLS
        )
    names = {call.func.id for call in calls}
    _require(len(names) == 1, "validation prompt contract must expose one entry point")
    expected = next(iter(names))
    arities = tuple(
        sorted(
            {
                len(call.args)
                for call in calls
                if call.func.id == expected and not call.keywords
            }
        )
    )
    _require(bool(arities), "validation prompt positional arity evidence missing")
    return expected, arities


def load_validation_rows(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    rows = _read_csv(repo_root / FROZEN_SPLIT_RELATIVE)
    _require(len(rows) == len({row["task_id"] for row in rows}), "frozen split duplicate task identity")
    validation = [
        row
        for row in rows
        if row["dataset"] == "MBPP+" and row["proposed_role"] == "validation"
    ]
    validation.sort(key=lambda row: int(row["selection_rank_within_pool"]))
    _require(len(validation) == EXPECTED_TASKS, "frozen split must contain exactly 20 MBPP+ validation tasks")
    _require(len({row["task_id"] for row in validation}) == EXPECTED_TASKS, "duplicate validation task identity")
    for row in validation:
        _require(row["split_assignment_status"] == "frozen", "validation split is not frozen")
        _require(row["active_development_generation_subset"] == "false", "validation task entered active development")
        _require(row["confirmatory_eligible"] == "false", "validation task mislabeled confirmatory")
        _require(row["project_contamination_status"] == "not_applicable_non_confirmatory", "validation project exposure status drift")
    return validation


def validate_isolation(
    validation: list[dict[str, str]], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    validation_ids = {row["task_id"] for row in validation}
    contamination_rows = _read_csv(repo_root / CONTAMINATION_RELATIVE)
    contamination = {row["task_id"]: row for row in contamination_rows}
    _require(len(contamination) == len(contamination_rows), "contamination manifest duplicate identity")
    for task_id in validation_ids:
        _require(task_id in contamination, "validation identity missing contamination row")
        row = contamination[task_id]
        _require(row["contamination_status"] == "unreviewed_candidate", "validation task has contamination status")
        _require(row["individually_reviewed"] == "false", "validation task was individually reviewed")
        _require(row["failure_census_source"] == "false", "validation task entered failure census")
        _require(row["rule_development_source"] == "false", "validation task entered rule development")
        evidence_paths = {
            value for value in row["evidence_paths"].split(";") if value
        }
        _require(
            evidence_paths
            == {DATASET_MANIFEST_RELATIVE.as_posix(), TASKS_RELATIVE.as_posix()},
            "validation task has non-dataset construction evidence path",
        )
        _require(not row["contamination_sources"].strip(), "validation task has contamination source")

    development_rows = _read_csv(repo_root / DEVELOPMENT_CELLS_RELATIVE)
    development_ids = {row["task_id"] for row in development_rows}
    _require(len(development_ids) == 60, "development task identity count drift")
    _require(not validation_ids.intersection(development_ids), "validation overlaps 60-task development evidence")

    split_rows = _read_csv(repo_root / FROZEN_SPLIT_RELATIVE)
    other_roles = {
        row["task_id"]
        for row in split_rows
        if row["proposed_role"] != "validation"
    }
    _require(not validation_ids.intersection(other_roles), "validation identity assigned another frozen role")
    return {
        "validation_tasks": len(validation_ids),
        "development_tasks_checked": len(development_ids),
        "validation_development_intersection": 0,
        "individually_reviewed": 0,
        "failure_census_sources": 0,
        "rule_development_sources": 0,
        "manual_replacement_or_resampling": False,
    }


def load_validation_tasks(
    validation_rows: list[dict[str, str]], repo_root: Path = REPO_ROOT
) -> list[dict[str, Any]]:
    ordered_ids = [row["task_id"] for row in validation_rows]
    selected = set(ordered_ids)
    found: dict[str, dict[str, Any]] = {}
    with (repo_root / TASKS_RELATIVE).open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in selected:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"model-visible task schema drift at line {line_no}",
            )
            _require(task_id not in found, "duplicate model-visible validation task")
            expected, arities = prompt_contract(record["prompt"])
            _require(expected == record["entry_point"], "prompt/task entry-point contract drift")
            found[task_id] = {
                **record,
                "expected_positional_arities": arities,
                "prompt_sha256": _sha256_text(record["prompt"]),
                "prompt_contract_sha256": _identity_hash(
                    {"entry_point": expected, "positional_arities": arities}
                ),
            }
    _require(set(found) == selected, "validation task missing from model-visible tasks file")
    return [found[task_id] for task_id in ordered_ids]


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_paths = (
        FROZEN_SPLIT_RELATIVE,
        CONTAMINATION_RELATIVE,
        TASKS_RELATIVE,
        DATASET_MANIFEST_RELATIVE,
        PROTOCOL_RELATIVE,
        HEALER_RELATIVE,
        PIPELINE_RELATIVE,
        DEVELOPMENT_CELLS_RELATIVE,
        DEVELOPMENT_MANIFEST_RELATIVE,
    )
    source_hashes = {
        path.as_posix(): _sha256_bytes((repo_root / path).read_bytes())
        for path in source_paths
    }
    _require(source_hashes[HEALER_RELATIVE.as_posix()] == EXPECTED_HEALER_SHA256, "Healer hash drift")
    _require(source_hashes[PIPELINE_RELATIVE.as_posix()] == EXPECTED_PIPELINE_SHA256, "Pipeline hash drift")

    dataset_manifest = json.loads(
        (repo_root / DATASET_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    _require(dataset_manifest["release_tag_or_dataset_version"] == EXPECTED_DATASET_VERSION, "dataset version drift")
    _require(dataset_manifest["evalplus_dataset_hash"] == EXPECTED_DATASET_HASH, "dataset hash drift")
    _require(dataset_manifest["tasks_sha256"] == source_hashes[TASKS_RELATIVE.as_posix()], "tasks file hash drift")
    _require(dataset_manifest["official_tests_and_canonical_solutions_included"] is False, "model-visible tasks file contains protected evaluator data")

    protocol = json.loads((repo_root / PROTOCOL_RELATIVE).read_text(encoding="utf-8"))
    primary = protocol["models"]["primary_development_model"]
    _require(primary["tag"] == EXPECTED_MODEL, "model tag drift")
    _require(primary["digest"] == EXPECTED_MODEL_DIGEST, "model digest drift")
    _require(primary["quantization"] == EXPECTED_QUANTIZATION, "model quantization drift")
    generation = protocol["generation"]
    _require(generation == EXPECTED_GENERATION_OPTIONS, "generation parameter drift")
    _require(tuple(protocol["seeds"]) == EXPECTED_SEEDS, "seed drift")
    _require(protocol["samples_per_task"] == 5, "samples-per-task drift")
    for key in ("automatic_retry", "overwrite_existing_output"):
        _require(protocol["policies"][key] is False, f"generation policy drift: {key}")

    validation_rows = load_validation_rows(repo_root)
    isolation = validate_isolation(validation_rows, repo_root)
    tasks = load_validation_tasks(validation_rows, repo_root)
    protocol_sha = source_hashes[PROTOCOL_RELATIVE.as_posix()]
    cells: list[dict[str, Any]] = []
    accounts: list[dict[str, Any]] = []
    for task_rank, task in enumerate(tasks, start=1):
        for sample_index, seed in enumerate(EXPECTED_SEEDS):
            generation_id = _identity_hash({
                "run_id": RUN_ID,
                "task_id": task["task_id"],
                "seed": seed,
                "model_digest": EXPECTED_MODEL_DIGEST,
                "prompt_sha256": task["prompt_sha256"],
                "protocol_sha256": protocol_sha,
            })
            program_id = _identity_hash({"generation_id": generation_id, "prompt_arm": "P0"})
            cell_index = len(cells) + 1
            cells.append({
                "cell_index": cell_index,
                "task_rank": task_rank,
                "task_id": task["task_id"],
                "seed": seed,
                "sample_index": sample_index,
                "generation_id": generation_id,
                "program_id": program_id,
                "prompt_sha256": task["prompt_sha256"],
                "prompt_contract_sha256": task["prompt_contract_sha256"],
                "run_id": RUN_ID,
                "model": EXPECTED_MODEL,
                "model_digest": EXPECTED_MODEL_DIGEST,
                "quantization": EXPECTED_QUANTIZATION,
                "thinking": "false",
                "num_ctx": generation["num_ctx"],
                "num_predict": generation["num_predict"],
                "temperature": generation["temperature"],
                "top_k": generation["top_k"],
                "top_p": generation["top_p"],
            })
            for arm in ("H0", "H1"):
                accounts.append({
                    "account_index": len(accounts) + 1,
                    "cell_index": cell_index,
                    "program_id": program_id,
                    "evaluation_account_id": _identity_hash(
                        {"program_id": program_id, "healer_account": arm}
                    ),
                    "healer_account": arm,
                    "task_id": task["task_id"],
                    "seed": seed,
                    "generation_id": generation_id,
                    "run_id": RUN_ID,
                    "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
                    "healer_sha256": EXPECTED_HEALER_SHA256 if arm == "H1" else "not_applied_control",
                    "healer_rule_id": EXPECTED_RULE_ID if arm == "H1" else "not_applied_control",
                    "same_raw_generation_h0_h1": "true",
                    "same_pipeline_normalized_input_h0_h1": "true",
                    "h1_requires_regeneration": "false",
                    "evaluation_status": "not_executed",
                })

    _require(len(cells) == EXPECTED_GENERATIONS, "generation cell count must be 100")
    _require(len({cell["generation_id"] for cell in cells}) == EXPECTED_GENERATIONS, "duplicate generation identity")
    _require(len({(cell["task_id"], cell["seed"]) for cell in cells}) == EXPECTED_GENERATIONS, "task-seed completeness drift")
    _require(len(accounts) == EXPECTED_ACCOUNTS, "evaluation account count must be 200")
    _require(len({row["evaluation_account_id"] for row in accounts}) == EXPECTED_ACCOUNTS, "duplicate evaluation account")
    return {
        "cells": cells,
        "accounts": accounts,
        "isolation": isolation,
        "source_hashes": source_hashes,
    }


def _execution_spec() -> dict[str, Any]:
    return {
        "spec_version": "mbpp_healer_v0_validation_p0_execution_v1",
        "status": "prepared_not_executed",
        "run_id": RUN_ID,
        "run_output_relative": RUN_OUTPUT_RELATIVE.as_posix(),
        "sequence": [
            "zero-model immutable manifest and source-hash preflight",
            "verify installed model provenance without creating run directory",
            "exactly one generation attempt per frozen cell with durable per-cell journal",
            "require all 100 raw generations complete",
            "publish combined raw JSONL",
            "apply frozen Pipeline to all 100 raw generations",
            "fork every normalized program to H0 unchanged and H1 frozen Healer without regeneration",
            "publish 200 evaluation accounts pending a later separately authorized EvalPlus milestone",
        ],
        "persistence": {
            "per_cell_journal": True,
            "flush_and_fsync": True,
            "same_directory_temp_file": True,
            "atomic_rename": True,
            "read_back_and_sha256_verify": True,
        },
        "forbidden": {
            "resume": True,
            "retry": True,
            "selective_rerun": True,
            "overwrite": True,
            "evalplus_in_this_runner": True,
            "h1_regeneration": True,
            "scaffold": True,
        },
        "decision_rules_frozen_before_results": {
            "regression_eq_0_and_verified_rescue_gte_1": "prospective_qualification_passed",
            "regression_eq_0_and_verified_rescue_eq_0": "safe_but_functional_benefit_not_reproduced",
            "regression_gt_0": "safety_qualification_not_passed",
            "task_level_rescue_distribution_modification_rate_mcnemar": "secondary_descriptive_only",
        },
    }


def _guide(manifest_sha256: str) -> bytes:
    command = (
        "C:\\Users\\yehya\\Documents\\GitHub\\MathProject_AST_Research_Stage2\\.venv\\Scripts\\python.exe "
        "scripts\\run_mbpp_healer_v0_validation_p0.py generate "
        "--manifest artifacts\\public_benchmark_governance\\healer_v0_validation_p0_v1\\manifest.json "
        f"--manifest-sha256 {manifest_sha256}"
    )
    text = f"""# MBPP+ Healer v0 validation P0 prospective qualification操作指南

本規格固定從既有frozen split機械載入20題validation，只使用P0官方prompt、qwen3.5:9b既有正式model digest與seeds 11/22/33/44/55。共100個raw generation cells與200個H0/H1 evaluation accounts。沒有Scaffold，H1不重新生成。

本準備輪已完成zero-model preflight，沒有呼叫Ollama或EvalPlus。人工執行前必須確認固定run output path不存在；runner拒絕resume、retry、selective rerun與overwrite。任何一格失敗時只保留已durably persisted的journals，禁止自行補跑。

## 唯一人工執行指令

在repository根目錄的Windows PowerShell執行：

```powershell
{command}
```

此指令只完成100次generation與evaluator-blind H0/H1 materialization；不執行EvalPlus。後續評估必須另由新Milestone授權。
"""
    return text.encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo_root)
    outputs: dict[str, bytes] = {
        "generation_cells.csv": _csv_bytes(analysis["cells"], CELL_FIELDS),
        "evaluation_accounts.csv": _csv_bytes(analysis["accounts"], ACCOUNT_FIELDS),
        "execution_spec.json": _json_bytes(_execution_spec()),
        "zero_model_preflight.json": _json_bytes({
            "status": "passed_without_model_or_evalplus",
            **analysis["isolation"],
            "generation_cells": 100,
            "evaluation_accounts": 200,
            "model_calls": 0,
            "evalplus_executions": 0,
            "validation_content_displayed_or_manually_reviewed": False,
        }),
    }
    manifest = {
        "manifest_version": "mbpp_healer_v0_validation_p0_v1",
        "status": "prepared_not_executed",
        "development_paired_analysis_commit": EXPECTED_START_COMMIT,
        "development_result": {"programs": 600, "changed": 41, "verified_rescue": 9, "regression": 0},
        "run_id": RUN_ID,
        "run_output_relative": RUN_OUTPUT_RELATIVE.as_posix(),
        "dataset": "MBPP+",
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "validation_task_count": 20,
        "seeds": list(EXPECTED_SEEDS),
        "generation_cells": 100,
        "evaluation_accounts": 200,
        "prompt_arm": "P0_official_task_prompt_verbatim",
        "model": EXPECTED_MODEL,
        "model_digest": EXPECTED_MODEL_DIGEST,
        "quantization": EXPECTED_QUANTIZATION,
        "generation_parameters": EXPECTED_GENERATION_OPTIONS,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "healer_sha256": EXPECTED_HEALER_SHA256,
        "healer_rule_order": [EXPECTED_RULE_ID],
        "scaffold": False,
        "h1_regeneration": False,
        "model_calls_during_freeze": 0,
        "evalplus_executions_during_freeze": 0,
        "identity_isolation": analysis["isolation"],
        "task_identity_order": [cell["task_id"] for cell in analysis["cells"][::5]],
        "prompt_sha256_by_task_identity": {
            cell["task_id"]: cell["prompt_sha256"] for cell in analysis["cells"][::5]
        },
        "source_sha256": analysis["source_hashes"],
        "output_sha256_excluding_manifest_and_operator_guide": {
            name: _sha256_bytes(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["manifest.json"] = _json_bytes(manifest)
    outputs["operator_guide_zh.md"] = _guide(_sha256_bytes(outputs["manifest.json"]))
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "validation freeze output directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "validation freeze file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "validation freeze output exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except (ValidationFreezeError, KeyError, ValueError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
