#!/usr/bin/env python3
"""Build the zero-execution Candidate B r003 Batch02 20-cell roster.

This module only reconciles already-frozen taxonomy records with the existing
remaining101 fixed roster.  It does not adjudicate cells and does not execute
candidates, diagnostics, EvalPlus, Healer, or models.
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
    "candidate_b_r003_taxonomy_v31_remaining81_batch02_20cell_roster_v1"
)
START_HEAD = "79a6543ae888a0cedf3694a9985d88c4f97e0713"
STATUS = "READY_FOR_BATCH02_20CELL_ADJUDICATION"
PLANNING_MARK = "ROSTER_AND_SUMMARY_ONLY_NO_ADJUDICATION"

PROGRESS_V2 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_frozen_progress_census_v2/manifest.json"
)
PROGRESS_V2_PROVENANCE = PROGRESS_V2.with_name("provenance.json")
PROGRESS_V1 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_frozen_progress_census_v1/manifest.json"
)
G2 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
MODULE_EXCEPTION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1/"
    "ai_provisional_adjudication.csv"
)
MULTIPLE_SIGNAL = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/"
    "ai_provisional_adjudication.csv"
)
OUTPUT_SHAPE20 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1/"
    "frozen_adjudication.csv"
)
BATCH01 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_batch01_20cell_frozen_v1/"
    "frozen_adjudication.csv"
)
BATCH01_ROSTER = BATCH01.with_name("frozen_roster.csv")
REMAINING101 = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1/"
    "remaining101_roster.csv"
)
REMAINING101_MANIFEST = REMAINING101.with_name("manifest.json")
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
PAIRED_CELLS = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv"
)

SOURCE_HASHES: dict[Path, str] = {
    PROGRESS_V2: "67fcd910bbfb5c07beb9c9231464b871e196931f6874059c59d28b2cacaddd71",
    PROGRESS_V2_PROVENANCE: "33ec1b9b15ddabae46ac8734227b684a7a849c69d039c9d0a3aac3864228dab0",
    PROGRESS_V1: "7eee4c9e94ae8ea3b42bfb8921e546533e12ac618b18703edf7d18993f254e1a",
    G2: "90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119",
    MODULE_EXCEPTION: "8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7",
    MULTIPLE_SIGNAL: "dc2e7202c048400d32e019fed6940051f65ca1a67b865727152d94dccf302d70",
    OUTPUT_SHAPE20: "eda69f61051228ff9d976ec57f6dcd9febea95a2c541095edac19f55074eac1f",
    BATCH01: "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb",
    BATCH01_ROSTER: "9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533",
    REMAINING101: "8fe0f5d95e7c6e86cda5f18dabfecae486120c50eeaf1baad6fe6c12b23143f6",
    REMAINING101_MANIFEST: "d2a7478da6852ba1a6592d2d1701b8ad3aee3bc018824a365aab9670fa0438bd",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    PAIRED_CELLS: "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
}

TAXONOMY_V31_REFERENCE = {
    "filename": "AI_生成程式共同失敗分類標準_實際使用版_v3.1.md",
    "sha256": "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
    "bytes": 26950,
    "status": "EXTERNAL_PLANNING_REFERENCE_NOT_INGESTED_INTO_REPO_GOVERNANCE",
}

FROZEN_SPECS = (
    ("g2_module_27", G2, 27, "proposed_primary_failure_layer", "proposed_healer_eligibility", "cell_identity_sha256"),
    ("module_exception_37", MODULE_EXCEPTION, 37, "provisional_primary_layer", "healer_eligibility", "cell_identity_sha256"),
    ("multiple_signal_13", MULTIPLE_SIGNAL, 13, "provisional_primary_layer", "healer_eligibility", "cell_identity_sha256"),
    ("output_contract_shape_20", OUTPUT_SHAPE20, 20, "primary_layer", "healer_eligibility", "cell_identity_sha256"),
    ("batch01_20", BATCH01, 20, "primary_layer", "healer_eligibility", "cell_id"),
)

AUDIT_FIELDS = (
    "frozen_sequence",
    "frozen_set",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "source_sha256",
    "primary_layer",
    "healer_eligibility",
    "transformed",
    "healer_transition",
    "verified_rescue",
    "regression",
)
ROSTER_FIELDS = (
    "batch_rank",
    "source_roster_rank",
    "cell_identity_sha256",
    "program_id",
    "source_sha256",
    "task_id",
    "seed",
    "generation_id",
    "condition",
    "evaluation_source_sha256",
    "task_identity_sha256",
    "selection_rule",
    "planning_annotation",
)
REMAINING_FIELDS = (
    "remaining_rank",
    "source_roster_rank",
    "cell_identity_sha256",
    "program_id",
    "source_sha256",
    "task_id",
    "seed",
    "generation_id",
    "condition",
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


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = repo / relative
        _require(path.is_file(), f"missing source: {relative.as_posix()}")
        _require(_sha(path.read_bytes()) == digest, f"source hash drift: {relative.as_posix()}")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    progress = json.loads((repo / PROGRESS_V2).read_text(encoding="utf-8"))
    _require(progress["formal_population"] == 198, "formal population drift")
    _require(progress["total_frozen"] == 117, "frozen progress drift")
    _require(progress["remaining"] == 81, "remaining progress drift")

    preparation_rows = _read_csv(repo, PREPARATION)
    _require(len(preparation_rows) == 198, "formal preparation must contain 198 cells")
    prep_by_program = {row["program_id"]: row for row in preparation_rows}
    _require(len(prep_by_program) == 198, "formal preparation program_id uniqueness drift")
    _require(len({row["cell_identity_sha256"] for row in preparation_rows}) == 198, "formal cell identity drift")

    paired_rows = [
        row for row in _read_csv(repo, PAIRED_CELLS) if row["prompt_condition"] == "Candidate_B"
    ]
    paired_by_program = {row["program_id"]: row for row in paired_rows}
    _require(len(paired_rows) == 300 and len(paired_by_program) == 300, "Candidate B paired cells drift")

    audit_rows: list[dict[str, str]] = []
    frozen_ids: set[str] = set()
    sequence = 0
    for set_name, path, expected, primary_field, healer_field, identity_field in FROZEN_SPECS:
        rows = _read_csv(repo, path)
        _require(len(rows) == expected, f"{set_name} count drift")
        for row in rows:
            sequence += 1
            program_id = row["program_id"]
            _require(program_id not in frozen_ids, f"duplicate frozen program_id: {program_id}")
            frozen_ids.add(program_id)
            prep = prep_by_program.get(program_id)
            pair = paired_by_program.get(program_id)
            _require(prep is not None, f"frozen program absent from formal198: {program_id}")
            _require(pair is not None, f"frozen program absent from Candidate B paired cells: {program_id}")
            _require(row[identity_field] == prep["cell_identity_sha256"], f"cell identity drift: {program_id}")
            _require(pair["task_id"] == prep["task_id"], f"paired task identity drift: {program_id}")
            _require(pair["seed"] == prep["seed"], f"paired seed identity drift: {program_id}")
            _require(pair["generation_id"] == prep["generation_id"], f"paired generation identity drift: {program_id}")
            _require(
                pair["h0_source_sha256"] == prep["evaluation_source_sha256"],
                f"paired H0 source identity drift: {program_id}",
            )
            supplied_source = row.get("source_sha256") or row.get("evaluation_source_sha256") or ""
            if supplied_source:
                _require(supplied_source == prep["evaluation_source_sha256"], f"frozen source drift: {program_id}")
            transformed = pair["source_changed_by_healer"] == "true"
            transition = pair["healer_transition"]
            audit_rows.append(
                {
                    "frozen_sequence": str(sequence),
                    "frozen_set": set_name,
                    "program_id": program_id,
                    "cell_identity_sha256": prep["cell_identity_sha256"],
                    "task_id": prep["task_id"],
                    "seed": prep["seed"],
                    "generation_id": prep["generation_id"],
                    "source_sha256": prep["evaluation_source_sha256"],
                    "primary_layer": row[primary_field],
                    "healer_eligibility": row[healer_field],
                    "transformed": str(transformed).lower(),
                    "healer_transition": transition,
                    "verified_rescue": str(transition == "fail_to_pass").lower(),
                    "regression": str(transition == "pass_to_fail").lower(),
                }
            )

    _require(sequence == 117 and len(frozen_ids) == 117, "frozen117 uniqueness drift")
    _require(len({row["cell_identity_sha256"] for row in audit_rows}) == 117, "frozen cell identity uniqueness drift")

    remaining101 = _read_csv(repo, REMAINING101)
    _require(len(remaining101) == 101, "remaining101 count drift")
    remaining101_ids = [row["program_id"] for row in remaining101]
    _require(len(set(remaining101_ids)) == 101, "remaining101 program_id uniqueness drift")
    _require(set(remaining101_ids).isdisjoint(frozen_ids - {row["program_id"] for row in _read_csv(repo, BATCH01)}), "remaining101 intersects frozen97")

    batch01_ids = {row["program_id"] for row in _read_csv(repo, BATCH01)}
    frozen97_ids = frozen_ids - batch01_ids
    _require(len(frozen97_ids) == 97 and len(batch01_ids) == 20, "frozen partition drift")
    _require(batch01_ids <= set(remaining101_ids), "Batch01 not contained in remaining101")
    _require(frozen97_ids | set(remaining101_ids) == set(prep_by_program), "97+101 formal population closure drift")

    remaining81 = [row for row in remaining101 if row["program_id"] not in batch01_ids]
    _require(len(remaining81) == 81, "remaining81 count drift")
    batch02_source = remaining81[:20]
    after_batch02 = remaining81[20:]
    _require(len(batch02_source) == 20 and len(after_batch02) == 61, "Batch02 partition drift")

    batch02_rows: list[dict[str, str]] = []
    for rank, row in enumerate(batch02_source, 1):
        prep = prep_by_program[row["program_id"]]
        _require(row["cell_id"] == prep["cell_identity_sha256"], f"remaining cell identity drift: {row['program_id']}")
        _require(row["source_sha256"] == prep["evaluation_source_sha256"], f"remaining source drift: {row['program_id']}")
        for field in ("task_id", "seed", "generation_id"):
            _require(row[field] == prep[field], f"remaining {field} drift: {row['program_id']}")
        batch02_rows.append(
            {
                "batch_rank": str(rank),
                "source_roster_rank": row["roster_rank"],
                "cell_identity_sha256": prep["cell_identity_sha256"],
                "program_id": row["program_id"],
                "source_sha256": row["source_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "generation_id": row["generation_id"],
                "condition": row["condition"],
                "evaluation_source_sha256": row["evaluation_source_sha256"],
                "task_identity_sha256": row["task_identity_sha256"],
                "selection_rule": "remaining101_fixed_order_excluding_frozen_batch01_take_first20",
                "planning_annotation": PLANNING_MARK,
            }
        )

    remaining61_rows = [
        {
            "remaining_rank": str(rank),
            "source_roster_rank": row["roster_rank"],
            "cell_identity_sha256": row["cell_id"],
            "program_id": row["program_id"],
            "source_sha256": row["source_sha256"],
            "task_id": row["task_id"],
            "seed": row["seed"],
            "generation_id": row["generation_id"],
            "condition": row["condition"],
        }
        for rank, row in enumerate(after_batch02, 1)
    ]

    _require({row["program_id"] for row in batch02_rows}.isdisjoint(frozen_ids), "Batch02 intersects frozen117")
    _require(len({row["cell_identity_sha256"] for row in batch02_rows}) == 20, "Batch02 cell identity uniqueness drift")
    _require(len({row["program_id"] for row in remaining61_rows}) == 61, "remaining61 uniqueness drift")

    primary = Counter(row["primary_layer"] for row in audit_rows)
    healer = Counter(row["healer_eligibility"] for row in audit_rows)
    transitions = Counter(row["healer_transition"] for row in audit_rows)
    transformed = sum(row["transformed"] == "true" for row in audit_rows)
    rescues = sum(row["verified_rescue"] == "true" for row in audit_rows)
    regressions = sum(row["regression"] == "true" for row in audit_rows)
    _require(primary == Counter({"L4": 68, "UNRESOLVED": 29, "L5": 17, "L2": 3}), f"primary drift: {primary}")
    _require(healer == Counter({"abstain": 94, "conditional": 23}), f"healer drift: {healer}")
    _require(transformed == 0 and rescues == 0 and regressions == 0, "frozen117 paired outcome drift")

    summary = {
        "status": STATUS,
        "formal_population": 198,
        "frozen_cells": 117,
        "remaining_before_batch02_selection": 81,
        "batch02_cells": 20,
        "remaining_after_batch02_selection": 61,
        "unique_frozen_program_id": len(frozen_ids),
        "unique_frozen_cell_identity": len({row["cell_identity_sha256"] for row in audit_rows}),
        "unique_frozen_source_sha256": len({row["source_sha256"] for row in audit_rows}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "healer_eligibility_distribution": {
            "eligible": int(healer.get("eligible", 0)),
            "conditional": int(healer.get("conditional", 0)),
            "abstain": int(healer.get("abstain", 0)),
        },
        "transformed": transformed,
        "verified_rescue": rescues,
        "regression": regressions,
        "healer_transition_distribution": dict(sorted(transitions.items())),
        "identity_basis": "program_id+cell_identity_sha256+task_id+seed+generation_id+H0_source_sha256",
        "execution_accounts_counted_as_cells": 0,
        "duplicate_seed_rows_counted": 0,
        "legacy_154_case_forensic_rows_counted": 0,
    }
    return {
        "audit_rows": audit_rows,
        "batch02_rows": batch02_rows,
        "remaining61_rows": remaining61_rows,
        "summary": summary,
    }


def _report(summary: dict[str, Any], roster_sha: str) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch02 20-cell roster",
            "",
            f"**唯一 verdict：`{STATUS}`**",
            "",
            "## Frozen117 彙總",
            "",
            f"- primary layer：{summary['primary_layer_distribution']}",
            f"- Healer eligibility：{summary['healer_eligibility_distribution']}",
            f"- unique cell identity：{summary['unique_frozen_cell_identity']}",
            f"- transformed：{summary['transformed']}",
            f"- verified rescue：{summary['verified_rescue']}",
            f"- regression：{summary['regression']}",
            "",
            "verified rescue/regression 以同一 program/cell identity 的 H0→H1 paired transition 核對；",
            "不以 execution account 為 cell，不重複計 seed，也不納入舊 154-case forensic。",
            "",
            "## Batch02",
            "",
            "- selection：remaining101 固定排序排除 frozen Batch01 20 格後取前 20 格",
            f"- roster SHA-256：`{roster_sha}`",
            "- 與 frozen117 重疊：0",
            "- roster selection 後尚餘：61",
            "",
            "本 revision 只建 roster、identity audit、彙總與 provenance；沒有新裁決或任何執行。",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    audit_bytes = _csv_bytes(AUDIT_FIELDS, analysis["audit_rows"])
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["batch02_rows"])
    remaining_bytes = _csv_bytes(REMAINING_FIELDS, analysis["remaining61_rows"])
    summary_bytes = _json_bytes(analysis["summary"])
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "candidate_imports": 0,
        "diagnostics_executions": 0,
        "evalplus_correctness_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    execution_bytes = _json_bytes(execution_counts)
    roster_sha = _sha(roster_bytes)
    report_bytes = _report(analysis["summary"], roster_sha).encode("utf-8")
    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "planning_annotation": PLANNING_MARK,
        "start_head": START_HEAD,
        "selection_rule": "remaining101 fixed roster order, exclude frozen Batch01, take first 20",
        "formal_reconciliation": "198=117+81",
        "selection_reconciliation": "81=20+61",
        "batch02_roster_sha256": roster_sha,
        "batch02_cells": 20,
        "remaining_after_selection": 61,
        "taxonomy_v31_planning_reference": TAXONOMY_V31_REFERENCE,
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "source_files_modified": False,
        "no_adjudication": True,
        **execution_counts,
    }
    provenance_bytes = _json_bytes(provenance)
    outputs = {
        "frozen117_cell_identity_audit.csv": audit_bytes,
        "frozen117_summary.json": summary_bytes,
        "batch02_roster.csv": roster_bytes,
        "remaining61_roster.csv": remaining_bytes,
        "execution_counts.json": execution_bytes,
        "report_zh.md": report_bytes,
        "provenance.json": provenance_bytes,
    }
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "start_head": START_HEAD,
        "frozen_cells": 117,
        "remaining_before_selection": 81,
        "batch02_cells": 20,
        "remaining_after_selection": 61,
        "batch02_roster_sha256": roster_sha,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution_counts,
    }
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output_dir / name).write_bytes(data)
    return output_dir


def main() -> None:
    output_dir = write_outputs()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output_dir}")
    print(f"verdict={manifest['status']}")
    print(f"batch02_roster_sha256={manifest['batch02_roster_sha256']}")
    print(f"remaining_after_selection={manifest['remaining_after_selection']}")


if __name__ == "__main__":
    main()
