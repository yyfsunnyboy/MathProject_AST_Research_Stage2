#!/usr/bin/env python3
"""Independent post-adjudication audit for remaining101 batch01 provisional v1.

POST_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FREEZE

Does not modify provisional v1, census, next20 roster, or frozen97.
Does not execute candidates, tests, EvalPlus, diagnostics, Healer, or models.
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
    from scripts import (
        prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_audit_v1"
)
START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "POST_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FREEZE"
ANALYZER = Path(
    "scripts/audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1.py"
)
AUDITOR_IDENTITY = "taxonomy_v31_batch01_post_adjudication_audit_v1_static_auditor"
AUDIT_TIMESTAMP = "2026-07-21T14:55:00+08:00"

PROV_DIR = provisional.OUTPUT_RELATIVE
PROV_RECORDS = PROV_DIR / "adjudication_records.csv"
PROV_ROSTER = PROV_DIR / "adjudication_roster.csv"
PROV_SUMMARY = PROV_DIR / "adjudication_summary.json"
PROV_MANIFEST = PROV_DIR / "manifest.json"
PROV_PROVENANCE = PROV_DIR / "provenance.json"
PROV_EXECUTION = PROV_DIR / "execution_counts.json"
PROV_MECHANISM = PROV_DIR / "mechanism_counts.json"
PROV_HEALER = PROV_DIR / "healer_eligibility_summary.json"
PROV_GAPS = PROV_DIR / "unresolved_evidence_gaps.csv"
PROV_REPORT = PROV_DIR / "adjudication_report_zh.md"

PROV_RECORDS_SHA256 = "e08f1eab72275d7c37884883b1a439438daee6a2be0d8df408ba758b2364990b"
PROV_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
PROV_SUMMARY_SHA256 = "82b92391e56b92fead7237c29121b74526d77042e0df1d595897383f8f6bb5bb"
PROV_MANIFEST_SHA256 = "710ef4fd707291db650e5b14d5594ed7920f1a9c2370ee3d5cde2f09a24a627e"
PROV_PROVENANCE_SHA256 = "45bdf1a8b32258365a85643e4ce2b8d3828f6b7e82072a6c31af5e6203b3a74c"
PROV_EXECUTION_SHA256 = "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7"
PROV_MECHANISM_SHA256 = "992c179dc80b5732649354908905184ac3034ceb270d7dea4ef19a456373f1e8"
PROV_HEALER_SHA256 = "2c1cc13e6742b52c599ce6d88fe642f5c7a35753f015e596698a538d6a9eb78a"
PROV_GAPS_SHA256 = "93e359567abbb1572cfa980d7a2a7995d5ca7bbc1c3b7d7e52035cde1db4257e"
PROV_REPORT_SHA256 = "301b354a18fbcd3e93661b7106102d41d9a8f26408f7a2f67b9f81d1439c5ea2"
PROV_ANALYZER_SHA256 = "f13d14593c08b6455911c6195024327136d83abd05f9b35dc995c1fcf2c183d3"

CENSUS_DIR = census_prep.OUTPUT_RELATIVE
NEXT20 = CENSUS_DIR / "next_adjudication_batch_roster.csv"
REMAINING101 = CENSUS_DIR / "remaining101_roster.csv"
CENSUS_MANIFEST = CENSUS_DIR / "manifest.json"
NEXT20_SHA256 = "a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91"
REMAINING101_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"
CENSUS_MANIFEST_SHA256 = "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd"
CENSUS_ANALYZER_SHA256 = "e4880ad7a79b74c669a38016f100c6ead9c0e1208be32982d6c98ecc74163cd6"

V31_SHA256 = census_prep.V31_REFERENCE_SHA256
V31_STATUS = census_prep.V31_REFERENCE_STATUS
TARGET_CELLS = 20

VALID_PRIMARY_VERDICT = frozenset({"AFFIRMED", "CHALLENGED", "INSUFFICIENT_AUDIT_EVIDENCE"})
VALID_MATERIALITY = frozenset({"NONE", "EDITORIAL", "MATERIAL"})
VALID_DIM = frozenset({"AFFIRMED", "CHALLENGED", "INSUFFICIENT_AUDIT_EVIDENCE"})

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    NEXT20: NEXT20_SHA256,
    REMAINING101: REMAINING101_SHA256,
    CENSUS_MANIFEST: CENSUS_MANIFEST_SHA256,
    census_prep.ANALYZER: CENSUS_ANALYZER_SHA256,
    PROV_RECORDS: PROV_RECORDS_SHA256,
    PROV_ROSTER: PROV_ROSTER_SHA256,
    PROV_SUMMARY: PROV_SUMMARY_SHA256,
    PROV_MANIFEST: PROV_MANIFEST_SHA256,
    PROV_PROVENANCE: PROV_PROVENANCE_SHA256,
    PROV_EXECUTION: PROV_EXECUTION_SHA256,
    PROV_MECHANISM: PROV_MECHANISM_SHA256,
    PROV_HEALER: PROV_HEALER_SHA256,
    PROV_GAPS: PROV_GAPS_SHA256,
    PROV_REPORT: PROV_REPORT_SHA256,
    provisional.ANALYZER: PROV_ANALYZER_SHA256,
    census_prep.G2_PROVISIONAL_CSV: census_prep.G2_PROVISIONAL_CSV_SHA256,
    census_prep.MODULE_EXCEPTION_CSV: census_prep.MODULE_EXCEPTION_CSV_SHA256,
    census_prep.MULTIPLE_SIGNAL_CSV: census_prep.MULTIPLE_SIGNAL_CSV_SHA256,
    census_prep.FREEZE20_CSV: census_prep.FREEZE20_CSV_SHA256,
}

CELL_FIELDS = (
    "audit_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "seed",
    "provisional_primary_layer",
    "audited_primary_layer",
    "primary_layer_verdict",
    "provisional_secondary_layer",
    "audited_secondary_layer",
    "outcome_validity_verdict",
    "mechanism_verdict",
    "failure_chain_verdict",
    "citation_verdict",
    "healer_decision_verdict",
    "confidence_verdict",
    "l2_reverse_audit_verdict",
    "audit_findings",
    "required_correction",
    "correction_materiality",
    "requires_provisional_v2",
    "evidence_citations",
    "auditor_identity",
    "audit_timestamp",
)

FINDING_FIELDS = (
    "finding_id",
    "program_id",
    "task_id",
    "finding_type",
    "materiality",
    "summary",
    "required_correction",
    "affects_primary",
    "affects_healer",
    "requires_provisional_v2",
)

CITATION_FIELDS = (
    "program_id",
    "task_id",
    "citation_kind",
    "citation_path",
    "citation_locator",
    "resolvable",
    "supports_claim",
    "citation_verdict",
    "notes",
)


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


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _row(
    *,
    audited_primary: str,
    primary_verdict: str,
    audited_secondary: str,
    outcome_verdict: str,
    mechanism_verdict: str,
    failure_chain_verdict: str,
    citation_verdict: str,
    healer_verdict: str,
    confidence_verdict: str,
    l2_reverse: str,
    findings: str,
    required_correction: str,
    materiality: str,
    requires_v2: bool,
) -> dict[str, Any]:
    _require(primary_verdict in VALID_PRIMARY_VERDICT, f"bad primary verdict {primary_verdict}")
    for value in (
        outcome_verdict,
        mechanism_verdict,
        failure_chain_verdict,
        citation_verdict,
        healer_verdict,
        confidence_verdict,
        l2_reverse,
    ):
        _require(value in VALID_DIM, f"bad dim verdict {value}")
    _require(materiality in VALID_MATERIALITY, f"bad materiality {materiality}")
    if primary_verdict == "CHALLENGED":
        _require(materiality == "MATERIAL", "challenged primary must be MATERIAL")
        _require(requires_v2, "challenged primary requires provisional v2")
        _require(bool(required_correction), "challenge requires correction text")
    return {
        "audited_primary_layer": audited_primary,
        "primary_layer_verdict": primary_verdict,
        "audited_secondary_layer": audited_secondary,
        "outcome_validity_verdict": outcome_verdict,
        "mechanism_verdict": mechanism_verdict,
        "failure_chain_verdict": failure_chain_verdict,
        "citation_verdict": citation_verdict,
        "healer_decision_verdict": healer_verdict,
        "confidence_verdict": confidence_verdict,
        "l2_reverse_audit_verdict": l2_reverse,
        "audit_findings": findings,
        "required_correction": required_correction,
        "correction_materiality": materiality,
        "requires_provisional_v2": str(requires_v2).lower(),
    }


# Deterministic per-program audit judgments after re-reading raw source + public contract.
AUDIT: dict[str, dict[str, Any]] = {
    # 1 Mbpp/769 — Diff order/content ≠ public list.
    "0c9f29239bdf609a6306524184cfbb830eeb41becd9d31709931fb300234c7a3": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Static expansion of list1-order filter yields [10,15,20,30] vs public "
            "[10,20,30,15]. Entry/signature OK; not L2. Tag incorrect_formula is slightly "
            "generic for ordering/difference semantics but strength CONFIRMED is acceptable."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 2 Mbpp/748 — leading space.
    "0f51d44f44faf38d9fbe794eb4c86a316809d300c9a5e206289d459bb71cabbf": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "First-capital branch inserts leading space for 'Python' → ' Python' ≠ public. "
            "No upstream L2. abstain correct."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 3 Mbpp/125 — Kadane polarity; hand-trace max_diff=2≠6.
    "151a1b3981da65abb7a94e2b2acac6491de4d6ad470da3c006f94b9a85273346": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Hand-trace of +1/-1 Kadane on public string yields 2≠6 without executing "
            "candidate as a program. Reinforces HIGH L5; not FAIL→L5 alone."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 4 Mbpp/742 — tetrahedron formula.
    "165c873221f996a992adfe426b96e62865dddc2407ce93ba89df3ea882dfac54": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Closed-form a²(√3/4+√6)≈25.94 ≠ public ≈15.588=a²√3. L2 reverse negative.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 5 Mbpp/287 UNRESOLVED
    "2c7db8ef79f3fb6f4877e45429a281e98b645f377f94b6d7912fb3d66f5847df": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Public square_Sum(2)==20 matched by loop; module assert residue not root cause. "
            "plus_fail cannot close L2/L5. ADJUDICATED+UNRESOLVED correct."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 6 Mbpp/410 seed55
    "3b027c95ed6970ead1bf34a58e5e5968a842375728129f12e3233a5ef00aed89": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public min==2 matched; no L2 shape/signature breach; plus_fail unresolved.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 7 Mbpp/427 seed22
    "5bf8a1f3934680a03fdc52a96fcca133f19f3a6885bcc6c4f81bd72ef2bdc6b4": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public date rewrite matched; packaging assert not L2 root; plus_fail unresolved.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 8 Mbpp/572
    "643332a7c66f839f75e24546129bca2d4aacf4cdbd005fce6765c2e811855238": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Dedupe → [1,2,3,4,5] vs public unique-count [1,4,5]. Clear L5; abstain OK.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 9 Mbpp/427 seed11
    "81cd6f1d055d47e781e3d08c914571b1959ebc39655a00f7ecfd110508503b4e": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Distinct source; public example matched; plus_fail unresolved; no L2.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 10 Mbpp/237
    "94ad97956f46bf1c8310acc9ba772d28e446fd47a066ac3a10c19733cdb80eb5": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Counter keeps order-sensitive keys; public merges reversed pairs. L5 closed. "
            "abstain (not conditional/eligible) matches v3.1 uniqueness/safety bar."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 11 Mbpp/410 seed44
    "ae0ea3edc7597b91f18d21dae1503c2333353a0b9686af9742afd8e1f056e10a": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public min matched; empty-list ValueError not exercised by public example; unresolved OK.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 12 Mbpp/16 seed44
    "bbcfbf7cb6786406b7dde275f718e2fcc2b980043166bfc200703d5cbef2b8dc": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public True matched; no signature/shape L2; plus_fail unresolved.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 13 Mbpp/138
    "bce7d06fe15d627115b96c241688d603b61450245867becd7f426917dfcfa2a9": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Public n=10→True path satisfied; bit-loop looks nonstandard but not publicly "
            "falsified. Minimal diagnostic=observe first failing base/plus return/exception "
            "without oracle. Keep UNRESOLVED+abstain."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 14 Mbpp/103 — MATERIAL: static DP leaves A[3][1]=0 ≠ 4.
    "bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b": _row(
        audited_primary="L5",
        primary_verdict="CHALLENGED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="CHALLENGED",
        failure_chain_verdict="CHALLENGED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="CHALLENGED",
        l2_reverse="AFFIRMED",
        findings=(
            "MATERIAL: nested loops never write A[3][1]; return A[n][m] remains 0, but public "
            "assert eulerian_num(3,1)==4. Static table expansion closes L5 without executing "
            "the candidate module. Provisional UNRESOLVED/LOW understates available public proof. "
            "Healer abstain remains correct (algorithm reconstruction)."
        ),
        required_correction=(
            "provisional v2: primary_layer UNRESOLVED→L5; confidence LOW→HIGH; "
            "replace unresolved_reason_code with empty; set mechanism incorrect_formula/"
            "algorithm_reconstruction_required to CONFIRMED with static A[3][1]=0 proof; "
            "rewrite failure_chain to public_assert_mismatch; keep healer=abstain; "
            "remove from unresolved_evidence_gaps."
        ),
        materiality="MATERIAL",
        requires_v2=True,
    ),
    # 15 Mbpp/16 seed33
    "cefff3d8a490047c757f7779c27204cf684a5b89df2223e5b7b447475b3f30af": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public True matched; plus_fail unresolved; no L2.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 16 Mbpp/581
    "d6cc3d6bdcc0be8b24448e7ba5b9808a9e505adf3b7dccbde8d30259c2d18cad": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="base²+base*slant≈21.82≠33. Formula L5 closed; abstain OK.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 17 Mbpp/118
    "da3b306e10fbd0e391950f9383ce978a7f07519334207d52f0738fadb1c4b7f6": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="s.split() matches public list; packaging assert not L2 root; plus_fail unresolved.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 18 Mbpp/14
    "e762c7d5362d7c213d760547ce6d9f8bce9b515216b1b80877c78733f20520af": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="a*b*c//2==240 matches public; plus_fail unresolved; no L2.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 19 Mbpp/721
    "ece76238dc23e4c6ac96b346c685f1846406516726a1310a5427ae189f79cad6": _row(
        audited_primary="L5",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings=(
            "Divides by n; integer path-sum/n cannot equal 5.2 (5.2*3 non-integer), while "
            "2n-1=5 fits 26/5=5.2. Strong static L5; abstain OK (max-sum≠max-average caveat)."
        ),
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
    # 20 Mbpp/16 seed11
    "fb762e37725ef76332c7c76243702f91d0378326ba55e4bba0db5890ecbc0cc1": _row(
        audited_primary="UNRESOLVED",
        primary_verdict="AFFIRMED",
        audited_secondary="",
        outcome_verdict="AFFIRMED",
        mechanism_verdict="AFFIRMED",
        failure_chain_verdict="AFFIRMED",
        citation_verdict="AFFIRMED",
        healer_verdict="AFFIRMED",
        confidence_verdict="AFFIRMED",
        l2_reverse="AFFIRMED",
        findings="Public True matched; plus_fail unresolved; no L2.",
        required_correction="",
        materiality="NONE",
        requires_v2=False,
    ),
}


def _static_contract_check(source: str, entry_point: str) -> dict[str, Any]:
    tree = ast.parse(source)
    defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
    ]
    yields = False
    if defs:
        yields = any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(defs[0]))
    module_asserts = sum(1 for node in tree.body if isinstance(node, ast.Assert))
    return {
        "entry_defs": len(defs),
        "yields": yields,
        "module_asserts": module_asserts,
        "parse_ok": True,
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    records = _read_csv(repo / PROV_RECORDS)
    roster = _read_csv(repo / PROV_ROSTER)
    next20 = _read_csv(repo / NEXT20)
    summary = json.loads((repo / PROV_SUMMARY).read_text(encoding="utf-8"))
    tasks = {row["task_id"]: row for row in _read_jsonl(repo / preparation.TASKS)}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }

    _require(len(records) == TARGET_CELLS, "provisional records drift")
    _require(len(roster) == TARGET_CELLS, "provisional roster drift")
    _require(len(next20) == TARGET_CELLS, "next20 drift")
    _require(summary["primary_layer_distribution"] == {"L5": 8, "UNRESOLVED": 12}, "primary summary drift")
    _require(summary["healer_eligibility_distribution"] == {"abstain": 20}, "healer summary drift")
    _require(summary["true_adjudicated_L2_count"] == 0, "L2 summary drift")
    _require(set(AUDIT) == {row["program_id"] for row in records}, "AUDIT keys must match records")
    _require(
        [row["program_id"] for row in records] == [row["program_id"] for row in next20],
        "records/next20 order identity drift",
    )

    cell_rows: list[dict[str, str]] = []
    finding_rows: list[dict[str, str]] = []
    citation_rows: list[dict[str, str]] = []
    finding_id = 0

    for rank, rec in enumerate(records, 1):
        pid = rec["program_id"]
        audit = AUDIT[pid]
        task = tasks[rec["task_id"]]
        journal = journals[pid]
        source = journal["evaluation_source"]
        _require(_sha(source.encode("utf-8")) == rec["source_sha256"], f"source sha mismatch {pid}")
        contract = _static_contract_check(source, str(task["entry_point"]))
        _require(contract["parse_ok"] and contract["entry_defs"] == 1, f"entry parse drift {pid}")
        _require(not contract["yields"], f"unexpected generator {pid}")

        citations = json.loads(rec["evidence_citations"])
        for item in citations:
            path = repo / item["path"] if not Path(item["path"]).is_absolute() else Path(item["path"])
            resolvable = path.is_file()
            citation_rows.append(
                {
                    "program_id": pid,
                    "task_id": rec["task_id"],
                    "citation_kind": item.get("kind", ""),
                    "citation_path": item.get("path", ""),
                    "citation_locator": item.get("locator", ""),
                    "resolvable": str(resolvable).lower(),
                    "supports_claim": "true" if resolvable else "false",
                    "citation_verdict": "AFFIRMED" if resolvable else "CHALLENGED",
                    "notes": "" if resolvable else "citation path missing",
                }
            )
            _require(resolvable, f"unresolvable citation for {pid}: {item}")

        cell_rows.append(
            {
                "audit_rank": str(rank),
                "cell_id": rec["cell_id"],
                "program_id": pid,
                "source_sha256": rec["source_sha256"],
                "task_id": rec["task_id"],
                "seed": rec["seed"],
                "provisional_primary_layer": rec["primary_layer"],
                "audited_primary_layer": audit["audited_primary_layer"],
                "primary_layer_verdict": audit["primary_layer_verdict"],
                "provisional_secondary_layer": rec["secondary_layer"],
                "audited_secondary_layer": audit["audited_secondary_layer"],
                "outcome_validity_verdict": audit["outcome_validity_verdict"],
                "mechanism_verdict": audit["mechanism_verdict"],
                "failure_chain_verdict": audit["failure_chain_verdict"],
                "citation_verdict": audit["citation_verdict"],
                "healer_decision_verdict": audit["healer_decision_verdict"],
                "confidence_verdict": audit["confidence_verdict"],
                "l2_reverse_audit_verdict": audit["l2_reverse_audit_verdict"],
                "audit_findings": audit["audit_findings"],
                "required_correction": audit["required_correction"],
                "correction_materiality": audit["correction_materiality"],
                "requires_provisional_v2": audit["requires_provisional_v2"],
                "evidence_citations": rec["evidence_citations"],
                "auditor_identity": AUDITOR_IDENTITY,
                "audit_timestamp": AUDIT_TIMESTAMP,
            }
        )

        if audit["correction_materiality"] != "NONE" or audit["primary_layer_verdict"] != "AFFIRMED":
            finding_id += 1
            finding_rows.append(
                {
                    "finding_id": f"F{finding_id:03d}",
                    "program_id": pid,
                    "task_id": rec["task_id"],
                    "finding_type": audit["primary_layer_verdict"],
                    "materiality": audit["correction_materiality"],
                    "summary": audit["audit_findings"],
                    "required_correction": audit["required_correction"],
                    "affects_primary": str(audit["primary_layer_verdict"] == "CHALLENGED").lower(),
                    "affects_healer": str(audit["healer_decision_verdict"] == "CHALLENGED").lower(),
                    "requires_provisional_v2": audit["requires_provisional_v2"],
                }
            )

    # L2=0 global reverse finding (informational NONE).
    finding_id += 1
    finding_rows.append(
        {
            "finding_id": f"F{finding_id:03d}",
            "program_id": "(batch)",
            "task_id": "(batch)",
            "finding_type": "L2_REVERSE_AUDIT",
            "materiality": "NONE",
            "summary": (
                "All 20 cells have exact expected entry point, no generator/list conflict, "
                "and no public signature/shape violation sufficient to explain failure. "
                "Contract-related planning signals were review clues only; unique-entry and "
                "return_shape signals were correctly rejected as root causes. L2=0 stands."
            ),
            "required_correction": "",
            "affects_primary": "false",
            "affects_healer": "false",
            "requires_provisional_v2": "false",
        }
    )

    primary_verdicts = Counter(row["primary_layer_verdict"] for row in cell_rows)
    materiality = Counter(row["correction_materiality"] for row in cell_rows)
    transition: Counter[str] = Counter()
    for row in cell_rows:
        transition[f"{row['provisional_primary_layer']}→{row['audited_primary_layer']}"] += 1

    mech_status = Counter()
    for rec in records:
        for item in json.loads(rec["mechanism_tags_json"]):
            mech_status[item["status"]] += 1

    needs_v2 = [row for row in cell_rows if row["requires_provisional_v2"] == "true"]
    challenged = [row for row in cell_rows if row["primary_layer_verdict"] == "CHALLENGED"]
    material_findings = [row for row in finding_rows if row["materiality"] == "MATERIAL"]

    if material_findings or challenged:
        overall = "POST_ADJUDICATION_REVISION_REQUIRED"
        freeze_ready = False
    else:
        overall = "READY_TO_PLAN_FREEZE_20_CELL_BATCH01"
        freeze_ready = True

    l5_cells = [row for row in cell_rows if row["provisional_primary_layer"] == "L5"]
    unresolved_cells = [row for row in cell_rows if row["provisional_primary_layer"] == "UNRESOLVED"]

    summary_out = {
        "status": STATUS,
        "overall_verdict": overall,
        "ready_to_plan_freeze": freeze_ready,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in cell_rows}),
        "unique_source_sha256": len({row["source_sha256"] for row in cell_rows}),
        "unique_task_id": len({row["task_id"] for row in cell_rows}),
        "primary_layer_verdict_distribution": dict(sorted(primary_verdicts.items())),
        "correction_materiality_distribution": dict(sorted(materiality.items())),
        "layer_transition_counts": dict(sorted(transition.items())),
        "provisional_primary_distribution": summary["primary_layer_distribution"],
        "l5_cells_audited": len(l5_cells),
        "l5_affirmed": sum(1 for row in l5_cells if row["primary_layer_verdict"] == "AFFIRMED"),
        "l5_challenged": sum(1 for row in l5_cells if row["primary_layer_verdict"] == "CHALLENGED"),
        "unresolved_cells_audited": len(unresolved_cells),
        "unresolved_affirmed": sum(
            1 for row in unresolved_cells if row["primary_layer_verdict"] == "AFFIRMED"
        ),
        "unresolved_challenged": sum(
            1 for row in unresolved_cells if row["primary_layer_verdict"] == "CHALLENGED"
        ),
        "l2_reverse_audit": {
            "provisional_L2": 0,
            "audited_true_L2": 0,
            "verdict": "AFFIRMED_L2_EQUALS_ZERO",
            "rationale": (
                "Planning contract signals ≠ adjudicated L2. All expected entry points present "
                "and unique; no generator-vs-list or public shape breach explaining failure."
            ),
        },
        "healer_audit": {
            "provisional_abstain": 20,
            "eligible_candidates_found": 0,
            "conditional_candidates_found": 0,
            "abstain_affirmed": 20,
            "abstain_challenged": 0,
        },
        "mechanism_strength_observed_in_provisional": dict(sorted(mech_status.items())),
        "citation_audit": {
            "citations_checked": len(citation_rows),
            "resolvable": sum(1 for row in citation_rows if row["resolvable"] == "true"),
            "unresolvable": sum(1 for row in citation_rows if row["resolvable"] == "false"),
        },
        "cells_requiring_provisional_v2": [row["program_id"] for row in needs_v2],
        "material_finding_count": len(material_findings),
        "editorial_finding_count": sum(1 for row in finding_rows if row["materiality"] == "EDITORIAL"),
        "none_materiality_cells": materiality.get("NONE", 0),
    }

    layer_matrix = {
        "counts": dict(sorted(transition.items())),
        "note": "audited_primary is audit judgment only; provisional v1 not rewritten",
    }

    mechanism_audit = {
        "provisional_by_status": dict(sorted(mech_status.items())),
        "expected_provisional_by_status": {
            "CONFIRMED": 32,
            "SUPPORTED": 15,
            "SUSPECTED": 16,
            "REJECTED": 29,
        },
        "status_total_match": mech_status == Counter({"CONFIRMED": 32, "SUPPORTED": 15, "SUSPECTED": 16, "REJECTED": 29}),
        "material_mechanism_challenges": [
            {
                "program_id": "bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b",
                "task_id": "Mbpp/103",
                "issue": "incorrect_formula/algorithm tags under-strength as SUSPECTED; should be CONFIRMED under L5",
            }
        ],
        "rejected_fallacies_affirmed": [
            "unique entry signal → entry-point error",
            "return_shape planning signal → L2",
            "evaluator FAIL → L5",
            "plus_fail → L5",
        ],
    }

    healer_audit = {
        "eligible": 0,
        "conditional": 0,
        "abstain": 20,
        "reverse_scan_found_safe_eligible": False,
        "reverse_scan_found_safe_conditional": False,
        "verdict": "ABSTAIN_20_AFFIRMED",
        "note": "No unique contract-local safe repair across batch; Mbpp/103 challenge keeps abstain.",
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
        "cell_rows": cell_rows,
        "finding_rows": finding_rows,
        "citation_rows": citation_rows,
        "summary": summary_out,
        "layer_matrix": layer_matrix,
        "mechanism_audit": mechanism_audit,
        "healer_audit": healer_audit,
        "execution_counts": execution_counts,
        "roster_rows": roster,
    }


def _report(analysis: dict[str, Any]) -> str:
    s = analysis["summary"]
    lines = [
        "# Candidate B r003 taxonomy v3.1：batch01 20-cell post-adjudication audit v1",
        "",
        f"**狀態：`{STATUS}`**",
        f"**總評：`{s['overall_verdict']}`**",
        "",
        "## 範圍",
        "",
        "- 僅稽核 provisional v1；不修改 provisional／census／next20／frozen97。",
        "- 不執行 candidate／tests／EvalPlus／diagnostics／Healer／外部模型。",
        "",
        "## 結果摘要",
        "",
        f"- primary verdict：{s['primary_layer_verdict_distribution']}",
        f"- materiality：{s['correction_materiality_distribution']}",
        f"- transition：{s['layer_transition_counts']}",
        f"- L5 affirmed/challenged：{s['l5_affirmed']}/{s['l5_challenged']}",
        f"- UNRESOLVED affirmed/challenged：{s['unresolved_affirmed']}/{s['unresolved_challenged']}",
        f"- L2 reverse：{s['l2_reverse_audit']['verdict']}",
        f"- healer：{s['healer_audit']}",
        f"- cells requiring provisional v2：{s['cells_requiring_provisional_v2']}",
        "",
        "## MATERIAL finding",
        "",
        "- Mbpp/103 (`bfa80269…`)：靜態 DP 展開顯示 `A[3][1]` 從未寫入，回傳 0≠公開 assert 4。",
        "  建議 provisional v2：UNRESOLVED→L5、confidence LOW→HIGH、healer 維持 abstain。",
        "",
        "## 為何 contract-signal 批仍可 L2=0",
        "",
        "- 20 格預期 entry point 皆存在且唯一；無 generator/list 衝突；無足以解釋失敗的公開 shape／signature 違約。",
        "- planning signal 只是審查線索；unique-entry 與 return_shape 已被正確 REJECTED 作為根因。",
        "",
        "## 停止點",
        "",
        "- 不修改 provisional v1；不建立 v2／freeze／commit／push（本輪）。",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    cell_bytes = _csv_bytes(CELL_FIELDS, analysis["cell_rows"])
    finding_bytes = _csv_bytes(FINDING_FIELDS, analysis["finding_rows"])
    citation_bytes = _csv_bytes(CITATION_FIELDS, analysis["citation_rows"])
    roster_bytes = _csv_bytes(
        (
            "audit_rank",
            "cell_id",
            "program_id",
            "source_sha256",
            "task_id",
            "seed",
            "provisional_primary_layer",
            "primary_layer_verdict",
            "correction_materiality",
            "requires_provisional_v2",
        ),
        [
            {
                "audit_rank": row["audit_rank"],
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "provisional_primary_layer": row["provisional_primary_layer"],
                "primary_layer_verdict": row["primary_layer_verdict"],
                "correction_materiality": row["correction_materiality"],
                "requires_provisional_v2": row["requires_provisional_v2"],
            }
            for row in analysis["cell_rows"]
        ],
    )
    summary_bytes = _json_bytes(analysis["summary"])
    matrix_bytes = _json_bytes(analysis["layer_matrix"])
    mech_bytes = _json_bytes(analysis["mechanism_audit"])
    healer_bytes = _json_bytes(analysis["healer_audit"])
    execution_bytes = _json_bytes(analysis["execution_counts"])
    report_bytes = _report(analysis).encode("utf-8")

    outputs_wo = {
        "audit_roster.csv": roster_bytes,
        "per_cell_audit_records.csv": cell_bytes,
        "audit_findings.csv": finding_bytes,
        "audit_summary.json": summary_bytes,
        "layer_transition_matrix.json": matrix_bytes,
        "mechanism_strength_audit.json": mech_bytes,
        "healer_decision_audit.json": healer_bytes,
        "citation_audit.csv": citation_bytes,
        "post_adjudication_audit_report_zh.md": report_bytes,
        "execution_counts.json": execution_bytes,
    }
    outputs_sha = {name: _sha(data) for name, data in outputs_wo.items()}

    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "overall_verdict": analysis["summary"]["overall_verdict"],
        "provisional_manifest_sha256": PROV_MANIFEST_SHA256,
        "provisional_records_sha256": PROV_RECORDS_SHA256,
        "provisional_roster_sha256": PROV_ROSTER_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "census_manifest_sha256": CENSUS_MANIFEST_SHA256,
        "taxonomy_v31_planning_reference": {
            "sha256": V31_SHA256,
            "status": V31_STATUS,
        },
        "cells_requiring_provisional_v2": analysis["summary"]["cells_requiring_provisional_v2"],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "auditor_identity": AUDITOR_IDENTITY,
        "audit_timestamp": AUDIT_TIMESTAMP,
        "provisional_v1_modified": False,
        "provisional_v2_created": False,
        "frozen_marker_written": False,
        **analysis["execution_counts"],
    }
    provenance_bytes = _json_bytes(provenance)
    outputs_wo["provenance.json"] = provenance_bytes
    outputs_sha["provenance.json"] = _sha(provenance_bytes)

    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "overall_verdict": analysis["summary"]["overall_verdict"],
        "ready_to_plan_freeze": analysis["summary"]["ready_to_plan_freeze"],
        "cells": TARGET_CELLS,
        "provisional_manifest_sha256": PROV_MANIFEST_SHA256,
        "provisional_records_sha256": PROV_RECORDS_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "primary_layer_verdict_distribution": analysis["summary"]["primary_layer_verdict_distribution"],
        "correction_materiality_distribution": analysis["summary"]["correction_materiality_distribution"],
        "cells_requiring_provisional_v2": analysis["summary"]["cells_requiring_provisional_v2"],
        "outputs_sha256_excluding_manifest": outputs_sha,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "provisional_v1_modified": False,
        "frozen_marker_written": False,
        **analysis["execution_counts"],
    }
    outputs = dict(outputs_wo)
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
    print(f"verdict={manifest['overall_verdict']}")
    print(f"v2_cells={manifest['cells_requiring_provisional_v2']}")


if __name__ == "__main__":
    main()
