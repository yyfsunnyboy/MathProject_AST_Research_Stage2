#!/usr/bin/env python3
"""Freeze Milestone 2E prospective P0/Candidate-A expansion protocol artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PureWindowsPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_a_expansion_protocol_v1"
)
FROZEN_SPLIT = Path("artifacts/public_benchmark_governance/frozen_split.csv")
EXPANSION_CSV = Path(
    "artifacts/public_benchmark_governance/development_expansion_v1/"
    "development_expansion_manifest.csv"
)
EXPANSION_JSON = Path(
    "artifacts/public_benchmark_governance/development_expansion_v1/"
    "development_expansion_manifest.json"
)
M2C_MANIFEST = Path(
    "artifacts/pbd/mbpp_sv0/r002/milestone_2c_v1_candidate_design/"
    "milestone_2c_manifest.json"
)
M2C_CANDIDATES = Path(
    "artifacts/pbd/mbpp_sv0/r002/milestone_2c_v1_candidate_design/"
    "scaffold_v1_candidates.json"
)
GENERATION_PROTOCOL = Path("configs/public_benchmark_generation_protocol_v1.json")
V0_MANIFEST = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0_manifest.json")

SOURCE_PATHS = {
    "frozen_split.csv": FROZEN_SPLIT,
    "development_expansion_manifest.csv": EXPANSION_CSV,
    "development_expansion_manifest.json": EXPANSION_JSON,
    "milestone_2c_manifest.json": M2C_MANIFEST,
    "scaffold_v1_candidates.json": M2C_CANDIDATES,
    "generation_protocol_v1.json": GENERATION_PROTOCOL,
    "mbpp_generic_code_scaffold_v0_manifest.json": V0_MANIFEST,
}
EXPECTED_SOURCE_HASHES = {
    "frozen_split.csv": "3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4",
    "development_expansion_manifest.csv": "daa12bf45ba78e4f83a40b3a1005079867417950da05e9ff9fca58bdf9777cce",
    "development_expansion_manifest.json": "b6b97e4a1e189491184f5d1d5ae960d5171e07e6266c7c0429db74914803fb91",
    "milestone_2c_manifest.json": "3a6acb130affb5414228594367fc9fc41a9229e510ea1da9198efd57ad9b8ef3",
    "scaffold_v1_candidates.json": "6a19996316031697699f9ea9f3447d4a3df286e28e5c132a57cb8c6c65d6a54a",
    "generation_protocol_v1.json": "987fb107bd6b36703ba6289fbd89a2aa69856031fd82402600794915ae0b583d",
    "mbpp_generic_code_scaffold_v0_manifest.json": "b48576bf74c6b5aae1a3f4a4c4266da5ee78e1df8e77f877b67f903e9ada93da",
}

STARTING_HEAD = "54a79833f393af1096d757fdf72c039536e9775a"
DATASET = "MBPP+"
DATASET_VERSION = "v0.2.0"
DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
MODEL = "qwen3.5:9b"
MODEL_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
QUANTIZATION = "Q4_K_M"
SEEDS = [11, 22, 33, 44, 55]
TASK_COUNT = 40
CELLS_PER_TREATMENT = 200
TOTAL_PLANNED_CELLS = 400
TIMEOUT_SECONDS = 600.0
WINDOWS_PATH_BUDGET = 240
WINDOWS_REPO_PREFIX = r"C:\Users\yehya\Documents\GitHub\MathProject_AST_Research_Stage2"

P0_TREATMENT_ID = "p0_official_prompt_only"
CA_TREATMENT_ID = "candidate_a_scaffold"
P0_RUN_ID = "mbpp_q35_9b_p0_exp40_r001"
CA_RUN_ID = "mbpp_q35_9b_ca_exp40_r001"
PAIRED_ANALYSIS_ID = "mbpp_q35_9b_ca_exp40_paired_r001"
P0_PHYSICAL = Path("artifacts/pbd/mbpp_e40/p0/r001")
CA_PHYSICAL = Path("artifacts/pbd/mbpp_e40/ca/r001")
PAIRED_PHYSICAL = Path("artifacts/pbd/mbpp_e40/pa/r001")
JOURNAL_DIRECTORY = "j"

CANDIDATE_ID = "v1_candidate_a_conservative_compaction"
CANDIDATE_STATUS = "frozen_experimental_candidate_not_official_v1"
CANDIDATE_SHA256 = "bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058"
PROMPT_SEPARATOR = "\n\n--- GENERIC CODE SCAFFOLD V0 ---\n\n"
PROMPT_SEPARATOR_SHA256 = "dc61671dd31a04c2f638edd612b86cc339fa1c89f81df2e4fb73344312077c1e"


class ProspectiveProtocolError(RuntimeError):
    """Raised before writes when prospective protocol evidence drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProspectiveProtocolError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def render_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _source_hashes(repo_root: Path) -> dict[str, str]:
    hashes = {
        label: sha256_bytes((repo_root / path).read_bytes())
        for label, path in SOURCE_PATHS.items()
    }
    _require(hashes == EXPECTED_SOURCE_HASHES, "prospective protocol source hash mismatch")
    return hashes


def _load_inputs(repo_root: Path) -> dict[str, Any]:
    source_hashes = _source_hashes(repo_root)
    expansion = json.loads((repo_root / EXPANSION_JSON).read_text(encoding="utf-8"))
    candidates = json.loads((repo_root / M2C_CANDIDATES).read_text(encoding="utf-8"))
    m2c = json.loads((repo_root / M2C_MANIFEST).read_text(encoding="utf-8"))
    protocol = json.loads((repo_root / GENERATION_PROTOCOL).read_text(encoding="utf-8"))
    v0_manifest = json.loads((repo_root / V0_MANIFEST).read_text(encoding="utf-8"))

    _require(expansion["status"] == "frozen_development_expansion_overlay", "2D overlay not frozen")
    expansion_tasks = [
        row
        for row in expansion["development_tasks"]
        if row["development_layer"] == "expansion_development"
    ]
    discovery_tasks = [
        row
        for row in expansion["development_tasks"]
        if row["development_layer"] == "discovery_development"
    ]
    task_ids = [row["task_id"] for row in expansion_tasks]
    _require(len(task_ids) == len(set(task_ids)) == TASK_COUNT, "expansion scope must be 40 unique tasks")
    _require(len(discovery_tasks) == 20, "2D discovery count drift")
    _require(
        not (set(task_ids) & {row["task_id"] for row in discovery_tasks}),
        "prospective scope overlaps discovery development",
    )
    _require(
        all(
            row["dataset"] == DATASET
            and row["dataset_version"] == DATASET_VERSION
            and row["source_frozen_governance_role"] == "historical_development_pool"
            and row["overlay_assignment_status"] == "frozen"
            for row in expansion_tasks
        ),
        "expansion task governance drift",
    )
    _require(
        expansion["zero_overlap"]["verified_total_forbidden_overlap"] == 0,
        "2D forbidden-role overlap changed",
    )
    with (repo_root / FROZEN_SPLIT).open(encoding="utf-8", newline="") as handle:
        frozen_rows = list(csv.DictReader(handle))
    _require(len(frozen_rows) == 542, "frozen split row count drift")
    frozen_keys = {(row["dataset"], row["task_id"]) for row in frozen_rows}
    _require(len(frozen_keys) == 542, "frozen split identities are not unique")
    _require(
        all(row["split_assignment_status"] == "frozen" for row in frozen_rows),
        "source split is not fully frozen",
    )
    frozen_by_key = {
        (row["dataset"], row["task_id"]): row for row in frozen_rows
    }
    expansion_keys = {(DATASET, task_id) for task_id in task_ids}
    _require(expansion_keys <= frozen_keys, "expansion task absent from frozen split")
    _require(
        all(
            frozen_by_key[key]["proposed_role"] == "historical_development_pool"
            and frozen_by_key[key]["confirmatory_eligible"] == "false"
            for key in expansion_keys
        ),
        "expansion scope contains non-historical or confirmatory-eligible task",
    )
    forbidden_roles = {
        "validation",
        "internal_confirmatory_candidate",
        "external_confirmatory_candidate",
        "excluded_historical",
        "sealed_reserve",
    }
    forbidden_keys = {
        (row["dataset"], row["task_id"])
        for row in frozen_rows
        if row["proposed_role"] in forbidden_roles
    }
    _require(not (expansion_keys & forbidden_keys), "expansion scope overlaps forbidden frozen roles")

    _require(m2c["freeze_status"] == "尚不凍結，只保留候選", "2C status drift")
    candidate = next(
        item for item in candidates["candidates"] if item["candidate_id"] == CANDIDATE_ID
    )
    candidate_text = candidate["exact_text_utf8"]
    _require(sha256_text(candidate_text) == CANDIDATE_SHA256, "Candidate A exact text drift")
    _require(candidate["changes_prompt_composition"] is False, "Candidate A composition drift")
    _require(candidates["freeze_status"] == "尚不凍結，只保留候選", "2C candidate status drift")

    primary = protocol["models"]["primary_development_model"]
    generation = protocol["generation"]
    _require(primary["tag"] == MODEL and primary["digest"] == MODEL_DIGEST, "model identity drift")
    _require(primary["quantization"] == QUANTIZATION, "quantization drift")
    _require(generation["thinking"] is False, "thinking must remain false")
    _require(protocol["seeds"] == SEEDS and protocol["samples_per_task"] == 5, "seed schedule drift")
    _require(protocol["policies"]["automatic_retry"] is False, "retry policy drift")
    _require(protocol["policies"]["overwrite_existing_output"] is False, "overwrite policy drift")
    separator = v0_manifest["separator"]
    _require(separator["exact_text_utf8"] == PROMPT_SEPARATOR, "fixed separator text drift")
    _require(separator["sha256"] == PROMPT_SEPARATOR_SHA256, "fixed separator hash drift")
    return {
        "source_hashes": source_hashes,
        "expansion": expansion,
        "task_ids": task_ids,
        "candidate_text": candidate_text,
        "generation_parameters": generation,
        "protocol_sha256": source_hashes["generation_protocol_v1.json"],
        "zero_overlap": {
            role: sum(
                key in expansion_keys
                for key, row in frozen_by_key.items()
                if row["proposed_role"] == role
            )
            for role in sorted(forbidden_roles)
        },
    }


def planned_cell_id(run_id: str, treatment_id: str, task_id: str, seed: int) -> str:
    material = (
        f"milestone_2e|{run_id}|{treatment_id}|{task_id}|{seed}|{MODEL_DIGEST}|"
        f"{CANDIDATE_SHA256 if treatment_id == CA_TREATMENT_ID else 'no_scaffold'}"
    )
    return sha256_text(material)


def _cells(run_id: str, treatment_id: str, task_ids: list[str]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for task_index, task_id in enumerate(task_ids):
        for sample_index, seed in enumerate(SEEDS):
            cells.append(
                {
                    "cell_index": len(cells) + 1,
                    "task_index": task_index,
                    "task_id": task_id,
                    "seed": seed,
                    "sample_index": sample_index,
                    "paired_identity": f"{task_id}|seed={seed}",
                    "planned_cell_id": planned_cell_id(
                        run_id, treatment_id, task_id, seed
                    ),
                    "attempt_count": 1,
                }
            )
    _require(len(cells) == CELLS_PER_TREATMENT, "treatment cell count must be 200")
    _require(
        len({(cell["task_id"], cell["seed"]) for cell in cells})
        == CELLS_PER_TREATMENT,
        "treatment cells are not unique",
    )
    return cells


def build_generation_plan(
    inputs: dict[str, Any], *, treatment_id: str
) -> dict[str, Any]:
    is_candidate = treatment_id == CA_TREATMENT_ID
    _require(treatment_id in {P0_TREATMENT_ID, CA_TREATMENT_ID}, "unknown treatment")
    run_id = CA_RUN_ID if is_candidate else P0_RUN_ID
    physical = CA_PHYSICAL if is_candidate else P0_PHYSICAL
    return {
        "plan_version": "mbpp_candidate_a_expansion_prospective_v1",
        "status": "frozen_not_executed",
        "run_id": run_id,
        "logical_run_id": run_id,
        "physical_storage_directory": physical.as_posix(),
        "journal_directory_name": JOURNAL_DIRECTORY,
        "dataset": DATASET,
        "dataset_version": DATASET_VERSION,
        "dataset_hash": DATASET_HASH,
        "source_development_overlay_sha256": inputs["source_hashes"][
            "development_expansion_manifest.json"
        ],
        "selection_policy": "Milestone 2D expansion_development only",
        "development_layer": "expansion_development",
        "excludes_discovery_development": True,
        "forbidden_role_overlap": 0,
        "task_count": TASK_COUNT,
        "task_ids": inputs["task_ids"],
        "samples_per_task": len(SEEDS),
        "seeds": SEEDS,
        "expected_cells": CELLS_PER_TREATMENT,
        "cells": _cells(run_id, treatment_id, inputs["task_ids"]),
        "treatment_id": treatment_id,
        "treatment_label": (
            "Candidate A: official prompt + fixed separator + exact candidate text"
            if is_candidate
            else "P0: official prompt only; no Scaffold"
        ),
        "prompt_composition_order": (
            ["official_prompt_verbatim", "fixed_separator", "candidate_a_exact_text"]
            if is_candidate
            else ["official_prompt_verbatim"]
        ),
        "scaffold": is_candidate,
        "candidate_id": CANDIDATE_ID if is_candidate else None,
        "candidate_status": CANDIDATE_STATUS if is_candidate else None,
        "candidate_exact_text_utf8": inputs["candidate_text"] if is_candidate else None,
        "candidate_exact_text_sha256": CANDIDATE_SHA256 if is_candidate else None,
        "separator_exact_text_utf8": PROMPT_SEPARATOR if is_candidate else None,
        "separator_sha256": PROMPT_SEPARATOR_SHA256 if is_candidate else None,
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "quantization": QUANTIZATION,
        "generation_parameters": inputs["generation_parameters"],
        "generation_protocol_sha256": inputs["protocol_sha256"],
        "ollama_request_timeout_seconds": TIMEOUT_SECONDS,
        "attempts_per_cell": 1,
        "retry": False,
        "resume": False,
        "selective_retry": False,
        "overwrite": False,
        "healer": False,
        "evaluator_feedback_to_model": False,
        "accounts": ["observed", "pipeline_corrected"],
        "pipeline_correction_spec": "agent_tools.finals_rebuild.extraction.extract_code",
        "pipeline_correction_spec_commit": "c5094bb7",
        "pipeline_correction_is_healer": False,
        "itt_policy": {
            "transport_complete_protocol_violations_included": True,
            "reasoning_leakage_counted_separately": True,
            "thinking_content_silently_removed": False,
            "regenerate_on_protocol_violation": False,
        },
    }


def build_promotion_gates() -> dict[str, Any]:
    return {
        "manifest_version": "candidate_a_expansion_promotion_gates_v1",
        "status": "prospectively_frozen_before_generation",
        "candidate_status": CANDIDATE_STATUS,
        "analysis_population": "all 200 paired Candidate-A/P0 expansion identities under ITT",
        "format_gate": {
            "all_required": True,
            "strict_python_only_compliance_rate_min": 0.90,
            "code_fence_rate_max": 0.05,
            "extra_text_rate_max": 0.05,
            "pipeline_extraction_success_rate_min": 0.95,
        },
        "pipeline_correctness_safety_gate": {
            "all_required": True,
            "candidate_pipeline_pass_count_gte_paired_p0": True,
            "paired_rescues_gte_paired_regressions": True,
            "all_regressions_fully_disclosed": True,
        },
        "protocol_gate": {
            "all_required": True,
            "reasoning_leakage_reported_separately": True,
            "silent_thinking_content_deletion_forbidden": True,
            "transport_complete_protocol_violations_in_itt": True,
            "regeneration_for_protocol_violation_forbidden": True,
        },
        "claim_rule": {
            "pipeline_correctness_improvement": {
                "paired_rescues_gt_paired_regressions": True,
                "exact_mcnemar_two_sided_p_lt": 0.05,
            },
            "format_and_safety_only_claim": (
                "improved direct evaluability and Pipeline-corrected non-inferiority to paired P0 only"
            ),
            "safety_gate_failure_consequence": (
                "Candidate A must not be promoted to official Scaffold v1"
            ),
        },
        "failure_governance": {
            "modify_candidate_a_and_rerun_same_40_forbidden": True,
            "mix_candidate_b_into_this_result_forbidden": True,
            "next_protocol_must_use_remaining_unactivated_historical_development_tasks": True,
        },
    }


def build_paired_analysis_plan(
    p0_plan: dict[str, Any], candidate_plan: dict[str, Any]
) -> dict[str, Any]:
    p0_keys = [(cell["task_id"], cell["seed"]) for cell in p0_plan["cells"]]
    ca_keys = [(cell["task_id"], cell["seed"]) for cell in candidate_plan["cells"]]
    _require(p0_keys == ca_keys and len(set(p0_keys)) == 200, "paired identity mismatch")
    return {
        "analysis_plan_version": "candidate_a_expansion_paired_prospective_v1",
        "status": "prospectively_frozen_not_executed",
        "analysis_id": PAIRED_ANALYSIS_ID,
        "physical_output_directory": PAIRED_PHYSICAL.as_posix(),
        "p0_run_id": P0_RUN_ID,
        "candidate_run_id": CA_RUN_ID,
        "pairing_key": ["task_id", "seed"],
        "paired_tasks": TASK_COUNT,
        "paired_identities": CELLS_PER_TREATMENT,
        "planned_generation_cells_total": TOTAL_PLANNED_CELLS,
        "primary_correctness_account": "pipeline_corrected",
        "secondary_account": "observed",
        "format_metrics": [
            "strict_python_only_compliance_rate",
            "code_fence_rate",
            "extra_text_rate",
            "pipeline_extraction_success_rate",
        ],
        "paired_transitions": [
            "fail_to_fail",
            "fail_to_pass",
            "pass_to_fail",
            "pass_to_pass",
        ],
        "statistical_test": {
            "name": "exact two-sided McNemar conditional binomial test",
            "alpha": 0.05,
            "discordant_successes": "paired rescues (P0 fail, Candidate A pass)",
            "discordant_failures": "paired regressions (P0 pass, Candidate A fail)",
            "zero_discordant_p_value": 1.0,
        },
        "itt": True,
        "reasoning_leakage_separate_metric": True,
        "all_regression_rows_required": True,
        "unknown_evaluator_failure_must_not_be_guessed": True,
        "promotion_gate_manifest": "promotion_gate_manifest.json",
    }


def _planned_paths(run_root: PureWindowsPath, cells: list[dict[str, Any]]) -> list[str]:
    paths = [
        run_root / "generation_plan.json",
        *(run_root / JOURNAL_DIRECTORY / f"{cell['planned_cell_id']}.json" for cell in cells),
        run_root / "raw_generations.jsonl",
        run_root / "pipeline_corrected.jsonl",
        run_root / "evaluation_results.csv",
        run_root / "evaluation_summary.md",
    ]
    temp_dirs = sorted({path.parent for path in paths}, key=str)
    paths.extend(directory / ".tmp-xxxxxxxxxxxxxxxx.tmp" for directory in temp_dirs)
    return [str(path) for path in paths]


def build_storage_mapping(
    p0_plan: dict[str, Any], candidate_plan: dict[str, Any]
) -> dict[str, Any]:
    windows_root = PureWindowsPath(WINDOWS_REPO_PREFIX)
    mappings = []
    for plan, relative in ((p0_plan, P0_PHYSICAL), (candidate_plan, CA_PHYSICAL)):
        paths = _planned_paths(
            windows_root / PureWindowsPath(relative.as_posix()), plan["cells"]
        )
        longest = max(paths, key=len)
        _require(len(longest) <= WINDOWS_PATH_BUDGET, "Windows path budget exceeded")
        mappings.append(
            {
                "logical_run_id": plan["run_id"],
                "physical_storage_directory": relative.as_posix(),
                "journal_directory_name": JOURNAL_DIRECTORY,
                "checked_path_count": len(paths),
                "longest_windows_path": longest,
                "longest_windows_path_length": len(longest),
                "within_budget": True,
            }
        )
    paired_path = str(
        windows_root / PureWindowsPath(PAIRED_PHYSICAL.as_posix()) / "paired_analysis_manifest.json"
    )
    _require(len(paired_path) <= WINDOWS_PATH_BUDGET, "paired analysis path budget exceeded")
    return {
        "mapping_version": "candidate_a_expansion_short_path_mapping_v1",
        "windows_repo_prefix": WINDOWS_REPO_PREFIX,
        "windows_path_budget_chars": WINDOWS_PATH_BUDGET,
        "requires_windows_long_path_registry_change": False,
        "run_directories_created_by_freezer": False,
        "runs": mappings,
        "paired_analysis": {
            "analysis_id": PAIRED_ANALYSIS_ID,
            "physical_output_directory": PAIRED_PHYSICAL.as_posix(),
            "preflight_path": paired_path,
            "preflight_path_length": len(paired_path),
            "within_budget": True,
        },
    }


def render_operator_guide(
    p0_plan: dict[str, Any], candidate_plan: dict[str, Any]
) -> bytes:
    lines = [
        "# MBPP+ Candidate A expansion prospective protocol 操作指南（Milestone 2E）",
        "",
        "## 現在的治理狀態",
        "",
        "本文件凍結未來正式命令；Milestone 2E 不得執行以下 generation、EvalPlus 或 paired analysis 命令。Candidate A 狀態為 `frozen_experimental_candidate_not_official_v1`，不是正式 Scaffold v1。不得 retry、resume、selective retry、overwrite 或建置 Healer。",
        "",
        f"- P0 logical run：`{P0_RUN_ID}`；physical：`{P0_PHYSICAL.as_posix()}`。",
        f"- Candidate A logical run：`{CA_RUN_ID}`；physical：`{CA_PHYSICAL.as_posix()}`。",
        f"- 每組：40 tasks × 5 seeds = {CELLS_PER_TREATMENT} cells；合計 {TOTAL_PLANNED_CELLS} cells。",
        f"- Candidate A SHA-256：`{CANDIDATE_SHA256}`。",
        "- Observed 與 Pipeline-corrected 分帳；Pipeline correction 不是 Healer。",
        "- Transport-complete 的 protocol violation 仍納入 ITT；不得靜默移除 thinking、不得因此重生。",
        "",
        "## Windows 生成指令（未執行）",
        "",
        "先執行唯讀 preflight：",
        "",
        "```powershell",
        "py -3.12 -B .\\scripts\\run_mbpp_candidate_a_expansion.py preflight",
        "```",
        "",
        "P0：",
        "",
        "```powershell",
        f"py -3.12 -B .\\scripts\\run_mbpp_candidate_a_expansion.py generate --treatment p0 --run-id {P0_RUN_ID} --base-url http://127.0.0.1:11434 --timeout-seconds 600",
        "```",
        "",
        "Candidate A（只能在 P0 完成後依預註冊順序執行）：",
        "",
        "```powershell",
        f"py -3.12 -B .\\scripts\\run_mbpp_candidate_a_expansion.py generate --treatment candidate_a --run-id {CA_RUN_ID} --base-url http://127.0.0.1:11434 --timeout-seconds 600",
        "```",
        "",
        "每格 exactly one attempt。若不完整，停止並依事故治理處理；不得 retry 或 selective retry。",
        "",
        "## WSL EvalPlus 評估指令（未執行）",
        "",
        "```powershell",
        "wsl -d Ubuntu",
        "```",
        "",
        "```bash",
        "cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2",
        "",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment p0 --run-id {P0_RUN_ID} --parallel 4",
        "",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment candidate_a --run-id {CA_RUN_ID} --parallel 4",
        "```",
        "",
        "兩組各自必須先有完整200個 raw 與 Pipeline identities，且 evaluation outputs 不存在，才能評估。",
        "",
        "## Paired analysis 指令（未執行）",
        "",
        "```bash",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/analyze_mbpp_candidate_a_expansion.py --p0-run-id {P0_RUN_ID} --candidate-run-id {CA_RUN_ID}",
        "```",
        "",
        "分析必須揭露全部 Pipeline regressions、獨立統計 reasoning leakage，並套用預先凍結的 promotion gates。若 Candidate A 失敗，不得修改後重跑同40題，也不得混入 Candidate B。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def frozen_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    repo_root = repo_root.resolve()
    inputs = _load_inputs(repo_root)
    p0_plan = build_generation_plan(inputs, treatment_id=P0_TREATMENT_ID)
    candidate_plan = build_generation_plan(inputs, treatment_id=CA_TREATMENT_ID)
    _require(
        [(cell["task_id"], cell["seed"]) for cell in p0_plan["cells"]]
        == [(cell["task_id"], cell["seed"]) for cell in candidate_plan["cells"]],
        "treatment schedules are not paired",
    )
    gates = build_promotion_gates()
    analysis = build_paired_analysis_plan(p0_plan, candidate_plan)
    storage = build_storage_mapping(p0_plan, candidate_plan)
    outputs: dict[Path, bytes] = {
        Path("p0_expansion_generation_plan.json"): render_json(p0_plan),
        Path("candidate_a_expansion_generation_plan.json"): render_json(candidate_plan),
        Path("paired_prospective_analysis_plan.json"): render_json(analysis),
        Path("promotion_gate_manifest.json"): render_json(gates),
        Path("storage_mapping.json"): render_json(storage),
        Path("operator_guide_zh.md"): render_operator_guide(p0_plan, candidate_plan),
    }
    manifest = {
        "manifest_version": "milestone_2e_candidate_a_expansion_protocol_v1",
        "status": "prospectively_frozen_not_executed",
        "starting_head": STARTING_HEAD,
        "scope": "Milestone 2D expansion_development only",
        "treatment_execution_order": [P0_RUN_ID, CA_RUN_ID],
        "source_artifacts": {
            label: {"path": SOURCE_PATHS[label].as_posix(), "sha256": digest}
            for label, digest in sorted(inputs["source_hashes"].items())
        },
        "run_ids": {"p0": P0_RUN_ID, "candidate_a": CA_RUN_ID},
        "physical_paths": {
            "p0": P0_PHYSICAL.as_posix(),
            "candidate_a": CA_PHYSICAL.as_posix(),
            "paired_analysis": PAIRED_PHYSICAL.as_posix(),
        },
        "counts": {
            "expansion_tasks": TASK_COUNT,
            "seeds_per_task": len(SEEDS),
            "p0_cells": CELLS_PER_TREATMENT,
            "candidate_a_cells": CELLS_PER_TREATMENT,
            "total_planned_cells": TOTAL_PLANNED_CELLS,
            "paired_identities": CELLS_PER_TREATMENT,
        },
        "zero_overlap": {
            **inputs["zero_overlap"],
            "verified_total_forbidden_overlap": sum(inputs["zero_overlap"].values()),
            "discovery_development": 0,
        },
        "candidate_a": {
            "candidate_id": CANDIDATE_ID,
            "status": CANDIDATE_STATUS,
            "exact_text_sha256": CANDIDATE_SHA256,
            "separator_sha256": PROMPT_SEPARATOR_SHA256,
            "official_v1": False,
        },
        "model_protocol": {
            "model": MODEL,
            "digest": MODEL_DIGEST,
            "quantization": QUANTIZATION,
            "generation_parameters": inputs["generation_parameters"],
            "timeout_seconds": TIMEOUT_SECONDS,
            "attempts_per_cell": 1,
            "retry": False,
            "resume": False,
            "selective_retry": False,
            "overwrite": False,
            "healer": False,
            "pipeline_correction_is_healer": False,
        },
        "promotion_gates_sha256": sha256_bytes(outputs[Path("promotion_gate_manifest.json")]),
        "storage_preflight": storage,
        "prohibited_actions_attestation": {
            "model_calls": 0,
            "evalplus_executions": 0,
            "run_directories_created": False,
            "healer_built": False,
            "candidate_a_promoted_to_official_v1": False,
            "formal_commands_executed": False,
        },
        "execution_components": {
            "freezer": "scripts/freeze_mbpp_candidate_a_expansion_protocol.py",
            "generation_evaluation_driver": "scripts/run_mbpp_candidate_a_expansion.py",
            "paired_analysis_driver": "scripts/analyze_mbpp_candidate_a_expansion.py",
            "targeted_tests": "tests/finals_rebuild/test_mbpp_candidate_a_expansion_protocol.py",
        },
        "outputs": {
            path.as_posix(): {"sha256": sha256_bytes(content), "size_bytes": len(content)}
            for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        },
    }
    outputs[Path("milestone_2e_manifest.json")] = render_json(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    for relative, content in frozen_outputs(repo_root).items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing output drift/overwrite: {relative}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_outputs(args.repo_root)
    print(
        json.dumps(
            {
                "status": "prospectively_frozen_not_executed",
                "p0_cells": CELLS_PER_TREATMENT,
                "candidate_a_cells": CELLS_PER_TREATMENT,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
