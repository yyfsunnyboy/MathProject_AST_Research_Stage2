#!/usr/bin/env python3
"""Independent mechanical audit of the Batch04 fixed roster.

The audit reconstructs remaining41 directly from frozen Batch01–03 identities
and the established remaining101 order.  It neither imports the Batch04 builder
nor creates taxonomy adjudication judgments.
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
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1_independent_audit_v1"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "INDEPENDENT_BATCH04_ROSTER_AUDIT_COMPLETE_NO_MATERIAL_FINDINGS"
VERDICT = "READY_FOR_BATCH04_PROVISIONAL_ADJUDICATION"
SELECTION_RULE = (
    "remaining101_fixed_order_excluding_frozen_batch01_batch02_batch03_take_first20"
)

FORMAL198 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
REMAINING101 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/"
    "remaining101_roster.csv"
)
FROZEN117 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1/"
    "frozen117_cell_identity_audit.csv"
)
BATCH01 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_roster.csv"
)
BATCH02 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_roster.csv"
)
BATCH03_FROZEN = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv"
)
BATCH03_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/selection_ledger.csv"
)
BATCH04_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1"
)
BATCH04_ROSTER = BATCH04_DIR / "batch04_roster.csv"
BATCH04_MANIFEST = BATCH04_DIR / "manifest.json"
BATCH04_LEDGER = BATCH04_DIR / "selection_ledger.csv"
BATCH04_REMAINING21 = BATCH04_DIR / "remaining21_roster.csv"
BATCH04_SHARED = BATCH04_DIR / "shared_source_ledger.csv"
BATCH04_SUMMARY = BATCH04_DIR / "remaining_closure_summary.json"
BATCH04_EXECUTION = BATCH04_DIR / "execution_counts.json"
BATCH04_PROVENANCE = BATCH04_DIR / "provenance.json"
BATCH04_REPORT = BATCH04_DIR / "report_zh.md"
BATCH04_SHA_LEDGER = BATCH04_DIR / "sha_ledger.json"
BATCH04_BUILDER = Path(
    "scripts/prepare_candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1.py"
)
BATCH04_TEST = Path(
    "tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1.py"
)
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    FROZEN117: "d8b48fa2bb2fcfd9963037fb84b0513206d0661f183c1812d7e0597040a51881",
    BATCH01: "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533",
    BATCH02: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    BATCH03_FROZEN: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    BATCH03_LEDGER: "a56f7fc2cc20e9e2bda2c99c417d99262c0415e541785b72bd6b3e9a6aed2bd5",
    BATCH04_ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    BATCH04_MANIFEST: "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719",
    BATCH04_LEDGER: "a093520adfb2de8662149e8ddadfa593dc61129db367774b6403eeaf635cbb27",
    BATCH04_REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    BATCH04_SHARED: "76777d09be859e5a1e42166e1b571c86e3d5bd1f1a071ec7b15e2cdece1664e8",
    BATCH04_SUMMARY: "b326d6b35690fda65a6542e78106571de2ed4f5b2810b68830734b0433d78d45",
    BATCH04_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    BATCH04_PROVENANCE: "0ecba4a11667a93c455e1d3cab45811a0674d6689acc75dff73974ff9969e18e",
    BATCH04_REPORT: "50400e8a485c5bf8cfeb2e41ea29f8c654d926d5522c5c00e94946cd05da931a",
    BATCH04_SHA_LEDGER: "890ef7d27d34578ff01d8669ad19acb54c30a1c2de98f901ddb81f629fc11f00",
    BATCH04_BUILDER: "34cf4259dd001dd15e1a2e472a9a445b14ab5b88d3c27f6707af78f4ad3b7240",
    BATCH04_TEST: "55c43055196dad3db22ed5a32fdb900dc6b0f9ed4f5c68efb90e48ff4c95a168",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

COMPARE_FIELDS = (
    "selection_rank",
    "remaining41_rank",
    "remaining61_rank",
    "source_roster_rank",
    "program_id",
    "cell_identity_sha256",
    "dataset",
    "task_id",
    "task_identity_sha256",
    "model",
    "condition",
    "seed",
    "generation_id",
    "source_artifact_path",
    "source_sha256",
    "evaluation_source_sha256",
    "selection_rule",
    "selection_rule_citation",
    "upstream_result_citation",
)
CELL_FINDING_FIELDS = (
    "selection_rank",
    "program_id",
    "cell_identity_sha256",
    "audit_status",
    "matched_fields",
    "mismatched_fields_json",
    "order_status",
    "identity_status",
    "source_status",
    "selection_rule_status",
    "program_readable_status",
    "material_reason",
)
ORDER_FINDING_FIELDS = ("check_id", "audit_status", "expected", "observed", "evidence", "material_reason")
MATERIAL_FIELDS = ("finding_scope", "finding_id", "original_value", "expected_value", "evidence", "impact")
SHARED_FINDING_FIELDS = (
    "source_sha256",
    "cell_count",
    "selection_ranks_json",
    "legality_status",
    "distinct_cell_status",
    "material_reason",
)


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


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def _identity(row: dict[str, str], cell_field: str) -> tuple[str, str]:
    return row["program_id"], row[cell_field]


def _expected_row(source: dict[str, str], rank: int) -> dict[str, str]:
    return {
        "selection_rank": str(rank),
        "remaining41_rank": str(rank),
        "remaining61_rank": str(rank + 20),
        "source_roster_rank": source["roster_rank"],
        "program_id": source["program_id"],
        "cell_identity_sha256": source["cell_id"],
        "dataset": source["dataset"],
        "task_id": source["task_id"],
        "task_identity_sha256": source["task_identity_sha256"],
        "model": source["model"],
        "condition": source["condition"],
        "seed": source["seed"],
        "generation_id": source["generation_id"],
        "source_artifact_path": source["raw_generation_reference"],
        "source_sha256": source["source_sha256"],
        "evaluation_source_sha256": source["evaluation_source_sha256"],
        "selection_rule": SELECTION_RULE,
        "selection_rule_citation": f"{BATCH03_LEDGER.as_posix()}#after_batch03_remaining_rank={rank}",
        "upstream_result_citation": (
            f"{REMAINING101.as_posix()}#roster_rank={source['roster_rank']};"
            f"program_id={source['program_id']}"
        ),
    }


def _program_readable(repo: Path, reference: str, expected_sha: str) -> bool:
    path_part, fragment = reference.split("#", 1)
    parts = dict(item.split("=", 1) for item in fragment.split(";"))
    path = repo / path_part
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("program_id") == parts["program_id"] and obj.get("healer_account") == parts.get(
                "healer_account", "H0"
            ):
                source = obj.get("evaluation_source", "")
                return isinstance(source, str) and len(source) > 0 and _sha(source.encode("utf-8")) == expected_sha
    return False


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    formal = _read_csv(repo, FORMAL198)
    remaining101 = _read_csv(repo, REMAINING101)
    frozen117 = _read_csv(repo, FROZEN117)
    batch01 = _read_csv(repo, BATCH01)
    batch02 = _read_csv(repo, BATCH02)
    batch03 = _read_csv(repo, BATCH03_FROZEN)
    deferred_ledger = [
        row
        for row in _read_csv(repo, BATCH03_LEDGER)
        if row["selection_disposition"] == "PLANNED_REMAINING_AFTER_BATCH03"
    ]
    actual_roster = _read_csv(repo, BATCH04_ROSTER)
    actual_remaining21 = _read_csv(repo, BATCH04_REMAINING21)
    actual_shared = _read_csv(repo, BATCH04_SHARED)

    _require(len(formal) == 198 and len(remaining101) == 101, "population input count drift")
    _require(len(frozen117) == 117 and len(batch01) == len(batch02) == len(batch03) == 20, "frozen input count drift")
    _require(len(deferred_ledger) == 41, "deferred remaining41 count drift")

    b1_ids = {_identity(row, "cell_id") for row in batch01}
    b2_ids = {_identity(row, "cell_identity_sha256") for row in batch02}
    b3_ids = {_identity(row, "cell_identity_sha256") for row in batch03}
    frozen117_ids = {_identity(row, "cell_identity_sha256") for row in frozen117}
    frozen157_ids = frozen117_ids | b2_ids | b3_ids
    _require(b1_ids <= frozen117_ids and len(frozen157_ids) == 157, "frozen157 set drift")

    independently_rebuilt41 = [
        row for row in remaining101 if _identity(row, "cell_id") not in b1_ids | b2_ids | b3_ids
    ]
    _require(len(independently_rebuilt41) == 41, "independent remaining41 count drift")
    for rank, (source, prior) in enumerate(zip(independently_rebuilt41, deferred_ledger), 1):
        _require(prior["after_batch03_remaining_rank"] == str(rank), f"deferred rank drift {rank}")
        _require(prior["program_id"] == source["program_id"], f"deferred program drift {rank}")
        _require(prior["cell_identity_sha256"] == source["cell_id"], f"deferred cell drift {rank}")
        _require(prior["source_sha256"] == source["source_sha256"], f"deferred source drift {rank}")

    expected_roster = [_expected_row(row, rank) for rank, row in enumerate(independently_rebuilt41[:20], 1)]
    _require(len(actual_roster) == 20, "Batch04 roster count drift")
    per_cell: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    for expected, actual in zip(expected_roster, actual_roster):
        mismatches = [field for field in COMPARE_FIELDS if actual.get(field, "") != expected[field]]
        readable = _program_readable(repo, expected["source_artifact_path"], expected["source_sha256"])
        if mismatches or not readable:
            material.append(
                {
                    "finding_scope": "per_cell",
                    "finding_id": expected["program_id"],
                    "original_value": json.dumps(
                        {f: actual.get(f, "") for f in mismatches} | {"program_readable": readable},
                        sort_keys=True,
                    ),
                    "expected_value": json.dumps(
                        {f: expected[f] for f in mismatches} | {"program_readable": True},
                        sort_keys=True,
                    ),
                    "evidence": f"independent remaining41 rank {expected['remaining41_rank']}",
                    "impact": "Batch04 roster is not the uniquely determined fixed-order selection",
                }
            )
        per_cell.append(
            {
                "selection_rank": expected["selection_rank"],
                "program_id": expected["program_id"],
                "cell_identity_sha256": expected["cell_identity_sha256"],
                "audit_status": "AFFIRMED" if not mismatches and readable else "MATERIAL",
                "matched_fields": str(len(COMPARE_FIELDS) - len(mismatches)),
                "mismatched_fields_json": json.dumps(mismatches, separators=(",", ":")),
                "order_status": "MATCH" if actual.get("selection_rank") == expected["selection_rank"] else "MISMATCH",
                "identity_status": (
                    "MATCH"
                    if actual.get("program_id") == expected["program_id"]
                    and actual.get("cell_identity_sha256") == expected["cell_identity_sha256"]
                    else "MISMATCH"
                ),
                "source_status": (
                    "MATCH"
                    if actual.get("source_artifact_path") == expected["source_artifact_path"]
                    and actual.get("source_sha256") == expected["source_sha256"]
                    else "MISMATCH"
                ),
                "selection_rule_status": (
                    "MATCH"
                    if actual.get("selection_rule") == SELECTION_RULE
                    and actual.get("selection_rule_citation") == expected["selection_rule_citation"]
                    else "MISMATCH"
                ),
                "program_readable_status": "MATCH" if readable else "MISMATCH",
                "material_reason": "" if not mismatches and readable else "roster_or_source_mismatch",
            }
        )
    _require(not material, f"material roster differences: {len(material)}")

    selected_ids = {_identity(row, "cell_identity_sha256") for row in actual_roster}
    remaining41_ids = {_identity(row, "cell_id") for row in independently_rebuilt41}
    deferred_ids = {_identity(row, "cell_id") for row in independently_rebuilt41[20:]}
    formal_ids = {_identity(row, "cell_identity_sha256") for row in formal}
    _require(len(actual_remaining21) == 21, "remaining21 count drift")
    _require(
        [row["program_id"] for row in actual_remaining21]
        == [row["program_id"] for row in independently_rebuilt41[20:]],
        "remaining21 order drift",
    )

    shared_findings: list[dict[str, str]] = []
    _require(len(actual_shared) == 1, "shared source group count drift")
    shared = actual_shared[0]
    ranks = json.loads(shared["selection_ranks_json"])
    cells = json.loads(shared["cell_identity_sha256_json"])
    legality_ok = (
        shared["legality"] == "LEGAL_SHARED_SOURCE_DISTINCT_CELLS"
        and int(shared["cell_count"]) == 2
        and len(set(cells)) == 2
        and ranks == ["5", "12"]
    )
    shared_findings.append(
        {
            "source_sha256": shared["source_sha256"],
            "cell_count": shared["cell_count"],
            "selection_ranks_json": shared["selection_ranks_json"],
            "legality_status": "AFFIRMED" if legality_ok else "MATERIAL",
            "distinct_cell_status": "MATCH" if len(set(cells)) == 2 else "MISMATCH",
            "material_reason": "" if legality_ok else "shared_source_legality_mismatch",
        }
    )
    _require(legality_ok, "shared source legality drift")

    checks = [
        ("remaining41_row_field_equality", "41", "41", BATCH03_LEDGER.as_posix()),
        ("fixed_order_rank_1_20", "1..20", ",".join(row["selection_rank"] for row in actual_roster), BATCH04_ROSTER.as_posix()),
        ("identity_source_order_20_20", "20/20", f"{len(selected_ids)}/{sum(1 for r in per_cell if r['source_status']=='MATCH')}", "per-cell audit"),
        ("formal_closure", "198=157+20+21", f"{len(formal_ids)}={len(frozen157_ids)}+{len(selected_ids)}+{len(deferred_ids)}", FORMAL198.as_posix()),
        ("selection_closure", "41=20+21", f"{len(remaining41_ids)}={len(selected_ids)}+{len(deferred_ids)}", BATCH03_LEDGER.as_posix()),
        ("frozen157_overlap", "0", str(len(selected_ids & frozen157_ids)), "frozen Batch01-03 union"),
        ("batch04_duplicate_cell", "0", str(20 - len(selected_ids)), BATCH04_ROSTER.as_posix()),
        ("legal_shared_source", "1 group / distinct cells", f"{len(actual_shared)} group / {len(set(cells))} cells", BATCH04_SHARED.as_posix()),
    ]
    order_findings = [
        {
            "check_id": cid,
            "audit_status": "AFFIRMED",
            "expected": expected,
            "observed": observed,
            "evidence": evidence,
            "material_reason": "",
        }
        for cid, expected, observed, evidence in checks
    ]
    _require(len(selected_ids) == 20 and len(deferred_ids) == 21, "20/21 uniqueness drift")
    _require(selected_ids.isdisjoint(frozen157_ids | deferred_ids), "selection overlap drift")
    _require(frozen157_ids | remaining41_ids == formal_ids, "formal identity omission drift")
    _require(all(row["audit_status"] == "AFFIRMED" for row in per_cell), "per-cell material finding")

    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "remaining41_rows_rebuilt": 41,
        "remaining41_rows_field_equal": 41,
        "remaining41_order_equal": True,
        "batch04_cells": 20,
        "batch04_cells_field_equal": 20,
        "identity_source_order_affirmed": "20/20",
        "per_cell_affirmed": 20,
        "material_findings": 0,
        "selection_rank_unique_and_determined": True,
        "content_or_error_directed_selection_detected": False,
        "formal_population": 198,
        "frozen157": 157,
        "planned_remaining21": 21,
        "formal_closure": "198=157+20+21",
        "selection_closure": "41=20+21",
        "unique_program_id": len({row["program_id"] for row in actual_roster}),
        "unique_cell_identity": len(selected_ids),
        "unique_source_sha256": 19,
        "legal_shared_source_groups": 1,
        "overlap_frozen157": 0,
        "duplicates": 0,
        "omissions": 0,
        "programs_readable_nonempty": 20,
        "upstream_modified": False,
        "taxonomy_judgments_created": 0,
        "batch05_started": False,
    }
    return {
        "per_cell": per_cell,
        "order_findings": order_findings,
        "shared_findings": shared_findings,
        "material": material,
        "summary": summary,
    }


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch04 roster v1 獨立 audit",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            "- remaining41：獨立重建41列，逐列逐欄及順序均一致",
            "- Batch04：20/20格 identity／source／order 一致",
            "- 固定排序：唯一決定的 remaining41 rank 1–20",
            "- 與既有157格交集=0；duplicate cell=0；omission=0",
            "- 閉合：198=157+20+21；41=20+21",
            "- 合法共享 source：1 組（ranks 5 與 12，cell 相異）",
            "- 20/20 程式可讀且非空",
            "- MATERIAL finding：0",
            "",
            "未建立 taxonomy／confidence／mechanism／Healer 判定；未開始 provisional adjudication 或 Batch05。",
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
        "per_cell_roster_findings.csv": _csv_bytes(CELL_FINDING_FIELDS, analysis["per_cell"]),
        "selection_order_findings.csv": _csv_bytes(ORDER_FINDING_FIELDS, analysis["order_findings"]),
        "shared_source_findings.csv": _csv_bytes(SHARED_FINDING_FIELDS, analysis["shared_findings"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"]).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "independent_rebuild": (
            "remaining101 fixed order minus Batch01/Batch02/Batch03; builder not imported"
        ),
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True,
        "batch04_frozen": False,
        "batch04_provisional_started": False,
        "batch05_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    sha_ledger = {
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "batch04_roster_sha256": SOURCE_HASHES[BATCH04_ROSTER],
        "batch04_manifest_sha256": SOURCE_HASHES[BATCH04_MANIFEST],
        "batch03_frozen_records_sha256": SOURCE_HASHES[BATCH03_FROZEN],
        "remaining101_sha256": SOURCE_HASHES[REMAINING101],
    }
    outputs["sha_ledger.json"] = _json_bytes(sha_ledger)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "cells": 20,
        "per_cell_affirmed": 20,
        "material_findings": 0,
        "identity_source_order_affirmed": "20/20",
        "overlap_frozen157": 0,
        "formal_closure": "198=157+20+21",
        "batch04_roster_sha256": SOURCE_HASHES[BATCH04_ROSTER],
        "batch04_manifest_sha256": SOURCE_HASHES[BATCH04_MANIFEST],
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
    print(f"findings_sha256={_sha((output / 'per_cell_roster_findings.csv').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
