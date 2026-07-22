#!/usr/bin/env python3
"""Build the zero-execution Final Batch05 roster from all remaining 21 cells."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_final_batch05_21cell_roster_v1")
START_HEAD = "1aa7b692c4d499ada2e0b6e0799b3475f2f68b18"
STATUS = "FINAL_BATCH05_ALL_REMAINING21_ROSTER_READY_FOR_AUDIT"
VERDICT = "READY_FOR_FINAL_BATCH05_ROSTER_AUDIT"
SELECTION_RULE = "final_batch_include_all_remaining21_in_existing_fixed_order"
SELECTION_REASON = "最後一批完整納入所有剩餘格"

FORMAL198 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")
REMAINING101 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv")
REMAINING21 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/remaining21_roster.csv")
CUMULATIVE177 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/cumulative_frozen_identity_ledger.csv")
PROGRESS_V4_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v4/manifest.json")
BATCH01 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_adjudication.csv")
BATCH02 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_adjudication.csv")
BATCH03 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv")
BATCH04 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/frozen_adjudication_records.csv")
BATCH04_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/manifest.json")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES = {
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    REMAINING21: "48647e94065311f5f8376fb9e3e3299b96b8a95176d97a890be90919ff2ed07b",
    CUMULATIVE177: "d91c7d7f215f9e4a086aaa806958d1f8782686f0e0f71f2fa0df6a6c025f9422",
    PROGRESS_V4_MANIFEST: "ba024d82aa7f2c6b8af4790fbc503b962c406ea258314981a43e1bed9d94b68f",
    BATCH01: "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb",
    BATCH02: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    BATCH03: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    BATCH04: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    BATCH04_MANIFEST: "b56f1796c9b97bdbb854a5699dcdce38326c26300d9ad7bb8411c9d0499e5ea4",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

ROSTER_FIELDS = (
    "selection_rank", "after_batch04_remaining_rank", "remaining41_rank", "remaining61_rank",
    "source_roster_rank", "program_id", "cell_identity_sha256", "dataset", "task_id",
    "task_identity_sha256", "model", "condition", "seed", "generation_id",
    "source_artifact_path", "source_sha256", "evaluation_source_sha256", "upstream_result_json",
    "selection_rule", "selection_reason", "selection_rule_citation", "upstream_result_citation",
)
EVIDENCE_FIELDS = (
    "selection_rank", "program_id", "cell_identity_sha256", "program_readable_nonempty",
    "source_sha256_verified", "task_evidence_readable_nonempty", "task_evidence_citation",
    "upstream_result_present", "source_artifact_path", "source_sha256",
)
SHARED_FIELDS = (
    "source_sha256", "cell_count", "selection_ranks_json", "program_ids_json",
    "cell_identity_sha256_json", "legality", "notes",
)
LEDGER_FIELDS = ROSTER_FIELDS + ("selection_disposition", "remaining_after_selection")


class RosterError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise RosterError(message)


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
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def _identity(row: dict[str, str], cell_field: str) -> tuple[str, str]:
    return row["program_id"], row[cell_field]


def _load_program(repo: Path, reference: str) -> str:
    path_part, fragment = reference.split("#", 1)
    keys = dict(item.split("=", 1) for item in fragment.split(";"))
    path = repo / path_part
    _require(path.is_file() and path.stat().st_size > 0, f"missing/empty source artifact: {path_part}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("program_id") == keys["program_id"] and obj.get("healer_account") == keys.get("healer_account", "H0"):
                source = obj.get("evaluation_source", "")
                _require(isinstance(source, str) and bool(source), f"empty program: {keys['program_id']}")
                return source
    raise RosterError(f"program missing from artifact: {reference}")


def _load_tasks(repo: Path) -> dict[str, dict[str, Any]]:
    path = repo / TASKS
    _require(path.is_file() and path.stat().st_size > 0, "task evidence artifact missing/empty")
    tasks: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            task_id = obj.get("task_id")
            if task_id:
                tasks[str(task_id)] = obj
    return tasks


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    formal = _read_csv(repo, FORMAL198)
    remaining101 = _read_csv(repo, REMAINING101)
    remaining21 = _read_csv(repo, REMAINING21)
    frozen177 = _read_csv(repo, CUMULATIVE177)
    batches = [_read_csv(repo, path) for path in (BATCH01, BATCH02, BATCH03, BATCH04)]
    tasks = _load_tasks(repo)
    _require(len(formal) == 198 and len(frozen177) == 177 and len(remaining21) == 21, "198/177/21 count drift")
    _require(all(len(rows) == 20 for rows in batches), "Batch01-04 frozen count drift")

    formal_by_id = {_identity(row, "cell_identity_sha256"): row for row in formal}
    frozen_ids = {_identity(row, "cell_identity_sha256") for row in frozen177}
    _require(len(formal_by_id) == 198 and len(frozen_ids) == 177, "formal/frozen duplicate identity")
    _require(frozen_ids <= set(formal_by_id), "frozen177 outside formal198")
    remaining_ids = set(formal_by_id) - frozen_ids
    upstream_remaining_ids = {_identity(row, "cell_identity_sha256") for row in remaining21}
    _require(len(remaining_ids) == 21 and remaining_ids == upstream_remaining_ids, "formal198-frozen177 != remaining21")

    batch_ids: set[tuple[str, str]] = set()
    for index, rows in enumerate(batches, 1):
        cell_field = "cell_id" if index == 1 else "cell_identity_sha256"
        ids = {_identity(row, cell_field) for row in rows}
        _require(len(ids) == 20 and ids <= frozen_ids, f"Batch{index:02d} not closed in frozen177")
        _require(batch_ids.isdisjoint(ids), f"Batch{index:02d} overlaps earlier frozen batch")
        batch_ids |= ids

    remaining101_by_program = {row["program_id"]: row for row in remaining101}
    roster: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []
    for rank, prior in enumerate(remaining21, 1):
        _require(prior["after_batch04_remaining_rank"] == str(rank), f"remaining21 order drift: {rank}")
        source = remaining101_by_program.get(prior["program_id"])
        _require(source is not None and source["cell_id"] == prior["cell_identity_sha256"], f"remaining101 identity drift: {rank}")
        _require(source["source_sha256"] == prior["source_sha256"], f"remaining101 source drift: {rank}")
        formal_row = formal_by_id[(prior["program_id"], prior["cell_identity_sha256"])]
        program = _load_program(repo, prior["source_artifact_path"])
        _require(_sha(program.encode("utf-8")) == prior["source_sha256"], f"program source SHA drift: {rank}")
        task = tasks.get(prior["task_id"])
        _require(task is not None and any(bool(task.get(k)) for k in ("prompt", "test", "entry_point")), f"task evidence missing: {rank}")
        upstream = {
            "diagnostic_phase": formal_row["diagnostic_phase"],
            "evalplus_base_status": formal_row["evalplus_base_status"],
            "evalplus_plus_status": formal_row["evalplus_plus_status"],
            "g1_parse": formal_row["g1_parse"],
            "g2_execution": formal_row["g2_execution"],
            "g4_correctness": formal_row["g4_correctness"],
        }
        row = {
            "selection_rank": str(rank),
            "after_batch04_remaining_rank": str(rank),
            "remaining41_rank": prior["remaining41_rank"],
            "remaining61_rank": prior["remaining61_rank"],
            "source_roster_rank": prior["source_roster_rank"],
            "program_id": prior["program_id"],
            "cell_identity_sha256": prior["cell_identity_sha256"],
            "dataset": source["dataset"],
            "task_id": prior["task_id"],
            "task_identity_sha256": source["task_identity_sha256"],
            "model": source["model"],
            "condition": prior["condition"],
            "seed": prior["seed"],
            "generation_id": prior["generation_id"],
            "source_artifact_path": prior["source_artifact_path"],
            "source_sha256": prior["source_sha256"],
            "evaluation_source_sha256": source["evaluation_source_sha256"],
            "upstream_result_json": json.dumps(upstream, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "selection_rule": SELECTION_RULE,
            "selection_reason": SELECTION_REASON,
            "selection_rule_citation": f"{REMAINING21.as_posix()}#after_batch04_remaining_rank={rank}",
            "upstream_result_citation": f"{FORMAL198.as_posix()}#program_id={prior['program_id']}",
        }
        roster.append(row)
        evidence.append({
            "selection_rank": str(rank), "program_id": prior["program_id"],
            "cell_identity_sha256": prior["cell_identity_sha256"], "program_readable_nonempty": "true",
            "source_sha256_verified": "true", "task_evidence_readable_nonempty": "true",
            "task_evidence_citation": f"{TASKS.as_posix()}#task_id={prior['task_id']}",
            "upstream_result_present": "true", "source_artifact_path": prior["source_artifact_path"],
            "source_sha256": prior["source_sha256"],
        })

    selected_ids = {_identity(row, "cell_identity_sha256") for row in roster}
    _require(len(roster) == len(selected_ids) == 21 and selected_ids == remaining_ids, "Batch05 identity closure drift")
    _require(selected_ids.isdisjoint(frozen_ids), "Batch05 overlaps frozen177")
    source_counts = Counter(row["source_sha256"] for row in roster)
    shared: list[dict[str, str]] = []
    for digest, count in sorted(source_counts.items()):
        if count > 1:
            members = [row for row in roster if row["source_sha256"] == digest]
            _require(len({row["cell_identity_sha256"] for row in members}) == count, "shared source duplicates cell")
            shared.append({
                "source_sha256": digest, "cell_count": str(count),
                "selection_ranks_json": json.dumps([row["selection_rank"] for row in members], separators=(",", ":")),
                "program_ids_json": json.dumps([row["program_id"] for row in members], separators=(",", ":")),
                "cell_identity_sha256_json": json.dumps([row["cell_identity_sha256"] for row in members], separators=(",", ":")),
                "legality": "LEGAL_SHARED_SOURCE_DISTINCT_CELLS",
                "notes": "same evaluation source across distinct program and cell identities; not a duplicate cell",
            })
    _require(len(source_counts) == 20 and len(shared) == 1, "shared-source expectation drift")
    ledger = [{**row, "selection_disposition": "FINAL_BATCH05_SELECTED_ALL_REMAINING", "remaining_after_selection": "0"} for row in roster]
    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "formal_population": 198, "frozen_before_batch05": 177, "remaining_before_batch05": 21,
        "batch05_selected": 21, "remaining_after_selection": 0,
        "formal_closure": "198=177+21", "selection_closure": "21=21+0",
        "unique_program_id": 21, "unique_cell_identity": 21, "unique_source_sha256": 20,
        "legal_shared_source_groups": 1, "overlap_with_frozen177": 0,
        "duplicate_cells": 0, "omitted_cells": 0, "programs_and_static_evidence_readable_nonempty": 21,
        "selection_rule": SELECTION_RULE, "selection_reason": SELECTION_REASON,
        "selection_uses_program_content_or_outcome": False, "taxonomy_judgments_created": 0,
    }
    return {"roster": roster, "evidence": evidence, "shared": shared, "ledger": ledger, "summary": summary}


def _report(summary: dict[str, Any], roster_sha: str) -> str:
    return (
        "# Candidate B r003 taxonomy v3.1：Final Batch05 全部剩餘21格 roster\n\n"
        f"**狀態：`{STATUS}`**\n\n**Roster SHA-256：`{roster_sha}`**\n\n"
        "- 198 = frozen177 + Final Batch05 21；21 = selected21 + remaining0。\n"
        "- Final Batch05 完整納入既有固定順序的全部 remaining21，未依結果、內容或可修復性選樣。\n"
        "- identity/source/order=21/21；與 frozen177 overlap=0；duplicate cell=0。\n"
        "- unique source=20；1組合法共享 source（不同 program/cell identity）。\n"
        "- 21/21 程式及靜態證據可讀且非空。\n"
        "- 本 revision 不包含任何 taxonomy、mechanism、confidence、outcome、failure chain 或 Healer 裁決。\n"
        "- model/candidate/tests/EvalPlus/diagnostics/validation/Healer/program execution 全部為0。\n"
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["roster"])
    execution = {
        "model_calls": 0, "candidate_executions": 0, "candidate_imports": 0,
        "public_test_executions": 0, "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0, "diagnostics_executions": 0,
        "validation_executions": 0, "healer_executions": 0, "programs_executed": 0,
    }
    outputs = {
        "batch05_roster.csv": roster_bytes,
        "selection_ledger.csv": _csv_bytes(LEDGER_FIELDS, analysis["ledger"]),
        "per_cell_static_evidence_ledger.csv": _csv_bytes(EVIDENCE_FIELDS, analysis["evidence"]),
        "shared_source_ledger.csv": _csv_bytes(SHARED_FIELDS, analysis["shared"]),
        "remaining_closure_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(roster_bytes)).encode("utf-8"),
    }
    sha_ledger = {
        "upstream_sha256": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "batch04_remaining21_actual_sha256": SOURCE_HASHES[REMAINING21],
        "batch05_roster_sha256": _sha(roster_bytes),
    }
    outputs["sha_ledger.json"] = _json_bytes(sha_ledger)
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "rebuild_basis": "formal198 minus cumulative frozen177, ordered and field-closed against committed Batch04 remaining21; Batch01-04 frozen records independently verified as disjoint subsets of frozen177",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True, "batch05_frozen": False, "batch06_created": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "formal_population": 198, "frozen_cells": 177,
        "batch05_cells": 21, "remaining_after_selection": 0,
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "batch04_remaining21_sha256": SOURCE_HASHES[REMAINING21],
        "batch04_frozen_records_sha256": SOURCE_HASHES[BATCH04],
        "batch04_freeze_manifest_sha256": SOURCE_HASHES[BATCH04_MANIFEST],
        "cumulative_frozen_identity_ledger_sha256": SOURCE_HASHES[CUMULATIVE177],
        "batch05_roster_sha256": _sha(roster_bytes),
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
    print(f"roster_sha256={manifest['batch05_roster_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
