#!/usr/bin/env python3
"""Provisional v1 formal adjudication for remaining101 batch01 (20 cells).

AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW

Fixed next_adjudication_batch_roster only. Does not execute candidates,
EvalPlus, diagnostics, validation, Healer, or models. Does not modify
frozen97 or the remaining101 census revision. Does not freeze/commit/push.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import (
        prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1"
)
START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1.py"
)
ADJUDICATOR_IDENTITY = "taxonomy_v31_batch01_provisional_v1_static_adjudicator"
ADJUDICATION_TIMESTAMP = "2026-07-21T14:41:00+08:00"

CENSUS_DIR = census_prep.OUTPUT_RELATIVE
NEXT_BATCH_ROSTER = CENSUS_DIR / "next_adjudication_batch_roster.csv"
REMAINING101_ROSTER = CENSUS_DIR / "remaining101_roster.csv"
SIGNAL_INVENTORY = CENSUS_DIR / "static_signal_inventory.csv"
CENSUS_MANIFEST = CENSUS_DIR / "manifest.json"
CENSUS_PROVENANCE = CENSUS_DIR / "provenance.json"
CENSUS_EXECUTION = CENSUS_DIR / "execution_counts.json"

NEXT_BATCH_ROSTER_SHA256 = "a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91"
REMAINING101_ROSTER_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"
SIGNAL_INVENTORY_SHA256 = "c3ffa467ce77aca62a205a68a12768f83720bec3b202a65a8f91e4efe916ffed"
CENSUS_MANIFEST_SHA256 = "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd"
CENSUS_PROVENANCE_SHA256 = "74a187c0502861151b9667a1f054699b9d144a91c39a42da7ec17c0800bb6a2a"
CENSUS_EXECUTION_SHA256 = "968c4c4ed0c2e8d5282cae5ca6ecb161393e7e9c5ea254c0459b0a133309d550"
CENSUS_SCRIPT_SHA256 = "e4880ad7a79b74c669a38016f100c6ead9c0e1208be32982d6c98ecc74163cd6"

V31_REFERENCE_FILENAME = census_prep.V31_REFERENCE_FILENAME
V31_REFERENCE_SHA256 = census_prep.V31_REFERENCE_SHA256
V31_REFERENCE_STATUS = census_prep.V31_REFERENCE_STATUS

TARGET_CELLS = 20
TARGET_PRIMARY_BATCH = "B_entry_signature_return_shape_import_candidates"
VALID_PRIMARY = frozenset({"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"})
VALID_SECONDARY = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
VALID_HEALER = frozenset({"eligible", "conditional", "abstain"})
VALID_CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW"})
VALID_MECH_STATUS = frozenset({"CONFIRMED", "SUPPORTED", "SUSPECTED", "REJECTED"})
VALID_OUTCOME = frozenset(
    {"VALID_MODEL_OUTCOME", "INVALID_INFRASTRUCTURE", "INVALID_EVALUATOR", "PENDING_REVIEW"}
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    census_prep.PREP_CSV: census_prep.PREP_CSV_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    REMAINING101_ROSTER: REMAINING101_ROSTER_SHA256,
    SIGNAL_INVENTORY: SIGNAL_INVENTORY_SHA256,
    CENSUS_MANIFEST: CENSUS_MANIFEST_SHA256,
    CENSUS_PROVENANCE: CENSUS_PROVENANCE_SHA256,
    CENSUS_EXECUTION: CENSUS_EXECUTION_SHA256,
    census_prep.ANALYZER: CENSUS_SCRIPT_SHA256,
    census_prep.G2_PROVISIONAL_CSV: census_prep.G2_PROVISIONAL_CSV_SHA256,
    census_prep.MODULE_EXCEPTION_CSV: census_prep.MODULE_EXCEPTION_CSV_SHA256,
    census_prep.MULTIPLE_SIGNAL_CSV: census_prep.MULTIPLE_SIGNAL_CSV_SHA256,
    census_prep.FREEZE20_CSV: census_prep.FREEZE20_CSV_SHA256,
    census_prep.FREEZE20_MANIFEST: census_prep.FREEZE20_MANIFEST_SHA256,
    census_prep.PROGRESS_CENSUS_MANIFEST: census_prep.PROGRESS_CENSUS_MANIFEST_SHA256,
}

ROSTER_FIELDS = (
    "batch_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "dataset",
    "model",
    "condition",
    "seed",
    "generation_id",
    "raw_generation_reference",
    "proposed_primary_batch",
    "return_type_bucket",
    "return_shape_bucket",
    "evaluator_outcome",
    "selection_reason",
)

RECORD_FIELDS = (
    "batch_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "dataset",
    "model",
    "condition",
    "seed",
    "generation_id",
    "raw_generation_reference",
    "review_status",
    "outcome_validity",
    "primary_layer",
    "secondary_layer",
    "mechanism_tags_json",
    "failure_chain",
    "healer_eligibility",
    "abstain_reason",
    "eligibility_rule",
    "rejection_condition",
    "unresolved_reason_code",
    "evidence_present",
    "evidence_missing",
    "minimal_future_diagnostic",
    "confidence",
    "evidence_citations",
    "source_structure_locator",
    "public_contract_locator",
    "evaluator_provenance_locator",
    "adjudicator_identity",
    "adjudication_timestamp",
    "evidence_summary",
    "planning_signal_note",
)

UNRESOLVED_GAP_FIELDS = (
    "program_id",
    "task_id",
    "primary_layer",
    "unresolved_reason_code",
    "evidence_present",
    "evidence_missing",
    "minimal_future_diagnostic",
    "healer_eligibility",
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


def _mech(*items: tuple[str, str, str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for tag, status, note in items:
        _require(status in VALID_MECH_STATUS, f"invalid mechanism status: {status}")
        out.append({"tag": tag, "status": status, "note": note})
    return out


def _decision(
    *,
    primary: str,
    secondary: str,
    mechanisms: list[dict[str, str]],
    failure_chain: list[str],
    outcome_validity: str,
    healer: str,
    abstain_reason: str,
    eligibility_rule: str,
    rejection_condition: str,
    unresolved_reason_code: str,
    evidence_present: str,
    evidence_missing: str,
    minimal_future_diagnostic: str,
    confidence: str,
    source_structure_locator: str,
    public_contract_locator: str,
    evidence_summary: str,
    planning_signal_note: str,
) -> dict[str, Any]:
    _require(primary in VALID_PRIMARY, f"invalid primary: {primary}")
    if secondary:
        _require(secondary in VALID_SECONDARY, f"invalid secondary: {secondary}")
        _require(secondary != primary, "secondary must not duplicate primary")
    _require(healer in VALID_HEALER, f"invalid healer: {healer}")
    _require(confidence in VALID_CONFIDENCE, f"invalid confidence: {confidence}")
    _require(outcome_validity in VALID_OUTCOME, f"invalid outcome: {outcome_validity}")
    _require(bool(failure_chain), "failure_chain required")
    _require(bool(mechanisms), "mechanism tags required")
    if primary == "UNRESOLVED":
        _require(healer == "abstain", "UNRESOLVED must abstain")
        _require(bool(unresolved_reason_code), "UNRESOLVED requires reason code")
        _require(bool(evidence_missing), "UNRESOLVED requires evidence_missing")
        _require(confidence == "LOW", "UNRESOLVED confidence should be LOW")
    if healer == "abstain":
        _require(bool(abstain_reason), "abstain requires abstain_reason")
    if healer in {"eligible", "conditional"}:
        _require(bool(eligibility_rule), "eligible/conditional require eligibility_rule")
        _require(bool(rejection_condition), "eligible/conditional require rejection_condition")
    # Reject evaluator-FAIL→L5 and signal→L2 shortcuts in decision metadata.
    _require(
        "evaluator FAIL" not in evidence_summary.lower()
        or "not solely" in evidence_summary.lower()
        or primary != "L5"
        or "public" in evidence_summary.lower(),
        "L5 must not be solely from evaluator FAIL",
    )
    return {
        "primary_layer": primary,
        "secondary_layer": secondary,
        "mechanism_tags_json": _json(mechanisms),
        "failure_chain": " → ".join(failure_chain),
        "outcome_validity": outcome_validity,
        "healer_eligibility": healer,
        "abstain_reason": abstain_reason,
        "eligibility_rule": eligibility_rule,
        "rejection_condition": rejection_condition,
        "unresolved_reason_code": unresolved_reason_code,
        "evidence_present": evidence_present,
        "evidence_missing": evidence_missing,
        "minimal_future_diagnostic": minimal_future_diagnostic,
        "confidence": confidence,
        "source_structure_locator": source_structure_locator,
        "public_contract_locator": public_contract_locator,
        "evidence_summary": evidence_summary,
        "planning_signal_note": planning_signal_note,
        "review_status": "ADJUDICATED",
    }


# Fixed deterministic decisions keyed by program_id (no model calls).
DECISIONS: dict[str, dict[str, Any]] = {
    # 1 Mbpp/769 — list difference order/content ≠ public assert.
    "0c9f29239bdf609a6306524184cfbb830eeb41becd9d31709931fb300234c7a3": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "list1-order filter yields [10,15,20,30] vs public [10,20,30,15]",
            ),
            ("return_shape_mismatch", "REJECTED", "both sides are lists; shape not the root cause"),
            ("entry_point_unique_candidate", "REJECTED", "expected Diff exists; not an error"),
            (
                "public_examples_non_discriminating",
                "REJECTED",
                "public assert uniquely discriminates ordering/content semantics",
            ),
        ),
        failure_chain=[
            "parseable Diff entry point present",
            "returns list comprehension preserving list1 order excluding list2",
            "public assert expects [10,20,30,15] not [10,15,20,30]",
            "primary=L5 semantic/algorithmic",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Ordering/difference semantics require algorithm reconstruction, not a unique local edit.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert Diff(...)==[10,20,30,15]; static list-comp body",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:def Diff; list comprehension return",
        public_contract_locator="data/mbpp_plus/tasks.jsonl#task_id=Mbpp/769 assert Diff([...])",
        evidence_summary=(
            "Public list assert is violated by static expansion of the list comprehension "
            "(list1 order keep). Return-shape planning signal is rejected as root cause."
        ),
        planning_signal_note="census return_shape_mismatch is planning-only; adjudicated L5 not L2",
    ),
    # 2 Mbpp/748 — leading space before first capital word.
    "0f51d44f44faf38d9fbe794eb4c86a316809d300c9a5e206289d459bb71cabbf": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "wrong_boundary_condition",
                "CONFIRMED",
                "first capital at i==0 inserts leading space → ' Python' ≠ 'Python'",
            ),
            ("return_shape_mismatch", "REJECTED", "return type is str as expected"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable capital_words_spaces present",
            "loop inserts space when capital starts and prev_is_capital is false",
            "public assert capital_words_spaces('Python')=='Python' fails under static first-char rule",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Boundary-condition repair for capital-word spacing is semantic, not unique contract alias.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert; static first-iteration space insertion",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:for-loop; result.append(' ') before first capital",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/748 assert capital_words_spaces(\"Python\")",
        evidence_summary=(
            "Public single-word example is failed by the static leading-space boundary. "
            "Not an L2 packaging/shape case."
        ),
        planning_signal_note="contract-batch membership ≠ adjudicated L2",
    ),
    # 3 Mbpp/125 — 0/1 polarity / Kadane objective wrong vs problem.
    "151a1b3981da65abb7a94e2b2acac6491de4d6ad470da3c006f94b9a85273346": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "scores '1' as +1/'0' as -1 maximizing ones-zeros; problem asks max |0s-1s| favoring zeros-ones for expected 6",
            ),
            ("algorithm_reconstruction_required", "SUPPORTED", "need correct 0/1 scoring objective"),
            ("return_shape_mismatch", "REJECTED", "returns int scalar as expected"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable find_length present",
            "Kadane uses +1 for '1' and -1 for '0'",
            "public expected 6 corresponds to maximizing zeros-minus-ones on this binary string",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Objective polarity/formula rewrite is algorithmic reconstruction.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert find_length('11000010001')==6; source scoring comments/body",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:current_sum +=1 for '1' else -=1",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/125",
        evidence_summary=(
            "Static scoring polarity contradicts the public expected maximum-difference "
            "interpretation for the given binary string. Evaluator FAIL is not used alone."
        ),
        planning_signal_note="return_shape signal rejected",
    ),
    # 4 Mbpp/742 — tetrahedron area formula wrong vs √3 a².
    "165c873221f996a992adfe426b96e62865dddc2407ce93ba89df3ea882dfac54": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "uses a²*(√3/4+√6) ≈25.94; public expects ≈15.588 = a²√3",
            ),
            ("return_shape_mismatch", "REJECTED", "float scalar return matches contract family"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable area_tetrahedron present",
            "formula includes extraneous √6 term",
            "public arithmetic area_tetrahedron(3)==15.588... unmatched",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Geometric formula reconstruction is not a unique safe local edit.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public float assert; static closed-form expression",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:return edge**2*(sqrt(3)/4+sqrt(6))",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/742",
        evidence_summary="Public numeric assert uniquely falsifies the static formula.",
        planning_signal_note="not L2",
    ),
    # 5 Mbpp/287 — public assert matches; plus-fail unresolved.
    "2c7db8ef79f3fb6f4877e45429a281e98b645f377f94b6d7912fb3d66f5847df": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "square_Sum(2)==20 matches loop 2²+4²",
            ),
            ("extra_wrapper_or_output", "SUPPORTED", "module-level assert present; not proven root cause"),
            ("return_shape_mismatch", "SUSPECTED", "planning signal only; no public shape violation observed"),
            ("diagnostic_execution_required", "CONFIRMED", "need non-oracle diagnostics to close layer"),
            ("runtime_vs_semantic_not_closed", "SUPPORTED", "base pass / plus fail without closable public root"),
            ("multiple_plausible_root_causes", "SUPPORTED", "L2 packaging vs L5 hidden semantic both possible"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable square_Sum; public example satisfied statically",
            "no public contract shape violation observed",
            "EvalPlus plus failure exists but path not inspectable without execution",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Root cause not closed; cannot mark eligible/conditional.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match; entry OK; packaging assert residue",
        evidence_missing="failing plus-case behavior; whether packaging assert affects harness",
        minimal_future_diagnostic="read-only capture of first failing plus case exception/return without oracle-guided repair",
        confidence="LOW",
        source_structure_locator="evaluation_source:loop + trailing assert square_Sum(2)==20",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/287",
        evidence_summary=(
            "Public example is satisfied. Planning return_shape signal is not confirmed as L2. "
            "Evidence insufficient to close L2 vs L5."
        ),
        planning_signal_note="signal≠layer",
    ),
    # 6 Mbpp/410 seed55
    "3b027c95ed6970ead1bf34a58e5e5968a842375728129f12e3233a5ef00aed89": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "min of numeric elements equals 2 on public list",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail path unknown"),
            ("runtime_vs_semantic_not_closed", "SUPPORTED", "L4 empty-numeric / L5 edge cases possible"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable min_val; filters numeric then min",
            "public assert satisfied",
            "plus-fail root cause not publicly closable",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match; entry OK",
        evidence_missing="first failing plus input/exception",
        minimal_future_diagnostic="non-oracle observation of first failing plus case return/exception",
        confidence="LOW",
        source_structure_locator="evaluation_source:min([x for x in lst if isinstance(x,(int,float))])",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/410",
        evidence_summary="Public example matches; cannot close taxonomy layer from allowed evidence.",
        planning_signal_note="signal≠layer",
    ),
    # 7 Mbpp/427 seed22
    "5bf8a1f3934680a03fdc52a96fcca133f19f3a6885bcc6c4f81bd72ef2bdc6b4": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "yyyy-mm-dd split reorder matches public dd-mm-yyyy",
            ),
            ("extra_wrapper_or_output", "SUPPORTED", "module assert present"),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable change_date_format; public example satisfied",
            "no confirmed public shape violation",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match; packaging assert",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:split('-') reorder + trailing assert",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/427",
        evidence_summary="Public date rewrite matches; layer not closable.",
        planning_signal_note="signal≠layer",
    ),
    # 8 Mbpp/572 — dedupe vs unique-occurrence.
    "643332a7c66f839f75e24546129bca2d4aacf4cdbd005fce6765c2e811855238": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "keeps first occurrence of every value → [1,2,3,4,5] vs public [1,4,5]",
            ),
            ("algorithm_reconstruction_required", "CONFIRMED", "need keep-only-count==1 filter"),
            ("return_shape_mismatch", "REJECTED", "list vs list; content semantics fail"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable two_unique_nums",
            "seen-set dedupe keeps all first occurrences",
            "public assert requires elements with count==1 only",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Algorithm rewrite from dedupe to unique-count filter.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert; static seen-set logic",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:seen set append-if-new",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/572",
        evidence_summary="Public example uniquely proves semantic mismatch vs dedupe.",
        planning_signal_note="not L2",
    ),
    # 9 Mbpp/427 seed11
    "81cd6f1d055d47e781e3d08c914571b1959ebc39655a00f7ecfd110508503b4e": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "same reorder logic matches public example",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable change_date_format; public example satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:split('-') reorder",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/427",
        evidence_summary="Distinct source for Mbpp/427; still cannot close layer.",
        planning_signal_note="signal≠layer",
    ),
    # 10 Mbpp/237 — order-insensitive tuple counting.
    "94ad97956f46bf1c8310acc9ba772d28e446fd47a066ac3a10c19733cdb80eb5": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "Counter treats (3,1)≠(1,3); public expects sorted-key {(1,3):2,...}",
            ),
            ("algorithm_reconstruction_required", "SUPPORTED", "need canonicalize tuple order before count"),
            ("return_shape_mismatch", "REJECTED", "dict vs dict; key semantics fail"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable check_occurences",
            "dict(Counter(lst)) keeps order-sensitive keys",
            "public assert merges reversed pairs into sorted keys",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason=(
            "Canonicalize-then-count repair is not uniquely constrained "
            "(arity>2, key form); prior governance rejected conditional without closed safety."
        ),
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert with order-insensitive keys; Counter body",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:dict(Counter(lst))",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/237",
        evidence_summary="Public mapping uniquely proves semantic key-normalization failure.",
        planning_signal_note="not L2; healer abstain (not eligible)",
    ),
    # 11 Mbpp/410 seed44
    "ae0ea3edc7597b91f18d21dae1503c2333353a0b9686af9742afd8e1f056e10a": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "public numeric min equals 2",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable min_val with empty-list ValueError guard",
            "public assert satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:empty check + numeric min",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/410",
        evidence_summary="Public example matches; layer not closable.",
        planning_signal_note="signal≠layer",
    ),
    # 12 Mbpp/16 seed44
    "bbcfbf7cb6786406b7dde275f718e2fcc2b980043166bfc200703d5cbef2b8dc": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "aab_cbbbc split/islower yields True",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable text_lowercase_underscore",
            "public True example satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior / false-negative cases",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:split('_') + islower",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/16",
        evidence_summary="Public example matches; cannot close L2/L5.",
        planning_signal_note="signal≠layer",
    ),
    # 13 Mbpp/138 — public True; base fail unresolved.
    "bce7d06fe15d627115b96c241688d603b61450245867becd7f426917dfcfa2a9": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "bit-loop returns True for 10 matching public assert",
            ),
            ("incorrect_formula", "SUSPECTED", "bit logic looks nonstandard but not publicly falsified"),
            ("extra_wrapper_or_output", "SUPPORTED", "module assert present"),
            ("algorithm_reconstruction_required", "SUSPECTED", "may need rewrite if other cases fail"),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "base/plus failures not publicly localized"),
            ("multiple_plausible_root_causes", "SUPPORTED", "L5 vs packaging vs other"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable is_Sum_Of_Powers_Of_Two",
            "public True example satisfied by static path for n=10",
            "base/plus failures not closable from one public True example",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved; suspicious formula not confirmed against additional public cases.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_need_diagnostics",
        evidence_present="public assert True path; packaging assert",
        evidence_missing="additional public/base failing inputs and observed returns",
        minimal_future_diagnostic="non-oracle observation of first failing base/plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:while n>1 bit tests + trailing assert",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/138",
        evidence_summary="Single public True example does not close layer; do not equate FAIL→L5.",
        planning_signal_note="signal≠layer",
    ),
    # 14 Mbpp/103 — Eulerian DP not publicly closable.
    "bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "algorithm_reconstruction_required",
                "SUSPECTED",
                "DP recurrence looks malformed but not hand-closed to ≠4 without execution",
            ),
            ("incorrect_formula", "SUSPECTED", "A[i][j] uses n,m oddly"),
            ("public_examples_non_discriminating", "SUPPORTED", "single assert insufficient to close"),
            ("diagnostic_execution_required", "CONFIRMED", "need safe evaluation of eulerian_num(3,1)"),
            ("runtime_vs_semantic_not_closed", "SUPPORTED", "L4 vs L5 unknown"),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable eulerian_num with unusual DP",
            "public assert eulerian_num(3,1)==4 not statically closed",
            "cannot choose L4 vs L5 from allowed evidence",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved DP; no unique safe repair.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="complex_algorithm_without_public_trace",
        evidence_present="source DP body; public single assert",
        evidence_missing="observed return for (3,1) and intermediate recurrence validity",
        minimal_future_diagnostic="sandboxed eval of eulerian_num(3,1) return only (no healer)",
        confidence="LOW",
        source_structure_locator="evaluation_source:DP nested loops A[n][m]",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/103",
        evidence_summary="Cannot confirm L5 from public evidence alone; FAIL≠L5.",
        planning_signal_note="signal≠layer",
    ),
    # 15 Mbpp/16 seed33
    "cefff3d8a490047c757f7779c27204cf684a5b89df2223e5b7b447475b3f30af": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "public True example satisfied",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable text_lowercase_underscore",
            "public example satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:split + islower/empty checks",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/16",
        evidence_summary="Public example matches; layer not closable.",
        planning_signal_note="signal≠layer",
    ),
    # 16 Mbpp/581 — surface area formula ≠ 33.
    "d6cc3d6bdcc0be8b24448e7ba5b9808a9e505adf3b7dccbde8d30259c2d18cad": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "base² + base*slant ≈21.82 ≠ public 33",
            ),
            ("algorithm_reconstruction_required", "SUPPORTED", "correct pyramid TSA formula unknown uniquely"),
            ("return_shape_mismatch", "REJECTED", "float scalar OK"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable surface_Area",
            "static slant/lateral formula expands ≠33",
            "public assert surface_Area(3,4)==33",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Geometric formula reconstruction not unique/safe.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public numeric assert; closed-form source",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:base_area + base_edge*slant_height",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/581",
        evidence_summary="Public arithmetic uniquely proves semantic formula failure.",
        planning_signal_note="not L2",
    ),
    # 17 Mbpp/118
    "da3b306e10fbd0e391950f9383ce978a7f07519334207d52f0738fadb1c4b7f6": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "s.split() matches public list example",
            ),
            ("extra_wrapper_or_output", "SUPPORTED", "module assert present"),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable string_to_list; public example satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match; packaging assert",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:s.split() + trailing assert",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/118",
        evidence_summary="Public example matches; cannot close layer.",
        planning_signal_note="signal≠layer",
    ),
    # 18 Mbpp/14
    "e762c7d5362d7c213d760547ce6d9f8bce9b515216b1b80877c78733f20520af": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "a*b*c//2 == 240 matches public",
            ),
            ("extra_wrapper_or_output", "SUPPORTED", "module assert present"),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable find_Volume; public arithmetic satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior (float/int/edge)",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:a*b*c//2 + trailing assert",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/14",
        evidence_summary="Public example matches; layer not closable.",
        planning_signal_note="signal≠layer",
    ),
    # 19 Mbpp/721 — divide by n instead of 2n-1.
    "ece76238dc23e4c6ac96b346c685f1846406516726a1310a5427ae189f79cad6": _decision(
        primary="L5",
        secondary="",
        mechanisms=_mech(
            (
                "incorrect_formula",
                "CONFIRMED",
                "returns max_sum/n; path length for N×N right/down paths is 2N-1 (=5 for N=3); 26/5=5.2",
            ),
            ("algorithm_reconstruction_required", "SUPPORTED", "average denominator wrong; may also need max-average vs max-sum"),
            ("return_shape_mismatch", "REJECTED", "float scalar OK"),
            ("entry_point_unique_candidate", "REJECTED", "entry point correct"),
        ),
        failure_chain=[
            "parseable maxAverageOfPath DP for max sum",
            "divides by n instead of path cell count 2n-1",
            "public assert 5.2 implies sum/5",
            "primary=L5",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Average-path formula reconstruction not a unique safe local edit.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="",
        evidence_present="public assert 5.2; source return max_sum/n; path-length identity 2n-1",
        evidence_missing="",
        minimal_future_diagnostic="",
        confidence="HIGH",
        source_structure_locator="evaluation_source:return max_sum / n",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/721",
        evidence_summary="Public average uniquely falsifies denominator n vs 2n-1.",
        planning_signal_note="not L2",
    ),
    # 20 Mbpp/16 seed11
    "fb762e37725ef76332c7c76243702f91d0378326ba55e4bba0db5890ecbc0cc1": _decision(
        primary="UNRESOLVED",
        secondary="",
        mechanisms=_mech(
            (
                "public_examples_non_discriminating",
                "CONFIRMED",
                "public True example satisfied (digits allowed)",
            ),
            ("return_shape_mismatch", "SUSPECTED", "planning only"),
            ("diagnostic_execution_required", "CONFIRMED", "plus-fail unknown"),
            ("entry_point_unique_candidate", "REJECTED", "not an error"),
        ),
        failure_chain=[
            "parseable text_lowercase_underscore",
            "public example satisfied",
            "plus-fail unresolved",
            "primary=UNRESOLVED",
            "healer=abstain",
        ],
        outcome_validity="VALID_MODEL_OUTCOME",
        healer="abstain",
        abstain_reason="Unresolved root cause.",
        eligibility_rule="",
        rejection_condition="",
        unresolved_reason_code="public_examples_non_discriminating_plus_fail",
        evidence_present="public assert match",
        evidence_missing="failing plus case behavior",
        minimal_future_diagnostic="non-oracle capture of first failing plus case",
        confidence="LOW",
        source_structure_locator="evaluation_source:split + islower/isdigit checks",
        public_contract_locator="tasks.jsonl#task_id=Mbpp/16",
        evidence_summary="Public example matches; cannot close layer.",
        planning_signal_note="signal≠layer",
    ),
}


def _frozen97(repo: Path) -> set[str]:
    ids: set[str] = set()
    for _name, path, _sha, _n in census_prep.FROZEN_SETS:
        ids.update(row["program_id"] for row in _read_csv(repo / path))
    _require(len(ids) == 97, f"frozen97 drift: {len(ids)}")
    return ids


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    batch = _read_csv(repo / NEXT_BATCH_ROSTER)
    remaining = _read_csv(repo / REMAINING101_ROSTER)
    inventory = {row["program_id"]: row for row in _read_csv(repo / SIGNAL_INVENTORY)}
    prep = {row["program_id"]: row for row in _read_csv(repo / census_prep.PREP_CSV)}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    frozen = _frozen97(repo)
    remaining_ids = {row["program_id"] for row in remaining}
    batch_ids = [row["program_id"] for row in batch]

    _require(len(batch) == TARGET_CELLS, f"batch size drift: {len(batch)}")
    _require(len(set(batch_ids)) == TARGET_CELLS, "duplicate program_id in batch")
    _require(len({row["source_sha256"] for row in batch}) == TARGET_CELLS, "source not unique")
    _require(not (set(batch_ids) & frozen), "batch intersects frozen97")
    _require(set(batch_ids) <= remaining_ids, "batch not subset of remaining101")
    _require(len(remaining_ids) == 101, "remaining101 drift")
    _require(len(frozen) + len(remaining_ids) == 198, "97+101 closure drift")
    _require(set(DECISIONS) == set(batch_ids), "DECISIONS keys must equal batch program_ids")
    _require(
        all(row["proposed_primary_batch"] == TARGET_PRIMARY_BATCH for row in batch),
        "batch primary batch drift",
    )

    roster_rows: list[dict[str, str]] = []
    record_rows: list[dict[str, str]] = []
    for row in batch:
        pid = row["program_id"]
        rem = next(r for r in remaining if r["program_id"] == pid)
        decision = DECISIONS[pid]
        journal = journals[pid]
        _require(
            journal["evaluation_source_sha256"] == row["source_sha256"],
            f"source sha drift: {pid}",
        )
        citations = _json(
            [
                {
                    "kind": "public_task",
                    "path": preparation.TASKS.as_posix(),
                    "locator": f"task_id={row['task_id']}",
                },
                {
                    "kind": "raw_generation",
                    "path": preparation.JOURNAL.as_posix(),
                    "locator": f"program_id={pid};healer_account=H0",
                },
                {
                    "kind": "planning_signal",
                    "path": SIGNAL_INVENTORY.as_posix(),
                    "locator": f"program_id={pid}",
                },
                {
                    "kind": "batch_roster",
                    "path": NEXT_BATCH_ROSTER.as_posix(),
                    "locator": f"program_id={pid}",
                },
                {
                    "kind": "evaluator_outcome",
                    "path": census_prep.PREP_CSV.as_posix(),
                    "locator": (
                        f"program_id={pid};"
                        f"evalplus_base={prep[pid].get('evalplus_base_status','')};"
                        f"evalplus_plus={prep[pid].get('evalplus_plus_status','')}"
                    ),
                },
            ]
        )
        roster_rows.append(
            {
                "batch_rank": row["batch_rank"],
                "cell_id": rem["cell_id"],
                "program_id": pid,
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "dataset": rem["dataset"],
                "model": rem["model"],
                "condition": rem["condition"],
                "seed": row["seed"],
                "generation_id": rem["generation_id"],
                "raw_generation_reference": rem["raw_generation_reference"],
                "proposed_primary_batch": row["proposed_primary_batch"],
                "return_type_bucket": row["return_type_bucket"],
                "return_shape_bucket": row["return_shape_bucket"],
                "evaluator_outcome": rem["evaluator_outcome"],
                "selection_reason": row["selection_reason"],
            }
        )
        record_rows.append(
            {
                "batch_rank": row["batch_rank"],
                "cell_id": rem["cell_id"],
                "program_id": pid,
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "dataset": rem["dataset"],
                "model": rem["model"],
                "condition": rem["condition"],
                "seed": row["seed"],
                "generation_id": rem["generation_id"],
                "raw_generation_reference": rem["raw_generation_reference"],
                "review_status": decision["review_status"],
                "outcome_validity": decision["outcome_validity"],
                "primary_layer": decision["primary_layer"],
                "secondary_layer": decision["secondary_layer"],
                "mechanism_tags_json": decision["mechanism_tags_json"],
                "failure_chain": decision["failure_chain"],
                "healer_eligibility": decision["healer_eligibility"],
                "abstain_reason": decision["abstain_reason"],
                "eligibility_rule": decision["eligibility_rule"],
                "rejection_condition": decision["rejection_condition"],
                "unresolved_reason_code": decision["unresolved_reason_code"],
                "evidence_present": decision["evidence_present"],
                "evidence_missing": decision["evidence_missing"],
                "minimal_future_diagnostic": decision["minimal_future_diagnostic"],
                "confidence": decision["confidence"],
                "evidence_citations": citations,
                "source_structure_locator": decision["source_structure_locator"],
                "public_contract_locator": decision["public_contract_locator"],
                "evaluator_provenance_locator": (
                    f"{census_prep.PREP_CSV.as_posix()}#program_id={pid}"
                ),
                "adjudicator_identity": ADJUDICATOR_IDENTITY,
                "adjudication_timestamp": ADJUDICATION_TIMESTAMP,
                "evidence_summary": decision["evidence_summary"],
                "planning_signal_note": decision["planning_signal_note"],
            }
        )

    _require(len(record_rows) == TARGET_CELLS, "record count drift")
    _require(all(r["review_status"] == "ADJUDICATED" for r in record_rows), "all must be ADJUDICATED")
    _require(
        all(r["primary_layer"] != "UNRESOLVED" or r["healer_eligibility"] == "abstain" for r in record_rows),
        "UNRESOLVED must abstain",
    )

    unresolved_gaps = [
        {
            "program_id": row["program_id"],
            "task_id": row["task_id"],
            "primary_layer": row["primary_layer"],
            "unresolved_reason_code": row["unresolved_reason_code"],
            "evidence_present": row["evidence_present"],
            "evidence_missing": row["evidence_missing"],
            "minimal_future_diagnostic": row["minimal_future_diagnostic"],
            "healer_eligibility": row["healer_eligibility"],
        }
        for row in record_rows
        if row["primary_layer"] == "UNRESOLVED"
    ]

    primary = Counter(row["primary_layer"] for row in record_rows)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in record_rows)
    healer = Counter(row["healer_eligibility"] for row in record_rows)
    outcome = Counter(row["outcome_validity"] for row in record_rows)
    confidence = Counter(row["confidence"] for row in record_rows)
    unresolved_reasons = Counter(
        row["unresolved_reason_code"] for row in record_rows if row["unresolved_reason_code"]
    )

    mech_tag_counts: Counter[str] = Counter()
    mech_status_counts: Counter[str] = Counter()
    for row in record_rows:
        for item in json.loads(row["mechanism_tags_json"]):
            mech_tag_counts[item["tag"]] += 1
            mech_status_counts[item["status"]] += 1

    eval_x_primary: Counter[str] = Counter()
    rtype_x_primary: Counter[str] = Counter()
    for roster, record in zip(roster_rows, record_rows, strict=True):
        eval_x_primary[f"{roster['evaluator_outcome']}×{record['primary_layer']}"] += 1
        rtype_x_primary[f"{roster['return_type_bucket'] or 'UNKNOWN'}×{record['primary_layer']}"] += 1

    true_l2 = primary.get("L2", 0)
    needs_diag = sum(1 for row in record_rows if row["minimal_future_diagnostic"])

    summary = {
        "status": STATUS,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in record_rows}),
        "unique_source_sha256": len({row["source_sha256"] for row in record_rows}),
        "unique_task_id": len({row["task_id"] for row in record_rows}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "unresolved_reason_code_distribution": dict(sorted(unresolved_reasons.items())),
        "true_adjudicated_L2_count": true_l2,
        "true_adjudicated_L2_ratio_of_batch": true_l2 / TARGET_CELLS,
        "contract_planning_signal_cells_in_parent99_note": (
            "Parent remaining101 had 99 B-batch contract-related planning signals; "
            "this batch is 20 of those. Adjudicated L2 count is independent and is "
            f"{true_l2}/20 in this provisional revision."
        ),
        "cells_needing_future_diagnostics": needs_diag,
        "evaluator_outcome_x_primary_layer": dict(sorted(eval_x_primary.items())),
        "return_type_bucket_x_primary_layer": dict(sorted(rtype_x_primary.items())),
        "separation_note": (
            "planning static signals ≠ adjudicated primary_layer ≠ healer_eligibility"
        ),
    }

    mechanism_counts = {
        "by_tag": dict(sorted(mech_tag_counts.items())),
        "by_status": dict(sorted(mech_status_counts.items())),
        "note": "mechanism status is CONFIRMED/SUPPORTED/SUSPECTED/REJECTED; not a layer",
    }

    healer_summary = {
        "distribution": dict(sorted(healer.items())),
        "eligible_count": healer.get("eligible", 0),
        "conditional_count": healer.get("conditional", 0),
        "abstain_count": healer.get("abstain", 0),
        "rule": (
            "eligible only for unique contract-local safe repairs; "
            "this batch has none. UNRESOLVED always abstain."
        ),
    }

    execution_counts = {
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

    return {
        "roster_rows": roster_rows,
        "record_rows": record_rows,
        "unresolved_gaps": unresolved_gaps,
        "summary": summary,
        "mechanism_counts": mechanism_counts,
        "healer_summary": healer_summary,
        "execution_counts": execution_counts,
        "inventory": inventory,
        "frozen": frozen,
        "remaining_ids": remaining_ids,
    }


def _report(analysis: dict[str, Any], roster_sha: str, records_sha: str) -> str:
    s = analysis["summary"]
    lines = [
        "# Candidate B r003 taxonomy v3.1：remaining101 batch01 20-cell provisional v1",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "## 範圍",
        "",
        "- 僅裁決固定 next 20-cell roster；不增減、不替換。",
        "- 不執行 candidate／tests／EvalPlus／diagnostics／validation／Healer。",
        "- 不修改 frozen97、不修改 census revision、不 freeze／commit／push。",
        "- `UNRESOLVED` 不是 L6；本輪 20 格皆 `ADJUDICATED`（不足則 UNRESOLVED，非 PENDING_REVIEW）。",
        "",
        "## Roster closure",
        "",
        f"- adjudication roster SHA-256：`{roster_sha}`",
        f"- adjudication records SHA-256：`{records_sha}`",
        f"- cells={s['cells']}; unique program/source/task="
        f"{s['unique_program_id']}/{s['unique_source_sha256']}/{s['unique_task_id']}",
        "",
        "## Primary / secondary",
        "",
    ]
    for k, v in s["primary_layer_distribution"].items():
        lines.append(f"- primary `{k}`：{v}")
    for k, v in s["secondary_layer_distribution"].items():
        lines.append(f"- secondary `{k}`：{v}")
    lines.extend(
        [
            "",
            "## Healer eligibility",
            "",
            f"- {s['healer_eligibility_distribution']}",
            "",
            "## Outcome / confidence",
            "",
            f"- outcome：{s['outcome_validity_distribution']}",
            f"- confidence：{s['confidence_distribution']}",
            "",
            "## UNRESOLVED",
            "",
            f"- count：{s['primary_layer_distribution'].get('UNRESOLVED', 0)}",
            f"- reason codes：{s['unresolved_reason_code_distribution']}",
            f"- needing future diagnostics：{s['cells_needing_future_diagnostics']}",
            "",
            "## L2 說明",
            "",
            f"- 本批真正裁決為 L2：{s['true_adjudicated_L2_count']} / 20",
            "- 上一輪 99 格 contract-related **planning signal** 不能直接等於 99 格 L2：",
            "  signal 只表示值得審查；L2 需公開契約明確、差異可觀察、且足以解釋失敗。",
            "  本批多數為 return-shape planning signal，但 entry point 正確、回傳型別家族相符，",
            "  根因若可由公開 assert 證明則多為 L5；若公開例子已滿足則為 UNRESOLVED。",
            "",
            "## Execution counts",
            "",
            "- 全部為 0。",
            "",
            "## 停止點",
            "",
            "- 完成 provisional v1 後停止；不進行 post-adjudication audit／v2／freeze。",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["roster_rows"])
    records_bytes = _csv_bytes(RECORD_FIELDS, analysis["record_rows"])
    unresolved_bytes = _csv_bytes(UNRESOLVED_GAP_FIELDS, analysis["unresolved_gaps"])
    summary_bytes = _json_bytes(analysis["summary"])
    mechanism_bytes = _json_bytes(analysis["mechanism_counts"])
    healer_bytes = _json_bytes(analysis["healer_summary"])
    execution_bytes = _json_bytes(analysis["execution_counts"])
    roster_sha = _sha(roster_bytes)
    records_sha = _sha(records_bytes)
    report_bytes = _report(analysis, roster_sha, records_sha).encode("utf-8")

    outputs_wo_manifest = {
        "adjudication_roster.csv": roster_bytes,
        "adjudication_records.csv": records_bytes,
        "adjudication_summary.json": summary_bytes,
        "mechanism_counts.json": mechanism_bytes,
        "unresolved_evidence_gaps.csv": unresolved_bytes,
        "healer_eligibility_summary.json": healer_bytes,
        "adjudication_report_zh.md": report_bytes,
        "execution_counts.json": execution_bytes,
    }
    outputs_sha = {name: _sha(data) for name, data in outputs_wo_manifest.items()}

    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "fixed_next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "remaining101_roster_sha256": REMAINING101_ROSTER_SHA256,
        "census_manifest_sha256": CENSUS_MANIFEST_SHA256,
        "taxonomy_v31_planning_reference": {
            "filename": V31_REFERENCE_FILENAME,
            "sha256": V31_REFERENCE_SHA256,
            "status": V31_REFERENCE_STATUS,
        },
        "selection_rule": {
            "primary_batch": TARGET_PRIMARY_BATCH,
            "source_representative": True,
            "round_robin_return_type": True,
            "stable_sort_program_id": True,
            "healer_eligibility_not_used": True,
        },
        "adjudication_roster_sha256": roster_sha,
        "adjudication_records_sha256": records_sha,
        "primary_layer_distribution": analysis["summary"]["primary_layer_distribution"],
        "healer_eligibility_distribution": analysis["summary"]["healer_eligibility_distribution"],
        "true_adjudicated_L2_count": analysis["summary"]["true_adjudicated_L2_count"],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "adjudicator_identity": ADJUDICATOR_IDENTITY,
        "adjudication_timestamp": ADJUDICATION_TIMESTAMP,
        "frozen_marker_written": False,
        "formal_progress_updated": False,
        **analysis["execution_counts"],
    }
    provenance_bytes = _json_bytes(provenance)
    outputs_wo_manifest["provenance.json"] = provenance_bytes
    outputs_sha["provenance.json"] = _sha(provenance_bytes)

    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "cells": TARGET_CELLS,
        "fixed_next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "remaining101_roster_sha256": REMAINING101_ROSTER_SHA256,
        "adjudication_roster_sha256": roster_sha,
        "adjudication_records_sha256": records_sha,
        "taxonomy_v31_reference_sha256": V31_REFERENCE_SHA256,
        "primary_layer_distribution": analysis["summary"]["primary_layer_distribution"],
        "healer_eligibility_distribution": analysis["summary"]["healer_eligibility_distribution"],
        "true_adjudicated_L2_count": analysis["summary"]["true_adjudicated_L2_count"],
        "outputs_sha256_excluding_manifest": outputs_sha,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "frozen_marker_written": False,
        **analysis["execution_counts"],
    }
    outputs = dict(outputs_wo_manifest)
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output_dir / name).write_bytes(data)
    return output_dir


def main() -> None:
    output_dir = write_outputs(REPO_ROOT)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output_dir}")
    print(f"status={manifest['status']}")
    print(f"primary={manifest['primary_layer_distribution']}")
    print(f"healer={manifest['healer_eligibility_distribution']}")
    print(f"true_L2={manifest['true_adjudicated_L2_count']}")


if __name__ == "__main__":
    main()
