#!/usr/bin/env python3
"""Build deterministic Milestone 2G integrated MBPP+ development evidence."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_mbpp_scaffold_healer_evidence_packets as evidence  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/milestone_2g_integrated_development_evidence"
)
EXPECTED_HEAD = "af3ccfd7af7308d67264bcfe57ce4a0696349772"
DECISION = "PROCEED_TO_NARROW_HEALER_AND_SCAFFOLD_DESIGN"
SEEDS = [11, 22, 33, 44, 55]

DISCOVERY_P0 = Path(
    "artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/"
    "mbpp_qwen35_9b_ab1_dev_run_003"
)
DISCOVERY_SCAFFOLD = Path("artifacts/pbd/mbpp_sv0/r002")
EXPANSION_P0 = Path("artifacts/pbd/mbpp_e40/p0/r001")
EXPANSION_CANDIDATE = Path("artifacts/pbd/mbpp_e40/ca/r002")

M1C = DISCOVERY_P0 / "milestone_1c_failure_census/failure_census.csv"
M1D = DISCOVERY_P0 / "milestone_1d_evidence_review/failure_signature_clusters.csv"
M2B = DISCOVERY_SCAFFOLD / "milestone_2b_paired_analysis/p1_failure_census.csv"
M2C = DISCOVERY_SCAFFOLD / "milestone_2c_v1_candidate_design/milestone_2c_cell_evidence.csv"
M2F_DIR = Path("artifacts/pbd/mbpp_e40/pa/r002/milestone_2f_evidence_review")
M2F_LEDGER = M2F_DIR / "expansion_cell_evidence.csv"
M2F_FAILURES = M2F_DIR / "candidate_a_failure_census.csv"
EXPANSION_OVERLAY = Path(
    "artifacts/public_benchmark_governance/development_expansion_v1/"
    "development_expansion_manifest.json"
)

RUNS = (
    {
        "layer": "discovery_development",
        "pair_id": "discovery_p0_vs_scaffold_v0",
        "baseline_label": "p0_official_prompt_only",
        "baseline_run_id": "mbpp_qwen35_9b_ab1_dev_run_003",
        "baseline_dir": DISCOVERY_P0,
        "treatment_label": "scaffold_v0",
        "treatment_run_id": "mbpp_qwen35_9b_scaffold_v0_dev_run_002",
        "treatment_dir": DISCOVERY_SCAFFOLD,
        "expected_cells": 100,
    },
    {
        "layer": "expansion_development",
        "pair_id": "expansion_p0_vs_candidate_a",
        "baseline_label": "p0_official_prompt_only",
        "baseline_run_id": "mbpp_q35_9b_p0_exp40_r001",
        "baseline_dir": EXPANSION_P0,
        "treatment_label": "candidate_a",
        "treatment_run_id": "mbpp_q35_9b_ca_exp40_r002",
        "treatment_dir": EXPANSION_CANDIDATE,
        "expected_cells": 200,
    },
)

SOURCE_FILES = (
    EXPANSION_OVERLAY,
    M1C,
    M1D,
    DISCOVERY_P0 / "milestone_1d_evidence_review/evidence_manifest.json",
    M2B,
    DISCOVERY_SCAFFOLD / "milestone_2b_paired_analysis/paired_analysis_manifest.json",
    M2C,
    DISCOVERY_SCAFFOLD / "milestone_2c_v1_candidate_design/milestone_2c_manifest.json",
    M2F_LEDGER,
    M2F_FAILURES,
    M2F_DIR / "milestone_2f_manifest.json",
    M2F_DIR / "rescue_regression_task_summary.csv",
) + tuple(
    run[key] / name
    for run in RUNS
    for key in ("baseline_dir", "treatment_dir")
    for name in ("generation_plan.json", "raw_generations.jsonl", "pipeline_corrected.jsonl", "evaluation_results.csv")
)

CELL_FIELDS = (
    "development_layer", "pair_id", "task_id", "seed", "paired_identity",
    "baseline_treatment", "baseline_run_id", "baseline_generation_id",
    "baseline_observed_status", "baseline_pipeline_status", "baseline_failure_signature",
    "baseline_failure_category", "baseline_truncated", "baseline_raw_compile_status",
    "baseline_pipeline_compile_status", "baseline_entry_point_status",
    "baseline_extraction_action", "baseline_raw_sha256", "baseline_pipeline_sha256",
    "treatment", "treatment_run_id", "treatment_generation_id",
    "treatment_observed_status", "treatment_pipeline_status", "treatment_failure_signature",
    "treatment_failure_category", "treatment_truncated", "treatment_raw_compile_status",
    "treatment_pipeline_compile_status", "treatment_entry_point_status",
    "treatment_extraction_action", "treatment_raw_sha256", "treatment_pipeline_sha256",
    "pipeline_transition", "program_count_represented", "pipeline_is_healer",
)

SIGNATURE_FIELDS = (
    "signature", "category", "cell_support", "unique_task_support",
    "discovery_p0_cells", "discovery_scaffold_v0_cells", "expansion_p0_cells",
    "expansion_candidate_a_cells", "supporting_task_ids", "evidence_basis",
    "counterexample_cells", "counterexample_task_ids", "semantic_risk",
    "default_automation_disposition",
)

SCAFFOLD_FIELDS = (
    "candidate_id", "status", "design_issue", "evidence_cells", "unique_task_support",
    "direct_evidence", "inference_limit", "recommended_direction", "exact_text_draft_utf8",
    "same_40_task_retest_allowed", "official_v1_frozen",
)

HEALER_FIELDS = (
    "rule_id", "signature", "trigger", "proposed_transformation", "unique_task_support",
    "cell_support", "supporting_task_ids", "counterexamples", "semantic_risk",
    "evaluator_blind_evidence", "safety_guard", "abstention_conditions",
    "recommended_status", "verified_rule", "evaluator_result_used_to_accept_repair",
)

CANDIDATE_B_TEXT = (
    "Return exactly one concise, complete, executable Python source file.\n"
    "Use the exact required function name and parameters, include required imports, and finish the implementation within the output limit.\n"
    "Do not use Markdown fences or explanatory text; output only Python code.\n"
)

BUILTIN_CALLS = {
    "abs", "all", "any", "isinstance", "len", "list", "max", "min", "round",
    "set", "sorted", "sum", "tuple",
}


class IntegratedEvidenceError(RuntimeError):
    """Raised before writes when development evidence does not reconcile."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegratedEvidenceError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256(value.encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index(rows: Iterable[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in indexed, f"{label}: duplicate {key}")
        indexed[key] = row
    return indexed


def _bool(value: bool) -> str:
    return str(value).lower()


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _prompt_contract(prompt: str) -> tuple[str, set[int]]:
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
    names = {call.func.id for call in calls if isinstance(call.func, ast.Name)}
    _require(len(names) == 1, "model-visible development prompt must identify one entry point")
    entry_point = next(iter(names))
    arities = {len(call.args) for call in calls if isinstance(call.func, ast.Name) and call.func.id == entry_point and not call.keywords}
    _require(bool(arities), f"{entry_point}: no positional arity evidence")
    return entry_point, arities


def _functions(source: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(source)
    return [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _top_level_bound_names(source: str) -> set[str]:
    names: set[str] = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _accepts_arity(function: ast.FunctionDef | ast.AsyncFunctionDef, arity: int) -> bool:
    args = function.args
    positional = len(args.posonlyargs) + len(args.args)
    required = positional - len(args.defaults)
    required_kwonly = sum(default is None for default in args.kw_defaults)
    return required_kwonly == 0 and arity >= required and (args.vararg is not None or arity <= positional)


def _entry_status(source: str | None, expected: str) -> str:
    if source is None:
        return "extraction_failed"
    try:
        names = {node.name for node in _functions(source)}
    except (SyntaxError, ValueError, OverflowError):
        return "not_assessed_compile_fail"
    return "present" if expected in names else "missing"


def _pipeline_hash(pipeline: dict[str, Any]) -> str:
    source = pipeline["pipeline_corrected_output"]
    if source is None:
        _require(pipeline["pipeline_corrected_output_sha256"] is None, "null pipeline hash drift")
        return ""
    digest = _sha256_text(source)
    _require(digest == pipeline["pipeline_corrected_output_sha256"], "pipeline output hash drift")
    return digest


def _classify_program(
    raw: dict[str, Any], pipeline: dict[str, Any], evaluation: dict[str, str],
    entry_point: str, arities: set[int],
) -> dict[str, Any]:
    features = evidence._raw_features(raw)
    source = pipeline["pipeline_corrected_output"]
    extracted = pipeline["extraction_status"] == "extracted" and source is not None
    entry = _entry_status(source, entry_point)
    if evaluation["pipeline_corrected_status"] == "pass":
        category, signature = "pipeline_pass", "pipeline_pass"
    elif not extracted:
        category, signature = "format_packaging", "format_or_packaging_extraction_failure"
    elif evaluation["pipeline_corrected_syntax_compile_status"] == "fail":
        category, signature = "syntax", "syntax_parse_failure"
    elif entry == "missing":
        funcs = _functions(source)
        compatible = (
            len(funcs) == 1
            and isinstance(funcs[0], ast.FunctionDef)
            and not funcs[0].decorator_list
            and funcs[0].name != entry_point
            and entry_point not in _top_level_bound_names(source)
            and all(_accepts_arity(funcs[0], arity) for arity in arities)
        )
        category = "uniquely_evidenced_static_structural_error" if compatible else "entry_point"
        signature = (
            "entrypoint_unique_arity_compatible_candidate"
            if compatible else "entrypoint_no_unique_safe_candidate"
        )
    elif evaluation["pipeline_corrected_runtime_timeout_status"] == "timeout":
        category, signature = "unknown_semantic_risk", "timeout_or_resource_failure"
    else:
        category, signature = "unknown_semantic_risk", "generic_evaluator_failure_unknown"
    return {
        "category": category,
        "signature": signature,
        "truncated": features["truncated"],
        "raw_compile": features["compile_status"],
        "entry": entry,
        "action": evidence._pipeline_action(pipeline),
        "unique_candidate": signature == "entrypoint_unique_arity_compatible_candidate",
    }


def _plan_keys(plan: dict[str, Any]) -> list[tuple[str, int]]:
    if "cells" in plan:
        return [(cell["task_id"], int(cell["seed"])) for cell in plan["cells"]]
    return [(task_id, int(seed)) for task_id in plan["task_ids"] for seed in plan["seeds"]]


def _load_run(repo_root: Path, relative: Path, expected_run_id: str) -> dict[str, Any]:
    root = repo_root / relative
    plan = _read_json(root / "generation_plan.json")
    run_id = plan.get("run_id", plan.get("logical_run_id"))
    _require(run_id == expected_run_id, f"run ID drift: {relative}")
    raw = _index(_read_jsonl(root / "raw_generations.jsonl"), f"{relative} raw")
    pipeline = _index(_read_jsonl(root / "pipeline_corrected.jsonl"), f"{relative} pipeline")
    evaluation = _index(_read_csv(root / "evaluation_results.csv"), f"{relative} eval")
    keys = _plan_keys(plan)
    _require(len(keys) == len(set(keys)) and set(raw) == set(pipeline) == set(evaluation) == set(keys), f"identity drift: {relative}")
    for key in keys:
        r, p, e = raw[key], pipeline[key], evaluation[key]
        _require(r["generation_id"] == p["generation_id"] == e["generation_id"], f"generation relation drift: {relative} {key}")
        raw_hash = _sha256_text(r["raw_response"])
        _require(raw_hash == r["raw_response_sha256"] == p["source_raw_response_sha256"] == e["observed_output_sha256"], f"raw hash relation drift: {relative} {key}")
        pipe_hash = _pipeline_hash(p)
        _require(pipe_hash == e["pipeline_corrected_output_sha256"], f"evaluation pipeline hash drift: {relative} {key}")
        _require(r.get("retry_count", 0) == 0, f"retry drift: {relative} {key}")
    return {"plan": plan, "keys": keys, "raw": raw, "pipeline": pipeline, "evaluation": evaluation}


def _source_hashes(repo_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = repo_root / relative
        _require(path.is_file(), f"missing source: {relative.as_posix()}")
        result[relative.as_posix()] = _sha256(path.read_bytes())
    forbidden = ("validation", "confirmatory", "sealed", "excluded")
    _require(not any(any(word in path.lower() for word in forbidden) for path in result), "forbidden-role source path")
    return result


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    overlay = _read_json(repo_root / EXPANSION_OVERLAY)
    _require(
        overlay["counts"]["historical_development_pool"] == 116
        and overlay["counts"]["total_development"] == 60
        and 116 - 60 == 56,
        "remaining historical development count drift",
    )
    task_layers = {row["task_id"]: row["development_layer"] for row in overlay["development_tasks"]}
    _require(Counter(task_layers.values()) == {"discovery_development": 20, "expansion_development": 40}, "development overlay count drift")
    _require(len(task_layers) == 60, "development task uniqueness drift")

    ledger_rows: list[dict[str, str]] = []
    program_records: list[dict[str, Any]] = []
    identity_set: set[tuple[str, int]] = set()
    treatment_counts: Counter[str] = Counter()

    for spec in RUNS:
        base = _load_run(repo_root, spec["baseline_dir"], spec["baseline_run_id"])
        treated = _load_run(repo_root, spec["treatment_dir"], spec["treatment_run_id"])
        _require(base["keys"] == treated["keys"], f"paired order drift: {spec['pair_id']}")
        _require(len(base["keys"]) == spec["expected_cells"], f"paired cell count drift: {spec['pair_id']}")
        for key in base["keys"]:
            task_id, seed = key
            _require(task_layers[task_id] == spec["layer"], f"overlay layer mismatch: {task_id}")
            _require(key not in identity_set, f"cross-layer duplicate identity: {key}")
            identity_set.add(key)
            prompt = base["raw"][key]["request"]["messages"][0]["content"]
            entry_point, arities = _prompt_contract(prompt)
            pair_programs: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = []
            for role, label, run_id, loaded in (
                ("baseline", spec["baseline_label"], spec["baseline_run_id"], base),
                ("treatment", spec["treatment_label"], spec["treatment_run_id"], treated),
            ):
                raw, pipeline, evaluation = loaded["raw"][key], loaded["pipeline"][key], loaded["evaluation"][key]
                classified = _classify_program(raw, pipeline, evaluation, entry_point, arities)
                record = {
                    "development_layer": spec["layer"], "role": role, "treatment": label,
                    "run_id": run_id, "task_id": task_id, "seed": seed,
                    "raw": raw, "pipeline": pipeline, "evaluation": evaluation,
                    "entry_point": entry_point, "arities": arities, **classified,
                }
                program_records.append(record)
                pair_programs.append((role, label, loaded, record))
                treatment_counts[label] += 1
            base_record, treated_record = pair_programs[0][3], pair_programs[1][3]
            transition = f"{base_record['evaluation']['pipeline_corrected_status']}_to_{treated_record['evaluation']['pipeline_corrected_status']}"

            def columns(prefix: str, record: dict[str, Any]) -> dict[str, str]:
                raw, pipeline, evaluation = record["raw"], record["pipeline"], record["evaluation"]
                return {
                    ("treatment" if prefix == "treatment" else "baseline_treatment"): record["treatment"],
                    f"{prefix}_run_id": record["run_id"],
                    f"{prefix}_generation_id": raw["generation_id"],
                    f"{prefix}_observed_status": evaluation["observed_status"],
                    f"{prefix}_pipeline_status": evaluation["pipeline_corrected_status"],
                    f"{prefix}_failure_signature": record["signature"],
                    f"{prefix}_failure_category": record["category"],
                    f"{prefix}_truncated": _bool(record["truncated"]),
                    f"{prefix}_raw_compile_status": record["raw_compile"],
                    f"{prefix}_pipeline_compile_status": evaluation["pipeline_corrected_syntax_compile_status"],
                    f"{prefix}_entry_point_status": record["entry"],
                    f"{prefix}_extraction_action": record["action"],
                    f"{prefix}_raw_sha256": raw["raw_response_sha256"],
                    f"{prefix}_pipeline_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                }
            ledger_rows.append({
                "development_layer": spec["layer"], "pair_id": spec["pair_id"],
                "task_id": task_id, "seed": str(seed), "paired_identity": f"{task_id}|seed={seed}",
                **columns("baseline", base_record), **columns("treatment", treated_record),
                "pipeline_transition": transition, "program_count_represented": "2",
                "pipeline_is_healer": "false",
            })

    _require(len(identity_set) == len(ledger_rows) == 300, "integrated identity count drift")
    _require(len(program_records) == sum(int(row["program_count_represented"]) for row in ledger_rows) == 600, "program count drift")
    _require(treatment_counts == {"p0_official_prompt_only": 300, "scaffold_v0": 100, "candidate_a": 200}, "treatment accounting drift")
    _require({task for task, _ in identity_set} == set(task_layers), "60-task coverage drift")

    # Confirm the integration agrees with the milestone-level evidence ledgers.
    m2c = _read_csv(repo_root / M2C)
    m2f = _read_csv(repo_root / M2F_LEDGER)
    _require(len(m2c) == 100 and len(m2f) == 200, "source evidence ledger count drift")
    integrated_index = {(row["task_id"], int(row["seed"])): row for row in ledger_rows}
    for row in m2c:
        merged = integrated_index[(row["task_id"], int(row["seed"]))]
        _require(merged["pipeline_transition"] == row["pipeline_transition"], "Milestone 2C transition mismatch")
    for row in m2f:
        merged = integrated_index[(row["task_id"], int(row["seed"]))]
        _require(merged["pipeline_transition"] == row["pipeline_transition"], "Milestone 2F transition mismatch")

    signatures = (
        ("format_or_packaging_extraction_failure", "format_packaging"),
        ("generation_length_termination", "truncation"),
        ("syntax_parse_failure", "syntax"),
        ("entrypoint_no_unique_safe_candidate", "entry_point"),
        ("import_or_dependency_failure_uniquely_evidenced", "import_dependency"),
        ("entrypoint_unique_arity_compatible_candidate", "uniquely_evidenced_static_structural_error"),
        ("generic_evaluator_failure_unknown", "unknown_semantic_risk"),
        ("timeout_or_resource_failure", "unknown_semantic_risk"),
    )
    signature_rows: list[dict[str, str]] = []
    signature_support: dict[str, dict[str, Any]] = {}
    for signature, category in signatures:
        if signature == "generation_length_termination":
            supported = [row for row in program_records if row["truncated"]]
        else:
            supported = [row for row in program_records if row["signature"] == signature]
        tasks = sorted({row["task_id"] for row in supported})
        counts = Counter(f"{row['development_layer']}|{row['treatment']}" for row in supported)
        counterexamples: list[dict[str, Any]] = []
        if signature == "entrypoint_unique_arity_compatible_candidate":
            counterexamples = [row for row in program_records if row["signature"] == "entrypoint_no_unique_safe_candidate"]
        signature_support[signature] = {"records": supported, "tasks": tasks, "counterexamples": counterexamples}
        basis = {
            "format_or_packaging_extraction_failure": "saved extraction status is not extracted",
            "generation_length_termination": "saved model done_reason is not stop; overlaps other primary categories",
            "syntax_parse_failure": "saved Pipeline syntax compile status is fail",
            "entrypoint_no_unique_safe_candidate": "expected entry point absent without exactly one arity-compatible top-level function",
            "import_or_dependency_failure_uniquely_evidenced": "no saved diagnostic uniquely identifies this category",
            "entrypoint_unique_arity_compatible_candidate": "compile pass; expected name unbound; exactly one undecorated synchronous top-level function accepts every model-visible positional arity",
            "generic_evaluator_failure_unknown": "compile and entry checks pass but evaluator result is generic failure",
            "timeout_or_resource_failure": "saved runtime timeout status only",
        }[signature]
        disposition = {
            "format_or_packaging_extraction_failure": "scaffold_or_pipeline_only",
            "generation_length_termination": "nonrepairable",
            "syntax_parse_failure": "insufficient_evidence",
            "entrypoint_no_unique_safe_candidate": "nonrepairable",
            "import_or_dependency_failure_uniquely_evidenced": "insufficient_evidence",
            "entrypoint_unique_arity_compatible_candidate": "eligible_for_implementation",
            "generic_evaluator_failure_unknown": "nonrepairable",
            "timeout_or_resource_failure": "nonrepairable",
        }[signature]
        signature_rows.append({
            "signature": signature, "category": category, "cell_support": str(len(supported)),
            "unique_task_support": str(len(tasks)),
            "discovery_p0_cells": str(counts["discovery_development|p0_official_prompt_only"]),
            "discovery_scaffold_v0_cells": str(counts["discovery_development|scaffold_v0"]),
            "expansion_p0_cells": str(counts["expansion_development|p0_official_prompt_only"]),
            "expansion_candidate_a_cells": str(counts["expansion_development|candidate_a"]),
            "supporting_task_ids": "|".join(tasks), "evidence_basis": basis,
            "counterexample_cells": str(len(counterexamples)),
            "counterexample_task_ids": "|".join(sorted({row["task_id"] for row in counterexamples})),
            "semantic_risk": "low" if category == "format_packaging" else "high" if category in {"unknown_semantic_risk", "entry_point", "syntax"} else "moderate",
            "default_automation_disposition": disposition,
        })

    candidate_failures = _read_csv(repo_root / M2F_FAILURES)
    ca_trunc = [row for row in candidate_failures if row["generation_truncation"] == "true"]
    ca_syntax = [row for row in candidate_failures if row["syntax_failure"] == "true"]
    _require(len(ca_trunc) == 18 and len({row["task_id"] for row in ca_trunc}) == 8, "Candidate A truncation evidence drift")
    _require(len(ca_syntax) == 19 and len({row["task_id"] for row in ca_syntax}) == 10, "Candidate A compile evidence drift")
    overlap = {(row["task_id"], row["seed"]) for row in ca_trunc} & {(row["task_id"], row["seed"]) for row in ca_syntax}

    scaffold_rows = [
        {
            "candidate_id": "candidate_b_concise_complete_draft",
            "status": "candidate_not_frozen", "design_issue": "concise_and_complete_within_output_limit",
            "evidence_cells": "18 truncation; 19 syntax; 15 overlap",
            "unique_task_support": "8 truncation tasks; 10 syntax tasks",
            "direct_evidence": "Candidate A failures include 18 length terminations across 8 tasks and 19 compile failures across 10 tasks",
            "inference_limit": "wording benefit is a design hypothesis; truncation does not identify missing intended code and cannot be auto-repaired",
            "recommended_direction": "request one concise complete implementation while retaining exact entry point and no-fence constraints",
            "exact_text_draft_utf8": CANDIDATE_B_TEXT,
            "same_40_task_retest_allowed": "false", "official_v1_frozen": "false",
        },
        {
            "candidate_id": "candidate_b_concise_complete_draft",
            "status": "candidate_not_frozen", "design_issue": "format_and_packaging",
            "evidence_cells": str(len(signature_support["format_or_packaging_extraction_failure"]["records"])),
            "unique_task_support": str(len(signature_support["format_or_packaging_extraction_failure"]["tasks"])),
            "direct_evidence": "discovery P0 shows repeated fence/packaging extraction failures while scaffolded outputs remove them",
            "inference_limit": "aggregate association does not isolate line-level causality",
            "recommended_direction": "retain no Markdown and output-only source contract",
            "exact_text_draft_utf8": CANDIDATE_B_TEXT,
            "same_40_task_retest_allowed": "false", "official_v1_frozen": "false",
        },
        {
            "candidate_id": "candidate_b_concise_complete_draft",
            "status": "candidate_not_frozen", "design_issue": "exact_entry_point",
            "evidence_cells": str(len(signature_support["entrypoint_unique_arity_compatible_candidate"]["records"])),
            "unique_task_support": str(len(signature_support["entrypoint_unique_arity_compatible_candidate"]["tasks"])),
            "direct_evidence": "missing expected names recur in saved development programs; Candidate A expansion has zero entry-point failures",
            "inference_limit": "does not prove Scaffold wording caused the structural improvement",
            "recommended_direction": "retain exact required function name and parameters",
            "exact_text_draft_utf8": CANDIDATE_B_TEXT,
            "same_40_task_retest_allowed": "false", "official_v1_frozen": "false",
        },
    ]

    entry_support = signature_support["entrypoint_unique_arity_compatible_candidate"]
    entry_counter = entry_support["counterexamples"]
    healer_rows = [
        {
            "rule_id": "entrypoint_alias_unique_arity_compatible_v0",
            "signature": "entrypoint_unique_arity_compatible_candidate",
            "trigger": "source parses; expected entry point absent and unbound; exactly one undecorated synchronous top-level function; all model-visible positional arities compatible",
            "proposed_transformation": "append a name-only alias: expected_entry_point = existing_function; never rewrite the body",
            "unique_task_support": str(len(entry_support["tasks"])), "cell_support": str(len(entry_support["records"])),
            "supporting_task_ids": "|".join(entry_support["tasks"]),
            "counterexamples": (
                f"{len(entry_counter)} cells/{len({row['task_id'] for row in entry_counter})} tasks "
                f"lack a unique safe candidate: {'|'.join(sorted({row['task_id'] for row in entry_counter}))}"
            ),
            "semantic_risk": "moderate; alias preserves body but exported-name intent can still be ambiguous",
            "evaluator_blind_evidence": "AST names, function count/signature, and model-visible call arity only; no evaluator outcome is consulted to accept a repair",
            "safety_guard": "one function only; exact arity compatibility; no target binding; no body/control-flow/import changes; deterministic diff budget",
            "abstention_conditions": "parse failure, truncation, multiple functions, incompatible/unknown arity, existing target binding, decorators or binding ambiguity, or any required body edit",
            "recommended_status": "eligible_for_implementation", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
        {
            "rule_id": "syntax_parse_failure_generic",
            "signature": "syntax_parse_failure",
            "trigger": "saved Pipeline program does not parse",
            "proposed_transformation": "none; collect narrower signatures prospectively before implementation",
            "unique_task_support": str(len(signature_support["syntax_parse_failure"]["tasks"])),
            "cell_support": str(len(signature_support["syntax_parse_failure"]["records"])),
            "supporting_task_ids": "|".join(signature_support["syntax_parse_failure"]["tasks"]),
            "counterexamples": "parse errors include truncation and heterogeneous syntax diagnostics",
            "semantic_risk": "high", "evaluator_blind_evidence": "parser diagnostic only",
            "safety_guard": "no generic syntax rewrite", "abstention_conditions": "always until a narrower independently justified signature exists",
            "recommended_status": "insufficient_evidence", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
        {
            "rule_id": "truncation_completion",
            "signature": "generation_length_termination",
            "trigger": "done_reason is not stop",
            "proposed_transformation": "none; missing continuation is not present in saved evidence",
            "unique_task_support": str(len(signature_support["generation_length_termination"]["tasks"])),
            "cell_support": str(len(signature_support["generation_length_termination"]["records"])),
            "supporting_task_ids": "|".join(signature_support["generation_length_termination"]["tasks"]),
            "counterexamples": "some truncated programs parse; some non-truncated programs fail syntax or semantics",
            "semantic_risk": "unbounded", "evaluator_blind_evidence": "termination metadata only",
            "safety_guard": "never synthesize missing code", "abstention_conditions": "always",
            "recommended_status": "nonrepairable", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
        {
            "rule_id": "format_packaging_extraction",
            "signature": "format_or_packaging_extraction_failure",
            "trigger": "extractor reports ambiguous or unsupported packaging",
            "proposed_transformation": "none in Healer; handle prospectively in Scaffold or by the frozen Pipeline extractor",
            "unique_task_support": str(len(signature_support["format_or_packaging_extraction_failure"]["tasks"])),
            "cell_support": str(len(signature_support["format_or_packaging_extraction_failure"]["records"])),
            "supporting_task_ids": "|".join(signature_support["format_or_packaging_extraction_failure"]["tasks"]),
            "counterexamples": "multiple competing fenced programs cannot be selected safely",
            "semantic_risk": "high if competing programs are chosen", "evaluator_blind_evidence": "fence and extraction metadata",
            "safety_guard": "do not choose among alternatives", "abstention_conditions": "ambiguous multiple payloads",
            "recommended_status": "scaffold_or_pipeline_only", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
        {
            "rule_id": "generic_unknown_failure",
            "signature": "generic_evaluator_failure_unknown",
            "trigger": "compile and expected entry checks pass but only generic evaluator failure is saved",
            "proposed_transformation": "none",
            "unique_task_support": str(len(signature_support["generic_evaluator_failure_unknown"]["tasks"])),
            "cell_support": str(len(signature_support["generic_evaluator_failure_unknown"]["records"])),
            "supporting_task_ids": "|".join(signature_support["generic_evaluator_failure_unknown"]["tasks"]),
            "counterexamples": "saved evidence cannot distinguish semantic assertion, runtime, name, or dependency causes",
            "semantic_risk": "unbounded", "evaluator_blind_evidence": "insufficient",
            "safety_guard": "no evaluator-driven search or acceptance", "abstention_conditions": "always",
            "recommended_status": "nonrepairable", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
        {
            "rule_id": "import_dependency_unknown",
            "signature": "import_or_dependency_failure_uniquely_evidenced",
            "trigger": "requires a saved, uniquely identifying static dependency diagnostic",
            "proposed_transformation": "none with current evidence",
            "unique_task_support": "0", "cell_support": "0", "supporting_task_ids": "",
            "counterexamples": "generic evaluator failures cannot be recoded as import failures",
            "semantic_risk": "high", "evaluator_blind_evidence": "no uniquely evidenced cells",
            "safety_guard": "require explicit static name/dependency proof", "abstention_conditions": "all current cells",
            "recommended_status": "insufficient_evidence", "verified_rule": "false",
            "evaluator_result_used_to_accept_repair": "false",
        },
    ]

    eligible = [row for row in healer_rows if row["recommended_status"] == "eligible_for_implementation"]
    _require(len(eligible) == 1 and int(eligible[0]["unique_task_support"]) >= 2, "narrow Healer sufficiency condition not met")
    source_hashes = _source_hashes(repo_root)
    return {
        "ledger_rows": ledger_rows, "signature_rows": signature_rows,
        "scaffold_rows": scaffold_rows, "healer_rows": healer_rows,
        "source_hashes": source_hashes, "task_layers": task_layers,
        "treatment_counts": dict(sorted(treatment_counts.items())),
        "candidate_a": {
            "truncation_cells": 18, "truncation_tasks": 8,
            "syntax_cells": 19, "syntax_tasks": 10,
            "truncation_syntax_overlap_cells": len(overlap),
        },
        "eligible_rule": eligible[0],
    }


def _report(result: dict[str, Any]) -> bytes:
    eligible = result["eligible_rule"]
    lines = [
        "# Milestone 2G：60題MBPP+ development整合證據",
        "",
        "## 結論",
        "",
        f"資料充分性決策：`{DECISION}`。現有development證據已足以**實作**一條窄範圍、evaluator-blind且有明確abstention的entry-point alias候選規則；這不代表規則已驗證、可部署或可宣稱提升correctness，也不代表Scaffold v1已凍結。",
        "",
        "## 60題、300 identities、600 programs的差別",
        "",
        "60題指60個unique task IDs，不能把同題五個seed說成五題。每題有seed 11、22、33、44、55，因此共有300個unique task-seed identities。每個identity各有兩個paired treatments，所以保存了600個generated programs：discovery 20題是P0與Scaffold v0共200個programs；expansion 40題是P0與Candidate A共400個programs。Pipeline是同一program的第二個評估帳，不是額外program，也不是Healer。",
        "",
        "## Candidate A改善與未升格原因",
        "",
        "Expansion中Candidate A把Pipeline-corrected pass由38/200（19%）提高到53/200（26.5%）；30 rescues、15 regressions，exact McNemar p=0.0356978。correctness improvement條件成立，但strict Python-only只有178/200（89%），低於預註冊90%，所以format gate失敗，Candidate A仍不得升格official v1。",
        "",
        "## Scaffold候選方向",
        "",
        f"Candidate A的147個Pipeline failures中，18格／8題有length termination，19格／10題有compile failure，兩者重疊{result['candidate_a']['truncation_syntax_overlap_cells']}格。這支持把『簡潔且完整、在輸出上限內完成』列為Candidate B的設計方向，但只是設計假說：truncation沒有保存遺失的後半段，不能由Healer補寫；compile failure也包含異質原因。",
        "",
        "本輪只保留一個`candidate_not_frozen` exact-text草案，保留no-fence、output-only與exact entry-point要求，並加入concise/complete方向。不得修改後在同40題重跑；未來若測試必須另立前瞻protocol與使用未啟用development tasks。",
        "",
        "## 可能交給Healer的錯誤",
        "",
        f"唯一達到實作門檻的窄候選是`{eligible['rule_id']}`：{eligible['cell_support']}格、{eligible['unique_task_support']}個unique tasks。trigger只用AST、top-level函式數、預期名稱與model-visible positional arity；transform只追加名稱alias，不改body。只要parse失敗、truncation、多函式、arity不相容、目標名稱已綁定、decorator／binding有歧義或需要改body，就必須abstain。規則接受不得查看修後evaluator pass/fail。",
        "",
        "## 必須abstain的錯誤",
        "",
        "generic evaluator unknown無法區分functional assertion、runtime、name或dependency原因；truncation缺少未生成內容；一般syntax error過度異質；多個候選函式或arity不相容也無唯一安全轉換。這些一律不能自動修復。format／packaging應由Scaffold或既有Pipeline處理，Pipeline correction不得稱為Healer。",
        "",
        "## 是否啟用剩餘56題？",
        "",
        "目前不需要先啟用全部剩餘56題，因為目標只是判斷能否進入窄規則與Candidate B的實作／預註冊階段：entry-point候選已有跨多題支持、反例、靜態trigger、安全門與abstention；Scaffold的concise/complete方向也有8至10個unique tasks支持。下一里程碑可實作候選資產並凍結獨立前瞻protocol，但不能把本輪候選視為verified rule。剩餘56題應保留為未啟用development資源，供未來前瞻測試或候選失敗後另立deterministic expansion；本輪不選題、不生成。",
        "",
        "## 外推限制",
        "",
        "所有結論只限這60題development、既定模型／sampling／treatments與保存的靜態診斷。未讀取validation、confirmatory、excluded historical或sealed reserve，不能外推到封存資料或其他模型。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    result = build_analysis(repo_root)
    decision = {
        "decision": DECISION,
        "development_tasks": 60,
        "unique_task_seed_identities": 300,
        "generated_programs": 600,
        "same_task_different_seed_is_new_task": False,
        "sufficient_for_at_least_one_narrow_evaluator_blind_rule_implementation": True,
        "eligible_rule_id": result["eligible_rule"]["rule_id"],
        "eligible_rule_unique_task_support": int(result["eligible_rule"]["unique_task_support"]),
        "eligible_rule_cell_support": int(result["eligible_rule"]["cell_support"]),
        "remaining_historical_development_tasks": 56,
        "activate_remaining_56_now": False,
        "reason": "one narrow static rule has multi-task support, counterexamples, deterministic safety guards, and explicit abstention; additional tasks remain reserved for prospective testing rather than retrospective selection",
        "next_step": "implement candidate assets and preregister a separate prospective protocol; do not freeze official v1 in this milestone",
        "candidate_a_same_40_task_retest_allowed": False,
        "model_calls": 0,
        "evalplus_executions": 0,
    }
    outputs = {
        "integrated_development_cell_ledger.csv": _csv_bytes(result["ledger_rows"], CELL_FIELDS),
        "integrated_failure_signature_census.csv": _csv_bytes(result["signature_rows"], SIGNATURE_FIELDS),
        "scaffold_candidate_evidence.csv": _csv_bytes(result["scaffold_rows"], SCAFFOLD_FIELDS),
        "healer_candidate_rule_ledger.csv": _csv_bytes(result["healer_rows"], HEALER_FIELDS),
        "development_sufficiency_decision.json": _json_bytes(decision),
        "integrated_development_analysis_zh.md": _report(result),
    }
    manifest = {
        "analysis_version": "milestone_2g_integrated_development_evidence_v1",
        "expected_starting_head": EXPECTED_HEAD,
        "scope": "existing discovery and expansion development artifacts only",
        "counts": {
            "unique_tasks": 60, "unique_task_seed_identities": 300,
            "generated_programs": 600, "ledger_rows": 300,
            "discovery_tasks": 20, "expansion_tasks": 40,
        },
        "treatment_program_counts": result["treatment_counts"],
        "pipeline_account_is_additional_program": False,
        "pipeline_correction_is_healer": False,
        "decision": DECISION,
        "candidate_b": {
            "status": "candidate_not_frozen",
            "exact_text_utf8": CANDIDATE_B_TEXT,
            "exact_text_sha256": _sha256_text(CANDIDATE_B_TEXT),
            "implemented": False, "same_40_task_retest_allowed": False,
        },
        "healer": {
            "implemented": False, "verified_rules": 0,
            "eligible_for_implementation_rule_count": 1,
            "evaluator_result_used_to_accept_repair": False,
        },
        "candidate_a_evidence": result["candidate_a"],
        "remaining_historical_development_tasks": 56,
        "remaining_tasks_selected_or_read": 0,
        "model_calls": 0, "evalplus_executions": 0,
        "formal_inputs_modified": False,
        "forbidden_roles_read": [],
        "source_artifact_sha256": result["source_hashes"],
        "output_sha256_excluding_manifest": {
            name: _sha256(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["milestone_2g_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "Milestone 2G output directory missing")
        actual = {path.name for path in output_dir.iterdir() if path.is_file()}
        _require(actual == set(outputs), "Milestone 2G output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "Milestone 2G output directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        write_outputs(check=args.check)
    except IntegratedEvidenceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
