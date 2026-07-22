#!/usr/bin/env python3
"""Static, zero-execution provisional adjudication for Final Batch05."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_provisional_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "AI_ASSISTED_STATIC_PROVISIONAL_ADJUDICATION_NOT_INDEPENDENTLY_AUDITED"
VERDICT = "READY_FOR_FINAL_BATCH05_PROVISIONAL_INDEPENDENT_AUDIT"
ADJUDICATOR = "taxonomy_v31_final_batch05_provisional_v1_static_adjudicator"
TIMESTAMP = "2026-07-22T00:00:00+08:00"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1/batch05_roster.csv")
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
REMAINING21 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/remaining21_roster.csv")
AUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1_independent_audit_v1")
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_roster_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
ACCOUNTS = Path("artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv")
PREPARATION = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ROSTER_MANIFEST: "b48500bf4be94e00ec9e836c21ff72cce7218476660b231785357b383b05731e",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    AUDIT_FINDINGS: "d834c492a4c61bc22048356de6d17c1da2c766f57d948f3df713570251761f34",
    AUDIT_MANIFEST: "bb1603b8eeaf9890a85d13291628f7985cc67bfbdc2d3221f39328295e506312",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
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
MECHANISM_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "primary_layer",
    "mechanism_tag", "strength", "note",
)
CHAIN_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "stage_count",
    "primary_layer", "outcome_validity", "failure_chain_json", "citations",
)
GAP_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "unresolved_reason_code",
    "evidence_present", "evidence_missing", "competing_explanations", "minimal_future_diagnostic",
)


class AdjudicationError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo / value


def _read_csv(repo: Path, value: Path) -> list[dict[str, str]]:
    with _path(repo, value).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, value: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in _path(repo, value).read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def _decision(
    observation: str,
    evidence: str,
    reason: str,
    mechanisms: list[tuple[str, str, str]],
) -> dict[str, Any]:
    return {
        "primary": "L5", "secondary": "", "confidence": "HIGH",
        "observation": observation, "evidence": evidence,
        "missing": "no evidence gap required for provisional layer closure",
        "competing": "other hidden-case defects may coexist but do not displace the static public-contract violation",
        "reason": reason, "mechanisms": mechanisms,
        "unresolved_code": "", "diagnostic": "",
    }


def _unresolved(
    observation: str,
    evidence: str,
    missing: str,
    competing: str,
    diagnostic: str,
    suspected: tuple[str, str] | None = None,
) -> dict[str, Any]:
    mechanisms = [
        ("public_examples_non_discriminating", "CONFIRMED", "preserved public example is statically satisfied"),
        ("plus_failure_not_localized", "CONFIRMED", "saved Plus status is fail but no failing input or assertion is preserved in allowed evidence"),
        ("diagnostic_execution_required", "SUPPORTED", "distinguishing the remaining explanations requires a new observation"),
    ]
    if suspected:
        mechanisms.append((suspected[0], "SUSPECTED", suspected[1]))
    return {
        "primary": "UNRESOLVED", "secondary": "", "confidence": "LOW",
        "observation": observation, "evidence": evidence, "missing": missing,
        "competing": competing,
        "reason": "審查已完成，但現有合法靜態證據不足以閉合至單一 L0–L5。",
        "mechanisms": mechanisms,
        "unresolved_code": "public_example_satisfied_plus_failure_not_localized",
        "diagnostic": diagnostic,
    }


DECISIONS: dict[int, dict[str, Any]] = {
    1: _unresolved(
        "implementation statically converts zero and positive integers by repeated division and satisfies 8->1000",
        "required entry point and string result are present; saved base passes and Plus fails",
        "first failing Plus input and whether signed decimal inputs are in contract",
        "negative-number handling, another numeric boundary, or an unstated representation convention remain plausible",
        "run one contract-approved signed boundary case and preserve input, expected representation, and exception/return",
        ("negative_number_boundary", "loop returns an empty string for n<0, but the public input domain does not close signed-number semantics"),
    ),
    2: _unresolved(
        "len(outer_list) equals the public all-sublists example",
        "required entry point and integer result are present; saved base passes and Plus fails",
        "whether heterogeneous outer lists are contract-valid and the first failing Plus case",
        "contract may require len(list-of-lists) or counting only sublist-valued members",
        "run one contract-approved heterogeneous outer-list case and preserve the expected counting rule",
        ("element_type_counting_semantics", "the implementation checks only the outer container, not each member"),
    ),
    3: _unresolved(
        "parser accepts the public two-digit fractional example and also accepts integers or shorter fractional parts",
        "public wording and example do not uniquely distinguish exactly-two from at-most-two precision semantics; base passes and Plus fails",
        "authoritative precision grammar and first failing Plus string",
        "exactly two digits, at most two digits, signs, and empty fractional components remain plausible boundaries",
        "run the minimal contract-approved boundary set {'123','123.1','123.'} and preserve the expected grammar",
        ("decimal_precision_boundary", "the <=2 rule may be too broad, but the public contract does not close the grammar"),
    ),
    4: _unresolved(
        "sorted dynamic programming constructs divisibility chains and satisfies the public example",
        "entry point and scalar result are present; saved base passes and Plus fails",
        "first failing Plus list and allowed zero/negative/duplicate domain",
        "duplicate-key collapse, zero divisors, signed values, or another boundary may explain the Plus failure",
        "run one minimal contract-approved list isolating duplicate/zero domain and preserve the first failing assertion",
        ("numeric_domain_boundary", "dict-keyed DP and modulo operations have unclosed duplicate and zero behavior"),
    ),
    5: _unresolved(
        "three hyphen-separated components are reversed and the public yyyy-mm-dd example is satisfied",
        "entry point and string shape are present; saved base passes and Plus fails",
        "first failing Plus date and normalization/validation requirements",
        "padding, malformed dates, calendar validation, or another unstated boundary may explain failure",
        "run one contract-approved boundary date that distinguishes pure component reversal from normalization",
        ("date_normalization_boundary", "source performs component reversal only; extra validation is not specified publicly"),
    ),
    6: _decision(
        "source keeps the first occurrence of every distinct value, producing [1,2,3,4,5] for the public input",
        "public result [1,4,5] requires values whose global frequency is exactly one",
        "the implementation solves stable deduplication rather than selecting values occurring only once",
        [
            ("dedupe_instead_of_unique_occurrence", "CONFIRMED", "repeated 2 and 3 are retained once instead of excluded"),
            ("semantic_goal_drift", "CONFIRMED", "implemented objective differs from the public contract"),
            ("algorithm_reconstruction_required", "SUPPORTED", "repair requires frequency-aware selection semantics"),
        ],
    ),
    7: _unresolved(
        "n modulo 10 returns the public positive last digit",
        "entry point and integer result are present; saved base passes and Plus fails",
        "signed-number convention and first failing Plus value",
        "negative inputs may require an absolute digit, or another numeric boundary may fail",
        "run one contract-approved negative integer and preserve the expected sign convention",
        ("negative_number_boundary", "Python modulo gives a non-obvious result for negative n"),
    ),
    8: _decision(
        "for public n=5 every loop branch continues and the function returns False",
        "public specification explicitly requires dif_Square(5)==True",
        "the difference-of-squares search conditions skip the witnessed valid case",
        [
            ("difference_of_squares_condition_error", "CONFIRMED", "control conditions skip n=5 and return False"),
            ("algorithmic_error", "CONFIRMED", "search does not implement the stated number-theoretic predicate"),
            ("algorithm_reconstruction_required", "SUPPORTED", "safe correction requires replacing the core decision procedure"),
        ],
    ),
    9: _unresolved(
        "len(outer_list) equals the public all-sublists example",
        "required entry point and integer result are present; saved base passes and Plus fails",
        "whether heterogeneous outer lists are contract-valid and the first failing Plus case",
        "contract may require len(list-of-lists) or counting only sublist-valued members",
        "run one contract-approved heterogeneous outer-list case and preserve the expected counting rule",
        ("element_type_counting_semantics", "the implementation checks only the outer container, not each member"),
    ),
    10: _decision(
        "Counter preserves tuple orientation and therefore keeps (3,1) separate from (1,3)",
        "public output merges reversed tuple pairs into canonical keys (1,3) and (2,5)",
        "the required unordered-pair normalization is absent",
        [
            ("tuple_pair_normalization_omitted", "CONFIRMED", "reversed tuples are counted as distinct keys"),
            ("semantic_goal_drift", "CONFIRMED", "raw tuple frequency is not canonical unordered-pair frequency"),
            ("algorithm_reconstruction_required", "SUPPORTED", "repair must introduce task-specific canonicalization"),
        ],
    ),
    11: _decision(
        "on [1,1,2,2,3], mid pair advances left to 4 and the loop exits with None",
        "public specification requires search([1,1,2,2,3])==3; saved evaluator also records base/Plus fail",
        "binary-search pair alignment and terminal return logic do not locate the unique element",
        [
            ("binary_search_pair_alignment_error", "CONFIRMED", "pair parity is not maintained when advancing bounds"),
            ("algorithmic_error", "CONFIRMED", "public input is statically mapped to None"),
            ("diagnostic_infrastructure_failure", "CONFIRMED", "preserved formal diagnostics record WorkerProcessExit; this diagnostic-only observation does not displace the public static L5 violation"),
            ("algorithm_reconstruction_required", "SUPPORTED", "correcting the binary search changes core control flow"),
        ],
    ),
    12: _decision(
        "list comprehension preserves list1 order and returns [10,15,20,30]",
        "public contract explicitly expects [10,20,30,15] for the same arguments",
        "the required output ordering semantics are not implemented",
        [
            ("incorrect_ordering_semantics", "CONFIRMED", "source order differs from the public required order"),
            ("embedded_assert_contract_drift", "CONFIRMED", "candidate's own assert encodes a different result than the prompt"),
            ("algorithm_reconstruction_required", "SUPPORTED", "general ordering rule cannot be recovered by a local invariant-preserving edit"),
        ],
    ),
    13: _decision(
        "split plus str.islower accepts components containing lowercase letters mixed with digits or punctuation",
        "public contract restricts accepted components to sequences of lowercase letters joined by underscore",
        "character-class validation is broader than the stated lowercase-letter grammar",
        [
            ("lowercase_letter_class_underconstrained", "CONFIRMED", "islower does not require every character to be a letter"),
            ("edge_case_omission", "CONFIRMED", "non-letter characters are not rejected"),
            ("algorithm_reconstruction_required", "SUPPORTED", "repair requires choosing and enforcing the public grammar"),
        ],
    ),
    14: _unresolved(
        "stack/pair logic accepts the public balanced-bracket example",
        "required entry point and boolean result are present; saved base passes and Plus fails",
        "first failing Plus expression and treatment of non-bracket characters",
        "non-bracket handling, expression grammar, or another boundary may explain the failure",
        "run one contract-approved expression containing a non-bracket token and preserve expected validity",
        ("expression_character_domain", "non-bracket characters are ignored, but public expression grammar is not closed"),
    ),
    15: _unresolved(
        "stack/pair logic accepts the public balanced-bracket example",
        "required entry point and boolean result are present; saved base passes and Plus fails",
        "first failing Plus expression and treatment of non-bracket characters",
        "non-bracket handling, expression grammar, or another boundary may explain the failure",
        "run one contract-approved expression containing a non-bracket token and preserve expected validity",
        ("expression_character_domain", "non-bracket characters are ignored, but public expression grammar is not closed"),
    ),
    16: _decision(
        "required is_polite entry point returns a boolean predicate while the public assertion requires the seventh polite number 11",
        "public contract directly states is_polite(7)==11; source returns True for 7",
        "candidate implements a politeness predicate under the required name instead of the nth-value function",
        [
            ("predicate_instead_of_nth_value", "CONFIRMED", "required callable returns bool rather than nth polite number"),
            ("semantic_goal_drift", "CONFIRMED", "source contains a separate nth_polite_number objective but binds the required entry to a predicate"),
            ("algorithm_reconstruction_required", "SUPPORTED", "rebinding or replacing semantics is not a thin contract-only repair"),
        ],
    ),
    17: _decision(
        "regex match for 'clearly' spans [0,7), but source reports match.end()-1 and returns end position 6",
        "public contract requires (0,7,'clearly')",
        "the end-position convention is implemented as inclusive instead of the required exclusive index",
        [
            ("end_index_off_by_one", "CONFIRMED", "subtracting one contradicts the public position tuple"),
            ("wrong_boundary_condition", "CONFIRMED", "end boundary uses the wrong convention"),
            ("algorithm_reconstruction_required", "SUPPORTED", "no pre-frozen evaluator-blind Healer rule authorizes semantic index changes"),
        ],
    ),
    18: _decision(
        "DP extends a chain whenever adjacent states are comparable, although divisibility comparability is not transitive when direction flips",
        "source can count [2,6,3] as length 3 even though 2 and 3 are not mutually divisible; public task requires every pair",
        "pairwise comparability is replaced by a non-valid dynamic-programming recurrence",
        [
            ("pairwise_divisibility_nontransitive_dp", "CONFIRMED", "state extension does not ensure all prior members are comparable to the new value"),
            ("algorithmic_error", "CONFIRMED", "the recurrence can admit invalid subsets"),
            ("algorithm_reconstruction_required", "SUPPORTED", "repair requires a correct chain/subset algorithm"),
        ],
    ),
    19: _decision(
        "for public '123.11', evaluation attempts .abs() on a float; the broad except converts that defect into False",
        "public contract requires is_decimal('123.11')==True",
        "malformed validation expression and exception swallowing produce a wrong semantic answer",
        [
            ("exception_swallowed_to_wrong_answer", "CONFIRMED", "AttributeError is caught and returned as False"),
            ("decimal_validation_expression_error", "CONFIRMED", "float has no .abs method and chained comparison is malformed"),
            ("algorithmic_error", "CONFIRMED", "public input is statically rejected"),
            ("algorithm_reconstruction_required", "SUPPORTED", "correct decimal grammar cannot be recovered by a unique local transformation"),
        ],
    ),
    20: _unresolved(
        "with k equal to list length, nested loops enumerate all unordered pairs and satisfy the public example",
        "entry point and scalar result are present; saved base passes and Plus fails",
        "meaning of k when it differs from len(nums), plus the first failing Plus case",
        "k may denote input length, a prefix length, or a window; public wording does not specify it",
        "run one contract-approved case with k<len(nums) and preserve the intended parameter semantics",
        ("second_parameter_semantics", "loop treats k as a forward window while iterating every list element"),
    ),
    21: _unresolved(
        "three hyphen-separated components are reversed and the public yyyy-mm-dd example is satisfied",
        "entry point and string shape are present; saved base passes and Plus fails",
        "first failing Plus date and normalization/validation requirements",
        "padding, malformed dates, calendar validation, or another unstated boundary may explain failure",
        "run one contract-approved boundary date that distinguishes pure component reversal from normalization",
        ("date_normalization_boundary", "source performs component reversal only; extra validation is not specified publicly"),
    ),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    remaining21 = _read_csv(repo, REMAINING21)
    audit = _read_csv(repo, AUDIT_FINDINGS)
    accounts = {row["program_id"]: row for row in _read_jsonl(repo, ACCOUNTS) if row.get("healer_account") == "H0"}
    tasks = {row["task_id"]: row for row in _read_jsonl(repo, TASKS)}
    eval_rows = {row["program_id"]: row for row in _read_csv(repo, EVALPLUS) if row["healer_account"] == "H0"}
    preparation = {row["program_id"]: row for row in _read_csv(repo, PREPARATION)}
    frozen_ids = {(row["program_id"], row["cell_identity_sha256"]) for row in _read_csv(repo, CUMULATIVE177)}
    _require(len(roster) == len(remaining21) == len(audit) == len(DECISIONS) == 21, "21-cell closure drift")
    _require(all(row["audit_status"] == "AFFIRMED" for row in audit), "roster audit not 21 AFFIRMED")
    _require([row["selection_rank"] for row in roster] == [str(i) for i in range(1, 22)], "roster rank drift")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in remaining21], "remaining21 order drift")

    records: list[dict[str, str]] = []
    mechanisms: list[dict[str, str]] = []
    chains: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    for rank, roster_row in enumerate(roster, 1):
        decision = DECISIONS[rank]
        program_id = roster_row["program_id"]
        account = accounts[program_id]
        source = account.get("evaluation_source", "")
        _require(isinstance(source, str) and bool(source), f"empty source rank {rank}")
        _require(_sha(source.encode("utf-8")) == roster_row["source_sha256"], f"source SHA drift rank {rank}")
        task = tasks[roster_row["task_id"]]
        eval_row = eval_rows[program_id]
        prep = preparation[program_id]
        _require(task["entry_point"] in source, f"entry point absent rank {rank}")
        _require(eval_row["base_status"] in {"pass", "fail"} and eval_row["plus_status"] == "fail", f"saved result drift rank {rank}")
        identity = (program_id, roster_row["cell_identity_sha256"])
        _require(identity not in frozen_ids, f"rank {rank} overlaps frozen177")
        citations = ";".join([
            f"{ROSTER.as_posix()}#selection_rank={rank}",
            f"{roster_row['source_artifact_path']}",
            f"{TASKS.as_posix()}#task_id={roster_row['task_id']}",
            f"{EVALPLUS.as_posix()}#program_id={program_id};healer_account=H0",
            f"{PREPARATION.as_posix()}#cell_identity_sha256={roster_row['cell_identity_sha256']}",
            f"{TAXONOMY.as_posix()}#sections=2,4,5,8,9,10,11,12",
        ])
        tags = [
            {"tag": tag, "strength": strength, "note": note}
            for tag, strength, note in decision["mechanisms"]
        ]
        first_tag = tags[0]["tag"]
        chain = [
            {
                "stage": "preserved_candidate_static_review", "gate": "G1/G2/G3e",
                "layer": None, "mechanism": "parseable_required_entry_point_present",
                "validity": "VALID_MODEL_OUTCOME",
                "evidence": f"{roster_row['source_artifact_path']}",
            },
            {
                "stage": "preserved_correctness_evidence", "gate": "G4",
                "layer": decision["primary"], "mechanism": first_tag,
                "validity": "VALID_MODEL_OUTCOME",
                "evidence": f"{EVALPLUS.as_posix()}#program_id={program_id};base={eval_row['base_status']};plus={eval_row['plus_status']}",
            },
        ]
        if prep["diagnostic_phase"] == "infrastructure":
            chain.insert(1, {
                "stage": "preserved_formal_diagnostics", "gate": "G2",
                "layer": "L0", "mechanism": "diagnostic_infrastructure_failure",
                "validity": "INVALID_INFRASTRUCTURE_DIAGNOSTIC_SCOPE_ONLY",
                "evidence": f"{PREPARATION.as_posix()}#cell_identity_sha256={roster_row['cell_identity_sha256']};exception={prep['diagnostic_exception_class']}",
            })
        if decision["primary"] == "UNRESOLVED":
            chain.append({
                "stage": "provisional_static_adjudication", "gate": "resolution",
                "layer": "UNRESOLVED", "mechanism": "insufficient_static_evidence",
                "validity": "VALID_MODEL_OUTCOME", "evidence": decision["missing"],
            })
        healer_reason = (
            "根因與唯一安全修法均未閉合；不得以 Plus failure 猜測修補。"
            if decision["primary"] == "UNRESOLVED"
            else "修正涉及題意、語意或核心演算法，且無事前凍結的唯一 evaluator-blind 局部規則。"
        )
        record = {
            "batch_rank": str(rank), "cell_identity_sha256": roster_row["cell_identity_sha256"],
            "program_id": program_id, "source_sha256": roster_row["source_sha256"],
            "task_id": roster_row["task_id"], "seed": roster_row["seed"],
            "generation_id": roster_row["generation_id"], "condition": roster_row["condition"],
            "review_status": "PROVISIONALLY_ADJUDICATED", "classification_status": "ADJUDICATED",
            "primary_layer": decision["primary"], "secondary_layer": decision["secondary"],
            "mechanism_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "failure_chain": json.dumps(chain, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "confidence": decision["confidence"], "outcome_validity": "VALID_MODEL_OUTCOME",
            "healer_eligibility": "abstain", "eligibility_reason": healer_reason,
            "eligibility_rule": "", "rejection_condition": "not_unique_local_deterministic_oracle_independent_semantics_preserving",
            "unresolved_reason_code": decision["unresolved_code"],
            "evidence_present": decision["evidence"], "evidence_missing": decision["missing"],
            "competing_explanations": decision["competing"], "reason": decision["reason"],
            "minimal_future_diagnostic": decision["diagnostic"],
            "public_evidence": task["prompt"].strip(), "evidence_citations": citations,
            "source_structure_locator": decision["observation"],
            "adjudicator_identity": ADJUDICATOR, "adjudication_timestamp": TIMESTAMP,
            "planning_signal_note": "fixed roster before adjudication; no outcome-based selection; Plus failure alone did not localize a mechanism",
        }
        records.append(record)
        for tag in tags:
            mechanisms.append({
                "batch_rank": str(rank), "program_id": program_id,
                "cell_identity_sha256": roster_row["cell_identity_sha256"],
                "primary_layer": decision["primary"], "mechanism_tag": tag["tag"],
                "strength": tag["strength"], "note": tag["note"],
            })
        chains.append({
            "batch_rank": str(rank), "program_id": program_id,
            "cell_identity_sha256": roster_row["cell_identity_sha256"],
            "stage_count": str(len(chain)), "primary_layer": decision["primary"],
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "failure_chain_json": record["failure_chain"], "citations": citations,
        })
        if decision["primary"] == "UNRESOLVED":
            gaps.append({field: record[field] for field in GAP_FIELDS})

    program_ids = {row["program_id"] for row in records}
    cell_ids = {row["cell_identity_sha256"] for row in records}
    source_ids = {row["source_sha256"] for row in records}
    _require(len(program_ids) == len(cell_ids) == 21 and len(source_ids) == 20, "identity/source closure drift")
    _require(len(gaps) == 11, "UNRESOLVED count drift")
    primary = Counter(row["primary_layer"] for row in records)
    secondary = Counter(row["secondary_layer"] or "empty" for row in records)
    confidence = Counter(row["confidence"] for row in records)
    outcome = Counter(row["outcome_validity"] for row in records)
    healer = Counter(row["healer_eligibility"] for row in records)
    mechanism_counts = Counter(row["mechanism_tag"] for row in mechanisms)
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 21, "rank_range": "1-21", "formal_population": 198,
        "frozen_before_batch05": 177, "remaining_adjudicated_after_batch05": 0,
        "set_closure": "198=177+21", "primary_distribution": dict(sorted(primary.items())),
        "secondary_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_distribution": dict(sorted(healer.items())),
        "mechanism_distribution": dict(sorted(mechanism_counts.items())),
        "unresolved_ranks": [int(row["batch_rank"]) for row in records if row["primary_layer"] == "UNRESOLVED"],
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "legal_shared_source_ranks": [5, 21], "overlap_with_frozen177": 0,
        "taxonomy_judgments_created": 21, "independent_audit_performed": False,
    }
    return {"records": records, "mechanisms": mechanisms, "chains": chains, "gaps": gaps, "summary": summary}


def _report(summary: dict[str, Any], records_sha: str) -> str:
    p = summary["primary_distribution"]
    return (
        "# Candidate B r003 taxonomy v3.1：Final Batch05 provisional adjudication v1\n\n"
        f"**狀態：`{STATUS}`**\n\n**Records SHA-256：`{records_sha}`**\n\n"
        f"- Primary：L5={p.get('L5', 0)}、UNRESOLVED={p.get('UNRESOLVED', 0)}；Secondary empty=21。\n"
        "- Confidence：HIGH=10、LOW=11；Outcome：VALID_MODEL_OUTCOME=21。\n"
        "- Healer：eligible=0、conditional=0、abstain=21。\n"
        "- UNRESOLVED ranks：1、2、3、4、5、7、9、14、15、20、21。\n"
        "- 198=177+21；本批處理後未裁決剩餘集合=0。\n"
        "- ranks 5、21 合法共享 source；program/cell identity 不同。\n"
        "- 本 revision 僅使用既有靜態 source、public specification 與保存結果，尚未進行獨立 audit。\n"
        "- model、candidate/import、public/hidden tests、EvalPlus、diagnostics、validation、Healer及program execution均為0。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    records_bytes = _csv_bytes(RECORD_FIELDS, analysis["records"])
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "adjudication_records.csv": records_bytes,
        "mechanism_ledger.csv": _csv_bytes(MECHANISM_FIELDS, analysis["mechanisms"]),
        "failure_chain_ledger.csv": _csv_bytes(CHAIN_FIELDS, analysis["chains"]),
        "unresolved_evidence_gaps.csv": _csv_bytes(GAP_FIELDS, analysis["gaps"]),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(records_bytes)).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "evidence_policy": "preserved public specification, generated source text, saved baseline/Plus statuses, and existing static metadata only",
        "candidate_code_imported_or_executed": False, "independent_audit_performed": False,
        "batch05_frozen": False, "batch06_created": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    outputs["manifest.json"] = _json_bytes({
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "records_sha256": _sha(records_bytes),
        "roster_sha256": SOURCE_HASHES[ROSTER], "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS],
        "roster_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "remaining21_sha256": SOURCE_HASHES[REMAINING21], "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "cells": 21, "remaining_after_adjudication": 0,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    })
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
    print(f"records_sha256={manifest['records_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
