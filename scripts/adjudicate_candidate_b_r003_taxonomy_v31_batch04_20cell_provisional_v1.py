#!/usr/bin/env python3
"""Static provisional adjudication for the fixed Batch04 20-cell roster.

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
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "AI_ASSISTED_STATIC_PROVISIONAL_ADJUDICATION_NOT_AUDITED"
VERDICT = "READY_FOR_BATCH04_PROVISIONAL_INDEPENDENT_AUDIT"
ADJUDICATOR = "taxonomy_v31_batch04_provisional_v1_static_adjudicator"
TIMESTAMP = "2026-07-22T00:00:00+08:00"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/batch04_roster.csv"
)
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
REMAINING21 = ROSTER.with_name("remaining21_roster.csv")
AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1_independent_audit_v1"
)
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_roster_findings.csv"
ACCOUNTS = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/"
    "manual_evalplus_run_001/evalplus_results.csv"
)
REMAINING101 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv"
)
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    ROSTER_MANIFEST: "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    AUDIT_MANIFEST: "cd11f7da198044968773198cb9e66f057b11fb5285e4a12e1f70c7fb8475f3b7",
    AUDIT_FINDINGS: "4b2bb8b7a8164388658f5f09eada38a029a1f5526d00a6c703dd840bd012265f",
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
MECHANISM_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "primary_layer",
    "mechanism_tag", "strength", "note",
)
CONDITIONAL_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "candidate_rule",
    "minimal_diagnostic", "upgrade_condition", "rejection_condition",
)
GAP_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "unresolved_reason_code",
    "evidence_present", "evidence_missing", "competing_explanations",
    "minimal_future_diagnostic",
)


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
    primary: str,
    observation: str,
    evidence: str,
    reason: str,
    mechanisms: list[tuple[str, str, str]],
    *,
    secondary: str = "",
    confidence: str = "HIGH",
    missing: str = "no evidence gap required for provisional layer closure",
    competing: str = "additional hidden-case defects may coexist but do not displace the public static violation",
    unresolved_code: str = "",
    diagnostic: str = "",
) -> dict[str, Any]:
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "observation": observation,
        "evidence": evidence,
        "missing": missing,
        "competing": competing,
        "reason": reason,
        "mechanisms": mechanisms,
        "unresolved_code": unresolved_code,
        "diagnostic": diagnostic,
    }


def _unresolved(
    observation: str,
    evidence: str,
    missing: str,
    competing: str,
    diagnostic: str,
    extra: list[tuple[str, str, str]] | None = None,
) -> dict[str, Any]:
    mechanisms = [
        ("public_examples_non_discriminating", "CONFIRMED", "preserved public example is satisfied by static derivation"),
        ("plus_failure_not_localized", "CONFIRMED", "existing plus status is fail but its first failing input is not preserved here"),
        ("diagnostic_execution_required", "SUPPORTED", "a new observation would be required to distinguish remaining explanations"),
    ]
    if extra:
        mechanisms.extend(extra)
    return _decision(
        "UNRESOLVED",
        observation,
        evidence,
        "review completed but current static evidence does not close one L0-L5 root layer",
        mechanisms,
        confidence="LOW",
        missing=missing,
        competing=competing,
        unresolved_code="public_example_satisfied_plus_failure_not_localized",
        diagnostic=diagnostic,
    )


DECISIONS = {
    "8406e78362de082453800aa627d56e53b5170bf464a7358ed301f3612aeb1ff3": _decision(
        "L5",
        "formula uses six equilateral faces a^2*(sqrt(3)/4)*6 for a=3, not public ~15.588",
        "public assert area_tetrahedron(3)==15.588457268119894 uniquely matches a^2*sqrt(3); static closed form differs",
        "required entry point and float scalar are present but the geometric formula contradicts the public numeric contract",
        [
            ("incorrect_formula", "CONFIRMED", "six-face scaling yields ~23.383 rather than public ~15.588=a^2*sqrt(3)"),
            ("algorithm_reconstruction_required", "SUPPORTED", "repair requires choosing the intended tetrahedron area formula"),
        ],
    ),
    "866739b5b8f57631f1a69318ccccf5b802b31f0fc38b57e6a75e358d9ef9a9c2": _decision(
        "L5",
        "first capital at i==0 inserts a leading space, statically yielding ' Python' not 'Python'",
        "public assert capital_words_spaces(\"Python\")=='Python' is directly falsified by the first-iteration space rule",
        "capital-word boundary logic inserts a space before the initial capital word",
        [
            ("wrong_boundary_condition", "CONFIRMED", "i==0 capital is treated as a word boundary that receives a leading space"),
            ("capital_boundary_detection_error", "CONFIRMED", "single-word capitalized input is spaced incorrectly"),
        ],
    ),
    "8be467a87d48ada42b452f75670c330df1e5f4a334816d133ece971a93245e51": _unresolved(
        "XOR middle-bit mask preserves MSB/LSB and statically yields 9->15",
        "required entry point and scalar shape present; public example and base tests pass; plus fails",
        "first failing plus integer and signed/zero bit-width convention",
        "failure may concern signed inputs, small values, or another unstated bit representation rule",
        "capture the first existing failing plus integer and return without applying a repair",
    ),
    "8c4a86b4c5c2dc7f2ec53338538b0859c10c4920752c5d3fe775a0332148cd44": _decision(
        "L5",
        "formula a^2*(sqrt(3)/4+sqrt(6)) for a=3 yields ~25.943, not public ~15.588",
        "public float assert uniquely falsifies the static closed-form expression",
        "extraneous sqrt(6) term changes the tetrahedron-area semantics relative to the public numeric contract",
        [
            ("incorrect_formula", "CONFIRMED", "includes sqrt(6) term so a=3 yields ~25.943 rather than ~15.588=a^2*sqrt(3)"),
            ("algorithm_reconstruction_required", "SUPPORTED", "geometric formula reconstruction is required"),
        ],
    ),
    "8ef0641f265717551638f61f1daf725c93f863842cab36e6f422970e23d7f298": _unresolved(
        "contiguous-window comparison returns False for the sole public example",
        "parseable required entry point; public example and base tests pass; plus fails; source_sha256 shared with rank 12",
        "whether sublist means contiguous slice or ordered/noncontiguous containment, and the first failing plus case",
        "contiguous and noncontiguous interpretations remain compatible with the public False example",
        "capture the first existing failing plus lists and return without applying a repair",
        [("sublist_semantics_ambiguous", "SUSPECTED", "public contract does not discriminate contiguous from noncontiguous semantics")],
    ),
    "8f2e043d3ef8a94ec9db97c703ff778ec9a46582d481a979e5cf806434f470fc": _decision(
        "L5",
        "for public n=5 (odd) returns merged[n//2]=12 instead of average of middle pair 16.0",
        "merged=[1,2,12,13,15,17,26,30,38,45]; public assert requires (15+17)/2=16.0",
        "odd-n branch selects a single interior element although two equal-length sorted lists always have even combined length",
        [
            ("incorrect_formula", "CONFIRMED", "n%2!=0 path uses merged[n//2] rather than (merged[n-1]+merged[n])/2"),
            ("algorithmic_error", "CONFIRMED", "median of two same-size sorted lists is mis-indexed on the public example"),
        ],
    ),
    "988e14a3191e7bc858a23195cd2356a37acd3408f288a68fe062cc838aa4d738": _unresolved(
        "split-and-reorder statically yields '02-01-2026' for public '2026-01-02'",
        "required entry point and string reshape present; public example and base tests pass; plus fails",
        "first failing plus date string and policy for malformed/non-yyyy-mm-dd inputs",
        "failure may concern malformed separators, component width, or another evaluator-domain convention",
        "capture the first existing failing plus date string and return without applying a repair",
    ),
    "9ad0aec70e9293ceb0bd48dd62d61cd09be24b487b3158726bf9b037a4c72d20": _decision(
        "L5",
        "pair XOR values are aggregated with ^= yielding 13, not the required sum 47",
        "public assert pair_xor_Sum([5,9,7,6],4)==47; all six pair XORs sum to 47 while source XOR-folds them to 13",
        "pair-XOR aggregation implements XOR-fold rather than summation required by the public contract",
        [
            ("algorithmic_error", "CONFIRMED", "pair XOR results are XOR-folded instead of summed"),
            ("wrong_parameter_semantics", "SUPPORTED", "k is used as a sliding window bound rather than an explicit pair-domain size"),
            ("incorrect_pair_domain", "SUSPECTED", "window restriction may omit required pairs on non-public inputs"),
        ],
    ),
    "9cecbec0d7bbabf0c9111cd5a25e8a8bf100bd34a82e191b68129e9bbef557a3": _unresolved(
        "sorted unique DP divisibility chain statically attains size 4 on the public list",
        "required entry point and int scalar present; public example and base tests pass; plus fails",
        "first failing plus list and intended policy for zeros/negatives/duplicates",
        "an undisclosed edge-case, divisibility convention, or evaluator-domain rule remains possible",
        "capture the first existing failing plus list and return without applying a repair",
    ),
    "9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba": _decision(
        "L5",
        "Counter filter excludes every repeated 1 and statically sums 2+3+4+5+6=20, not public 21",
        "public assertion requires each distinct value once, including repeated value 1",
        "candidate implements occurrence-count-one rather than deduplicated-value semantics",
        [
            ("dedupe_instead_of_unique_occurrence", "CONFIRMED", "repeated values are omitted rather than counted once"),
            ("semantic_goal_drift", "CONFIRMED", "non-repeated was interpreted as frequency exactly one"),
        ],
    ),
    "a63f9d97cba10e46cb00cd363e9f3de9cec93661af43258ddfd7f9deda1dae91": _unresolved(
        "loop sums (2i)^2 for i=1..n and statically yields 20 at n=2",
        "required entry point and scalar return are present; public n=2 example is satisfied; base=pass/plus=fail",
        "first failing plus input and the applicable non-positive/large-n boundary",
        "an undisclosed boundary, resource case, or evaluator-domain convention remains possible",
        "capture the first existing failing plus input and return/exception without applying a repair",
    ),
    "a6a4398773853bd405ef18d191a8182c599b3467aabc2b417f070a11fc93044b": _unresolved(
        "contiguous-window comparison returns False for the sole public example",
        "parseable required entry point; public example and base tests pass; plus fails; identical source_sha256 to rank 5",
        "whether sublist means contiguous slice or ordered/noncontiguous containment, and the first failing plus case",
        "contiguous and noncontiguous interpretations remain compatible with the public False example",
        "capture the first existing failing plus lists and return without applying a repair",
        [("sublist_semantics_ambiguous", "SUSPECTED", "public text does not discriminate sublist semantics")],
    ),
    "a6b26635210ce9147ed93f1b67d5770d814ac10f06a4819332de022287d457a8": _decision(
        "L5",
        "binary search advances only on arr[mid] < value and therefore computes left insertion at equality",
        "task explicitly requests the right insertion point; the public greater-than-all case is nondiscriminating",
        "strict comparison implements lower-bound rather than right-bound semantics",
        [
            ("wrong_boundary_condition", "CONFIRMED", "equality is routed left"),
            ("duplicate_value_semantics", "CONFIRMED", "equal runs are not skipped to the right"),
        ],
    ),
    "a6f3b32f10e03fb5ebe7025f863b1bff932bf5459b3d9aae070a3497d37ed62a": _decision(
        "L4",
        "while left < right body is only comments/pass so left/right never move on public [1,1,2,2,3]",
        "static control-flow shows nontermination for any len>1; prep records WorkerProcessExit/not_run consistent with kill-on-timeout",
        "parseable required entry point exists but the search loop never updates bounds, so execution cannot complete",
        [
            ("nontermination", "CONFIRMED", "binary-search loop body is pass and never advances left/right"),
            ("control_flow_failure", "CONFIRMED", "intended pair-index updates are absent"),
            ("algorithm_reconstruction_required", "SUPPORTED", "unique-element search algorithm was not implemented"),
        ],
        secondary="L5",
    ),
    "b63e3c913c74a74a79cca769520da9b92a2d6bcb640882d2df8a189812e67ef6": _unresolved(
        "numeric filter then min statically yields 2 on the public heterogeneous list",
        "required entry point present; public example and base tests pass; plus fails",
        "first failing plus list and policy for bools/empty-numeric/non-real numerics",
        "bool-as-int inclusion, empty numeric min, or another heterogeneous ordering rule remain possible",
        "capture the first existing failing plus list and return/exception without applying a repair",
    ),
    "b677e7ee4faca0108c29317a74d6acd3c5f699de647fe062c61ad5efc6dbb2e5": _decision(
        "L5",
        "space-insertion branch appends only ' ' and omits the current capital, e.g. HelloWorld->'Hello orld'",
        "task requires spaces between capital-started words; source drops the boundary character whenever a space is inserted",
        "string assembly omits capitals on word splits, contradicting the capital-word spacing contract",
        [
            ("control_flow_failure", "CONFIRMED", "space branch does not also append the current character"),
            ("capital_boundary_detection_error", "CONFIRMED", "camel-case capitals are deleted rather than spaced"),
            ("semantic_goal_drift", "SUPPORTED", "spacing transformation destroys letters instead of separating words"),
        ],
    ),
    "b977ada54f0a13704e4e0f3507761d860242d6b745c9d9f44e0750c972d28e2c": _unresolved(
        "repeated division produces public 8->'1000' with no leading zeros",
        "required entry point and string shape present; public example and base tests pass; plus fails",
        "intended domain for negative/non-integer inputs and first failing plus behavior",
        "signed input policy, zero formatting already handled, or another evaluator-domain rule remains possible",
        "capture the first existing failing plus integer and return without applying a repair",
    ),
    "ba78506a3e44c95de2ee2e90bcfbebfc58b91703227e9ec65aaf922d046c31cd": _decision(
        "L5",
        "Counter treats (3,1)!=(1,3) while public expects sorted-key {(1,3):2,(2,5):2,(3,6):1}",
        "public assert merges reversed pairs into order-normalized keys; dict(Counter(lst)) keeps order-sensitive keys",
        "occurrence mapping omits required tuple canonicalization before counting",
        [
            ("order_sensitive_counter", "CONFIRMED", "reversed pairs remain distinct keys contrary to public mapping"),
            ("semantic_goal_drift", "CONFIRMED", "raw Counter replaces order-insensitive unique-tuple counting"),
            ("algorithm_reconstruction_required", "SUPPORTED", "canonicalize-then-count repair is required"),
        ],
    ),
    "be02f058d52c050cf5574665a7ed4d56e20d6afde2ef686be3c6c59cc8878352": _decision(
        "L5",
        "for public n=5 the tiny loop tests only i=1 and returns False although 5=3^2-2^2",
        "public assertion requires dif_Square(5)==True; source range stops at int((n//2)**0.5) and never reaches outer square 3",
        "search bound and difference construction omit a valid square-difference representation",
        [
            ("algorithmic_error", "CONFIRMED", "search does not cover the required square pair for n=5"),
            ("incorrect_search_bound", "CONFIRMED", "outer square 3 is excluded by int((n//2)**0.5)"),
        ],
    ),
    "bf89a824ca07792fc9d14d89cd30b82b2d94122c012226a5b6d6519f19d60cfe": _unresolved(
        "prefixing remainders produces public 8->'1000' with no leading zeros",
        "required entry point and string shape present; public example and base tests pass; plus fails",
        "intended signed/input domain and first failing plus behavior",
        "signed input policy or another evaluator-domain rule remains possible",
        "capture the first existing failing plus integer and return without applying a repair",
    ),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    remaining21 = _read_csv(repo, REMAINING21)
    audit_manifest = json.loads((repo / AUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(
        audit_manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_ADJUDICATION",
        "roster audit verdict drift",
    )
    _require(len(roster) == 20 and set(DECISIONS) == {r["program_id"] for r in roster}, "decision/roster closure drift")
    _require(len(remaining21) == 21, "remaining21 must stay 21 and untouched as an upstream pin")
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
        citations = ";".join(
            [
                f"{ROSTER.as_posix()}#program_id={pid}",
                f"{ACCOUNTS.as_posix()}#program_id={pid};healer_account=H0",
                f"{TASKS.as_posix()}#task_id={roster_row['task_id']}",
                f"{EVALPLUS.as_posix()}#program_id={pid};healer_account=H0",
                f"{PREPARATION.as_posix()}#cell_identity_sha256={roster_row['cell_identity_sha256']}",
                f"{TAXONOMY.as_posix()}#sections=4,5,8,9,10,11,12",
            ]
        )
        if d["primary"] == "UNRESOLVED":
            chain = (
                "parseable required entry point → public example satisfied statically → "
                "existing base pass/plus fail not localized → primary=UNRESOLVED → healer=abstain"
            )
            healer_reason = "Root layer and unique safe repair are not closed."
        elif d["primary"] == "L4":
            chain = (
                "parseable required entry point → nonterminating control flow → "
                "primary=L4; secondary=L5 → algorithm reconstruction required → healer=abstain"
            )
            healer_reason = (
                "Repair requires implementing the missing search algorithm and is not a unique "
                "local oracle-independent transformation."
            )
        else:
            chain = (
                "parseable required entry point and output shape → public contract statically "
                "contradicted → primary=L5 → algorithm/semantics repair required → healer=abstain"
            )
            healer_reason = (
                "Repair changes task semantics or algorithm and is not a unique local "
                "oracle-independent transformation."
            )
        record = {
            "batch_rank": roster_row["selection_rank"],
            "cell_identity_sha256": roster_row["cell_identity_sha256"],
            "program_id": pid,
            "source_sha256": roster_row["source_sha256"],
            "task_id": roster_row["task_id"],
            "seed": roster_row["seed"],
            "generation_id": roster_row["generation_id"],
            "condition": roster_row["condition"],
            "review_status": "PROVISIONALLY_ADJUDICATED",
            "classification_status": "ADJUDICATED",
            "primary_layer": d["primary"],
            "secondary_layer": d["secondary"],
            "mechanism_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "failure_chain": chain,
            "confidence": d["confidence"],
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "healer_eligibility": "abstain",
            "eligibility_reason": healer_reason,
            "eligibility_rule": "",
            "rejection_condition": "semantic_or_evidence_closure_not_safe_for_deterministic_healer",
            "unresolved_reason_code": d["unresolved_code"],
            "evidence_present": d["evidence"],
            "evidence_missing": d["missing"],
            "competing_explanations": d["competing"],
            "reason": d["reason"],
            "minimal_future_diagnostic": d["diagnostic"],
            "public_evidence": task["prompt"].strip().replace("\n", " "),
            "evidence_citations": citations,
            "source_structure_locator": d["observation"],
            "adjudicator_identity": ADJUDICATOR,
            "adjudication_timestamp": TIMESTAMP,
            "planning_signal_note": (
                "roster order fixed before adjudication; no planning signal promoted to layer "
                "or Healer disposition"
            ),
        }
        records.append(record)
        evidence_rows.append(
            {
                "batch_rank": record["batch_rank"],
                "program_id": pid,
                "cell_identity_sha256": record["cell_identity_sha256"],
                "task_id": record["task_id"],
                "source_sha256": record["source_sha256"],
                "public_specification": record["public_evidence"],
                "static_source_observation": d["observation"],
                "existing_base_status": ev["base_status"],
                "existing_plus_status": ev["plus_status"],
                "evidence_present": d["evidence"],
                "evidence_missing": d["missing"],
                "competing_explanations": d["competing"],
                "minimal_future_diagnostic": d["diagnostic"],
                "citations": citations,
            }
        )
        for tag, strength, note in d["mechanisms"]:
            mechanisms.append(
                {
                    "batch_rank": record["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": record["cell_identity_sha256"],
                    "primary_layer": d["primary"],
                    "mechanism_tag": tag,
                    "strength": strength,
                    "note": note,
                }
            )
        if d["primary"] == "UNRESOLVED":
            gaps.append({field: record[field] for field in GAP_FIELDS})

    _require([r["program_id"] for r in records] == [r["program_id"] for r in roster], "record order drift")
    _require(
        [r["source_sha256"] for r in records] == [r["source_sha256"] for r in roster],
        "source order drift",
    )
    _require(
        len({r["program_id"] for r in records}) == len({r["cell_identity_sha256"] for r in records}) == 20,
        "identity uniqueness drift",
    )
    _require(len({r["source_sha256"] for r in records}) == 19, "unique source drift")
    shared = [r for r in records if r["batch_rank"] in {"5", "12"}]
    _require(
        len({r["source_sha256"] for r in shared}) == 1 and len({r["cell_identity_sha256"] for r in shared}) == 2,
        "legal shared source drift",
    )
    _require(all(r["primary_layer"] in {"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"} for r in records), "primary schema drift")
    _require(all(r["healer_eligibility"] in {"eligible", "conditional", "abstain"} for r in records), "healer schema drift")
    _require(all(r["eligibility_reason"] for r in records), "abstain reason missing")
    _require(
        all(
            r["unresolved_reason_code"] and r["evidence_missing"] and r["minimal_future_diagnostic"]
            for r in records
            if r["primary_layer"] == "UNRESOLVED"
        ),
        "unresolved gap incomplete",
    )

    primary = Counter(r["primary_layer"] for r in records)
    secondary = Counter(r["secondary_layer"] or "empty" for r in records)
    confidence = Counter(r["confidence"] for r in records)
    outcome = Counter(r["outcome_validity"] for r in records)
    healer = Counter(r["healer_eligibility"] for r in records)
    mechanism_counts = Counter(r["mechanism_tag"] for r in mechanisms)
    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": len({r["source_sha256"] for r in records}),
        "legal_shared_source_groups": 1,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {
            "eligible": healer.get("eligible", 0),
            "conditional": healer.get("conditional", 0),
            "abstain": healer.get("abstain", 0),
        },
        "mechanism_tag_distribution": dict(sorted(mechanism_counts.items())),
        "unresolved_cells": len(gaps),
        "conditional_queue_cells": 0,
        "eligible_cells": 0,
        "abstain_cells": healer["abstain"],
        "remaining21_cells_unchanged": 21,
        "new_runtime_observations": 0,
        "upstream_modified": False,
        "batch05_started": False,
    }
    _require(primary == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1}), f"primary distribution drift: {primary}")
    _require(secondary == Counter({"empty": 19, "L5": 1}), f"secondary distribution drift: {secondary}")
    _require(confidence == Counter({"HIGH": 11, "LOW": 9}), f"confidence distribution drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome distribution drift: {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer distribution drift: {healer}")
    return {
        "records": records,
        "evidence": evidence_rows,
        "mechanisms": mechanisms,
        "conditional": [],
        "gaps": gaps,
        "summary": summary,
    }


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch04 provisional adjudication v1",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"- Primary：{summary['primary_layer_distribution']}",
            f"- Secondary：{summary['secondary_layer_distribution']}",
            f"- Confidence：{summary['confidence_distribution']}",
            f"- Outcome：{summary['outcome_validity_distribution']}",
            f"- Healer：{summary['healer_eligibility_distribution']}",
            f"- UNRESOLVED：{summary['unresolved_cells']}",
            f"- conditional queue：{summary['conditional_queue_cells']}",
            "",
            "eligible與conditional候選均為0。所有20格均abstain：L5/L4格需要語意或演算法修正；"
            "UNRESOLVED格的根因與唯一安全修法未閉合。",
            "",
            "ranks 5與12共享source且cell相異，分類一致；remaining21未改動；未開始Batch05。",
            "",
            "本revision僅使用保存的靜態source、公開task specification及既有evaluator metadata；"
            "未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型。",
        ]
    ) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0,
        "candidate_executions": 0,
        "candidate_imports": 0,
        "public_test_executions": 0,
        "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
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
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "roster_audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS],
        "taxonomy_v31_sha256": SOURCE_HASHES[TAXONOMY],
        "remaining21_roster_sha256": SOURCE_HASHES[REMAINING21],
        "evidence_scope": (
            "preserved generated source text, public task specification, "
            "existing evaluator/EvalPlus metadata only"
        ),
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication_audit": True,
        "batch04_frozen": False,
        "batch05_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "cells": 20,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
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
