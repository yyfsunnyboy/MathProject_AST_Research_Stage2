#!/usr/bin/env python3
"""Independent static audit of Batch03 provisional adjudication v1.

Independent expectations are encoded from preserved source, public contracts,
and existing evaluator metadata before comparison with provisional records.
No candidate, test, diagnostic, model, validation, or Healer is executed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1_independent_audit_v1")
START_HEAD = "923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS = "INDEPENDENT_STATIC_AUDIT_COMPLETE_MATERIAL_FINDINGS"
VERDICT = "BATCH03_PROVISIONAL_REVISION_REQUIRED"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/batch03_roster.csv")
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
ROSTER_AUDIT_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1_independent_audit_v1/manifest.json")
PROVISIONAL_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1")
RECORDS = PROVISIONAL_DIR / "adjudication_records.csv"
PROVISIONAL_MANIFEST = PROVISIONAL_DIR / "manifest.json"
PROVISIONAL_SUMMARY = PROVISIONAL_DIR / "adjudication_summary.json"
PROVISIONAL_EVIDENCE = PROVISIONAL_DIR / "per_cell_evidence_ledger.csv"
PROVISIONAL_MECHANISMS = PROVISIONAL_DIR / "mechanism_ledger.csv"
PROVISIONAL_CONDITIONAL = PROVISIONAL_DIR / "conditional_diagnostic_queue.csv"
PROVISIONAL_GAPS = PROVISIONAL_DIR / "unresolved_evidence_gaps.csv"
PROVISIONAL_EXECUTION = PROVISIONAL_DIR / "execution_counts.json"
PROVISIONAL_PROVENANCE = PROVISIONAL_DIR / "provenance.json"
PROVISIONAL_REPORT = PROVISIONAL_DIR / "report_zh.md"
PROVISIONAL_BUILDER = Path("scripts/adjudicate_candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1.py")
PROVISIONAL_TEST = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1.py")
ACCOUNTS = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv")
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")

SOURCE_HASHES = {
    ROSTER: "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",
    ROSTER_MANIFEST: "42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c",
    ROSTER_AUDIT_MANIFEST: "ba20a3ab6e3200f2c9c2effbabd27537f6f4b1415637fec5846c80ec90425a4a",
    RECORDS: "dbc19dc8b0a1004013b51c94fe66d24b1def455911b9ac69ea56f611d9e6a0fd",
    PROVISIONAL_MANIFEST: "8467b8713144182abcb8d21fb40454c80daec89459fb42077d16c549231e2282",
    PROVISIONAL_SUMMARY: "80386b6672cb25ba6d709abd97c4cbb0743761bb4ad8062c66410f15cc32112c",
    PROVISIONAL_EVIDENCE: "0d1c8f5143eedba9a863ea6b58c247ebfc6397848f3fb04f318970b072472b53",
    PROVISIONAL_MECHANISMS: "2ddb06e9e81e5053b0b44dbc19b32bd369925fab33bfe6f838cd93f8c18de14f",
    PROVISIONAL_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    PROVISIONAL_GAPS: "f728a5088f3c169969196caceb85258b1045cc48bde0d762ef6b6885715d7c60",
    PROVISIONAL_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    PROVISIONAL_PROVENANCE: "fcfaa41e42a7989eac425e0b0d54361381e862802e237f02906127934dac924f",
    PROVISIONAL_REPORT: "74fcccc9ec81b13de7cb0f266b6e9858fdb850ba5fd0b5752cd9e2bf05ee75ee",
    PROVISIONAL_BUILDER: "e8c5d3e68656154a29171af93c05cab33f7e49c7c15636be66e6c9e433e81095",
    PROVISIONAL_TEST: "d0dfe328ec24df12110156d06d289197fc859257a6050b79222425a09c5beb85",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
}

TAXONOMY_SHA = "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0"
MATERIAL_IDS = {
    "3b802dcce09d236485df19d1c985675e091e74cbb5fcbf6e73f753d873f62e88",
    "71012956073b53a6d9d9341681ec221238d2d1fe8cdd2dfc5a82291b2fb7d44f",
}

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "audit_status", "independent_primary", "provisional_primary",
    "independent_secondary", "provisional_secondary", "independent_confidence",
    "provisional_confidence", "independent_outcome", "provisional_outcome",
    "independent_healer", "provisional_healer", "field_differences_json",
    "independent_evidence", "audit_rationale", "impact",
)
DIFF_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "audit_status",
    "field_name", "provisional_value", "recommended_value", "evidence", "impact",
)
MATERIAL_FIELDS = DIFF_FIELDS + ("recommended_action",)
NON_MATERIAL_FIELDS = DIFF_FIELDS + ("disposition",)
HEALER_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "independent_healer", "provisional_healer", "audit_status", "safety_evidence", "minimal_diagnostic")
UNRESOLVED_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "audit_status", "competing_explanations_closed", "gap_specificity", "minimal_diagnostic_status", "independent_rationale")


class AuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    with (repo / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (repo / path).read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _taxonomy_path_and_sha(repo: Path) -> tuple[Path, str]:
    manifest = json.loads((repo / PROVISIONAL_MANIFEST).read_text(encoding="utf-8"))
    provenance = json.loads((repo / PROVISIONAL_PROVENANCE).read_text(encoding="utf-8"))
    _require(manifest["taxonomy_v31_sha256"] == TAXONOMY_SHA, "manifest taxonomy SHA drift")
    matches = [(Path(path), digest) for path, digest in provenance["source_hashes"].items() if "AI_生成程式共同失敗分類標準" in path]
    _require(len(matches) == 1, "taxonomy path resolution drift")
    path, digest = matches[0]
    _require(digest == TAXONOMY_SHA and path.is_file(), "taxonomy provenance drift")
    _require(_sha(path.read_bytes()) == TAXONOMY_SHA, "authoritative taxonomy byte drift")
    return path, digest


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        _require((repo / path).is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha((repo / path).read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")
    _taxonomy_path_and_sha(repo)


def _exp(primary: str, mechanisms: dict[str, str], evidence: str, rationale: str, *, secondary: str = "", confidence: str = "HIGH") -> dict[str, Any]:
    return {"primary": primary, "secondary": secondary, "confidence": confidence, "outcome": "VALID_MODEL_OUTCOME", "healer": "abstain", "mechanisms": mechanisms, "evidence": evidence, "rationale": rationale}


GENERIC_UNRESOLVED = {
    "public_examples_non_discriminating": "CONFIRMED",
    "plus_failure_not_localized": "CONFIRMED",
    "diagnostic_execution_required": "SUPPORTED",
}

EXPECTATIONS = {
    "32d57f4a3d936a6e9c655af0f10d9b2a06578a1adedc54df98892a4d6b795bd3": _exp("UNRESOLVED", GENERIC_UNRESOLVED, "sum-of-even-squares source satisfies n=2 and base; first plus case absent", "No public static counterexample closes L5 or runtime failure.", confidence="LOW"),
    "32edbe1532826de4a3416eb06e43c97bc8b4687cce8161729414d2811d583c85": _exp("L5", {"incorrect_ordering_semantics":"CONFIRMED","algorithm_reconstruction_required":"SUPPORTED"}, "source yields [10,15,20,30], public requires [10,20,30,15]", "Direct public semantic contradiction closes L5."),
    "392899632bcf304144c5f48b7ac2120b6a200c6ce845b067a875cb427149c55a": _exp("L5", {"precision_validation_error":"CONFIRMED","edge_case_omission":"CONFIRMED"}, "source never constrains fractional digit count", "Precision-two predicate is not implemented."),
    "3b802dcce09d236485df19d1c985675e091e74cbb5fcbf6e73f753d873f62e88": _exp("L5", {"frequency_one_instead_of_distinct_value":"CONFIRMED","semantic_goal_drift":"CONFIRMED"}, "source omits repeated 1 and returns 20; public result 21 counts each distinct value once", "Primary L5 is correct, but the provisional mechanism tag names the inverse behavior."),
    "4378e8d490f8f3ec4fca63d29b42264fbfb25d6f05a847acf0868d3b54f7c1a9": _exp("L5", {"precision_validation_error":"CONFIRMED","semantic_goal_drift":"CONFIRMED"}, "source rounds before measuring precision", "Longer fractions are accepted after rounding."),
    "53e1494c968d9de1060a6f2704a8ca57d68b803f0afb1ab122539dfdb36dd039": _exp("L5", {"wrong_boundary_condition":"CONFIRMED","duplicate_value_semantics":"CONFIRMED"}, "strict < binary search computes lower bound", "Right insertion requires equality to advance."),
    "578c5bf9895c10e09e10e0c1194a2ddf6b87d783e19582571098150b36269dea": _exp("L5", {"incorrect_ordering_semantics":"CONFIRMED","algorithm_reconstruction_required":"SUPPORTED"}, "source yields list1 order contrary to public output", "Direct public semantic contradiction closes L5."),
    "5b58236a8dd74781896f67d4a87859b04f6c7abba8fda28db27f116dbd4ccf8e": _exp("L5", {"algorithmic_error":"CONFIRMED","incorrect_search_bound":"CONFIRMED"}, "public n=5 loop excludes outer square 3 and returns False", "Public case directly falsifies algorithm."),
    "5ed7bb37b7f3170d75713428f8354054a4844c9100019b561eb00fc00144aba2": _exp("UNRESOLVED", GENERIC_UNRESOLVED, "same correct positive-n loop; public/base pass; first plus case absent", "Boundary or domain failure cannot be localized statically.", confidence="LOW"),
    "6107650d8a56ae0107d45b67e7571175e6698d84bc9f0ede8dff58f8f4929424": _exp("UNRESOLVED", GENERIC_UNRESOLVED, "standard bracket stack satisfies public/base; first plus expression absent", "Non-bracket policy or another hidden boundary remains unclosed.", confidence="LOW"),
    "65b945dcb63cfad531df7d56b1817fde397b27f6dff98c6581a337b4c41d31c3": _exp("L5", {"capital_boundary_detection_error":"CONFIRMED","edge_case_omission":"CONFIRMED"}, "internal uppercase after a letter is never marked as a boundary", "Stated capital-word splitting semantics are absent."),
    "6d29dd4ee79a526d569748360106a53eb4e80487bd7e69eefe2cb8e0e714aed7": _exp("L5", {"wrong_boundary_condition":"CONFIRMED","duplicate_value_semantics":"CONFIRMED"}, "first >= branch always adds one", "Below-minimum and equal-run behavior contradict right insertion."),
    "6d322d7901db24de0d45c8ba71525e66d011932474ab8aeae274058d5f8def35": _exp("UNRESOLVED", {**GENERIC_UNRESOLVED,"sublist_semantics_ambiguous":"SUSPECTED"}, "contiguous implementation satisfies nondiscriminating public/base", "Public text and preserved outcomes do not close contiguous vs noncontiguous semantics.", confidence="LOW"),
    "71012956073b53a6d9d9341681ec221238d2d1fe8cdd2dfc5a82291b2fb7d44f": _exp("L5", {"frequency_one_instead_of_distinct_value":"CONFIRMED","semantic_goal_drift":"CONFIRMED"}, "source omits repeated 1 and returns 20; public result 21 counts each distinct value once", "Primary L5 is correct, but the provisional mechanism tag names the inverse behavior."),
    "77223f4bbae7279a826f083779d37952881c8d4d61f1bb229600fefffcf4c5fd": _exp("UNRESOLVED", {**GENERIC_UNRESOLVED,"unsupported_input_guard":"SUSPECTED"}, "formula satisfies public/base but guard role is not defined", "Third-parameter contract or first plus tuple is needed.", confidence="LOW"),
    "7a42d5510092e63637c51173576a5bbdd091d9fb18fbc36627f0cd73a6dc86a9": _exp("L5", {"wrong_boundary_condition":"CONFIRMED","duplicate_value_semantics":"CONFIRMED"}, "strict < binary search computes lower bound", "Right insertion requires equality to advance."),
    "7c7bf358de0139c9688826eac3ca6414efd233291d4226cc2f656c58f9c3a8a3": _exp("UNRESOLVED", {**GENERIC_UNRESOLVED,"code_bloat":"CONFIRMED","hardcoded_public_example":"CONFIRMED"}, "general mask and hardcoded n=9 both satisfy public/base", "Signed/small-value representation cannot be inferred from undisclosed plus failure.", confidence="LOW"),
    "7e865e15f3bf0cfe4619ac724f009fa7a0d5134e1660e32f1a74469073da8824": _exp("L2", {"output_schema_mismatch":"CONFIRMED","semantic_goal_drift":"CONFIRMED","algorithm_reconstruction_required":"SUPPORTED"}, "required is_polite returns bool while public requires integer 11", "L2 is primary; nth_polite/helper binding prevents a unique safe alias and L5 remains secondary.", secondary="L5"),
    "80e9e1cc3a249dd8da36d260f934304728b7eb6a6438bdb0f851e45f47ab74bb": _exp("L5", {"wrong_parameter_semantics":"CONFIRMED","incorrect_pair_domain":"CONFIRMED","algorithmic_error":"CONFIRMED"}, "k is used as XOR threshold and public sum 47 is not produced", "Public case directly establishes semantic misinterpretation."),
    "83b0f95093eb347659aaf335ea129890f0d3be93e35b8a532e0d7968f916e795": _exp("UNRESOLVED", {**GENERIC_UNRESOLVED,"sublist_semantics_ambiguous":"SUSPECTED"}, "contiguous implementation satisfies nondiscriminating public/base", "Public text and preserved outcomes do not close sublist semantics.", confidence="LOW"),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    records = _read_csv(repo, RECORDS)
    accounts = {r["program_id"]: r for r in _read_jsonl(repo, ACCOUNTS) if r["healer_account"] == "H0"}
    tasks = {r["task_id"]: r for r in _read_jsonl(repo, TASKS)}
    evals = {r["program_id"]: r for r in _read_csv(repo, EVALPLUS) if r["healer_account"] == "H0"}
    prep = {r["program_id"]: r for r in _read_csv(repo, PREPARATION)}
    _require(len(roster) == len(records) == 20 and set(EXPECTATIONS) == {r["program_id"] for r in roster}, "20-cell audit closure drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in records], "record order drift")

    findings: list[dict[str, str]] = []
    differences: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    healer_rows: list[dict[str, str]] = []
    unresolved_rows: list[dict[str, str]] = []
    inferred_primary = Counter()
    inferred_secondary = Counter()
    inferred_confidence = Counter()
    inferred_healer = Counter()
    for rr, record in zip(roster, records):
        pid = rr["program_id"]
        exp = EXPECTATIONS[pid]
        _require(record["cell_identity_sha256"] == rr["cell_identity_sha256"], f"cell identity drift: {pid}")
        _require(record["source_sha256"] == rr["source_sha256"] == accounts[pid]["evaluation_source_sha256"] == prep[pid]["evaluation_source_sha256"], f"source closure drift: {pid}")
        _require(tasks[rr["task_id"]]["task_id"] == rr["task_id"] and pid in evals, f"evidence closure drift: {pid}")
        actual_mechanisms = {item["tag"]: item["strength"] for item in json.loads(record["mechanism_tags_json"])}
        field_diffs: list[str] = []
        comparisons = {
            "primary_layer": (record["primary_layer"], exp["primary"]),
            "secondary_layer": (record["secondary_layer"], exp["secondary"]),
            "confidence": (record["confidence"], exp["confidence"]),
            "outcome_validity": (record["outcome_validity"], exp["outcome"]),
            "healer_eligibility": (record["healer_eligibility"], exp["healer"]),
            "mechanism_tags_json": (actual_mechanisms, exp["mechanisms"]),
        }
        for field, (actual, recommended) in comparisons.items():
            if actual != recommended:
                field_diffs.append(field)
                row = {
                    "batch_rank": record["batch_rank"], "program_id": pid,
                    "cell_identity_sha256": record["cell_identity_sha256"],
                    "audit_status": "MATERIAL" if field == "mechanism_tags_json" else "MATERIAL",
                    "field_name": field,
                    "provisional_value": json.dumps(actual, ensure_ascii=False, sort_keys=True) if isinstance(actual, dict) else actual,
                    "recommended_value": json.dumps(recommended, ensure_ascii=False, sort_keys=True) if isinstance(recommended, dict) else recommended,
                    "evidence": exp["evidence"],
                    "impact": "mechanism direction is reversed; layer/confidence/outcome/Healer distributions remain unchanged" if field == "mechanism_tags_json" else "adjudication field changes",
                }
                differences.append(row)
                material.append({**row, "recommended_action": "replace inverse tag with frequency_one_instead_of_distinct_value; preserve semantic_goal_drift"})
        completeness = {
            "failure_chain": bool(record["failure_chain"]), "evidence_present": bool(record["evidence_present"]),
            "evidence_missing": bool(record["evidence_missing"]), "competing_explanations": bool(record["competing_explanations"]),
            "reason": bool(record["reason"]), "citations": all(token in record["evidence_citations"] for token in (ACCOUNTS.as_posix(), TASKS.as_posix(), EVALPLUS.as_posix(), "AI_生成程式共同失敗分類標準")),
        }
        if exp["primary"] == "UNRESOLVED":
            completeness["minimal_future_diagnostic"] = bool(record["minimal_future_diagnostic"])
        missing_fields = [name for name, ok in completeness.items() if not ok]
        _require(not missing_fields, f"evidence field incomplete {pid}: {missing_fields}")
        status = "MATERIAL" if field_diffs else "AFFIRMED"
        findings.append({
            "batch_rank": record["batch_rank"], "program_id": pid, "cell_identity_sha256": record["cell_identity_sha256"], "source_sha256": record["source_sha256"],
            "audit_status": status, "independent_primary": exp["primary"], "provisional_primary": record["primary_layer"],
            "independent_secondary": exp["secondary"], "provisional_secondary": record["secondary_layer"],
            "independent_confidence": exp["confidence"], "provisional_confidence": record["confidence"],
            "independent_outcome": exp["outcome"], "provisional_outcome": record["outcome_validity"],
            "independent_healer": exp["healer"], "provisional_healer": record["healer_eligibility"],
            "field_differences_json": json.dumps(field_diffs, separators=(",", ":")),
            "independent_evidence": exp["evidence"], "audit_rationale": exp["rationale"],
            "impact": "mechanism-only revision required" if field_diffs else "none",
        })
        healer_rows.append({
            "batch_rank": record["batch_rank"], "program_id": pid, "cell_identity_sha256": record["cell_identity_sha256"],
            "independent_healer": "abstain", "provisional_healer": record["healer_eligibility"], "audit_status": "AFFIRMED",
            "safety_evidence": "semantic/algorithm change required" if exp["primary"] in {"L2", "L5"} else "root layer and unique local repair not closed",
            "minimal_diagnostic": record["minimal_future_diagnostic"] if exp["primary"] == "UNRESOLVED" else "",
        })
        if exp["primary"] == "UNRESOLVED":
            unresolved_rows.append({
                "batch_rank": record["batch_rank"], "program_id": pid, "cell_identity_sha256": record["cell_identity_sha256"],
                "audit_status": "AFFIRMED", "competing_explanations_closed": "false",
                "gap_specificity": "SPECIFIC", "minimal_diagnostic_status": "MINIMAL_NON_ORACLE",
                "independent_rationale": exp["rationale"],
            })
        inferred_primary[exp["primary"]] += 1
        inferred_secondary[exp["secondary"] or "empty"] += 1
        inferred_confidence[exp["confidence"]] += 1
        inferred_healer[exp["healer"]] += 1

    _require({r["program_id"] for r in findings if r["audit_status"] == "MATERIAL"} == MATERIAL_IDS, "material cell closure drift")
    _require(len(material) == 2 and len(differences) == 2, "field difference closure drift")
    _require(len(unresolved_rows) == 7 and all(r["audit_status"] == "AFFIRMED" for r in healer_rows), "focused audit closure drift")
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT, "cells": 20,
        "affirmed": 18, "non_material": 0, "material": 2, "field_level_differences": 2,
        "identity_source_closure": 20, "unique_program_id": 20, "unique_cell_identity": 20,
        "unique_source_sha256": len({r["source_sha256"] for r in records}),
        "shared_source_groups": 1, "shared_source_explanation": "two distinct cells share byte-identical generated source but retain distinct program/cell/generation identities",
        "inferred_primary_distribution": dict(sorted(inferred_primary.items())),
        "inferred_secondary_distribution": dict(sorted(inferred_secondary.items())),
        "inferred_confidence_distribution": dict(sorted(inferred_confidence.items())),
        "inferred_outcome_distribution": {"VALID_MODEL_OUTCOME": 20},
        "inferred_healer_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "l2_cells_affirmed": 1, "l5_cells_affirmed_layer": 12,
        "unresolved_cells_affirmed": 7, "healer_dispositions_affirmed": 20,
        "upstream_modified": False, "new_runtime_observations": 0,
    }
    return {"findings": findings, "differences": differences, "material": material, "non_material": [], "healer": healer_rows, "unresolved": unresolved_rows, "summary": summary}


def _report(summary: dict[str, Any], material: list[dict[str, str]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3.1：Batch03 provisional v1 獨立audit", "",
        f"**狀態：`{STATUS}`**", "",
        f"- AFFIRMED：{summary['affirmed']}", f"- NON_MATERIAL：{summary['non_material']}", f"- MATERIAL：{summary['material']}", "",
        "兩個MATERIAL finding均為同一方向性mechanism錯誤：candidate只計出現一次的值，公開結果要求distinct值各計一次；",
        "原tag `dedupe_instead_of_unique_occurrence` 描述的是相反方向。建議改為 `frequency_one_instead_of_distinct_value`，",
        "保留L5、HIGH、VALID_MODEL_OUTCOME、abstain與`semantic_goal_drift`。", "",
        f"- audit後Primary：{summary['inferred_primary_distribution']}",
        f"- audit後Healer：{summary['inferred_healer_distribution']}",
        "- 7格UNRESOLVED、12格L5 layer、1格L2及20格Healer disposition其餘均獨立affirm。", "",
        "未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型；未修改provisional。", "",
    ]
    return "\n".join(lines)


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "per_cell_audit_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "field_level_difference_ledger.csv": _csv_bytes(DIFF_FIELDS, analysis["differences"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "non_material_findings.csv": _csv_bytes(NON_MATERIAL_FIELDS, analysis["non_material"]),
        "healer_disposition_audit.csv": _csv_bytes(HEALER_FIELDS, analysis["healer"]),
        "unresolved_audit.csv": _csv_bytes(UNRESOLVED_FIELDS, analysis["unresolved"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], analysis["material"]).encode("utf-8"),
    }
    taxonomy_path, taxonomy_sha = _taxonomy_path_and_sha(repo)
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "provisional_records_sha256": SOURCE_HASHES[RECORDS], "provisional_manifest_sha256": SOURCE_HASHES[PROVISIONAL_MANIFEST],
        "taxonomy_path_resolved_from_provisional_provenance": taxonomy_path.as_posix(), "taxonomy_sha256": taxonomy_sha,
        "independent_evidence_scope": "preserved generated source, public task specification, existing evaluator/EvalPlus metadata",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "provisional_modified": False, "batch03_frozen": False, "batch04_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20, "affirmed": 18, "non_material": 0, "material": 2,
        "provisional_records_sha256": SOURCE_HASHES[RECORDS], "provisional_manifest_sha256": SOURCE_HASHES[PROVISIONAL_MANIFEST],
        "taxonomy_sha256": taxonomy_sha,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    }
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output = repo / OUTPUT_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output / name).write_bytes(data)
    return output


def main() -> None:
    output = write_outputs()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output}")
    print(f"findings_sha256={manifest['outputs_sha256_excluding_manifest']['per_cell_audit_findings.csv']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
