#!/usr/bin/env python3
"""Build Batch03 provisional v2 from the two approved audit findings only.

The v1 records and independent audit are immutable inputs.  Exactly two rows
receive one mechanism-tag correction; no cell is re-adjudicated and no runtime
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
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v2")
START_HEAD = "923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS = "AUDIT_REVISED_PROVISIONAL_ADJUDICATION_V2"
VERDICT = "READY_FOR_BATCH03_PROVISIONAL_V2_REAUDIT"

ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/batch03_roster.csv")
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
ROSTER_AUDIT_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1_independent_audit_v1/manifest.json")
V1_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1")
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
AUDIT_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1_independent_audit_v1")
AUDIT_FINDINGS = AUDIT_DIR / "per_cell_audit_findings.csv"
AUDIT_MATERIAL = AUDIT_DIR / "material_findings.csv"
AUDIT_MANIFEST = AUDIT_DIR / "manifest.json"
AUDIT_SUMMARY = AUDIT_DIR / "audit_summary.json"
AUDIT_PROVENANCE = AUDIT_DIR / "provenance.json"
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    ROSTER: "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",
    ROSTER_MANIFEST: "42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c",
    ROSTER_AUDIT_MANIFEST: "ba20a3ab6e3200f2c9c2effbabd27537f6f4b1415637fec5846c80ec90425a4a",
    V1_RECORDS: "dbc19dc8b0a1004013b51c94fe66d24b1def455911b9ac69ea56f611d9e6a0fd",
    V1_MANIFEST: "8467b8713144182abcb8d21fb40454c80daec89459fb42077d16c549231e2282",
    V1_EVIDENCE: "0d1c8f5143eedba9a863ea6b58c247ebfc6397848f3fb04f318970b072472b53",
    V1_MECHANISMS: "2ddb06e9e81e5053b0b44dbc19b32bd369925fab33bfe6f838cd93f8c18de14f",
    V1_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    V1_GAPS: "f728a5088f3c169969196caceb85258b1045cc48bde0d762ef6b6885715d7c60",
    V1_SUMMARY: "80386b6672cb25ba6d709abd97c4cbb0743761bb4ad8062c66410f15cc32112c",
    V1_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    V1_PROVENANCE: "fcfaa41e42a7989eac425e0b0d54361381e862802e237f02906127934dac924f",
    V1_REPORT: "74fcccc9ec81b13de7cb0f266b6e9858fdb850ba5fd0b5752cd9e2bf05ee75ee",
    AUDIT_FINDINGS: "6660f56ae629775ced6d7ab57b6b5b8d5931413ac00fb0dd7baad469ad5bf133",
    AUDIT_MATERIAL: "0fe1c7517bdc327fff62fc97fa159d97af3873f2c00a43ea750f40abae5a0a45",
    AUDIT_MANIFEST: "d0bdab2fa65865958336c063c432b05022acae5905fa1c63c29a971118a8f070",
    AUDIT_SUMMARY: "10648ff6228592824df652ee6437eb6f2481acf508620292e6d9ac52b2cc0faf",
    AUDIT_PROVENANCE: "7539ecfcaee7a7607c87bc8eea3cfdf8602f3c7dab820076c9cc286899fe925a",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

TARGET_IDS = {
    "3b802dcce09d236485df19d1c985675e091e74cbb5fcbf6e73f753d873f62e88",
    "71012956073b53a6d9d9341681ec221238d2d1fe8cdd2dfc5a82291b2fb7d44f",
}
OLD_TAG = "dedupe_instead_of_unique_occurrence"
NEW_TAG = "frequency_one_instead_of_distinct_value"
NEW_NOTE = "candidate includes only global-frequency-one values; public result requires each distinct value once"

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
MECHANISM_FIELDS = ("batch_rank", "program_id", "cell_identity_sha256", "primary_layer", "mechanism_tag", "strength", "note")
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
    _require(audit_manifest["verdict"] == "BATCH03_PROVISIONAL_REVISION_REQUIRED", "audit verdict drift")
    _require(len(roster) == len(v1) == 20, "20-cell closure drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in v1], "roster/v1 order drift")
    _require({r["program_id"] for r in material} == TARGET_IDS and len(material) == 2, "approved material closure drift")
    for finding in material:
        _require(finding["field_name"] == "mechanism_tags_json", "audit approved non-mechanism change")
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
            _require(old_map == {OLD_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"}, f"target v1 mechanism drift: {pid}")
            for item in tags:
                if item["tag"] == OLD_TAG:
                    item["tag"] = NEW_TAG
                    item["note"] = NEW_NOTE
            new["mechanism_tags_json"] = json.dumps(tags, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            changed = [field for field in RECORD_FIELDS if old[field] != new[field]]
            _require(changed == ["mechanism_tags_json"], f"target changed fields drift: {pid}: {changed}")
            for field in RECORD_FIELDS:
                if field != "mechanism_tags_json":
                    _require(old[field] == new[field], f"unapproved target field change: {pid}:{field}")
            new_map = _mechanism_map(new)
            _require(new_map == {NEW_TAG: "CONFIRMED", "semantic_goal_drift": "CONFIRMED"}, f"target v2 mechanism drift: {pid}")
            differences.append({
                "batch_rank": new["batch_rank"], "program_id": pid, "cell_identity_sha256": new["cell_identity_sha256"],
                "approved_by_audit": "true", "changed_fields_json": json.dumps(changed, separators=(",", ":")),
                "v1_mechanisms_json": json.dumps(old_map, sort_keys=True, separators=(",", ":")),
                "v2_mechanisms_json": json.dumps(new_map, sort_keys=True, separators=(",", ":")),
                "preserved_primary": new["primary_layer"], "preserved_secondary": new["secondary_layer"],
                "preserved_confidence": new["confidence"], "preserved_outcome": new["outcome_validity"],
                "preserved_healer": new["healer_eligibility"],
                "audit_material_locator": f"{AUDIT_MATERIAL.as_posix()}#program_id={pid}",
            })
        else:
            _require(new == old, f"non-target record changed: {pid}")
        v2.append(new)

    _require(len(differences) == 2, "approved adoption count drift")
    _require(sum(old == new for old, new in zip(v1, v2)) == 18, "18-cell equality drift")

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
    _require(changed_mechanism_rows == 2, "mechanism ledger adoption drift")

    primary = Counter(r["primary_layer"] for r in v2)
    secondary = Counter(r["secondary_layer"] or "empty" for r in v2)
    confidence = Counter(r["confidence"] for r in v2)
    outcome = Counter(r["outcome_validity"] for r in v2)
    healer = Counter(r["healer_eligibility"] for r in v2)
    mechanism_counts = Counter(r["mechanism_tag"] for r in updated_mechanisms)
    _require(primary == Counter({"L5":12,"UNRESOLVED":7,"L2":1}), f"primary drift: {primary}")
    _require(secondary == Counter({"empty":19,"L5":1}), f"secondary drift: {secondary}")
    _require(confidence == Counter({"HIGH":13,"LOW":7}), f"confidence drift: {confidence}")
    _require(outcome == Counter({"VALID_MODEL_OUTCOME":20}), f"outcome drift: {outcome}")
    _require(healer == Counter({"abstain":20}), f"healer drift: {healer}")
    _require(mechanism_counts[OLD_TAG] == 0 and mechanism_counts[NEW_TAG] == 2 and mechanism_counts["semantic_goal_drift"] == 4, "mechanism count drift")
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT, "cells":20,
        "audit_material_findings_adopted":2, "unauthorized_differences":0,
        "changed_records":2, "unchanged_records":18,
        "unique_program_id":20, "unique_cell_identity":20,
        "unique_source_sha256":len({r["source_sha256"] for r in v2}),
        "primary_layer_distribution":dict(sorted(primary.items())),
        "secondary_layer_distribution":dict(sorted(secondary.items())),
        "confidence_distribution":dict(sorted(confidence.items())),
        "outcome_validity_distribution":dict(sorted(outcome.items())),
        "healer_eligibility_distribution":{"eligible":0,"conditional":0,"abstain":20},
        "mechanism_tag_distribution":dict(sorted(mechanism_counts.items())),
        "upstream_modified":False, "new_runtime_observations":0,
    }
    return {"roster":roster,"v1":v1,"records":v2,"differences":differences,"mechanisms":updated_mechanisms,"summary":summary}


def _report(summary: dict[str, Any], differences: list[dict[str, str]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3.1：Batch03 provisional adjudication v2", "",
        f"**狀態：`{STATUS}`**", "", "## Audit-approved revisions", "",
    ]
    for row in differences:
        lines.append(f"- Rank {row['batch_rank']} `{row['program_id']}`：`{OLD_TAG}` → `{NEW_TAG}`")
    lines.extend([
        "", "兩格只修改mechanism tag及其確定性note；primary、secondary、confidence、outcome、Healer、evidence、citation與identity均不變。",
        "其餘18格records逐欄等同v1。", "",
        f"- Primary：{summary['primary_layer_distribution']}", f"- Secondary：{summary['secondary_layer_distribution']}",
        f"- Confidence：{summary['confidence_distribution']}", f"- Outcome：{summary['outcome_validity_distribution']}",
        f"- Healer：{summary['healer_eligibility_distribution']}",
        f"- `{OLD_TAG}`：0；`{NEW_TAG}`：2；`semantic_goal_drift`：4", "",
        "未重新裁決、未audit v2，亦未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型。", "",
    ])
    return "\n".join(lines)


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls":0,"candidate_executions":0,"candidate_imports":0,
        "public_test_executions":0,"hidden_test_executions":0,"evalplus_correctness_executions":0,
        "diagnostics_executions":0,"validation_executions":0,"healer_executions":0,"programs_executed":0,
    }
    outputs = {
        "adjudication_records.csv":_csv_bytes(RECORD_FIELDS, analysis["records"]),
        "approved_difference_ledger.csv":_csv_bytes(DIFF_FIELDS, analysis["differences"]),
        "per_cell_evidence_ledger.csv":(repo / V1_EVIDENCE).read_bytes(),
        "mechanism_ledger.csv":_csv_bytes(MECHANISM_FIELDS, analysis["mechanisms"]),
        "conditional_diagnostic_queue.csv":(repo / V1_CONDITIONAL).read_bytes(),
        "unresolved_evidence_gaps.csv":(repo / V1_GAPS).read_bytes(),
        "adjudication_summary.json":_json_bytes(analysis["summary"]),
        "execution_counts.json":_json_bytes(execution),
        "report_zh.md":_report(analysis["summary"], analysis["differences"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head":START_HEAD,
        "chain":[
            {"stage":"roster","path":ROSTER.as_posix(),"sha256":SOURCE_HASHES[ROSTER]},
            {"stage":"roster_audit","path":ROSTER_AUDIT_MANIFEST.as_posix(),"sha256":SOURCE_HASHES[ROSTER_AUDIT_MANIFEST]},
            {"stage":"provisional_v1","path":V1_RECORDS.as_posix(),"sha256":SOURCE_HASHES[V1_RECORDS]},
            {"stage":"independent_audit","path":AUDIT_MANIFEST.as_posix(),"sha256":SOURCE_HASHES[AUDIT_MANIFEST]},
            {"stage":"provisional_v2","path":OUTPUT_RELATIVE.as_posix()},
        ],
        "taxonomy_path":TAXONOMY.as_posix(),"taxonomy_sha256":SOURCE_HASHES[TAXONOMY],
        "source_hashes":{path.as_posix():digest for path,digest in SOURCE_HASHES.items()},
        "v1_modified":False,"audit_modified":False,"v2_audited":False,"batch03_frozen":False,"batch04_started":False,
    }
    outputs["provenance.json"]=_json_bytes(provenance)
    manifest = {
        "revision":OUTPUT_RELATIVE.as_posix(),"status":STATUS,"verdict":VERDICT,"start_head":START_HEAD,"cells":20,
        "roster_sha256":SOURCE_HASHES[ROSTER],"roster_manifest_sha256":SOURCE_HASHES[ROSTER_MANIFEST],
        "roster_audit_manifest_sha256":SOURCE_HASHES[ROSTER_AUDIT_MANIFEST],
        "provisional_v1_records_sha256":SOURCE_HASHES[V1_RECORDS],"provisional_v1_manifest_sha256":SOURCE_HASHES[V1_MANIFEST],
        "audit_findings_sha256":SOURCE_HASHES[AUDIT_FINDINGS],"audit_material_findings_sha256":SOURCE_HASHES[AUDIT_MATERIAL],
        "audit_manifest_sha256":SOURCE_HASHES[AUDIT_MANIFEST],"taxonomy_sha256":SOURCE_HASHES[TAXONOMY],
        "material_findings_adopted":2,"unauthorized_differences":0,"unchanged_records":18,
        "outputs_sha256_excluding_manifest":{name:_sha(data) for name,data in outputs.items()}, **execution,
    }
    outputs["manifest.json"]=_json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output=repo / OUTPUT_RELATIVE
    output.mkdir(parents=True,exist_ok=True)
    for name,data in build_outputs(repo).items():
        (output / name).write_bytes(data)
    return output


def main() -> None:
    output=write_outputs()
    manifest=json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output}")
    print(f"records_sha256={manifest['outputs_sha256_excluding_manifest']['adjudication_records.csv']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
