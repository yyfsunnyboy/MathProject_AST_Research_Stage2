#!/usr/bin/env python3
"""Build the deterministic Milestone 2F Candidate A evidence review."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_mbpp_candidate_a_expansion as prospective  # noqa: E402
from scripts import build_mbpp_development_failure_census as census_v1  # noqa: E402
from scripts import build_mbpp_scaffold_healer_evidence_packets as evidence  # noqa: E402
from scripts import build_mbpp_scaffold_v0_paired_analysis as paired_math  # noqa: E402
from scripts import freeze_mbpp_candidate_a_expansion_protocol as frozen  # noqa: E402
from scripts import freeze_mbpp_candidate_a_interruption_recovery as recovery  # noqa: E402


P0_RELATIVE = Path("artifacts/pbd/mbpp_e40/p0/r001")
CA_RELATIVE = Path("artifacts/pbd/mbpp_e40/ca/r002")
PAIRED_RELATIVE = Path("artifacts/pbd/mbpp_e40/pa/r002")
R001_RELATIVE = Path("artifacts/pbd/mbpp_e40/ca/r001")
OUTPUT_RELATIVE = PAIRED_RELATIVE / "milestone_2f_evidence_review"

EXPECTED_HEAD = "dd38c939693921e30fd6588d02272c4bc7c34f51"
EXPECTED_CANDIDATE_HASH = "bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058"
EXPECTED_MODEL = "qwen3.5:9b"
EXPECTED_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
EXPECTED_QUANTIZATION = "Q4_K_M"
EXPECTED_SEEDS = [11, 22, 33, 44, 55]
EXPECTED_TRANSITIONS = {
    "fail_to_fail": 132,
    "fail_to_pass": 30,
    "pass_to_fail": 15,
    "pass_to_pass": 23,
}

SOURCE_FILES = (
    P0_RELATIVE / "generation_plan.json",
    P0_RELATIVE / "raw_generations.jsonl",
    P0_RELATIVE / "pipeline_corrected.jsonl",
    P0_RELATIVE / "evaluation_results.csv",
    P0_RELATIVE / "evaluation_summary.md",
    CA_RELATIVE / "generation_plan.json",
    CA_RELATIVE / "raw_generations.jsonl",
    CA_RELATIVE / "pipeline_corrected.jsonl",
    CA_RELATIVE / "evaluation_results.csv",
    CA_RELATIVE / "evaluation_summary.md",
    PAIRED_RELATIVE / "paired_cell_results.csv",
    PAIRED_RELATIVE / "all_pipeline_regressions.csv",
    PAIRED_RELATIVE / "paired_analysis_manifest.json",
    R001_RELATIVE / "generation_plan.json",
    Path("artifacts/public_benchmark_governance/candidate_a_expansion_recovery_r002/candidate_a_r001_incident_manifest.json"),
)

CELL_FIELDS = (
    "task_id", "seed", "paired_identity", "p0_generation_id", "candidate_generation_id",
    "p0_observed_status", "candidate_observed_status", "p0_pipeline_status",
    "candidate_pipeline_status", "pipeline_transition", "p0_raw_sha256",
    "candidate_raw_sha256", "candidate_pipeline_sha256", "p0_journal_file_sha256",
    "candidate_journal_file_sha256", "strict_output_compliance",
    "generation_protocol_compliance", "code_fence_marker_count", "extra_text",
    "multiple_program_segments", "raw_compile_status", "raw_compile_diagnostic",
    "pipeline_compile_status", "raw_entry_point_status", "pipeline_entry_point_status",
    "termination_status", "done_reason", "extraction_status", "extraction_action",
    "reasoning_leakage", "functional_correctness", "format_violations",
    "transition_evidence_class", "causal_interpretation",
)

NONCOMPLIANCE_FIELDS = (
    "task_id", "seed", "generation_id", "strict_output_compliance",
    "generation_protocol_compliance", "code_fence_marker_count", "extra_text",
    "multiple_program_segments", "raw_compile_status", "raw_compile_diagnostic",
    "pipeline_compile_status", "raw_entry_point_status", "pipeline_entry_point_status",
    "termination_status", "done_reason", "extraction_status", "extraction_action",
    "reasoning_leakage", "functional_correctness", "format_violations",
    "reproducible_diagnostic",
)

TASK_FIELDS = (
    "task_id", "seed_11_transition", "seed_22_transition", "seed_33_transition",
    "seed_44_transition", "seed_55_transition", "fail_to_fail", "fail_to_pass",
    "pass_to_fail", "pass_to_pass", "net_rescues", "cross_seed_pattern",
    "causal_limit",
)

FAILURE_FIELDS = (
    "task_id", "seed", "generation_id", "raw_generation_sha256",
    "pipeline_output_sha256", "pipeline_extracted", "observed_status", "pipeline_status",
    "failure_stage", "exception_type_or_evaluator_outcome", "failure_category",
    "classification_basis", "format_or_extraction_failure", "syntax_failure",
    "entry_point_failure", "generation_truncation", "protocol_violation", "unknown_failure",
    "scaffold_candidate", "evaluator_blind_healer_candidate", "must_not_auto_repair",
    "semantic_risk", "review_status", "candidate_label_caveat",
)


class EvidenceReviewError(RuntimeError):
    """Raised before writing when formal evidence does not reconcile."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceReviewError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index(rows: Iterable[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in result, f"{label}: duplicate identity {key}")
        result[key] = row
    return result


def _bool(value: bool) -> str:
    return str(value).lower()


def _compile_diagnostic(source: str) -> tuple[str, str]:
    try:
        compile(source, "<saved-candidate-raw>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        if isinstance(exc, SyntaxError):
            diagnostic = f"SyntaxError:{exc.msg}:line={exc.lineno}:offset={exc.offset}"
        else:
            diagnostic = type(exc).__name__
        return "fail", diagnostic
    return "pass", "compile_ok"


def _entry_status(source: str | None, entry_point: str) -> str:
    if source is None:
        return "extraction_failed"
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, OverflowError):
        return "not_assessed_compile_fail"
    names = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    return "present" if entry_point in names else "missing"


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _journal_hash(repo_root: Path, run_relative: Path, generation_id: str) -> str:
    path = repo_root / run_relative / "j" / f"{generation_id}.json"
    _require(path.is_file(), f"missing journal {path}")
    return _sha256_bytes(path.read_bytes())


def _journal_inventory(repo_root: Path, run_relative: Path) -> dict[str, Any]:
    files = sorted((repo_root / run_relative / "j").glob("*.json"), key=lambda p: p.name)
    entries = [f"{path.name}:{_sha256_bytes(path.read_bytes())}" for path in files]
    return {
        "count": len(files),
        "inventory_sha256": _sha256_text("\n".join(entries) + "\n"),
    }


def _validate_protocol(plan: dict[str, Any], raw: dict[tuple[str, int], dict[str, Any]], label: str) -> None:
    _require(plan["expected_cells"] == 200, f"{label}: expected cell count drift")
    _require(plan["model"] == EXPECTED_MODEL, f"{label}: model drift")
    _require(plan["model_digest"] == EXPECTED_DIGEST, f"{label}: digest drift")
    _require(plan["quantization"] == EXPECTED_QUANTIZATION, f"{label}: quantization drift")
    _require(plan["seeds"] == EXPECTED_SEEDS, f"{label}: seed drift")
    _require(plan["ollama_request_timeout_seconds"] == 600.0, f"{label}: timeout drift")
    _require(plan["attempts_per_cell"] == 1, f"{label}: attempt policy drift")
    _require(plan["retry"] is False and plan["resume"] is False, f"{label}: retry/resume policy drift")
    _require(plan["selective_retry"] is False and plan["overwrite"] is False, f"{label}: selective retry/overwrite drift")
    _require(plan["healer"] is False and plan["pipeline_correction_is_healer"] is False, f"{label}: Healer accounting drift")
    params = plan["generation_parameters"]
    _require(params["thinking"] is False and params["stream"] is False, f"{label}: think/stream drift")
    expected_options = {name: params[name] for name in ("num_ctx", "num_predict", "temperature", "top_k", "top_p")}
    for key, row in raw.items():
        _require(row["generation_id"] == row["planned_cell_id"], f"{label} {key}: generation ID drift")
        _require(row["model"] == EXPECTED_MODEL and row["model_digest"] == EXPECTED_DIGEST, f"{label} {key}: model metadata drift")
        _require(row["retry_count"] == 0 and row["first_attempt"] is True, f"{label} {key}: retry drift")
        _require(row["transport_complete"] is True and row["model_generation_complete"] is True, f"{label} {key}: incomplete generation")
        _require(row["protocol_compliant"] is True and row["protocol_violations"] == [], f"{label} {key}: protocol violation")
        _require(row["reasoning_leakage"] is False and row["healer"] is False, f"{label} {key}: reasoning/Healer drift")
        request = row["request"]
        _require(request["think"] is False and request["stream"] is False, f"{label} {key}: request protocol drift")
        _require(request["model"] == EXPECTED_MODEL, f"{label} {key}: request model drift")
        options = dict(request["options"])
        _require(options.pop("seed") == key[1] and options == expected_options, f"{label} {key}: sampling drift")


def _failure_classification(
    pipeline: dict[str, Any], evaluation: dict[str, str], entry_point: str,
) -> dict[str, str]:
    base = census_v1._classify(pipeline, evaluation, entry_point)
    category = base["category"]
    return {
        "failure_stage": base["failure_stage"],
        "outcome": base["outcome"],
        "category": category,
        "basis": base["basis"],
        "scaffold": _bool(category == "extraction_or_format_failure"),
        "healer": _bool(category in {"syntax_failure", "missing_or_wrong_entry_point"}),
        "must_not_auto": _bool(category in {"unknown", "timeout_or_resource_failure", "functional_test_failure"}),
        "risk": base["risk"],
        "review": base["review"],
    }


def _source_hashes(repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = repo_root / relative
        _require(path.is_file(), f"missing formal source artifact: {relative.as_posix()}")
        hashes[relative.as_posix()] = _sha256_bytes(path.read_bytes())
    return hashes


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    p0_dir, ca_dir, paired_dir = repo_root / P0_RELATIVE, repo_root / CA_RELATIVE, repo_root / PAIRED_RELATIVE
    p0_plan, ca_plan = _read_json(p0_dir / "generation_plan.json"), _read_json(ca_dir / "generation_plan.json")
    _require(p0_plan["run_id"] == frozen.P0_RUN_ID, "P0 run ID drift")
    _require(ca_plan["run_id"] == recovery.CA_R002_RUN_ID, "Candidate r002 run ID drift")
    _require(ca_plan["candidate_exact_text_sha256"] == EXPECTED_CANDIDATE_HASH, "Candidate A exact-text hash drift")
    _require(_sha256_text(ca_plan["candidate_exact_text_utf8"]) == EXPECTED_CANDIDATE_HASH, "Candidate A exact text bytes drift")
    _require(ca_plan["predecessor_cells_reused"] == 0, "r001 cells reused by r002")

    planned = [(cell["task_id"], int(cell["seed"])) for cell in p0_plan["cells"]]
    ca_planned = [(cell["task_id"], int(cell["seed"])) for cell in ca_plan["cells"]]
    _require(len(planned) == len(set(planned)) == 200 and planned == ca_planned, "planned paired identity drift")

    collections = {
        "p0_raw": _index(_read_jsonl(p0_dir / "raw_generations.jsonl"), "P0 raw"),
        "p0_pipeline": _index(_read_jsonl(p0_dir / "pipeline_corrected.jsonl"), "P0 pipeline"),
        "p0_eval": _index(_read_csv(p0_dir / "evaluation_results.csv"), "P0 eval"),
        "ca_raw": _index(_read_jsonl(ca_dir / "raw_generations.jsonl"), "Candidate raw"),
        "ca_pipeline": _index(_read_jsonl(ca_dir / "pipeline_corrected.jsonl"), "Candidate pipeline"),
        "ca_eval": _index(_read_csv(ca_dir / "evaluation_results.csv"), "Candidate eval"),
        "paired": _index(_read_csv(paired_dir / "paired_cell_results.csv"), "paired results"),
    }
    expected_keys = set(planned)
    _require(all(set(rows) == expected_keys for rows in collections.values()), "formal artifact identity mismatch")
    _validate_protocol(p0_plan, collections["p0_raw"], "P0")
    _validate_protocol(ca_plan, collections["ca_raw"], "Candidate")

    r001_manifest = _read_json(repo_root / SOURCE_FILES[-1])
    r001_ids = {item["generation_id"] for item in r001_manifest["journal_records"]}
    ca_ids = {row["generation_id"] for row in collections["ca_raw"].values()}
    _require(not r001_ids & ca_ids, "Candidate r001 generation mixed into r002")
    _require(r001_manifest["valid_generation_for_formal_analysis"] == 0, "r001 formal-credit drift")

    entry_points = census_v1._load_entry_points(repo_root, p0_plan["task_ids"])
    paired_manifest = _read_json(paired_dir / "paired_analysis_manifest.json")
    prospective_result = prospective.build_analysis(frozen.P0_RUN_ID, recovery.CA_R002_RUN_ID)
    _require(paired_manifest["transition_counts"] == EXPECTED_TRANSITIONS, "saved transition counts drift")
    _require(prospective_result["transition_counts"] == EXPECTED_TRANSITIONS, "recomputed transition counts drift")
    recomputed_p = paired_math.exact_mcnemar_p(30, 15)
    _require(math.isclose(recomputed_p, 0.035697803555194696, abs_tol=1e-15), "McNemar calculation drift")
    _require(math.isclose(paired_manifest["exact_mcnemar_two_sided_p"], recomputed_p, abs_tol=1e-15), "saved McNemar p drift")

    cell_rows: list[dict[str, str]] = []
    noncompliance_rows: list[dict[str, str]] = []
    failure_rows: list[dict[str, str]] = []
    transition_by_task: dict[str, dict[int, str]] = {}

    for key in planned:
        task_id, seed = key
        p0_raw, p0_pipe, p0_eval = collections["p0_raw"][key], collections["p0_pipeline"][key], collections["p0_eval"][key]
        ca_raw, ca_pipe, ca_eval = collections["ca_raw"][key], collections["ca_pipeline"][key], collections["ca_eval"][key]
        paired = collections["paired"][key]
        _require(p0_raw["generation_id"] == p0_pipe["generation_id"] == p0_eval["generation_id"] == paired["p0_generation_id"], f"P0 generation relation drift {key}")
        _require(ca_raw["generation_id"] == ca_pipe["generation_id"] == ca_eval["generation_id"] == paired["candidate_generation_id"], f"Candidate generation relation drift {key}")
        _require(_sha256_text(p0_raw["raw_response"]) == p0_raw["raw_response_sha256"] == p0_pipe["source_raw_response_sha256"] == p0_eval["observed_output_sha256"], f"P0 raw hash relation drift {key}")
        _require(_sha256_text(ca_raw["raw_response"]) == ca_raw["raw_response_sha256"] == ca_pipe["source_raw_response_sha256"] == ca_eval["observed_output_sha256"], f"Candidate raw hash relation drift {key}")
        p0_pipeline_source = p0_pipe["pipeline_corrected_output"]
        if p0_pipeline_source is None:
            _require(
                p0_pipe["extraction_status"] != "extracted"
                and p0_pipe["pipeline_corrected_output_sha256"] is None
                and p0_eval["pipeline_corrected_output_sha256"] == "",
                f"P0 failed-extraction hash relation drift {key}",
            )
        else:
            _require(
                _sha256_text(p0_pipeline_source)
                == p0_pipe["pipeline_corrected_output_sha256"]
                == p0_eval["pipeline_corrected_output_sha256"],
                f"P0 pipeline hash relation drift {key}",
            )
        pipeline_source = ca_pipe["pipeline_corrected_output"]
        _require(_sha256_text(pipeline_source) == ca_pipe["pipeline_corrected_output_sha256"] == ca_eval["pipeline_corrected_output_sha256"], f"Candidate pipeline hash relation drift {key}")
        _require(paired["p0_pipeline_status"] == p0_eval["pipeline_corrected_status"] and paired["candidate_pipeline_status"] == ca_eval["pipeline_corrected_status"], f"paired status drift {key}")

        features = evidence._raw_features(ca_raw)
        strict = features["compliant"] and ca_raw["reasoning_leakage"] is False
        compile_status, compile_diagnostic = _compile_diagnostic(ca_raw["raw_response"])
        _require(compile_status == features["compile_status"], f"raw compile reconstruction drift {key}")
        violations = list(features["violations"])
        if ca_raw["reasoning_leakage"]:
            violations.append("reasoning_leakage")
        transition = paired["pipeline_transition"]
        transition_by_task.setdefault(task_id, {})[seed] = transition
        causal = (
            "paired_association_only_no_scaffold_semantic_causality_claim"
            if transition in {"fail_to_pass", "pass_to_fail"}
            else "descriptive_paired_outcome"
        )
        evidence_class = {
            "fail_to_pass": "paired_rescue",
            "pass_to_fail": "paired_regression_insufficient_functional_cause_evidence",
            "pass_to_pass": "common_pipeline_pass",
            "fail_to_fail": "persistent_pipeline_failure",
        }[transition]
        common = {
            "task_id": task_id,
            "seed": str(seed),
            "candidate_generation_id": ca_raw["generation_id"],
            "strict_output_compliance": _bool(strict),
            "generation_protocol_compliance": _bool(ca_raw["protocol_compliant"]),
            "code_fence_marker_count": str(features["marker_count"]),
            "extra_text": _bool(features["extra_text"]),
            "multiple_program_segments": _bool(features["multiple"]),
            "raw_compile_status": compile_status,
            "raw_compile_diagnostic": compile_diagnostic,
            "pipeline_compile_status": ca_eval["pipeline_corrected_syntax_compile_status"],
            "raw_entry_point_status": _entry_status(ca_raw["raw_response"], entry_points[task_id]),
            "pipeline_entry_point_status": _entry_status(pipeline_source, entry_points[task_id]),
            "termination_status": "length_terminated" if features["truncated"] else "stop_complete",
            "done_reason": str(ca_raw["generation_metadata"]["done_reason"]),
            "extraction_status": ca_pipe["extraction_status"],
            "extraction_action": evidence._pipeline_action(ca_pipe),
            "reasoning_leakage": _bool(ca_raw["reasoning_leakage"]),
            "functional_correctness": ca_eval["pipeline_corrected_status"],
            "format_violations": "|".join(violations) or "none",
        }
        cell_rows.append({
            "task_id": task_id,
            "seed": str(seed),
            "paired_identity": f"{task_id}|seed={seed}",
            "p0_generation_id": p0_raw["generation_id"],
            "candidate_generation_id": ca_raw["generation_id"],
            "p0_observed_status": p0_eval["observed_status"],
            "candidate_observed_status": ca_eval["observed_status"],
            "p0_pipeline_status": p0_eval["pipeline_corrected_status"],
            "candidate_pipeline_status": ca_eval["pipeline_corrected_status"],
            "pipeline_transition": transition,
            "p0_raw_sha256": p0_raw["raw_response_sha256"],
            "candidate_raw_sha256": ca_raw["raw_response_sha256"],
            "candidate_pipeline_sha256": ca_pipe["pipeline_corrected_output_sha256"],
            "p0_journal_file_sha256": _journal_hash(repo_root, P0_RELATIVE, p0_raw["generation_id"]),
            "candidate_journal_file_sha256": _journal_hash(repo_root, CA_RELATIVE, ca_raw["generation_id"]),
            **{name: value for name, value in common.items() if name not in {"task_id", "seed", "candidate_generation_id"}},
            "transition_evidence_class": evidence_class,
            "causal_interpretation": causal,
        })
        if not strict:
            noncompliance_rows.append({
                "task_id": task_id,
                "seed": str(seed),
                "generation_id": ca_raw["generation_id"],
                **{name: value for name, value in common.items() if name not in {"task_id", "seed", "candidate_generation_id"}},
                "reproducible_diagnostic": f"violations={common['format_violations']};{compile_diagnostic};done_reason={common['done_reason']}",
            })

        if ca_eval["pipeline_corrected_status"] == "fail":
            classification = _failure_classification(ca_pipe, ca_eval, entry_points[task_id])
            truncated = features["truncated"]
            protocol_violation = not ca_raw["protocol_compliant"]
            failure_rows.append({
                "task_id": task_id,
                "seed": str(seed),
                "generation_id": ca_raw["generation_id"],
                "raw_generation_sha256": ca_raw["raw_response_sha256"],
                "pipeline_output_sha256": ca_pipe["pipeline_corrected_output_sha256"],
                "pipeline_extracted": _bool(ca_pipe["extraction_status"] == "extracted"),
                "observed_status": ca_eval["observed_status"],
                "pipeline_status": ca_eval["pipeline_corrected_status"],
                "failure_stage": classification["failure_stage"],
                "exception_type_or_evaluator_outcome": classification["outcome"],
                "failure_category": classification["category"],
                "classification_basis": classification["basis"],
                "format_or_extraction_failure": _bool(classification["category"] == "extraction_or_format_failure"),
                "syntax_failure": _bool(classification["category"] == "syntax_failure"),
                "entry_point_failure": _bool(classification["category"] == "missing_or_wrong_entry_point"),
                "generation_truncation": _bool(truncated),
                "protocol_violation": _bool(protocol_violation),
                "unknown_failure": _bool(classification["category"] == "unknown"),
                "scaffold_candidate": _bool(classification["category"] == "extraction_or_format_failure" or truncated),
                "evaluator_blind_healer_candidate": classification["healer"],
                "must_not_auto_repair": classification["must_not_auto"],
                "semantic_risk": classification["risk"],
                "review_status": classification["review"],
                "candidate_label_caveat": "candidate_label_not_validated_repair_rule",
            })

    _require(len(cell_rows) == 200 and len(noncompliance_rows) == 22, "cell/strict format count drift")
    _require(len(failure_rows) == 147, "Candidate failure count drift")
    _require(
        all(
            sum(row["pipeline_transition"] == name for row in cell_rows) == count
            for name, count in EXPECTED_TRANSITIONS.items()
        ),
        "rebuilt cell transition count drift",
    )

    task_rows: list[dict[str, str]] = []
    for task_id in p0_plan["task_ids"]:
        profiles = transition_by_task[task_id]
        _require(set(profiles) == set(EXPECTED_SEEDS), f"incomplete task profile {task_id}")
        counts = Counter(profiles.values())
        task_rows.append({
            "task_id": task_id,
            **{f"seed_{seed}_transition": profiles[seed] for seed in EXPECTED_SEEDS},
            **{name: str(counts[name]) for name in ("fail_to_fail", "fail_to_pass", "pass_to_fail", "pass_to_pass")},
            "net_rescues": str(counts["fail_to_pass"] - counts["pass_to_fail"]),
            "cross_seed_pattern": (
                "consistent_rescue_5_of_5" if counts["fail_to_pass"] == 5 else
                "regression_concentrated_4_of_5" if counts["pass_to_fail"] == 4 else
                "mixed_or_partial"
            ),
            "causal_limit": "association_across_frozen_seeds_not_semantic_causal_identification",
        })

    task_index = {row["task_id"]: row for row in task_rows}
    _require(task_index["Mbpp/6"]["fail_to_pass"] == "5", "known Mbpp/6 rescue profile drift")
    _require(task_index["Mbpp/14"]["pass_to_fail"] == "4" and task_index["Mbpp/607"]["pass_to_fail"] == "4", "known regression concentration drift")
    regression_tasks = {row["task_id"] for row in cell_rows if row["pipeline_transition"] == "pass_to_fail"}
    _require(regression_tasks == {"Mbpp/432", "Mbpp/572", "Mbpp/14", "Mbpp/722", "Mbpp/607", "Mbpp/786"}, "regression task set drift")

    failure_counts = dict(sorted(Counter(row["failure_category"] for row in failure_rows).items()))
    truncation_failures = sum(row["generation_truncation"] == "true" for row in failure_rows)
    protocol_failures = sum(row["protocol_violation"] == "true" for row in failure_rows)
    source_hashes = _source_hashes(repo_root)
    journal_inventories = {
        "p0_r001": _journal_inventory(repo_root, P0_RELATIVE),
        "candidate_r002": _journal_inventory(repo_root, CA_RELATIVE),
    }
    _require(journal_inventories["p0_r001"]["count"] == journal_inventories["candidate_r002"]["count"] == 200, "journal count drift")

    return {
        "cell_rows": cell_rows,
        "noncompliance_rows": noncompliance_rows,
        "task_rows": task_rows,
        "failure_rows": failure_rows,
        "source_hashes": source_hashes,
        "journal_inventories": journal_inventories,
        "failure_counts": failure_counts,
        "truncation_failures": truncation_failures,
        "protocol_failures": protocol_failures,
        "mcnemar_p": recomputed_p,
        "paired_manifest": paired_manifest,
    }


def _report(result: dict[str, Any]) -> bytes:
    categories = result["failure_counts"]
    task_rows = {row["task_id"]: row for row in result["task_rows"]}
    noncompliance_counts = Counter()
    for row in result["noncompliance_rows"]:
        for violation in row["format_violations"].split("|"):
            noncompliance_counts[violation] += 1
    regression_counts = {
        row["task_id"]: int(row["pass_to_fail"])
        for row in result["task_rows"] if int(row["pass_to_fail"])
    }
    lines = [
        "# Milestone 2F：Candidate A expansion證據審查與升格判定",
        "",
        "## 一頁結論",
        "",
        "Candidate A在這批40題、每題5個固定seed的development expansion中，把Pipeline-corrected通過率從P0的19%（38/200）提高到26.5%（53/200），淨增加15格，也就是7.5個百分點。配對結果有30個rescues、15個regressions；two-sided exact McNemar p = 0.0356978，因此預註冊的correctness improvement統計條件成立。這是development內的配對關聯證據，不證明Scaffold造成某一種語意修正。",
        "",
        "然而Candidate A不能升格為official Scaffold v1：strict Python-only只有89%（178/200），低於事先凍結的90%門檻。fence為0%、extra text為0%、Pipeline extraction為100%，correctness safety gate與protocol gate都通過，但promotion要求完整通過所有gate；本輪不事後把89%改寫成及格。正確表述是：**correctness有顯著改善，但未滿足預註冊完整promotion gates。**",
        "",
        "## 1. 完整性與重現性",
        "",
        "- P0與Candidate A各有200個generation、200個evaluation rows與200個journals；40 tasks × 5 seeds形成200組唯一且完整配對。",
        "- model為`qwen3.5:9b`，digest、Q4_K_M、think=false與全部sampling參數均符合凍結計畫；兩組retry皆為0。",
        "- raw文字SHA、Pipeline來源／輸出SHA、evaluation SHA、generation ID與paired identities逐格相符。",
        "- Candidate r001的兩個事故generation ID沒有出現在r002，r001對正式分析仍為0格。",
        "- 重新計算transition為132 fail→fail、30 fail→pass、15 pass→fail、23 pass→pass；exact McNemar p與正式paired manifest一致。",
        "- 本分析未呼叫模型、未執行EvalPlus，也沒有將Pipeline correction稱為Healer。",
        "",
        "## 2. 22格格式不合規是什麼？",
        "",
        f"22格是依同一個預註冊操作定義逐格重建；違規診斷計數（可重疊）為`{json.dumps(dict(sorted(noncompliance_counts.items())), ensure_ascii=False)}`。每格的done reason、compile diagnostic、entry point、extraction與功能結果都列在CSV。",
        "",
        "這四個概念不可混用：strict output compliance衡量raw輸出是否可直接當Python檔；generation protocol compliance衡量transport、一次嘗試與thinking等執行規則；Pipeline extraction只說既有extractor是否產生程式；functional correctness才是保存的EvalPlus pass/fail。某格protocol compliant或extraction成功，仍可能格式不合規或功能失敗。",
        "",
        "## 3. Rescues、regressions與跨seed集中性",
        "",
        "30個rescues、15個regressions及23個共同成功均逐格列入ledger。Mbpp/6是5/5 rescues，表示這個task在五個凍結seed上方向一致；這仍是關聯，不是語意因果識別。",
        "",
        f"15個regressions只出現在6題：`{json.dumps(regression_counts, ensure_ascii=False)}`。其中Mbpp/14與Mbpp/607各4/5 regressions。現有evaluator只保存generic fail，無法指出錯誤演算法、邊界案例或其他功能原因，所以15格都標為`insufficient_evidence`，不能宣稱是Scaffold造成特定語意錯誤。",
        "",
        "## 4. Candidate A的147個Pipeline failures",
        "",
        f"既有taxonomy的primary分類為`{json.dumps(categories, ensure_ascii=False)}`；另有{result['truncation_failures']}格failure與length termination重疊，protocol violation為{result['protocol_failures']}格。truncation是正交診斷，不拿來覆蓋syntax、entry-point或unknown primary category。",
        "",
        "只有format/extraction或length termination可作為下一版Scaffold的候選問題；syntax與missing entry point可列為evaluator-blind Healer研究候選，但屬高風險，標籤不等於已驗證repair rule。generic evaluator unknown、timeout及需要語意判斷的失敗不得自動修復，也不得因unknown硬分配給Healer。Pipeline correction不是Healer。",
        "",
        "## 5. Promotion decision",
        "",
        "| Gate／rule | 結果 | 直接證據 |",
        "|---|---:|---|",
        "| Strict Python-only ≥90% | Fail | 89%（178/200） |",
        "| Fence ≤5% | Pass | 0% |",
        "| Extra text ≤5% | Pass | 0% |",
        "| Pipeline extraction ≥95% | Pass | 100% |",
        "| Correctness safety | Pass | 53≥38；30 rescues≥15 regressions；regressions全揭露 |",
        "| Protocol | Pass | reasoning leakage 0；transport-complete ITT；無retry |",
        "| Correctness claim rule | Pass | 30>15且exact McNemar p=0.0356978<0.05 |",
        "| 完整promotion | **Fail** | format gate未通過，Candidate A不得升格official v1 |",
        "",
        "## 6. 下一步：Scaffold還是Healer？",
        "",
        "先針對22格的可觀察格式診斷形成Candidate B的evidence-based設計需求，再以未啟用development tasks另立前瞻protocol；本輪不設計、實作或凍結Candidate B。Healer只能另行研究那些可由saved source做evaluator-blind判斷的syntax或entry-point候選，而且必須先驗證不改變語意。unknown功能失敗不能交給Healer。",
        "",
        "## 7. 外推限制",
        "",
        "所有數字只適用於這40題expansion development、這個模型版本、量化、sampling、Scaffold文字與五個seed。沒有讀取validation、internal/external confirmatory、excluded historical或sealed reserve；因此不能外推到封存split、其他模型、其他sampling或正式benchmark效能。",
        "",
        "完成標記：`CANDIDATE_A_EXPANSION_EVIDENCE_REVIEW_COMPLETED`",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    result = build_analysis(repo_root)
    outputs = {
        "expansion_cell_evidence.csv": _csv_bytes(result["cell_rows"], CELL_FIELDS),
        "candidate_a_format_noncompliance.csv": _csv_bytes(result["noncompliance_rows"], NONCOMPLIANCE_FIELDS),
        "rescue_regression_task_summary.csv": _csv_bytes(result["task_rows"], TASK_FIELDS),
        "candidate_a_failure_census.csv": _csv_bytes(result["failure_rows"], FAILURE_FIELDS),
        "candidate_a_expansion_analysis_zh.md": _report(result),
    }
    manifest = {
        "analysis_version": "milestone_2f_candidate_a_expansion_evidence_review_v1",
        "completion_marker": "CANDIDATE_A_EXPANSION_EVIDENCE_REVIEW_COMPLETED",
        "expected_starting_head": EXPECTED_HEAD,
        "development_only": True,
        "external_generalization_claimed": False,
        "model_calls": 0,
        "evalplus_executions": 0,
        "formal_inputs_modified": False,
        "p0_run_id": frozen.P0_RUN_ID,
        "candidate_run_id": recovery.CA_R002_RUN_ID,
        "invalidated_candidate_r001_formal_cells": 0,
        "candidate_exact_text_sha256": EXPECTED_CANDIDATE_HASH,
        "cell_counts": {"p0": 200, "candidate_a": 200, "paired": 200},
        "transition_counts": EXPECTED_TRANSITIONS,
        "p0_pipeline_pass": 38,
        "candidate_pipeline_pass": 53,
        "net_gain_cells": 15,
        "net_gain_percentage_points": 7.5,
        "exact_mcnemar_two_sided_p": result["mcnemar_p"],
        "format": {"strict_python_only": {"count": 178, "rate": 0.89}, "noncompliant": 22, "fence_rate": 0.0, "extra_text_rate": 0.0, "pipeline_extraction_rate": 1.0},
        "gates": {"format_gate": False, "pipeline_correctness_safety_gate": True, "protocol_gate": True, "correctness_improvement_condition": True, "full_promotion": False},
        "promotion_decision": "correctness significantly improved on development, but preregistered full promotion gates were not all satisfied; Candidate A remains not official v1",
        "failure_category_counts": result["failure_counts"],
        "failure_truncation_overlap_count": result["truncation_failures"],
        "failure_protocol_violation_count": result["protocol_failures"],
        "source_artifact_sha256": result["source_hashes"],
        "journal_inventories": result["journal_inventories"],
        "output_sha256_excluding_manifest": {name: _sha256_bytes(value) for name, value in sorted(outputs.items())},
        "restrictions_observed": [
            "development artifacts only", "no model call", "no regeneration retry or resume",
            "no EvalPlus execution", "no sealed-role access", "no gate changes",
            "no Candidate B Scaffold v1 or Healer implementation",
        ],
    }
    outputs["milestone_2f_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "Milestone 2F output directory missing")
        actual_names = {path.name for path in output_dir.iterdir() if path.is_file()}
        _require(actual_names == set(outputs), "Milestone 2F output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "Milestone 2F output directory already exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify frozen bytes without writing")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        write_outputs(check=args.check)
    except EvidenceReviewError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
