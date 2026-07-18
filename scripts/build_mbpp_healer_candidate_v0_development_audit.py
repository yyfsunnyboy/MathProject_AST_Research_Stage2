#!/usr/bin/env python3
"""Build a deterministic offline audit of the narrow MBPP+ Healer candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild import mbpp_evaluator_blind_healer as healer  # noqa: E402
from scripts import build_mbpp_integrated_development_evidence as integrated  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_candidate_v0_development_audit"
)
LEDGER_FIELDS = (
    "development_layer", "prompt_condition", "treatment", "run_id", "task_id",
    "seed", "generation_id", "pipeline_precedes_healer", "pipeline_output_available",
    "generation_truncated", "input_sha256", "healer_status", "triggered_rule_ids",
    "applied_rule_ids", "diagnostic", "output_sha256", "source_changed",
    "ast_prefix_preserved", "rule_order", "same_guards_all_conditions",
    "static_shape_match_before_truncation_guard", "evaluator_input_used", "development_only",
)
SUMMARY_FIELDS = (
    "rule_id", "candidate_status", "rule_order_position", "expected_repairable_signature",
    "p0_static_signature_cells_before_truncation_guard",
    "scaffold_static_signature_cells_before_truncation_guard",
    "p0_trigger_cells", "p0_trigger_unique_tasks", "p0_trigger_task_ids",
    "scaffold_trigger_cells", "scaffold_trigger_unique_tasks", "scaffold_trigger_task_ids",
    "p0_transformed_cells", "scaffold_transformed_cells", "semantic_risk",
    "safety_guards", "abstention_conditions", "evaluator_blind",
    "same_version_order_guards", "development_only", "verified_functional_repair",
)


class HealerAuditError(RuntimeError):
    """Raised before writes when the development audit does not reconcile."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HealerAuditError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _index(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in result, f"{label}: duplicate identity {key}")
        result[key] = row
    return result


def _plan_keys(plan: dict[str, Any]) -> list[tuple[str, int]]:
    if "cells" in plan:
        return [(cell["task_id"], int(cell["seed"])) for cell in plan["cells"]]
    return [(task_id, int(seed)) for task_id in plan["task_ids"] for seed in plan["seeds"]]


def _load_without_evaluator(repo_root: Path, relative: Path, run_id: str) -> dict[str, Any]:
    root = repo_root / relative
    plan = _read_json(root / "generation_plan.json")
    _require(plan.get("run_id", plan.get("logical_run_id")) == run_id, f"run ID drift: {relative}")
    raw = _index(_read_jsonl(root / "raw_generations.jsonl"), f"{relative} raw")
    pipeline = _index(_read_jsonl(root / "pipeline_corrected.jsonl"), f"{relative} pipeline")
    keys = _plan_keys(plan)
    _require(len(keys) == len(set(keys)), f"plan duplicate: {relative}")
    _require(set(keys) == set(raw) == set(pipeline), f"identity drift: {relative}")
    for key in keys:
        _require(raw[key]["generation_id"] == pipeline[key]["generation_id"], f"generation drift: {relative} {key}")
        _require(raw[key].get("retry_count", 0) == 0, f"retry drift: {relative} {key}")
        _require(
            raw[key]["raw_response_sha256"] == pipeline[key]["source_raw_response_sha256"],
            f"raw/Pipeline hash drift: {relative} {key}",
        )
    return {"keys": keys, "raw": raw, "pipeline": pipeline}


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    rows: list[dict[str, str]] = []
    identities: set[tuple[str, int]] = set()
    source_paths: set[Path] = {Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")}

    for spec in integrated.RUNS:
        conditions = (
            ("p0", spec["baseline_label"], spec["baseline_run_id"], spec["baseline_dir"]),
            ("scaffold", spec["treatment_label"], spec["treatment_run_id"], spec["treatment_dir"]),
        )
        base = _load_without_evaluator(
            repo_root, spec["baseline_dir"], spec["baseline_run_id"]
        )
        for key in base["keys"]:
            _require(key not in identities, f"cross-layer duplicate {key}")
            identities.add(key)
        for prompt_condition, treatment, run_id, relative in conditions:
            run = base if prompt_condition == "p0" else _load_without_evaluator(repo_root, relative, run_id)
            _require(run["keys"] == base["keys"], f"paired order drift: {spec['pair_id']}")
            source_paths.update({
                relative / "generation_plan.json",
                relative / "raw_generations.jsonl",
                relative / "pipeline_corrected.jsonl",
            })
            for task_id, seed in run["keys"]:
                raw = run["raw"][(task_id, seed)]
                pipeline = run["pipeline"][(task_id, seed)]
                prompt = base["raw"][(task_id, seed)]["request"]["messages"][0]["content"]
                expected, arities = integrated._prompt_contract(prompt)
                normalized = pipeline["pipeline_corrected_output"]
                truncated = raw.get("generation_metadata", {}).get("done_reason") != "stop"
                result = healer.apply_healer(normalized, expected, arities, truncated)
                shape_only_result = healer.apply_healer(normalized, expected, arities, False)
                expected_input_hash = pipeline.get("pipeline_corrected_output_sha256")
                _require(result.input_sha256 == expected_input_hash, f"input hash drift: {run_id} {task_id} {seed}")
                changed = result.output_source != normalized
                _require(changed == (result.status == "transformed"), f"change/status drift: {run_id} {task_id} {seed}")
                rows.append({
                    "development_layer": spec["layer"],
                    "prompt_condition": prompt_condition,
                    "treatment": treatment,
                    "run_id": run_id,
                    "task_id": task_id,
                    "seed": str(seed),
                    "generation_id": raw["generation_id"],
                    "pipeline_precedes_healer": "true",
                    "pipeline_output_available": str(normalized is not None).lower(),
                    "generation_truncated": str(truncated).lower(),
                    "input_sha256": result.input_sha256 or "",
                    "healer_status": result.status,
                    "triggered_rule_ids": "|".join(result.triggered_rule_ids),
                    "applied_rule_ids": "|".join(result.applied_rule_ids),
                    "diagnostic": result.diagnostic,
                    "output_sha256": result.output_sha256 or "",
                    "source_changed": str(changed).lower(),
                    "ast_prefix_preserved": str(result.ast_prefix_preserved).lower(),
                    "rule_order": "|".join(healer.RULE_ORDER),
                    "same_guards_all_conditions": "true",
                    "static_shape_match_before_truncation_guard": str(
                        shape_only_result.status == "transformed"
                    ).lower(),
                    "evaluator_input_used": "false",
                    "development_only": "true",
                })

    _require(len(identities) == 300, "task-seed identity count drift")
    _require(len({task_id for task_id, _ in identities}) == 60, "task count drift")
    _require(len(rows) == 600, "program count drift")
    _require(Counter(row["prompt_condition"] for row in rows) == {"p0": 300, "scaffold": 300}, "condition count drift")

    transformed = [row for row in rows if row["healer_status"] == "transformed"]
    p0 = [row for row in transformed if row["prompt_condition"] == "p0"]
    scaffold = [row for row in transformed if row["prompt_condition"] == "scaffold"]
    p0_static = [row for row in rows if row["prompt_condition"] == "p0" and row["static_shape_match_before_truncation_guard"] == "true"]
    scaffold_static = [row for row in rows if row["prompt_condition"] == "scaffold" and row["static_shape_match_before_truncation_guard"] == "true"]
    summary = [{
        "rule_id": healer.RULE_ID,
        "candidate_status": healer.CANDIDATE_STATUS,
        "rule_order_position": "1",
        "expected_repairable_signature": "entrypoint_unique_arity_compatible_candidate",
        "p0_static_signature_cells_before_truncation_guard": str(len(p0_static)),
        "scaffold_static_signature_cells_before_truncation_guard": str(len(scaffold_static)),
        "p0_trigger_cells": str(len(p0)),
        "p0_trigger_unique_tasks": str(len({row['task_id'] for row in p0})),
        "p0_trigger_task_ids": "|".join(sorted({row["task_id"] for row in p0})),
        "scaffold_trigger_cells": str(len(scaffold)),
        "scaffold_trigger_unique_tasks": str(len({row['task_id'] for row in scaffold})),
        "scaffold_trigger_task_ids": "|".join(sorted({row["task_id"] for row in scaffold})),
        "p0_transformed_cells": str(len(p0)),
        "scaffold_transformed_cells": str(len(scaffold)),
        "semantic_risk": "moderate_name_alias_may_expose_wrong_semantics",
        "safety_guards": "parsed source; target unbound; one undecorated synchronous top-level function; all visible positional arities compatible; alias-only AST diff",
        "abstention_conditions": "Pipeline unavailable; truncation; syntax failure; target binding; async/decorated/multiple/no function; missing or incompatible arity; AST diff violation",
        "evaluator_blind": "true",
        "same_version_order_guards": "true",
        "development_only": "true",
        "verified_functional_repair": "false",
    }]
    diagnostic_counts = {
        condition: dict(sorted(Counter(
            row["diagnostic"] for row in rows if row["prompt_condition"] == condition
        ).items()))
        for condition in ("p0", "scaffold")
    }
    source_hashes = {
        path.as_posix(): _sha256((repo_root / path).read_bytes()) for path in sorted(source_paths)
    }
    return {"rows": rows, "summary": summary, "diagnostic_counts": diagnostic_counts, "source_hashes": source_hashes}


def _spec(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": healer.CANDIDATE_ID,
        "status": healer.CANDIDATE_STATUS,
        "development_only": True,
        "frozen_or_validation_ready": False,
        "input_account": "frozen Pipeline-normalized source",
        "pipeline_operations_counted_as_healer": False,
        "rule_order": list(healer.RULE_ORDER),
        "public_api": "apply_healer(normalized_source, expected_entry_point, expected_positional_arities, generation_truncated)",
        "treatment_or_scaffold_argument": False,
        "evaluator_or_test_result_argument": False,
        "transformation": "append name-only alias: expected_entry_point = sole_existing_function",
        "body_control_flow_import_edits": False,
        "diagnostic_counts": result["diagnostic_counts"],
        "functional_correctness_re_evaluated": False,
        "static_signature_before_truncation_guard": {
            "p0_cells": int(result["summary"][0]["p0_static_signature_cells_before_truncation_guard"]),
            "scaffold_cells": int(result["summary"][0]["scaffold_static_signature_cells_before_truncation_guard"]),
        },
        "model_calls": 0,
        "evalplus_executions": 0,
    }


def _report(result: dict[str, Any]) -> bytes:
    row = result["summary"][0]
    lines = [
        "# MBPP+ evaluator-blind Healer candidate v0 development audit",
        "",
        "這是development-only候選實作與靜態安全稽核，不是正式Healer凍結，也不是功能修復成效證明。本輪只重用既有600份Pipeline-normalized development程式，沒有呼叫模型或EvalPlus。",
        "",
        "## 候選規則",
        "",
        "唯一規則只在程式可解析、預期名稱尚未被綁定、恰有一個無decorator的同步頂層函式，且其參數數量相容於prompt中可見呼叫時，於檔尾追加名稱alias。原函式body、control flow與imports完全不改。任何模糊情況都維持原輸出並abstain。",
        "",
        "## 2×2相容性",
        "",
        "Pipeline一定先執行；H0保留normalized source，H1才呼叫此候選。API沒有P0/P1、Scaffold或evaluator欄位，因此兩種prompt條件使用相同版本、單一規則順序及相同guards。Pipeline extraction、fence stripping與plain-text normalization不計入Healer。",
        "",
        "## Development-only觸發",
        "",
        f"guard前靜態shape signature在P0為{row['p0_static_signature_cells_before_truncation_guard']}格、Scaffold為{row['scaffold_static_signature_cells_before_truncation_guard']}格。套用truncation等全部guards後，P0實際安全觸發並轉換{row['p0_trigger_cells']}格／{row['p0_trigger_unique_tasks']}題；Scaffold條件為{row['scaffold_trigger_cells']}格／{row['scaffold_trigger_unique_tasks']}題。P0少掉的一格是length-terminated輸出，依規則必須abstain。這些是靜態trigger與AST差異證據，不是evaluator驗證的repair success。",
        "",
        "semantic risk仍為中等：被alias的唯一函式可能本身語意錯誤。因此未來只能前瞻比較同一generation的H0/H1帳，不能用pass/fail挑選是否接受修復。truncation、syntax、multiple functions、unknown與語意不確定案例全部abstain。",
        "",
        "## 目前狀態",
        "",
        "候選尚未凍結、尚未進入validation。正式2×2計畫仍須先凍結final P1、Healer source/hash/rule order/guards、Pipeline hash、validation identities與claim rules。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    result = build_analysis(repo_root)
    outputs = {
        "healer_candidate_v0_cell_ledger.csv": _csv_bytes(result["rows"], LEDGER_FIELDS),
        "healer_candidate_v0_rule_summary.csv": _csv_bytes(result["summary"], SUMMARY_FIELDS),
        "healer_candidate_v0_spec.json": _json_bytes(_spec(result)),
        "healer_candidate_v0_development_audit_zh.md": _report(result),
    }
    manifest = {
        "manifest_version": "mbpp_healer_candidate_v0_development_audit_v1",
        "status": healer.CANDIDATE_STATUS,
        "development_only": True,
        "counts": {"tasks": 60, "task_seed_identities": 300, "programs": 600},
        "prompt_condition_programs": {"p0": 300, "scaffold": 300},
        "pipeline_precedes_healer": True,
        "same_healer_version_rule_order_guards": True,
        "evaluator_inputs_used": False,
        "functional_correctness_re_evaluated": False,
        "model_calls": 0,
        "evalplus_executions": 0,
        "source_sha256": result["source_hashes"],
        "output_sha256_excluding_manifest": {
            name: _sha256(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["healer_candidate_v0_development_audit_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "output directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "output directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except HealerAuditError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
