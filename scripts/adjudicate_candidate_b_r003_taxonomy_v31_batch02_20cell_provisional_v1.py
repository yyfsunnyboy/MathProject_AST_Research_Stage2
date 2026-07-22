#!/usr/bin/env python3
"""Static provisional adjudication of the fixed Candidate B r003 Batch02 roster.

No candidate/import/test/EvalPlus/diagnostic/validation/Healer/model execution is
performed.  Decisions use only frozen source, public contracts, existing results,
and static derivation.
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
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1"
)
START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_INDEPENDENT_AUDIT"
VERDICT = "READY_FOR_BATCH02_PROVISIONAL_V1_AUDIT"
ADJUDICATOR = "taxonomy_v31_batch02_provisional_v1_static_adjudicator"
ADJUDICATION_TIMESTAMP = "2026-07-22T00:00:00+08:00"

ROSTER_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1"
)
ROSTER = ROSTER_DIR / "batch02_roster.csv"
ROSTER_MANIFEST = ROSTER_DIR / "manifest.json"
ROSTER_PROVENANCE = ROSTER_DIR / "provenance.json"
ROSTER_BUILDER = Path(
    "scripts/prepare_candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1.py"
)
INVENTORY = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/"
    "static_signal_inventory.csv"
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
PAIRED = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv"
)

SOURCE_HASHES = {
    ROSTER: "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d",
    ROSTER_MANIFEST: "05aa6192198ba4e7c6bf2ea04e043e7bd3c14a2619ba41b623496cf34e21c0a0",
    ROSTER_PROVENANCE: "5913705830ce8b6685bd1e5bd6ed7aa16d12ca6ce456f2c137290aded7395fd6",
    ROSTER_BUILDER: "499e3bd4d37d57b81ff8eb2ffde5ab8e59dd355c60cdb530aa948dd1faa02f70",
    INVENTORY: "c3ffa467ce77aca62a205a68a12768f83720bec3b202a65a8f91e4efe916ffed",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    JOURNAL: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PAIRED: "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
}

TAXONOMY_REFERENCE = {
    "filename": "AI_生成程式共同失敗分類標準_實際使用版_v3.1.md",
    "sha256": "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
    "status": "EXTERNAL_PLANNING_REFERENCE_NOT_INGESTED_INTO_REPO_GOVERNANCE",
}

ROSTER_FIELDS = (
    "batch_rank", "cell_identity_sha256", "program_id", "source_sha256",
    "task_id", "seed", "generation_id", "condition", "source_roster_rank",
)
RECORD_FIELDS = (
    "batch_rank", "cell_identity_sha256", "program_id", "source_sha256", "task_id",
    "seed", "generation_id", "condition", "review_status", "primary_layer",
    "secondary_layer", "mechanism_tags_json", "failure_chain", "confidence",
    "outcome_validity", "healer_eligibility", "eligibility_reason", "eligibility_rule",
    "rejection_condition", "unresolved_reason_code", "evidence_present",
    "evidence_missing", "minimal_future_diagnostic", "public_evidence",
    "evidence_citations", "source_structure_locator", "adjudicator_identity",
    "adjudication_timestamp", "planning_signal_note",
)
GAP_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "task_id",
    "unresolved_reason_code", "evidence_present", "evidence_missing",
    "minimal_future_diagnostic", "healer_eligibility",
)

VALID_PRIMARY = {"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"}
VALID_SECONDARY = {"", "L0", "L1", "L2", "L3", "L4", "L5"}
VALID_STRENGTH = {"CONFIRMED", "SUPPORTED", "SUSPECTED", "REJECTED"}
VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
VALID_HEALER = {"eligible", "conditional", "abstain"}
VALID_OUTCOME = {"VALID_MODEL_OUTCOME", "INVALID_INFRASTRUCTURE", "INVALID_EVALUATOR", "PENDING_REVIEW"}


class AdjudicationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


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


def _mech(*items: tuple[str, str, str]) -> list[dict[str, str]]:
    result = []
    for tag, strength, note in items:
        _require(strength in VALID_STRENGTH, f"invalid mechanism strength: {strength}")
        result.append({"tag": tag, "strength": strength, "note": note})
    return result


def _decision(
    *, primary: str, secondary: str = "", mechanisms: list[dict[str, str]],
    chain: list[str], confidence: str, healer: str, eligibility_reason: str,
    public_evidence: str, source_locator: str, unresolved_reason: str = "",
    evidence_missing: str = "", future_diagnostic: str = "", eligibility_rule: str = "",
    rejection_condition: str = "", evidence_present: str = "frozen source; public contract; existing EvalPlus status",
) -> dict[str, Any]:
    _require(primary in VALID_PRIMARY, f"invalid primary: {primary}")
    _require(secondary in VALID_SECONDARY and secondary != primary, "invalid secondary")
    _require(confidence in VALID_CONFIDENCE, "invalid confidence")
    _require(healer in VALID_HEALER, "invalid healer")
    if primary == "UNRESOLVED":
        _require(confidence == "LOW" and healer == "abstain", "UNRESOLVED must be LOW/abstain")
        _require(bool(unresolved_reason and evidence_missing and future_diagnostic), "UNRESOLVED gap incomplete")
    if healer == "eligible":
        _require(bool(eligibility_rule and rejection_condition), "eligible rule/guard required")
    return {
        "primary_layer": primary,
        "secondary_layer": secondary,
        "mechanism_tags_json": _json(mechanisms),
        "failure_chain": " → ".join(chain),
        "confidence": confidence,
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "healer_eligibility": healer,
        "eligibility_reason": eligibility_reason,
        "eligibility_rule": eligibility_rule,
        "rejection_condition": rejection_condition,
        "unresolved_reason_code": unresolved_reason,
        "evidence_present": evidence_present,
        "evidence_missing": evidence_missing,
        "minimal_future_diagnostic": future_diagnostic,
        "public_evidence": public_evidence,
        "source_structure_locator": source_locator,
        "planning_signal_note": "planning signal was reviewed but never promoted directly to L2 or healer eligibility",
    }


def _unresolved(note: str, source_locator: str, public_evidence: str, missing: str) -> dict[str, Any]:
    return _decision(
        primary="UNRESOLVED",
        mechanisms=_mech(
            ("public_examples_non_discriminating", "CONFIRMED", note),
            ("plus_failure_not_localized", "CONFIRMED", "existing base pass / plus fail has no disclosed failing input"),
            ("return_shape_mismatch", "SUSPECTED", "census signal only; public return violation not established"),
            ("diagnostic_execution_required", "SUPPORTED", "additional observation would be needed to close the root layer"),
        ),
        chain=["parseable entry point present", "public example satisfied statically", "plus failure root not localized", "primary=UNRESOLVED", "healer=abstain"],
        confidence="LOW", healer="abstain",
        eligibility_reason="Evidence does not establish one unique local oracle-independent repair.",
        unresolved_reason="public_example_satisfied_plus_failure_not_localized",
        evidence_missing=missing,
        future_diagnostic="capture the first existing failing plus-case input class and exception/return without applying a repair",
        public_evidence=public_evidence, source_locator=source_locator,
    )


DECISIONS: dict[str, dict[str, Any]] = {
    "00227845900dfa7dd96b61bef5d30b83f583ff6576a9846c8b20c41fbbf5ffc0": _unresolved(
        "contiguous-sublist implementation returns False for the sole public example",
        "evaluation_source:def is_Sub_Array; sliding contiguous window",
        "assert is_Sub_Array([1,4,3,5],[1,2]) == False",
        "whether hidden plus cases define sublist as contiguous or non-contiguous and the first failing behavior",
    ),
    "0289530320e18702b3707c97e303a554dad0bdbb69b4aa25e0a3382ec2da0e89": _decision(
        primary="L2", secondary="L5",
        mechanisms=_mech(
            ("output_schema_mismatch", "CONFIRMED", "returns bool while public contract requires nth decagonal integer 27"),
            ("task_semantics_misread_as_membership_predicate", "CONFIRMED", "solves membership rather than generation"),
            ("algorithm_reconstruction_required", "CONFIRMED", "inverse/membership formula cannot be packaged into the required generator"),
        ),
        chain=["entry point present", "predicate computes membership-like boolean", "public contract requires integer nth value", "primary=L2; secondary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Correcting the return schema also requires replacing the algorithm; no unique packaging-only edit.",
        public_evidence="assert is_num_decagonal(3) == 27",
        source_locator="evaluation_source:def is_num_decagonal returns boolean membership expression",
    ),
    "0c4c8a0096c96cacc5adea93589cc74bc53fcb5d9dad02c7a7e9a9c51d830483": _unresolved(
        "middle-bit mask gives 15 for public n=9",
        "evaluation_source:bit_length/full_mask/middle_mask and trailing assert",
        "assert toggle_middle_bits(9) == 15",
        "the first plus boundary that fails and whether n<3 handling or another semantic edge is responsible",
    ),
    "0ccf0f940c52dbf90d4e25aa554e4a6cf41703658cc8dc88f380d32d585b7d45": _decision(
        primary="L2", secondary="L5",
        mechanisms=_mech(
            ("output_schema_mismatch", "CONFIRMED", "returns bool instead of the required integer 27"),
            ("task_semantics_misread_as_membership_predicate", "CONFIRMED", "square-root predicate does not generate a decagonal number"),
            ("algorithm_reconstruction_required", "CONFIRMED", "generation formula is absent"),
        ),
        chain=["entry point present", "boolean square-root predicate", "public integer result required", "primary=L2; secondary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Repair requires constructing the missing generation algorithm, not a local output adapter.",
        public_evidence="assert is_num_decagonal(3) == 27",
        source_locator="evaluation_source:return abs(k-round(k))... boolean",
    ),
    "0d1b40c698eb61156fcd8273761fdde26c3a55ea65bd7874bf4c5dfa7bb15b57": _unresolved(
        "stack/pair logic returns True for the sole balanced public expression",
        "evaluation_source:stack and closing-bracket pair checks",
        "assert check_expression('{()}[{}]') == True",
        "first failing plus expression and whether non-bracket handling or another boundary is intended",
    ),
    "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d": _decision(
        primary="L5",
        mechanisms=_mech(
            ("negative_number_boundary", "CONFIRMED", "Python n%10 gives 7 for -123 whereas the last decimal digit is 3"),
            ("semantic_boundary_repair", "SUPPORTED", "handling sign requires an explicit semantic choice such as abs(n)%10"),
            ("return_shape_mismatch", "REJECTED", "integer scalar shape is correct"),
        ),
        chain=["entry point present", "returns n modulo 10", "negative inputs expose sign/modulo semantic mismatch", "primary=L5", "healer=abstain"],
        confidence="MEDIUM", healer="abstain",
        eligibility_reason="Sign semantics change algorithm behavior and are not an output-packaging repair.",
        public_evidence="task asks for last digit; public positive example is 123→3",
        source_locator="evaluation_source:return n % 10",
    ),
    "1538fce8f0da403922caeaebb8afd96d129f6faf80378266f3b689bcdfd7231c": _unresolved(
        "stack/pair logic returns True for the sole balanced public expression",
        "evaluation_source:stack and closing-bracket pair checks",
        "assert check_expression('{()}[{}]') == True",
        "first failing plus expression and the intended treatment of non-bracket characters",
    ),
    "15e92b97d59405977ea60125b6561bc1d30dd262ffe10eef4db8220e844f0345": _decision(
        primary="L5",
        mechanisms=_mech(
            ("wrong_boundary_condition", "CONFIRMED", "comparison arr[mid] < value implements left insertion, not right insertion for duplicates"),
            ("duplicate_value_semantics", "CONFIRMED", "right insertion must advance past equal values"),
            ("return_shape_mismatch", "REJECTED", "integer insertion index shape is correct"),
        ),
        chain=["entry point present", "binary search moves right only for strictly smaller values", "equal values are placed on the left", "primary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Changing comparison semantics alters the algorithm; taxonomy eligibility excludes semantic repairs.",
        public_evidence="task explicitly requests the right insertion point; public no-duplicate example returns 4",
        source_locator="evaluation_source:if arr[mid] < value",
    ),
    "190a6f4d6f37fc027ca4c750047f26410391c75504d986687ffa4e4fdf237f7e": _decision(
        primary="L5",
        mechanisms=_mech(
            ("incorrect_recurrence", "CONFIRMED", "dp[i]=sum(dp[:i]) yields powers of two after n=1, not Bell numbers"),
            ("algorithm_reconstruction_required", "CONFIRMED", "Bell triangle/recurrence state is absent"),
            ("public_example_non_discriminating", "SUPPORTED", "n=2 happens to equal 2 under the wrong recurrence"),
        ),
        chain=["entry point present", "prefix-sum recurrence", "recurrence diverges from Bell partition counts beyond public n=2", "primary=L5", "healer=abstain"],
        confidence="MEDIUM", healer="abstain",
        eligibility_reason="A correct Bell recurrence requires algorithm reconstruction.",
        public_evidence="task requests Bell partition counts; assert bell_number(2)==2",
        source_locator="evaluation_source:row_sum += dp[j]; dp[i]=row_sum",
    ),
    "1ad9aa1f3690e77628cb0d4db2bb1e46e3dd763ff73a464291e3f095b9f6a3cf": _decision(
        primary="L5",
        mechanisms=_mech(
            ("incorrect_ordering_semantics", "CONFIRMED", "list1-order filter gives [10,15,20,30], not public [10,20,30,15]"),
            ("algorithm_reconstruction_required", "SUPPORTED", "required difference ordering is not implemented"),
            ("return_shape_mismatch", "REJECTED", "both actual and expected are lists"),
        ),
        chain=["entry point present", "filters list1 in original order", "public expected ordering differs", "primary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Repair changes list-difference ordering semantics.",
        public_evidence="assert Diff([...],[25,40,35]) == [10,20,30,15]",
        source_locator="evaluation_source:return [x for x in list1 if x not in list2]",
    ),
    "1c39a49b4005394ebfe1338e37cfef9e9db2b71dbd3a6114c1b0fda88ef8f4c8": _decision(
        primary="L5",
        mechanisms=_mech(
            ("incorrect_formula", "CONFIRMED", "maximum triangle with diameter 2r and height r has area r^2, not r^2/2"),
            ("algorithm_reconstruction_required", "SUPPORTED", "geometric formula must be corrected"),
            ("public_example_non_discriminating", "SUPPORTED", "negative-radius None guard does not test the formula"),
        ),
        chain=["entry point and negative guard valid", "positive branch returns r^2/2", "semicircle maximum-area geometry requires r^2", "primary=L5", "healer=abstain"],
        confidence="MEDIUM", healer="abstain",
        eligibility_reason="Correcting a geometry formula is semantic, not a mechanical contract repair.",
        public_evidence="task asks for largest triangle in a semicircle; negative public guard returns None",
        source_locator="evaluation_source:return radius ** 2 / 2",
    ),
    "2007ec98d098057747bdf3975c81264c967ff76547d3bac23e622cdfe8571bf6": _unresolved(
        "middle-bit mask gives 15 for public n=9",
        "evaluation_source:full_mask ^ msb_bit ^ lsb_bit and trailing assert",
        "assert toggle_middle_bits(9) == 15",
        "the first failing plus boundary and intended behavior for very small or signed inputs",
    ),
    "252857c7146e4e03a3ab17d02333bc99e89b8b38f5ed12e1c1a6f8ad88707eae": _unresolved(
        "float parse plus <=2 fractional characters accepts the sole public 123.11 example",
        "evaluation_source:float(s), dot check, fractional length <=2",
        "assert is_decimal('123.11') == True",
        "whether precision means exactly two or up to two digits and the first failing syntax class",
    ),
    "26a25fbe4008e736db5684337d5d6b744a199a2cc7319535c3ea4dd83c546065": _unresolved(
        "repeated division produces public 8→1000 and no leading zeros",
        "evaluation_source:while n>0 append remainder then reverse",
        "assert decimal_to_binary(8) == '1000'",
        "the intended domain for negative/non-integer inputs and first failing plus behavior",
    ),
    "284533f93cc2a9c9012d005c206eb17d6cc6285ea8b17d997e50cb62fcabeafd": _decision(
        primary="L4", secondary="L5",
        mechanisms=_mech(
            ("mixed_type_comparison_exception", "CONFIRMED", "after current_min changes from str to int, is_numeric remains false and later str<int comparison can raise TypeError"),
            ("state_invariant_broken", "CONFIRMED", "current_min type and is_numeric flag can disagree"),
            ("algorithm_reconstruction_required", "SUPPORTED", "heterogeneous ordering policy is not consistently defined"),
        ),
        chain=["entry point present", "state starts as nonnumeric string", "numeric candidate changes value but not type-state flag", "later incompatible comparison can raise", "primary=L4; secondary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Multiple state and ordering choices prevent a unique local repair.",
        public_evidence="assert min_val(['Python',3,2,4,5,'version']) == 2",
        source_locator="evaluation_source:not is_numeric and str(val_int) < current_min",
    ),
    "2c3e0315fdaee4106bde69e7cbb8fdf7a0827cfabb24165dcf6197428338d83b": _unresolved(
        "prefixing remainders produces public 8→1000",
        "evaluation_source:while n>0 binary=str(n%2)+binary",
        "assert decimal_to_binary(8) == '1000'",
        "the intended signed/input domain and first failing plus behavior",
    ),
    "2ce918fcbdb6d00efd2ed40243b601a3efbc5a849c1391961daf9b03717c7fba": _unresolved(
        "sum of (2i)^2 gives public square_Sum(2)==20",
        "evaluation_source:for i in 1..n; total += (2*i)**2 and trailing assert",
        "assert square_Sum(2) == 20",
        "the first failing plus boundary and intended behavior for non-positive inputs",
    ),
    "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a": _decision(
        primary="L5",
        mechanisms=_mech(
            ("negative_number_boundary", "CONFIRMED", "Python n%10 follows modulo semantics rather than magnitude's last digit for negative n"),
            ("semantic_boundary_repair", "SUPPORTED", "sign handling is absent"),
            ("return_shape_mismatch", "REJECTED", "integer scalar shape is correct"),
        ),
        chain=["entry point present", "returns n modulo 10", "negative values violate ordinary last-digit semantics", "primary=L5", "healer=abstain"],
        confidence="MEDIUM", healer="abstain",
        eligibility_reason="Sign handling changes semantics and is not an eligible packaging edit.",
        public_evidence="task asks for last digit; public positive example is 123→3",
        source_locator="evaluation_source:return n % 10",
    ),
    "31213b4e7d52c7e2991c5a31ed8d7d24e07a16b756a5bb326348e488aba8d5e9": _decision(
        primary="L5",
        mechanisms=_mech(
            ("wrong_aggregation_operator", "CONFIRMED", "uses total ^= pair xor while task requires sum of pair xor values"),
            ("incorrect_pair_domain", "SUPPORTED", "j is additionally window-limited by k rather than plainly all pairs"),
            ("algorithm_reconstruction_required", "CONFIRMED", "aggregation and pair enumeration semantics must be rebuilt"),
        ),
        chain=["entry point present", "enumerates a k-limited pair window", "XOR-accumulates pair XOR values instead of summing", "public expected 47 not represented", "primary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Repair changes core aggregation and possibly pair enumeration algorithms.",
        public_evidence="assert pair_xor_Sum([5,9,7,6],4) == 47",
        source_locator="evaluation_source:total ^= nums[i] ^ nums[j]",
    ),
    "3162f7ce0a2214cadadba6f4903b5961215cda0f2d6eb3ea126a92f69e605640": _decision(
        primary="L2", secondary="L5",
        mechanisms=_mech(
            ("output_schema_mismatch", "CONFIRMED", "returns constant True while public contract requires integer 27"),
            ("incorrect_formula", "CONFIRMED", "computed (5n²-3n)/2 gives 18 at n=3, not decagonal 4n²-3n=27"),
            ("algorithm_reconstruction_required", "CONFIRMED", "returning val would still preserve the wrong polygonal formula"),
        ),
        chain=["entry point present", "wrong polygonal formula computes 18 for n=3", "constant boolean returned instead of integer", "primary=L2; secondary=L5", "healer=abstain"],
        confidence="HIGH", healer="abstain",
        eligibility_reason="Changing only return True to return val would still return 18; repair requires formula reconstruction as well as schema correction.",
        public_evidence="task requests nth decagonal number and assert is_num_decagonal(3) == 27",
        source_locator="evaluation_source:val=(5*n**2-3*n)//2 followed by return True",
    ),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    prep = {row["program_id"]: row for row in _read_csv(repo, PREPARATION)}
    inventory = {row["program_id"]: row for row in _read_csv(repo, INVENTORY)}
    journals = {row["program_id"]: row for row in _read_jsonl(repo, JOURNAL) if row["healer_account"] == "H0"}
    tasks = {row["task_id"]: row for row in _read_jsonl(repo, TASKS)}
    evalplus = {row["program_id"]: row for row in _read_csv(repo, EVALPLUS) if row["healer_account"] == "H0"}
    paired = {row["program_id"]: row for row in _read_csv(repo, PAIRED) if row["prompt_condition"] == "Candidate_B"}

    _require(len(roster) == 20, "Batch02 roster count drift")
    ids = [row["program_id"] for row in roster]
    _require(len(set(ids)) == 20 and set(ids) == set(DECISIONS), "decision/roster closure drift")
    _require(len({row["cell_identity_sha256"] for row in roster}) == 20, "cell identity uniqueness drift")

    roster_rows: list[dict[str, str]] = []
    records: list[dict[str, str]] = []
    for row in roster:
        pid = row["program_id"]
        p, inv, journal, task, ev, pair = prep[pid], inventory[pid], journals[pid], tasks[row["task_id"]], evalplus[pid], paired[pid]
        _require(row["cell_identity_sha256"] == p["cell_identity_sha256"] == inv["cell_id"], f"cell identity drift: {pid}")
        _require(row["source_sha256"] == p["evaluation_source_sha256"] == journal["evaluation_source_sha256"], f"source SHA drift: {pid}")
        for field in ("task_id", "seed", "generation_id"):
            _require(str(row[field]) == str(p[field]) == str(journal[field]) == str(pair[field]), f"{field} drift: {pid}")
        _require(task["entry_point"] in journal["evaluation_source"], f"entry point absent from source: {pid}")
        _require(ev["base_status"] in {"pass", "fail"} and ev["plus_status"] in {"pass", "fail"}, f"existing evaluator status drift: {pid}")

        roster_rows.append({field: row[field] for field in ROSTER_FIELDS})
        decision = DECISIONS[pid]
        citations = ";".join(
            [
                f"{ROSTER.as_posix()}#program_id={pid}",
                f"{JOURNAL.as_posix()}#program_id={pid};healer_account=H0",
                f"{TASKS.as_posix()}#task_id={row['task_id']}",
                f"{EVALPLUS.as_posix()}#program_id={pid};healer_account=H0",
                f"{PREPARATION.as_posix()}#cell_identity_sha256={row['cell_identity_sha256']}",
            ]
        )
        records.append(
            {
                "batch_rank": row["batch_rank"],
                "cell_identity_sha256": row["cell_identity_sha256"],
                "program_id": pid,
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "generation_id": row["generation_id"],
                "condition": row["condition"],
                "review_status": "PROVISIONALLY_ADJUDICATED",
                **decision,
                "evidence_citations": citations,
                "adjudicator_identity": ADJUDICATOR,
                "adjudication_timestamp": ADJUDICATION_TIMESTAMP,
            }
        )

    primary = Counter(row["primary_layer"] for row in records)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in records)
    confidence = Counter(row["confidence"] for row in records)
    outcome = Counter(row["outcome_validity"] for row in records)
    healer = Counter(row["healer_eligibility"] for row in records)
    mechanism = Counter()
    mechanism_strength = Counter()
    for row in records:
        for item in json.loads(row["mechanism_tags_json"]):
            mechanism[item["tag"]] += 1
            mechanism_strength[f"{item['tag']}::{item['strength']}"] += 1
    gaps = [{field: row[field] for field in GAP_FIELDS} for row in records if row["primary_layer"] == "UNRESOLVED"]
    _require(len(gaps) == primary.get("UNRESOLVED", 0), "UNRESOLVED gap closure drift")
    _require(primary == Counter({"UNRESOLVED": 9, "L5": 7, "L2": 3, "L4": 1}), f"primary drift: {primary}")
    _require(healer == Counter({"abstain": 20}), f"healer drift: {healer}")
    _require(confidence == Counter({"LOW": 9, "HIGH": 7, "MEDIUM": 4}), f"confidence drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift: {outcome}")

    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "unique_program_id": len({row["program_id"] for row in records}),
        "unique_cell_identity": len({row["cell_identity_sha256"] for row in records}),
        "unique_source_sha256": len({row["source_sha256"] for row in records}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "mechanism_tag_distribution": dict(sorted(mechanism.items())),
        "mechanism_tag_strength_distribution": dict(sorted(mechanism_strength.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {
            "eligible": healer.get("eligible", 0),
            "conditional": healer.get("conditional", 0),
            "abstain": healer.get("abstain", 0),
        },
        "unresolved_cells": len(gaps),
        "suitable_for_independent_audit": True,
        "no_planning_signal_promoted_directly": True,
    }
    return {"roster": roster_rows, "records": records, "gaps": gaps, "summary": summary}


def _report(summary: dict[str, Any], records: list[dict[str, str]], gaps: list[dict[str, str]]) -> str:
    unresolved = ", ".join(row["program_id"] for row in gaps)
    eligible = ", ".join(row["program_id"] for row in records if row["healer_eligibility"] == "eligible")
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch02 20-cell provisional adjudication v1",
            "", f"**狀態：`{STATUS}`**", "", f"**Verdict：`{VERDICT}`**", "",
            "## 統計", "",
            f"- primary：{summary['primary_layer_distribution']}",
            f"- secondary：{summary['secondary_layer_distribution']}",
            f"- confidence：{summary['confidence_distribution']}",
            f"- outcome：{summary['outcome_validity_distribution']}",
            f"- Healer：{summary['healer_eligibility_distribution']}",
            f"- UNRESOLVED：{summary['unresolved_cells']}", "",
            "## Healer 邊界", "",
            f"- eligible：`{eligible or '(none)'}`",
            "- eligible 不由 planning signal 推定；其餘語意、演算法、證據不足均 abstain。", "",
            "## UNRESOLVED", "", f"`{unresolved}`", "",
            "每格均有 reason、evidence gap 與僅供未來稽核評估的 minimal diagnostic；本輪未執行。", "",
            "## 執行邊界", "",
            "candidate/import/public/hidden/EvalPlus/diagnostics/validation/Healer/model execution 全部為 0。", "",
            "本 provisional v1 適合進入獨立 audit；尚未 audit、freeze 或升格。", "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "adjudication_roster.csv": _csv_bytes(ROSTER_FIELDS, analysis["roster"]),
        "adjudication_records.csv": _csv_bytes(RECORD_FIELDS, analysis["records"]),
        "unresolved_evidence_gaps.csv": _csv_bytes(GAP_FIELDS, analysis["gaps"]),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], analysis["records"], analysis["gaps"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution,
        "start_head": START_HEAD,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "taxonomy_v31_reference": TAXONOMY_REFERENCE,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "evidence_policy": "frozen raw output + public contract + existing results + static derivation only",
        "new_runtime_observations": 0,
        "upstream_modified": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS, "verdict": VERDICT, "start_head": START_HEAD,
        "cells": 20, "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
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
