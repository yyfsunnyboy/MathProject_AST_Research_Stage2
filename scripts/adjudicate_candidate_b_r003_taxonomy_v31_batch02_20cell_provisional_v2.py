#!/usr/bin/env python3
"""Build Batch02 provisional adjudication v2 from approved audit findings only.

The v1 revision and independent audit are immutable inputs.  Exactly two rows
are revised; the other eighteen records remain field-for-field identical to v1.
No runtime or model work is performed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v2"
)
START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "AUDIT_REVISED_PROVISIONAL_ADJUDICATION_V2"
VERDICT = "READY_FOR_BATCH02_PROVISIONAL_V2_REAUDIT"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1/batch02_roster.csv"
)
V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1"
)
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_ROSTER = V1_DIR / "adjudication_roster.csv"
V1_SUMMARY = V1_DIR / "adjudication_summary.json"
V1_GAPS = V1_DIR / "unresolved_evidence_gaps.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1_independent_audit_v1"
)
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_findings.csv"
AUDIT_SUMMARY = AUDIT_DIR / "audit_summary.json"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_PROVENANCE = AUDIT_DIR / "provenance.json"
AUDIT_SCRIPT = Path("scripts/audit_candidate_b_r003_taxonomy_v31_batch02_20cell_provisional_v1.py")

SOURCE_HASHES = {
    ROSTER: "8742e496ce63a834d6b72237319c8b2419fd749b2e2af971700aaef4055c435d",
    V1_RECORDS: "cb4101111e610faeadc292f8d26dbbb5088848011bf9d4527dbbe029b07252e9",
    V1_ROSTER: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    V1_SUMMARY: "603abb708bd6cdbeacfd9f3f56c261ed4cd3f8b5d4a85289bdaa70d548772c48",
    V1_GAPS: "8f5e9c39d94e541ba185a1c5c5337b43f6ba3e7179f2b53a5a23c1b57db1d61c",
    V1_MANIFEST: "888873b1ec39831511e53b9d41b6b07e71752faaf1aff23f12817e8576dc3d01",
    AUDIT_MATERIAL: "47160a3054e2bd634a1530f4f25e663209164d5d45c7f618fb02af1cb3182e9c",
    AUDIT_FINDINGS: "a1e00df9cc6b6ffb6da72bd349441711390720f10d0924991ce4cb3070093364",
    AUDIT_SUMMARY: "8fba9ef5f776a5b277ad33c075d86ffa7589253494397c7d41de26f22b3cc697",
    AUDIT_MANIFEST: "c0dc812fc114bd251e97ee69e770d9613a5209c59ef251aa3c5bd5d2d872c620",
    AUDIT_PROVENANCE: "94b59788f1ac8bd578ed39f50e865988d56edc89e29cc8ef66683f5cf9507587",
    AUDIT_SCRIPT: "a83048b674eb131b37a19ab42db4c91c7178b118c8b4d4966307520b0ae46d2d",
}

TARGET_IDS = {
    "12179f714d4beea5b64235cf46138bb8095c7170101cacbc268dbb8e53ed2f1d",
    "30f2df90febe8769b5db029b8b00959550855960e64ef7a41e570149744cad4a",
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
DELTA_FIELDS = (
    "program_id", "cell_identity_sha256", "changed_fields_json",
    "v1_primary_layer", "v2_primary_layer", "v1_confidence", "v2_confidence",
    "v1_healer_eligibility", "v2_healer_eligibility", "audit_material_locator",
)


class RevisionError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RevisionError(message)


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


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        _require((repo / path).is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha((repo / path).read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    v1_rows = _read_csv(repo, V1_RECORDS)
    material_rows = _read_csv(repo, AUDIT_MATERIAL)
    _require(len(roster) == len(v1_rows) == 20, "20-cell closure drift")
    _require({row["program_id"] for row in material_rows} == TARGET_IDS, "audit target closure drift")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in v1_rows], "roster/v1 order drift")
    _require(len({row["program_id"] for row in roster}) == 20, "program uniqueness drift")
    _require(len({row["cell_identity_sha256"] for row in roster}) == 20, "cell identity uniqueness drift")
    material_by_id = {row["program_id"]: row for row in material_rows}

    v2_rows: list[dict[str, str]] = []
    deltas: list[dict[str, str]] = []
    for roster_row, v1 in zip(roster, v1_rows):
        pid = v1["program_id"]
        _require(v1["cell_identity_sha256"] == roster_row["cell_identity_sha256"], f"cell identity drift: {pid}")
        _require(v1["source_sha256"] == roster_row["source_sha256"], f"source SHA drift: {pid}")
        v2 = deepcopy(v1)
        if pid in TARGET_IDS:
            finding = material_by_id[pid]
            _require(finding["audit_status"] == "MATERIAL", f"target not MATERIAL: {pid}")
            _require(finding["original_primary_layer"] == v1["primary_layer"] == "L5", f"original primary drift: {pid}")
            _require(finding["original_confidence"] == v1["confidence"] == "MEDIUM", f"original confidence drift: {pid}")
            _require(finding["recommended_primary_layer"] == "UNRESOLVED", f"audit recommendation drift: {pid}")
            _require(finding["recommended_confidence"] == "LOW", f"audit confidence drift: {pid}")
            _require(finding["recommended_healer_eligibility"] == "abstain", f"audit healer drift: {pid}")
            v2.update(
                {
                    "primary_layer": finding["recommended_primary_layer"],
                    "secondary_layer": finding["recommended_secondary_layer"],
                    "mechanism_tags_json": finding["recommended_mechanisms_json"],
                    "failure_chain": finding["recommended_failure_chain"],
                    "confidence": finding["recommended_confidence"],
                    "outcome_validity": finding["recommended_outcome_validity"],
                    "healer_eligibility": finding["recommended_healer_eligibility"],
                    "eligibility_reason": finding["audit_rationale"],
                    "unresolved_reason_code": finding["recommended_unresolved_reason_code"],
                    "evidence_present": finding["recommended_evidence_present"],
                    "evidence_missing": finding["recommended_evidence_missing"],
                    "minimal_future_diagnostic": finding["recommended_minimal_future_diagnostic"],
                    "public_evidence": finding["independent_evidence"],
                    "evidence_citations": (
                        v1["evidence_citations"] + ";" +
                        f"{AUDIT_MATERIAL.as_posix()}#program_id={pid}"
                    ),
                }
            )
            changed = [field for field in RECORD_FIELDS if v1[field] != v2[field]]
            expected_changed = {
                "primary_layer", "mechanism_tags_json", "failure_chain", "confidence",
                "eligibility_reason", "unresolved_reason_code", "evidence_present",
                "evidence_missing", "minimal_future_diagnostic", "public_evidence",
                "evidence_citations",
            }
            _require(set(changed) == expected_changed, f"unapproved delta fields for {pid}: {changed}")
            deltas.append(
                {
                    "program_id": pid,
                    "cell_identity_sha256": v2["cell_identity_sha256"],
                    "changed_fields_json": _json(changed),
                    "v1_primary_layer": v1["primary_layer"], "v2_primary_layer": v2["primary_layer"],
                    "v1_confidence": v1["confidence"], "v2_confidence": v2["confidence"],
                    "v1_healer_eligibility": v1["healer_eligibility"],
                    "v2_healer_eligibility": v2["healer_eligibility"],
                    "audit_material_locator": f"{AUDIT_MATERIAL.as_posix()}#program_id={pid}",
                }
            )
        else:
            _require(v2 == v1, f"non-target row changed: {pid}")
        v2_rows.append(v2)

    _require(len(deltas) == 2, "exactly two revisions required")
    for v1, v2 in zip(v1_rows, v2_rows):
        if v1["program_id"] not in TARGET_IDS:
            _require(v1 == v2, f"18-cell field equality drift: {v1['program_id']}")

    primary = Counter(row["primary_layer"] for row in v2_rows)
    secondary = Counter(row["secondary_layer"] or "(empty)" for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    outcome = Counter(row["outcome_validity"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    mechanisms = Counter()
    mechanism_strength = Counter()
    for row in v2_rows:
        for item in json.loads(row["mechanism_tags_json"]):
            mechanisms[item["tag"]] += 1
            mechanism_strength[f"{item['tag']}::{item['strength']}"] += 1
    gaps = [{field: row[field] for field in GAP_FIELDS} for row in v2_rows if row["primary_layer"] == "UNRESOLVED"]

    _require(primary == Counter({"UNRESOLVED": 11, "L5": 5, "L2": 3, "L4": 1}), f"primary drift: {primary}")
    _require(confidence == Counter({"LOW": 11, "HIGH": 7, "MEDIUM": 2}), f"confidence drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift: {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer drift: {healer}")
    _require(len(gaps) == 11 and all(row["unresolved_reason_code"] and row["evidence_missing"] and row["minimal_future_diagnostic"] for row in gaps), "gap closure drift")

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "cells": 20, "unique_program_id": 20, "unique_cell_identity": 20,
        "unique_source_sha256": len({row["source_sha256"] for row in v2_rows}),
        "audit_approved_revised_cells": 2, "unchanged_v1_cells": 18,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "mechanism_tag_distribution": dict(sorted(mechanisms.items())),
        "mechanism_tag_strength_distribution": dict(sorted(mechanism_strength.items())),
        "unresolved_cells": len(gaps),
        "v1_modified": False, "audit_modified": False,
    }
    return {"roster": roster, "v1": v1_rows, "records": v2_rows, "gaps": gaps, "deltas": deltas, "summary": summary}


def _report(summary: dict[str, Any], deltas: list[dict[str, str]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3.1：Batch02 provisional adjudication v2",
        "", f"**狀態：`{STATUS}`**", "", f"**Verdict：`{VERDICT}`**", "",
        "## Audit-approved revisions", "",
    ]
    for row in deltas:
        lines.append(
            f"- `{row['program_id']}`：L5/MEDIUM/abstain → UNRESOLVED/LOW/abstain"
        )
    lines.extend(
        [
            "", "其餘18格逐欄與v1一致。", "",
            "## v2 統計", "",
            f"- primary：{summary['primary_layer_distribution']}",
            f"- secondary：{summary['secondary_layer_distribution']}",
            f"- confidence：{summary['confidence_distribution']}",
            f"- outcome：{summary['outcome_validity_distribution']}",
            f"- Healer：{summary['healer_eligibility_distribution']}",
            f"- UNRESOLVED：{summary['unresolved_cells']}", "",
            "本 revision 未執行 candidate、tests、imports、EvalPlus、diagnostics、validation、Healer 或模型。",
            "v1 與 independent audit 均未修改；v2 尚未 re-audit 或 freeze。", "",
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
        "adjudication_roster.csv": _csv_bytes(ROSTER_FIELDS, analysis["roster"]),
        "adjudication_records.csv": _csv_bytes(RECORD_FIELDS, analysis["records"]),
        "audit_approved_changes.csv": _csv_bytes(DELTA_FIELDS, analysis["deltas"]),
        "unresolved_evidence_gaps.csv": _csv_bytes(GAP_FIELDS, analysis["gaps"]),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], analysis["deltas"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution,
        "start_head": START_HEAD, "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "provisional_v1_records_sha256": SOURCE_HASHES[V1_RECORDS],
        "audit_material_findings_sha256": SOURCE_HASHES[AUDIT_MATERIAL],
        "revision_scope": "exactly two audit-approved rows; eighteen rows field-identical to v1",
        "new_runtime_observations": 0, "upstream_modified": False,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20,
        "fixed_roster_sha256": SOURCE_HASHES[ROSTER],
        "provisional_v1_records_sha256": SOURCE_HASHES[V1_RECORDS],
        "audit_material_findings_sha256": SOURCE_HASHES[AUDIT_MATERIAL],
        "audit_approved_revised_cells": 2, "unchanged_v1_cells": 18,
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
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
