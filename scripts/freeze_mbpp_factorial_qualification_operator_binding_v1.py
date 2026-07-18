#!/usr/bin/env python3
"""Freeze executable operator bindings for the b28 development qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PureWindowsPath
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_mbpp_factorial_development_qualification_v1 as qualification  # noqa: E402


OUTPUT_RELATIVE = qualification.OUTPUT_RELATIVE / "operator_binding_v1"
QUALIFICATION_MANIFEST = qualification.OUTPUT_RELATIVE / "factorial_development_qualification_manifest.json"
QUALIFICATION_PLAN = qualification.OUTPUT_RELATIVE / "candidate_b_2x2_development_plan.json"
QUALIFICATION_ACCOUNTS = qualification.OUTPUT_RELATIVE / "candidate_b_2x2_account_plan.csv"
GENERATION_PROTOCOL = Path("configs/public_benchmark_generation_protocol_v1.json")
RUNNER_SOURCE = Path("scripts/run_mbpp_factorial_development_qualification.py")
FACTORIAL_PATH = Path("artifacts/pbd/mbpp_b28/fa/r001")
DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
WINDOWS_REPO_PREFIX = r"C:\Users\yehya\Documents\GitHub\MathProject_AST_Research_Stage2"
JOURNAL_DIRECTORY = "j"


class OperatorBindingError(RuntimeError):
    """Raised before writes when an operator binding invariant drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OperatorBindingError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_qualification_outputs(repo_root: Path) -> None:
    rebuilt = qualification.build_outputs(repo_root)
    output_dir = repo_root / qualification.OUTPUT_RELATIVE
    for name, content in rebuilt.items():
        _require((output_dir / name).is_file(), f"qualification output missing: {name}")
        _require((output_dir / name).read_bytes() == content, f"qualification output drift: {name}")


def _generation_plan(
    qualification_plan: dict[str, Any], treatment: str, source_hashes: dict[str, str]
) -> dict[str, Any]:
    _require(treatment in {"p0", "candidate_b"}, "unknown treatment")
    prompt_condition = "P0" if treatment == "p0" else "P1_candidate_b"
    generation = qualification_plan["generation"]["p0" if treatment == "p0" else "p1"]
    cells = [
        dict(cell, cell_index=index + 1)
        for index, cell in enumerate(qualification_plan["generation"]["cells"])
        if cell["prompt_condition"] == prompt_condition
    ]
    task_ids = list(dict.fromkeys(cell["task_id"] for cell in cells))
    _require(len(cells) == 140 and len(task_ids) == 28, "generation plan count drift")
    _require(len({(cell["task_id"], cell["seed"]) for cell in cells}) == 140, "identity drift")
    candidate = qualification_plan["candidate_b"]
    return {
        "plan_version": "mbpp_b28_generation_plan_v1",
        "status": "frozen_not_executed_development_only",
        "run_id": generation["run_id"],
        "logical_run_id": generation["run_id"],
        "physical_storage_directory": generation["physical_path"],
        "treatment": treatment,
        "treatment_id": "p0_official_prompt_only" if treatment == "p0" else "candidate_b_scaffold",
        "prompt_condition": prompt_condition,
        "task_ids": task_ids,
        "task_count": 28,
        "seeds": list(qualification.SEEDS),
        "expected_cells": 140,
        "cells": cells,
        "dataset": "MBPP+",
        "dataset_version": "v0.2.0",
        "dataset_hash": DATASET_HASH,
        "model": qualification_plan["model_protocol"]["model"],
        "model_digest": qualification_plan["model_protocol"]["digest"],
        "quantization": qualification_plan["model_protocol"]["quantization"],
        "generation_parameters": qualification_plan["model_protocol"]["sampling"],
        "think": False,
        "timeout_seconds": 600,
        "attempts_per_cell": 1,
        "retry": False,
        "resume": False,
        "selective_retry": False,
        "overwrite": False,
        "healer": False,
        "pipeline_correction_during_generation": False,
        "pipeline_correction_is_healer": False,
        "candidate_id": candidate["candidate_id"] if treatment == "candidate_b" else None,
        "candidate_status": candidate["status"] if treatment == "candidate_b" else None,
        "candidate_exact_text_utf8": candidate["exact_text_utf8"] if treatment == "candidate_b" else None,
        "candidate_exact_text_sha256": candidate["exact_text_sha256"] if treatment == "candidate_b" else None,
        "separator_exact_text_utf8": qualification_plan["prompt_composition"]["separator_exact_text_utf8"] if treatment == "candidate_b" else None,
        "separator_sha256": qualification_plan["prompt_composition"]["separator_sha256"] if treatment == "candidate_b" else None,
        "generation_protocol_path": GENERATION_PROTOCOL.as_posix(),
        "generation_protocol_sha256": source_hashes[GENERATION_PROTOCOL.as_posix()],
        "operator_driver_sha256": source_hashes[RUNNER_SOURCE.as_posix()],
        "source_qualification_plan_sha256": source_hashes[QUALIFICATION_PLAN.as_posix()],
        "formal_validation": False,
    }


def _storage_mapping(plans: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for name, plan in plans.items():
        physical = plan["physical_storage_directory"]
        longest = PureWindowsPath(WINDOWS_REPO_PREFIX) / physical / JOURNAL_DIRECTORY / ("f" * 64 + ".json")
        rows.append({
            "treatment": name,
            "run_id": plan["run_id"],
            "physical_path": physical,
            "longest_planned_windows_path": str(longest),
            "longest_planned_windows_path_length": len(str(longest)),
            "within_240_character_budget": len(str(longest)) < 240,
        })
    factorial_longest = PureWindowsPath(WINDOWS_REPO_PREFIX) / FACTORIAL_PATH / "factorial_sources.jsonl"
    _require(all(row["within_240_character_budget"] for row in rows), "generation path budget failed")
    _require(len(str(factorial_longest)) < 240, "factorial path budget failed")
    return {
        "windows_path_budget": 240,
        "runs": rows,
        "factorial_materialization_path": FACTORIAL_PATH.as_posix(),
        "factorial_longest_windows_path_length": len(str(factorial_longest)),
        "all_paths_within_budget": True,
        "run_directories_created": False,
    }


def _operator_guide(plans: dict[str, dict[str, Any]]) -> bytes:
    p0 = plans["p0"]
    p1 = plans["candidate_b"]
    lines = [
        "# MBPP+ b28 2×2 development qualification operator guide",
        "",
        "本guide只操作development-only qualification。執行前必須確認main、乾淨工作樹、HEAD==origin/main，並先執行preflight。不得在validation、confirmatory或sealed資料上使用這些指令。",
        "",
        "## Windows：生成",
        "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe scripts\\run_mbpp_factorial_development_qualification.py preflight",
        f".\\.venv\\Scripts\\python.exe scripts\\run_mbpp_factorial_development_qualification.py generate --treatment p0 --run-id {p0['run_id']}",
        f".\\.venv\\Scripts\\python.exe scripts\\run_mbpp_factorial_development_qualification.py generate --treatment candidate_b --run-id {p1['run_id']}",
        "```",
        "",
        "每個run必須完整140/140且每格exactly one attempt。若中斷或失敗，既有run directory永久不可resume、retry、補跑或覆寫；必須先建立新的事故addendum。",
        "",
        "## Windows或WSL：建立H0/H1來源帳",
        "",
        "```text",
        "python scripts/run_mbpp_factorial_development_qualification.py materialize-factorial",
        "```",
        "",
        "此步不呼叫模型或evaluator。每份generation先經同一Pipeline；H0原樣保存normalized source，H1套用同一Healer source、rule order與guards。Pipeline extraction與fence處理不計入Healer。",
        "",
        "## WSL：EvalPlus",
        "",
        "EvalPlus執行指令尚未啟用：必須先確認兩個140-cell runs及560個factorial source accounts完整，並在下一個execution addendum固定evaluator driver hash。不得直接改用舊Candidate A evaluator。",
        "",
        "## 禁止事項",
        "",
        "不得為H1重新生成；不得用evaluator結果選擇、撤回或接受個別repair；不得把raw packaging ablation混入四帳；不得修改Candidate B、Pipeline或Healer後重跑相同28題。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    repo_root = repo_root.resolve()
    _verify_qualification_outputs(repo_root)
    qualification_plan = _read_json(repo_root / QUALIFICATION_PLAN)
    qualification_manifest = _read_json(repo_root / QUALIFICATION_MANIFEST)
    _require(qualification_manifest["status"] == "frozen_not_executed_development_only", "qualification status drift")
    source_paths = (
        QUALIFICATION_MANIFEST, QUALIFICATION_PLAN, QUALIFICATION_ACCOUNTS,
        GENERATION_PROTOCOL, RUNNER_SOURCE,
    )
    source_hashes = {path.as_posix(): _sha256((repo_root / path).read_bytes()) for path in source_paths}
    plans = {
        name: _generation_plan(qualification_plan, name, source_hashes)
        for name in ("p0", "candidate_b")
    }
    _require(
        [(cell["task_id"], cell["seed"]) for cell in plans["p0"]["cells"]]
        == [(cell["task_id"], cell["seed"]) for cell in plans["candidate_b"]["cells"]],
        "P0/P1 paired schedule drift",
    )
    storage = _storage_mapping(plans)
    outputs = {
        "p0_generation_plan.json": _json_bytes(plans["p0"]),
        "candidate_b_generation_plan.json": _json_bytes(plans["candidate_b"]),
        "storage_mapping.json": _json_bytes(storage),
        "operator_guide_zh.md": _operator_guide(plans),
    }
    manifest = {
        "manifest_version": "mbpp_factorial_qualification_operator_binding_v1",
        "status": "frozen_not_executed_development_only",
        "source_qualification_manifest_sha256": source_hashes[QUALIFICATION_MANIFEST.as_posix()],
        "source_sha256": source_hashes,
        "counts": {"p0_generation_cells": 140, "candidate_b_generation_cells": 140, "paired_identities": 140, "future_factorial_accounts": 560},
        "run_ids": {name: plan["run_id"] for name, plan in plans.items()},
        "physical_paths": {name: plan["physical_storage_directory"] for name, plan in plans.items()} | {"factorial": FACTORIAL_PATH.as_posix()},
        "model_calls": 0,
        "evalplus_executions": 0,
        "run_directories_created": False,
        "evaluation_driver_enabled": False,
        "output_sha256_excluding_manifest": {name: _sha256(content) for name, content in sorted(outputs.items())},
    }
    outputs["operator_binding_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "operator binding directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "operator output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "operator binding directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except OperatorBindingError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
