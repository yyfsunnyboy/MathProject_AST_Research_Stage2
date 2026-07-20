#!/usr/bin/env python3
"""Build a conservative Candidate B r003 MBPP+ failure census without evaluation."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_failure_census_v1"
)
START_HEAD = "9af07367fc3ff08b9ebe30eff1000533c4724228"
TAXONOMY_PATH = Path(
    r"C:\Users\yehya\Downloads\20260719_AI生成程式共同失敗分類標準_實際使用版_v2.md"
)
TAXONOMY_SHA256 = "7a28fcbc19cee92592639ed828c502ef79644ff6b1d71eabe2060076c81abeef"

SOURCE_HASHES = {
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv": "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/execution_manifest.json": "4ddb7beda50db18e4c6bf77484c34626c1088753fcfdb68c16e52f851f0b66f7",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json": "6a84a328307f3ce98a49933008aa18da481aae52920238b9204dcf47b1280606",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/candidate_b_h0_h1_accounts.csv": "54e05091ef35af7f99a32a5409c74f688d00c2564d31b8a52301af8d65ce360e",
    "artifacts/public_benchmark_governance/candidate_b_development60_replay_r003_v1/candidate_b_generation_cells.csv": "1e7ab332d441f0fff207f8ec80ac24379184b39387f569e2e6985c232c0effc5",
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/raw_generations.jsonl": "3d8295ff5e7260d733d8f68736a792afa79501d70ca8bde8d4dd88c1b2b002b3",
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl": "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    "artifacts/public_benchmark_governance/candidate_b_r003_formal_paired_analysis_v1/manifest.json": "88576cfd91968df9fdb92de76af031724156c0fafb37c384c8930f726fc33d86",
    "artifacts/public_benchmark_governance/candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv": "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
    "scripts/analyze_candidate_b_r003_formal_paired.py": "a5e9358fa4fc378ad3f900355e9b99ad7507237b467b1a44810eee105b8fdc53",
}

STDLIB_MODULES = {
    "array", "bisect", "collections", "copy", "datetime", "decimal", "fractions",
    "functools", "heapq", "itertools", "json", "math", "operator", "random", "re",
    "statistics", "string", "sys", "typing",
}
BUILTIN_CALLS = {
    "abs", "all", "any", "bin", "bool", "chr", "dict", "enumerate", "filter",
    "float", "frozenset", "int", "len", "list", "map", "max", "min", "next",
    "ord", "pow", "print", "range", "reversed", "round", "set", "slice", "sorted",
    "str", "sum", "tuple", "zip",
}

CENSUS_FIELDS = (
    "dataset", "task_id", "model", "condition", "seed", "program_id", "generation_id",
    "prompt_hash", "evaluator_hash", "evaluation_revision", "infrastructure_valid",
    "raw_response_present", "candidate_present", "evaluation_source_sha256",
    "evalplus_base_status", "evalplus_plus_status", "final_status", "g1_parse",
    "g2_execution", "g3_contract", "g3a_required_api", "g3c_canonical_form",
    "g4_correctness", "primary_failure_layer", "outcome_validity", "failure_subtype",
    "mechanism_tags", "failure_chain", "exception_type", "exception_message",
    "repairability_tier", "healer_eligible", "matched_rule_family", "review_status",
    "gate_evidence_scope", "machine_evidence", "negative_control", "included",
)
LAYER_VALIDITY_FIELDS = (
    "primary_failure_layer", "cells", "valid_model_outcome", "invalid_evaluator",
    "invalid_contract", "invalid_infrastructure", "pending_review", "pass_cells", "fail_cells",
)
ELIGIBILITY_FIELDS = (
    "repairability_tier", "healer_eligible", "cells", "unique_tasks", "fail_cells",
)
RULE_FIELDS = (
    "rule_family", "repairability_tier", "supported_cells", "unique_tasks",
    "public_contract_evidence", "source_ast_observables", "safety_guards", "ambiguities",
    "regression_risk", "current_healer_status", "implementation_status",
)
REVIEW_FIELDS = (
    "review_rank", "program_id", "task_id", "seed", "machine_bucket",
    "repairability_tier", "outcome_validity", "selection_basis", "review_question",
    "ast_evidence", "evalplus_base_status", "evalplus_plus_status",
    "evaluation_source_sha256", "source_in_queue", "manual_evidence_reviewed",
    "representative_review_disposition",
)


class CensusError(RuntimeError):
    """Raised before output on provenance, identity, or completeness drift."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CensusError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verify_bytes(data: bytes, expected: str, label: str) -> None:
    _require(_sha(data) == expected, f"hash drift: {label}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _index_unique(rows: Iterable[dict[str, Any]], field: str, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row[field])
        _require(key not in indexed, f"duplicate identity in {label}: {key}")
        indexed[key] = row
    return indexed


def _require_exact_keys(actual: set[str], expected: set[str], label: str) -> None:
    _require(actual == expected, f"missing or unexpected identity in {label}")


def _identity_hash(value: Any) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


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
            and node.func.id not in BUILTIN_CALLS
        )
    names = {call.func.id for call in calls}
    _require(len(names) == 1, "public prompt entry-point contract drift")
    entry = next(iter(names))
    arities = tuple(sorted({len(call.args) for call in calls if call.func.id == entry and not call.keywords}))
    _require(bool(arities), "public prompt arity contract missing")
    return entry, arities


def _function_accepts(function: ast.FunctionDef | ast.AsyncFunctionDef, arities: tuple[int, ...]) -> bool:
    positional = len(function.args.posonlyargs) + len(function.args.args)
    minimum = positional - len(function.args.defaults)
    maximum: int | None = None if function.args.vararg else positional
    return all(arity >= minimum and (maximum is None or arity <= maximum) for arity in arities)


def _function_has_value_return(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    class ReturnVisitor(ast.NodeVisitor):
        def __init__(self, root: ast.AST) -> None:
            self.root = root
            self.found = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node is self.root:
                self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node is self.root:
                self.generic_visit(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_Return(self, node: ast.Return) -> None:
            if node.value is not None:
                self.found = True

        def visit_Yield(self, node: ast.Yield) -> None:
            self.found = True

        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            self.found = True

    visitor = ReturnVisitor(function)
    visitor.visit(function)
    return visitor.found


def _bound_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Param)):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def _missing_stdlib_modules(tree: ast.Module) -> list[str]:
    bound = _bound_names(tree)
    used = {
        node.value.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and isinstance(node.value.ctx, ast.Load)
        and node.value.id in STDLIB_MODULES
    }
    return sorted(used - bound)


def _ast_fingerprint(tree: ast.Module) -> dict[str, Any]:
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    recursive = any(
        isinstance(call.func, ast.Name) and call.func.id == function.name
        for function in functions for call in ast.walk(function) if isinstance(call, ast.Call)
    )
    return {
        "top_level_functions": len(functions),
        "imports": sum(isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body),
        "loops": sum(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree)),
        "calls": len(calls),
        "recursive": recursive,
    }


def _classify(
    *, source: str | None, passed: bool, entry: str, arities: tuple[int, ...],
    generation_truncated: bool, raw_strict: bool,
) -> dict[str, Any]:
    base = {
        "exception_type": "", "exception_message": "", "failure_chain": [],
        "matched_rule_family": "", "healer_eligible": False,
    }
    if source is None:
        return {**base, "final_status": "FAILED", "g1_parse": "NOT_ASSESSED", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "NOT_ASSESSED", "g4_correctness": "NOT_ASSESSED",
                "primary_failure_layer": "L0", "outcome_validity": "INVALID_INFRASTRUCTURE",
                "failure_subtype": "MISSING_EVALUATION_SOURCE", "mechanism_tags": ["infrastructure_failure"],
                "repairability_tier": "INELIGIBLE", "review_status": "machine_classified",
                "gate_evidence_scope": "source_missing", "machine_evidence": {"candidate_present": False}}
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, OverflowError) as exc:
        return {**base, "final_status": "FAILED", "g1_parse": "FAIL", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "NOT_ASSESSED", "g4_correctness": "NOT_ASSESSED",
                "primary_failure_layer": "L1", "outcome_validity": "VALID_MODEL_OUTCOME",
                "failure_subtype": "PYTHON_PARSE_FAILURE", "mechanism_tags": ["model_assembly_failure"],
                "exception_type": type(exc).__name__, "exception_message": str(exc).splitlines()[0][:160],
                "repairability_tier": "CANDIDATE_REVIEW", "review_status": "pending_representative_review",
                "gate_evidence_scope": "direct_ast_parse",
                "machine_evidence": {"raw_strict_python_only": raw_strict,
                                     "parse_exception_type": type(exc).__name__,
                                     "parse_exception_message": str(exc).splitlines()[0][:160]}}

    fingerprint = _ast_fingerprint(tree)
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    expected = [function for function in functions if function.name == entry]
    compatible_aliases = [function.name for function in functions if function.name != entry and _function_accepts(function, arities)]
    missing_modules = _missing_stdlib_modules(tree)
    evidence = {
        **fingerprint, "expected_entry_point_present": bool(expected),
        "expected_arities": list(arities), "compatible_alias_count": len(compatible_aliases),
        "missing_stdlib_modules": missing_modules, "generation_truncated": generation_truncated,
        "raw_strict_python_only": raw_strict,
    }
    if passed:
        return {**base, "final_status": "PASSED", "g1_parse": "PASS", "g2_execution": "PASS",
                "g3_contract": "PASS", "g4_correctness": "PASS", "primary_failure_layer": "PASSED",
                "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "NEGATIVE_CONTROL_PASS",
                "mechanism_tags": [], "repairability_tier": "INELIGIBLE", "review_status": "negative_control",
                "gate_evidence_scope": "formal_evalplus_pass", "machine_evidence": evidence}
    if generation_truncated:
        return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "NOT_ASSESSED", "g4_correctness": "NOT_ASSESSED", "primary_failure_layer": "L1",
                "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "GENERATION_TRUNCATED",
                "mechanism_tags": ["model_assembly_failure"], "repairability_tier": "CANDIDATE_REVIEW",
                "review_status": "pending_representative_review", "gate_evidence_scope": "generation_metadata_plus_ast",
                "machine_evidence": evidence}
    if not expected:
        if len(compatible_aliases) == 1:
            return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                    "g3_contract": "FAIL", "g4_correctness": "NOT_ASSESSED", "primary_failure_layer": "L2",
                    "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS",
                    "mechanism_tags": ["output_packaging"], "repairability_tier": "ELIGIBLE_EXACT",
                    "healer_eligible": True, "matched_rule_family": "ENTRYPOINT_ALIAS_UNIQUE_ARITY_COMPATIBLE_V0",
                    "review_status": "machine_classified_existing_v0", "gate_evidence_scope": "public_contract_plus_ast",
                    "machine_evidence": evidence}
        tier = "CANDIDATE_REVIEW" if compatible_aliases else "INELIGIBLE"
        return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "FAIL", "g4_correctness": "NOT_ASSESSED", "primary_failure_layer": "L2",
                "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "REQUIRED_FUNCTION_MISSING_AMBIGUOUS",
                "mechanism_tags": ["output_packaging", "needs_human_review"], "repairability_tier": tier,
                "review_status": "pending_representative_review" if tier == "CANDIDATE_REVIEW" else "machine_ineligible",
                "gate_evidence_scope": "public_contract_plus_ast", "machine_evidence": evidence}
    if not any(_function_accepts(function, arities) for function in expected):
        return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "FAIL", "g4_correctness": "NOT_ASSESSED", "primary_failure_layer": "L2",
                "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "REQUIRED_SIGNATURE_INCOMPATIBLE",
                "mechanism_tags": ["output_packaging", "needs_human_review"], "repairability_tier": "CANDIDATE_REVIEW",
                "review_status": "pending_representative_review", "gate_evidence_scope": "public_contract_plus_ast",
                "machine_evidence": evidence}
    if not any(_function_has_value_return(function) for function in expected):
        return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "FAIL", "g4_correctness": "NOT_ASSESSED", "primary_failure_layer": "L2",
                "outcome_validity": "VALID_MODEL_OUTCOME", "failure_subtype": "RETURN_CONTRACT_NO_VALUE_OBSERVED",
                "mechanism_tags": ["output_packaging"], "repairability_tier": "INELIGIBLE",
                "review_status": "machine_ineligible", "gate_evidence_scope": "public_assert_contract_plus_ast",
                "machine_evidence": evidence}
    if missing_modules:
        return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
                "g3_contract": "PASS", "g4_correctness": "FAIL", "primary_failure_layer": "UNRESOLVED",
                "outcome_validity": "PENDING_REVIEW", "failure_subtype": "L4_MISSING_STDLIB_IMPORT_CANDIDATE",
                "mechanism_tags": ["model_assembly_failure", "needs_human_review"],
                "repairability_tier": "CANDIDATE_REVIEW", "review_status": "pending_representative_review",
                "matched_rule_family": "STDLIB_MODULE_IMPORT_GUARDED_CANDIDATE",
                "gate_evidence_scope": "aggregate_evalplus_plus_static_candidate", "machine_evidence": evidence}
    return {**base, "final_status": "FAILED", "g1_parse": "PASS", "g2_execution": "NOT_ASSESSED",
            "g3_contract": "PASS", "g4_correctness": "FAIL", "primary_failure_layer": "UNRESOLVED",
            "outcome_validity": "PENDING_REVIEW", "failure_subtype": "AGGREGATE_EVALPLUS_FAILURE_NO_DIAGNOSTIC",
            "mechanism_tags": ["needs_human_review"], "repairability_tier": "UNRESOLVED",
            "review_status": "pending_representative_review", "gate_evidence_scope": "aggregate_evalplus_only",
            "machine_evidence": evidence}


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_analysis(repo_root: Path = REPO_ROOT, taxonomy_path: Path = TAXONOMY_PATH) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    taxonomy_path = taxonomy_path.resolve()
    _require(taxonomy_path.is_file(), "taxonomy v2 attachment missing")
    _verify_bytes(taxonomy_path.read_bytes(), TAXONOMY_SHA256, "taxonomy v2 attachment")
    observed_hashes: dict[str, str] = {}
    for relative, expected in SOURCE_HASHES.items():
        path = repo_root / relative
        _require(path.is_file(), f"source missing: {relative}")
        data = path.read_bytes()
        _verify_bytes(data, expected, relative)
        observed_hashes[relative] = _sha(data)

    governance = repo_root / "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1"
    run_dir = repo_root / "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003"
    accounts = [row for row in _read_csv(governance / "candidate_b_h0_h1_accounts.csv") if row["healer_account"] == "H0"]
    results = [row for row in _read_csv(governance / "manual_evalplus_run_001/evalplus_results.csv") if row["healer_account"] == "H0"]
    materialized = [row for row in _read_jsonl(run_dir / "h0_h1_accounts.jsonl") if row["healer_account"] == "H0"]
    raw = _read_jsonl(run_dir / "raw_generations.jsonl")
    generation_cells = _read_csv(repo_root / "artifacts/public_benchmark_governance/candidate_b_development60_replay_r003_v1/candidate_b_generation_cells.csv")
    for label, rows in (("H0 accounts", accounts), ("H0 results", results), ("H0 materialized", materialized), ("raw generations", raw), ("generation cells", generation_cells)):
        _require(len(rows) == 300, f"{label} row count must be 300")
    account_by_program = _index_unique(accounts, "program_id", "H0 accounts")
    result_by_program = _index_unique(results, "program_id", "H0 results")
    materialized_by_program = _index_unique(materialized, "program_id", "H0 materialized")
    raw_by_program = _index_unique(raw, "program_id", "raw generations")
    generation_by_program = _index_unique(generation_cells, "program_id", "generation cells")
    program_ids = set(account_by_program)
    for label, index in (("results", result_by_program), ("materialized", materialized_by_program), ("raw", raw_by_program), ("generation", generation_by_program)):
        _require_exact_keys(set(index), program_ids, label)

    execution = _read_json(governance / "manual_evalplus_run_001/execution_manifest.json")
    manifest = _read_json(governance / "manifest.json")
    _require(execution["candidate_b_h0_cells_evaluated"] == 300, "formal H0 evaluation count drift")
    _require(execution["results_sha256"] == SOURCE_HASHES["artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv"], "result binding drift")
    _require(manifest["r001_r002_used_as_result_source"] is False, "r001/r002 result-source policy drift")

    evaluator_hash = "sha256:" + SOURCE_HASHES["artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json"]
    rows: list[dict[str, Any]] = []
    for program_id in sorted(program_ids):
        account, result = account_by_program[program_id], result_by_program[program_id]
        source_row, raw_row, generation = materialized_by_program[program_id], raw_by_program[program_id], generation_by_program[program_id]
        for field in ("evaluation_account_id", "run_id", "task_id", "seed", "generation_id", "evaluation_source_sha256"):
            _require(str(account[field]) == str(result[field]) == str(source_row[field]), f"joined provenance drift: {field} {program_id}")
        _require(account["raw_response_sha256"] == raw_row["raw_response_sha256"] == source_row["raw_response_sha256"], "raw response SHA drift")
        _verify_bytes(raw_row["raw_response"].encode("utf-8"), raw_row["raw_response_sha256"], f"raw bytes {program_id}")
        source = source_row.get("evaluation_source")
        _require(isinstance(source, str) and source, "Candidate B evaluation source missing")
        _verify_bytes(source.encode("utf-8"), source_row["evaluation_source_sha256"], f"evaluation source bytes {program_id}")
        prompt = raw_row["request"]["messages"][0]["content"]
        _verify_bytes(prompt.encode("utf-8"), raw_row["composed_prompt_sha256"], f"prompt bytes {program_id}")
        entry, arities = _prompt_contract(prompt)
        _require(
            _identity_hash({"entry_point": entry, "positional_arities": arities}) == generation["prompt_contract_sha256"],
            f"public prompt contract hash drift: {program_id}",
        )
        passed = result["evalplus_pass"] == "true"
        _require(result["evalplus_pass"] in {"true", "false"}, "invalid formal pass result")
        done_reason = str(raw_row.get("generation_metadata", {}).get("done_reason", ""))
        classified = _classify(
            source=source, passed=passed, entry=entry, arities=arities,
            generation_truncated=done_reason == "length", raw_strict=raw_row["strict_python_only"] is True,
        )
        rows.append({
            "dataset": "MBPP+", "task_id": account["task_id"], "model": "qwen3.5:9b",
            "condition": "Candidate_B_H0", "seed": account["seed"], "program_id": program_id,
            "generation_id": account["generation_id"], "prompt_hash": "sha256:" + raw_row["composed_prompt_sha256"],
            "evaluator_hash": evaluator_hash, "evaluation_revision": "manual_evalplus_run_001_original",
            "infrastructure_valid": "true", "raw_response_present": "true", "candidate_present": "true",
            "evaluation_source_sha256": source_row["evaluation_source_sha256"],
            "evalplus_base_status": result["base_status"], "evalplus_plus_status": result["plus_status"],
            "final_status": classified["final_status"], "g1_parse": classified["g1_parse"],
            "g2_execution": classified["g2_execution"], "g3_contract": classified["g3_contract"],
            "g3a_required_api": "NOT_APPLICABLE", "g3c_canonical_form": "NOT_APPLICABLE",
            "g4_correctness": classified["g4_correctness"],
            "primary_failure_layer": classified["primary_failure_layer"],
            "outcome_validity": classified["outcome_validity"], "failure_subtype": classified["failure_subtype"],
            "mechanism_tags": json.dumps(classified["mechanism_tags"], separators=(",", ":")),
            "failure_chain": json.dumps(classified["failure_chain"], separators=(",", ":")),
            "exception_type": classified["exception_type"], "exception_message": classified["exception_message"],
            "repairability_tier": classified["repairability_tier"],
            "healer_eligible": str(classified["healer_eligible"]).lower(),
            "matched_rule_family": classified["matched_rule_family"], "review_status": classified["review_status"],
            "gate_evidence_scope": classified["gate_evidence_scope"],
            "machine_evidence": json.dumps(classified["machine_evidence"], sort_keys=True, separators=(",", ":")),
            "negative_control": str(passed).lower(), "included": "true",
        })
    _require(len(rows) == len({row["program_id"] for row in rows}) == 300, "300-program census completeness drift")
    _require(sum(row["final_status"] == "PASSED" for row in rows) == 76, "pass count must be 76")
    _require(sum(row["final_status"] == "FAILED" for row in rows) == 224, "fail count must be 224")
    pairs = {(row["task_id"], row["seed"]) for row in rows}
    _require(len(pairs) == 300 and len({task for task, _ in pairs}) == 60, "60x5 identity completeness drift")
    _require({seed for _, seed in pairs} == {"11", "22", "33", "44", "55"}, "seed identity drift")

    layer_validity = []
    for layer in ("PASSED", "L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"):
        subset = [row for row in rows if row["primary_failure_layer"] == layer]
        layer_validity.append({
            "primary_failure_layer": layer, "cells": len(subset),
            "valid_model_outcome": sum(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in subset),
            "invalid_evaluator": sum(row["outcome_validity"] == "INVALID_EVALUATOR" for row in subset),
            "invalid_contract": sum(row["outcome_validity"] == "INVALID_CONTRACT" for row in subset),
            "invalid_infrastructure": sum(row["outcome_validity"] == "INVALID_INFRASTRUCTURE" for row in subset),
            "pending_review": sum(row["outcome_validity"] == "PENDING_REVIEW" for row in subset),
            "pass_cells": sum(row["final_status"] == "PASSED" for row in subset),
            "fail_cells": sum(row["final_status"] == "FAILED" for row in subset),
        })
    eligibility = []
    eligibility_counts = Counter((row["repairability_tier"], row["healer_eligible"]) for row in rows)
    for (tier, eligible), count in sorted(eligibility_counts.items()):
        subset = [row for row in rows if row["repairability_tier"] == tier and row["healer_eligible"] == eligible]
        eligibility.append({"repairability_tier": tier, "healer_eligible": eligible, "cells": count,
                            "unique_tasks": len({row["task_id"] for row in subset}),
                            "fail_cells": sum(row["final_status"] == "FAILED" for row in subset)})

    family_specs = [
        ("ENTRYPOINT_ALIAS_UNIQUE_ARITY_COMPATIBLE_V0", "ELIGIBLE_EXACT", "required function name and public assert arities", "expected name absent; exactly one compatible top-level function", "valid identifiers; unique function; arity compatible; expected name unbound; parse after alias", "candidate function may still be semantically wrong", "low syntax/packaging risk; observed functional rescue may remain zero", "existing_production_v0"),
        ("STDLIB_MODULE_IMPORT_GUARDED_CANDIDATE", "CANDIDATE_REVIEW", "no hidden tests or answers; source/AST only", "known stdlib module used as attribute while unbound and unimported", "known stdlib allowlist; module unbound in all scopes; import-only edit; compile and full regression evaluation required", "execution path may not reach use; dynamic bindings or shadowing may exist", "medium; import can alter name resolution or hide deeper semantic failure", "not_implemented"),
        ("PARSE_OR_TRUNCATION_MECHANICAL_REVIEW", "CANDIDATE_REVIEW", "generation metadata and parser diagnostics only", "parse failure or length termination", "only deterministic token-level completion with unique closure; otherwise abstain", "intended continuation is generally unknowable", "high unless repair is uniquely mechanical", "not_implemented"),
        ("SIGNATURE_CONTRACT_REVIEW", "CANDIDATE_REVIEW", "required function and arities from public assertions", "required name present but observed signature incompatible, or missing name is ambiguous", "no parameter reordering/default synthesis without public evidence; compile and regression evaluation required", "parameter semantics cannot be inferred from arity alone", "high; may change intended semantics", "not_implemented"),
    ]
    rules: list[dict[str, Any]] = []
    for family, tier, contract, observable, guards, ambiguity, risk, status in family_specs:
        subset = [row for row in rows if row["matched_rule_family"] == family]
        if family == "PARSE_OR_TRUNCATION_MECHANICAL_REVIEW":
            subset = [row for row in rows if row["failure_subtype"] in {"PYTHON_PARSE_FAILURE", "GENERATION_TRUNCATED"}]
        if family == "SIGNATURE_CONTRACT_REVIEW":
            subset = [row for row in rows if row["failure_subtype"] in {"REQUIRED_FUNCTION_MISSING_AMBIGUOUS", "REQUIRED_SIGNATURE_INCOMPATIBLE"} and row["repairability_tier"] == "CANDIDATE_REVIEW"]
        rules.append({"rule_family": family, "repairability_tier": tier, "supported_cells": len(subset),
                      "unique_tasks": len({row["task_id"] for row in subset}), "public_contract_evidence": contract,
                      "source_ast_observables": observable, "safety_guards": guards, "ambiguities": ambiguity,
                      "regression_risk": risk, "current_healer_status": status,
                      "implementation_status": "evidence_only_no_rule_change"})

    repair_strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    exact_rows = [row for row in rows if row["repairability_tier"] == "ELIGIBLE_EXACT"]
    for row in rows:
        if row["repairability_tier"] != "CANDIDATE_REVIEW":
            continue
        repair_strata[(row["failure_subtype"], row["exception_type"])].append(row)
    review_candidates = list(exact_rows)
    for key in sorted(repair_strata):
        review_candidates.extend(sorted(repair_strata[key], key=lambda row: row["program_id"])[:3])
    generic = [row for row in rows if row["repairability_tier"] == "UNRESOLVED"]
    strata: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in generic:
        evidence = json.loads(row["machine_evidence"])
        key = (row["evalplus_base_status"], row["evalplus_plus_status"], str(evidence["top_level_functions"]), str(evidence["recursive"]))
        strata[key].append(row)
    representatives = []
    for key in sorted(strata):
        representatives.append(sorted(strata[key], key=lambda row: row["program_id"])[0])
    representatives = representatives[:12]
    selected = {row["program_id"]: row for row in review_candidates + representatives}
    review_rows = []
    for rank, row in enumerate(sorted(selected.values(), key=lambda item: (item["repairability_tier"], item["failure_subtype"], item["program_id"])), 1):
        if row["repairability_tier"] == "ELIGIBLE_EXACT":
            disposition = "retain_existing_v0_evidence_only_no_new_rule; formal changed H1 was fail_to_fail"
        elif row["failure_subtype"] in {"PYTHON_PARSE_FAILURE", "GENERATION_TRUNCATED"}:
            disposition = "do_not_automate_without_unique_mechanical_completion; ambiguity remains"
        elif row["failure_subtype"] in {"REQUIRED_FUNCTION_MISSING_AMBIGUOUS", "REQUIRED_SIGNATURE_INCOMPATIBLE"}:
            disposition = "defer; arity alone cannot establish parameter semantics"
        else:
            disposition = "remain pending; aggregate EvalPlus status cannot separate runtime from semantic failure"
        review_rows.append({"review_rank": rank, "program_id": row["program_id"], "task_id": row["task_id"],
                            "seed": row["seed"], "machine_bucket": row["failure_subtype"],
                            "repairability_tier": row["repairability_tier"], "outcome_validity": row["outcome_validity"],
                            "selection_basis": "feature_stratum_then_program_id_not_task_or_answer",
                            "review_question": "Can public-contract and AST evidence establish a general guarded repair without reconstructing the answer?",
                            "ast_evidence": row["machine_evidence"], "evalplus_base_status": row["evalplus_base_status"],
                            "evalplus_plus_status": row["evalplus_plus_status"],
                            "evaluation_source_sha256": row["evaluation_source_sha256"], "source_in_queue": "false",
                            "manual_evidence_reviewed": "true", "representative_review_disposition": disposition})
    return {"rows": rows, "layer_validity": layer_validity, "eligibility": eligibility, "rules": rules,
            "review_rows": review_rows, "observed_hashes": observed_hashes}


def _adapter() -> bytes:
    text = f"""# AI生成程式共同失敗分類標準 v2：MBPP+ adapter

## 身分與範圍

- 上位 taxonomy：`20260719_AI生成程式共同失敗分類標準_實際使用版_v2.md`
- 上位 taxonomy SHA-256：`{TAXONOMY_SHA256}`
- 適用範圍：Candidate B r003 development60 的 300 個 H0 programs。
- 本 adapter 只使用公開 prompt contract、evaluation source、AST、generation metadata 與既有 frozen EvalPlus pass/base/plus status；不使用答案、task-specific patch 或 hidden tests。

## MBPP+ gate 對應

| Gate | MBPP+ adapter |
|---|---|
| G1 | `ast.parse(evaluation_source)`；失敗為 L1。 |
| G2 | frozen 結果沒有逐格 exception traceback；除正式 PASS 外，不由 aggregate FAIL 猜測 execution gate。 |
| G3 | 公開 prompt assertions 提供 required function name、觀察 arity與return-use contract；缺函式、signature不相容或沒有 value return 為 L2。 |
| G3a | `NOT_APPLICABLE`：MBPP+ 本輪沒有事前 required Domain API。 |
| G3c | `NOT_APPLICABLE`：MBPP+ 以函式測試通過為準，沒有 canonical-form gate。 |
| G4 | 使用既有 frozen EvalPlus 結果，不重跑；aggregate FAIL 若無更早層證據，維持 `UNRESOLVED`。 |

`evaluator_hash` 欄位使用 frozen evaluation manifest SHA-256 作治理身分；該 manifest 綁定
EvalPlus `0.3.1` 與 `evalplus_0.3.1_check_correctness_subset`。Repository 沒有凍結 EvalPlus
package source hash，因此此欄不可誤稱為 evaluator package code hash；這項 provenance 限制保留在報告中。

## L0–L5 與保守規則

- L0：缺 raw/candidate/result 或來源身分不完整；`INVALID_INFRASTRUCTURE`，不送 Healer。
- L1：evaluation source 無法 parse，或 fail cell 有明確 length truncation；僅機械且唯一的修復才可 review。
- L2：required function、signature、return contract 或 packaging 的公開契約失敗。
- L3：僅 Domain API；本輪一般 MBPP+ 為 N/A，不因缺一般標準函式庫 import 改標 L3。
- L4：runtime/data-flow/缺標準函式庫 import。缺 import 只有靜態候選證據時標 `UNRESOLVED + CANDIDATE_REVIEW`，沒有 traceback 不直接定案 L4。
- L5：必須先有 G1/G2/G3 完整證據才可標。aggregate EvalPlus FAIL、甚至 base-pass/plus-fail，都不足以排除 plus input 下的 runtime failure，因此不得默認 L5。
- 證據不足：`primary_failure_layer=UNRESOLVED`、`outcome_validity=PENDING_REVIEW`。
- 76 個 formal PASS 作 negative controls，保留 `PASSED` 而不塞入 L0–L5。

## repairability_tier

- `ELIGIBLE_EXACT`：公開 contract + AST 可唯一決定的既有 entry-point alias guard。
- `CANDIDATE_REVIEW`：有一般性機械候選，但仍需人工與 regression 評估；本輪不實作。
- `INELIGIBLE`：PASS、L0、語義/return重建或其他越界情況。
- `UNRESOLVED`：尚無足夠證據決定失敗層或修復資格。

## 人工 review 邊界

Queue 只含 AST/contract 特徵與 hash，不含 source。代表案例由 feature stratum 後依 program_id 決定，不以 task_id、答案或 hidden tests 選擇或設計修法。任何 candidate family 都只是 development evidence；`healer_rules_modified=false`。
"""
    return text.encode("utf-8")


def _report(result: dict[str, Any]) -> bytes:
    rows = result["rows"]
    layer_counter = Counter(row["primary_failure_layer"] for row in rows)
    layers = {layer: layer_counter[layer] for layer in ("PASSED", "L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED")}
    validity = Counter(row["outcome_validity"] for row in rows)
    tiers = Counter(row["repairability_tier"] for row in rows)
    subtype = Counter(row["failure_subtype"] for row in rows if row["final_status"] == "FAILED")
    rule_lines = "\n".join(
        f"- `{row['rule_family']}`：{row['supported_cells']} cells／{row['unique_tasks']} tasks；{row['repairability_tier']}；{row['regression_risk']}。"
        for row in result["rules"]
    )
    text = f"""# Candidate B r003 failure census（development60）

## 範圍與方法

本 census 完整納入 Candidate B r003 的 300 個 H0 programs：76 pass 作 negative controls，224 fail 進入失敗 census。分析以程式批次讀取 evaluation source 並建立 AST 特徵；本報告與 CSV 不輸出 source，也沒有逐格複述程式。沒有呼叫模型、沒有重跑 EvalPlus、沒有讀取 r001/r002 response、沒有操作 untouched20 validation。

逐格 `evaluator_hash` 使用 frozen evaluation manifest SHA-256 作治理身分，該 manifest 綁定 EvalPlus 0.3.1 與 evaluator engine；repository 未凍結 package source hash，因此不能把此值解讀為 evaluator package code hash。

## 保守分類結果

Primary layer/count：`{json.dumps(layers, ensure_ascii=False)}`。

Outcome validity/count：`{json.dumps(dict(sorted(validity.items())), ensure_ascii=False)}`。

Failure subtype/count：`{json.dumps(dict(sorted(subtype.items())), ensure_ascii=False)}`。

只有公開 contract 與 AST 能直接證明的 parse/required-function/signature/return 問題才定案 L1/L2。缺標準函式庫 import 但沒有 traceback 的格子只列為 L4 candidate，不直接定案；其餘 aggregate EvalPlus failures 維持 `UNRESOLVED/PENDING_REVIEW`。尤其 base-pass/plus-fail 不能自動視為 L5，因為 plus input 下仍可能發生 runtime/data-flow failure。

## Healer eligibility

Repairability tier/count：`{json.dumps(dict(sorted(tiers.items())), ensure_ascii=False)}`。

`ELIGIBLE_EXACT` 只代表既有 v0 entry-point alias guard 的公開契約/AST資格，不代表功能 rescue；r003 正式 paired analysis 已顯示兩個 changed windows 均 fail→fail。本輪沒有修改或新增任何 Healer rule。

## Candidate rule families

{rule_lines}

這些 families 不使用答案、task-specific knowledge 或 hidden tests。缺 import family 仍有 execution-path、dynamic binding、shadowing與深層語義錯誤風險；signature/parse repair 的語義歧義更高，均不可直接升為 production rule。

## Human review queue

Queue 共 {len(result['review_rows'])} 個代表案例，只提供公開 contract/AST evidence、EvalPlus aggregate status 與 source hash，不包含 source。選樣規則是 feature stratum 後依 program_id，並非依 task_id 或答案挑選。未取得 traceback 或更完整 gate evidence 的案例維持 `PENDING_REVIEW`，沒有為湊齊分類而猜成 L5。

## 治理結論

本 census 可定位少量明確 contract/packaging failures，並提出需獨立評估的 guarded rule families；但大多數 formal failures 缺少逐格 execution diagnostics，不能可靠拆成 L4 與 L5。結論只屬 development evidence，不授權修改 Prompt、Pipeline、Healer v0，亦不授權實作 Healer v1 或啟動 validation。

- model_calls=0
- evalplus_executions=0
- healer_rules_modified=false
- validation_not_executed=true
"""
    return text.encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT, taxonomy_path: Path = TAXONOMY_PATH) -> dict[Path, bytes]:
    result = build_analysis(repo_root, taxonomy_path)
    subtype_rows = []
    for subtype, count in sorted(Counter(row["failure_subtype"] for row in result["rows"]).items()):
        subset = [row for row in result["rows"] if row["failure_subtype"] == subtype]
        subtype_rows.append({"failure_subtype": subtype, "cells": count, "unique_tasks": len({row["task_id"] for row in subset}),
                             "primary_layers": "|".join(sorted({row["primary_failure_layer"] for row in subset})),
                             "repairability_tiers": "|".join(sorted({row["repairability_tier"] for row in subset}))})
    source_ledger = [{"path": path, "role": "frozen_repo_input", "expected_sha256": expected,
                      "observed_sha256": result["observed_hashes"][path], "verified": "true"}
                     for path, expected in sorted(SOURCE_HASHES.items())]
    source_ledger.append({"path": str(taxonomy_path), "role": "external_taxonomy_v2_attachment",
                          "expected_sha256": TAXONOMY_SHA256, "observed_sha256": TAXONOMY_SHA256, "verified": "true"})
    outputs: dict[Path, bytes] = {
        Path("mbpp_plus_taxonomy_adapter_zh.md"): _adapter(),
        Path("candidate_b_r003_failure_census.csv"): _csv_bytes(result["rows"], CENSUS_FIELDS),
        Path("layer_validity_summary.csv"): _csv_bytes(result["layer_validity"], LAYER_VALIDITY_FIELDS),
        Path("healer_eligibility_summary.csv"): _csv_bytes(result["eligibility"], ELIGIBILITY_FIELDS),
        Path("failure_subtype_summary.csv"): _csv_bytes(subtype_rows, ("failure_subtype", "cells", "unique_tasks", "primary_layers", "repairability_tiers")),
        Path("candidate_rule_families.csv"): _csv_bytes(result["rules"], RULE_FIELDS),
        Path("human_review_queue.csv"): _csv_bytes(result["review_rows"], REVIEW_FIELDS),
        Path("failure_census_report_zh.md"): _report(result),
        Path("source_hash_ledger.csv"): _csv_bytes(source_ledger, ("path", "role", "expected_sha256", "observed_sha256", "verified")),
        Path("execution_manifest.json"): _json_bytes({
            "status": "candidate_b_r003_failure_census_complete_development_only",
            "analyzer": "scripts/analyze_candidate_b_r003_failure_census.py", "programs": 300,
            "pass_negative_controls": 76, "fail_census_cells": 224, "tasks": 60, "seeds_per_task": 5,
            "taxonomy_attachment_sha256": TAXONOMY_SHA256, "batch_ast_analysis": True,
            "full_sources_emitted": False, "task_id_answer_or_hidden_tests_used_for_rule_design": False,
            "manual_representative_ast_evidence_reviewed": True,
            "model_calls": 0, "evalplus_executions": 0, "healer_rules_modified": False,
            "validation_not_executed": True, "r001_r002_responses_read": False,
        }),
        Path("provenance.json"): _json_bytes({
            "analysis_version": "candidate_b_r003_failure_census_v1", "start_head": START_HEAD,
            "candidate_response_source": "r003_only", "development_replay_only": True,
            "taxonomy_source_sha256": TAXONOMY_SHA256, "evaluation_source": "frozen_manual_evalplus_run_001",
            "manual_source_review_in_agent_context": False,
            "manual_representative_ast_evidence_reviewed": True,
            "review_queue_contains_source": False, "cell_exclusions": 0, "post_result_rule_changes": False,
        }),
    }
    manifest = {
        "manifest_version": "candidate_b_r003_failure_census_v1", "status": "complete_development_only",
        "programs": 300, "pass_negative_controls": 76, "fail_census_cells": 224,
        "tasks": 60, "seeds": [11, 22, 33, 44, 55],
        "layer_counts": {layer: sum(row["primary_failure_layer"] == layer for row in result["rows"])
                         for layer in ("PASSED", "L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED")},
        "validity_counts": dict(sorted(Counter(row["outcome_validity"] for row in result["rows"]).items())),
        "repairability_counts": dict(sorted(Counter(row["repairability_tier"] for row in result["rows"]).items())),
        "human_review_queue_cells": len(result["review_rows"]),
        "model_calls": 0, "evalplus_executions": 0, "healer_rules_modified": False,
        "validation_not_executed": True,
        "outputs_sha256_excluding_manifest": {path.as_posix(): _sha(content) for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())},
    }
    outputs[Path("manifest.json")] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, taxonomy_path: Path = TAXONOMY_PATH) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root, taxonomy_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, content in outputs.items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing deterministic output drift: {relative}")
        else:
            path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--taxonomy-path", type=Path, default=TAXONOMY_PATH)
    args = parser.parse_args()
    write_outputs(args.repo_root, args.taxonomy_path)
    print(json.dumps({"status": "complete", "programs": 300, "passes": 76, "failures": 224}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
