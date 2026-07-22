#!/usr/bin/env python3
"""Build the immutable zero-execution Batch03 roster from fixed remaining61.

Selection is purely positional: reconstruct remaining61 from the established
remaining101 order after excluding frozen Batch01 and Batch02, then take its
first twenty rows.  No program content or adjudication field is consulted.
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
    "candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1"
)
START_HEAD = "923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS = "IMMUTABLE_BATCH03_20CELL_ROSTER_READY_FOR_AUDIT"
VERDICT = "READY_FOR_BATCH03_ROSTER_AUDIT"
SELECTION_RULE = "remaining101_fixed_order_excluding_frozen_batch01_and_batch02_take_first20"

PROGRESS_MANIFEST = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_frozen_progress_census_v3/manifest.json")
PROGRESS_SUMMARY = PROGRESS_MANIFEST.with_name("frozen_progress_summary.json")
PROGRESS_REGISTRY = PROGRESS_MANIFEST.with_name("batch_registry.csv")
BATCH02_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1")
BATCH02_RECORDS = BATCH02_DIR / "frozen_adjudication.csv"
BATCH02_MANIFEST = BATCH02_DIR / "manifest.json"
BATCH02_ROSTER = BATCH02_DIR / "frozen_roster.csv"
BATCH02_PLAN_DIR = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1")
BATCH02_PLAN_MANIFEST = BATCH02_PLAN_DIR / "manifest.json"
EXISTING_REMAINING61 = BATCH02_PLAN_DIR / "remaining61_roster.csv"
FROZEN117_AUDIT = BATCH02_PLAN_DIR / "frozen117_cell_identity_audit.csv"
BATCH01_ROSTER = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/frozen_roster.csv")
REMAINING101 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/remaining101_roster.csv")
FORMAL198 = Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv")

SOURCE_HASHES = {
    PROGRESS_MANIFEST: "92f076996db37ea4188f83168889c70ea5b7814d6374b2b1f24cdd170760bf1e",
    PROGRESS_SUMMARY: "45f03d8afc276b91509ad028ff6b990e9646faa243d9da1fd8525bc90e490cc4",
    PROGRESS_REGISTRY: "8bea2f4fe0875335e232e64d497a36b3f79ab1eb9b427879f1a54d04f47a120f",
    BATCH02_RECORDS: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    BATCH02_MANIFEST: "41f8f76edf2669ee37494a03cf9d05ec0464bb7379d6ada58a6e2921fbeafee6",
    BATCH02_ROSTER: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    BATCH02_PLAN_MANIFEST: "05aa6192198ba4e7c6bf2ea04e043e7bd3c14a2619ba41b623496cf34e21c0a0",
    EXISTING_REMAINING61: "23187a50042dfa6e9f1c522dd5e7434285a156c7066dd52200b1f63eae1dc156",
    FROZEN117_AUDIT: "d8b48fa2bb2fcfd9963037fb84b0513206d0661f183c1812d7e0597040a51881",
    BATCH01_ROSTER: "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
}

ROSTER_FIELDS = (
    "selection_rank", "remaining61_rank", "source_roster_rank", "program_id",
    "cell_identity_sha256", "dataset", "task_id", "task_identity_sha256",
    "model", "condition", "seed", "generation_id", "source_artifact_path",
    "source_sha256", "evaluation_source_sha256", "selection_rule",
    "selection_rule_citation",
)
LEDGER_FIELDS = ROSTER_FIELDS + ("selection_disposition", "after_batch03_remaining_rank")


class RosterError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RosterError(message)


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


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    progress = json.loads((repo / PROGRESS_SUMMARY).read_text(encoding="utf-8"))
    _require(progress["formal_population"] == 198, "formal population drift")
    _require(progress["total_frozen"] == 137 and progress["remaining"] == 61, "137/61 progress drift")

    formal = _read_csv(repo, FORMAL198)
    frozen117 = _read_csv(repo, FROZEN117_AUDIT)
    batch01 = _read_csv(repo, BATCH01_ROSTER)
    batch02 = _read_csv(repo, BATCH02_ROSTER)
    remaining101 = _read_csv(repo, REMAINING101)
    prior_remaining61 = _read_csv(repo, EXISTING_REMAINING61)
    _require(len(formal) == 198 and len({_identity(r, "cell_identity_sha256") for r in formal}) == 198, "formal198 identity drift")
    _require(len(frozen117) == 117 and len({_identity(r, "cell_identity_sha256") for r in frozen117}) == 117, "frozen117 drift")
    _require(len(batch01) == len(batch02) == 20, "frozen batch roster count drift")
    _require(len(remaining101) == 101 and len(prior_remaining61) == 61, "remaining roster count drift")

    frozen117_ids = {_identity(r, "cell_identity_sha256") for r in frozen117}
    batch01_ids = {_identity(r, "cell_id") for r in batch01}
    batch02_ids = {_identity(r, "cell_identity_sha256") for r in batch02}
    _require(batch01_ids <= frozen117_ids, "Batch01 not contained in frozen117")
    _require(frozen117_ids.isdisjoint(batch02_ids), "Batch02 overlaps frozen117")
    frozen137 = frozen117_ids | batch02_ids
    _require(len(frozen137) == 137, "frozen137 identity closure drift")

    remaining101_by_id = {_identity(r, "cell_id"): r for r in remaining101}
    _require(len(remaining101_by_id) == 101, "remaining101 uniqueness drift")
    reconstructed = [r for r in remaining101 if _identity(r, "cell_id") not in batch01_ids | batch02_ids]
    _require(len(reconstructed) == 61, "reconstructed remaining61 count drift")
    for expected_rank, (row, prior) in enumerate(zip(reconstructed, prior_remaining61), 1):
        _require(prior["remaining_rank"] == str(expected_rank), f"remaining61 rank drift: {expected_rank}")
        mapping = {
            "source_roster_rank": "roster_rank", "cell_identity_sha256": "cell_id",
            "program_id": "program_id", "source_sha256": "source_sha256",
            "task_id": "task_id", "seed": "seed", "generation_id": "generation_id",
            "condition": "condition",
        }
        for prior_field, source_field in mapping.items():
            _require(prior[prior_field] == row[source_field], f"prior remaining61 byte-field drift at rank {expected_rank}: {prior_field}")

    formal_ids = {_identity(r, "cell_identity_sha256") for r in formal}
    remaining61_ids = {_identity(r, "cell_id") for r in reconstructed}
    _require(frozen137.isdisjoint(remaining61_ids), "remaining61 overlaps frozen137")
    _require(frozen137 | remaining61_ids == formal_ids, "198=137+61 identity omission drift")

    roster: list[dict[str, str]] = []
    ledger: list[dict[str, str]] = []
    for remaining_rank, row in enumerate(reconstructed, 1):
        selected = remaining_rank <= 20
        core = {
            "selection_rank": str(remaining_rank) if selected else "",
            "remaining61_rank": str(remaining_rank), "source_roster_rank": row["roster_rank"],
            "program_id": row["program_id"], "cell_identity_sha256": row["cell_id"],
            "dataset": row["dataset"], "task_id": row["task_id"],
            "task_identity_sha256": row["task_identity_sha256"], "model": row["model"],
            "condition": row["condition"], "seed": row["seed"], "generation_id": row["generation_id"],
            "source_artifact_path": row["raw_generation_reference"], "source_sha256": row["source_sha256"],
            "evaluation_source_sha256": row["evaluation_source_sha256"], "selection_rule": SELECTION_RULE,
            "selection_rule_citation": f"{EXISTING_REMAINING61.as_posix()}#remaining_rank={remaining_rank}",
        }
        if selected:
            roster.append(core)
        ledger.append({
            **core,
            "selection_disposition": "BATCH03_SELECTED" if selected else "PLANNED_REMAINING_AFTER_BATCH03",
            "after_batch03_remaining_rank": "" if selected else str(remaining_rank - 20),
        })

    selected_ids = {_identity(r, "cell_identity_sha256") for r in roster}
    deferred_ids = {_identity(r, "cell_identity_sha256") for r in ledger if r["selection_disposition"] == "PLANNED_REMAINING_AFTER_BATCH03"}
    _require(len(roster) == len(selected_ids) == 20, "Batch03 uniqueness drift")
    _require(len(deferred_ids) == 41 and selected_ids.isdisjoint(deferred_ids), "20+41 partition drift")
    _require(selected_ids | deferred_ids == remaining61_ids, "remaining61 selection omission drift")
    _require(selected_ids.isdisjoint(frozen117_ids | batch01_ids | batch02_ids), "Batch03 frozen overlap drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in reconstructed[:20]], "fixed-order selection drift")

    summary = {
        "revision": OUTPUT_RELATIVE.name, "status": STATUS, "verdict": VERDICT,
        "formal_population": 198, "frozen_before_batch03": 137,
        "remaining_before_batch03": 61, "batch03_selected": 20,
        "planned_remaining_after_batch03": 41,
        "formal_closure": "198=137+20+41", "selection_closure": "61=20+41",
        "unique_batch03_program_id": len({r["program_id"] for r in roster}),
        "unique_batch03_cell_identity": len(selected_ids),
        "overlap_with_frozen117": len(selected_ids & frozen117_ids),
        "overlap_with_batch01": len(selected_ids & batch01_ids),
        "overlap_with_batch02": len(selected_ids & batch02_ids),
        "duplicate_identities": 0, "omitted_identities": 0,
        "selection_rule": SELECTION_RULE, "selection_uses_program_content_or_adjudication": False,
        "upstream_modified": False,
    }
    return {"roster": roster, "ledger": ledger, "summary": summary}


def _report(summary: dict[str, Any], roster_sha: str) -> str:
    return "\n".join([
        "# Candidate B r003 taxonomy v3.1：Batch03 固定 20-cell roster", "",
        f"**狀態：`{STATUS}`**", "", f"**Roster SHA-256：`{roster_sha}`**", "",
        "## 閉合", "", "- 198 = frozen137 + Batch03 20 + planned remaining41",
        "- 61 = Batch03 20 + planned remaining41", "- 與 frozen117、Batch01、Batch02 overlap 均為 0",
        "- duplicate=0；omission=0", "",
        "Batch03 嚴格取既有 remaining61 固定排序的前20格；未依程式內容、錯誤類型、可修復性或預期結果挑選。", "",
        "本 revision 未裁決、未 freeze Batch03、未開始 Batch04，亦未執行 candidate、tests、EvalPlus、diagnostics、validation、Healer或模型。", "",
    ])


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
        "batch03_roster.csv": roster_bytes,
        "selection_ledger.csv": _csv_bytes(LEDGER_FIELDS, analysis["ledger"]),
        "remaining_closure_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(roster_bytes)).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"], **execution, "start_head": START_HEAD,
        "batch03_roster_sha256": _sha(roster_bytes),
        "rebuild_basis": "remaining101 fixed order minus frozen Batch01 and frozen Batch02; exact row closure against existing remaining61",
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True, "batch03_frozen": False, "batch04_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(), "status": STATUS, "verdict": VERDICT,
        "start_head": START_HEAD, "formal_population": 198, "frozen_cells": 137,
        "batch03_cells": 20, "remaining_after_selection": 41,
        "batch03_roster_sha256": _sha(roster_bytes),
        "batch02_frozen_records_sha256": SOURCE_HASHES[BATCH02_RECORDS],
        "batch02_frozen_manifest_sha256": SOURCE_HASHES[BATCH02_MANIFEST],
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
    print(f"batch03_roster_sha256={manifest['batch03_roster_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
