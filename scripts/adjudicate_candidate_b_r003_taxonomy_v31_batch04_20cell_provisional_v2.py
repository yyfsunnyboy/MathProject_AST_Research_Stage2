#!/usr/bin/env python3
"""Build Batch04 provisional v2 from the single approved audit finding only.

The v1 records and independent audit are immutable inputs.  Exactly one row
receives one mechanism-tag correction; no cell is re-adjudicated and no runtime
or model work is performed.
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
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v2"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "AUDIT_REVISED_PROVISIONAL_ADJUDICATION_V2"
VERDICT = "READY_FOR_BATCH04_PROVISIONAL_V2_INDEPENDENT_REAUDIT"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/batch04_roster.csv"
)
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
ROSTER_AUDIT_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1_independent_audit_v1/manifest.json"
)
V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1"
)
V1_RECORDS = V1_DIR / "adjudication_records.csv"
V1_MANIFEST = V1_DIR / "manifest.json"
V1_EVIDENCE = V1_DIR / "per_cell_evidence_ledger.csv"
V1_MECHANISMS = V1_DIR / "mechanism_ledger.csv"
V1_CONDITIONAL = V1_DIR / "conditional_diagnostic_queue.csv"
V1_GAPS = V1_DIR / "unresolved_evidence_gaps.csv"
V1_SUMMARY = V1_DIR / "adjudication_summary.json"
V1_EXECUTION = V1_DIR / "execution_counts.json"
V1_PROVENANCE = V1_DIR / "provenance.json"
V1_REPORT = V1_DIR / "report_zh.md"
AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1_independent_audit_v1"
)
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_audit_findings.csv"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_SUMMARY = AUDIT_DIR / "audit_summary.json"
AUDIT_PROVENANCE = AUDIT_DIR / "provenance.json"
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    ROSTER_MANIFEST: "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719",
    ROSTER_AUDIT_MANIFEST: "cd11f7da198044968773198cb9e66f057b11fb5285e4a12e1f70c7fb8475f3b7",
    V1_RECORDS: "5f61c4fc90f9200376e85c622f3fd54d4fa2fd6f0829e1606fb52a17a6033624",
    V1_MANIFEST: "6d170aa0e8f1c54cccf10159c42b5c61fad00b133c843749d15efab1a15250e4",
    V1_EVIDENCE: "85a8ee679816ca931126cec3199139b3523504f7b69b915dad8765ddf2cf362e",
    V1_MECHANISMS: "3002f3833d14935d754dfcfcb0c507e391d2d20cc10f6c901e4ea3028e420465",
    V1_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    V1_GAPS: "76ad7647b3348705e0069da451af73a601014f8e403b73f85b920ceb46feda48",
    V1_SUMMARY: "8ab1fc6381d7828dbc67cb6c9a759fe6967a939d739883f436a5ab0a3f680d1b",
    V1_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    V1_PROVENANCE: "3531dcb2aebd1595ee9ed00329b3128864ad0e282b5770e456b00793bc54724c",
    V1_REPORT: "8dc1dbe9c1b842e415ddc4674dbbd257178ec9783efbdcf6b97f4e18ee11c0f9",
    AUDIT_FINDINGS: "95a7d6927666b8f153db68a39a4f4e3db219aad95ce15f3f340b55a4ce197f53",
    AUDIT_MATERIAL: "17560e5c50ec7147be536c9f8c7d26ce230ae4d912e3f600c0ef7b0169a391b2",
    AUDIT_MANIFEST: "a264dd9b32a33911c2d6ba9fec0bbbb75d7459c3ae5599734b05178ddff46e83",
    AUDIT_SUMMARY: "e728c12691bc8ee0da8d9aee24d6383700495b5281140988d8d161398c65f55f",
    AUDIT_PROVENANCE: "32fa8110159248e46b2723a690afc3d6bc229010ec0f8c340d3a796e2d9d2ebd",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

TARGET_IDS = {
    "9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba",
}
OLD_TAG = "dedupe_instead_of_unique_occurrence"
NEW_TAG = "frequency_one_instead_of_distinct_value"
NEW_NOTE = (
    "candidate includes only global-frequency-one values; "
    "public result requires each distinct value once"
)

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
DIFF_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "approved_by_audit",
    "changed_fields_json", "v1_mechanisms_json", "v2_mechanisms_json",
    "preserved_primary", "preserved_secondary", "preserved_confidence",
    "preserved_outcome", "preserved_healer", "audit_material_locator",
)


class RevisionError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RevisionError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    actual = path if path.is_absolute() else repo / path
    with actual.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _mechanism_map(row: dict[str, str]) -> dict[str, str]:
    return {item["tag"]: item["strength"] for item in json.loads(row["mechanism_tags_json"])}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    v1 = _read_csv(repo, V1_RECORDS)
    material = _read_csv(repo, AUDIT_MATERIAL)
    audit_manifest = json.loads((repo / AUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(audit_manifest["verdict"] == "BATCH04_PROVISIONAL_V2_REVISION_REQUIRED", "audit verdict drift")
    _require(len(roster) == len(v1) == 20, "20-cell closure drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in v1], "roster/v1 order drift")
    _require({r["program_id"] for r in material} == TARGET_IDS and len(material) == 1, "approved material closure drift")
    for finding in material:
        _require(finding["field_name"] == "mechanism_tags_json", "audit approved non-mechanism change")
        _require(finding["batch_rank"] == "10", "approved rank drift")
        _require(OLD_TAG in finding["provisional_value"] and NEW_TAG in finding["recommended_value"], "audit recommendation drift")

    v2: list[dict[str, str]] = []
    differences: list[dict[str, str]] = []
    for roster_row, old in zip(roster, v1):
        pid = old["program_id"]
        _require(old["cell_identity_sha256"] == roster_row["cell_identity_sha256"], f"identity drift: {pid}")
        _require(old["source_sha256"] == roster_row["source_sha256"], f"source drift: {pid}")
        new = deepcopy(old)
        if pid in TARGET_IDS:
            tags = json.loads(old["mechanism_tags_json"])
            old_map = {item["tag"]: item["strength"] for item in tags}
            _require(
                old_map == {OLD_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"},
                f"target v1 mechanism drift: {pid}",
            )
            _require(old["primary_layer"] == "L5", "rank10 primary drift")
            _require(old["confidence"] == "HIGH", "rank10 confidence drift")
            _require(old["outcome_validity"] == "VALID_MODEL_OUTCOME", "rank10 outcome drift")
            _require(old["healer_eligibility"] == "abstain", "rank10 healer drift")
            for item in tags:
                if item["tag"] == OLD_TAG:
                    item["tag"] = NEW_TAG
                    item["note"] = NEW_NOTE
            new["mechanism_tags_json"] = json.dumps(
                tags, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            changed = [field for field in RECORD_FIELDS if old[field] != new[field]]
            _require(changed == ["mechanism_tags_json"], f"target changed fields drift: {pid}: {changed}")
            for field in RECORD_FIELDS:
                if field != "mechanism_tags_json":
                    _require(old[field] == new[field], f"unapproved target field change: {pid}:{field}")
            new_map = _mechanism_map(new)
            _require(
                new_map == {NEW_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"},
                f"target v2 mechanism drift: {pid}",
            )
            differences.append(
                {
                    "batch_rank": new["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": new["cell_identity_sha256"],
                    "approved_by_audit": "true",
                    "changed_fields_json": json.dumps(changed, separators=(",", ":")),
                    "v1_mechanisms_json": json.dumps(old_map, sort_keys=True, separators=(",", ":")),
                    "v2_mechanisms_json": json.dumps(new_map, sort_keys=True, separators=(",", ":")),
                    "preserved_primary": new["primary_layer"],
                    "preserved_secondary": new["secondary_layer"],
                    "preserved_confidence": new["confidence"],
                    "preserved_outcome": new["outcome_validity"],
                    "preserved_healer": new["healer_eligibility"],
                    "audit_material_locator": f"{AUDIT_MATERIAL.as_posix()}#program_id={pid}",
                }
            )
        else:
            _require(new == old, f"non-target record changed: {pid}")
        v2.append(new)

    _require(len(differences) == 1, "approved adoption count drift")
    _require(sum(old == new for old, new in zip(v1, v2)) == 19, "19-cell equality drift")
    _require(len({r["source_sha256"] for r in v2}) == 19, "unique source drift")
    shared = [r for r in v2 if r["batch_rank"] in {"5", "12"}]
    _require(
        len({r["source_sha256"] for r in shared}) == 1 and len({r["cell_identity_sha256"] for r in shared}) == 2,
        "legal shared source drift",
    )

    mechanism_rows = _read_csv(repo, V1_MECHANISMS)
    updated_mechanisms: list[dict[str, str]] = []
    changed_mechanism_rows = 0
    for old_row in mechanism_rows:
        row = deepcopy(old_row)
        if row["program_id"] in TARGET_IDS and row["mechanism_tag"] == OLD_TAG:
            row["mechanism_tag"] = NEW_TAG
            row["note"] = NEW_NOTE
            changed_mechanism_rows += 1
        updated_mechanisms.append(row)
    _require(changed_mechanism_rows == 1, "mechanism ledger adoption drift")

    primary = Counter(r["primary_layer"] for r in v2)
    secondary = Counter(r["secondary_layer"] or "empty" for r in v2)
    confidence = Counter(r["confidence"] for r in v2)
    outcome = Counter(r["outcome_validity"] for r in v2)
    healer = Counter(r["healer_eligibility"] for r in v2)
    mechanism_counts = Counter(r["mechanism_tag"] for r in updated_mechanisms)
    _require(primary == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1}), f"primary drift: {primary}")
    _require(secondary == Counter({"empty": 19, "L5": 1}), f"secondary drift: {secondary}")
    _require(confidence == Counter({"HIGH": 11, "LOW": 9}), f"confidence drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME": 20}), f"outcome drift: {outcome}")
    _require(healer == Counter({"abstain": 20}), f"healer drift: {healer}")
    _require(
        mechanism_counts[OLD_TAG] == 0
        and mechanism_counts[NEW_TAG] == 1
        and mechanism_counts["semantic_goal_drift"] == 3,
        f"mechanism count drift: {mechanism_counts}",
    )
    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "audit_material_findings_adopted": 1,
        "unauthorized_differences": 0,
        "changed_records": 1,
        "unchanged_records": 19,
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": len({r["source_sha256"] for r in v2}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "confidence_distribution": dict(sorted(confidence.items())),
        "outcome_validity_distribution": dict(sorted(outcome.items())),
        "healer_eligibility_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "mechanism_tag_distribution": dict(sorted(mechanism_counts.items())),
        "upstream_modified": False,
        "new_runtime_observations": 0,
        "batch05_started": False,
    }
    return {
        "roster": roster,
        "v1": v1,
        "records": v2,
        "differences": differences,
        "mechanisms": updated_mechanisms,
        "summary": summary,
    }


def _report(summary: dict[str, Any], differences: list[dict[str, str]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3.1：Batch04 provisional adjudication v2",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "## Audit-approved revisions",
        "",
    ]
    for row in differences:
        lines.append(f"- Rank {row['batch_rank']} `{row['program_id']}`：`{OLD_TAG}` → `{NEW_TAG}`")
    lines.extend(
        [
            "",
            "僅修改mechanism tag及其確定性note；primary、secondary、confidence、outcome、Healer、"
            "evidence、citation與identity均不變。",
            "其餘19格records逐欄等同v1。",
            "",
            f"- Primary：{summary['primary_layer_distribution']}",
            f"- Secondary：{summary['secondary_layer_distribution']}",
            f"- Confidence：{summary['confidence_distribution']}",
            f"- Outcome：{summary['outcome_validity_distribution']}",
            f"- Healer：{summary['healer_eligibility_distribution']}",
            f"- `{OLD_TAG}`：0；`{NEW_TAG}`：1；`semantic_goal_drift`：3",
            "",
            "未重新裁決、未audit v2，亦未執行candidate、imports、tests、EvalPlus、diagnostics、"
            "validation、Healer或模型；未freeze、未開始Batch05。",
            "",
        ]
    )
    return "\n".join(lines)


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
        "approved_difference_ledger.csv": _csv_bytes(DIFF_FIELDS, analysis["differences"]),
        "per_cell_evidence_ledger.csv": (repo / V1_EVIDENCE).read_bytes(),
        "mechanism_ledger.csv": _csv_bytes(MECHANISM_FIELDS, analysis["mechanisms"]),
        "conditional_diagnostic_queue.csv": (repo / V1_CONDITIONAL).read_bytes(),
        "unresolved_evidence_gaps.csv": (repo / V1_GAPS).read_bytes(),
        "adjudication_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], analysis["differences"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "chain": [
            {"stage": "roster", "path": ROSTER.as_posix(), "sha256": SOURCE_HASHES[ROSTER]},
            {
                "stage": "roster_audit",
                "path": ROSTER_AUDIT_MANIFEST.as_posix(),
                "sha256": SOURCE_HASHES[ROSTER_AUDIT_MANIFEST],
            },
            {"stage": "provisional_v1", "path": V1_RECORDS.as_posix(), "sha256": SOURCE_HASHES[V1_RECORDS]},
            {
                "stage": "independent_audit",
                "path": AUDIT_MANIFEST.as_posix(),
                "sha256": SOURCE_HASHES[AUDIT_MANIFEST],
            },
            {"stage": "provisional_v2", "path": OUTPUT_RELATIVE.as_posix()},
        ],
        "taxonomy_path": TAXONOMY.as_posix(),
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "v1_modified": False,
        "audit_modified": False,
        "v2_audited": False,
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
        "roster_sha256": SOURCE_HASHES[ROSTER],
        "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_manifest_sha256": SOURCE_HASHES[ROSTER_AUDIT_MANIFEST],
        "provisional_v1_records_sha256": SOURCE_HASHES[V1_RECORDS],
        "provisional_v1_manifest_sha256": SOURCE_HASHES[V1_MANIFEST],
        "audit_findings_sha256": SOURCE_HASHES[AUDIT_FINDINGS],
        "audit_material_findings_sha256": SOURCE_HASHES[AUDIT_MATERIAL],
        "audit_manifest_sha256": SOURCE_HASHES[AUDIT_MANIFEST],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "material_findings_adopted": 1,
        "unauthorized_differences": 0,
        "unchanged_records": 19,
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
