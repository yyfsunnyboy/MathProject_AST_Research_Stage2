#!/usr/bin/env python3
"""AI-assisted provisional adjudication for remaining121 output/contract-shape 20 cells.

AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW

Uses fixed next_batch_roster only. Does not execute candidates, EvalPlus,
diagnostics, validation, Healer, or models.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
    import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
REVISION_SLUG = OUTPUT_RELATIVE.name
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1.py"
)

PLANNING_DIR = planning_prep.OUTPUT_RELATIVE
NEXT_BATCH_ROSTER = PLANNING_DIR / "next_batch_roster.csv"
NEXT_BATCH_ROSTER_SHA256 = "b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804"
PLANNING_MANIFEST = PLANNING_DIR / "manifest.json"
PLANNING_MANIFEST_SHA256 = "66cb8f366d3820b31715753513ed6b038bd471b85b536c3b6779217b041387ab"

MACHINE_CENSUS_MANIFEST = census_prep.OUTPUT_RELATIVE / "manifest.json"
MACHINE_CENSUS_CSV = census_prep.OUTPUT_RELATIVE / "machine_census.csv"
MACHINE_CENSUS_ROSTER = census_prep.OUTPUT_RELATIVE / "fixed_roster.csv"
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
MACHINE_CENSUS_CSV_SHA256 = "284802c8f1aeff92ad70f65b42c4aa7dabc252da592f8ad62011be71537f8a32"
MACHINE_CENSUS_ROSTER_SHA256 = "6e2c6e243fc6ff01c0b0fc2c6939e99cf7f87ef5f17bdf97206adc62ab9af1a5"

MULTIPLE_SIGNAL_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/manifest.json"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

G2_PROVISIONAL_CSV = planning_prep.G2_PROVISIONAL_CSV
MODULE_EXCEPTION_CSV = planning_prep.MODULE_EXCEPTION_CSV
MULTIPLE_SIGNAL_CSV = planning_prep.MULTIPLE_SIGNAL_CSV

AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1"
)
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_CSV = AUDIT_DIR / "pre_adjudication_adversarial_audit.csv"

TARGET_CELLS = 20
TARGET_UNIQUE_TASKS = 13
TARGET_UNIQUE_SOURCES = 20
TARGET_CLUSTER = "output_or_contract_shape_signal"
VALID_PRIMARY_LAYERS = frozenset({"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"})
VALID_SECONDARY_LAYERS = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
VALID_HEALER = frozenset({"eligible", "conditional", "abstain"})
VALID_CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW"})

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    preparation.TAXONOMY_CODEBOOK: preparation.SOURCE_HASHES[preparation.TAXONOMY_CODEBOOK],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    MACHINE_CENSUS_CSV: MACHINE_CENSUS_CSV_SHA256,
    MACHINE_CENSUS_ROSTER: MACHINE_CENSUS_ROSTER_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    PLANNING_MANIFEST: PLANNING_MANIFEST_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    G2_PROVISIONAL_CSV: planning_prep.G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: planning_prep.MODULE_EXCEPTION_CSV_SHA256,
    MULTIPLE_SIGNAL_CSV: planning_prep.MULTIPLE_SIGNAL_CSV_SHA256,
}

ADJUDICATION_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "seed",
    "cell_identity_sha256",
    "allowed_evidence",
    "observed_machine_signal",
    "primary_layer",
    "secondary_layers",
    "mechanism_tags",
    "failure_chain",
    "outcome_validity",
    "healer_eligibility",
    "abstain_reason",
    "confidence",
    "evidence_citations",
    "adjudication_identity",
    "evidence_summary",
    "adjudication_status",
)

CITATION_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "citation_kind",
    "citation_path",
    "citation_locator",
)

ROSTER_CLOSURE_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "in_fixed_roster",
    "in_processed77",
    "source_sha_verified",
    "primary_layer",
)


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


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _processed77(repo: Path) -> set[str]:
    ids: set[str] = set()
    for roster_path in (G2_PROVISIONAL_CSV, MODULE_EXCEPTION_CSV, MULTIPLE_SIGNAL_CSV):
        ids.update(row["program_id"] for row in _read_csv(repo / roster_path))
    return ids


def _allowed_evidence(program_id: str, task_id: str) -> list[str]:
    return [
        preparation.TASKS.as_posix() + f"#task_id={task_id}",
        preparation.JOURNAL.as_posix() + f"#program_id={program_id};healer_account=H0",
        MACHINE_CENSUS_CSV.as_posix(),
        NEXT_BATCH_ROSTER.as_posix(),
    ]


def _chain(*stages: str) -> list[str]:
    return list(stages)


def _decision(
    *,
    primary: str,
    secondary: list[str],
    mechanisms: list[str],
    failure_chain: list[str],
    confidence: str,
    eligibility: str,
    abstain_reason: str,
    evidence_summary: str,
) -> dict[str, Any]:
    _require(primary in VALID_PRIMARY_LAYERS, f"invalid primary: {primary}")
    _require(all(layer in VALID_SECONDARY_LAYERS for layer in secondary), "invalid secondary")
    _require(primary not in secondary, "primary duplicated in secondary")
    _require(eligibility in VALID_HEALER, f"invalid healer eligibility: {eligibility}")
    _require(confidence in VALID_CONFIDENCE, f"invalid confidence: {confidence}")
    _require(bool(failure_chain), "failure_chain must be non-empty ordered causal chain")
    if primary == "UNRESOLVED":
        _require(eligibility == "abstain", "UNRESOLVED must abstain")
        _require(bool(abstain_reason), "UNRESOLVED requires abstain_reason")
    if eligibility == "abstain":
        _require(bool(abstain_reason), "abstain requires abstain_reason")
    return {
        "primary_layer": primary,
        "secondary_layers": _json(list(secondary)),
        "mechanism_tags": _json(list(mechanisms)),
        "failure_chain": _json(list(failure_chain)),
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "healer_eligibility": eligibility,
        "abstain_reason": abstain_reason,
        "confidence": confidence,
        "evidence_summary": evidence_summary,
    }


# Fixed decisions keyed by program_id (deterministic, no model calls).
DECISIONS: dict[str, dict[str, Any]] = {
    # #1 Mbpp/440 — public module assert present; return-shape alone not root cause.
    "0490b9359595e547cd1f19b993b279e4771e6b010b486895ef005aa327ec6ba5": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public assert for find_adverb_position is embedded and return shape is observed, "
            "but public evidence does not uniquely map failure to L2 vs L5 without hidden tests."
        ),
        evidence_summary=(
            "Completed with tuple/nonempty_sequence. Source uses re.search for *ly adverb and "
            "contains the public assert. Return-shape signal alone cannot prove L2/L5; "
            "hidden EvalPlus failure path not inspectable."
        ),
    ),
    # #2 Mbpp/581 — public arithmetic: code ≈34.63 ≠ 33.
    "1e808b1c61f92345c10814778fbcbd28d5a2234c3503895c07c7e7fd52af0818": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["incorrect_surface_area_formula", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_arithmetic_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Semantic/output incorrectness: square-pyramid formula choice is not a unique "
            "bounded safe edit without reconstructing the intended geometric formula."
        ),
        evidence_summary=(
            "Public assert surface_Area(3,4)==33. Static expansion of code: "
            "slant=sqrt((3/2)^2+4^2)=sqrt(18.25); return 9+6*slant ≠ 33. "
            "Public arithmetic proves semantic/output incorrectness (L5)."
        ),
    ),
    # #3 Mbpp/103 — Eulerian DP; cannot close L4/L5 from public prompt alone.
    "29badcaa34166c620978b4f621aa3856859d296e210f7c7a38561b39849fe9cc": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "complex_dp_without_public_trace"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Eulerian DP body is not uniquely checkable against public assert eulerian_num(3,1)==4 "
            "without evaluating hidden cases; L4 vs L5 not closable from public evidence."
        ),
        evidence_summary=(
            "Completed int/scalar. Entry/arity match. Public prompt only gives one assert; "
            "DP recurrence cannot be publicly certified as the failure layer."
        ),
    ),
    # #4 Mbpp/432 — (min+max)/2 of three sides = 25 ≠ 20.
    "2a852f2b4fbd540de726aa6c79682744adf89211081a0bad86db8be05dca8d08": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["incorrect_trapezium_median_formula", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_arithmetic_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Semantic formula repair is not uniquely constrained: which two of three sides "
            "are the parallel bases is not specified by public prompt alone."
        ),
        evidence_summary=(
            "Public assert median_trapezium(15,25,35)==20. Code sorts sides and returns "
            "(min+max)/2 = (15+35)/2 = 25 ≠ 20. Public arithmetic proves L5."
        ),
    ),
    # #5 Mbpp/572 — unique-occurrence filter vs dedupe.
    "3a45ffef6c26dddc43c38babe1756cb674e65b3b7768249922aeea330cee1070": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["dedupe_instead_of_unique_occurrence", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_semantic_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Semantic/output incorrectness default abstain; although public example implies "
            "keep-only-unique-count elements, repair still requires algorithm rewrite."
        ),
        evidence_summary=(
            "Public assert two_unique_nums([1,2,3,2,3,4,5])==[1,4,5]. Code keeps first "
            "occurrence of every value (dedupe) → [1,2,3,4,5], which mismatches the "
            "public example requiring elements that appear exactly once."
        ),
    ),
    # #6 Mbpp/138 — public assert True; cannot close layer.
    "40c33be662bdff3a810ff1d30fdbb10b665c7d1d00a58e010245fba1f4ae091d": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public assert is_Sum_Of_Powers_Of_Two(10)==True is satisfied by static bit-loop "
            "trace; hidden failure cause not inspectable."
        ),
        evidence_summary=(
            "Completed bool/scalar. Entry present. Only one public True example; "
            "return-shape signal does not uniquely prove L2/L5."
        ),
    ),
    # #7 Mbpp/11 — public example "hello"/"l" → "heo" matches remove first+last.
    "4646a249b7fe3dcaeb8cbcfc0ce9f76bcbcdda03f74c6dd983397d8a5f0f3ec7": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public assert remove_Occ('hello','l')=='heo' matches first/last removal logic; "
            "cannot attribute unresolved failure to a taxonomy layer without hidden tests."
        ),
        evidence_summary=(
            "Completed str/mixed. Public contract example is consistent with source behavior; "
            "return-shape alone is not root cause."
        ),
    ),
    # #8 Mbpp/16 — public assert True; cannot close.
    "4e8e311abbfa06697db20b02b810ed3b5556d46c5c19274bd64ba2b9a2766f73": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public assert text_lowercase_underscore('aab_cbbbc')==(True) matches split/islower "
            "logic; hidden failure path not inspectable."
        ),
        evidence_summary=(
            "Completed bool/scalar. Entry/arity OK. Public example does not expose a closable "
            "L2/L5 root cause."
        ),
    ),
    # #9 Mbpp/103 seed22 — another Eulerian DP source; unresolved.
    "5c195ebd425a3dd8b06b2403e00a815ad2538d6c9f54119448a585dac8c88715": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "complex_dp_without_public_trace"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Distinct source for Mbpp/103; public prompt still insufficient to close L4 vs L5 "
            "for Eulerian recurrence."
        ),
        evidence_summary=(
            "Distinct source-level evidence unit (seed=22). Completed int/scalar. "
            "Public evidence does not uniquely prove semantic mismatch."
        ),
    ),
    # #10 Mbpp/603 — yield generator vs public list contract.
    "5e7b11eaaa932e83d0b496103cbe88e706d6b4edcbf5190b1395b7cdb7bc26a9": _decision(
        primary="L2",
        secondary=[],
        mechanisms=["generator_instead_of_list", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "generator_object_returned",
            "public_list_contract_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Converting yield→list is not a unique safe fix: ludic sieving algorithm body "
            "(del nums[:idx+step]) still requires algorithm rebuild."
        ),
        evidence_summary=(
            "Public assert get_ludic(10)==[1,2,3,5,7] requires a list. Source uses `yield`, "
            "so the entry point returns a generator object. Static yield + public list "
            "assert is a closable output-contract (L2) violation; return_type_bucket=other "
            "is supporting signal only."
        ),
    ),
    # #11 Mbpp/119 — binary search ends returning None ≠ 3.
    "6f38684ffaadcde4e2165ae9043a98afe30f777b49c3752269cec0e18417fdff": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["binary_search_missing_final_return", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_semantic_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Semantic/output incorrectness default abstain; public trace proves None≠3 but "
            "a single return-arr[left] edit is not proven unique across all pair layouts."
        ),
        evidence_summary=(
            "Public assert search([1,1,2,2,3])==3. Static control-flow: mid pairs force "
            "left→4==right, loop exits, function returns None. Public example proves "
            "semantic/output incorrectness (L5)."
        ),
    ),
    # #12 Mbpp/237 — order-insensitive tuple counting.
    "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["order_sensitive_counter", "return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_semantic_mismatch",
        ),
        confidence="HIGH",
        eligibility="conditional",
        abstain_reason=(
            "Public example uniquely implies order-insensitive counting with sorted-key form, "
            "but tuple arity>2 and key canonicalization are not fully constrained → conditional."
        ),
        evidence_summary=(
            "Public assert treats (3,1)/(1,3) and (2,5)/(5,2) as identical keys. "
            "Counter(lst) treats them as distinct. Public example proves L5. "
            "Healer eligibility conditional (bounded normalize-key repair plausible but not unique)."
        ),
    ),
    # #13 Mbpp/118 — public assert matches split().
    "794b418dfbb6d97af9e2062fff770e1a4c2f85140a9b42ec6cc6b6fa589eb937": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public assert string_to_list('python programming') matches s.split(); "
            "hidden failure cause not inspectable from public evidence."
        ),
        evidence_summary=(
            "Completed list/mixed. Source is s.split() plus packaging assert matching prompt. "
            "No closable L2/L5 root cause from allowed evidence."
        ),
    ),
    # #14 Mbpp/581 seed11 — lateral_area uses one face only; ≠33.
    "a2dc45257f6a71f7d31a1b9dd5c14e57129eefbe2d06e48dfa1ebb6199e88be3": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["incorrect_surface_area_formula", "return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_arithmetic_mismatch",
        ),
        confidence="HIGH",
        eligibility="abstain",
        abstain_reason=(
            "Semantic formula repair for square-pyramid surface area is not a unique bounded "
            "safe edit; distinct source from seed=33 but same L5 family."
        ),
        evidence_summary=(
            "Distinct source for Mbpp/581. Public assert surface_Area(3,4)==33. "
            "Code returns base^2 + base*slant ≈ 9+12.82 ≠ 33. Public arithmetic proves L5."
        ),
    ),
    # #15 Mbpp/138 seed55 — public True; unresolved.
    "a4fb31fb0a9e1c4080e4c75cc53a842c29cfd030ea1cd5ba7d6f29a34bd605ee": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Distinct source for Mbpp/138; public assert True does not expose closable root cause."
        ),
        evidence_summary=(
            "Distinct source-level evidence (seed=55). Completed bool/scalar with packaging assert. "
            "Public evidence insufficient to choose L2/L5."
        ),
    ),
    # #16 Mbpp/103 seed55 — mixed return; unresolved.
    "ad4c43603b9f8b7f5b6a3a777940c6c799881fc2fb043e193e3237bcaf3af7f9": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "complex_dp_without_public_trace"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Conditional audit cell: mixed return_type observed but L4 vs L5 for Eulerian DP "
            "cannot be closed from public prompt alone."
        ),
        evidence_summary=(
            "Distinct source for Mbpp/103 (seed=55). float DP table with int cast; "
            "return_type_bucket=mixed is a signal only. No public arithmetic closure."
        ),
    ),
    # #17 Mbpp/237 seed22 — same L5 family, distinct source.
    "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea": _decision(
        primary="L5",
        secondary=[],
        mechanisms=["order_sensitive_counter", "return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_assert_semantic_mismatch",
        ),
        confidence="HIGH",
        eligibility="conditional",
        abstain_reason=(
            "Same order-insensitive counting requirement as sibling source; healer conditional "
            "because canonical key form is not uniquely fixed beyond public 2-tuples."
        ),
        evidence_summary=(
            "Distinct source for Mbpp/237. Counter without order normalization mismatches "
            "public assert keys {(1,3):2,(2,5):2,(3,6):1}. Embedded packaging assert uses "
            "order-sensitive expected dict and does not override the public prompt contract."
        ),
    ),
    # #18 Mbpp/473 — public intersection likely matched; unresolved.
    "df59c7d238b574cc10029a2d5c026996fa8af2e08ecc1c9af6c527261d8dc344": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Public order-insensitive intersection example is not shown to fail under static "
            "normalize(min,max) logic; cannot close L2/L5 without hidden tests."
        ),
        evidence_summary=(
            "Completed set/mixed. Entry/arity match with set[tuple] annotation. "
            "Return-shape signal alone is not root cause."
        ),
    ),
    # #19 Mbpp/473 seed33 — distinct source; unresolved.
    "e46a657fce3ecde2ac8078af376204deab08196894a3a0db8c3029e317c0a95c": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed", "packaging_or_scaffold_residue"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Distinct source for Mbpp/473; packaging assert expects the public set and does not "
            "expose a closable taxonomy root cause from allowed evidence."
        ),
        evidence_summary=(
            "Distinct source-level evidence (seed=33). frozenset normalize + sorted tuple "
            "result; public example not shown to fail statically."
        ),
    ),
    # #20 Mbpp/11 seed44 — distinct source; unresolved.
    "f14d52366f2dcbb7a33abeeac05c19a43cb0fccd515244e688d7a3ee885a8b34": _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["return_shape_observed"],
        failure_chain=_chain(
            "module_loaded",
            "entry_point_invoked",
            "returned_value_observed",
            "public_root_cause_unresolved",
        ),
        confidence="LOW",
        eligibility="abstain",
        abstain_reason=(
            "Distinct source for Mbpp/11; public example matches first/last removal; "
            "hidden failure not inspectable."
        ),
        evidence_summary=(
            "Distinct source-level evidence (seed=44). Same public-contract consistency as "
            "sibling remove_Occ source; UNRESOLVED."
        ),
    ),
}


def _load_fixed_roster(repo: Path) -> list[dict[str, str]]:
    roster = _read_csv(repo / NEXT_BATCH_ROSTER)
    _require(len(roster) == TARGET_CELLS, f"roster size drift: {len(roster)}")
    _require(
        _sha((repo / NEXT_BATCH_ROSTER).read_bytes()) == NEXT_BATCH_ROSTER_SHA256,
        "next_batch_roster sha drift",
    )
    program_ids = [row["program_id"] for row in roster]
    _require(len(set(program_ids)) == TARGET_CELLS, "program_id uniqueness drift")
    _require(
        len({row["evaluation_source_sha256"] for row in roster}) == TARGET_UNIQUE_SOURCES,
        "source uniqueness drift",
    )
    _require(len({row["task_id"] for row in roster}) == TARGET_UNIQUE_TASKS, "task uniqueness drift")
    _require(all(row["condition"] == "Candidate_B/H0" for row in roster), "condition drift")
    _require(all(row["work_cluster"] == TARGET_CLUSTER for row in roster), "cluster drift")
    processed = _processed77(repo)
    _require(len(processed) == 77, "processed77 size drift")
    _require(not (set(program_ids) & processed), "processed77 intersection must be empty")
    _require(set(DECISIONS) == set(program_ids), "DECISIONS keys must equal fixed roster")
    return roster


def build_rows(repo: Path = REPO_ROOT) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    verify_sources(repo)
    roster = _load_fixed_roster(repo)
    census = {row["program_id"]: row for row in _read_csv(repo / MACHINE_CENSUS_CSV)}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    processed = _processed77(repo)
    adjudication: list[dict[str, str]] = []
    citations: list[dict[str, str]] = []
    closure: list[dict[str, str]] = []

    for row in roster:
        program_id = row["program_id"]
        task_id = row["task_id"]
        source_sha = row["evaluation_source_sha256"]
        journal = journals[program_id]
        source = journal["evaluation_source"]
        _require(_sha(source.encode("utf-8")) == source_sha, f"source sha mismatch: {program_id}")
        # AST parse only — no execution.
        ast.parse(source)
        census_row = census[program_id]
        _require(census_row["diagnostic_phase"] == "completed", f"phase drift: {program_id}")
        _require(census_row["termination"] == "returned", f"termination drift: {program_id}")
        decision = DECISIONS[program_id]
        allowed = _allowed_evidence(program_id, task_id)
        identity = f"{program_id}:{source_sha}:{REVISION_SLUG}"
        evidence_citations = [
            {
                "kind": "public_prompt",
                "path": preparation.TASKS.as_posix(),
                "locator": f"task_id={task_id}",
            },
            {
                "kind": "candidate_source",
                "path": preparation.JOURNAL.as_posix(),
                "locator": f"program_id={program_id};healer_account=H0;sha256={source_sha}",
            },
            {
                "kind": "machine_census",
                "path": MACHINE_CENSUS_CSV.as_posix(),
                "locator": (
                    f"program_id={program_id};phase=completed;"
                    f"return_type={row['return_type_bucket']};"
                    f"return_shape={row['return_shape_bucket']}"
                ),
            },
            {
                "kind": "fixed_roster",
                "path": NEXT_BATCH_ROSTER.as_posix(),
                "locator": f"batch_rank={row['batch_rank']}",
            },
        ]
        adjudication.append(
            {
                "program_id": program_id,
                "task_id": task_id,
                "source_sha256": source_sha,
                "seed": row["seed"],
                "cell_identity_sha256": row["cell_identity_sha256"],
                "allowed_evidence": _json(allowed),
                "observed_machine_signal": TARGET_CLUSTER,
                "primary_layer": decision["primary_layer"],
                "secondary_layers": decision["secondary_layers"],
                "mechanism_tags": decision["mechanism_tags"],
                "failure_chain": decision["failure_chain"],
                "outcome_validity": decision["outcome_validity"],
                "healer_eligibility": decision["healer_eligibility"],
                "abstain_reason": decision["abstain_reason"],
                "confidence": decision["confidence"],
                "evidence_citations": _json(evidence_citations),
                "adjudication_identity": identity,
                "evidence_summary": decision["evidence_summary"],
                "adjudication_status": STATUS,
            }
        )
        for cite in evidence_citations:
            citations.append(
                {
                    "program_id": program_id,
                    "task_id": task_id,
                    "source_sha256": source_sha,
                    "citation_kind": cite["kind"],
                    "citation_path": cite["path"],
                    "citation_locator": cite["locator"],
                }
            )
        closure.append(
            {
                "program_id": program_id,
                "task_id": task_id,
                "source_sha256": source_sha,
                "in_fixed_roster": "true",
                "in_processed77": str(program_id in processed).lower(),
                "source_sha_verified": "true",
                "primary_layer": decision["primary_layer"],
            }
        )

    _require(len(adjudication) == TARGET_CELLS, "adjudication row count drift")
    _require(all(row["in_processed77"] == "false" for row in closure), "closure processed intersection")
    return adjudication, citations, closure


def _summary(adjudication: list[dict[str, str]]) -> dict[str, Any]:
    primary = Counter(row["primary_layer"] for row in adjudication)
    secondary: Counter[str] = Counter()
    mechanisms: Counter[str] = Counter()
    for row in adjudication:
        for layer in json.loads(row["secondary_layers"]):
            secondary[layer] += 1
        for tag in json.loads(row["mechanism_tags"]):
            mechanisms[tag] += 1
    outcome = Counter(row["outcome_validity"] for row in adjudication)
    healer = Counter(row["healer_eligibility"] for row in adjudication)
    confidence = Counter(row["confidence"] for row in adjudication)
    return {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in adjudication}),
        "unique_source_sha256": len({row["source_sha256"] for row in adjudication}),
        "unique_task_id": len({row["task_id"] for row in adjudication}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "mechanism_tag_distribution": dict(sorted(mechanisms.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "unresolved_cells": primary.get("UNRESOLVED", 0),
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "note": (
            "20 cells are 20 source-level evidence units across 13 tasks; "
            "do not describe as 20 independent tasks."
        ),
    }


def _summary_zh(summary: dict[str, Any]) -> str:
    lines = [
        "# AI-assisted provisional adjudication summary（output/contract-shape 20-cell）",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "本 revision **不是** ground truth、formal human review 或 Healer 驗證。",
        "",
        "## 母體",
        "",
        f"- cells={summary['cells']}",
        f"- unique program_id={summary['unique_program_id']}",
        f"- unique source_sha256={summary['unique_source_sha256']}",
        f"- unique task_id={summary['unique_task_id']}",
        f"- {summary['note']}",
        "",
        "## Primary layer",
        "",
        "| Layer | Cells |",
        "|---|---:|",
    ]
    for key, value in summary["primary_layer_distribution"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            f"- UNRESOLVED={summary['unresolved_cells']}",
            "",
            "## Secondary layer",
            "",
            "| Layer | Mentions |",
            "|---|---:|",
        ]
    )
    if summary["secondary_layer_distribution"]:
        for key, value in summary["secondary_layer_distribution"].items():
            lines.append(f"| `{key}` | {value} |")
    else:
        lines.append("| _(none)_ | 0 |")
    lines.extend(
        [
            "",
            "## Mechanism tags",
            "",
            "| Tag | Mentions |",
            "|---|---:|",
        ]
    )
    for key, value in summary["mechanism_tag_distribution"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Outcome validity / Healer / Confidence",
            "",
            f"- outcome_validity：{summary['outcome_validity_distribution']}",
            f"- healer_eligibility：{summary['healer_eligibility_distribution']}",
            f"- confidence：{summary['confidence_distribution']}",
            "",
            "## 5 格 pre-audit conditional 對象處理",
            "",
            "- Mbpp/603：`yield` vs public list → **L2**（contract），healer abstain",
            "- Mbpp/119：public 追蹤回傳 None≠3 → **L5**，healer abstain",
            "- Mbpp/237×2：order-insensitive Counter mismatch → **L5**，healer conditional",
            "- Mbpp/103 seed55：mixed return / DP → **UNRESOLVED**，abstain",
            "",
            "## 邊界",
            "",
            "- 未執行 candidate / EvalPlus / diagnostics / validation / Healer / model",
            "- 未查看 hidden expected/actual 或 traceback",
            "- 適合作為 post-adjudication adversarial audit 輸入；**尚未凍結**",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    adjudication, citations, closure = build_rows(repo)
    summary = _summary(adjudication)
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
    }
    provenance = {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "start_head": START_HEAD,
        "target_cells": TARGET_CELLS,
        "unique_task_id": TARGET_UNIQUE_TASKS,
        "unique_source_sha256": TARGET_UNIQUE_SOURCES,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "multiple_signal_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
        "planning_manifest_sha256": PLANNING_MANIFEST_SHA256,
        "formal_human_review": False,
        "ground_truth": False,
        "healer_executed": False,
        "frozen": False,
        "hidden_expected_actual_used": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "source_hashes_verified": len(SOURCE_HASHES),
        "unresolved_cells": summary["unresolved_cells"],
        "primary_layer_distribution": summary["primary_layer_distribution"],
        "healer_eligibility_distribution": summary["healer_eligibility_distribution"],
    }
    return {
        Path("ai_provisional_adjudication.csv"): _csv_bytes(ADJUDICATION_FIELDS, adjudication),
        Path("adjudication_summary.json"): _json_bytes(summary),
        Path("adjudication_summary_zh.md"): _summary_zh(summary).encode("utf-8"),
        Path("evidence_citation_audit.csv"): _csv_bytes(CITATION_FIELDS, citations),
        Path("roster_closure_audit.csv"): _csv_bytes(ROSTER_CLOSURE_FIELDS, closure),
        Path("execution_counts.json"): _json_bytes(execution_counts),
        Path("provenance.json"): _json_bytes(provenance),
    }


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    summary = json.loads(outputs[Path("adjudication_summary.json")].decode("utf-8"))
    manifest = {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "target_cells": TARGET_CELLS,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "frozen": False,
        "formal_human_review": False,
        "unresolved_cells": summary["unresolved_cells"],
        "primary_layer_distribution": summary["primary_layer_distribution"],
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
    }
    (destination / "manifest.json").write_bytes(_json_bytes(manifest))
    return destination


def main() -> None:
    path = write_outputs()
    print(path)


if __name__ == "__main__":
    main()
