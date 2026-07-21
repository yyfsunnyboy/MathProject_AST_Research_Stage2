#!/usr/bin/env python3
"""Independent post-adjudication re-audit v2 for remaining101 batch01 provisional v2.

POST_ADJUDICATION_REAUDIT_V2_NOT_FREEZE

Verifies provisional v2 correctly applied audit v1's single MATERIAL correction
(Mbpp/103). Does not modify provisional v1/v2, audit v1, census, next20, or
frozen97. Does not execute candidates, tests, diagnostics, Healer, or models.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import (
        prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1,
    )
    from scripts import (
        adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as provisional_v2,
    )
    from scripts import (
        audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1 as census_prep
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v1 as provisional_v1
    import adjudicate_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_provisional_v2 as provisional_v2
    import audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_v1 as audit_v1


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2"
)
START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "POST_ADJUDICATION_REAUDIT_V2_NOT_FREEZE"
ANALYZER = Path(
    "scripts/audit_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_post_adjudication_reaudit_v2.py"
)
AUDITOR_IDENTITY = "taxonomy_v31_batch01_post_adjudication_reaudit_v2_static_auditor"
AUDIT_TIMESTAMP = "2026-07-21T15:09:00+08:00"

TARGET_CELLS = 20
TARGET_PROGRAM_ID = provisional_v2.TARGET_PROGRAM_ID
TARGET_TASK_ID = provisional_v2.TARGET_TASK_ID
TARGET_SOURCE_SHA256 = provisional_v2.TARGET_SOURCE_SHA256

V1_DIR = provisional_v1.OUTPUT_RELATIVE
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_ROSTER = V1_DIR / "adjudication_roster.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_RECORDS_SHA256 = "e08f1eab72275d7c37884883b1a439438daee6a2be0d8df408ba758b2364990b"
V1_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
V1_MANIFEST_SHA256 = "710ef4fd707291db650e5b14d5594ed7920f1a9c2370ee3d5cde2f09a24a627e"

V2_DIR = provisional_v2.OUTPUT_RELATIVE
V2_RECORDS = V2_DIR / "adjudication_records.csv"
V2_ROSTER = V2_DIR / "adjudication_roster.csv"
V2_SUMMARY = V2_DIR / "adjudication_summary.json"
V2_MANIFEST = V2_DIR / "manifest.json"
V2_PROVENANCE = V2_DIR / "provenance.json"
V2_EXECUTION = V2_DIR / "execution_counts.json"
V2_MECHANISM = V2_DIR / "mechanism_counts.json"
V2_MECH_TRANS = V2_DIR / "mechanism_transition.json"
V2_REV_TRANS = V2_DIR / "revision_transition.json"
V2_GAPS = V2_DIR / "unresolved_evidence_gaps.csv"
V2_HEALER = V2_DIR / "healer_eligibility_summary.json"
V2_REPORT = V2_DIR / "adjudication_report_zh.md"

V2_RECORDS_SHA256 = "4f4d7479050b4a7bab8b0384169f5407331d720a33a3af47d2f45477a4ef6596"
V2_ROSTER_SHA256 = "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533"
V2_SUMMARY_SHA256 = "8e2d1893cd7df3d1c29093aed15b12b5a9222d2e9e8296c654af572f9102e809"
V2_MANIFEST_SHA256 = "30af6d5deaacfc0400e71936b532b5b52987f28f2ce2a04ea2da478a55e88d47"
V2_PROVENANCE_SHA256 = "3fa91d39eb7a270239a1abfe9356762e8a4ba6bac2c9b0f54637abef6983aef7"
V2_EXECUTION_SHA256 = "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7"
V2_MECHANISM_SHA256 = "8b956f69eeae34572f45201973d5639cf5b39f4f169fd54dc8006cf99ab7d06e"
V2_MECH_TRANS_SHA256 = "63f1cc216e4473b956474fafdadb27a61dabf66567ef3bc85b3e67c32ff9b983"
V2_REV_TRANS_SHA256 = "a79505f5cc0f69616ddf6e2fe04a21df67d9ce2158b47728da427f20aad799d9"
V2_GAPS_SHA256 = "4c1d7a72db70444e4fe032f33f65dc42795c17565543c5c420c15eec99221c93"
V2_HEALER_SHA256 = "5fd1b3483b7be86ec81b629ceba9337ba72cc59c610003a0d5291699549d7cc8"
V2_REPORT_SHA256 = "f9563936e8dd54c86d1cbb40e3848f1e1abd06fee6b2ff2391ab80b19b418050"
V2_ANALYZER_SHA256 = "34fdecfc7b197bed7ca271eb7a075990092f409855a186b212e6df685e17235e"

AUDIT_DIR = audit_v1.OUTPUT_RELATIVE
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_SUMMARY = AUDIT_DIR / "audit_summary.json"
AUDIT_RECORDS = AUDIT_DIR / "per_cell_audit_records.csv"
AUDIT_FINDINGS = AUDIT_DIR / "audit_findings.csv"
AUDIT_MANIFEST_SHA256 = "37438e79a8aa5ac68edafa5291c5c0601085dbdf96b3a92015e2b4de20905adf"
AUDIT_SUMMARY_SHA256 = "96df5df91f27e211715995d4005d65490999b955f1bfca2828fce4967eac17eb"
AUDIT_RECORDS_SHA256 = "997b7ff0bbf588c000a794f4b2f96dafbcb643cbafb12eb88eb1500dd3802ebe"
AUDIT_FINDINGS_SHA256 = "ab33751e000136da4713b24292b388979e9ed641f492cac366dad3c32c30fb92"
AUDIT_ANALYZER_SHA256 = "27190416b88eaf3a7777337a98b34b5da5b6f7643888c9b55f9be03483994863"

CENSUS_DIR = census_prep.OUTPUT_RELATIVE
NEXT20 = CENSUS_DIR / "next_adjudication_batch_roster.csv"
REMAINING101 = CENSUS_DIR / "remaining101_roster.csv"
CENSUS_MANIFEST = CENSUS_DIR / "manifest.json"
NEXT20_SHA256 = "a22f086ba7d61995de98dafd57edcbdcb01fe46e780bd595163a6eabf813eb91"
REMAINING101_SHA256 = "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6"
CENSUS_MANIFEST_SHA256 = "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd"

SEMANTIC_FIELDS = provisional_v2.SEMANTIC_FIELDS
VALID_VERDICT = frozenset({"AFFIRMED", "CHALLENGED", "INSUFFICIENT_AUDIT_EVIDENCE"})
VALID_MATERIALITY = frozenset({"NONE", "EDITORIAL", "MATERIAL"})

RUNTIME_CLAIM_PATTERNS = (
    re.compile(r"\bran the candidate\b", re.I),
    re.compile(r"\bexecuted the candidate\b", re.I),
    re.compile(r"\bnew execution\b", re.I),
    re.compile(r"\bobserved at runtime\b", re.I),
    re.compile(r"\bimported the candidate\b", re.I),
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    NEXT20: NEXT20_SHA256,
    REMAINING101: REMAINING101_SHA256,
    CENSUS_MANIFEST: CENSUS_MANIFEST_SHA256,
    V1_RECORDS: V1_RECORDS_SHA256,
    V1_ROSTER: V1_ROSTER_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    provisional_v1.ANALYZER: provisional_v2.V1_ANALYZER_SHA256,
    AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
    AUDIT_SUMMARY: AUDIT_SUMMARY_SHA256,
    AUDIT_RECORDS: AUDIT_RECORDS_SHA256,
    AUDIT_FINDINGS: AUDIT_FINDINGS_SHA256,
    audit_v1.ANALYZER: AUDIT_ANALYZER_SHA256,
    V2_RECORDS: V2_RECORDS_SHA256,
    V2_ROSTER: V2_ROSTER_SHA256,
    V2_SUMMARY: V2_SUMMARY_SHA256,
    V2_MANIFEST: V2_MANIFEST_SHA256,
    V2_PROVENANCE: V2_PROVENANCE_SHA256,
    V2_EXECUTION: V2_EXECUTION_SHA256,
    V2_MECHANISM: V2_MECHANISM_SHA256,
    V2_MECH_TRANS: V2_MECH_TRANS_SHA256,
    V2_REV_TRANS: V2_REV_TRANS_SHA256,
    V2_GAPS: V2_GAPS_SHA256,
    V2_HEALER: V2_HEALER_SHA256,
    V2_REPORT: V2_REPORT_SHA256,
    provisional_v2.ANALYZER: V2_ANALYZER_SHA256,
    census_prep.G2_PROVISIONAL_CSV: census_prep.G2_PROVISIONAL_CSV_SHA256,
    census_prep.MODULE_EXCEPTION_CSV: census_prep.MODULE_EXCEPTION_CSV_SHA256,
    census_prep.MULTIPLE_SIGNAL_CSV: census_prep.MULTIPLE_SIGNAL_CSV_SHA256,
    census_prep.FREEZE20_CSV: census_prep.FREEZE20_CSV_SHA256,
}

CELL_FIELDS = (
    "reaudit_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "seed",
    "v1_primary_layer",
    "v2_primary_layer",
    "semantic_change",
    "cell_verdict",
    "mbpp103_correction_ok",
    "failure_chain_static_ok",
    "mechanism_transition_ok",
    "healer_ok",
    "unresolved_fields_ok",
    "citation_ok",
    "audit_findings",
    "required_correction",
    "correction_materiality",
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
)


class ReauditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReauditError(message)


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


def _mech_map(row: dict[str, str]) -> dict[str, dict[str, str]]:
    return {item["tag"]: item for item in json.loads(row["mechanism_tags_json"])}


def _status_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for item in json.loads(row["mechanism_tags_json"]):
            counter[item["status"]] += 1
    return counter


def _claims_runtime_observation(text: str) -> bool:
    return any(pattern.search(text) for pattern in RUNTIME_CLAIM_PATTERNS)


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)

    audit_summary = json.loads((repo / AUDIT_SUMMARY).read_text(encoding="utf-8"))
    _require(
        audit_summary["overall_verdict"] == "POST_ADJUDICATION_REVISION_REQUIRED",
        "audit v1 verdict drift",
    )
    _require(
        audit_summary["cells_requiring_provisional_v2"] == [TARGET_PROGRAM_ID],
        "audit target cell drift",
    )

    v1_rows = _read_csv(repo / V1_RECORDS)
    v2_rows = _read_csv(repo / V2_RECORDS)
    v1_roster = _read_csv(repo / V1_ROSTER)
    v2_roster = _read_csv(repo / V2_ROSTER)
    next20 = _read_csv(repo / NEXT20)
    gaps = _read_csv(repo / V2_GAPS)
    v2_summary = json.loads((repo / V2_SUMMARY).read_text(encoding="utf-8"))

    _require(len(v1_rows) == TARGET_CELLS and len(v2_rows) == TARGET_CELLS, "cell count drift")
    _require(
        [row["program_id"] for row in v2_rows]
        == [row["program_id"] for row in next20]
        == [row["program_id"] for row in v1_rows],
        "identity order drift",
    )
    _require(
        [row["program_id"] for row in v2_roster] == [row["program_id"] for row in next20],
        "roster/next20 drift",
    )
    _require(len({row["source_sha256"] for row in v2_rows}) == TARGET_CELLS, "source uniqueness drift")

    cell_rows: list[dict[str, str]] = []
    finding_rows: list[dict[str, str]] = []
    semantic_diffs: list[dict[str, Any]] = []
    finding_id = 0
    material_count = 0

    for rank, (v1_row, v2_row) in enumerate(zip(v1_rows, v2_rows, strict=True), 1):
        pid = v2_row["program_id"]
        field_diffs = {
            field: {"from": v1_row.get(field, ""), "to": v2_row.get(field, "")}
            for field in SEMANTIC_FIELDS
            if v1_row.get(field, "") != v2_row.get(field, "")
        }
        changed = bool(field_diffs)
        if changed:
            semantic_diffs.append({"program_id": pid, "task_id": v2_row["task_id"], "diffs": field_diffs})

        cell_verdict = "AFFIRMED"
        materiality = "NONE"
        findings = "Semantic identity unchanged vs provisional v1."
        required = ""
        mbpp103_ok = "n/a"
        chain_ok = "n/a"
        mech_ok = "n/a"
        healer_ok = "true" if v2_row["healer_eligibility"] == "abstain" else "false"
        unresolved_ok = "n/a"
        citation_ok = "true"

        if pid != TARGET_PROGRAM_ID:
            if changed:
                cell_verdict = "CHALLENGED"
                materiality = "MATERIAL"
                findings = f"Unexpected semantic changes on non-target cell: {sorted(field_diffs)}"
                required = "Revert non-target cell to provisional v1 semantics."
                material_count += 1
            else:
                # unchanged UNRESOLVED must keep gaps
                if v2_row["primary_layer"] == "UNRESOLVED":
                    unresolved_ok = (
                        "true"
                        if v2_row["unresolved_reason_code"] and v2_row["evidence_missing"]
                        else "false"
                    )
                    if unresolved_ok == "false":
                        cell_verdict = "CHALLENGED"
                        materiality = "MATERIAL"
                        findings = "UNRESOLVED cell missing reason/gap fields."
                        required = "Restore unresolved reason/gap from v1."
                        material_count += 1
        else:
            mbpp103_ok = "true"
            checks = []
            if v2_row["source_sha256"] != TARGET_SOURCE_SHA256:
                mbpp103_ok = "false"
                checks.append("source sha mismatch")
            if not (
                v1_row["primary_layer"] == "UNRESOLVED"
                and v2_row["primary_layer"] == "L5"
                and v1_row["confidence"] == "LOW"
                and v2_row["confidence"] == "HIGH"
                and v2_row["secondary_layer"] == ""
                and v2_row["outcome_validity"] == "VALID_MODEL_OUTCOME"
                and v2_row["healer_eligibility"] == "abstain"
            ):
                mbpp103_ok = "false"
                checks.append("layer/confidence/healer/outcome mismatch vs audit requirement")
            if v2_row["unresolved_reason_code"] or v2_row["evidence_missing"] or v2_row["minimal_future_diagnostic"]:
                mbpp103_ok = "false"
                unresolved_ok = "false"
                checks.append("unresolved fields not cleared")
            else:
                unresolved_ok = "true"

            chain = v2_row["failure_chain"]
            static_markers = (
                "STATIC" in chain
                and "A[3][1]" in chain
                and "not a new candidate execution" in chain
                and "4" in chain
                and "L5" in chain
                and "abstain" in chain.lower()
            )
            runtime_claim = _claims_runtime_observation(chain) or _claims_runtime_observation(
                v2_row["evidence_summary"]
            )
            chain_ok = "true" if static_markers and not runtime_claim else "false"
            if chain_ok == "false":
                checks.append("failure_chain static/runtime distinction failed")

            m1 = _mech_map(v1_row)
            m2 = _mech_map(v2_row)
            expected = {
                "incorrect_formula": ("SUSPECTED", "CONFIRMED"),
                "algorithm_reconstruction_required": ("SUSPECTED", "CONFIRMED"),
                "public_examples_non_discriminating": ("SUPPORTED", "REJECTED"),
                "diagnostic_execution_required": ("CONFIRMED", "REJECTED"),
                "runtime_vs_semantic_not_closed": ("SUPPORTED", "REJECTED"),
                "return_shape_mismatch": ("SUSPECTED", "REJECTED"),
                "entry_point_unique_candidate": ("REJECTED", "REJECTED"),
            }
            mech_ok = "true"
            for tag, (old, new) in expected.items():
                if tag not in m1 or tag not in m2 or m1[tag]["status"] != old or m2[tag]["status"] != new:
                    mech_ok = "false"
                    checks.append(f"mechanism transition failed for {tag}")
                    break
            if set(m1) != set(m2):
                mech_ok = "false"
                checks.append("mechanism tag set changed unexpectedly")

            citations = json.loads(v2_row["evidence_citations"])
            has_audit_cite = any(
                item.get("kind") in {"post_adjudication_audit", "post_adjudication_finding"}
                for item in citations
            )
            if not has_audit_cite:
                citation_ok = "false"
                checks.append("missing audit citation")
            for item in citations:
                path = repo / item["path"]
                if not path.is_file():
                    citation_ok = "false"
                    checks.append(f"unresolvable citation {item['path']}")

            if checks:
                cell_verdict = "CHALLENGED"
                materiality = "MATERIAL"
                findings = "; ".join(checks)
                required = "Revise provisional v2 Mbpp/103 to match audit v1 MATERIAL correction."
                material_count += 1
                mbpp103_ok = "false"
            else:
                findings = (
                    "Mbpp/103 correctly implements audit v1 MATERIAL correction: "
                    "UNRESOLVED/LOW→L5/HIGH, STATIC DP proof, unresolved fields cleared, "
                    "healer abstain retained."
                )

        if healer_ok == "false" and materiality == "NONE":
            cell_verdict = "CHALLENGED"
            materiality = "MATERIAL"
            findings = "Healer decision is not abstain."
            required = "Set healer_eligibility=abstain."
            material_count += 1

        cell_rows.append(
            {
                "reaudit_rank": str(rank),
                "cell_id": v2_row["cell_id"],
                "program_id": pid,
                "source_sha256": v2_row["source_sha256"],
                "task_id": v2_row["task_id"],
                "seed": v2_row["seed"],
                "v1_primary_layer": v1_row["primary_layer"],
                "v2_primary_layer": v2_row["primary_layer"],
                "semantic_change": str(changed).lower(),
                "cell_verdict": cell_verdict,
                "mbpp103_correction_ok": mbpp103_ok,
                "failure_chain_static_ok": chain_ok,
                "mechanism_transition_ok": mech_ok,
                "healer_ok": healer_ok,
                "unresolved_fields_ok": unresolved_ok,
                "citation_ok": citation_ok,
                "audit_findings": findings,
                "required_correction": required,
                "correction_materiality": materiality,
                "auditor_identity": AUDITOR_IDENTITY,
                "audit_timestamp": AUDIT_TIMESTAMP,
            }
        )
        if materiality != "NONE":
            finding_id += 1
            finding_rows.append(
                {
                    "finding_id": f"R{finding_id:03d}",
                    "program_id": pid,
                    "task_id": v2_row["task_id"],
                    "finding_type": cell_verdict,
                    "materiality": materiality,
                    "summary": findings,
                    "required_correction": required,
                }
            )

    _require(len(semantic_diffs) == 1, f"expected exactly 1 changed cell, got {len(semantic_diffs)}")
    _require(semantic_diffs[0]["program_id"] == TARGET_PROGRAM_ID, "changed cell is not Mbpp/103")

    # Mechanism transition audit (tag-level for Mbpp/103 + global totals).
    v1_target = next(row for row in v1_rows if row["program_id"] == TARGET_PROGRAM_ID)
    v2_target = next(row for row in v2_rows if row["program_id"] == TARGET_PROGRAM_ID)
    m1 = _mech_map(v1_target)
    m2 = _mech_map(v2_target)
    tag_transitions = []
    for tag in sorted(set(m1) | set(m2)):
        old = m1.get(tag, {}).get("status", "ABSENT")
        new = m2.get(tag, {}).get("status", "ABSENT")
        reason = ""
        if tag in {"incorrect_formula", "algorithm_reconstruction_required"} and old == "SUSPECTED" and new == "CONFIRMED":
            reason = "STATIC A[3][1]=0 proof closes L5; audit required CONFIRMED"
        elif tag == "diagnostic_execution_required" and old == "CONFIRMED" and new == "REJECTED":
            reason = "diagnostics no longer required after static closure"
        elif tag in {"public_examples_non_discriminating", "runtime_vs_semantic_not_closed"} and old == "SUPPORTED" and new == "REJECTED":
            reason = "UNRESOLVED-binding tag contradicted by closed HIGH L5"
        elif tag == "return_shape_mismatch" and old == "SUSPECTED" and new == "REJECTED":
            reason = "planning signal not root cause after L5 closure"
        elif tag == "entry_point_unique_candidate" and old == new == "REJECTED":
            reason = "unchanged; entry point is not an error"
        else:
            reason = "unexpected or undocumented"
        tag_transitions.append(
            {
                "tag": tag,
                "v1_status": old,
                "v2_status": new,
                "transition": f"{old}→{new}",
                "reason": reason,
                "v1_note": m1.get(tag, {}).get("note", ""),
                "v2_note": m2.get(tag, {}).get("note", ""),
            }
        )

    v1_status = _status_counts(v1_rows)
    v2_status = _status_counts(v2_rows)
    c1 = Counter(item["status"] for item in m1.values())
    c2 = Counter(item["status"] for item in m2.values())
    local_delta = {
        status: int(c2.get(status, 0) - c1.get(status, 0))
        for status in sorted(set(c1) | set(c2))
    }
    expected_global = {
        status: int(v1_status.get(status, 0) + local_delta.get(status, 0))
        for status in ("CONFIRMED", "SUPPORTED", "SUSPECTED", "REJECTED")
    }
    totals_rebuild_ok = all(v2_status.get(k, 0) == expected_global[k] for k in expected_global)
    expected_totals = {
        "CONFIRMED": 33,
        "SUPPORTED": 13,
        "SUSPECTED": 13,
        "REJECTED": 33,
    }
    totals_match_reported = dict(v2_status) == expected_totals

    if not totals_rebuild_ok or not totals_match_reported:
        finding_id += 1
        material_count += 1
        finding_rows.append(
            {
                "finding_id": f"R{finding_id:03d}",
                "program_id": TARGET_PROGRAM_ID,
                "task_id": TARGET_TASK_ID,
                "finding_type": "MECHANISM_TOTALS",
                "materiality": "MATERIAL",
                "summary": (
                    f"Mechanism totals not reconstructible: v2={dict(v2_status)} "
                    f"expected_from_103_delta={expected_global}"
                ),
                "required_correction": "Fix mechanism tags/strength so totals rebuild from tag transitions.",
            }
        )

    # Stats from v2 records.
    primary = Counter(row["primary_layer"] for row in v2_rows)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    stats_ok = (
        primary == Counter({"L5": 9, "UNRESOLVED": 11})
        and confidence == Counter({"HIGH": 9, "LOW": 11})
        and healer == Counter({"abstain": 20})
        and outcome == Counter({"VALID_MODEL_OUTCOME": 20})
        and secondary == Counter({"(empty)": 20})
        and primary.get("L2", 0) == 0
        and len(gaps) == 11
        and TARGET_PROGRAM_ID not in {row["program_id"] for row in gaps}
        and all(row["unresolved_reason_code"] for row in gaps)
    )
    if not stats_ok:
        finding_id += 1
        material_count += 1
        finding_rows.append(
            {
                "finding_id": f"R{finding_id:03d}",
                "program_id": "(batch)",
                "task_id": "(batch)",
                "finding_type": "STATISTICS",
                "materiality": "MATERIAL",
                "summary": "Recomputed statistics do not match required v2 closure.",
                "required_correction": "Repair provisional v2 aggregates/records.",
            }
        )

    cell_verdicts = Counter(row["cell_verdict"] for row in cell_rows)
    materiality_counts = Counter(row["correction_materiality"] for row in cell_rows)
    if material_count == 0 and cell_verdicts.get("CHALLENGED", 0) == 0:
        overall = "READY_TO_FREEZE_BATCH01_20CELL_V2"
        freeze_ready = True
    else:
        overall = "POST_ADJUDICATION_V2_REVISION_REQUIRED"
        freeze_ready = False

    summary = {
        "status": STATUS,
        "overall_verdict": overall,
        "ready_to_freeze": freeze_ready,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in v2_rows}),
        "unique_source_sha256": len({row["source_sha256"] for row in v2_rows}),
        "unique_task_id": len({row["task_id"] for row in v2_rows}),
        "cell_verdict_distribution": dict(sorted(cell_verdicts.items())),
        "correction_materiality_distribution": dict(sorted(materiality_counts.items())),
        "semantic_changed_cells": len(semantic_diffs),
        "unchanged_cells": TARGET_CELLS - len(semantic_diffs),
        "mbpp103_program_id": TARGET_PROGRAM_ID,
        "mbpp103_source_sha256": TARGET_SOURCE_SHA256,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "unresolved_gaps": len(gaps),
        "mbpp103_in_unresolved_gaps": TARGET_PROGRAM_ID in {row["program_id"] for row in gaps},
        "material_finding_count": material_count,
        "v2_summary_matches_records": v2_summary["primary_layer_distribution"] == dict(sorted(primary.items())),
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
    }

    semantic_diff_audit = {
        "changed_cells": semantic_diffs,
        "unchanged_cells": 19,
        "only_mbpp103_changed": len(semantic_diffs) == 1
        and semantic_diffs[0]["program_id"] == TARGET_PROGRAM_ID,
    }

    mechanism_transition_audit = {
        "mbpp103_tag_transitions": tag_transitions,
        "v1_global_status": dict(sorted(v1_status.items())),
        "v2_global_status": dict(sorted(v2_status.items())),
        "mbpp103_local_status_delta": dict(sorted(local_delta.items())),
        "global_totals_rebuild_from_mbpp103_delta": expected_global,
        "totals_rebuild_ok": totals_rebuild_ok,
        "reported_expected_totals": expected_totals,
        "totals_match_reported_v2": totals_match_reported,
        "explanation": (
            "From Mbpp/103 only: SUSPECTED→CONFIRMED ×2 (+2 C, -2 Su); "
            "CONFIRMED→REJECTED ×1 (-1 C, +1 R); SUPPORTED→REJECTED ×2 (-2 S, +2 R); "
            "SUSPECTED→REJECTED ×1 (-1 Su, +1 R). Net: C+1, S-2, Su-3, R+4 → "
            "32/15/16/29 → 33/13/13/33."
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
        "cell_rows": cell_rows,
        "finding_rows": finding_rows,
        "summary": summary,
        "semantic_diff_audit": semantic_diff_audit,
        "mechanism_transition_audit": mechanism_transition_audit,
        "execution_counts": execution_counts,
        "v2_roster": v2_roster,
    }


def _report(analysis: dict[str, Any]) -> str:
    s = analysis["summary"]
    m = analysis["mechanism_transition_audit"]
    lines = [
        "# Candidate B r003 taxonomy v3.1：batch01 provisional v2 post-adjudication re-audit v2",
        "",
        f"**狀態：`{STATUS}`**",
        f"**總評：`{s['overall_verdict']}`**",
        "",
        "## 範圍",
        "",
        "- 僅稽核 provisional v2 是否正確落實 audit v1 唯一 MATERIAL correction（Mbpp/103）。",
        "- 不修改 v1／audit v1／v2／census／next20／frozen97；零執行。",
        "",
        "## 結果",
        "",
        f"- cell verdicts：{s['cell_verdict_distribution']}",
        f"- materiality：{s['correction_materiality_distribution']}",
        f"- semantic changed cells：{s['semantic_changed_cells']}（應為 1）",
        f"- primary：{s['primary_layer_distribution']}",
        f"- confidence：{s['confidence_distribution']}",
        f"- healer：{s['healer_eligibility_distribution']}",
        f"- unresolved gaps：{s['unresolved_gaps']}（不含 Mbpp/103={not s['mbpp103_in_unresolved_gaps']}）",
        "",
        "## Mechanism totals",
        "",
        f"- v1：{m['v1_global_status']}",
        f"- v2：{m['v2_global_status']}",
        f"- rebuild OK：{m['totals_rebuild_ok']}",
        f"- explanation：{m['explanation']}",
        "",
        "## 停止點",
        "",
        "- 不 freeze／commit／push；不開始其餘 81 格。",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    cell_bytes = _csv_bytes(CELL_FIELDS, analysis["cell_rows"])
    finding_bytes = _csv_bytes(FINDING_FIELDS, analysis["finding_rows"])
    roster_bytes = _csv_bytes(
        (
            "reaudit_rank",
            "cell_id",
            "program_id",
            "source_sha256",
            "task_id",
            "v1_primary_layer",
            "v2_primary_layer",
            "semantic_change",
            "cell_verdict",
            "correction_materiality",
        ),
        [
            {
                "reaudit_rank": row["reaudit_rank"],
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "v1_primary_layer": row["v1_primary_layer"],
                "v2_primary_layer": row["v2_primary_layer"],
                "semantic_change": row["semantic_change"],
                "cell_verdict": row["cell_verdict"],
                "correction_materiality": row["correction_materiality"],
            }
            for row in analysis["cell_rows"]
        ],
    )
    summary_bytes = _json_bytes(analysis["summary"])
    semantic_bytes = _json_bytes(analysis["semantic_diff_audit"])
    mech_bytes = _json_bytes(analysis["mechanism_transition_audit"])
    execution_bytes = _json_bytes(analysis["execution_counts"])
    report_bytes = _report(analysis).encode("utf-8")

    outputs_wo = {
        "reaudit_roster.csv": roster_bytes,
        "per_cell_reaudit_records.csv": cell_bytes,
        "reaudit_findings.csv": finding_bytes,
        "semantic_diff_audit.json": semantic_bytes,
        "mechanism_transition_audit.json": mech_bytes,
        "reaudit_summary.json": summary_bytes,
        "reaudit_report_zh.md": report_bytes,
        "execution_counts.json": execution_bytes,
    }
    outputs_sha = {name: _sha(data) for name, data in outputs_wo.items()}

    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "overall_verdict": analysis["summary"]["overall_verdict"],
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "provisional_v1_roster_sha256": V1_ROSTER_SHA256,
        "audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v2_roster_sha256": V2_ROSTER_SHA256,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "taxonomy_v31_reference_sha256": census_prep.V31_REFERENCE_SHA256,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "auditor_identity": AUDITOR_IDENTITY,
        "audit_timestamp": AUDIT_TIMESTAMP,
        "provisional_v1_modified": False,
        "audit_v1_modified": False,
        "provisional_v2_modified": False,
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
        "ready_to_freeze": analysis["summary"]["ready_to_freeze"],
        "cells": TARGET_CELLS,
        "provisional_v2_records_sha256": V2_RECORDS_SHA256,
        "provisional_v1_records_sha256": V1_RECORDS_SHA256,
        "audit_v1_manifest_sha256": AUDIT_MANIFEST_SHA256,
        "next20_roster_sha256": NEXT20_SHA256,
        "remaining101_roster_sha256": REMAINING101_SHA256,
        "cell_verdict_distribution": analysis["summary"]["cell_verdict_distribution"],
        "correction_materiality_distribution": analysis["summary"]["correction_materiality_distribution"],
        "material_finding_count": analysis["summary"]["material_finding_count"],
        "outputs_sha256_excluding_manifest": outputs_sha,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "provisional_v2_modified": False,
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
    print(f"ready_to_freeze={manifest['ready_to_freeze']}")
    print(f"material={manifest['material_finding_count']}")


if __name__ == "__main__":
    main()
