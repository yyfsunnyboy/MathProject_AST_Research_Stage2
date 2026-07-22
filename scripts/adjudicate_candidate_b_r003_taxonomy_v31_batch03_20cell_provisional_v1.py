#!/usr/bin/env python3
"""Static provisional adjudication for the fixed Batch03 20-cell roster.

Only preserved source text, public task specifications, and existing evaluator
metadata are read.  Candidate code is never imported or executed, and no new
diagnostic observation is produced.
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
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1")
START_HEAD = "923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS = "AI_ASSISTED_STATIC_PROVISIONAL_ADJUDICATION_NOT_AUDITED"
VERDICT = "READY_FOR_BATCH03_PROVISIONAL_AUDIT"
ADJUDICATOR = "taxonomy_v31_batch03_provisional_v1_static_adjudicator"
TIMESTAMP = "2026-07-22T00:00:00+08:00"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/batch03_roster.csv")
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
AUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1_independent_audit_v1")
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_roster_findings.csv"
ACCOUNTS = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv")
REMAINING101 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv")
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",
    ROSTER_MANIFEST: "42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c",
    AUDIT_MANIFEST: "ba20a3ab6e3200f2c9c2effbabd27537f6f4b1415637fec5846c80ec90425a4a",
    AUDIT_FINDINGS: "675d7f5a7ae0b931903577124249168574d3aec3d29946178d57c675ba4d212a",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

RECORD_FIELDS = (
    "batch_rank", "cell_identity_sha256", "program_id", "source_sha256", "task_id",
    "seed", "generation_id", "condition", "review_status", "classification_status",
    "primary_layer", "secondary_layer", "mechanism_tags_json", "failure_chain",
    "confidence", "outcome_validity", "healer_eligibility", "eligibility_reason",
    "eligibility_rule", "rejection_condition", "unresolved_reason_code",
    "evidence_present", "evidence_missing", "competing_explanations", "reason",
    "minimal_future_diagnostic", "public_evidence", "evidence_citations",
    "source_structure_locator", "adjudicator_identity", "adjudication_timestamp",
    "planning_signal_note",
)
EVIDENCE_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "task_id", "source_sha256",
    "public_specification", "static_source_observation", "existing_base_status",
    "existing_plus_status", "evidence_present", "evidence_missing",
    "competing_explanations", "minimal_future_diagnostic", "citations",
)
MECHANISM_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "primary_layer", "mechanism_tag", "strength", "note")
CONDITIONAL_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "candidate_rule", "minimal_diagnostic", "upgrade_condition", "rejection_condition")
GAP_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "unresolved_reason_code", "evidence_present", "evidence_missing", "competing_explanations", "minimal_future_diagnostic")


class AdjudicationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    actual = path if path.is_absolute() else repo / path
    with actual.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, path: Path) -> list[dict[str, Any]]:
    actual = path if path.is_absolute() else repo / path
    return [json.loads(line) for line in actual.read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        actual = path if path.is_absolute() else repo / path
        _require(actual.is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha(actual.read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")


def _decision(
    primary: str, observation: str, evidence: str, reason: str,
    mechanisms: list[tuple[str, str, str]], *, secondary: str = "",
    confidence: str = "HIGH", missing: str = "no evidence gap required for provisional layer closure",
    competing: str = "additional hidden-case defects may coexist but do not displace the public static violation",
    unresolved_code: str = "", diagnostic: str = "",
) -> dict[str, Any]:
    return {
        "primary": primary, "secondary": secondary, "confidence": confidence,
        "observation": observation, "evidence": evidence, "missing": missing,
        "competing": competing, "reason": reason, "mechanisms": mechanisms,
        "unresolved_code": unresolved_code, "diagnostic": diagnostic,
    }


def _unresolved(observation: str, evidence: str, missing: str, competing: str, diagnostic: str, extra: list[tuple[str, str, str]] | None = None) -> dict[str, Any]:
    mechanisms = [
        ("public_examples_non_discriminating", "CONFIRMED", "preserved public example is satisfied by static derivation"),
        ("plus_failure_not_localized", "CONFIRMED", "existing plus status is fail but its first failing input is not preserved here"),
        ("diagnostic_execution_required", "SUPPORTED", "a new observation would be required to distinguish remaining explanations"),
    ]
    if extra:
        mechanisms.extend(extra)
    return _decision(
        "UNRESOLVED", observation, evidence,
        "review completed but current static evidence does not close one L0-L5 root layer",
        mechanisms, confidence="LOW", missing=missing, competing=competing,
        unresolved_code="public_example_satisfied_plus_failure_not_localized",
        diagnostic=diagnostic,
    )


DECISIONS = {
    "32d57f4a3d936a6e9c655af0f10d9b2a06578a1adedc54df98892a4d6b795bd3": _unresolved(
        "loop sums (2i)^2 for i=1..n and statically yields 20 at n=2",
        "required entry point and scalar return are present; public n=2 example is satisfied; base=pass/plus=fail",
        "first failing plus input and the applicable non-positive/large-n boundary",
        "an undisclosed boundary, resource case, or evaluator-domain convention remains possible",
        "capture the first existing failing plus input and return/exception without applying a repair",
    ),
    "32edbe1532826de4a3416eb06e43c97bc8b4687cce8161729414d2811d583c85": _decision(
        "L5", "list1-order filtering yields [10,15,20,30], not public [10,20,30,15]",
        "public assertion directly distinguishes the required difference ordering",
        "output shape is correct but ordering semantics contradict the public contract",
        [("incorrect_ordering_semantics", "CONFIRMED", "candidate preserves list1 order while public result uses different order"), ("algorithm_reconstruction_required", "SUPPORTED", "repair requires choosing the intended ordering algorithm")],
    ),
    "392899632bcf304144c5f48b7ac2120b6a200c6ce845b067a875cb427149c55a": _decision(
        "L5", "function checks numeric parse and decimal-point presence but never enforces precision two",
        "task explicitly requires decimal precision of 2; source accepts arbitrary valid fractional lengths",
        "precision-validation semantics are absent despite a correct boolean interface",
        [("precision_validation_error", "CONFIRMED", "fractional digit count is not constrained"), ("edge_case_omission", "CONFIRMED", "more-than-two-digit fractional forms remain accepted")],
    ),
    "3b802dcce09d236485df19d1c985675e091e74cbb5fcbf6e73f753d873f62e88": _decision(
        "L5", "Counter filter excludes every repeated 1 and statically sums 2+3+4+5+6=20, not public 21",
        "public assertion requires each distinct value once, including repeated value 1",
        "candidate implements occurrence-count-one rather than deduplicated-value semantics",
        [("dedupe_instead_of_unique_occurrence", "CONFIRMED", "repeated values are omitted rather than counted once"), ("semantic_goal_drift", "CONFIRMED", "non-repeated was interpreted as frequency exactly one")],
    ),
    "4378e8d490f8f3ec4fca63d29b42264fbfb25d6f05a847acf0868d3b54f7c1a9": _decision(
        "L5", "rounding to two places before measuring digits makes longer valid fractions appear two-digit",
        "task requires checking original decimal precision; source validates a rounded representation",
        "round-before-validate changes the semantic predicate",
        [("precision_validation_error", "CONFIRMED", "precision is measured after rounding"), ("semantic_goal_drift", "CONFIRMED", "numeric roundability replaces lexical precision")],
    ),
    "53e1494c968d9de1060a6f2704a8ca57d68b803f0afb1ab122539dfdb36dd039": _decision(
        "L5", "binary search advances only on arr[mid] < value and therefore computes left insertion at equality",
        "public task explicitly requests the right insertion point",
        "strict comparison implements lower-bound rather than right-bound semantics",
        [("wrong_boundary_condition", "CONFIRMED", "equality is routed left"), ("duplicate_value_semantics", "CONFIRMED", "equal runs are not skipped")],
    ),
    "578c5bf9895c10e09e10e0c1194a2ddf6b87d783e19582571098150b36269dea": _decision(
        "L5", "set-backed list1 filtering yields [10,15,20,30], not public [10,20,30,15]",
        "public assertion directly distinguishes the required difference ordering",
        "membership logic is plausible but the required ordering is not implemented",
        [("incorrect_ordering_semantics", "CONFIRMED", "candidate preserves list1 order contrary to public output"), ("algorithm_reconstruction_required", "SUPPORTED", "repair requires selecting intended ordering semantics")],
    ),
    "5b58236a8dd74781896f67d4a87859b04f6c7abba8fda28db27f116dbd4ccf8e": _decision(
        "L5", "for public n=5 the bounded loop tests i=1,2 only and returns False",
        "public assertion requires dif_Square(5) == True; source can be evaluated symbolically for those two iterations",
        "search bound and difference construction omit a valid 5=3^2-2^2 representation",
        [("algorithmic_error", "CONFIRMED", "search does not cover the required square pair"), ("incorrect_search_bound", "CONFIRMED", "outer square 3 is excluded for n=5")],
    ),
    "5ed7bb37b7f3170d75713428f8354054a4844c9100019b561eb00fc00144aba2": _unresolved(
        "loop sums (2i)^2 for i=1..n and embedded public n=2 assertion is satisfied",
        "entry point/scalar shape present; public example and base tests pass; plus fails",
        "first failing plus input and applicable boundary/resource condition",
        "an undisclosed boundary, resource case, or evaluator-domain convention remains possible",
        "capture the first existing failing plus input and return/exception without applying a repair",
    ),
    "6107650d8a56ae0107d45b67e7571175e6698d84bc9f0ede8dff58f8f4929424": _unresolved(
        "standard stack/matching implementation statically accepts the sole public balanced expression",
        "all three bracket families are paired; public example and base tests pass; plus fails",
        "first failing plus expression and policy for non-bracket characters",
        "failure may concern non-bracket policy, an undisclosed expression boundary, or evaluator convention",
        "capture the first existing failing plus expression and return without applying a repair",
    ),
    "65b945dcb63cfad531df7d56b1817fde397b27f6dff98c6581a337b4c41d31c3": _decision(
        "L5", "uppercase is recognized only at index 0 or after a non-letter, so internal capitals never receive a space",
        "task requires spaces between words beginning with capital letters; source misses camel-case word boundaries",
        "capital-boundary predicate contradicts the stated word-splitting goal",
        [("capital_boundary_detection_error", "CONFIRMED", "internal uppercase after a letter is ignored"), ("edge_case_omission", "CONFIRMED", "multiword camel-case strings are not split")],
    ),
    "6d29dd4ee79a526d569748360106a53eb4e80487bd7e69eefe2cb8e0e714aed7": _decision(
        "L5", "on first nums[left] >= target the function returns left+1 regardless of equality",
        "right insertion requires index 0 for a target below the first element and after the full equal run for equality",
        "linear boundary logic is wrong for both below-minimum and duplicate cases",
        [("wrong_boundary_condition", "CONFIRMED", "greater-than case incorrectly adds one"), ("duplicate_value_semantics", "CONFIRMED", "only the first equal element is skipped")],
    ),
    "6d322d7901db24de0d45c8ba71525e66d011932474ab8aeae274058d5f8def35": _unresolved(
        "contiguous-window comparison returns False for the sole public example",
        "parseable required entry point; public example and base tests pass; plus fails",
        "whether sublist means contiguous slice or ordered/noncontiguous containment, and the first failing plus case",
        "contiguous and noncontiguous interpretations remain compatible with the public False example",
        "capture the first existing failing plus lists and return without applying a repair",
        [("sublist_semantics_ambiguous", "SUSPECTED", "public contract does not discriminate contiguous from noncontiguous semantics")],
    ),
    "71012956073b53a6d9d9341681ec221238d2d1fe8cdd2dfc5a82291b2fb7d44f": _decision(
        "L5", "Counter filter excludes every repeated 1 and statically sums 20 instead of public 21",
        "public assertion establishes that repeated value 1 contributes once",
        "frequency-exactly-one semantics contradict the public result",
        [("dedupe_instead_of_unique_occurrence", "CONFIRMED", "repeated values are omitted instead of deduplicated"), ("semantic_goal_drift", "CONFIRMED", "non-repeated was interpreted as occurrence count one")],
    ),
    "77223f4bbae7279a826f083779d37952881c8d4d61f1bb229600fefffcf4c5fd": _unresolved(
        "source returns (a+b)/2 for the public tuple but adds an undocumented abs(a-b)<=c guard",
        "public example is satisfied and base tests pass; plus fails; prompt does not define the third argument's domain role",
        "first failing plus tuple and public contract for the third parameter/valid trapezium domain",
        "the guard may be an invalid semantic restriction or may encode an unstated validity domain",
        "capture the first existing failing plus tuple and expected return class without applying a repair",
        [("unsupported_input_guard", "SUSPECTED", "guard is not justified by the preserved public text")],
    ),
    "7a42d5510092e63637c51173576a5bbdd091d9fb18fbc36627f0cd73a6dc86a9": _decision(
        "L5", "binary search uses arr[mid] < value and returns the leftmost equal position",
        "task explicitly requests right insertion; the public greater-than-all case is nondiscriminating",
        "equality routing implements lower bound rather than right bound",
        [("wrong_boundary_condition", "CONFIRMED", "equality is routed to the left half"), ("duplicate_value_semantics", "CONFIRMED", "equal values are not passed")],
    ),
    "7c7bf358de0139c9688826eac3ca6414efd233291d4226cc2f656c58f9c3a8a3": _unresolved(
        "general XOR mask preserves MSB/LSB and toggles middle bits for positive n, while n=9 is redundantly hardcoded",
        "public 9->15 example and base tests pass; plus fails; required entry point and scalar shape are present",
        "first failing plus integer and signed/zero bit-width convention",
        "failure may concern signed inputs, small values, or another unstated bit representation rule",
        "capture the first existing failing plus integer and return without applying a repair",
        [("code_bloat", "CONFIRMED", "source contains extensive redundant derivation"), ("hardcoded_public_example", "CONFIRMED", "n==9 is special-cased despite a general branch")],
    ),
    "7e865e15f3bf0cfe4619ac724f009fa7a0d5134e1660e32f1a74469073da8824": _decision(
        "L2", "required is_polite returns a boolean predicate while the public contract requires integer 11 for input 7",
        "public assertion establishes required callable name and integer nth-value output",
        "required entry point is present but implements the wrong return contract; nth_polite cannot be safely aliased because it dynamically calls is_polite as its helper",
        [("output_schema_mismatch", "CONFIRMED", "boolean scalar replaces required integer nth value"), ("semantic_goal_drift", "CONFIRMED", "property predicate replaces nth-value computation"), ("algorithm_reconstruction_required", "SUPPORTED", "making the helper/generator binding safe requires semantic restructuring")],
        secondary="L5",
    ),
    "80e9e1cc3a249dd8da36d260f934304728b7eb6a6438bdb0f851e45f47ab74bb": _decision(
        "L5", "candidate treats k as an XOR threshold; public pair XORs sum to 47 but threshold filtering retains only a subset",
        "public assertion directly specifies pair_xor_Sum([5,9,7,6],4)==47",
        "the second parameter and pair aggregation domain are semantically misinterpreted",
        [("wrong_parameter_semantics", "CONFIRMED", "k is used as a value threshold instead of the pair-domain size"), ("incorrect_pair_domain", "CONFIRMED", "pairs with XOR greater than k are incorrectly excluded"), ("algorithmic_error", "CONFIRMED", "aggregation does not cover all required pairs")],
    ),
    "83b0f95093eb347659aaf335ea129890f0d3be93e35b8a532e0d7968f916e795": _unresolved(
        "contiguous-window comparison returns False for the sole public example",
        "parseable required entry point; public example and base tests pass; plus fails",
        "whether sublist means contiguous slice or ordered/noncontiguous containment, and the first failing plus case",
        "contiguous and noncontiguous interpretations remain compatible with the public False example",
        "capture the first existing failing plus lists and return without applying a repair",
        [("sublist_semantics_ambiguous", "SUSPECTED", "public text does not discriminate sublist semantics")],
    ),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    audit_manifest = json.loads((repo / AUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(audit_manifest["verdict"] == "READY_FOR_BATCH03_PROVISIONAL_ADJUDICATION", "roster audit verdict drift")
    _require(len(roster) == 20 and set(DECISIONS) == {r["program_id"] for r in roster}, "decision/roster closure drift")
    accounts = {r["program_id"]: r for r in _read_jsonl(repo, ACCOUNTS) if r["healer_account"] == "H0"}
    tasks = {r["task_id"]: r for r in _read_jsonl(repo, TASKS)}
    evals = {r["program_id"]: r for r in _read_csv(repo, EVALPLUS) if r["healer_account"] == "H0"}
    prep = {r["program_id"]: r for r in _read_csv(repo, PREPARATION)}

    records: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []
    mechanisms: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    for roster_row in roster:
        pid = roster_row["program_id"]
        account, task, ev, formal = accounts[pid], tasks[roster_row["task_id"]], evals[pid], prep[pid]
        _require(account["evaluation_source_sha256"] == roster_row["source_sha256"], f"account source drift: {pid}")
        _require(formal["cell_identity_sha256"] == roster_row["cell_identity_sha256"], f"formal identity drift: {pid}")
        _require(formal["evaluation_source_sha256"] == roster_row["source_sha256"], f"formal source drift: {pid}")
        d = DECISIONS[pid]
        tags = [{"tag": tag, "strength": strength, "note": note} for tag, strength, note in d["mechanisms"]]
        citations = ";".join([
            f"{ROSTER.as_posix()}#program_id={pid}",
            f"{ACCOUNTS.as_posix()}#program_id={pid};healer_account=H0",
            f"{TASKS.as_posix()}#task_id={roster_row['task_id']}",
            f"{EVALPLUS.as_posix()}#program_id={pid};healer_account=H0",
            f"{PREPARATION.as_posix()}#cell_identity_sha256={roster_row['cell_identity_sha256']}",
            f"{TAXONOMY.as_posix()}#sections=4,5,8,9,10,11,12",
        ])
        if d["primary"] == "UNRESOLVED":
            chain = "parseable required entry point → public example satisfied statically → existing base pass/plus fail not localized → primary=UNRESOLVED → healer=abstain"
        elif d["primary"] == "L2":
            chain = "parseable required entry point → public return contract violated → primary=L2; secondary=L5 → nonlocal semantic repair required → healer=abstain"
        else:
            chain = "parseable required entry point and output shape → public contract statically contradicted → primary=L5 → algorithm/semantics repair required → healer=abstain"
        healer_reason = "Root layer and unique safe repair are not closed." if d["primary"] == "UNRESOLVED" else "Repair changes task semantics or algorithm and is not a unique local oracle-independent transformation."
        record = {
            "batch_rank": roster_row["selection_rank"], "cell_identity_sha256": roster_row["cell_identity_sha256"],
            "program_id": pid, "source_sha256": roster_row["source_sha256"], "task_id": roster_row["task_id"],
            "seed": roster_row["seed"], "generation_id": roster_row["generation_id"], "condition": roster_row["condition"],
            "review_status": "PROVISIONALLY_ADJUDICATED", "classification_status": "ADJUDICATED",
            "primary_layer": d["primary"], "secondary_layer": d["secondary"],
            "mechanism_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "failure_chain": chain, "confidence": d["confidence"], "outcome_validity": "VALID_MODEL_OUTCOME",
            "healer_eligibility": "abstain", "eligibility_reason": healer_reason,
            "eligibility_rule": "", "rejection_condition": "semantic_or_evidence_closure_not_safe_for_deterministic_healer",
            "unresolved_reason_code": d["unresolved_code"], "evidence_present": d["evidence"],
            "evidence_missing": d["missing"], "competing_explanations": d["competing"], "reason": d["reason"],
            "minimal_future_diagnostic": d["diagnostic"], "public_evidence": task["prompt"].strip().replace("\n", " "),
            "evidence_citations": citations, "source_structure_locator": d["observation"],
            "adjudicator_identity": ADJUDICATOR, "adjudication_timestamp": TIMESTAMP,
            "planning_signal_note": "roster order fixed before adjudication; no planning signal promoted to layer or Healer disposition",
        }
        records.append(record)
        evidence_rows.append({
            "batch_rank": record["batch_rank"], "program_id": pid, "cell_identity_sha256": record["cell_identity_sha256"],
            "task_id": record["task_id"], "source_sha256": record["source_sha256"],
            "public_specification": record["public_evidence"], "static_source_observation": d["observation"],
            "existing_base_status": ev["base_status"], "existing_plus_status": ev["plus_status"],
            "evidence_present": d["evidence"], "evidence_missing": d["missing"],
            "competing_explanations": d["competing"], "minimal_future_diagnostic": d["diagnostic"], "citations": citations,
        })
        for tag, strength, note in d["mechanisms"]:
            mechanisms.append({"batch_rank": record["batch_rank"], "program_id": pid, "cell_identity_sha256": record["cell_identity_sha256"], "primary_layer": d["primary"], "mechanism_tag": tag, "strength": strength, "note": note})
        if d["primary"] == "UNRESOLVED":
            gaps.append({field: record[field] for field in GAP_FIELDS})

    _require([r["program_id"] for r in records] == [r["program_id"] for r in roster], "record order drift")
    _require(len({r["program_id"] for r in records}) == len({r["cell_identity_sha256"] for r in records}) == 20, "identity uniqueness drift")
    _require(all(r["primary_layer"] in {"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"} for r in records), "primary schema drift")
    _require(all(r["healer_eligibility"] in {"eligible", "conditional", "abstain"} for r in records), "healer schema drift")
    _require(all(r["eligibility_reason"] for r in records), "abstain reason missing")
    _require(all(r["unresolved_reason_code"] and r["evidence_missing"] and r["minimal_future_diagnostic"] for r in records if r["primary_layer"] == "UNRESOLVED"), "unresolved gap incomplete")

    primary = Counter(r["primary_layer"] for r in records)
    secondary = Counter(r["secondary_layer"] or "empty" for r in records)
    confidence = Counter(r["confidence"] for r in records)
    outcome = Counter(r["outcome_validity"] for r in records)
    healer = Counter(r["healer_eligibility"] for r in records)
    mechanism_counts = Counter(r["mechanism_tag"] for r in mechanisms)
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT, "cells": 20,
        "unique_program_id": 20, "unique_cell_identity": 20,
        "unique_source_sha256": len({r["source_sha256"] for r in records}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {"eligible": healer.get("eligible", 0), "conditional": healer.get("conditional", 0), "abstain": healer.get("abstain", 0)},
        "mechanism_tag_distribution": dict(sorted(mechanism_counts.items())),
        "unresolved_cells": len(gaps), "conditional_queue_cells": 0,
        "eligible_cells": 0, "abstain_cells": healer["abstain"],
        "new_runtime_observations": 0, "upstream_modified": False,
    }
    _require(primary == Counter({"L5": 12, "UNRESOLVED": 7, "L2": 1}), f"primary distribution drift: {primary}")
    _require(secondary == Counter({"empty": 19, "L5": 1}), f"secondary distribution drift: {secondary}")
    _require(confidence == Counter({"HIGH": 13, "LOW": 7}), f"confidence distribution drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome distribution drift: {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer distribution drift: {healer}")
    return {"records": records, "evidence": evidence_rows, "mechanisms": mechanisms, "conditional": [], "gaps": gaps, "summary": summary}


def _report(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# Candidate B r003 taxonomy v3.1：Batch03 provisional adjudication v1", "",
        f"**狀態：`{STATUS}`**", "",
        f"- Primary：{summary['primary_layer_distribution']}",
        f"- Secondary：{summary['secondary_layer_distribution']}",
        f"- Confidence：{summary['confidence_distribution']}",
        f"- Outcome：{summary['outcome_validity_distribution']}",
        f"- Healer：{summary['healer_eligibility_distribution']}",
        f"- UNRESOLVED：{summary['unresolved_cells']}", "",
        "eligible與conditional候選均為0。所有20格均abstain：L5/L2格需要語意或演算法修正；UNRESOLVED格的根因與唯一安全修法未閉合。", "",
        "本revision僅使用保存的靜態source、公開task specification及既有evaluator metadata；未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型。", "",
    ])


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "adjudication_records.csv": _csv_bytes(RECORD_FIELDS, analysis["records"]),
        "per_cell_evidence_ledger.csv": _csv_bytes(EVIDENCE_FIELDS, analysis["evidence"]),
        "mechanism_ledger.csv": _csv_bytes(MECHANISM_FIELDS, analysis["mechanisms"]),
        "conditional_diagnostic_queue.csv": _csv_bytes(CONDITIONAL_FIELDS, analysis["conditional"]),
        "unresolved_evidence_gaps.csv": _csv_bytes(GAP_FIELDS, analysis["gaps"]),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER], "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST], "taxonomy_v31_sha256": SOURCE_HASHES[TAXONOMY],
        "evidence_scope": "preserved generated source text, public task specification, existing evaluator/EvalPlus metadata only",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication_audit": True, "batch03_frozen": False, "batch04_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20, "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST], "roster_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "taxonomy_v31_sha256": SOURCE_HASHES[TAXONOMY],
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
    print(f"records_sha256={manifest['outputs_sha256_excluding_manifest']['adjudication_records.csv']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
