#!/usr/bin/env python3
"""Freeze Validation20 Scaffold × Healer v3 plans and per-model manifests.

This script only materializes deterministic governance artifacts. It never
calls a model, never executes candidate programs, and never runs EvalPlus.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PLAN_ID = "mbpp_validation20_scaffold_healer_v3"
ARTIFACT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/validation20_scaffold_healer_v3"
)
FROZEN_SPLIT_RELATIVE = Path("artifacts/public_benchmark_governance/frozen_split.csv")
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
AB2G_RELATIVE = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0.txt")
EXTRACTION_RELATIVE = Path("agent_tools/finals_rebuild/extraction.py")
PIPELINE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h1_h2_cumulative_pipeline.py"
)
H1_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
H2_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py")
H3_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_h3_empty_suite_pass_insertion.py")
H4_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py"
)

H4_ARCHIVE_COMMIT = "8954a257826582197ad7c0a10fe0c4b0c59fd4f9"
H4_RULE_SHA256 = "1aabe131b7312c9bc1e0b34b20540bef6f7d3ec858c2c2994cf84bc84f85a513"

DATASET_NAME = "MBPP+"
DATASET_VERSION = "v0.2.0"
DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EVALPLUS_VERSION = "0.3.1"
EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"

VALIDATION_TASK_IDS: tuple[str, ...] = (
    "Mbpp/4",
    "Mbpp/86",
    "Mbpp/130",
    "Mbpp/132",
    "Mbpp/247",
    "Mbpp/264",
    "Mbpp/265",
    "Mbpp/281",
    "Mbpp/405",
    "Mbpp/418",
    "Mbpp/425",
    "Mbpp/456",
    "Mbpp/459",
    "Mbpp/564",
    "Mbpp/569",
    "Mbpp/580",
    "Mbpp/586",
    "Mbpp/611",
    "Mbpp/755",
    "Mbpp/775",
)
SEEDS: tuple[int, ...] = (11, 22, 33, 44, 55)

PROMPT_SEPARATOR = "\n\n--- VALIDATION20_PROMPT_CONDITION ---\n\n"
AB2A_TEXT = (
    "Before writing the final code, internally:\n"
    "1. identify an algorithm that handles all valid inputs;\n"
    "2. check important edge cases and index boundaries;\n"
    "3. verify the return value and type;\n"
    "4. mentally test one normal case and one edge case;\n"
    "5. verify that every loop and recursive call has a guaranteed termination condition."
)

GENERATION_OPTIONS: dict[str, Any] = {
    "num_ctx": 8192,
    "num_predict": 2048,
    "stream": False,
    "temperature": 0.2,
    "thinking": False,
    "top_k": 20,
    "top_p": 0.95,
}

# Machine-verified on this build host against local Ollama /api/tags (2026-07-25).
MODEL_SPECS: dict[str, dict[str, Any]] = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "tag": "qwen3.5:4b",
        "operator_role": "local_team",
        "candidates_per_model": 400,
        "eval_cells_per_model": 1200,
        "identity_status": "machine_verified_on_build_host",
        "identity_source": "local_ollama_/api/tags_2026-07-25",
        "digest": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
        "parameter_size": "4.7B",
        "quantization_level": "Q4_K_M",
        "family": "qwen35",
        "format": "gguf",
        "size_bytes": 3389983735,
        "modified_at": "2026-07-16T22:38:31.4275049+08:00",
        "template_sha256": "b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315",
        "run_id": "mbpp_validation20_qwen35_4b_r001",
        "run_output_relative": Path(
            "artifacts/public_benchmark_development/mbpp_validation20/"
            "qwen35_4b/runs/mbpp_validation20_qwen35_4b_r001"
        ),
        "evalplus_output_relative": ARTIFACT_RELATIVE
        / "evalplus_runs"
        / "qwen35_4b"
        / "manual_evalplus_run_001",
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "tag": "qwen3.5:9b",
        "operator_role": "local_team",
        "candidates_per_model": 400,
        "eval_cells_per_model": 1200,
        "identity_status": "machine_verified_on_build_host",
        "identity_source": "local_ollama_/api/tags_2026-07-25",
        "digest": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
        "parameter_size": "9.7B",
        "quantization_level": "Q4_K_M",
        "family": "qwen35",
        "format": "gguf",
        "size_bytes": 6594474711,
        "modified_at": "2026-07-16T22:38:34.436418+08:00",
        "template_sha256": "b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315",
        "run_id": "mbpp_validation20_qwen35_9b_r001",
        "run_output_relative": Path(
            "artifacts/public_benchmark_development/mbpp_validation20/"
            "qwen35_9b/runs/mbpp_validation20_qwen35_9b_r001"
        ),
        "evalplus_output_relative": ARTIFACT_RELATIVE
        / "evalplus_runs"
        / "qwen35_9b"
        / "manual_evalplus_run_001",
    },
    "qwen3:0.6b": {
        "model_key": "qwen3_0_6b",
        "tag": "qwen3:0.6b",
        "operator_role": "classmate",
        "candidates_per_model": 400,
        "eval_cells_per_model": 1200,
        # Must be filled on the classmate machine before formal generation.
        "identity_status": "pending_machine_verification",
        "identity_source": None,
        "digest": None,
        "parameter_size": None,
        "quantization_level": None,
        "family": None,
        "format": None,
        "size_bytes": None,
        "modified_at": None,
        "template_sha256": None,
        "run_id": "mbpp_validation20_qwen3_0_6b_r001",
        "run_output_relative": Path(
            "artifacts/public_benchmark_development/mbpp_validation20/"
            "qwen3_0_6b/runs/mbpp_validation20_qwen3_0_6b_r001"
        ),
        "evalplus_output_relative": ARTIFACT_RELATIVE
        / "evalplus_runs"
        / "qwen3_0_6b"
        / "manual_evalplus_run_001",
    },
}

ALLOWED_MODEL_TAGS: tuple[str, ...] = tuple(MODEL_SPECS.keys())

PROMPT_CONDITIONS: tuple[dict[str, Any], ...] = (
    {
        "prompt_condition": "Ab1",
        "generic_scaffold": False,
        "algorithmic_scaffold": False,
        "scaffold_compose": "bare",
    },
    {
        "prompt_condition": "Ab2g",
        "generic_scaffold": True,
        "algorithmic_scaffold": False,
        "scaffold_compose": "ab2g_only",
    },
    {
        "prompt_condition": "Ab2A",
        "generic_scaffold": False,
        "algorithmic_scaffold": True,
        "scaffold_compose": "ab2a_only",
    },
    {
        "prompt_condition": "Ab2gA-factorial-v1",
        "generic_scaffold": True,
        "algorithmic_scaffold": True,
        "scaffold_compose": "ab2g_then_ab2a",
    },
)

CELL_FIELDS = (
    "cell_identity",
    "generation_id",
    "task_id",
    "seed",
    "prompt_condition",
    "model_tag",
    "model_key",
    "operator_role",
    "sample_index",
    "composed_prompt_sha256",
    "expected_entry_point",
    "expected_positional_arities",
    "validation_only",
    "forbid_development_substitute",
)

STAGES: tuple[str, ...] = ("raw", "pipeline_corrected", "post_h1_h2_h3_h4")

DERIVED_SUMMARY_PRIORITY: tuple[str, ...] = (
    "invalid_or_missing_candidate",
    "evaluator_infrastructure_failure",
    "verified_rescue",
    "execution_regression",
    "transformed_known_pass_preserved",
    "partial_repair",
    "unchanged_pass",
    "unchanged_failure",
)

FORBIDDEN_OUTPUT_COLLISION_RELATIVES: tuple[str, ...] = (
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1",
    "artifacts/public_benchmark_governance/h2_module_assert_quarantine_functional_evaluation_v1",
    "artifacts/public_benchmark_governance/h4_top_level_demo_print_quarantine_development_replay_v1",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1",
    "artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1",
    "artifacts/public_benchmark_development/mbpp_qwen35_4b_failure_supply_pilot",
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60",
)


class FreezeError(RuntimeError):
    """Fail-closed freeze violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in fields})
    return buffer.getvalue().encode("utf-8")


def _identity_hash(payload: dict[str, Any]) -> str:
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def source_hashes(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    relatives = (
        FROZEN_SPLIT_RELATIVE,
        TASKS_RELATIVE,
        PROTOCOL_RELATIVE,
        AB2G_RELATIVE,
        EXTRACTION_RELATIVE,
        PIPELINE_RELATIVE,
        H1_RELATIVE,
        H2_RELATIVE,
        H3_RELATIVE,
        H4_RELATIVE,
    )
    out: dict[str, str] = {}
    for relative in relatives:
        path = repo_root / relative
        _require(path.is_file(), f"missing source: {relative.as_posix()}")
        out[relative.as_posix()] = _sha256_bytes(path.read_bytes())
    _require(out[H4_RELATIVE.as_posix()] == H4_RULE_SHA256, "H4 rule SHA drift vs 8954a257 archive")
    return out


def load_validation_tasks(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    split_rows = _read_csv(repo_root / FROZEN_SPLIT_RELATIVE)
    validation = [
        row["task_id"]
        for row in split_rows
        if row["proposed_role"] == "validation" and row["dataset"] == "MBPP+"
    ]
    _require(sorted(validation) == sorted(VALIDATION_TASK_IDS), "Validation20 task set drift vs frozen_split")
    tasks = {
        row["task_id"]: row
        for row in _read_jsonl(repo_root / TASKS_RELATIVE)
        if row["task_id"] in VALIDATION_TASK_IDS
    }
    missing = [task_id for task_id in VALIDATION_TASK_IDS if task_id not in tasks]
    _require(not missing, f"missing Validation20 prompts: {missing}")
    ordered: list[dict[str, str]] = []
    for task_id in VALIDATION_TASK_IDS:
        row = tasks[task_id]
        _require(
            set(row) == {"task_id", "prompt", "entry_point"},
            f"unexpected model-visible fields for {task_id}",
        )
        ordered.append(
            {
                "task_id": task_id,
                "prompt": row["prompt"],
                "entry_point": row["entry_point"],
            }
        )
    return ordered


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
            and node.func.id
            not in {
                "len",
                "str",
                "int",
                "float",
                "list",
                "dict",
                "set",
                "tuple",
                "bool",
                "type",
                "isinstance",
                "print",
                "range",
                "enumerate",
                "zip",
                "sorted",
                "reversed",
                "sum",
                "min",
                "max",
                "abs",
                "round",
                "any",
                "all",
                "map",
                "filter",
            }
        )
    names = {call.func.id for call in calls}
    _require(len(names) == 1, "validation prompt must expose exactly one entry point")
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
    _require(bool(arities), f"{expected}: positional arity evidence missing")
    return expected, arities


def load_ab2g_text(repo_root: Path = REPO_ROOT) -> str:
    text = (repo_root / AB2G_RELATIVE).read_text(encoding="utf-8")
    _require(text.endswith("\n") or "\n" in text, "Ab2g text unexpectedly empty")
    return text.rstrip("\n")


def compose_condition_text(*, prompt_condition: str, ab2g_text: str) -> str:
    if prompt_condition == "Ab1":
        return ""
    if prompt_condition == "Ab2g":
        return ab2g_text
    if prompt_condition == "Ab2A":
        return AB2A_TEXT
    if prompt_condition == "Ab2gA-factorial-v1":
        return ab2g_text + "\n\n" + AB2A_TEXT
    raise FreezeError(f"unknown prompt_condition: {prompt_condition}")


def compose_full_prompt(
    *,
    official_prompt: str,
    prompt_condition: str,
    ab2g_text: str,
) -> str:
    addon = compose_condition_text(prompt_condition=prompt_condition, ab2g_text=ab2g_text)
    if not addon:
        return official_prompt
    return official_prompt + PROMPT_SEPARATOR + addon


def model_dir(model_tag: str) -> Path:
    return ARTIFACT_RELATIVE / "models" / MODEL_SPECS[model_tag]["model_key"]


def build_generation_cells(
    *,
    model_tag: str,
    tasks: list[dict[str, str]],
    ab2g_text: str,
) -> list[dict[str, Any]]:
    spec = MODEL_SPECS[model_tag]
    cells: list[dict[str, Any]] = []
    for task in tasks:
        expected, arities = prompt_contract(task["prompt"])
        _require(expected == task["entry_point"], f"entry_point drift: {task['task_id']}")
        for seed_index, seed in enumerate(SEEDS):
            for condition in PROMPT_CONDITIONS:
                prompt_condition = condition["prompt_condition"]
                composed = compose_full_prompt(
                    official_prompt=task["prompt"],
                    prompt_condition=prompt_condition,
                    ab2g_text=ab2g_text,
                )
                generation_id = _identity_hash(
                    {
                        "plan_id": PLAN_ID,
                        "task_id": task["task_id"],
                        "seed": seed,
                        "prompt_condition": prompt_condition,
                        "model_tag": model_tag,
                    }
                )
                cell_identity = _identity_hash(
                    {
                        "generation_id": generation_id,
                        "stage_plan": list(STAGES),
                    }
                )
                cells.append(
                    {
                        "cell_identity": cell_identity,
                        "generation_id": generation_id,
                        "task_id": task["task_id"],
                        "seed": seed,
                        "prompt_condition": prompt_condition,
                        "model_tag": model_tag,
                        "model_key": spec["model_key"],
                        "operator_role": spec["operator_role"],
                        "sample_index": seed_index,
                        "composed_prompt_sha256": _sha256_text(composed),
                        "expected_entry_point": expected,
                        "expected_positional_arities": "|".join(map(str, arities)),
                        "validation_only": "true",
                        "forbid_development_substitute": "true",
                    }
                )
    _require(len(cells) == 400, f"{model_tag}: expected 400 cells, got {len(cells)}")
    return cells


def model_identity_block(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "tag": spec["tag"],
        "model_key": spec["model_key"],
        "operator_role": spec["operator_role"],
        "identity_status": spec["identity_status"],
        "identity_source": spec["identity_source"],
        "digest": spec["digest"],
        "parameter_size": spec["parameter_size"],
        "quantization_level": spec["quantization_level"],
        "family": spec["family"],
        "format": spec["format"],
        "size_bytes": spec["size_bytes"],
        "modified_at": spec["modified_at"],
        "template_sha256": spec["template_sha256"],
        "machine_verified_identity_required_before_generate": True,
        "digest_must_be_full_64_hex": True,
        "guessing_forbidden": True,
    }


def build_model_manifest(
    *,
    model_tag: str,
    cells: list[dict[str, Any]],
    hashes: dict[str, str],
) -> dict[str, Any]:
    spec = MODEL_SPECS[model_tag]
    return {
        "plan_id": PLAN_ID,
        "manifest_version": f"{PLAN_ID}_model_{spec['model_key']}",
        "status": "prepared_not_generated",
        "run_id": spec["run_id"],
        "model": model_identity_block(spec),
        "counts": {
            "tasks": 20,
            "seeds": 5,
            "prompt_conditions": 4,
            "candidates": 400,
            "stages_per_candidate": 3,
            "evalplus_cells": 1200,
        },
        "task_ids": list(VALIDATION_TASK_IDS),
        "seeds": list(SEEDS),
        "prompt_conditions": [row["prompt_condition"] for row in PROMPT_CONDITIONS],
        "generation_options": dict(GENERATION_OPTIONS),
        "generation_options_sha256": _sha256_text(
            json.dumps(GENERATION_OPTIONS, sort_keys=True, separators=(",", ":"))
        ),
        "dataset": {
            "name": DATASET_NAME,
            "version": DATASET_VERSION,
            "hash": DATASET_HASH,
        },
        "evalplus": {
            "version": EVALPLUS_VERSION,
            "engine": EVALUATOR_ENGINE,
            "execution_environment": "wsl_linux_only",
        },
        "paths": {
            "governance_model_dir": model_dir(model_tag).as_posix(),
            "generation_output_dir": spec["run_output_relative"].as_posix(),
            "evalplus_output_dir": spec["evalplus_output_relative"].as_posix(),
            "generation_cells": (model_dir(model_tag) / "generation_cells.csv").as_posix(),
            "raw_candidate_sha_ledger": (
                spec["run_output_relative"] / "raw_candidate_sha_ledger.csv"
            ).as_posix(),
        },
        "resume_policy": {
            "single_model_only": True,
            "overwrite_forbidden": True,
            "any_identity_mismatch": "fail_closed",
            "resume_skip_requires_exact_match_of": [
                "cell_identity",
                "generation_id",
                "model_tag",
                "model_digest",
                "composed_prompt_sha256",
                "prompt_condition",
                "seed",
                "completion_flag=success",
                "persisted_complete=true",
            ],
        },
        "isolation": {
            "forbid_cross_model_output_collision": True,
            "forbidden_collision_paths": list(FORBIDDEN_OUTPUT_COLLISION_RELATIVES),
            "peer_model_output_dirs": [
                MODEL_SPECS[tag]["run_output_relative"].as_posix()
                for tag in ALLOWED_MODEL_TAGS
                if tag != model_tag
            ],
        },
        "source_sha256": hashes,
        "cell_count": len(cells),
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }


def build_master_manifest(*, hashes: dict[str, str], tasks: list[dict[str, str]]) -> dict[str, Any]:
    ab2g_text = load_ab2g_text()
    return {
        "plan_id": PLAN_ID,
        "status": "frozen_plans_not_executed",
        "experiment_name": "Validation20 Scaffold × Algorithm Scaffold × Cumulative Healer",
        "design": "2x2 prompt factorial × paired Healer pre/post × 3 models",
        "preregistration_doc": (
            "docs/決賽文件/20260725_Stage2_Validation20_Scaffold_Healer_預登錄規格_v3.md"
        ),
        "supersedes": (
            "docs/決賽文件/20260725_Stage2_Validation20_Scaffold_Healer_預登錄規格_v2.md"
        ),
        "models_axis": ["qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b"],
        "removed_models": ["2B"],
        "2b_forbidden": True,
        "counts": {
            "validation_tasks": 20,
            "seeds": 5,
            "prompt_conditions": 4,
            "models": 3,
            "immutable_candidates": 1200,
            "local_team_candidates": 800,
            "classmate_candidates": 400,
            "primary_comparison_rows_raw_vs_post_healer": 2400,
            "attribution_rows_pipeline_corrected": 1200,
            "evalplus_stage_evaluations": 3600,
            "local_team_evalplus_cells": 2400,
            "classmate_evalplus_cells": 1200,
        },
        "operator_split": {
            "local_team": ["qwen3.5:4b", "qwen3.5:9b"],
            "classmate": ["qwen3:0.6b"],
        },
        "stages": list(STAGES),
        "healer_order": [
            "pipeline_correction=extract_code",
            "H1",
            "H2",
            "H3",
            "H4",
            "EvalPlus",
        ],
        "h4_archive": {
            "commit": H4_ARCHIVE_COMMIT,
            "rule_path": H4_RELATIVE.as_posix(),
            "rule_sha256": H4_RULE_SHA256,
            "implementation_frozen_for_validation": True,
            "qualification_status": "development_candidate_not_frozen",
            "engineering_status": "functionally_demonstrated",
            "development_replay_is_not_evalplus_qualification": True,
            "evalplus_executed": False,
            "execution_safety_status": "not_established",
        },
        "accounting": {
            "formal_ledger": "non_exclusive_multidimensional_labels_v3",
            "dimensions": ["decision", "transition", "repair_depth", "rule_trace"],
            "derived_mutex_summary": list(DERIVED_SUMMARY_PRIORITY),
            "derived_summary_is_mechanically_derived": True,
            "partial_repair_not_verified_rescue": True,
            "parse_rescue_not_verified_rescue": True,
            "execution_rescue_not_verified_rescue": True,
        },
        "execution_environment": {
            "formal_evaluator": "wsl_linux_only",
            "evalplus_version": EVALPLUS_VERSION,
            "dataset_version": DATASET_VERSION,
            "dataset_hash": DATASET_HASH,
            "native_windows_evalplus_forbidden": True,
            "powershell_may_only_invoke_wsl": True,
        },
        "task_ids": list(VALIDATION_TASK_IDS),
        "seeds": list(SEEDS),
        "prompt_conditions": [row["prompt_condition"] for row in PROMPT_CONDITIONS],
        "prompt_separator": PROMPT_SEPARATOR,
        "ab2a_text": AB2A_TEXT,
        "ab2a_text_sha256": _sha256_text(AB2A_TEXT),
        "ab2g_path": AB2G_RELATIVE.as_posix(),
        "ab2g_sha256": hashes[AB2G_RELATIVE.as_posix()],
        "generation_options": dict(GENERATION_OPTIONS),
        "source_sha256": hashes,
        "task_entry_points": {
            task["task_id"]: task["entry_point"] for task in tasks
        },
        "model_manifests": {
            tag: (model_dir(tag) / "model_manifest.json").as_posix()
            for tag in ALLOWED_MODEL_TAGS
        },
        "forbidden_practices": [
            "no_2b_model",
            "no_development_candidate_substitute",
            "no_evalplus_before_blind_healer",
            "no_pass_fail_gated_healer",
            "no_cross_model_output_overwrite",
            "no_native_windows_evalplus",
        ],
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }


def build_evaluation_plan() -> dict[str, Any]:
    return {
        "plan_id": f"{PLAN_ID}_evaluation",
        "status": "prepared_not_executed",
        "dataset_version": DATASET_VERSION,
        "dataset_hash": DATASET_HASH,
        "evalplus_version": EVALPLUS_VERSION,
        "evaluator_engine": EVALUATOR_ENGINE,
        "execution_environment": "wsl_linux_only",
        "stages": list(STAGES),
        "cells_total": 3600,
        "cells_by_model": {
            tag: MODEL_SPECS[tag]["eval_cells_per_model"] for tag in ALLOWED_MODEL_TAGS
        },
        "pairing": {
            "immutable_candidate_identity": "generation_id",
            "raw_stage": "raw",
            "pipeline_stage": "pipeline_corrected",
            "final_stage": "post_h1_h2_h3_h4",
            "byte_identical_stage_cache_allowed": True,
            "byte_identical_cache_requires_provenance_record": True,
            "stage_accounts_never_dropped_when_bytes_identical": True,
        },
        "ledgers_required": [
            "execution_manifest.json",
            "cell_level_ledger.csv",
            "aggregate_summary.json",
            "rescue_ledger.csv",
            "regression_ledger.csv",
            "infrastructure_failure_ledger.csv",
            "eval_result_cache_provenance.jsonl",
        ],
        "healer_blindness": {
            "transform_before_evalplus": True,
            "no_pass_fail_input_to_healer": True,
            "no_canonical_solution_to_healer": True,
            "raw_pass_also_receives_eligibility": True,
        },
        "formal_ledger_dimensions": [
            "decision",
            "transition",
            "repair_depth",
            "rule_trace",
        ],
        "derived_summary_priority": list(DERIVED_SUMMARY_PRIORITY),
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }


def build_derived_summary_schema() -> dict[str, Any]:
    return {
        "schema_id": f"{PLAN_ID}_derived_summary_v1",
        "formal_base_ledger": [
            "decision",
            "transition",
            "repair_depth",
            "rule_trace",
        ],
        "mutex_summary_priority": list(DERIVED_SUMMARY_PRIORITY),
        "rules": {
            "invalid_or_missing_candidate": (
                "candidate missing, SHA mismatch, or stage source unavailable"
            ),
            "evaluator_infrastructure_failure": (
                "EvalPlus harness/platform/import/result-locate failure; "
                "not counted as candidate failure"
            ),
            "verified_rescue": (
                "raw EvalPlus fail AND post_h1_h2_h3_h4 EvalPlus full pass; "
                "parse_rescue/partial_repair/execution_rescue alone never qualify"
            ),
            "execution_regression": (
                "raw EvalPlus pass AND post_h1_h2_h3_h4 EvalPlus fail"
            ),
            "transformed_known_pass_preserved": (
                "raw pass AND final pass AND decision=transformed"
            ),
            "partial_repair": (
                "raw fail AND final fail AND repair_depth indicates improvement "
                "without full EvalPlus pass"
            ),
            "unchanged_pass": "decision=abstained/no_source_change AND raw pass AND final pass",
            "unchanged_failure": (
                "decision=abstained/no_source_change AND raw fail AND final fail"
            ),
        },
        "forbidden_equivalences": [
            "partial_repair != verified_rescue",
            "parse_rescue != verified_rescue",
            "execution_rescue != verified_rescue",
        ],
    }


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    hashes = source_hashes(repo_root)
    tasks = load_validation_tasks(repo_root)
    ab2g_text = load_ab2g_text(repo_root)
    outputs: dict[str, bytes] = {}

    master = build_master_manifest(hashes=hashes, tasks=tasks)
    outputs[(ARTIFACT_RELATIVE / "master_manifest.json").as_posix()] = _json_bytes(master)
    outputs[(ARTIFACT_RELATIVE / "task_manifest.json").as_posix()] = _json_bytes(
        {
            "plan_id": PLAN_ID,
            "role": "validation",
            "source": FROZEN_SPLIT_RELATIVE.as_posix(),
            "frozen_split_sha256": hashes[FROZEN_SPLIT_RELATIVE.as_posix()],
            "task_ids": list(VALIDATION_TASK_IDS),
            "task_count": 20,
            "mutually_exclusive_from": [
                "historical_development_pool",
                "internal_confirmatory_candidate",
                "external_confirmatory_candidate",
                "sealed_reserve",
                "excluded_historical",
            ],
            "tasks": [
                {
                    "task_id": task["task_id"],
                    "entry_point": task["entry_point"],
                    "official_prompt_sha256": _sha256_text(task["prompt"]),
                }
                for task in tasks
            ],
        }
    )
    outputs[(ARTIFACT_RELATIVE / "prompt_conditions.json").as_posix()] = _json_bytes(
        {
            "plan_id": PLAN_ID,
            "separator": PROMPT_SEPARATOR,
            "separator_sha256": _sha256_text(PROMPT_SEPARATOR),
            "ab2g_path": AB2G_RELATIVE.as_posix(),
            "ab2g_sha256": hashes[AB2G_RELATIVE.as_posix()],
            "ab2a_text": AB2A_TEXT,
            "ab2a_text_sha256": _sha256_text(AB2A_TEXT),
            "conditions": list(PROMPT_CONDITIONS),
            "factorial_note": (
                "Ab2gA-factorial-v1 = Ab2g exact text + blank line + Ab2A exact text; "
                "never substitute Ab2gA-short-v1"
            ),
        }
    )
    outputs[(ARTIFACT_RELATIVE / "generation_plan.json").as_posix()] = _json_bytes(
        {
            "plan_id": f"{PLAN_ID}_generation",
            "status": "prepared_not_generated",
            "formula": "20 tasks × 5 seeds × 4 prompt conditions × 3 models = 1200",
            "immutable_candidates": 1200,
            "per_model_candidates": 400,
            "single_model_per_invocation": True,
            "generation_options": dict(GENERATION_OPTIONS),
            "models": {
                tag: {
                    "operator_role": MODEL_SPECS[tag]["operator_role"],
                    "run_id": MODEL_SPECS[tag]["run_id"],
                    "output_dir": MODEL_SPECS[tag]["run_output_relative"].as_posix(),
                    "identity_status": MODEL_SPECS[tag]["identity_status"],
                }
                for tag in ALLOWED_MODEL_TAGS
            },
            "model_calls": 0,
            "candidate_program_executed": False,
            "evalplus_executed": False,
        }
    )
    outputs[(ARTIFACT_RELATIVE / "evaluation_plan.json").as_posix()] = _json_bytes(
        build_evaluation_plan()
    )
    outputs[(ARTIFACT_RELATIVE / "derived_summary_schema.json").as_posix()] = _json_bytes(
        build_derived_summary_schema()
    )

    for model_tag in ALLOWED_MODEL_TAGS:
        cells = build_generation_cells(
            model_tag=model_tag, tasks=tasks, ab2g_text=ab2g_text
        )
        manifest = build_model_manifest(
            model_tag=model_tag, cells=cells, hashes=hashes
        )
        rel_dir = model_dir(model_tag)
        outputs[(rel_dir / "model_manifest.json").as_posix()] = _json_bytes(manifest)
        outputs[(rel_dir / "generation_cells.csv").as_posix()] = _csv_bytes(
            cells, CELL_FIELDS
        )

    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    outputs = build_outputs(repo_root)
    digests: dict[str, str] = {}
    for relative, payload in outputs.items():
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_bytes()
            _require(
                existing == payload,
                f"refusing to overwrite drifted artifact: {relative}",
            )
        else:
            path.write_bytes(payload)
        digests[relative] = _sha256_bytes(payload)
    lock_path = repo_root / ARTIFACT_RELATIVE / "artifact_lock.json"
    lock = {
        "plan_id": PLAN_ID,
        "status": "frozen_plans_not_executed",
        "artifact_sha256": digests,
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }
    lock_bytes = _json_bytes(lock)
    if lock_path.exists():
        _require(lock_path.read_bytes() == lock_bytes, "artifact_lock drift")
    else:
        lock_path.write_bytes(lock_bytes)
    digests[lock_path.relative_to(repo_root).as_posix()] = _sha256_bytes(lock_bytes)
    return digests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Rebuild in memory and verify on-disk bytes without writing.",
    )
    args = parser.parse_args(argv)
    if args.check:
        outputs = build_outputs()
        for relative, payload in outputs.items():
            path = REPO_ROOT / relative
            _require(path.is_file(), f"missing: {relative}")
            _require(path.read_bytes() == payload, f"drift: {relative}")
        print(
            json.dumps(
                {
                    "status": "freeze_check_passed",
                    "artifacts": len(outputs),
                    "model_calls": 0,
                    "candidate_program_executed": False,
                    "evalplus_executed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    digests = write_outputs()
    print(
        json.dumps(
            {
                "status": "freeze_written",
                "artifacts": len(digests),
                "model_calls": 0,
                "candidate_program_executed": False,
                "evalplus_executed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
