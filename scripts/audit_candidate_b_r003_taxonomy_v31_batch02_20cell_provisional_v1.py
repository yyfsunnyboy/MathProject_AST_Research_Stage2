#!/usr/bin/env python3
"""Independent static audit of Batch02 provisional adjudication v1.

Independent expectations are encoded from frozen source, public contracts, and
existing evaluator evidence before comparison with provisional records.  This
script executes no candidate, import, test, diagnostic, EvalPlus, Healer, model,
or validation workload and never rewrites the provisional revision.
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
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1_independent_audit_v1"
)
START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "INDEPENDENT_STATIC_AUDIT_COMPLETE_MATERIAL_FINDINGS"
VERDICT = "BATCH02_POST_AUDIT_REVISION_REQUIRED"
AUDITOR = "taxonomy_v31_batch02_provisional_v1_independent_static_auditor"
AUDIT_TIMESTAMP = "2026-07-22T00:00:00+08:00"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1/batch02_roster.csv"
)
PROVISIONAL_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1"
)
RECORDS = PROVISIONAL_DIR / "adjudication_records.csv"
PROVISIONAL_ROSTER = PROVISIONAL_DIR / "adjudication_roster.csv"
PROVISIONAL_SUMMARY = PROVISIONAL_DIR / "adjudication_summary.json"
PROVISIONAL_GAPS = PROVISIONAL_DIR / "unresolved_evidence_gaps.csv"
PROVISIONAL_MANIFEST = PROVISIONAL_DIR / "manifest.json"
PROVISIONAL_PROVENANCE = PROVISIONAL_DIR / "provenance.json"
PROVISIONAL_SCRIPT = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1.py"
)
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
JOURNAL = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/"
    "manual_evalplus_run_001/evalplus_results.csv"
)

SOURCE_HASHES = {
    ROSTER: "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d",
    RECORDS: "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9",
    PROVISIONAL_ROSTER: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    PROVISIONAL_SUMMARY: "603abb708bd6cdbeacfd9f3f56c261ed4cd3f8b5d4a85289bdaa70d548772c48",
    PROVISIONAL_GAPS: "8f5e9c39d94e541ba185a1c5c5337b43f6ba3e7179f2b53a5a23c1b57db1d61c",
    PROVISIONAL_MANIFEST: "888873b1ec39831511e53b9d41b6b07e71752faaf1aff23f12817e8576dc3d01",
    PROVISIONAL_PROVENANCE: "a69c7d9e1f683d7dc4520a4dbc8b416867fdffc06a7d3fe353f496c1520f7915",
    PROVISIONAL_SCRIPT: "a3b987b03d786b5738ed8e4c5c6d3ae520576a839999226d06b019fd3578a059",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    JOURNAL: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
}

FINDING_FIELDS = (
    "audit_rank", "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "task_id", "audit_status", "original_primary_layer", "recommended_primary_layer",
    "original_secondary_layer", "recommended_secondary_layer", "original_confidence",
    "recommended_confidence", "original_outcome_validity", "recommended_outcome_validity",
    "original_healer_eligibility", "recommended_healer_eligibility",
    "mechanism_audit_status", "failure_chain_audit_status", "citation_audit_status",
    "healer_audit_status", "independent_evidence", "audit_rationale", "impact",
)
MATERIAL_FIELDS = FINDING_FIELDS + (
    "original_mechanisms_json", "recommended_mechanisms_json", "original_failure_chain",
    "recommended_failure_chain", "recommended_unresolved_reason_code",
    "recommended_evidence_present", "recommended_evidence_missing",
    "recommended_minimal_future_diagnostic",
)

VALID_STRENGTH = {"CONFIRMED", "SUPPORTED", "SUSPECTED", "REJECTED"}


class AuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    with (repo / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (repo / path).read_text(encoding="utf-8").splitlines() if line]


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        _require((repo / path).is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha((repo / path).read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")


def _expect(
    primary: str, secondary: str, confidence: str, healer: str,
    required_mechanisms: dict[str, str], evidence: str, rationale: str,
) -> dict[str, Any]:
    return {
        "primary": primary, "secondary": secondary, "confidence": confidence,
        "outcome": "VALID_MODEL_OUTCOME", "healer": healer,
        "required_mechanisms": required_mechanisms,
        "evidence": evidence, "rationale": rationale,
    }


# These expectations are independent reconstructions from public contract/source,
# not projections of provisional fields.
INDEPENDENT_EXPECTATIONS = {
    "00227845900dfa7dd96b61bef5d30b83f583ff6576a9846c8b20c41fbbf5ffc0": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "public False example is satisfied; plus failing input is undisclosed", "Contiguous-vs-noncontiguous sublist semantics cannot be closed."),
    "0289530320e18702b3707c97e303a554dad0bdbb69b4aa25e0a3382ec2da0e89": _expect("L2", "L5", "HIGH", "abstain", {"output_schema_mismatch": "CONFIRMED", "task_semantics_misread_as_membership_predicate": "CONFIRMED"}, "single public entry return is boolean; contract requires integer 27", "Unique public return violation is L2, but predicate algorithm requires reconstruction, so secondary L5 and abstain."),
    "0c4c8a0096c96cacc5adea93589cc74bc53fcb5d9dad02c7a7e9a9c51d830483": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "static mask produces public 9→15; plus boundary is undisclosed", "No public evidence closes the small-input/signed boundary."),
    "0ccf0f940c52dbf90d4e25aa554e4a6cf41703658cc8dc88f380d32d585b7d45": _expect("L2", "L5", "HIGH", "abstain", {"output_schema_mismatch": "CONFIRMED", "algorithm_reconstruction_required": "CONFIRMED"}, "single public entry return is boolean; nth-value generator contract requires integer", "L2 is directly evidenced, but generation algorithm is absent; abstain."),
    "0d1b40c698eb61156fcd8273761fdde26c3a55ea65bd7874bf4c5dfa7bb15b57": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "stack logic satisfies sole public balanced expression", "First failing expression and non-bracket policy are missing."),
    "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d": _expect("UNRESOLVED", "", "LOW", "abstain", {"negative_number_boundary": "SUSPECTED", "plus_failure_not_localized": "CONFIRMED"}, "n%10 satisfies public positive 123→3; public input domain does not explicitly include negatives", "Negative-domain L5 is plausible but not established without the failing plus input or an explicit signed-domain contract."),
    "1538fce8f0da403922caeaebb8afd96d129f6faf80378266f3b689bcdfd7231c": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "stack logic satisfies sole public balanced expression", "First failing expression and non-bracket policy are missing."),
    "15e92b97d59405977ea60125b6561bc1d30dd262ffe10eef4db8220e844f0345": _expect("L5", "", "HIGH", "abstain", {"wrong_boundary_condition": "CONFIRMED", "duplicate_value_semantics": "CONFIRMED"}, "task explicitly requires right insertion; strict < implements left insertion at equality", "Semantic binary-search repair changes algorithm behavior and must abstain."),
    "190a6f4d6f37fc027ca4c750047f26410391c75504d986687ffa4e4fdf237f7e": _expect("L5", "", "MEDIUM", "abstain", {"incorrect_recurrence": "CONFIRMED", "algorithm_reconstruction_required": "CONFIRMED"}, "prefix-sum recurrence yields 4 for n=3 whereas Bell(3)=5", "Public Bell-number semantics statically falsify the recurrence beyond the nondiscriminating n=2 example."),
    "1ad9aa1f3690e77628cb0d4db2bb1e46e3dd763ff73a464291e3f095b9f6a3cf": _expect("L5", "", "HIGH", "abstain", {"incorrect_ordering_semantics": "CONFIRMED", "return_shape_mismatch": "REJECTED"}, "source gives [10,15,20,30], public assert requires [10,20,30,15]", "List shape is correct; ordering semantics are wrong."),
    "1c39a49b4005394ebfe1338e37cfef9e9db2b71dbd3a6114c1b0fda88ef8f4c8": _expect("L5", "", "MEDIUM", "abstain", {"incorrect_formula": "CONFIRMED", "algorithm_reconstruction_required": "SUPPORTED"}, "maximum triangle uses diameter 2r and height r, area r²; source returns r²/2", "Positive-radius formula is semantically wrong despite nondiscriminating negative public assert."),
    "2007ec98d098057747bdf3975c81264c967ff76547d3bac23e622cdfe8571bf6": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "static mask produces public 9→15", "First failing plus boundary is missing."),
    "252857c7146e4e03a3ab17d02333bc99e89b8b38f5ed12e1c1a6f8ad88707eae": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "float/fraction-length logic accepts public 123.11", "Exactly-two vs up-to-two precision and failing syntax class are not public."),
    "26a25fbe4008e736db5684337d5d6b744a199a2cc7319535c3ea4dd83c546065": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "division/reversal gives public 8→1000", "Signed/non-integer domain and first failing plus behavior are missing."),
    "284533f93cc2a9c9012d005c206eb17d6cc6285ea8b17d997e50cb62fcabeafd": _expect("L4", "L5", "HIGH", "abstain", {"mixed_type_comparison_exception": "CONFIRMED", "state_invariant_broken": "CONFIRMED"}, "public list changes current_min from str to int without changing is_numeric, then evaluates str<int", "The deterministic TypeError occurs before semantic correctness, so L4 primary; inconsistent heterogeneous ordering remains secondary L5."),
    "2c3e0315fdaee4106bde69e7cbb8fdf7a0827cfabb24165dcf6197428338d83b": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "prefixing remainders gives public 8→1000", "Signed/input domain and first failing plus behavior are missing."),
    "2ce918fcbdb6d00efd2ed40243b601a3efbc5a849c1391961daf9b03717c7fba": _expect("UNRESOLVED", "", "LOW", "abstain", {"public_examples_non_discriminating": "CONFIRMED", "plus_failure_not_localized": "CONFIRMED"}, "sum of even squares gives public n=2→20", "Non-positive boundary and first failing plus behavior are missing."),
    "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a": _expect("UNRESOLVED", "", "LOW", "abstain", {"negative_number_boundary": "SUSPECTED", "plus_failure_not_localized": "CONFIRMED"}, "n%10 satisfies public positive 123→3; signed domain is not explicit", "The exact plus failure is required before promoting a hypothetical negative boundary to L5."),
    "31213b4e7d52c7e2991c5a31ed8d7d24e07a16b756a5bb326348e488aba8d5e9": _expect("L5", "", "HIGH", "abstain", {"wrong_aggregation_operator": "CONFIRMED", "incorrect_pair_domain": "SUPPORTED"}, "source XOR-accumulates pair XORs; public contract requires their sum 47", "Core aggregation semantics are wrong and require reconstruction."),
    "3162f7ce0a2214cadadba6f4903b5961215cda0f2d6eb3ea126a92f69e605640": _expect("L2", "L5", "HIGH", "abstain", {"output_schema_mismatch": "CONFIRMED", "incorrect_formula": "CONFIRMED"}, "returns True; computed (5n²-3n)/2 gives 18 at n=3 while public contract requires 27", "L2 must remain primary, L5 secondary, and abstain because return-val alone preserves a wrong formula."),
}


MATERIAL_RECOMMENDATIONS = {
    pid: {
        "primary": "UNRESOLVED", "secondary": "", "confidence": "LOW",
        "outcome": "VALID_MODEL_OUTCOME", "healer": "abstain",
        "mechanisms": [
            {"tag": "negative_number_boundary", "strength": "SUSPECTED", "note": "plausible signed-input boundary, not publicly closed"},
            {"tag": "public_examples_non_discriminating", "strength": "CONFIRMED", "note": "positive public example is satisfied"},
            {"tag": "plus_failure_not_localized", "strength": "CONFIRMED", "note": "existing plus failure input is undisclosed"},
            {"tag": "diagnostic_execution_required", "strength": "SUPPORTED", "note": "first failing plus input/domain is needed to close L5"},
            {"tag": "return_shape_mismatch", "strength": "REJECTED", "note": "integer scalar shape is correct"},
        ],
        "chain": "entry point present → n%10 satisfies public positive example → signed domain and plus failure are not disclosed → primary=UNRESOLVED → healer=abstain",
        "reason": "input_domain_not_publicly_closed_plus_failure_not_localized",
        "present": "source returns n%10; public positive assert; existing base pass / plus fail",
        "missing": "first failing plus input and explicit evidence that negative numbers are in the required domain",
        "future": "capture the first existing failing plus-case input and return without applying a repair",
    }
    for pid in (
        "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d",
        "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a",
    )
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    provisional = _read_csv(repo, RECORDS)
    prep = {row["program_id"]: row for row in _read_csv(repo, PREPARATION)}
    journals = {row["program_id"]: row for row in _read_jsonl(repo, JOURNAL) if row["healer_account"] == "H0"}
    tasks = {row["task_id"]: row for row in _read_jsonl(repo, TASKS)}
    evalplus = {row["program_id"]: row for row in _read_csv(repo, EVALPLUS) if row["healer_account"] == "H0"}

    _require(len(roster) == len(provisional) == 20, "20-cell closure drift")
    _require(set(INDEPENDENT_EXPECTATIONS) == {row["program_id"] for row in roster}, "independent expectation closure drift")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in provisional], "roster/records order drift")
    _require(len({row["cell_identity_sha256"] for row in roster}) == 20, "cell identity uniqueness drift")

    findings: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    recommended_layers = Counter()
    recommended_confidence = Counter()
    recommended_healer = Counter()

    for audit_rank, (rr, record) in enumerate(zip(roster, provisional), 1):
        pid = rr["program_id"]
        expected = INDEPENDENT_EXPECTATIONS[pid]
        _require(rr["cell_identity_sha256"] == record["cell_identity_sha256"] == prep[pid]["cell_identity_sha256"], f"identity drift: {pid}")
        _require(rr["source_sha256"] == record["source_sha256"] == journals[pid]["evaluation_source_sha256"], f"source drift: {pid}")
        _require(rr["task_id"] == record["task_id"] == journals[pid]["task_id"], f"task drift: {pid}")
        _require(tasks[rr["task_id"]]["entry_point"] in journals[pid]["evaluation_source"], f"entry source drift: {pid}")
        _require(evalplus[pid]["base_status"] in {"pass", "fail"} and evalplus[pid]["plus_status"] in {"pass", "fail"}, f"evaluator evidence drift: {pid}")

        mechanisms = json.loads(record["mechanism_tags_json"])
        mechanism_map = {item["tag"]: item.get("strength") or item.get("status") for item in mechanisms}
        _require(all(value in VALID_STRENGTH for value in mechanism_map.values()), f"invalid mechanism strength: {pid}")
        mechanism_ok = all(mechanism_map.get(tag) == strength for tag, strength in expected["required_mechanisms"].items())
        citation_ok = all(fragment in record["evidence_citations"] for fragment in (pid, rr["task_id"], rr["cell_identity_sha256"]))
        chain_ok = bool(record["failure_chain"] and record["public_evidence"] and record["source_structure_locator"])
        healer_ok = record["healer_eligibility"] == expected["healer"]
        dimensions_ok = all(
            (
                record["primary_layer"] == expected["primary"],
                record["secondary_layer"] == expected["secondary"],
                record["confidence"] == expected["confidence"],
                record["outcome_validity"] == expected["outcome"],
                healer_ok,
            )
        )
        is_material = pid in MATERIAL_RECOMMENDATIONS
        _require(is_material or (dimensions_ok and mechanism_ok and citation_ok and chain_ok), f"unexpected non-material mismatch: {pid}")

        recommendation = MATERIAL_RECOMMENDATIONS.get(pid)
        recommended_primary = recommendation["primary"] if recommendation else expected["primary"]
        recommended_secondary = recommendation["secondary"] if recommendation else expected["secondary"]
        recommended_conf = recommendation["confidence"] if recommendation else expected["confidence"]
        recommended_outcome = recommendation["outcome"] if recommendation else expected["outcome"]
        recommended_h = recommendation["healer"] if recommendation else expected["healer"]
        recommended_layers[recommended_primary] += 1
        recommended_confidence[recommended_conf] += 1
        recommended_healer[recommended_h] += 1

        status = "MATERIAL" if is_material else "AFFIRMED"
        impact = (
            "Primary distribution changes L5→UNRESOLVED; confidence MEDIUM→LOW; unresolved gaps increase by one; Healer remains abstain."
            if is_material else "No provisional field change required."
        )
        finding = {
            "audit_rank": str(audit_rank), "batch_rank": rr["batch_rank"],
            "program_id": pid, "cell_identity_sha256": rr["cell_identity_sha256"],
            "source_sha256": rr["source_sha256"], "task_id": rr["task_id"],
            "audit_status": status,
            "original_primary_layer": record["primary_layer"], "recommended_primary_layer": recommended_primary,
            "original_secondary_layer": record["secondary_layer"], "recommended_secondary_layer": recommended_secondary,
            "original_confidence": record["confidence"], "recommended_confidence": recommended_conf,
            "original_outcome_validity": record["outcome_validity"], "recommended_outcome_validity": recommended_outcome,
            "original_healer_eligibility": record["healer_eligibility"], "recommended_healer_eligibility": recommended_h,
            "mechanism_audit_status": "REVISION_REQUIRED" if is_material else "AFFIRMED",
            "failure_chain_audit_status": "REVISION_REQUIRED" if is_material else "AFFIRMED",
            "citation_audit_status": "AFFIRMED" if citation_ok else "MATERIAL_MISSING",
            "healer_audit_status": "AFFIRMED" if healer_ok else "REVISION_REQUIRED",
            "independent_evidence": expected["evidence"], "audit_rationale": expected["rationale"],
            "impact": impact,
        }
        findings.append(finding)
        if is_material:
            material.append(
                {
                    **finding,
                    "original_mechanisms_json": record["mechanism_tags_json"],
                    "recommended_mechanisms_json": _json(recommendation["mechanisms"]),
                    "original_failure_chain": record["failure_chain"],
                    "recommended_failure_chain": recommendation["chain"],
                    "recommended_unresolved_reason_code": recommendation["reason"],
                    "recommended_evidence_present": recommendation["present"],
                    "recommended_evidence_missing": recommendation["missing"],
                    "recommended_minimal_future_diagnostic": recommendation["future"],
                }
            )

    status_counts = Counter(row["audit_status"] for row in findings)
    _require(status_counts == Counter({"AFFIRMED": 18, "MATERIAL": 2}), f"audit status drift: {status_counts}")
    _require(recommended_layers == Counter({"UNRESOLVED": 11, "L5": 5, "L2": 3, "L4": 1}), f"recommended layer drift: {recommended_layers}")
    _require(recommended_confidence == Counter({"LOW": 11, "HIGH": 7, "MEDIUM": 2}), f"recommended confidence drift: {recommended_confidence}")
    _require(recommended_healer == Counter({"abstain": 20}), f"recommended healer drift: {recommended_healer}")

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 20, "unique_program_id": 20, "unique_cell_identity": 20,
        "audit_status_distribution": dict(sorted(status_counts.items())),
        "material_findings": len(material),
        "original_primary_distribution": dict(sorted(Counter(row["primary_layer"] for row in provisional).items())),
        "recommended_primary_distribution": dict(sorted(recommended_layers.items())),
        "recommended_confidence_distribution": dict(sorted(recommended_confidence.items())),
        "recommended_healer_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "l2_cells_reviewed": 3, "l2_cells_affirmed": 3,
        "l4_cells_reviewed": 1, "l4_cells_affirmed": 1,
        "decagonal_cells_reviewed": 3, "decagonal_l2_secondary_l5_abstain_affirmed": 3,
        "original_unresolved_reviewed": 9, "original_unresolved_affirmed": 9,
        "additional_unresolved_recommended": 2,
        "zero_eligible_and_conditional_audit_conclusion": "CORRECT_NOT_OVERLY_CONSERVATIVE",
        "ready_to_freeze": False,
    }
    return {"findings": findings, "material": material, "summary": summary}


def _report(summary: dict[str, Any], material: list[dict[str, str]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3.1：Batch02 provisional v1 independent audit",
        "", f"**狀態：`{STATUS}`**", "", f"**Verdict：`{VERDICT}`**", "",
        "## Audit 結果", "",
        f"- AFFIRMED：{summary['audit_status_distribution']['AFFIRMED']}",
        f"- MATERIAL：{summary['audit_status_distribution']['MATERIAL']}",
        f"- provisional primary：{summary['original_primary_distribution']}",
        f"- 建議 primary：{summary['recommended_primary_distribution']}", "",
        "## Material findings", "",
    ]
    for row in material:
        lines.extend(
            [
                f"### `{row['program_id']}` / `{row['task_id']}`",
                "",
                f"- 原裁決：{row['original_primary_layer']} / {row['original_confidence']}",
                f"- 建議：{row['recommended_primary_layer']} / {row['recommended_confidence']}",
                f"- 證據：{row['independent_evidence']}",
                f"- 理由：{row['audit_rationale']}",
                f"- 影響：{row['impact']}", "",
            ]
        )
    lines.extend(
        [
            "## 重點核查", "",
            "- 三格 L2 全部 affirmed；各有公開整數 contract、單一 public entry return 違約與 source 證據。",
            "- L4 mixed-type cell affirmed；TypeError 先於語意結果，secondary L5 合理。",
            "- 三格 decagonal 均維持 L2 + secondary L5 + abstain。",
            "- 原九格 UNRESOLVED 全部 affirmed；另兩格 last_Digit 應改列 UNRESOLVED。",
            "- eligible=0、conditional=0 並非過度保守；Healer funnel affirmed。", "",
            "本 audit 不得 freeze provisional v1；須先產生修訂版並重新 audit。", "",
        ]
    )
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
        "per_cell_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "audit_report_zh.md": _report(analysis["summary"], analysis["material"]).encode("utf-8"),
        "execution_counts.json": _json_bytes(execution),
    }
    provenance = {
        **analysis["summary"], **execution,
        "start_head": START_HEAD, "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "provisional_records_sha256": SOURCE_HASHES[RECORDS],
        "independent_reconstruction_precedes_comparison": True,
        "provisional_modified": False, "upstream_modified": False,
        "new_runtime_observations": 0,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "provisional_records_sha256": SOURCE_HASHES[RECORDS],
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
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
