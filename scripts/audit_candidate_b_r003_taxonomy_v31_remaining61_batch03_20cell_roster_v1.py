#!/usr/bin/env python3
"""Independent mechanical audit of the Batch03 fixed roster.

The audit reconstructs remaining61 directly from frozen upstream rosters and
the established remaining101 order.  It neither imports the Batch03 builder
nor reads candidate programs or adjudication fields.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1_independent_audit_v1"
)
START_HEAD = "923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS = "INDEPENDENT_BATCH03_ROSTER_AUDIT_COMPLETE_NO_MATERIAL_FINDINGS"
VERDICT = "READY_FOR_BATCH03_PROVISIONAL_ADJUDICATION"
SELECTION_RULE = "remaining101_fixed_order_excluding_frozen_batch01_and_batch02_take_first20"

PROGRESS_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v3/manifest.json")
PROGRESS_SUMMARY = PROGRESS_MANIFEST.with_name("frozen_progress_summary.json")
FORMAL198 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
REMAINING101 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv")
BATCH01 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_roster.csv")
BATCH02 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_roster.csv")
PLAN_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1")
EXISTING_REMAINING61 = PLAN_DIR / "remaining61_roster.csv"
FROZEN117 = PLAN_DIR / "frozen117_cell_identity_audit.csv"
BATCH03_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1")
BATCH03_ROSTER = BATCH03_DIR / "batch03_roster.csv"
BATCH03_MANIFEST = BATCH03_DIR / "manifest.json"
BATCH03_LEDGER = BATCH03_DIR / "selection_ledger.csv"
BATCH03_SUMMARY = BATCH03_DIR / "remaining_closure_summary.json"
BATCH03_EXECUTION = BATCH03_DIR / "execution_counts.json"
BATCH03_PROVENANCE = BATCH03_DIR / "provenance.json"
BATCH03_REPORT = BATCH03_DIR / "report_zh.md"
BATCH03_BUILDER = Path("scripts/prepare_candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1.py")
BATCH03_TEST = Path("tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1.py")

SOURCE_HASHES = {
    PROGRESS_MANIFEST: "92f076996db37ea4188f83168889c70ea5b7814d6374b2b1f24cdd170760bf1e",
    PROGRESS_SUMMARY: "45f03d8afc276b91509ad028ff6b990e9646faa243d9da1fd8525bc90e490cc4",
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    BATCH01: "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533",
    BATCH02: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    EXISTING_REMAINING61: "23187a50042dfa6e9f1c522dd5e7434285a156c7066dd52200b1f63eae1dc156",
    FROZEN117: "d8b48fa2bb2fcfd9963037fb84b0513206d0661f183c1812d7e0597040a51881",
    BATCH03_ROSTER: "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",
    BATCH03_MANIFEST: "42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c",
    BATCH03_LEDGER: "a56f7fc2cc20e9e2bda2c99c417d99262c0415e541785b72bd6b3e9a6aed2bd5",
    BATCH03_SUMMARY: "60e3c47ed2b29187cda1e9feea30b7236dc77b3d791b2ac773de017168a43356",
    BATCH03_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    BATCH03_PROVENANCE: "83332d5544649aa07a3d3d4ece4ec3e2a6442a858cf2321e47b77e2837b5be5e",
    BATCH03_REPORT: "1331be03a514c0fcf1a68eeb0862d2179b659d9e0bb84b933e8ebc36b9d3ce33",
    BATCH03_BUILDER: "9211eefd00a01a33d0865c380ca9c562895ec49443da3bddc48b9e85bff3f49a",
    BATCH03_TEST: "78a17e9dce7434801048ab777abcc81d48dadb06871826de434e5ea49bb1bf5e",
}

COMPARE_FIELDS = (
    "selection_rank", "remaining61_rank", "source_roster_rank", "program_id",
    "cell_identity_sha256", "dataset", "task_id", "task_identity_sha256",
    "model", "condition", "seed", "generation_id", "source_artifact_path",
    "source_sha256", "evaluation_source_sha256", "selection_rule",
    "selection_rule_citation",
)
CELL_FINDING_FIELDS = (
    "selection_rank", "program_id", "cell_identity_sha256", "audit_status",
    "matched_fields", "mismatched_fields_json", "order_status",
    "identity_status", "source_status", "selection_rule_status", "material_reason",
)
ORDER_FINDING_FIELDS = ("check_id", "audit_status", "expected", "observed", "evidence", "material_reason")
MATERIAL_FIELDS = ("finding_scope", "finding_id", "original_value", "expected_value", "evidence", "impact")


class AuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, relative: Path) -> list[dict[str, str]]:
    with (repo / relative).open(encoding="utf-8", newline="") as handle:
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
    for relative, digest in SOURCE_HASHES.items():
        path = repo / relative
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def _identity(row: dict[str, str], cell_field: str) -> tuple[str, str]:
    return row["program_id"], row[cell_field]


def _expected_row(source: dict[str, str], rank: int) -> dict[str, str]:
    return {
        "selection_rank": str(rank), "remaining61_rank": str(rank),
        "source_roster_rank": source["roster_rank"], "program_id": source["program_id"],
        "cell_identity_sha256": source["cell_id"], "dataset": source["dataset"],
        "task_id": source["task_id"], "task_identity_sha256": source["task_identity_sha256"],
        "model": source["model"], "condition": source["condition"], "seed": source["seed"],
        "generation_id": source["generation_id"], "source_artifact_path": source["raw_generation_reference"],
        "source_sha256": source["source_sha256"], "evaluation_source_sha256": source["evaluation_source_sha256"],
        "selection_rule": SELECTION_RULE,
        "selection_rule_citation": f"{EXISTING_REMAINING61.as_posix()}#remaining_rank={rank}",
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    progress = json.loads((repo / PROGRESS_SUMMARY).read_text(encoding="utf-8"))
    formal = _read_csv(repo, FORMAL198)
    remaining101 = _read_csv(repo, REMAINING101)
    batch01 = _read_csv(repo, BATCH01)
    batch02 = _read_csv(repo, BATCH02)
    prior61 = _read_csv(repo, EXISTING_REMAINING61)
    frozen117 = _read_csv(repo, FROZEN117)
    actual_roster = _read_csv(repo, BATCH03_ROSTER)
    _require(progress["formal_population"] == 198 and progress["total_frozen"] == 137 and progress["remaining"] == 61, "progress closure drift")
    _require(len(formal) == 198 and len(remaining101) == 101 and len(prior61) == 61, "population input count drift")
    _require(len(batch01) == len(batch02) == 20 and len(frozen117) == 117, "frozen input count drift")

    b1_ids = {_identity(row, "cell_id") for row in batch01}
    b2_ids = {_identity(row, "cell_identity_sha256") for row in batch02}
    frozen117_ids = {_identity(row, "cell_identity_sha256") for row in frozen117}
    frozen137_ids = frozen117_ids | b2_ids
    _require(b1_ids <= frozen117_ids and frozen117_ids.isdisjoint(b2_ids) and len(frozen137_ids) == 137, "frozen137 set drift")

    independently_rebuilt61 = [row for row in remaining101 if _identity(row, "cell_id") not in b1_ids | b2_ids]
    _require(len(independently_rebuilt61) == 61, "independent remaining61 count drift")
    for rank, (source, prior) in enumerate(zip(independently_rebuilt61, prior61), 1):
        expected_prior = {
            "remaining_rank": str(rank), "source_roster_rank": source["roster_rank"],
            "cell_identity_sha256": source["cell_id"], "program_id": source["program_id"],
            "source_sha256": source["source_sha256"], "task_id": source["task_id"],
            "seed": source["seed"], "generation_id": source["generation_id"], "condition": source["condition"],
        }
        _require(prior == expected_prior, f"existing remaining61 row/field drift at rank {rank}")

    expected_roster = [_expected_row(row, rank) for rank, row in enumerate(independently_rebuilt61[:20], 1)]
    _require(len(actual_roster) == 20, "Batch03 roster count drift")
    per_cell: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    for expected, actual in zip(expected_roster, actual_roster):
        mismatches = [field for field in COMPARE_FIELDS if actual.get(field, "") != expected[field]]
        if mismatches:
            material.append({
                "finding_scope": "per_cell", "finding_id": expected["program_id"],
                "original_value": json.dumps({f: actual.get(f, "") for f in mismatches}, sort_keys=True),
                "expected_value": json.dumps({f: expected[f] for f in mismatches}, sort_keys=True),
                "evidence": f"independent remaining61 rank {expected['remaining61_rank']}",
                "impact": "Batch03 roster is not the uniquely determined fixed-order selection",
            })
        per_cell.append({
            "selection_rank": expected["selection_rank"], "program_id": expected["program_id"],
            "cell_identity_sha256": expected["cell_identity_sha256"],
            "audit_status": "AFFIRMED" if not mismatches else "MATERIAL",
            "matched_fields": str(len(COMPARE_FIELDS) - len(mismatches)),
            "mismatched_fields_json": json.dumps(mismatches, separators=(",", ":")),
            "order_status": "MATCH" if actual.get("selection_rank") == expected["selection_rank"] else "MISMATCH",
            "identity_status": "MATCH" if actual.get("program_id") == expected["program_id"] and actual.get("cell_identity_sha256") == expected["cell_identity_sha256"] else "MISMATCH",
            "source_status": "MATCH" if actual.get("source_artifact_path") == expected["source_artifact_path"] and actual.get("source_sha256") == expected["source_sha256"] else "MISMATCH",
            "selection_rule_status": "MATCH" if actual.get("selection_rule") == SELECTION_RULE and actual.get("selection_rule_citation") == expected["selection_rule_citation"] else "MISMATCH",
            "material_reason": "" if not mismatches else "roster_field_mismatch",
        })
    _require(not material, f"material roster differences: {len(material)}")

    selected_ids = {_identity(row, "cell_identity_sha256") for row in actual_roster}
    remaining61_ids = {_identity(row, "cell_id") for row in independently_rebuilt61}
    deferred_ids = {_identity(row, "cell_id") for row in independently_rebuilt61[20:]}
    formal_ids = {_identity(row, "cell_identity_sha256") for row in formal}
    checks = [
        ("remaining61_row_field_equality", "61", "61", EXISTING_REMAINING61.as_posix()),
        ("fixed_order_rank_1_20", "1..20", ",".join(row["selection_rank"] for row in actual_roster), BATCH03_ROSTER.as_posix()),
        ("formal_closure", "198=137+20+41", f"{len(formal_ids)}={len(frozen137_ids)}+{len(selected_ids)}+{len(deferred_ids)}", FORMAL198.as_posix()),
        ("selection_closure", "61=20+41", f"{len(remaining61_ids)}={len(selected_ids)}+{len(deferred_ids)}", EXISTING_REMAINING61.as_posix()),
        ("frozen117_overlap", "0", str(len(selected_ids & frozen117_ids)), FROZEN117.as_posix()),
        ("batch01_overlap", "0", str(len(selected_ids & b1_ids)), BATCH01.as_posix()),
        ("batch02_overlap", "0", str(len(selected_ids & b2_ids)), BATCH02.as_posix()),
        ("duplicate_and_omission", "0/0", f"{20-len(selected_ids)}/{len((frozen137_ids | remaining61_ids) ^ formal_ids)}", "independent set reconciliation"),
    ]
    order_findings = [
        {"check_id": cid, "audit_status": "AFFIRMED", "expected": expected, "observed": observed,
         "evidence": evidence, "material_reason": ""}
        for cid, expected, observed, evidence in checks
    ]
    _require(len(selected_ids) == 20 and len(deferred_ids) == 41, "20/41 uniqueness drift")
    _require(selected_ids.isdisjoint(frozen117_ids | b1_ids | b2_ids | deferred_ids), "selection overlap drift")
    _require(frozen137_ids | remaining61_ids == formal_ids, "formal identity omission drift")
    _require(all(row["audit_status"] == "AFFIRMED" for row in per_cell), "per-cell material finding")

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "remaining61_rows_rebuilt": 61, "remaining61_rows_field_equal": 61,
        "remaining61_order_equal": True, "batch03_cells": 20,
        "batch03_cells_field_equal": 20, "per_cell_affirmed": 20,
        "material_findings": 0, "selection_rank_unique_and_determined": True,
        "content_or_error_directed_selection_detected": False,
        "formal_population": 198, "frozen137": 137, "planned_remaining41": 41,
        "formal_closure": "198=137+20+41", "selection_closure": "61=20+41",
        "unique_program_id": len({row["program_id"] for row in actual_roster}),
        "unique_cell_identity": len(selected_ids), "overlap_frozen117": 0,
        "overlap_batch01": 0, "overlap_batch02": 0, "duplicates": 0, "omissions": 0,
        "upstream_modified": False, "taxonomy_judgments_created": 0,
    }
    return {"per_cell": per_cell, "order_findings": order_findings, "material": material, "summary": summary}


def _report(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# Candidate B r003 taxonomy v3.1：Batch03 roster v1 獨立 audit", "",
        f"**狀態：`{STATUS}`**", "",
        "- remaining61：獨立重建61列，逐列逐欄及順序均一致",
        "- Batch03：20/20格、全部17個指定欄位一致",
        "- 固定排序：唯一決定的remaining61 rank 1–20",
        "- overlap、duplicate、omission：全部0",
        "- 閉合：198=137+20+41；61=20+41",
        "- MATERIAL finding：0", "",
        "未讀取候選程式或建立taxonomy、confidence、mechanism、Healer判定；未開始provisional adjudication或Batch04。", "",
    ])


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "per_cell_roster_findings.csv": _csv_bytes(CELL_FINDING_FIELDS, analysis["per_cell"]),
        "selection_order_findings.csv": _csv_bytes(ORDER_FINDING_FIELDS, analysis["order_findings"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "independent_rebuild": "remaining101 fixed order minus Batch01 and Batch02; builder not imported",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True, "batch03_frozen": False, "batch03_provisional_started": False,
        "batch04_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "cells": 20, "per_cell_affirmed": 20,
        "material_findings": 0, "batch03_roster_sha256": SOURCE_HASHES[BATCH03_ROSTER],
        "batch03_manifest_sha256": SOURCE_HASHES[BATCH03_MANIFEST],
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
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
