#!/usr/bin/env python3
"""Independently audit the zero-execution Final Batch05 all-remaining roster."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1_independent_audit_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "FINAL_BATCH05_ALL_REMAINING21_ROSTER_INDEPENDENT_AUDIT_COMPLETE"
VERDICT = "READY_FOR_FINAL_BATCH05_PROVISIONAL_ADJUDICATION"
SELECTION_RULE = "final_batch_include_all_remaining21_in_existing_fixed_order"
SELECTION_REASON = "最後一批完整納入所有剩餘格"

FORMAL198 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
REMAINING101 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv")
REMAINING21 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/remaining21_roster.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
BATCH01 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_adjudication.csv")
BATCH02 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_adjudication.csv")
BATCH03 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv")
BATCH04 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/frozen_adjudication_records.csv")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
ROSTER_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1")
ROSTER = ROSTER_DIR / "batch05_roster.csv"
ROSTER_MANIFEST = ROSTER_DIR / "manifest.json"
ROSTER_SUMMARY = ROSTER_DIR / "remaining_closure_summary.json"
ROSTER_EVIDENCE = ROSTER_DIR / "per_cell_static_evidence_ledger.csv"
ROSTER_SELECTION = ROSTER_DIR / "selection_ledger.csv"
ROSTER_SHARED = ROSTER_DIR / "shared_source_ledger.csv"
ROSTER_EXECUTION = ROSTER_DIR / "execution_counts.json"
ROSTER_PROVENANCE = ROSTER_DIR / "provenance.json"
ROSTER_REPORT = ROSTER_DIR / "report_zh.md"
ROSTER_SHA_LEDGER = ROSTER_DIR / "sha_ledger.json"
ROSTER_BUILDER = Path("scripts/prepare_candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1.py")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    BATCH01: "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb",
    BATCH02: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    BATCH03: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    BATCH04: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    ROSTER: "4ec24e450a66c50db46230a5b950137af6e6a4cb3d9a067f182a545818851764",
    ROSTER_MANIFEST: "b48500bf4be94e00ec9e836c21ff72cce7218476660b231785357b383b05731e",
    ROSTER_SUMMARY: "569cc0cb14353c2b5792b401479dbdb642a677e17b574bf93e54fbf1073c0971",
    ROSTER_EVIDENCE: "4a7ddd3d06b3578754b2de0d6fdc5034e351428d1927df859fb7d351168cb476",
    ROSTER_SELECTION: "99c313918bd0a25197fbd98fa99048039f103142c3ca4a965d7a0b5551614c9d",
    ROSTER_SHARED: "6b22d4fa8352ba0575ef04392a27412ce550b2bca4b4447f48f12b76aa627dee",
    ROSTER_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    ROSTER_PROVENANCE: "48b6189d1f12b237742f3c1d332398e0a1a60bf327c7a550821ff181dec38cb9",
    ROSTER_REPORT: "7cc82394cf3a4e6c51290aa1247d233663dba6b9a4121059f7a892e4dc2ed421",
    ROSTER_SHA_LEDGER: "4e36cac123b54baed00cb62d5016a9d099dbcd9302c8f642e23a836a4d91da37",
    ROSTER_BUILDER: "46c5fdd3c4f2822d9ab35b5558363ae9a932a2484304319be889e6a981c03139",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

COMPARE_FIELDS = (
    "selection_rank", "after_batch04_remaining_rank", "remaining41_rank", "remaining61_rank",
    "source_roster_rank", "program_id", "cell_identity_sha256", "dataset", "task_id",
    "task_identity_sha256", "model", "condition", "seed", "generation_id",
    "source_artifact_path", "source_sha256", "evaluation_source_sha256", "upstream_result_json",
    "selection_rule", "selection_reason", "selection_rule_citation", "upstream_result_citation",
)
FINDING_FIELDS = (
    "selection_rank", "program_id", "cell_identity_sha256", "audit_status", "matched_fields",
    "mismatched_fields_json", "identity_status", "source_status", "order_status",
    "program_and_static_evidence_status", "selection_status", "material_reason",
)
SELECTION_FIELDS = ("check_id", "audit_status", "expected", "observed", "evidence", "material_reason")
MATERIAL_FIELDS = ("finding_scope", "finding_id", "observed", "expected", "evidence", "impact")
SHARED_FIELDS = (
    "source_sha256", "cell_count", "selection_ranks_json", "program_ids_json",
    "distinct_cell_identities", "audit_status", "legality", "notes",
)


class AuditError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, value: Path) -> Path:
    return value if value.is_absolute() else repo / value


def _read_csv(repo: Path, value: Path) -> list[dict[str, str]]:
    with _path(repo, value).open(encoding="utf-8", newline="") as handle:
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
        path = _path(repo, relative)
        _require(path.is_file(), f"missing source: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"source byte drift: {relative.as_posix()}")


def _identity(row: dict[str, str], field: str) -> tuple[str, str]:
    return row["program_id"], row[field]


def _program_ok(repo: Path, reference: str, expected_sha: str) -> bool:
    path_part, fragment = reference.split("#", 1)
    keys = dict(item.split("=", 1) for item in fragment.split(";"))
    path = repo / path_part
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("program_id") == keys["program_id"] and obj.get("healer_account") == keys.get("healer_account", "H0"):
                source = obj.get("evaluation_source", "")
                return isinstance(source, str) and bool(source) and _sha(source.encode("utf-8")) == expected_sha
    return False


def _task_ids(repo: Path) -> set[str]:
    path = repo / TASKS
    _require(path.is_file() and path.stat().st_size > 0, "task artifact missing/empty")
    found: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("task_id") and any(bool(obj.get(k)) for k in ("prompt", "test", "entry_point")):
                found.add(str(obj["task_id"]))
    return found


def _expected(prior: dict[str, str], source: dict[str, str], formal: dict[str, str], rank: int) -> dict[str, str]:
    upstream = {
        "diagnostic_phase": formal["diagnostic_phase"], "evalplus_base_status": formal["evalplus_base_status"],
        "evalplus_plus_status": formal["evalplus_plus_status"], "g1_parse": formal["g1_parse"],
        "g2_execution": formal["g2_execution"], "g4_correctness": formal["g4_correctness"],
    }
    return {
        "selection_rank": str(rank), "after_batch04_remaining_rank": str(rank),
        "remaining41_rank": prior["remaining41_rank"], "remaining61_rank": prior["remaining61_rank"],
        "source_roster_rank": prior["source_roster_rank"], "program_id": prior["program_id"],
        "cell_identity_sha256": prior["cell_identity_sha256"], "dataset": source["dataset"],
        "task_id": prior["task_id"], "task_identity_sha256": source["task_identity_sha256"],
        "model": source["model"], "condition": prior["condition"], "seed": prior["seed"],
        "generation_id": prior["generation_id"], "source_artifact_path": prior["source_artifact_path"],
        "source_sha256": prior["source_sha256"], "evaluation_source_sha256": source["evaluation_source_sha256"],
        "upstream_result_json": json.dumps(upstream, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "selection_rule": SELECTION_RULE, "selection_reason": SELECTION_REASON,
        "selection_rule_citation": f"{REMAINING21.as_posix()}#after_batch04_remaining_rank={rank}",
        "upstream_result_citation": f"{FORMAL198.as_posix()}#program_id={prior['program_id']}",
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    formal_rows = _read_csv(repo, FORMAL198)
    remaining101 = _read_csv(repo, REMAINING101)
    remaining21 = _read_csv(repo, REMAINING21)
    frozen177 = _read_csv(repo, CUMULATIVE177)
    actual = _read_csv(repo, ROSTER)
    batches = [_read_csv(repo, p) for p in (BATCH01, BATCH02, BATCH03, BATCH04)]
    task_ids = _task_ids(repo)
    _require(len(formal_rows) == 198 and len(frozen177) == 177 and len(remaining21) == len(actual) == 21, "population count drift")
    formal = {_identity(row, "cell_identity_sha256"): row for row in formal_rows}
    frozen_ids = {_identity(row, "cell_identity_sha256") for row in frozen177}
    authoritative_remaining = set(formal) - frozen_ids
    remaining21_ids = {_identity(row, "cell_identity_sha256") for row in remaining21}
    _require(len(formal) == 198 and len(frozen_ids) == 177, "formal/frozen duplicate")
    _require(authoritative_remaining == remaining21_ids and len(authoritative_remaining) == 21, "remaining set mismatch")
    batch_union: set[tuple[str, str]] = set()
    for i, rows in enumerate(batches, 1):
        ids = {_identity(row, "cell_id" if i == 1 else "cell_identity_sha256") for row in rows}
        _require(len(ids) == 20 and ids <= frozen_ids and batch_union.isdisjoint(ids), f"Batch{i:02d} closure drift")
        batch_union |= ids

    source_by_program = {row["program_id"]: row for row in remaining101}
    expected_rows: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    for rank, (prior, observed) in enumerate(zip(remaining21, actual), 1):
        source = source_by_program[prior["program_id"]]
        expected = _expected(prior, source, formal[(prior["program_id"], prior["cell_identity_sha256"])], rank)
        expected_rows.append(expected)
        mismatches = [field for field in COMPARE_FIELDS if observed.get(field, "") != expected[field]]
        evidence_ok = _program_ok(repo, expected["source_artifact_path"], expected["source_sha256"]) and expected["task_id"] in task_ids
        if mismatches or not evidence_ok:
            material.append({
                "finding_scope": "per_cell", "finding_id": expected["program_id"],
                "observed": json.dumps({f: observed.get(f, "") for f in mismatches}, sort_keys=True),
                "expected": json.dumps({f: expected[f] for f in mismatches}, sort_keys=True),
                "evidence": f"formal198-frozen177 and remaining21 rank {rank}",
                "impact": "identity/source/order closure or static evidence failed",
            })
        findings.append({
            "selection_rank": str(rank), "program_id": expected["program_id"],
            "cell_identity_sha256": expected["cell_identity_sha256"],
            "audit_status": "AFFIRMED" if not mismatches and evidence_ok else "MATERIAL",
            "matched_fields": str(len(COMPARE_FIELDS) - len(mismatches)),
            "mismatched_fields_json": json.dumps(mismatches, separators=(",", ":")),
            "identity_status": "MATCH" if observed.get("program_id") == expected["program_id"] and observed.get("cell_identity_sha256") == expected["cell_identity_sha256"] else "MISMATCH",
            "source_status": "MATCH" if observed.get("source_artifact_path") == expected["source_artifact_path"] and observed.get("source_sha256") == expected["source_sha256"] else "MISMATCH",
            "order_status": "MATCH" if observed.get("selection_rank") == str(rank) else "MISMATCH",
            "program_and_static_evidence_status": "READABLE_NONEMPTY_SHA_MATCH" if evidence_ok else "MISMATCH",
            "selection_status": "ALL_REMAINING_FIXED_ORDER_MATCH" if not mismatches else "MISMATCH",
            "material_reason": "" if not mismatches and evidence_ok else "field_or_evidence_mismatch",
        })
    _require(not material, f"material roster findings: {len(material)}")
    actual_ids = {_identity(row, "cell_identity_sha256") for row in actual}
    _require(len(actual_ids) == 21 and actual_ids == authoritative_remaining and actual_ids.isdisjoint(frozen_ids), "actual identity closure drift")
    _require([r["program_id"] for r in actual] == [r["program_id"] for r in remaining21], "order drift")

    selection_findings = [
        {"check_id": "formal_closure", "audit_status": "AFFIRMED", "expected": "198=177+21", "observed": "198=177+21", "evidence": f"{FORMAL198.as_posix()} minus {CUMULATIVE177.as_posix()}", "material_reason": ""},
        {"check_id": "selection_closure", "audit_status": "AFFIRMED", "expected": "21=21+0", "observed": "21=21+0", "evidence": REMAINING21.as_posix(), "material_reason": ""},
        {"check_id": "all_remaining_selected", "audit_status": "AFFIRMED", "expected": "21/21", "observed": "21/21", "evidence": "set and order equality", "material_reason": ""},
        {"check_id": "frozen_overlap", "audit_status": "AFFIRMED", "expected": "0", "observed": "0", "evidence": CUMULATIVE177.as_posix(), "material_reason": ""},
        {"check_id": "duplicate_cell", "audit_status": "AFFIRMED", "expected": "0", "observed": "0", "evidence": "unique program/cell pairs", "material_reason": ""},
        {"check_id": "content_independent_selection", "audit_status": "AFFIRMED", "expected": "all remaining fixed order", "observed": "all remaining fixed order", "evidence": REMAINING21.as_posix(), "material_reason": ""},
    ]
    counts = Counter(row["source_sha256"] for row in actual)
    shared_findings: list[dict[str, str]] = []
    for digest, count in sorted(counts.items()):
        if count > 1:
            members = [row for row in actual if row["source_sha256"] == digest]
            distinct = len({row["cell_identity_sha256"] for row in members})
            _require(count == distinct, "shared source duplicates cell")
            shared_findings.append({
                "source_sha256": digest, "cell_count": str(count),
                "selection_ranks_json": json.dumps([row["selection_rank"] for row in members], separators=(",", ":")),
                "program_ids_json": json.dumps([row["program_id"] for row in members], separators=(",", ":")),
                "distinct_cell_identities": str(distinct), "audit_status": "AFFIRMED",
                "legality": "LEGAL_SHARED_SOURCE_DISTINCT_CELLS",
                "notes": "shared source at ranks 5 and 21; distinct program and cell identities",
            })
    _require(len(counts) == 20 and len(shared_findings) == 1, "shared source count drift")
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "formal_population": 198, "frozen_cells": 177, "authoritative_remaining": 21,
        "batch05_cells": 21, "remaining_after_selection": 0,
        "formal_closure": "198=177+21", "selection_closure": "21=21+0",
        "identity_source_order_affirmed": 21, "per_cell_affirmed": 21, "material_findings": 0,
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "overlap_with_frozen177": 0, "duplicate_cells": 0, "omitted_cells": 0,
        "legal_shared_source_groups": 1, "programs_and_static_evidence_readable_nonempty": 21,
        "selection_is_all_remaining_without_content_or_outcome_filter": True,
        "taxonomy_judgments_created": 0,
    }
    return {"findings": findings, "selection": selection_findings, "material": material, "shared": shared_findings, "summary": summary}


def _report(roster_sha: str) -> str:
    return (
        "# Final Batch05 全部剩餘21格 roster：獨立 audit\n\n"
        f"**結論：`{VERDICT}`**\n\n"
        f"- audited roster SHA-256：`{roster_sha}`\n"
        "- formal198 − frozen177 恰為 committed remaining21；198=177+21。\n"
        "- roster 逐欄 identity/source/order 21/21 AFFIRMED；selection後 remaining=0。\n"
        "- overlap=0、duplicate=0、omission=0、MATERIAL=0。\n"
        "- ranks 5與21合法共享 source，program/cell identity均不同。\n"
        "- 21/21 程式及靜態證據可讀、非空且 source SHA 相符。\n"
        "- audit 未建立任何分類或 Healer 判定，所有執行計數為0。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "per_cell_roster_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "selection_order_findings.csv": _csv_bytes(SELECTION_FIELDS, analysis["selection"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "shared_source_findings.csv": _csv_bytes(SHARED_FIELDS, analysis["shared"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(SOURCE_HASHES[ROSTER]).encode("utf-8"),
    }
    outputs["sha_ledger.json"] = _json_bytes({
        "audited_upstream_sha256": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "batch04_remaining21_actual_sha256": SOURCE_HASHES[REMAINING21],
        "audited_batch05_roster_sha256": SOURCE_HASHES[ROSTER],
    })
    outputs["provenance.json"] = _json_bytes({
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "independent_rebuild_basis": "formal198 minus frozen177; Batch01-04 frozen subset/disjoint closure; committed remaining21 exact set/order; no import of roster builder",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True, "batch05_frozen": False, "batch06_created": False,
    })
    outputs["manifest.json"] = _json_bytes({
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "batch05_cells": 21, "remaining_after_selection": 0,
        "material_findings": 0, "audited_batch05_roster_sha256": SOURCE_HASHES[ROSTER],
        "roster_manifest_sha256": SOURCE_HASHES[ROSTER_MANIFEST],
        "batch04_remaining21_sha256": SOURCE_HASHES[REMAINING21],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    })
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
    print(f"findings_sha256={_sha((output / 'per_cell_roster_findings.csv').read_bytes())}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
