#!/usr/bin/env python3
"""Final freeze audit for remaining121 output/contract-shape provisional v2.

FINAL_FREEZE_AUDIT_NOT_FREEZE_COMMIT

Validates provisional v2 completeness and freeze readiness. Does not re-adjudicate,
overwrite any revision, execute programs, or call models.
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
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v2_final_freeze_audit_v1"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "FINAL_FREEZE_AUDIT_NOT_FREEZE_COMMIT"
ADJUDICATION_STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/audit_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v2_final_freeze_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v2_final_freeze_v1.py"
)

NEXT_BATCH_ROSTER = planning_prep.OUTPUT_RELATIVE / "next_batch_roster.csv"
NEXT_BATCH_ROSTER_SHA256 = "b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804"

MACHINE_CENSUS_MANIFEST = census_prep.OUTPUT_RELATIVE / "manifest.json"
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"

MULTIPLE_SIGNAL_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/manifest.json"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1"
)
V1_MANIFEST = V1_DIR / "manifest.json"
V1_CSV = V1_DIR / "ai_provisional_adjudication.csv"
V1_SUMMARY = V1_DIR / "adjudication_summary.json"
V1_SUMMARY_ZH = V1_DIR / "adjudication_summary_zh.md"
V1_CITATION = V1_DIR / "evidence_citation_audit.csv"
V1_CLOSURE = V1_DIR / "roster_closure_audit.csv"
V1_EXEC = V1_DIR / "execution_counts.json"
V1_PROV = V1_DIR / "provenance.json"
V1_FILE_SHA256: dict[Path, str] = {
    V1_MANIFEST: "548486f59c5a42ef03375ace981bbd7219c5f94ae0b374ac3be1c305805fbf8d",
    V1_CSV: "87bf9dd0715cac8581028c98ffff0c1d0c6a91154bbfffe9470f244fe741f4f7",
    V1_SUMMARY: "ecb9d6d934ef047f9362fa498c07842928f18c17c7e0d37593aa1566d0afbbdb",
    V1_SUMMARY_ZH: "8307289e00c5c701eabf83761d9dab27464c99bb389d41d3b7690dd3b93e62ff",
    V1_CITATION: "41c0bf5dbb7f909e9be0e59f254dd80df7aa38ccda022d61503773f97f2a6824",
    V1_CLOSURE: "1d1c1836846cb0a574f73af0ab0fe8d47d6c8d2051b4c782c06939719f1e9cb2",
    V1_EXEC: "88c78805d447e3a2e2c44d775437be83107006c510f66032faf074d5e8ef65d2",
    V1_PROV: "86afc3657d6cf5396199d38fed129ed3247b944c90186ee2d5483f781418611d",
}

POST_AUDIT_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_post_adjudication_audit_v1/"
    "manifest.json"
)
POST_AUDIT_MANIFEST_SHA256 = (
    "73fc418fe9c15bc35ade4ebe208d436eea516ac89860a962e78bea173bc1b508"
)

V2_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2"
)
V2_MANIFEST = V2_DIR / "manifest.json"
V2_CSV = V2_DIR / "ai_provisional_adjudication.csv"
V2_DELTA = V2_DIR / "revision_delta_v1_to_v2.csv"
V2_CLARIFICATION = V2_DIR / "pre_audit_sufficiency_clarification_zh.md"
V2_CITATION = V2_DIR / "evidence_citation_audit.csv"
V2_CLOSURE = V2_DIR / "roster_closure_audit.csv"
V2_MANIFEST_SHA256 = "11f59ee2b9296db4a13a055354dd9e554bd287839e9a6cc1f1c1a5604d8f18e6"
V2_CSV_SHA256 = "7f89e457e5a3e19a8c13a0651feed0b71d27e3877653927c2360f37c5c119a78"
V2_DELTA_SHA256 = "3601b0d54cc025bf9ddbef5827b31ad051f851f093ac5ce1e3ed45abc73df421"
V2_CLARIFICATION_SHA256 = (
    "0eda165904a86e30803947c99b1fc6f2e6c1c7d696992d59c4bcea1edecdbd7a"
)

PRE_AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1"
)
PRE_AUDIT_MANIFEST = PRE_AUDIT_DIR / "manifest.json"
PRE_AUDIT_MANIFEST_SHA256 = (
    "76502df20b8cddbc765133500c68d6692fdb1ede20933a0730e27aeb1f323272"
)

G2_PROVISIONAL_CSV = planning_prep.G2_PROVISIONAL_CSV
MODULE_EXCEPTION_CSV = planning_prep.MODULE_EXCEPTION_CSV
MULTIPLE_SIGNAL_CSV = planning_prep.MULTIPLE_SIGNAL_CSV

TARGET_CELLS = 20
TARGET_UNIQUE_TASKS = 13
TARGET_UNIQUE_SOURCES = 20
EXPECTED_PRIMARY = {"UNRESOLVED": 12, "L5": 7, "L2": 1}
EXPECTED_HEALER = {"abstain": 20}
EXPECTED_CONFIDENCE = {"HIGH": 8, "LOW": 12}
APPROVED_PIDS = frozenset(
    {
        "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
        "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
    }
)
IMMUTABLE_FIELDS = (
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
    "confidence",
    "evidence_citations",
    "adjudication_identity",
    "evidence_summary",
    "adjudication_status",
)
MUTABLE_ALLOWED = frozenset({"healer_eligibility", "abstain_reason"})

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    POST_AUDIT_MANIFEST: POST_AUDIT_MANIFEST_SHA256,
    PRE_AUDIT_MANIFEST: PRE_AUDIT_MANIFEST_SHA256,
    V2_MANIFEST: V2_MANIFEST_SHA256,
    V2_CSV: V2_CSV_SHA256,
    V2_DELTA: V2_DELTA_SHA256,
    V2_CLARIFICATION: V2_CLARIFICATION_SHA256,
    **V1_FILE_SHA256,
}

FINAL_AUDIT_FIELDS = (
    "audit_rank",
    "program_id",
    "task_id",
    "source_sha256",
    "primary_layer",
    "healer_eligibility",
    "confidence",
    "failure_chain_ok",
    "citations_ok",
    "outcome_separated",
    "identity_status_ok",
    "unresolved_abstain_ok",
    "cell_verdict",
    "notes",
)

DELTA_CLOSURE_FIELDS = (
    "program_id",
    "field",
    "v1_value",
    "v2_value",
    "in_revision_delta",
    "approved",
    "closure_verdict",
)

ROSTER_SHA_FIELDS = (
    "check_id",
    "artifact_path",
    "expected_sha256",
    "observed_sha256",
    "match",
    "role",
)


class FreezeAuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeAuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _processed77(repo: Path) -> set[str]:
    ids: set[str] = set()
    for roster_path in (G2_PROVISIONAL_CSV, MODULE_EXCEPTION_CSV, MULTIPLE_SIGNAL_CSV):
        ids.update(row["program_id"] for row in _read_csv(repo / roster_path))
    return ids


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo / NEXT_BATCH_ROSTER)
    v1_rows = _read_csv(repo / V1_CSV)
    v2_rows = _read_csv(repo / V2_CSV)
    delta = _read_csv(repo / V2_DELTA)
    clarification = (repo / V2_CLARIFICATION).read_text(encoding="utf-8")
    citations = _read_csv(repo / V2_CITATION)
    processed = _processed77(repo)

    _require(len(roster) == TARGET_CELLS, "roster size drift")
    _require(len(v1_rows) == TARGET_CELLS, "v1 size drift")
    _require(len(v2_rows) == TARGET_CELLS, "v2 size drift")
    roster_ids = [row["program_id"] for row in roster]
    v1_ids = [row["program_id"] for row in v1_rows]
    v2_ids = [row["program_id"] for row in v2_rows]
    _require(v1_ids == roster_ids, "v1 order/identity != roster")
    _require(v2_ids == roster_ids, "v2 order/identity != roster")
    _require(len(set(v2_ids)) == TARGET_CELLS, "program uniqueness")
    _require(
        len({row["source_sha256"] for row in v2_rows}) == TARGET_UNIQUE_SOURCES,
        "source uniqueness",
    )
    _require(len({row["task_id"] for row in v2_rows}) == TARGET_UNIQUE_TASKS, "task uniqueness")
    _require(all(row["condition"] == "Candidate_B/H0" for row in roster), "condition drift")
    _require(not (set(v2_ids) & processed), "processed77 intersection")
    _require(len(processed) == 77, "processed77 size")

    # v1 byte integrity already checked via SOURCE_HASHES; confirm independent dirs.
    _require(V1_DIR.resolve() != V2_DIR.resolve(), "v2 must be independent of v1")
    _require(
        (repo / V2_DIR / "revision_delta_v1_to_v2.csv").is_file(),
        "v2 missing delta artifact",
    )
    _require(not (repo / V1_DIR / "revision_delta_v1_to_v2.csv").exists(), "v1 must not contain v2 delta")

    # Delta closure.
    _require(len(delta) == 4, f"delta row count drift: {len(delta)}")
    delta_pids = {row["program_id"] for row in delta}
    _require(delta_pids == APPROVED_PIDS, f"unexpected delta program_ids: {delta_pids}")
    _require(
        Counter(row["field"] for row in delta)
        == Counter({"healer_eligibility": 2, "abstain_reason": 2}),
        "delta field mix drift",
    )
    for row in delta:
        if row["field"] == "healer_eligibility":
            _require(row["old_value"] == "conditional" and row["new_value"] == "abstain", "healer delta")
        if row["field"] == "abstain_reason":
            _require("L5" in row["new_value"], "abstain_reason must cite L5")
            _require(
                "task-specific" in row["new_value"] or "task-specific" in row["change_reason"],
                "abstain_reason must note task-specific probe",
            )
            _require("generic Healer" in row["new_value"] or "generic" in row["new_value"], "non-generic")

    v1_by = {row["program_id"]: row for row in v1_rows}
    v2_by = {row["program_id"]: row for row in v2_rows}
    unexpected_diffs: list[dict[str, str]] = []
    approved_diffs: list[dict[str, str]] = []
    all_fields = sorted(set(v1_rows[0]) | set(v2_rows[0]))
    for program_id in roster_ids:
        v1 = v1_by[program_id]
        v2 = v2_by[program_id]
        for field in all_fields:
            if v1.get(field, "") == v2.get(field, ""):
                continue
            in_delta = any(
                d["program_id"] == program_id and d["field"] == field for d in delta
            )
            approved = program_id in APPROVED_PIDS and field in MUTABLE_ALLOWED and in_delta
            record = {
                "program_id": program_id,
                "field": field,
                "v1_value": v1.get(field, ""),
                "v2_value": v2.get(field, ""),
                "in_revision_delta": str(in_delta).lower(),
                "approved": str(approved).lower(),
                "closure_verdict": "accept" if approved else "unapproved_diff",
            }
            if approved:
                approved_diffs.append(record)
            else:
                unexpected_diffs.append(record)
            if field in IMMUTABLE_FIELDS:
                _require(False, f"immutable field differs: {program_id}.{field}")

    # Stable order: match revision_delta then field name.
    approved_diffs = sorted(
        approved_diffs,
        key=lambda row: (
            row["program_id"],
            0 if row["field"] == "healer_eligibility" else 1,
            row["field"],
        ),
    )
    _require(len(approved_diffs) == 4, f"approved diff count: {len(approved_diffs)}")
    _require(not unexpected_diffs, f"unapproved diffs: {unexpected_diffs}")

    # Statistics closure.
    primary = Counter(row["primary_layer"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    secondary_nonempty = sum(1 for row in v2_rows if json.loads(row["secondary_layers"]))
    _require(dict(primary) == EXPECTED_PRIMARY, f"primary drift: {dict(primary)}")
    _require(dict(healer) == EXPECTED_HEALER, f"healer drift: {dict(healer)}")
    _require(dict(confidence) == EXPECTED_CONFIDENCE, f"confidence drift: {dict(confidence)}")
    _require(dict(outcome) == {"VALID_MODEL_OUTCOME": 20}, f"outcome drift: {dict(outcome)}")
    _require(secondary_nonempty == 0, "secondary must be empty")
    unresolved = [row for row in v2_rows if row["primary_layer"] == "UNRESOLVED"]
    _require(len(unresolved) == 12, "unresolved count")
    _require(all(row["healer_eligibility"] == "abstain" for row in unresolved), "UNRESOLVED abstain")
    l5 = [row for row in v2_rows if row["primary_layer"] == "L5"]
    _require(len(l5) == 7, "L5 count")
    _require(all(row["healer_eligibility"] == "abstain" for row in l5), "L5 not proven-repairable")
    _require(healer.get("eligible", 0) == 0 and healer.get("conditional", 0) == 0, "no healer candidates")

    # Sufficiency clarification.
    clar_checks = {
        "does_not_overwrite_preaudit": "不覆寫" in clarification or "不竄改" in clarification,
        "sufficient_means_adjudicable": "足以進行合法" in clarification,
        "unresolved_allowed": "UNRESOLVED" in clarification and "包含" in clarification,
        "not_layer_closed": "不等於" in clarification,
        "eleven_sufficient": "11" in clarification and "sufficient" in clarification,
        "one_conditional": "1" in clarification and "conditional" in clarification,
        "forbids_seven_narrative": "新增 7 格" in clarification,
    }
    _require(all(clar_checks.values()), f"clarification checks failed: {clar_checks}")
    # Pre-audit still intact (hash pinned).
    _require(
        _sha((repo / PRE_AUDIT_MANIFEST).read_bytes()) == PRE_AUDIT_MANIFEST_SHA256,
        "pre-audit overwritten",
    )

    # Per-cell integrity.
    citation_by_program: dict[str, list[dict[str, str]]] = {}
    for row in citations:
        citation_by_program.setdefault(row["program_id"], []).append(row)

    cell_audits: list[dict[str, str]] = []
    for rank, row in enumerate(v2_rows, 1):
        chain = json.loads(row["failure_chain"])
        cites = json.loads(row["evidence_citations"])
        chain_ok = isinstance(chain, list) and len(chain) >= 2
        cites_ok = isinstance(cites, list) and len(cites) >= 1 and bool(citation_by_program.get(row["program_id"]))
        outcome_ok = row["outcome_validity"] == "VALID_MODEL_OUTCOME"
        identity_ok = row["adjudication_status"] == ADJUDICATION_STATUS
        unresolved_ok = (
            row["primary_layer"] != "UNRESOLVED"
            or (row["healer_eligibility"] == "abstain" and bool(row["abstain_reason"]))
        )
        healer_reason_ok = (
            row["healer_eligibility"] != "abstain" or bool(row["abstain_reason"])
        )
        cell_ok = chain_ok and cites_ok and outcome_ok and identity_ok and unresolved_ok and healer_reason_ok
        cell_audits.append(
            {
                "audit_rank": str(rank),
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "source_sha256": row["source_sha256"],
                "primary_layer": row["primary_layer"],
                "healer_eligibility": row["healer_eligibility"],
                "confidence": row["confidence"],
                "failure_chain_ok": str(chain_ok).lower(),
                "citations_ok": str(cites_ok).lower(),
                "outcome_separated": str(outcome_ok).lower(),
                "identity_status_ok": str(identity_ok).lower(),
                "unresolved_abstain_ok": str(unresolved_ok).lower(),
                "cell_verdict": "accept" if cell_ok else "change_required",
                "notes": (
                    "source-level evidence unit; not an independent-task claim"
                    if cell_ok
                    else "integrity failure"
                ),
            }
        )
    _require(len(cell_audits) == 20, "cell audit coverage")
    _require(all(row["cell_verdict"] == "accept" for row in cell_audits), "cell integrity failure")
    _require(len({row["program_id"] for row in cell_audits}) == 20, "duplicate cell audit")

    # Summary note about source-level units.
    summary_zh = (repo / V2_DIR / "adjudication_summary_zh.md").read_text(encoding="utf-8")
    _require("source-level" in summary_zh or "13" in summary_zh, "missing source/task framing")
    _require("20 個獨立 task" not in summary_zh, "must not claim 20 independent tasks")

    sha_rows = []
    for relative, expected in sorted(
        {
            MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
            MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
            NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
            V1_MANIFEST: V1_FILE_SHA256[V1_MANIFEST],
            V1_CSV: V1_FILE_SHA256[V1_CSV],
            POST_AUDIT_MANIFEST: POST_AUDIT_MANIFEST_SHA256,
            V2_MANIFEST: V2_MANIFEST_SHA256,
            V2_CSV: V2_CSV_SHA256,
        }.items(),
        key=lambda item: item[0].as_posix(),
    ):
        observed = _sha((repo / relative).read_bytes())
        sha_rows.append(
            {
                "check_id": relative.as_posix().replace("/", "_")[-48:],
                "artifact_path": relative.as_posix(),
                "expected_sha256": expected,
                "observed_sha256": observed,
                "match": str(observed == expected).lower(),
                "role": "FROZEN_INPUT",
            }
        )
    _require(all(row["match"] == "true" for row in sha_rows), "sha closure failure")

    audit_verdict = "READY_TO_FREEZE_COMMIT_AND_PUSH_20_CELL_V2"
    if unexpected_diffs:
        audit_verdict = "REVISION_REQUIRED_BEFORE_FREEZE"

    statistics = {
        "cells": 20,
        "unique_program_id": 20,
        "unique_source_sha256": 20,
        "unique_task_id": 13,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_nonempty_cells": secondary_nonempty,
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "unresolved_cells": 12,
        "unresolved_all_abstain": True,
        "l5_cells": 7,
        "l5_all_abstain": True,
        "healer_eligible_or_conditional": 0,
        "approved_cell_field_changes": 4,
        "affected_cells": 2,
        "unapproved_diffs": 0,
        "v1_byte_identical": True,
        "v2_independent_revision": True,
        "clarification_ok": True,
        "cell_audits_accept": 20,
        "audit_verdict": audit_verdict,
        "freeze_authorized_by_this_audit": True,
        "note": "20 source-level evidence units across 13 tasks; not 20 independent tasks.",
    }

    return {
        "cell_audits": cell_audits,
        "delta_closure": approved_diffs,
        "sha_rows": sha_rows,
        "statistics": statistics,
        "audit_verdict": audit_verdict,
        "clar_checks": clar_checks,
    }


def _report_zh(analysis: dict[str, Any]) -> str:
    stats = analysis["statistics"]
    return "\n".join(
        [
            "# Final freeze audit（output/contract-shape provisional v2）",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Audit verdict：`{analysis['audit_verdict']}`**",
            "",
            "## 基準與 SHA closure",
            "",
            "- census / multiple-signal / next-batch roster / v1 / post-audit / v2 SHA 全部匹配",
            "- v1 全部產物逐 byte 未變；v2 為獨立 revision",
            "",
            "## Roster",
            "",
            "- cells=20，program=20，source=20，task=13",
            "- Candidate_B/H0；processed77 交集=0",
            "- v2 roster 順序與身分與 v1 / fixed next_batch_roster 一致",
            "",
            "## v1→v2 差異封閉",
            "",
            "- affected cells=2（Mbpp/237）",
            "- changed fields=4（healer_eligibility×2 + abstain_reason×2）",
            "- 未核准差異=0",
            "",
            "## 最終統計",
            "",
            f"- primary：{stats['primary_layer_distribution']}",
            f"- healer：{stats['healer_eligibility_distribution']}",
            f"- outcome：{stats['outcome_validity_distribution']}",
            f"- confidence：{stats['confidence_distribution']}",
            "- secondary：全空",
            "- UNRESOLVED 12 全部 abstain；L5 7 全部 abstain；無 eligible/conditional",
            "",
            "## Sufficiency 澄清",
            "",
            "- 未覆寫 pre-audit",
            "- sufficient = 足以合法裁決（可含 UNRESOLVED）",
            "- 11 sufficient + 1 conditional → UNRESOLVED；禁止「新增 7 格」敘述",
            "",
            "## 逐格完整性",
            "",
            "- 20/20 accept；failure_chain 有序非空；citations 可追溯",
            "- outcome 與 taxonomy 分離；adjudication_status 維持 provisional 標記",
            "",
            "## 凍結邊界",
            "",
            "- 本 audit **授權**後續 freeze/commit/push 流程，但本輪**不**寫入 frozen 標記、不 commit、不 push",
            "- 不得提前宣布總數已凍結 97 格；不得開始剩餘 101 格",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    provenance = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "start_head": START_HEAD,
        "audited_revision": V2_DIR.name,
        "parent_v1_revision": V1_DIR.name,
        "v1_manifest_sha256": V1_FILE_SHA256[V1_MANIFEST],
        "v1_csv_sha256": V1_FILE_SHA256[V1_CSV],
        "v2_manifest_sha256": V2_MANIFEST_SHA256,
        "v2_csv_sha256": V2_CSV_SHA256,
        "post_audit_manifest_sha256": POST_AUDIT_MANIFEST_SHA256,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "multiple_signal_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
        "audit_verdict": analysis["audit_verdict"],
        "freeze_written": False,
        "v2_modified": False,
        "v1_modified": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "statistics": analysis["statistics"],
    }
    return {
        Path("final_freeze_audit.csv"): _csv_bytes(FINAL_AUDIT_FIELDS, analysis["cell_audits"]),
        Path("v1_v2_delta_closure_audit.csv"): _csv_bytes(
            DELTA_CLOSURE_FIELDS, analysis["delta_closure"]
        ),
        Path("roster_and_sha_closure_audit.csv"): _csv_bytes(ROSTER_SHA_FIELDS, analysis["sha_rows"]),
        Path("final_statistics_audit.json"): _json_bytes(analysis["statistics"]),
        Path("final_freeze_audit_zh.md"): _report_zh(analysis).encode("utf-8"),
        Path("execution_counts.json"): _json_bytes(execution_counts),
        Path("provenance.json"): _json_bytes(provenance),
    }


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    # Snapshot immutability of v1/v2 before write.
    v1_before = {path: (repo / path).read_bytes() for path in V1_FILE_SHA256}
    v2_before = {
        V2_MANIFEST: (repo / V2_MANIFEST).read_bytes(),
        V2_CSV: (repo / V2_CSV).read_bytes(),
    }
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    for path, expected in v1_before.items():
        _require((repo / path).read_bytes() == expected, f"v1 mutated: {path}")
    for path, expected in v2_before.items():
        _require((repo / path).read_bytes() == expected, f"v2 mutated: {path}")
    verdict = json.loads(outputs[Path("provenance.json")].decode("utf-8"))["audit_verdict"]
    manifest = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "audited_revision": V2_DIR.name,
        "audit_verdict": verdict,
        "freeze_written": False,
        "v1_modified": False,
        "v2_modified": False,
        "target_cells": TARGET_CELLS,
        "approved_cell_field_changes": 4,
        "unapproved_diffs": 0,
        "v1_manifest_sha256": V1_FILE_SHA256[V1_MANIFEST],
        "v2_manifest_sha256": V2_MANIFEST_SHA256,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
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
