#!/usr/bin/env python3
"""Minimal model-parameterized public benchmark H2 replay & readiness runner.

Supports:
- Models: qwen3.5:4b, qwen3.5:9b, qwen3:0.6b
- Datasets: humaneval (164), mbpp (378), all (542)
- 4 ITT conditions: Ab1-Raw, Ab1-H2, Ab2g-Raw, Ab2g-H2
- Fixed extractor (non-modifying code block extractor)
- Frozen H2 quarantine rule with fail-closed SHA256 check
- Reads ONLY full benchmark generation artifacts in runs/<ds_prefix>_<model_key>/
- Zero model calls during replay/audit
- Materializes 2,168 ITT states per model into per-cell journals
- CLI flags: --model, --dataset, --dry-run, --resume, --parallel 1, --output-dir
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID,
    quarantine_module_assert_entrypoint_selftest,
)

RULE_RELATIVE = pathlib.Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py")
EXPECTED_RULE_SHA256 = (
    "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
)

TASK_FILES = {
    "humaneval": pathlib.Path("tasks_humaneval.jsonl"),
    "mbpp": pathlib.Path("tasks_mbpp.jsonl"),
}

EXPECTED_TASK_COUNTS = {"humaneval": 164, "mbpp": 378}
CONDITIONS = ("Ab1-Raw", "Ab1-H2", "Ab2g-Raw", "Ab2g-H2")
ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "expected_digest": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
        "run_dirs": {
            "humaneval": pathlib.Path("runs/he_qwen35_4b"),
            "mbpp": pathlib.Path("runs/mb_qwen35_4b"),
        },
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h2_full_replay_v1"),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "expected_digest": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
        "run_dirs": {
            "humaneval": pathlib.Path("runs/he_qwen35_9b"),
            "mbpp": pathlib.Path("runs/mb_qwen35_9b"),
        },
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h2_full_replay_v1"),
    },
    "qwen3:0.6b": {
        "model_key": "qwen06",
        "expected_digest": None,
        "run_dirs": {
            "humaneval": pathlib.Path("runs/he_qwen06"),
            "mbpp": pathlib.Path("runs/mb_qwen06"),
        },
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1"),
    },
}


class BenchmarkRunnerError(RuntimeError):
    """Fail-closed error for benchmark runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkRunnerError(message)


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_cell_identity(model_tag: str, task_id: str, condition: str) -> str:
    """Generates unique cell identity for ITT replay state."""
    raw = f"{model_tag}:{task_id}:{condition}"
    return _sha256_text(raw)


def load_tasks(dataset_name: str, repo_root: pathlib.Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Loads and validates benchmark task records from dataset jsonl file."""
    _require(dataset_name in ALLOWED_DATASETS, f"unsupported dataset: {dataset_name}")
    datasets_to_load = ["humaneval", "mbpp"] if dataset_name == "all" else [dataset_name]

    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for ds in datasets_to_load:
        task_file = repo_root / TASK_FILES[ds]
        _require(task_file.is_file(), f"task file missing: {task_file}")
        lines = task_file.read_text(encoding="utf-8").splitlines()
        ds_tasks = []
        for line in lines:
            if not line.strip():
                continue
            rec = json.loads(line)
            tid = rec.get("task_id")
            ep = rec.get("entry_point")
            _require(bool(tid), f"missing task_id in {ds}")
            _require(tid not in seen_ids, f"duplicate task_id: {tid}")
            _require(bool(ep) and str(ep).isidentifier(), f"invalid entry_point '{ep}' for task {tid}")
            seen_ids.add(tid)
            ds_tasks.append(rec)
        _require(
            len(ds_tasks) == EXPECTED_TASK_COUNTS[ds],
            f"{ds} task count mismatch: expected {EXPECTED_TASK_COUNTS[ds]}, found {len(ds_tasks)}",
        )
        tasks.extend(ds_tasks)

    return tasks


def validate_roster(dataset_name: str, repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Validates roster integrity for HumanEval and MBPP datasets."""
    tasks = load_tasks(dataset_name, repo_root=repo_root)
    he_count = sum(1 for t in tasks if str(t["task_id"]).startswith("HumanEval"))
    mb_count = sum(1 for t in tasks if str(t["task_id"]).startswith("Mbpp"))

    return {
        "status": "roster_validation_passed",
        "dataset": dataset_name,
        "total_tasks": len(tasks),
        "humaneval_tasks": he_count,
        "mbpp_tasks": mb_count,
        "unique_task_ids": len(tasks),
    }


def zero_model_preflight(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes zero-model preflight checks ensuring code immutability and rule hashes."""
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")

    rule_path = repo_root / RULE_RELATIVE
    _require(rule_path.is_file(), f"H2 rule file missing: {rule_path}")
    actual_hash = _sha256_file(rule_path)
    _require(
        actual_hash == EXPECTED_RULE_SHA256,
        f"H2 rule hash mismatch: expected {EXPECTED_RULE_SHA256}, got {actual_hash}",
    )

    roster_info = validate_roster(dataset, repo_root=repo_root)

    return {
        "status": "zero_model_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "rule_id": RULE_ID,
        "rule_hash": actual_hash,
        "model_calls": 0,
        "roster_info": roster_info,
    }


def audit_inventory(
    model_tag: str,
    dataset_name: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Audits existing raw generation attempts and extracted completions for model & dataset."""
    tasks = load_tasks(dataset_name, repo_root=repo_root)
    spec = MODEL_SPECS[model_tag]
    expected_digest = spec["expected_digest"]

    # Map of (task_id, treatment) -> attempt record
    present_raw: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_count = 0
    digest_drift_count = 0

    datasets_to_scan = ["humaneval", "mbpp"] if dataset_name == "all" else [dataset_name]

    for ds in datasets_to_scan:
        dir_path = repo_root / spec["run_dirs"][ds]
        if not dir_path.exists():
            continue

        manifest_file = dir_path / "generation_manifest.json"
        if manifest_file.is_file():
            try:
                m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                m_digest = m_data.get("model_digest")
                if expected_digest and m_digest and m_digest != expected_digest:
                    digest_drift_count += 1
            except Exception:
                pass

        attempts_file = dir_path / "generation_attempts.jsonl"
        if attempts_file.is_file():
            for line in attempts_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    tid = rec.get("task_id")
                    tr = rec.get("treatment") or rec.get("prompt_condition")
                    if tr:
                        tr = str(tr).lower()
                    if tid and tr in ("ab1", "ab2g"):
                        cell_key = (tid, tr)
                        if cell_key in present_raw:
                            duplicate_count += 1
                        else:
                            present_raw[cell_key] = rec
                except Exception:
                    pass

    _require(duplicate_count == 0, f"duplicate generation attempts detected: {duplicate_count}")
    _require(digest_drift_count == 0, f"model digest drift detected for model {model_tag}")

    he_tasks = [t for t in tasks if str(t["task_id"]).startswith("HumanEval")]
    mb_tasks = [t for t in tasks if str(t["task_id"]).startswith("Mbpp")]

    he_ab1 = sum(1 for t in he_tasks if (t["task_id"], "ab1") in present_raw)
    he_ab2g = sum(1 for t in he_tasks if (t["task_id"], "ab2g") in present_raw)
    he_present_raw = he_ab1 + he_ab2g

    mb_ab1 = sum(1 for t in mb_tasks if (t["task_id"], "ab1") in present_raw)
    mb_ab2g = sum(1 for t in mb_tasks if (t["task_id"], "ab2g") in present_raw)
    mb_present_raw = mb_ab1 + mb_ab2g

    total_present_raw = he_present_raw + mb_present_raw
    total_planned_raw = len(tasks) * 2
    total_planned_itt = len(tasks) * len(CONDITIONS)

    he_missing_raw = len(he_tasks) * 2 - he_present_raw
    mb_missing_raw = len(mb_tasks) * 2 - mb_present_raw
    total_missing_raw = total_planned_raw - total_present_raw

    he_missing_itt = len(he_tasks) * len(CONDITIONS) - (he_present_raw * 2)
    mb_missing_itt = len(mb_tasks) * len(CONDITIONS) - (mb_present_raw * 2)
    total_missing_itt = total_planned_itt - (total_present_raw * 2)

    readiness = "READY" if total_missing_raw == 0 else "NOT_READY"

    return {
        "model_tag": model_tag,
        "dataset": dataset_name,
        "readiness_status": readiness,
        "humaneval_tasks": len(he_tasks),
        "mbpp_tasks": len(mb_tasks),
        "total_tasks": len(tasks),
        "conditions_count": len(CONDITIONS),
        "total_planned_itt_states": total_planned_itt,
        "present_raw_generations": total_present_raw,
        "missing_raw_generations": total_missing_raw,
        "missing_itt_states": total_missing_itt,
        "present_raw_map": present_raw,
        "breakdown": {
            "humaneval": {
                "tasks": len(he_tasks),
                "planned_itt_states": len(he_tasks) * len(CONDITIONS),
                "present_raw": he_present_raw,
                "ab1_present": he_ab1,
                "ab2g_present": he_ab2g,
                "missing_raw": he_missing_raw,
                "missing_itt": he_missing_itt,
            },
            "mbpp": {
                "tasks": len(mb_tasks),
                "planned_itt_states": len(mb_tasks) * len(CONDITIONS),
                "present_raw": mb_present_raw,
                "ab1_present": mb_ab1,
                "ab2g_present": mb_ab2g,
                "missing_raw": mb_missing_raw,
                "missing_itt": mb_missing_itt,
            },
        },
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Performs dry-run readiness audit for specified model and dataset."""
    preflight = zero_model_preflight(model=model, dataset=dataset, repo_root=repo_root)
    inventory = audit_inventory(model, dataset, repo_root=repo_root)
    # Exclude internal map from dry-run summary output
    inventory_summary = {k: v for k, v in inventory.items() if k != "present_raw_map"}

    return {
        "status": "dry_run_completed",
        "preflight": preflight,
        "inventory": inventory_summary,
        "model_calls": 0,
        "evalplus_executed": False,
    }


def run_replay_execution(
    *,
    model: str,
    dataset: str,
    resume: bool = True,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes H2 replay materialization creating per-cell journals for ITT states."""
    preflight = zero_model_preflight(model=model, dataset=dataset, repo_root=repo_root)
    inventory = audit_inventory(model, dataset, repo_root=repo_root)

    _require(
        inventory["readiness_status"] == "READY",
        f"raw generations incomplete for {model} on {dataset}: missing {inventory['missing_raw_generations']} raw generations",
    )

    spec = MODEL_SPECS[model]
    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    j_dir = out_dir / "j"
    j_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(dataset, repo_root=repo_root)
    present_map = inventory["present_raw_map"]

    executed_cells = 0
    skipped_cells = 0
    total_itt_cells = len(tasks) * len(CONDITIONS)

    ab1_raw_count = 0
    ab1_h2_count = 0
    ab2g_raw_count = 0
    ab2g_h2_count = 0

    ledger_rows: list[dict[str, Any]] = []

    for task_rec in tasks:
        tid = task_rec["task_id"]
        ep = task_rec["entry_point"]

        for tr in ("ab1", "ab2g"):
            raw_rec = present_map.get((tid, tr))
            _require(raw_rec is not None, f"raw generation missing for task {tid} treatment {tr}")

            raw_resp = raw_rec.get("raw_response") or ""
            ext_res = extract_code(raw_resp)
            is_extracted = (ext_res.extraction_status == "extracted")
            ext_code = ext_res.extracted_code if is_extracted else ""

            # Determine conditions to evaluate
            cond_raw = "Ab1-Raw" if tr == "ab1" else "Ab2g-Raw"
            cond_h2 = "Ab1-H2" if tr == "ab1" else "Ab2g-H2"

            # 1. Process Raw condition
            cell_id_raw = generate_cell_identity(model, tid, cond_raw)
            j_file_raw = j_dir / f"{cell_id_raw}.json"

            skip_raw = False
            if resume and j_file_raw.is_file():
                try:
                    existing = json.loads(j_file_raw.read_text(encoding="utf-8"))
                    if existing.get("persisted_complete") is True:
                        skipped_cells += 1
                        skip_raw = True
                        if cond_raw == "Ab1-Raw": ab1_raw_count += 1
                        else: ab2g_raw_count += 1
                        ledger_rows.append({
                            "cell_identity": cell_id_raw,
                            "task_id": tid,
                            "condition": cond_raw,
                            "output_source": existing.get("output_source", ""),
                        })
                except Exception:
                    pass

            if not skip_raw:
                journal_raw = {
                    "cell_identity": cell_id_raw,
                    "model_tag": model,
                    "task_id": tid,
                    "condition": cond_raw,
                    "treatment": tr,
                    "entry_point": ep,
                    "extraction_status": ext_res.extraction_status,
                    "extraction_method": ext_res.extraction_method,
                    "output_source": ext_code,
                    "persisted_complete": True,
                    "runner_identity": "public_benchmark_h2_replay_v1",
                    "h2_triggered": False,
                }
                durable_write_json_new(j_file_raw, journal_raw)
                executed_cells += 1
                if cond_raw == "Ab1-Raw": ab1_raw_count += 1
                else: ab2g_raw_count += 1
                ledger_rows.append({
                    "cell_identity": cell_id_raw,
                    "task_id": tid,
                    "condition": cond_raw,
                    "output_source": ext_code,
                })

            # 2. Process H2 condition
            cell_id_h2 = generate_cell_identity(model, tid, cond_h2)
            j_file_h2 = j_dir / f"{cell_id_h2}.json"

            skip_h2 = False
            if resume and j_file_h2.is_file():
                try:
                    existing = json.loads(j_file_h2.read_text(encoding="utf-8"))
                    if existing.get("persisted_complete") is True:
                        skipped_cells += 1
                        skip_h2 = True
                        if cond_h2 == "Ab1-H2": ab1_h2_count += 1
                        else: ab2g_h2_count += 1
                        ledger_rows.append({
                            "cell_identity": cell_id_h2,
                            "task_id": tid,
                            "condition": cond_h2,
                            "output_source": existing.get("output_source", ""),
                        })
                except Exception:
                    pass

            if not skip_h2:
                h2_res = quarantine_module_assert_entrypoint_selftest(
                    ext_code,
                    ep,
                    extraction_unambiguous=is_extracted,
                    source_complete=True,
                )

                journal_h2 = {
                    "cell_identity": cell_id_h2,
                    "model_tag": model,
                    "task_id": tid,
                    "condition": cond_h2,
                    "treatment": tr,
                    "entry_point": ep,
                    "extraction_status": ext_res.extraction_status,
                    "extraction_method": ext_res.extraction_method,
                    "output_source": h2_res.output_source,
                    "h2_triggered": h2_res.triggered,
                    "h2_transformed": h2_res.transformed,
                    "persisted_complete": True,
                    "runner_identity": "public_benchmark_h2_replay_v1",
                }
                durable_write_json_new(j_file_h2, journal_h2)
                executed_cells += 1
                if cond_h2 == "Ab1-H2": ab1_h2_count += 1
                else: ab2g_h2_count += 1
                ledger_rows.append({
                    "cell_identity": cell_id_h2,
                    "task_id": tid,
                    "condition": cond_h2,
                    "output_source": h2_res.output_source,
                })

    he_tasks = [t for t in tasks if str(t["task_id"]).startswith("HumanEval")]
    mb_tasks = [t for t in tasks if str(t["task_id"]).startswith("Mbpp")]

    summary = {
        "status": "replay_execution_completed",
        "model_tag": model,
        "dataset": dataset,
        "output_directory": out_dir.as_posix(),
        "raw_generations": inventory["present_raw_generations"],
        "itt_states": total_itt_cells,
        "humaneval_itt_states": len(he_tasks) * len(CONDITIONS),
        "mbpp_itt_states": len(mb_tasks) * len(CONDITIONS),
        "ab1_raw_count": ab1_raw_count,
        "ab1_h2_count": ab1_h2_count,
        "ab2g_raw_count": ab2g_raw_count,
        "ab2g_h2_count": ab2g_h2_count,
        "missing": 0,
        "duplicate": 0,
        "skipped_resume_cells": skipped_cells,
        "executed_cells": executed_cells,
        "model_calls": 0,
        "evalplus_executed": False,
    }

    # Write summary manifest
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Write cell_level_ledger.csv
    ledger_path = out_dir / "cell_level_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cell_identity", "task_id", "condition", "output_source_sha256", "has_output_source"])
        for row in ledger_rows:
            src = row.get("output_source", "")
            src_hash = _sha256_text(src) if src else ""
            writer.writerow([
                row["cell_identity"],
                row["task_id"],
                row["condition"],
                src_hash,
                bool(src),
            ])

    # Write execution_manifest.json
    manifest_path = out_dir / "execution_manifest.json"
    manifest_data = {
        "plan_id": f"{spec['model_key']}_h2_full_replay_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_tag": model,
        "dataset": dataset,
        "total_tasks": len(tasks),
        "total_planned_itt_states": total_itt_cells,
        "executed_cells": executed_cells + skipped_cells,
        "rule_id": RULE_ID,
        "rule_sha256": EXPECTED_RULE_SHA256,
        "model_calls": 0,
        "evalplus_executed": False,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)

    if args.parallel != 1:
        _require(False, "--parallel must be 1 for strict determinism")

    if args.dry_run:
        result = run_dry_run(model=args.model, dataset=args.dataset)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    result = run_replay_execution(
        model=args.model,
        dataset=args.dataset,
        resume=args.resume,
        output_dir_arg=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
