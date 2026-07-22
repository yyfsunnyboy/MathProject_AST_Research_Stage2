#!/usr/bin/env python3
"""Build the immutable zero-execution Batch04 roster from remaining41.

Selection is purely positional: reconstruct remaining41 from the established
remaining101 order after excluding frozen Batch01–03, then take its first
twenty rows.  No program content is used for selection, and no taxonomy
adjudication fields are produced.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "IMMUTABLE_BATCH04_20CELL_ROSTER_READY_FOR_AUDIT"
VERDICT = "READY_FOR_BATCH04_ROSTER_AUDIT"
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
REMAINING61 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1/"
    "remaining61_roster.csv"
)
BATCH01_ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/"
    "frozen_roster.csv"
)
BATCH02_ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_roster.csv"
)
BATCH02_RECORDS = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/frozen_adjudication.csv"
)
BATCH03_ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/batch03_roster.csv"
)
BATCH03_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/selection_ledger.csv"
)
BATCH03_FROZEN = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/frozen_adjudication_records.csv"
)
BATCH03_FROZEN_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/manifest.json"
)
TAXONOMY = Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES: dict[Path, str] = {
    FORMAL198: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    FROZEN117: "d8b48fa2bb2fcfd9963037fb84b0513206d0661f183c1812d7e0597040a51881",
    REMAINING61: "23187a50042dfa6e9f1c522dd5e7434285a156c7066dd52200b1f63eae1dc156",
    BATCH01_ROSTER: "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533",
    BATCH02_ROSTER: "ca1544ad12d0336638425ac770e7bf40c19e94ca59522e7cf0a90f3d122d6e4c",
    BATCH02_RECORDS: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    BATCH03_ROSTER: "6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",
    BATCH03_LEDGER: "a56f7fc2cc20e9e2bda2c99c417d99262c0415e541785b72bd6b3e9a6aed2bd5",
    BATCH03_FROZEN: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    BATCH03_FROZEN_MANIFEST: "af9becc880d45e6969074cf5e2e53e47a3b87b4cbf6a6ecab0cb4b69963f51d9",
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

ROSTER_FIELDS = (
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
LEDGER_FIELDS = ROSTER_FIELDS + (
    "selection_disposition",
    "after_batch04_remaining_rank",
)
SHARED_SOURCE_FIELDS = (
    "source_sha256",
    "cell_count",
    "selection_ranks_json",
    "program_ids_json",
    "cell_identity_sha256_json",
    "legality",
    "notes",
)
REMAINING21_FIELDS = (
    "after_batch04_remaining_rank",
    "remaining41_rank",
    "remaining61_rank",
    "source_roster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "condition",
    "seed",
    "generation_id",
    "source_artifact_path",
    "source_sha256",
)


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


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing upstream: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"upstream byte drift: {relative.as_posix()}")


def _identity(row: dict[str, str], cell_field: str) -> tuple[str, str]:
    return row["program_id"], row[cell_field]


def _load_evaluation_source(repo: Path, reference: str) -> str:
    path_part, fragment = reference.split("#", 1)
    parts = dict(item.split("=", 1) for item in fragment.split(";"))
    path = repo / path_part
    _require(path.is_file(), f"missing source artifact: {path_part}")
    _require(path.stat().st_size > 0, f"empty source artifact: {path_part}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if obj.get("program_id") == parts["program_id"] and obj.get("healer_account") == parts.get(
                "healer_account", "H0"
            ):
                source = obj.get("evaluation_source", "")
                _require(isinstance(source, str) and len(source) > 0, f"empty evaluation_source: {parts['program_id']}")
                return source
    raise RosterError(f"program not found in artifact: {reference}")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    formal = _read_csv(repo, FORMAL198)
    remaining101 = _read_csv(repo, REMAINING101)
    frozen117 = _read_csv(repo, FROZEN117)
    remaining61 = _read_csv(repo, REMAINING61)
    batch01 = _read_csv(repo, BATCH01_ROSTER)
    batch02 = _read_csv(repo, BATCH02_ROSTER)
    batch03_roster = _read_csv(repo, BATCH03_ROSTER)
    batch03_frozen = _read_csv(repo, BATCH03_FROZEN)
    batch03_ledger = _read_csv(repo, BATCH03_LEDGER)

    _require(len(formal) == 198, "formal198 count drift")
    _require(len(remaining101) == 101, "remaining101 count drift")
    _require(len(frozen117) == 117 and len(remaining61) == 61, "117/61 count drift")
    _require(len(batch01) == len(batch02) == len(batch03_roster) == len(batch03_frozen) == 20, "batch roster count drift")

    b1_ids = {_identity(row, "cell_id") for row in batch01}
    b2_ids = {_identity(row, "cell_identity_sha256") for row in batch02}
    b3_ids = {_identity(row, "cell_identity_sha256") for row in batch03_frozen}
    b3_roster_ids = {_identity(row, "cell_identity_sha256") for row in batch03_roster}
    frozen117_ids = {_identity(row, "cell_identity_sha256") for row in frozen117}
    _require(b1_ids <= frozen117_ids, "Batch01 not contained in frozen117")
    _require(b3_ids == b3_roster_ids, "Batch03 frozen/roster identity drift")
    _require(frozen117_ids.isdisjoint(b2_ids) and frozen117_ids.isdisjoint(b3_ids) and b2_ids.isdisjoint(b3_ids), "frozen batch overlap")
    frozen157 = frozen117_ids | b2_ids | b3_ids
    _require(len(frozen157) == 157, "frozen157 identity closure drift")

    reconstructed41 = [
        row for row in remaining101 if _identity(row, "cell_id") not in b1_ids | b2_ids | b3_ids
    ]
    _require(len(reconstructed41) == 41, "reconstructed remaining41 count drift")

    deferred_ledger = [
        row for row in batch03_ledger if row["selection_disposition"] == "PLANNED_REMAINING_AFTER_BATCH03"
    ]
    _require(len(deferred_ledger) == 41, "batch03 deferred count drift")
    for rank, (source, prior) in enumerate(zip(reconstructed41, deferred_ledger), 1):
        _require(prior["after_batch03_remaining_rank"] == str(rank), f"remaining41 rank drift: {rank}")
        _require(prior["program_id"] == source["program_id"], f"remaining41 program drift: {rank}")
        _require(prior["cell_identity_sha256"] == source["cell_id"], f"remaining41 cell drift: {rank}")
        _require(prior["source_sha256"] == source["source_sha256"], f"remaining41 source drift: {rank}")
        _require(prior["remaining61_rank"] == str(rank + 20), f"remaining61 rank citation drift: {rank}")

    remaining61_tail = remaining61[20:]
    _require(len(remaining61_tail) == 41, "remaining61 tail drift")
    for rank, (source, prior61) in enumerate(zip(reconstructed41, remaining61_tail), 1):
        _require(prior61["program_id"] == source["program_id"], f"remaining61-tail program drift: {rank}")
        _require(prior61["cell_identity_sha256"] == source["cell_id"], f"remaining61-tail cell drift: {rank}")

    formal_ids = {_identity(row, "cell_identity_sha256") for row in formal}
    remaining41_ids = {_identity(row, "cell_id") for row in reconstructed41}
    _require(frozen157.isdisjoint(remaining41_ids), "remaining41 overlaps frozen157")
    _require(frozen157 | remaining41_ids == formal_ids, "198=157+41 identity omission drift")

    roster: list[dict[str, str]] = []
    ledger: list[dict[str, str]] = []
    remaining21: list[dict[str, str]] = []
    for remaining_rank, row in enumerate(reconstructed41, 1):
        selected = remaining_rank <= 20
        remaining61_rank = str(remaining_rank + 20)
        core = {
            "selection_rank": str(remaining_rank) if selected else "",
            "remaining41_rank": str(remaining_rank),
            "remaining61_rank": remaining61_rank,
            "source_roster_rank": row["roster_rank"],
            "program_id": row["program_id"],
            "cell_identity_sha256": row["cell_id"],
            "dataset": row["dataset"],
            "task_id": row["task_id"],
            "task_identity_sha256": row["task_identity_sha256"],
            "model": row["model"],
            "condition": row["condition"],
            "seed": row["seed"],
            "generation_id": row["generation_id"],
            "source_artifact_path": row["raw_generation_reference"],
            "source_sha256": row["source_sha256"],
            "evaluation_source_sha256": row["evaluation_source_sha256"],
            "selection_rule": SELECTION_RULE,
            "selection_rule_citation": (
                f"{BATCH03_LEDGER.as_posix()}#after_batch03_remaining_rank={remaining_rank}"
            ),
            "upstream_result_citation": (
                f"{REMAINING101.as_posix()}#roster_rank={row['roster_rank']};"
                f"program_id={row['program_id']}"
            ),
        }
        if selected:
            source_text = _load_evaluation_source(repo, row["raw_generation_reference"])
            _require(
                _sha(source_text.encode("utf-8")) == row["source_sha256"],
                f"source sha mismatch: {row['program_id']}",
            )
            roster.append(core)
        else:
            remaining21.append(
                {
                    "after_batch04_remaining_rank": str(remaining_rank - 20),
                    "remaining41_rank": str(remaining_rank),
                    "remaining61_rank": remaining61_rank,
                    "source_roster_rank": row["roster_rank"],
                    "program_id": row["program_id"],
                    "cell_identity_sha256": row["cell_id"],
                    "task_id": row["task_id"],
                    "condition": row["condition"],
                    "seed": row["seed"],
                    "generation_id": row["generation_id"],
                    "source_artifact_path": row["raw_generation_reference"],
                    "source_sha256": row["source_sha256"],
                }
            )
        ledger.append(
            {
                **core,
                "selection_disposition": "BATCH04_SELECTED" if selected else "PLANNED_REMAINING_AFTER_BATCH04",
                "after_batch04_remaining_rank": "" if selected else str(remaining_rank - 20),
            }
        )

    selected_ids = {_identity(row, "cell_identity_sha256") for row in roster}
    deferred_ids = {_identity(row, "cell_identity_sha256") for row in remaining21}
    _require(len(roster) == len(selected_ids) == 20, "Batch04 uniqueness drift")
    _require(len(deferred_ids) == 21 and selected_ids.isdisjoint(deferred_ids), "20+21 partition drift")
    _require(selected_ids | deferred_ids == remaining41_ids, "remaining41 selection omission drift")
    _require(selected_ids.isdisjoint(frozen157), "Batch04 frozen157 overlap")
    _require(
        [row["program_id"] for row in roster] == [row["program_id"] for row in reconstructed41[:20]],
        "fixed-order selection drift",
    )
    _require(len({row["task_id"] for row in roster}) >= 1, "task identity missing")
    _require(all(row["condition"] and row["seed"] and row["generation_id"] for row in roster), "identity field empty")

    source_counts = Counter(row["source_sha256"] for row in roster)
    shared_rows: list[dict[str, str]] = []
    for source_sha, count in sorted(source_counts.items()):
        if count < 2:
            continue
        members = [row for row in roster if row["source_sha256"] == source_sha]
        cell_ids = {row["cell_identity_sha256"] for row in members}
        _require(len(cell_ids) == count, f"illegal duplicate cell under shared source: {source_sha}")
        shared_rows.append(
            {
                "source_sha256": source_sha,
                "cell_count": str(count),
                "selection_ranks_json": json.dumps([row["selection_rank"] for row in members], separators=(",", ":")),
                "program_ids_json": json.dumps([row["program_id"] for row in members], separators=(",", ":")),
                "cell_identity_sha256_json": json.dumps(sorted(cell_ids), separators=(",", ":")),
                "legality": "LEGAL_SHARED_SOURCE_DISTINCT_CELLS",
                "notes": "same evaluation_source across distinct cell identities; not a duplicate cell",
            }
        )
    _require(len(source_counts) == 19 and len(shared_rows) == 1, "shared-source expectation drift")

    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "formal_population": 198,
        "frozen_before_batch04": 157,
        "remaining_before_batch04": 41,
        "batch04_selected": 20,
        "planned_remaining_after_batch04": 21,
        "formal_closure": "198=157+20+21",
        "selection_closure": "41=20+21",
        "unique_batch04_program_id": len({row["program_id"] for row in roster}),
        "unique_batch04_cell_identity": len(selected_ids),
        "unique_batch04_source_sha256": len(source_counts),
        "legal_shared_source_groups": len(shared_rows),
        "overlap_with_frozen157": 0,
        "overlap_with_batch01": 0,
        "overlap_with_batch02": 0,
        "overlap_with_batch03": 0,
        "duplicate_identities": 0,
        "omitted_identities": 0,
        "programs_readable_nonempty": 20,
        "selection_rule": SELECTION_RULE,
        "selection_uses_program_content_or_adjudication": False,
        "taxonomy_judgments_created": 0,
        "upstream_modified": False,
        "batch05_started": False,
    }
    return {
        "roster": roster,
        "ledger": ledger,
        "remaining21": remaining21,
        "shared_sources": shared_rows,
        "summary": summary,
    }


def _report(summary: dict[str, Any], roster_sha: str) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch04 固定 20-cell roster",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Roster SHA-256：`{roster_sha}`**",
            "",
            "## 閉合",
            "",
            "- 198 = frozen157 + Batch04 20 + planned remaining21",
            "- 41 = Batch04 20 + planned remaining21",
            "- 與 frozen157／Batch01–03 overlap 均為 0",
            "- duplicate cell=0；omission=0",
            "- unique source=19；合法共享 source 組=1",
            "- 20/20 程式與靜態證據可讀且非空",
            "",
            "Batch04 嚴格取既有 remaining41 固定排序的前20格；未依程式內容、錯誤類型、可修復性或預期結果挑選。",
            "",
            "本 revision 未裁決、未 freeze、未開始 Batch05，亦未執行 candidate、tests、EvalPlus、diagnostics、validation、Healer或模型。",
        ]
    ) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["roster"])
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
    sha_ledger = {
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
        "formal198_sha256": SOURCE_HASHES[FORMAL198],
        "remaining101_sha256": SOURCE_HASHES[REMAINING101],
        "frozen117_sha256": SOURCE_HASHES[FROZEN117],
        "batch01_roster_sha256": SOURCE_HASHES[BATCH01_ROSTER],
        "batch02_roster_sha256": SOURCE_HASHES[BATCH02_ROSTER],
        "batch02_records_sha256": SOURCE_HASHES[BATCH02_RECORDS],
        "batch03_roster_sha256": SOURCE_HASHES[BATCH03_ROSTER],
        "batch03_frozen_records_sha256": SOURCE_HASHES[BATCH03_FROZEN],
        "batch03_frozen_manifest_sha256": SOURCE_HASHES[BATCH03_FROZEN_MANIFEST],
        "batch04_roster_sha256": _sha(roster_bytes),
    }
    outputs = {
        "batch04_roster.csv": roster_bytes,
        "selection_ledger.csv": _csv_bytes(LEDGER_FIELDS, analysis["ledger"]),
        "remaining21_roster.csv": _csv_bytes(REMAINING21_FIELDS, analysis["remaining21"]),
        "shared_source_ledger.csv": _csv_bytes(SHARED_SOURCE_FIELDS, analysis["shared_sources"]),
        "remaining_closure_summary.json": _json_bytes(analysis["summary"]),
        "sha_ledger.json": _json_bytes(sha_ledger),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], _sha(roster_bytes)).encode("utf-8"),
    }
    provenance = {
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "batch04_roster_sha256": _sha(roster_bytes),
        "rebuild_basis": (
            "remaining101 fixed order minus frozen Batch01/Batch02/Batch03; "
            "exact row closure against Batch03 deferred remaining41"
        ),
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "no_adjudication": True,
        "batch04_frozen": False,
        "batch05_started": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "formal_population": 198,
        "frozen_cells": 157,
        "batch04_cells": 20,
        "remaining_after_selection": 21,
        "batch04_roster_sha256": _sha(roster_bytes),
        "batch03_frozen_records_sha256": SOURCE_HASHES[BATCH03_FROZEN],
        "batch03_frozen_manifest_sha256": SOURCE_HASHES[BATCH03_FROZEN_MANIFEST],
        "taxonomy_sha256": SOURCE_HASHES[TAXONOMY],
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
    print(f"roster_sha256={manifest['batch04_roster_sha256']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
