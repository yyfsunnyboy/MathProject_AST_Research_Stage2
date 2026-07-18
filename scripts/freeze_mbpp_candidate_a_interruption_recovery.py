#!/usr/bin/env python3
"""Freeze Candidate-A r001 interruption incident and full r002 replacement protocol."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path, PureWindowsPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_mbpp_candidate_a_expansion_protocol as original  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_a_expansion_recovery_r002"
)
ORIGINAL_PROTOCOL_DIR = original.OUTPUT_RELATIVE
ORIGINAL_P0_PLAN = ORIGINAL_PROTOCOL_DIR / "p0_expansion_generation_plan.json"
ORIGINAL_CA_PLAN = ORIGINAL_PROTOCOL_DIR / "candidate_a_expansion_generation_plan.json"
ORIGINAL_ANALYSIS_PLAN = ORIGINAL_PROTOCOL_DIR / "paired_prospective_analysis_plan.json"
ORIGINAL_GATES = ORIGINAL_PROTOCOL_DIR / "promotion_gate_manifest.json"
ORIGINAL_STORAGE = ORIGINAL_PROTOCOL_DIR / "storage_mapping.json"
ORIGINAL_GUIDE = ORIGINAL_PROTOCOL_DIR / "operator_guide_zh.md"
ORIGINAL_MANIFEST = ORIGINAL_PROTOCOL_DIR / "milestone_2e_manifest.json"

P0_RUN_RELATIVE = Path("artifacts/pbd/mbpp_e40/p0/r001")
CA_R001_RELATIVE = Path("artifacts/pbd/mbpp_e40/ca/r001")
CA_R002_RELATIVE = Path("artifacts/pbd/mbpp_e40/ca/r002")
PAIRED_R002_RELATIVE = Path("artifacts/pbd/mbpp_e40/pa/r002")
P0_RUN_ID = original.P0_RUN_ID
CA_R001_RUN_ID = original.CA_RUN_ID
CA_R002_RUN_ID = "mbpp_q35_9b_ca_exp40_r002"
PAIRED_R002_ID = "mbpp_q35_9b_ca_exp40_paired_r002"
INCIDENT_STATUS = "permanently_invalidated_operator_interrupt"
STARTING_HEAD = "ac6a8fd134dc21ea25c06226a3caffa3ca85c2e2"

ORIGINAL_SOURCE_PATHS = {
    "p0_expansion_generation_plan.json": ORIGINAL_P0_PLAN,
    "candidate_a_expansion_generation_plan.json": ORIGINAL_CA_PLAN,
    "paired_prospective_analysis_plan.json": ORIGINAL_ANALYSIS_PLAN,
    "promotion_gate_manifest.json": ORIGINAL_GATES,
    "storage_mapping.json": ORIGINAL_STORAGE,
    "operator_guide_zh.md": ORIGINAL_GUIDE,
    "milestone_2e_manifest.json": ORIGINAL_MANIFEST,
}
EXPECTED_ORIGINAL_SOURCE_HASHES = {
    "p0_expansion_generation_plan.json": "cee8e9908bfb9759189b290e8b3f13a7609e3ec80395585f07b9c0425f255531",
    "candidate_a_expansion_generation_plan.json": "883c9ad85725953e32a611a5cc6b6730d38c7b71c28c01206f67d3f9e859d12f",
    "paired_prospective_analysis_plan.json": "3ac7cb6a7b75503f98e48b3c88888c87d864f58f15f69a4ca934ac41d15221e5",
    "promotion_gate_manifest.json": "07f6550c140c9063da0551909f979638d5306adbfb77ff7c4ffc372e94662d84",
    "storage_mapping.json": "345d025de909e607330417e9fb790632301fbd1dc4f7090f11beac5707c5593e",
    "operator_guide_zh.md": "b303e2052ffc81eb9ff9fba888436ecd46f0c1da2ccd6242aa21059f2874dce9",
    "milestone_2e_manifest.json": "f9f1fcdee72a5fdffc613b84912b52aab3b03add3ca555d192621efa04a09a2c",
}

CA_R001_EXPECTED_FILES = {
    "generation_plan.json": {
        "sha256": "883c9ad85725953e32a611a5cc6b6730d38c7b71c28c01206f67d3f9e859d12f",
        "size_bytes": 62707,
    },
    "j/151d77fae8ffac7c760a91767c4f6c67bd039776bd906879ffcd099a9015f8be.json": {
        "sha256": "30931786181bb62ba7f47e940a1ac478803d9df10feb2127fc6ccbef9b639545",
        "size_bytes": 22154,
    },
    "j/29fc8cf9ec16041ef35778656dbc6a7d531817363e19c04e856343a5d29796b6.json": {
        "sha256": "5e0c2dd5d7ff718437d102c0832ef1328eca615ecdfc57cb9bceb9c5d6e9486f",
        "size_bytes": 3866,
    },
}
P0_EXPECTED_FILES = {
    "generation_plan.json": "cee8e9908bfb9759189b290e8b3f13a7609e3ec80395585f07b9c0425f255531",
    "raw_generations.jsonl": "2e89154a4723f9b3a95a7605250498079065e65708bfd1c6ede235a0f7e19596",
    "pipeline_corrected.jsonl": "7cc419aaa8587e0648e9b198270c2efd388fccd67c8331e0629b0374a8fcf402",
}


class InterruptionRecoveryError(RuntimeError):
    """Raised before writes when incident evidence or recovery invariants drift."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InterruptionRecoveryError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def render_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _validate_original_protocol(repo_root: Path) -> dict[str, str]:
    hashes = {
        label: sha256_bytes((repo_root / path).read_bytes())
        for label, path in ORIGINAL_SOURCE_PATHS.items()
    }
    _require(hashes == EXPECTED_ORIGINAL_SOURCE_HASHES, "original Milestone 2E artifact drift")
    return hashes


def inspect_incident(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    incident_dir = repo_root / CA_R001_RELATIVE
    _require(incident_dir.is_dir(), "Candidate A r001 incident directory missing")
    actual_files = {
        path.relative_to(incident_dir).as_posix(): path
        for path in incident_dir.rglob("*")
        if path.is_file()
    }
    _require(set(actual_files) == set(CA_R001_EXPECTED_FILES), "Candidate A r001 file set drift")
    artifacts = []
    for relative, expected in CA_R001_EXPECTED_FILES.items():
        path = actual_files[relative]
        metadata = {
            "path": (CA_R001_RELATIVE / relative).as_posix(),
            "sha256": sha256_bytes(path.read_bytes()),
            "size_bytes": path.stat().st_size,
        }
        _require(metadata["sha256"] == expected["sha256"], f"r001 hash drift: {relative}")
        _require(metadata["size_bytes"] == expected["size_bytes"], f"r001 size drift: {relative}")
        artifacts.append(metadata)

    plan = json.loads((incident_dir / "generation_plan.json").read_text(encoding="utf-8"))
    _require(plan["run_id"] == CA_R001_RUN_ID and len(plan["cells"]) == 200, "r001 plan drift")
    planned_by_id = {cell["planned_cell_id"]: cell for cell in plan["cells"]}
    journal_records = []
    for relative in sorted(name for name in actual_files if name.startswith("j/")):
        path = actual_files[relative]
        record = json.loads(path.read_text(encoding="utf-8"))
        generation_id = record.get("generation_id")
        _require(generation_id in planned_by_id, "r001 journal generation ID absent from plan")
        cell = planned_by_id[generation_id]
        _require(
            record.get("task_id") == cell["task_id"] and record.get("seed") == cell["seed"],
            "r001 journal task/seed mismatch",
        )
        raw = record.get("raw_response")
        body_text = record.get("raw_http_response_body")
        _require(isinstance(raw, str) and isinstance(body_text, str), "r001 response evidence missing")
        body = json.loads(body_text)
        message = body.get("message") if isinstance(body.get("message"), dict) else {}
        calculated = sha256_text(raw)
        response_fully_saved = (
            body.get("done") is True
            and message.get("content") == raw
            and calculated == record.get("raw_response_sha256")
        )
        _require(response_fully_saved, "r001 saved response integrity failure")
        journal_records.append(
            {
                "journal_path": (CA_R001_RELATIVE / relative).as_posix(),
                "journal_file_sha256": sha256_bytes(path.read_bytes()),
                "journal_file_size_bytes": path.stat().st_size,
                "task_id": record["task_id"],
                "seed": record["seed"],
                "generation_id": generation_id,
                "planned_cell_id": record.get("planned_cell_id"),
                "journal_status_field": record.get("status"),
                "derived_status": "complete_saved_first_attempt_incident_evidence_only",
                "transport_complete": record.get("transport_complete") is True,
                "model_generation_complete": record.get("model_generation_complete") is True,
                "generation_complete": record.get("generation_complete") is True,
                "protocol_compliant": record.get("protocol_compliant") is True,
                "protocol_violations": record.get("protocol_violations", []),
                "response_fully_saved": response_fully_saved,
                "raw_response_size_bytes": len(raw.encode("utf-8")),
                "raw_response_sha256": calculated,
                "model_done": body.get("done"),
                "model_done_reason": body.get("done_reason"),
                "length_terminated": body.get("done_reason") == "length",
                "formal_analysis_eligible": False,
            }
        )
    _require(len(journal_records) == 2, "r001 must contain exactly two incident journals")
    return {
        "incident_version": "candidate_a_operator_interrupt_r001_v1",
        "logical_run_id": CA_R001_RUN_ID,
        "physical_storage_directory": CA_R001_RELATIVE.as_posix(),
        "status": INCIDENT_STATUS,
        "incident_type": "operator_ctrl_c_interrupt_during_sequential_generation",
        "journal_count": 2,
        "planned_cells": 200,
        "valid_generation_for_formal_analysis": 0,
        "journal_records": journal_records,
        "existing_artifacts": artifacts,
        "unpersisted_in_flight_request": {
            "possible": True,
            "known_to_exist": False,
            "recoverable_from_disk": False,
            "reason": (
                "Ctrl+C may have occurred during a later run_attempt or after a response but before "
                "journal persistence; the disk evidence cannot prove or exclude such a request."
            ),
            "formal_cell_credit": 0,
        },
        "reuse_policy": {
            "delete": False,
            "modify": False,
            "move": False,
            "resume": False,
            "retry": False,
            "selective_retry": False,
            "merge_into_r002": False,
            "use_in_formal_analysis": False,
        },
        "evidence_only_statement": (
            "The two complete saved journals are incident evidence only and contribute zero "
            "formal-generation cells."
        ),
    }


def inspect_p0(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    run_dir = repo_root / P0_RUN_RELATIVE
    _require(run_dir.is_dir(), "valid P0 r001 directory missing")
    hashes = {
        name: sha256_bytes((run_dir / name).read_bytes()) for name in P0_EXPECTED_FILES
    }
    _require(hashes == P0_EXPECTED_FILES, "P0 r001 artifact hash drift")
    plan = json.loads((run_dir / "generation_plan.json").read_text(encoding="utf-8"))
    raw = _read_jsonl(run_dir / "raw_generations.jsonl")
    pipeline = _read_jsonl(run_dir / "pipeline_corrected.jsonl")
    journals = list((run_dir / "j").glob("*.json"))
    planned_keys = {(cell["task_id"], int(cell["seed"])) for cell in plan["cells"]}
    raw_keys = {(row["task_id"], int(row["seed"])) for row in raw}
    _require(plan["run_id"] == P0_RUN_ID, "P0 run ID drift")
    _require(len(plan["cells"]) == len(raw) == len(pipeline) == len(journals) == 200, "P0 completeness drift")
    _require(planned_keys == raw_keys and len(raw_keys) == 200, "P0 identity drift")
    _require(sum(row.get("retry_count", -1) for row in raw) == 0, "P0 retry count drift")
    _require(all(row.get("generation_complete") is True for row in raw), "P0 incomplete generation")
    _require(all(row.get("protocol_compliant") is True for row in raw), "P0 protocol violation drift")
    return {
        "logical_run_id": P0_RUN_ID,
        "physical_storage_directory": P0_RUN_RELATIVE.as_posix(),
        "status": "valid_complete_generation_do_not_rerun",
        "planned_cells": 200,
        "raw_generation_records": 200,
        "pipeline_records": 200,
        "journal_records": 200,
        "unique_task_seed_identities": 200,
        "retry_count_sum": 0,
        "protocol_violation_count": 0,
        "generation_complete_count": 200,
        "artifact_sha256": hashes,
        "rerun_allowed": False,
    }


def replacement_cell_id(task_id: str, seed: int) -> str:
    material = (
        f"milestone_2e_r|{CA_R002_RUN_ID}|{original.CA_TREATMENT_ID}|{task_id}|{seed}|"
        f"{original.MODEL_DIGEST}|{original.CANDIDATE_SHA256}"
    )
    return sha256_text(material)


def build_r002_plan(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    source = json.loads((repo_root / ORIGINAL_CA_PLAN).read_text(encoding="utf-8"))
    plan = copy.deepcopy(source)
    plan.update(
        {
            "plan_version": "mbpp_candidate_a_expansion_interruption_recovery_r002_v1",
            "status": "frozen_recovery_replacement_not_executed",
            "run_id": CA_R002_RUN_ID,
            "logical_run_id": CA_R002_RUN_ID,
            "physical_storage_directory": CA_R002_RELATIVE.as_posix(),
            "invalidated_predecessor_run_id": CA_R001_RUN_ID,
            "invalidated_predecessor_status": INCIDENT_STATUS,
            "predecessor_cells_reused": 0,
            "full_regeneration_required": True,
        }
    )
    for cell in plan["cells"]:
        new_id = replacement_cell_id(cell["task_id"], int(cell["seed"]))
        cell["planned_cell_id"] = new_id
        cell["attempt_count"] = 1
    _require(len(plan["cells"]) == 200, "r002 must contain 200 cells")
    _require(len({(cell["task_id"], cell["seed"]) for cell in plan["cells"]}) == 200, "r002 identity drift")
    _require(len({cell["planned_cell_id"] for cell in plan["cells"]}) == 200, "r002 cell ID collision")
    _require(plan["candidate_exact_text_sha256"] == original.CANDIDATE_SHA256, "Candidate A hash drift")
    _require(plan["model_digest"] == original.MODEL_DIGEST, "model digest drift")
    _require(plan["generation_parameters"]["thinking"] is False, "think flag drift")
    _require(plan["ollama_request_timeout_seconds"] == 600.0, "timeout drift")
    _require(not any(plan[key] for key in ("retry", "resume", "selective_retry", "overwrite", "healer")), "r002 forbidden policy")
    return plan


def build_paired_plan(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    source = json.loads((repo_root / ORIGINAL_ANALYSIS_PLAN).read_text(encoding="utf-8"))
    source.update(
        {
            "analysis_plan_version": "candidate_a_expansion_paired_recovery_r002_v1",
            "status": "prospectively_refrozen_not_executed",
            "analysis_id": PAIRED_R002_ID,
            "physical_output_directory": PAIRED_R002_RELATIVE.as_posix(),
            "p0_run_id": P0_RUN_ID,
            "candidate_run_id": CA_R002_RUN_ID,
            "invalidated_candidate_run_id": CA_R001_RUN_ID,
            "invalidated_candidate_cells_included": 0,
        }
    )
    return source


def _planned_paths(run_relative: Path, plan: dict[str, Any]) -> list[str]:
    root = PureWindowsPath(original.WINDOWS_REPO_PREFIX) / PureWindowsPath(run_relative.as_posix())
    finals = [
        root / "generation_plan.json",
        *(root / "j" / f"{cell['planned_cell_id']}.json" for cell in plan["cells"]),
        root / "raw_generations.jsonl",
        root / "pipeline_corrected.jsonl",
        root / "evaluation_results.csv",
        root / "evaluation_summary.md",
    ]
    temp_dirs = sorted({path.parent for path in finals}, key=str)
    finals.extend(directory / ".tmp-xxxxxxxxxxxxxxxx.tmp" for directory in temp_dirs)
    return [str(path) for path in finals]


def build_storage_mapping(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    p0 = json.loads((repo_root / ORIGINAL_P0_PLAN).read_text(encoding="utf-8"))
    r002 = build_r002_plan(repo_root)
    mappings = []
    for run_id, relative, plan, status in (
        (P0_RUN_ID, P0_RUN_RELATIVE, p0, "existing_valid_do_not_rerun"),
        (CA_R002_RUN_ID, CA_R002_RELATIVE, r002, "planned_not_created"),
    ):
        paths = _planned_paths(relative, plan)
        longest = max(paths, key=len)
        _require(len(longest) <= original.WINDOWS_PATH_BUDGET, "recovery path budget exceeded")
        mappings.append(
            {
                "logical_run_id": run_id,
                "physical_storage_directory": relative.as_posix(),
                "status": status,
                "journal_directory_name": "j",
                "checked_path_count": len(paths),
                "longest_windows_path": longest,
                "longest_windows_path_length": len(longest),
                "within_budget": True,
            }
        )
    paired_path = str(
        PureWindowsPath(original.WINDOWS_REPO_PREFIX)
        / PureWindowsPath(PAIRED_R002_RELATIVE.as_posix())
        / "paired_analysis_manifest.json"
    )
    _require(len(paired_path) <= original.WINDOWS_PATH_BUDGET, "paired path budget exceeded")
    return {
        "mapping_version": "candidate_a_interruption_recovery_short_path_v1",
        "windows_path_budget_chars": original.WINDOWS_PATH_BUDGET,
        "requires_windows_long_path_registry_change": False,
        "invalidated_run": {
            "logical_run_id": CA_R001_RUN_ID,
            "physical_storage_directory": CA_R001_RELATIVE.as_posix(),
            "status": INCIDENT_STATUS,
            "reuse_allowed": False,
        },
        "runs": mappings,
        "paired_analysis": {
            "analysis_id": PAIRED_R002_ID,
            "physical_output_directory": PAIRED_R002_RELATIVE.as_posix(),
            "preflight_path": paired_path,
            "preflight_path_length": len(paired_path),
            "within_budget": True,
        },
        "r002_directory_created_by_freezer": False,
    }


def render_operator_guide() -> bytes:
    lines = [
        "# Candidate A operator interruption recovery 操作指南（Milestone 2E-R）",
        "",
        "## 事故治理",
        "",
        f"Candidate A `{CA_R001_RUN_ID}` 因 operator Ctrl+C 標記為 `{INCIDENT_STATUS}`。r001 的2個journals只作事故證據，formal valid generation=0；不得刪除、修改、移動、resume、retry、selective retry、補跑、合併至r002或納入paired analysis。可能存在未持久化的in-flight request，但磁碟無法證明或恢復，formal credit=0。",
        "",
        f"P0 `{P0_RUN_ID}` 已完整200/200、retry=0、protocol violations=0，保持有效且不得重跑。Candidate A必須以全新 `{CA_R002_RUN_ID}` 從第一格完整重新生成200格，不得沿用r001 response。Candidate A仍是 `{original.CANDIDATE_STATUS}`，不是正式v1。",
        "",
        "Milestone 2E-R 不得執行以下正式命令；本輪不呼叫模型、EvalPlus或paired analysis，也不建立r002目錄。",
        "",
        "## Windows 唯讀 preflight（可執行，不呼叫模型）",
        "",
        "```powershell",
        "py -3.12 -B .\\scripts\\run_mbpp_candidate_a_expansion.py preflight",
        "```",
        "",
        "## Windows Candidate A r002 generation（本輪未執行）",
        "",
        "```powershell",
        f"py -3.12 -B .\\scripts\\run_mbpp_candidate_a_expansion.py generate --treatment candidate_a --run-id {CA_R002_RUN_ID} --base-url http://127.0.0.1:11434 --timeout-seconds 600",
        "```",
        "",
        "不得再次執行P0 generation；r002每格exactly one attempt，任何中斷均停止，不得retry/resume。",
        "",
        "## WSL EvalPlus（本輪未執行）",
        "",
        "```bash",
        "cd /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment p0 --run-id {P0_RUN_ID} --parallel 4",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_a_expansion.py evaluate --treatment candidate_a --run-id {CA_R002_RUN_ID} --parallel 4",
        "```",
        "",
        "P0若已評估則不得重跑evaluation；所有evaluation outputs仍遵守overwrite禁止。",
        "",
        "## Paired analysis（本輪未執行）",
        "",
        "```bash",
        f"/home/yehya/.venvs/ast_evalplus/bin/python scripts/analyze_mbpp_candidate_a_expansion.py --p0-run-id {P0_RUN_ID} --candidate-run-id {CA_R002_RUN_ID}",
        "```",
        "",
        "paired analysis只能使用P0 r001完整200格與Candidate A r002完整200格；Candidate A r001貢獻0格。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def frozen_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    repo_root = repo_root.resolve()
    source_hashes = _validate_original_protocol(repo_root)
    incident = inspect_incident(repo_root)
    p0 = inspect_p0(repo_root)
    r002 = build_r002_plan(repo_root)
    paired = build_paired_plan(repo_root)
    storage = build_storage_mapping(repo_root)
    _require(not (repo_root / CA_R002_RELATIVE).exists(), "r002 directory must not exist during freeze")
    _require(not (repo_root / PAIRED_R002_RELATIVE).exists(), "r002 paired directory must not exist during freeze")
    p0_plan = json.loads((repo_root / ORIGINAL_P0_PLAN).read_text(encoding="utf-8"))
    p0_keys = [(cell["task_id"], cell["seed"]) for cell in p0_plan["cells"]]
    r002_keys = [(cell["task_id"], cell["seed"]) for cell in r002["cells"]]
    _require(p0_keys == r002_keys and len(set(p0_keys)) == 200, "recovery pairing mismatch")
    outputs: dict[Path, bytes] = {
        Path("candidate_a_r001_incident_manifest.json"): render_json(incident),
        Path("candidate_a_r002_generation_plan.json"): render_json(r002),
        Path("paired_prospective_analysis_plan_r002.json"): render_json(paired),
        Path("storage_mapping_r002.json"): render_json(storage),
        Path("operator_guide_recovery_zh.md"): render_operator_guide(),
    }
    manifest = {
        "manifest_version": "milestone_2e_r_candidate_a_interruption_recovery_v1",
        "status": "recovery_protocol_frozen_not_executed",
        "starting_head": STARTING_HEAD,
        "incident": {
            "run_id": CA_R001_RUN_ID,
            "status": INCIDENT_STATUS,
            "journal_evidence_count": 2,
            "valid_generation_for_formal_analysis": 0,
            "artifacts_modified_moved_or_deleted": False,
        },
        "valid_p0": p0,
        "replacement": {
            "run_id": CA_R002_RUN_ID,
            "physical_storage_directory": CA_R002_RELATIVE.as_posix(),
            "planned_cells": 200,
            "predecessor_cells_reused": 0,
            "directory_created": False,
        },
        "paired_analysis": {
            "p0_run_id": P0_RUN_ID,
            "candidate_run_id": CA_R002_RUN_ID,
            "paired_identities": 200,
            "candidate_r001_cells_included": 0,
        },
        "invariants_preserved": {
            "candidate_exact_text_sha256": original.CANDIDATE_SHA256,
            "model": original.MODEL,
            "model_digest": original.MODEL_DIGEST,
            "quantization": original.QUANTIZATION,
            "generation_parameters": r002["generation_parameters"],
            "timeout_seconds": 600.0,
            "task_ids_unchanged": r002["task_ids"] == p0_plan["task_ids"],
            "seeds": r002["seeds"],
        },
        "source_protocol_artifacts": {
            label: {"path": ORIGINAL_SOURCE_PATHS[label].as_posix(), "sha256": digest}
            for label, digest in sorted(source_hashes.items())
        },
        "prohibited_actions_attestation": {
            "model_calls": 0,
            "evalplus_executions": 0,
            "paired_analysis_executions": 0,
            "r001_artifacts_modified_moved_or_deleted": False,
            "r001_responses_merged_into_r002": False,
            "r002_directory_created": False,
            "p0_rerun": False,
            "healer_built": False,
        },
        "execution_components": {
            "freezer": "scripts/freeze_mbpp_candidate_a_interruption_recovery.py",
            "generation_evaluation_driver": "scripts/run_mbpp_candidate_a_expansion.py",
            "paired_analysis_driver": "scripts/analyze_mbpp_candidate_a_expansion.py",
            "targeted_tests": "tests/finals_rebuild/test_mbpp_candidate_a_interruption_recovery.py",
        },
        "outputs": {
            path.as_posix(): {"sha256": sha256_bytes(content), "size_bytes": len(content)}
            for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        },
    }
    outputs[Path("milestone_2e_r_manifest.json")] = render_json(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    for relative, content in frozen_outputs(repo_root).items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing recovery output drift: {relative}")
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
                "incident_status": INCIDENT_STATUS,
                "r001_formal_cells": 0,
                "r002_planned_cells": 200,
                "status": "recovery_protocol_frozen_not_executed",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
