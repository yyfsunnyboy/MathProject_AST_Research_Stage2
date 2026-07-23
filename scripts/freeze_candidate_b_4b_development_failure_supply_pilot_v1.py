#!/usr/bin/env python3
"""Freeze the qwen3.5:4b development-only failure-supply pilot preregistration.

Zero-model materializer. Writes governance artifacts only. Never calls Ollama
generation, never executes candidate code, never evaluates with EvalPlus, and
never modifies Healer.
"""

from __future__ import annotations

import argparse
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

OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_development_failure_supply_pilot_preregistration_v1"
)
RUN_ID = "mbpp_q35_4b_dev20_failure_supply_pilot_r001"
RUN_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_4b_failure_supply_pilot/"
    f"runs/{RUN_ID}"
)
NINE_B_RUN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r003"
)
NINE_B_AB1_RUN_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
    "mbpp_qwen35_9b_ab1_dev_run_003"
)
NINE_B_SCAFFOLD_RUN_RELATIVE = Path("artifacts/pbd/mbpp_sv0/r002")

FROZEN_SPLIT_RELATIVE = Path("artifacts/public_benchmark_governance/frozen_split.csv")
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
SCAFFOLD_RELATIVE = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0.txt")
SCAFFOLD_MANIFEST_RELATIVE = Path(
    "configs/scaffolds/mbpp_generic_code_scaffold_v0_manifest.json"
)
TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
HEALER_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
PIPELINE_RELATIVE = Path("agent_tools/finals_rebuild/extraction.py")

EXPECTED_FROZEN_SPLIT_SHA256 = (
    "3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4"
)
EXPECTED_PROTOCOL_SHA256 = (
    "987fb107bd6b36703ba6289fbd89a2aa69856031fd82402600794915ae0b583d"
)
EXPECTED_SCAFFOLD_SHA256 = (
    "31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305"
)
EXPECTED_HEALER_SHA256 = (
    "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
)
EXPECTED_PIPELINE_SHA256 = (
    "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
)

MODEL_TAG = "qwen3.5:4b"
MODEL_DIGEST = "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd"
MODEL_QUANTIZATION = "Q4_K_M"
MODEL_PARAMETER_SIZE = "4.7B"
MODEL_SIZE_BYTES = 3389983735
MODEL_TEMPLATE_SHA256 = (
    "b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315"
)
MODEL_MODIFIED_AT = "2026-07-16T22:38:31.4275049+08:00"
PROTOCOL_OLLAMA_VERSION = "0.32.0"
OBSERVED_OLLAMA_VERSION_AT_PREREG = "0.32.1"
NINE_B_MODEL_TAG = "qwen3.5:9b"
NINE_B_MODEL_DIGEST = (
    "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
)

SEEDS = (11, 22, 33, 44, 55)
CONDITIONS = (
    {
        "condition_id": "Ab1_H0",
        "generation_condition": "Ab1",
        "scaffold_mode": "bare",
        "healer_account_mapping": "H0",
        "spec_label": "Ab1-Raw / Observed control mapping",
        "prompt_condition": "Ab1",
    },
    {
        "condition_id": "Ab2g_H1",
        "generation_condition": "Ab2g",
        "scaffold_mode": "generic_scaffold_v0",
        "healer_account_mapping": "H1",
        "spec_label": "Ab2g-Raw with Generic Code Scaffold v0 (mapped as H1 arm)",
        "prompt_condition": "Ab2g",
    },
)
EXPECTED_TASK_COUNT = 20
EXPECTED_CELL_COUNT = 200
STATUS = "4B_DEVELOPMENT_FAILURE_SUPPLY_PILOT_PREREGISTERED_NOT_EXECUTED"
PILOT_WAIVER = "development_only_failure_supply_pilot_v1"

PROMPT_SEPARATOR = "\n\n--- GENERIC CODE SCAFFOLD V0 ---\n\n"
GENERATION_OPTIONS = {
    "num_ctx": 8192,
    "num_predict": 2048,
    "stream": False,
    "temperature": 0.2,
    "thinking": False,
    "top_k": 20,
    "top_p": 0.95,
}

ACTIVE_TASK_IDS = (
    "Mbpp/633",
    "Mbpp/769",
    "Mbpp/453",
    "Mbpp/259",
    "Mbpp/739",
    "Mbpp/124",
    "Mbpp/72",
    "Mbpp/792",
    "Mbpp/435",
    "Mbpp/597",
    "Mbpp/732",
    "Mbpp/721",
    "Mbpp/765",
    "Mbpp/777",
    "Mbpp/473",
    "Mbpp/420",
    "Mbpp/742",
    "Mbpp/279",
    "Mbpp/125",
    "Mbpp/603",
)

CELL_FIELDS = (
    "cell_index",
    "cell_identity",
    "run_id",
    "task_id",
    "seed",
    "sample_index",
    "condition_id",
    "generation_condition",
    "scaffold_mode",
    "healer_account_mapping",
    "prompt_condition",
    "generation_id",
    "program_id",
    "official_prompt_sha256",
    "composed_prompt_sha256",
    "scaffold_sha256",
    "model_tag",
    "model_digest",
    "development_only",
    "completion_flag",
)

FORBIDDEN_ROLES = (
    "validation",
    "confirmatory",
    "sealed_reserve",
    "human_eval_plus_external",
)


class PilotFreezeError(RuntimeError):
    """Raised before writes when any pilot invariant drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotFreezeError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _source_hash(repo_root: Path, relative: Path, expected: str) -> str:
    actual = _sha256_bytes((repo_root / relative).read_bytes())
    _require(actual == expected, f"source SHA-256 drift: {relative.as_posix()}")
    return actual


def _load_active_rows(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / FROZEN_SPLIT_RELATIVE
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    active = [
        row
        for row in rows
        if row["dataset"] == "MBPP+"
        and row["proposed_role"] == "historical_development_pool"
        and row["active_development_generation_subset"].lower() == "true"
    ]
    task_ids = [row["task_id"] for row in active]
    _require(
        task_ids == list(ACTIVE_TASK_IDS),
        f"active development subset drift: {task_ids}",
    )
    _require(
        all(row["confirmatory_eligible"].lower() == "false" for row in active),
        "active subset contains confirmatory-eligible task",
    )
    contaminated = [
        row["task_id"]
        for row in rows
        if row["task_id"] in set(ACTIVE_TASK_IDS)
        and (
            row["proposed_role"] in FORBIDDEN_ROLES
            or row.get("confirmatory_eligible", "").lower() == "true"
        )
    ]
    _require(not contaminated, f"development-only leak: {contaminated}")
    return active


def _load_prompts(repo_root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    path = repo_root / TASKS_RELATIVE
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in ACTIVE_TASK_IDS:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"{path.as_posix()}:{line_no}: unexpected model-visible fields",
            )
            found[task_id] = record["prompt"]
    missing = [task_id for task_id in ACTIVE_TASK_IDS if task_id not in found]
    _require(not missing, f"missing model-visible prompts: {missing}")
    return found


def _compose_prompt(official: str, condition: dict[str, str], scaffold_text: str) -> str:
    if condition["scaffold_mode"] == "bare":
        return official
    _require(
        condition["scaffold_mode"] == "generic_scaffold_v0",
        f"unknown scaffold mode: {condition['scaffold_mode']}",
    )
    return official + PROMPT_SEPARATOR + scaffold_text


def _generation_id(
    *,
    task_id: str,
    seed: int,
    condition_id: str,
    composed_prompt_sha256: str,
) -> str:
    material = (
        f"{RUN_ID}|{task_id}|{seed}|{condition_id}|"
        f"{MODEL_DIGEST}|{composed_prompt_sha256}"
    )
    return _sha256_text(material)


def _cell_identity(
    *,
    task_id: str,
    seed: int,
    condition_id: str,
    generation_id: str,
    composed_prompt_sha256: str,
) -> str:
    payload = {
        "run_id": RUN_ID,
        "task_id": task_id,
        "seed": seed,
        "condition_id": condition_id,
        "model_tag": MODEL_TAG,
        "model_digest": MODEL_DIGEST,
        "composed_prompt_sha256": composed_prompt_sha256,
        "generation_id": generation_id,
        "completion_flag": "pending",
    }
    return _sha256_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
    )


def build_cells(
    prompts: dict[str, str],
    scaffold_text: str,
    scaffold_sha256: str,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    index = 0
    for task_id in ACTIVE_TASK_IDS:
        official = prompts[task_id]
        official_sha = _sha256_text(official)
        for seed_index, seed in enumerate(SEEDS, start=1):
            for condition in CONDITIONS:
                composed = _compose_prompt(official, condition, scaffold_text)
                composed_sha = _sha256_text(composed)
                generation_id = _generation_id(
                    task_id=task_id,
                    seed=seed,
                    condition_id=condition["condition_id"],
                    composed_prompt_sha256=composed_sha,
                )
                program_id = _sha256_text(f"program|{generation_id}")
                cell_identity = _cell_identity(
                    task_id=task_id,
                    seed=seed,
                    condition_id=condition["condition_id"],
                    generation_id=generation_id,
                    composed_prompt_sha256=composed_sha,
                )
                index += 1
                cells.append(
                    {
                        "cell_index": str(index),
                        "cell_identity": cell_identity,
                        "run_id": RUN_ID,
                        "task_id": task_id,
                        "seed": str(seed),
                        "sample_index": str(seed_index),
                        "condition_id": condition["condition_id"],
                        "generation_condition": condition["generation_condition"],
                        "scaffold_mode": condition["scaffold_mode"],
                        "healer_account_mapping": condition["healer_account_mapping"],
                        "prompt_condition": condition["prompt_condition"],
                        "generation_id": generation_id,
                        "program_id": program_id,
                        "official_prompt_sha256": official_sha,
                        "composed_prompt_sha256": composed_sha,
                        "scaffold_sha256": (
                            ""
                            if condition["scaffold_mode"] == "bare"
                            else scaffold_sha256
                        ),
                        "model_tag": MODEL_TAG,
                        "model_digest": MODEL_DIGEST,
                        "development_only": "true",
                        "completion_flag": "pending",
                    }
                )
    _require(len(cells) == EXPECTED_CELL_COUNT, f"expected 200 cells, got {len(cells)}")
    identities = {row["cell_identity"] for row in cells}
    generation_ids = {row["generation_id"] for row in cells}
    _require(len(identities) == EXPECTED_CELL_COUNT, "cell_identity collision")
    _require(len(generation_ids) == EXPECTED_CELL_COUNT, "generation_id collision")
    return cells


def build_manifest(
    *,
    source_hashes: dict[str, str],
    cells: list[dict[str, Any]],
    scaffold_sha256: str,
) -> dict[str, Any]:
    return {
        "manifest_version": "candidate_b_4b_development_failure_supply_pilot_preregistration_v1",
        "status": STATUS,
        "pilot_waiver": PILOT_WAIVER,
        "run_id": RUN_ID,
        "output_directory": RUN_OUTPUT_RELATIVE.as_posix(),
        "research_scope": "HumanEval+_MBPP+_Stage2_development_only",
        "dataset": "MBPP+",
        "split_policy": {
            "source": FROZEN_SPLIT_RELATIVE.as_posix(),
            "frozen_split_sha256": source_hashes[FROZEN_SPLIT_RELATIVE.as_posix()],
            "allowed_role": "historical_development_pool",
            "active_development_generation_subset_only": True,
            "task_count": EXPECTED_TASK_COUNT,
            "task_ids": list(ACTIVE_TASK_IDS),
            "forbidden_roles": list(FORBIDDEN_ROLES),
            "forbid_validation": True,
            "forbid_confirmatory": True,
            "forbid_sealed_reserve": True,
            "forbid_humaneval_plus_external": True,
        },
        "design": {
            "tasks": EXPECTED_TASK_COUNT,
            "seeds": list(SEEDS),
            "conditions": [dict(item) for item in CONDITIONS],
            "raw_program_cells": EXPECTED_CELL_COUNT,
            "formula": "20 tasks × 5 seeds × 2 conditions = 200 raw programs",
            "auto_expand_to_60_tasks": False,
        },
        "model": {
            "tag": MODEL_TAG,
            "digest": MODEL_DIGEST,
            "quantization": MODEL_QUANTIZATION,
            "parameter_size": MODEL_PARAMETER_SIZE,
            "size_bytes": MODEL_SIZE_BYTES,
            "template_sha256": MODEL_TEMPLATE_SHA256,
            "modified_at": MODEL_MODIFIED_AT,
            "protocol_role": "frozen_transfer_model",
            "public_benchmark_general_execution_allowed": False,
            "pilot_execution_waiver": PILOT_WAIVER,
            "protocol_ollama_version_pin": PROTOCOL_OLLAMA_VERSION,
            "observed_ollama_runtime_version_at_preregistration": (
                OBSERVED_OLLAMA_VERSION_AT_PREREG
            ),
            "digest_source": "local_ollama_/api/tags_live_inspect_matched_protocol",
        },
        "parity_with_9b": {
            "primary_contrast_model_tag": NINE_B_MODEL_TAG,
            "primary_contrast_model_digest": NINE_B_MODEL_DIGEST,
            "generation_options": GENERATION_OPTIONS,
            "scaffold_path": SCAFFOLD_RELATIVE.as_posix(),
            "scaffold_sha256": scaffold_sha256,
            "prompt_separator": PROMPT_SEPARATOR,
            "pipeline_path": PIPELINE_RELATIVE.as_posix(),
            "pipeline_sha256": source_hashes[PIPELINE_RELATIVE.as_posix()],
            "healer_path": HEALER_RELATIVE.as_posix(),
            "healer_sha256": source_hashes[HEALER_RELATIVE.as_posix()],
            "healer_modification_allowed": False,
            "planned_primary_difference": "model_tag_and_digest_only_qwen3.5:4b",
            "isolated_from_9b_output_dirs": [
                NINE_B_RUN_RELATIVE.as_posix(),
                NINE_B_AB1_RUN_RELATIVE.as_posix(),
                NINE_B_SCAFFOLD_RUN_RELATIVE.as_posix(),
            ],
        },
        "stop_and_expansion_gates": {
            "complete_200_cells_before_any_rule_search": True,
            "auto_expand_to_60_forbidden": True,
            "stop_rule_search_if_pipeline_corrected_failures_lt": 20,
            "stop_rule_search_if_distinct_failure_tasks_lt": 5,
            "candidate_general_rule_min_distinct_tasks": 2,
            "detector_may_use_task_id": False,
            "detector_may_use_answers": False,
            "detector_may_use_post_repair_pass": False,
            "repair_must_be_unique_local_deterministic": True,
            "answer_independent_safety_guard_required": True,
            "fail_gate_implies": "GENERAL_HEALER_ABSTAIN_NO_HEALER_MODIFICATION",
        },
        "resume_policy": {
            "overwrite_forbidden": True,
            "resume_skip_requires_exact_match_of": [
                "cell_identity",
                "model_tag",
                "model_digest",
                "composed_prompt_sha256",
                "condition_id",
                "seed",
                "completion_flag=success",
            ],
            "any_identity_mismatch": "fail_closed",
        },
        "execution_state": {
            "model_calls": 0,
            "candidate_code_executions": 0,
            "evalplus_executions": 0,
            "healer_modifications": 0,
            "raw_programs_materialized": 0,
            "preregistered_not_executed": True,
        },
        "source_hashes": source_hashes,
        "cell_count": len(cells),
        "unique_task_count": len({row["task_id"] for row in cells}),
        "unique_condition_count": len({row["condition_id"] for row in cells}),
    }


def build_preregistration_markdown(manifest: dict[str, Any]) -> str:
    tasks = "\n".join(f"- `{task_id}`" for task_id in ACTIVE_TASK_IDS)
    return f"""# 4B Development-only Failure-supply Pilot Preregistration

## Status

`{STATUS}`

本輪僅完成執行配套與預登錄，**尚未呼叫模型、尚未產生任何 4B raw program、尚未修改 Healer**。

## Research Boundary

- Scope：HumanEval+／MBPP+ Stage2 development-only
- Model：`{MODEL_TAG}` digest `{MODEL_DIGEST}`
- Quantization：`{MODEL_QUANTIZATION}`；parameter size：`{MODEL_PARAMETER_SIZE}`
- Protocol role：`frozen_transfer_model`（一般 public-benchmark execution 仍為 false）
- Pilot waiver：`{PILOT_WAIVER}`（僅授權本 development-only failure-supply pilot）
- Protocol Ollama pin：`{PROTOCOL_OLLAMA_VERSION}`；prereg 當下本機觀察：`{OBSERVED_OLLAMA_VERSION_AT_PREREG}`

## Fixed Design

- Tasks：凍結 `active_development_generation_subset` 20 題
- Frozen split SHA-256：`{EXPECTED_FROZEN_SPLIT_SHA256}`
- Seeds：`{list(SEEDS)}`
- Conditions：`Ab1_H0`（bare／H0 mapping）與 `Ab2g_H1`（Generic Code Scaffold v0／H1 mapping）
- Cells：20 × 5 × 2 = **200** raw programs
- Scaffold SHA-256：`{EXPECTED_SCAFFOLD_SHA256}`
- Generation options 與 9B 對照保持一致；計畫內主要差異僅模型改為 `{MODEL_TAG}`

## Active Development Tasks

{tasks}

## Output Isolation

- Pilot run directory：`{RUN_OUTPUT_RELATIVE.as_posix()}`
- 不得覆寫 9B 或其他既有 artifact
- resume 僅在 cell identity、model fingerprint、prompt SHA、condition、seed 與完成旗標全部吻合時 skip；任一不符 fail-closed

## Stop / Expansion Gates

- 先完成 200 格試點，不得自動擴展至 60 題
- pipeline-corrected failures < 20 或涵蓋 < 5 distinct tasks → 停止後續規則搜尋
- 候選通用規則至少需 2 個不同 task 的獨立證據
- detector 不得依賴 Task ID、答案或修後 PASS
- repair 必須唯一、局部、決定性，並具備答案無關 safety guard
- 未通過門檻即 ABSTAIN，不得修改 Healer

## Explicit Non-claims

- 本文件不宣稱 4B 已產生結果
- 本文件不宣稱已找到新的通用 Healer 規則
- Conditional23 正式結論維持 ABSTAIN／現有 Healer 凍結
"""


def build_zero_model_preflight_receipt(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "zero_model_preflight_passed",
        "run_id": RUN_ID,
        "model_calls": 0,
        "ollama_generation_calls": 0,
        "candidate_code_executions": 0,
        "evalplus_executions": 0,
        "healer_modifications": 0,
        "cell_count": manifest["cell_count"],
        "task_count": manifest["unique_task_count"],
        "condition_count": manifest["unique_condition_count"],
        "output_directory": RUN_OUTPUT_RELATIVE.as_posix(),
        "output_directory_must_be_absent_or_compatible_resume": True,
        "overwrite_forbidden": True,
        "development_only_verified": True,
        "forbidden_roles_blocked": list(FORBIDDEN_ROLES),
        "model_digest_pinned": MODEL_DIGEST,
        "public_benchmark_general_execution_allowed": False,
        "pilot_waiver": PILOT_WAIVER,
    }


def build_outputs(repo_root: Path) -> dict[str, bytes]:
    source_hashes = {
        FROZEN_SPLIT_RELATIVE.as_posix(): _source_hash(
            repo_root, FROZEN_SPLIT_RELATIVE, EXPECTED_FROZEN_SPLIT_SHA256
        ),
        PROTOCOL_RELATIVE.as_posix(): _source_hash(
            repo_root, PROTOCOL_RELATIVE, EXPECTED_PROTOCOL_SHA256
        ),
        SCAFFOLD_RELATIVE.as_posix(): _source_hash(
            repo_root, SCAFFOLD_RELATIVE, EXPECTED_SCAFFOLD_SHA256
        ),
        HEALER_RELATIVE.as_posix(): _source_hash(
            repo_root, HEALER_RELATIVE, EXPECTED_HEALER_SHA256
        ),
        PIPELINE_RELATIVE.as_posix(): _source_hash(
            repo_root, PIPELINE_RELATIVE, EXPECTED_PIPELINE_SHA256
        ),
    }
    protocol = json.loads((repo_root / PROTOCOL_RELATIVE).read_text(encoding="utf-8"))
    transfer = protocol["models"]["frozen_transfer_model"]
    _require(transfer["tag"] == MODEL_TAG, "protocol 4B tag drift")
    _require(transfer["digest"] == MODEL_DIGEST, "protocol 4B digest drift")
    _require(transfer["quantization"] == MODEL_QUANTIZATION, "protocol 4B quant drift")
    _require(
        transfer["public_benchmark_execution_allowed"] is False,
        "protocol must keep general 4B public execution disabled",
    )
    _require(
        transfer["template_sha256"] == MODEL_TEMPLATE_SHA256,
        "protocol 4B template SHA drift",
    )
    _require(protocol["generation"] == GENERATION_OPTIONS, "generation options drift")
    _require(tuple(protocol["seeds"]) == SEEDS, "seed schedule drift")

    scaffold_text = (repo_root / SCAFFOLD_RELATIVE).read_text(encoding="utf-8")
    scaffold_sha = source_hashes[SCAFFOLD_RELATIVE.as_posix()]
    _require(
        _sha256_text(scaffold_text) == scaffold_sha,
        "scaffold text/hash mismatch",
    )
    _load_active_rows(repo_root)
    prompts = _load_prompts(repo_root)
    cells = build_cells(prompts, scaffold_text, scaffold_sha)
    manifest = build_manifest(
        source_hashes=source_hashes,
        cells=cells,
        scaffold_sha256=scaffold_sha,
    )
    preflight = build_zero_model_preflight_receipt(manifest)
    active_list = {
        "frozen_split_sha256": EXPECTED_FROZEN_SPLIT_SHA256,
        "active_development_generation_subset": True,
        "task_ids": list(ACTIVE_TASK_IDS),
        "task_count": EXPECTED_TASK_COUNT,
    }
    stop_gates = manifest["stop_and_expansion_gates"]
    provenance = {
        "status": STATUS,
        "authoritative_sources": source_hashes,
        "model_fingerprint": {
            "tag": MODEL_TAG,
            "digest": MODEL_DIGEST,
            "quantization": MODEL_QUANTIZATION,
            "parameter_size": MODEL_PARAMETER_SIZE,
            "template_sha256": MODEL_TEMPLATE_SHA256,
            "modified_at": MODEL_MODIFIED_AT,
            "size_bytes": MODEL_SIZE_BYTES,
            "observed_ollama_runtime_version_at_preregistration": (
                OBSERVED_OLLAMA_VERSION_AT_PREREG
            ),
        },
        "isolation": {
            "pilot_output": RUN_OUTPUT_RELATIVE.as_posix(),
            "must_not_overwrite": [
                NINE_B_RUN_RELATIVE.as_posix(),
                NINE_B_AB1_RUN_RELATIVE.as_posix(),
                NINE_B_SCAFFOLD_RUN_RELATIVE.as_posix(),
            ],
        },
        "execution_state": manifest["execution_state"],
    }
    return {
        "manifest.json": _canonical_bytes(manifest),
        "preregistration.md": build_preregistration_markdown(manifest).encode("utf-8"),
        "generation_cells.csv": _csv_bytes(cells, CELL_FIELDS),
        "active_development_task_list.json": _canonical_bytes(active_list),
        "zero_model_preflight.json": _canonical_bytes(preflight),
        "stop_and_expansion_gates.json": _canonical_bytes(stop_gates),
        "provenance.json": _canonical_bytes(provenance),
        "execution_spec.json": _canonical_bytes(
            {
                "run_id": RUN_ID,
                "output_directory": RUN_OUTPUT_RELATIVE.as_posix(),
                "model_tag": MODEL_TAG,
                "model_digest": MODEL_DIGEST,
                "seeds": list(SEEDS),
                "conditions": [dict(item) for item in CONDITIONS],
                "generation_options": GENERATION_OPTIONS,
                "scaffold_sha256": scaffold_sha,
                "cell_count": EXPECTED_CELL_COUNT,
                "resume_policy": manifest["resume_policy"],
                "healer_modification_allowed": False,
                "preregistered_not_executed": True,
            }
        ),
    }


def write_outputs(repo_root: Path, *, check_only: bool = False) -> dict[str, str]:
    outputs = build_outputs(repo_root)
    out_dir = repo_root / OUTPUT_RELATIVE
    hashes = {name: _sha256_bytes(payload) for name, payload in outputs.items()}
    if check_only:
        for name, payload in outputs.items():
            path = out_dir / name
            _require(path.is_file(), f"missing frozen artifact: {path.as_posix()}")
            actual = path.read_bytes()
            _require(
                actual == payload,
                f"frozen artifact drift: {path.as_posix()}",
            )
        return hashes
    if out_dir.exists():
        existing = sorted(p.name for p in out_dir.iterdir() if p.is_file())
        _require(
            not existing or set(existing) <= set(outputs),
            f"refusing to overwrite unexpected files in {out_dir.as_posix()}: {existing}",
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        path = out_dir / name
        if path.exists() and path.read_bytes() != payload:
            raise PilotFreezeError(f"refusing to overwrite drifted artifact: {path.as_posix()}")
        path.write_bytes(payload)
    return hashes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate existing frozen artifacts without writing.",
    )
    args = parser.parse_args(argv)
    hashes = write_outputs(REPO_ROOT, check_only=args.check)
    print(
        json.dumps(
            {
                "status": STATUS if not args.check else "CHECK_PASSED",
                "output_directory": OUTPUT_RELATIVE.as_posix(),
                "artifact_sha256": hashes,
                "model_calls": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
