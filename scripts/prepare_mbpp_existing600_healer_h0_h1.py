#!/usr/bin/env python3
"""Freeze the evaluator-blind H0/H1 accounts for 600 existing MBPP programs.

This program is an offline materializer.  It never generates model output and
never imports or invokes EvalPlus.  All checks complete before any file is
written, and an existing output directory is never overwritten.
"""

from __future__ import annotations

import argparse
import ast
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


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1"
)
HEALER_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
PIPELINE_RELATIVE = Path("agent_tools/finals_rebuild/extraction.py")
EXPECTED_HEALER_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_PIPELINE_SHA256 = "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
EXPECTED_EVALUATOR_VERSION = "0.3.1"
EXPECTED_EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"
EXPECTED_CANDIDATE_ID = "mbpp_evaluator_blind_healer_candidate_v0"
EXPECTED_RULE_ID = "entrypoint_alias_unique_arity_compatible_v0"

DISCOVERY_P0 = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/"
    "runs/mbpp_qwen35_9b_ab1_dev_run_003"
)
DISCOVERY_SCAFFOLD = Path("artifacts/pbd/mbpp_sv0/r002")
EXPANSION_P0 = Path("artifacts/pbd/mbpp_e40/p0/r001")
EXPANSION_SCAFFOLD = Path("artifacts/pbd/mbpp_e40/ca/r002")

RUNS = (
    {
        "development_layer": "discovery_development",
        "baseline": {
            "prompt_condition": "p0",
            "treatment": "p0_official_prompt_only",
            "run_id": "mbpp_qwen35_9b_ab1_dev_run_003",
            "relative": DISCOVERY_P0,
        },
        "treatment": {
            "prompt_condition": "scaffold_like",
            "treatment": "scaffold_v0",
            "run_id": "mbpp_qwen35_9b_scaffold_v0_dev_run_002",
            "relative": DISCOVERY_SCAFFOLD,
        },
        "expected_cells": 100,
    },
    {
        "development_layer": "expansion_development",
        "baseline": {
            "prompt_condition": "p0",
            "treatment": "p0_official_prompt_only",
            "run_id": "mbpp_q35_9b_p0_exp40_r001",
            "relative": EXPANSION_P0,
        },
        "treatment": {
            "prompt_condition": "scaffold_like",
            "treatment": "candidate_a_scaffold",
            "run_id": "mbpp_q35_9b_ca_exp40_r002",
            "relative": EXPANSION_SCAFFOLD,
        },
        "expected_cells": 200,
    },
)

ACCOUNT_FIELDS = (
    "program_index", "account_index", "program_id", "evaluation_account_id",
    "healer_account", "development_layer", "prompt_condition", "treatment",
    "run_id", "task_id", "seed", "sample_index", "generation_id",
    "raw_sha256", "normalized_source_available", "normalized_source_sha256",
    "normalized_source_state_sha256", "evaluation_source_sha256",
    "expected_entry_point", "expected_positional_arities", "generation_truncated",
    "healer_candidate_id", "healer_rule_id", "healer_status", "healer_diagnostic",
    "source_changed", "alias_only_verified", "compile_verified",
    "existing_h0_status", "existing_h0_pass", "evaluation_disposition",
    "same_generation_identity_h0_h1", "same_raw_sha_h0_h1",
    "same_normalized_sha_h0_h1", "evaluator_used_by_healer",
)

REUSE_FIELDS = (
    "program_id", "h0_evaluation_account_id", "h1_evaluation_account_id",
    "development_layer", "prompt_condition", "run_id", "task_id", "seed",
    "generation_id", "raw_sha256", "normalized_source_available",
    "h0_source_sha256", "h1_source_sha256", "h0_source_state_sha256",
    "h1_source_state_sha256", "source_state_sha256_exact_match",
    "existing_h0_output_sha256_verified", "existing_h0_status",
    "existing_h0_pass", "existing_h0_result_complete", "reuse_eligible",
    "reuse_basis", "reuse_independent_of_h0_pass_fail",
)

_BUILTIN_CALLS = {
    "abs", "all", "any", "isinstance", "len", "list", "max", "min",
    "round", "set", "sorted", "sum", "tuple",
}


class PreparationError(RuntimeError):
    """Raised before writes when any frozen invariant fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreparationError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _identity_hash(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in result, f"{label}: duplicate identity {key}")
        result[key] = row
    return result


def _plan_keys(plan: dict[str, Any]) -> list[tuple[str, int]]:
    if plan.get("cells"):
        return [(str(cell["task_id"]), int(cell["seed"])) for cell in plan["cells"]]
    return [(str(task_id), int(seed)) for task_id in plan["task_ids"] for seed in plan["seeds"]]


def _prompt_contract(prompt: str) -> tuple[str, tuple[int, ...]]:
    calls: list[ast.Call] = []
    for line in prompt.splitlines():
        if not line.strip().startswith("assert "):
            continue
        try:
            tree = ast.parse(line.strip())
        except SyntaxError:
            continue
        calls.extend(
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id not in _BUILTIN_CALLS
        )
    names = {call.func.id for call in calls}
    _require(len(names) == 1, "development prompt must expose exactly one entry point")
    expected = next(iter(names))
    arities = tuple(sorted({len(call.args) for call in calls if call.func.id == expected and not call.keywords}))
    _require(bool(arities), f"{expected}: positional arity evidence missing")
    return expected, arities


def _source_state_sha256(source: str | None) -> str:
    state = {
        "normalized_source_available": source is not None,
        "normalized_source_sha256": _sha256_text(source) if source is not None else None,
    }
    return _identity_hash(state)


def _load_run(repo_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    root = repo_root / spec["relative"]
    plan = _read_json(root / "generation_plan.json")
    plan_run_id = plan.get("run_id", plan.get("logical_run_id"))
    _require(plan_run_id == spec["run_id"], f"run ID drift: {spec['relative']}")
    _require(plan.get("dataset_version") == EXPECTED_DATASET_VERSION, "dataset version drift")
    _require(plan.get("dataset_hash") == EXPECTED_DATASET_HASH, "dataset hash drift")
    keys = _plan_keys(plan)
    _require(len(keys) == len(set(keys)), f"duplicate plan identity: {spec['run_id']}")
    raw = _index(_read_jsonl(root / "raw_generations.jsonl"), f"{spec['run_id']} raw")
    pipeline = _index(_read_jsonl(root / "pipeline_corrected.jsonl"), f"{spec['run_id']} pipeline")
    evaluation = _index(_read_csv(root / "evaluation_results.csv"), f"{spec['run_id']} evaluation")
    _require(set(keys) == set(raw) == set(pipeline) == set(evaluation), f"identity drift: {spec['run_id']}")
    for key in keys:
        raw_row, pipeline_row, eval_row = raw[key], pipeline[key], evaluation[key]
        _require(raw_row["generation_id"] == pipeline_row["generation_id"] == eval_row["generation_id"], f"generation drift: {spec['run_id']} {key}")
        _require(raw_row.get("retry_count", 0) == 0, f"retry found: {spec['run_id']} {key}")
        _require(raw_row["raw_response_sha256"] == pipeline_row["source_raw_response_sha256"], f"raw hash drift: {spec['run_id']} {key}")
        source = pipeline_row["pipeline_corrected_output"]
        source_hash = pipeline_row.get("pipeline_corrected_output_sha256")
        _require(source_hash == (_sha256_text(source) if source is not None else None), f"normalized hash drift: {spec['run_id']} {key}")
        _require((eval_row.get("pipeline_corrected_output_sha256") or None) == source_hash, f"H0 evaluation source hash drift: {spec['run_id']} {key}")
        _require(eval_row["evaluator_version"] == EXPECTED_EVALUATOR_VERSION, f"evaluator version drift: {spec['run_id']} {key}")
        _require(eval_row["evaluator_engine"] == EXPECTED_EVALUATOR_ENGINE, f"evaluator engine drift: {spec['run_id']} {key}")
        status = eval_row["pipeline_corrected_status"]
        _require(status in {"pass", "fail"}, f"invalid H0 status: {spec['run_id']} {key}")
        if eval_row.get("pipeline_corrected_evalplus_pass"):
            _require((eval_row["pipeline_corrected_evalplus_pass"] == "true") == (status == "pass"), f"H0 pass field drift: {spec['run_id']} {key}")
        if source is None:
            _require(status == "fail", f"unavailable Pipeline output passed: {spec['run_id']} {key}")
            _require(eval_row["pipeline_corrected_syntax_compile_status"] == "not_run_extraction_failed", f"unavailable source compile state drift: {spec['run_id']} {key}")
    return {"root": root, "plan": plan, "keys": keys, "raw": raw, "pipeline": pipeline, "evaluation": evaluation}


def _ast_invariants(original: str, transformed: str, expected: str) -> bool:
    original_tree = ast.parse(original)
    transformed_tree = ast.parse(transformed)
    _require(len(transformed_tree.body) == len(original_tree.body) + 1, "transformed AST statement budget drift")
    original_dump = ast.dump(original_tree, include_attributes=False)
    prefix_dump = ast.dump(ast.Module(body=transformed_tree.body[:-1], type_ignores=[]), include_attributes=False)
    _require(original_dump == prefix_dump, "function body/import/parameter AST changed")
    last = transformed_tree.body[-1]
    _require(
        isinstance(last, ast.Assign)
        and len(last.targets) == 1
        and isinstance(last.targets[0], ast.Name)
        and last.targets[0].id == expected
        and isinstance(last.value, ast.Name),
        "last statement is not the expected entry-point alias",
    )
    exact = original.rstrip() + "\n\n" + f"{expected} = {last.value.id}\n"
    _require(transformed == exact, "transformation is not the frozen alias-only byte form")
    compile(transformed, "<frozen-mbpp-h1>", "exec")
    return True


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return b"".join((json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8") for row in rows)


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    healer_hash = _sha256_bytes((repo_root / HEALER_RELATIVE).read_bytes())
    pipeline_hash = _sha256_bytes((repo_root / PIPELINE_RELATIVE).read_bytes())
    _require(healer_hash == EXPECTED_HEALER_SHA256, "Healer source SHA-256 drift")
    _require(pipeline_hash == EXPECTED_PIPELINE_SHA256, "Pipeline source SHA-256 drift")
    _require(healer.CANDIDATE_ID == EXPECTED_CANDIDATE_ID, "Healer candidate ID drift")
    _require(healer.RULE_ORDER == (EXPECTED_RULE_ID,), "Healer rule version/order drift")

    programs: list[dict[str, Any]] = []
    source_paths: set[Path] = {HEALER_RELATIVE, PIPELINE_RELATIVE}
    task_seed_identities: set[tuple[str, int]] = set()
    for pairing in RUNS:
        baseline = _load_run(repo_root, pairing["baseline"])
        treatment = _load_run(repo_root, pairing["treatment"])
        _require(len(baseline["keys"]) == pairing["expected_cells"], "baseline cell count drift")
        _require(treatment["keys"] == baseline["keys"], "paired prompt-condition order drift")
        for key in baseline["keys"]:
            _require(key not in task_seed_identities, f"cross-layer duplicate identity: {key}")
            task_seed_identities.add(key)
        prompt_contracts: dict[str, tuple[str, tuple[int, ...]]] = {}
        for key in baseline["keys"]:
            prompt = baseline["raw"][key]["request"]["messages"][0]["content"]
            contract = _prompt_contract(prompt)
            prior = prompt_contracts.setdefault(key[0], contract)
            _require(prior == contract, f"prompt contract drift by seed: {key[0]}")
        for condition_spec, run in ((pairing["baseline"], baseline), (pairing["treatment"], treatment)):
            source_paths.update(condition_spec["relative"] / name for name in (
                "generation_plan.json", "raw_generations.jsonl",
                "pipeline_corrected.jsonl", "evaluation_results.csv",
            ))
            for task_id, seed in run["keys"]:
                raw = run["raw"][(task_id, seed)]
                pipeline = run["pipeline"][(task_id, seed)]
                evaluation = run["evaluation"][(task_id, seed)]
                expected, arities = prompt_contracts[task_id]
                normalized = pipeline["pipeline_corrected_output"]
                normalized_hash = pipeline.get("pipeline_corrected_output_sha256")
                truncated = raw.get("generation_metadata", {}).get("done_reason") != "stop"
                result = healer.apply_healer(normalized, expected, arities, truncated)
                _require(result.input_sha256 == normalized_hash, f"Healer input hash drift: {condition_spec['run_id']} {task_id} {seed}")
                changed = result.output_source != normalized
                _require(changed == (result.status == "transformed"), "Healer status/change drift")
                alias_verified = _ast_invariants(normalized, result.output_source, expected) if changed else False
                program_id = _identity_hash({
                    "run_id": condition_spec["run_id"], "task_id": task_id,
                    "seed": seed, "generation_id": raw["generation_id"],
                })
                programs.append({
                    "program_id": program_id,
                    "development_layer": pairing["development_layer"],
                    "prompt_condition": condition_spec["prompt_condition"],
                    "treatment": condition_spec["treatment"],
                    "run_id": condition_spec["run_id"],
                    "task_id": task_id,
                    "seed": seed,
                    "sample_index": int(raw.get("sample_index", 0)),
                    "generation_id": raw["generation_id"],
                    "raw_sha256": raw["raw_response_sha256"],
                    "normalized_source": normalized,
                    "normalized_source_sha256": normalized_hash,
                    "normalized_source_state_sha256": _source_state_sha256(normalized),
                    "expected_entry_point": expected,
                    "expected_positional_arities": arities,
                    "generation_truncated": truncated,
                    "healer_status": result.status,
                    "healer_diagnostic": result.diagnostic,
                    "h1_source": result.output_source,
                    "h1_source_sha256": result.output_sha256,
                    "source_changed": changed,
                    "alias_only_verified": alias_verified,
                    "compile_verified": alias_verified,
                    "h0_status": evaluation["pipeline_corrected_status"],
                    "h0_pass": evaluation["pipeline_corrected_status"] == "pass",
                })

    _require(len(task_seed_identities) == 300, "task-seed identity count must be 300")
    _require(len({task for task, _ in task_seed_identities}) == 60, "development task count must be 60")
    _require(len(programs) == 600, "program count must be 600")
    _require(len({program["program_id"] for program in programs}) == 600, "duplicate program identity")
    _require(Counter(p["prompt_condition"] for p in programs) == {"p0": 300, "scaffold_like": 300}, "prompt-condition count drift")
    transformed = [p for p in programs if p["source_changed"]]
    unchanged = [p for p in programs if not p["source_changed"]]
    _require(len(transformed) == 41 and len(unchanged) == 559, "fail closed: expected exactly 41 transformed and 559 unchanged")
    _require(Counter(p["prompt_condition"] for p in transformed) == {"p0": 39, "scaffold_like": 2}, "transformed stratum count drift")
    _require(all(p["alias_only_verified"] and p["compile_verified"] for p in transformed), "transformed source validation incomplete")

    account_rows: list[dict[str, Any]] = []
    changed_rows: list[dict[str, Any]] = []
    reuse_rows: list[dict[str, Any]] = []
    for program_index, program in enumerate(programs, 1):
        account_ids = {
            arm: _identity_hash({"program_id": program["program_id"], "healer_account": arm})
            for arm in ("H0", "H1")
        }
        for arm in ("H0", "H1"):
            is_h1 = arm == "H1"
            source_hash = program["h1_source_sha256"] if is_h1 else program["normalized_source_sha256"]
            changed = bool(is_h1 and program["source_changed"])
            disposition = (
                "existing_frozen_h0_result"
                if arm == "H0"
                else "pending_manual_evalplus_changed_source"
                if changed
                else "reuse_existing_h0_by_source_state_sha256_identity"
            )
            account_rows.append({
                "program_index": program_index,
                "account_index": len(account_rows) + 1,
                "program_id": program["program_id"],
                "evaluation_account_id": account_ids[arm],
                "healer_account": arm,
                "development_layer": program["development_layer"],
                "prompt_condition": program["prompt_condition"],
                "treatment": program["treatment"],
                "run_id": program["run_id"],
                "task_id": program["task_id"],
                "seed": program["seed"],
                "sample_index": program["sample_index"],
                "generation_id": program["generation_id"],
                "raw_sha256": program["raw_sha256"],
                "normalized_source_available": str(program["normalized_source"] is not None).lower(),
                "normalized_source_sha256": program["normalized_source_sha256"] or "",
                "normalized_source_state_sha256": program["normalized_source_state_sha256"],
                "evaluation_source_sha256": source_hash or "",
                "expected_entry_point": program["expected_entry_point"],
                "expected_positional_arities": "|".join(map(str, program["expected_positional_arities"])),
                "generation_truncated": str(program["generation_truncated"]).lower(),
                "healer_candidate_id": EXPECTED_CANDIDATE_ID if is_h1 else "not_applied_control",
                "healer_rule_id": EXPECTED_RULE_ID if is_h1 else "not_applied_control",
                "healer_status": program["healer_status"] if is_h1 else "not_applied_control",
                "healer_diagnostic": program["healer_diagnostic"] if is_h1 else "not_applied_control",
                "source_changed": str(changed).lower(),
                "alias_only_verified": str(program["alias_only_verified"] if changed else False).lower(),
                "compile_verified": str(program["compile_verified"] if changed else False).lower(),
                "existing_h0_status": program["h0_status"],
                "existing_h0_pass": str(program["h0_pass"]).lower(),
                "evaluation_disposition": disposition,
                "same_generation_identity_h0_h1": "true",
                "same_raw_sha_h0_h1": "true",
                "same_normalized_sha_h0_h1": "true",
                "evaluator_used_by_healer": "false",
            })
        if program["source_changed"]:
            changed_rows.append({
                "program_id": program["program_id"],
                "evaluation_account_id": account_ids["H1"],
                "development_layer": program["development_layer"],
                "prompt_condition": program["prompt_condition"],
                "run_id": program["run_id"],
                "task_id": program["task_id"],
                "seed": program["seed"],
                "sample_index": program["sample_index"],
                "generation_id": program["generation_id"],
                "raw_sha256": program["raw_sha256"],
                "normalized_source_sha256": program["normalized_source_sha256"],
                "h1_source_sha256": program["h1_source_sha256"],
                "healer_candidate_id": EXPECTED_CANDIDATE_ID,
                "healer_rule_id": EXPECTED_RULE_ID,
                "completion": program["h1_source"],
            })
        else:
            available = program["normalized_source"] is not None
            reuse_rows.append({
                "program_id": program["program_id"],
                "h0_evaluation_account_id": account_ids["H0"],
                "h1_evaluation_account_id": account_ids["H1"],
                "development_layer": program["development_layer"],
                "prompt_condition": program["prompt_condition"],
                "run_id": program["run_id"],
                "task_id": program["task_id"],
                "seed": program["seed"],
                "generation_id": program["generation_id"],
                "raw_sha256": program["raw_sha256"],
                "normalized_source_available": str(available).lower(),
                "h0_source_sha256": program["normalized_source_sha256"] or "",
                "h1_source_sha256": program["h1_source_sha256"] or "",
                "h0_source_state_sha256": program["normalized_source_state_sha256"],
                "h1_source_state_sha256": _source_state_sha256(program["h1_source"]),
                "source_state_sha256_exact_match": "true",
                "existing_h0_output_sha256_verified": "true",
                "existing_h0_status": program["h0_status"],
                "existing_h0_pass": str(program["h0_pass"]).lower(),
                "existing_h0_result_complete": "true",
                "reuse_eligible": "true",
                "reuse_basis": "source_sha256_exact_match" if available else "canonical_pipeline_unavailable_state_sha256_exact_match",
                "reuse_independent_of_h0_pass_fail": "true",
            })

    _require(len(account_rows) == 1200, "account manifest must contain 1200 rows")
    _require(Counter(row["healer_account"] for row in account_rows) == {"H0": 600, "H1": 600}, "H0/H1 account count drift")
    _require(len(changed_rows) == 41 and len(reuse_rows) == 559, "changed/reuse output count drift")
    _require(all(row["h0_source_state_sha256"] == row["h1_source_state_sha256"] for row in reuse_rows), "unchanged source-state hash drift")
    return {
        "accounts": account_rows,
        "changed": changed_rows,
        "reuse": reuse_rows,
        "source_hashes": {path.as_posix(): _sha256_bytes((repo_root / path).read_bytes()) for path in sorted(source_paths)},
    }


def _operator_guide(manifest_sha256_placeholder: str = "<MANIFEST_SHA256>") -> bytes:
    command = (
        "/home/yehya/.venvs/ast_evalplus/bin/python "
        "scripts/run_mbpp_existing600_healer_eval.py "
        "--manifest artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/manifest.json "
        f"--manifest-sha256 {manifest_sha256_placeholder} --parallel 1 "
        "--output-dir artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/manual_evalplus_run_001"
    )
    text = f"""# 既有600份 development programs：Healer H0/H1 功能評估操作指南

本資產只涵蓋既有60題、300個task-seed identities與P0／Scaffold-like共600份Pipeline-normalized帳。H0沿用既有正式結果；H1固定使用`entrypoint_alias_unique_arity_compatible_v0`。Pipeline extraction與normalization不是Healer。

## 凍結結果

- H0帳：600；H1帳：600。
- H1實際changed：41（P0 39、Scaffold-like 2），全部通過alias-only AST與compile驗證。
- unchanged：559。只有source-state SHA-256精確相同才沿用H0；是否沿用與H0 pass/fail無關。Pipeline無可用輸出的帳以明確canonical unavailable state SHA-256核對，不虛構source bytes。
- 本準備輪沒有呼叫模型、沒有執行EvalPlus、沒有讀取或操作`mbpp_b28`。

## 唯一人工評估指令

請在repository根目錄的WSL shell中執行以下唯一一條指令；不得改變manifest、hash、interpreter、`--parallel 1`或output path：

```bash
{command}
```

Driver只評估41個changed H1 cells，拒絕其他Healer／Pipeline、identity、數量、parallel值、既有output directory與任何hash drift；它沒有generation、retry、resume、selective acceptance或overwrite功能。559格不會重新執行EvalPlus，也不會覆寫H0。

評估完成只會產出changed-H1原始結果，不會先宣告rescue或regression。之後必須另行、明確執行paired analyzer，才可依預先固定規則分類fail→fail、fail→pass、pass→fail、pass→pass，並分層列出P0與Scaffold-like。

判定固定為：regression > 0不合格；regression = 0且rescue >= 1才可進入獨立prospective qualification；兩者皆0則僅能稱靜態安全且未觀察到功能效益。不得依結果撤回個別transformation。
"""
    return text.encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo_root)
    outputs: dict[str, bytes] = {
        "h0_h1_accounts.csv": _csv_bytes(analysis["accounts"], ACCOUNT_FIELDS),
        "changed_h1_eval_input.jsonl": _jsonl_bytes(analysis["changed"]),
        "unchanged_h0_reuse_ledger.csv": _csv_bytes(analysis["reuse"], REUSE_FIELDS),
    }
    evaluation_plan = {
        "plan_id": "mbpp_existing600_healer_h0_h1_functional_evaluation_v1",
        "status": "frozen_waiting_for_manual_evalplus",
        "scope": {"development_tasks": 60, "task_seed_identities": 300, "programs": 600, "h0_accounts": 600, "h1_accounts": 600},
        "changed_h1_evalplus_cells": 41,
        "unchanged_h1_reuse_cells": 559,
        "changed_by_prompt_condition": {"p0": 39, "scaffold_like": 2},
        "interpreter": "/home/yehya/.venvs/ast_evalplus/bin/python",
        "parallel": 1,
        "evalplus_executed_during_preparation": False,
        "model_calls": 0,
        "h0_re_evaluation_or_overwrite": False,
        "reuse_gate": "exact normalized source-state SHA-256 identity plus complete verified H0 identity/result",
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "rule_order": [EXPECTED_RULE_ID],
        "healer_sha256": EXPECTED_HEALER_SHA256,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
    }
    analysis_plan = {
        "plan_id": "mbpp_existing600_healer_paired_analysis_v1",
        "input_cells": 600,
        "categories": ["fail_to_fail", "fail_to_pass_rescue", "pass_to_fail_regression", "pass_to_pass"],
        "strata": ["all", "p0", "scaffold_like"],
        "decision_rules": {
            "regression_gt_0": "healer_candidate_not_qualified",
            "regression_eq_0_and_rescue_gte_1": "eligible_for_independent_prospective_qualification",
            "regression_eq_0_and_rescue_eq_0": "statically_safe_no_observed_functional_benefit",
        },
        "per_cell_accept_revert_or_selective_use": False,
        "final_conclusion_before_all_41_changed_results": False,
    }
    outputs["evaluation_plan.json"] = _canonical_bytes(evaluation_plan)
    outputs["paired_analysis_plan.json"] = _canonical_bytes(analysis_plan)
    guide_template = _operator_guide()
    outputs["operator_guide_zh.md"] = guide_template
    manifest = {
        "manifest_version": "mbpp_existing600_healer_h0_h1_functional_evaluation_v1",
        "status": "prepared_not_executed",
        "development_only": True,
        "counts": {"tasks": 60, "task_seed_identities": 300, "programs": 600, "accounts": 1200, "h0": 600, "h1": 600, "changed": 41, "unchanged": 559},
        "changed_by_prompt_condition": {"p0": 39, "scaffold_like": 2},
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "rule_order": [EXPECTED_RULE_ID],
        "healer_sha256": EXPECTED_HEALER_SHA256,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
        "model_calls": 0,
        "evalplus_executions": 0,
        "new_generation_runs": 0,
        "source_sha256": analysis["source_hashes"],
        # The guide embeds the manifest hash, so it is deliberately outside
        # this non-circular lock set.  Its bytes remain deterministic and are
        # checked by --check through build_outputs().
        "output_sha256_excluding_manifest_and_operator_guide": {
            name: _sha256_bytes(content)
            for name, content in sorted(outputs.items())
            if name != "operator_guide_zh.md"
        },
    }
    outputs["manifest.json"] = _canonical_bytes(manifest)
    manifest_sha = _sha256_bytes(outputs["manifest.json"])
    outputs["operator_guide_zh.md"] = _operator_guide(manifest_sha)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "frozen output directory missing")
        actual = {path.name for path in output_dir.iterdir() if path.is_file()}
        _require(actual == set(outputs), "frozen output file set drift")
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
    except (PreparationError, SyntaxError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
