#!/usr/bin/env python3
"""Formal freeze for remaining121 output/contract-shape 20-cell provisional v2.

FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION

Creates an independent freeze revision and a progress census revision.
Does not overwrite provisional v1/v2, audits, or previously frozen batches.
Does not execute programs or call models.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep


REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1"
)
PROGRESS_OUTPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_frozen_progress_census_v1"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
PROGRESS_STATUS = "TAXONOMY_V3_FROZEN_PROGRESS_CENSUS"
ADJUDICATION_IDENTITY = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/freeze_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1.py"
)

NEXT_BATCH_ROSTER = planning_prep.OUTPUT_RELATIVE / "next_batch_roster.csv"
NEXT_BATCH_ROSTER_SHA256 = "b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804"
MACHINE_CENSUS_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1/manifest.json"
)
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
MULTIPLE_SIGNAL_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/manifest.json"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

V1_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v1"
)
V1_MANIFEST = V1_DIR / "manifest.json"
V1_CSV = V1_DIR / "ai_provisional_adjudication.csv"
V1_MANIFEST_SHA256 = "548486f59c5a42ef03375ace981bbd7219c5f94ae0b374ac3be1c305805fbf8d"
V1_CSV_SHA256 = "87bf9dd0715cac8581028c98ffff0c1d0c6a91154bbfffe9470f244fe741f4f7"

V2_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2"
)
V2_MANIFEST = V2_DIR / "manifest.json"
V2_CSV = V2_DIR / "ai_provisional_adjudication.csv"
V2_DELTA = V2_DIR / "revision_delta_v1_to_v2.csv"
V2_MANIFEST_SHA256 = "11f59ee2b9296db4a13a055354dd9e554bd287839e9a6cc1f1c1a5604d8f18e6"
V2_CSV_SHA256 = "7f89e457e5a3e19a8c13a0651feed0b71d27e3877653927c2360f37c5c119a78"

POST_AUDIT_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_post_adjudication_audit_v1/"
    "manifest.json"
)
POST_AUDIT_MANIFEST_SHA256 = (
    "73fc418fe9c15bc35ade4ebe208d436eea516ac89860a962e78bea173bc1b508"
)

FINAL_AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_v2_final_freeze_audit_v1"
)
FINAL_AUDIT_MANIFEST = FINAL_AUDIT_DIR / "manifest.json"
FINAL_AUDIT_MANIFEST_SHA256 = (
    "701dc681cad277e51bf984843358fe04c8cd0beb9d3e66db11f14d70dd5fbdd6"
)
FINAL_AUDIT_VERDICT = "READY_TO_FREEZE_COMMIT_AND_PUSH_20_CELL_V2"

G2_CSV = planning_prep.G2_PROVISIONAL_CSV
MODULE_EXCEPTION_CSV = planning_prep.MODULE_EXCEPTION_CSV
MULTIPLE_SIGNAL_CSV = planning_prep.MULTIPLE_SIGNAL_CSV

TARGET_CELLS = 20
PREVIOUSLY_FROZEN = 77
NEWLY_FROZEN = 20
TOTAL_FROZEN = 97
REMAINING = 101
FORMAL_POPULATION = 198

SOURCE_HASHES: dict[Path, str] = {
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    V1_CSV: V1_CSV_SHA256,
    V2_MANIFEST: V2_MANIFEST_SHA256,
    V2_CSV: V2_CSV_SHA256,
    POST_AUDIT_MANIFEST: POST_AUDIT_MANIFEST_SHA256,
    FINAL_AUDIT_MANIFEST: FINAL_AUDIT_MANIFEST_SHA256,
    G2_CSV: planning_prep.G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: planning_prep.MODULE_EXCEPTION_CSV_SHA256,
    MULTIPLE_SIGNAL_CSV: planning_prep.MULTIPLE_SIGNAL_CSV_SHA256,
}

FROZEN_FIELDS = (
    "freeze_rank",
    "program_id",
    "task_id",
    "source_sha256",
    "seed",
    "cell_identity_sha256",
    "condition",
    "observed_machine_signal",
    "primary_layer",
    "secondary_layers",
    "mechanism_tags",
    "failure_chain",
    "outcome_validity",
    "healer_eligibility",
    "abstain_reason",
    "confidence",
    "evidence_citations",
    "adjudication_identity",
    "adjudication_status",
    "frozen_from_revision",
    "freeze_status",
)

BATCH_REGISTRY_FIELDS = (
    "batch_id",
    "cells",
    "unique_program_id",
    "unique_source_sha256",
    "unique_task_id",
    "source_revision",
    "source_manifest_sha256",
    "freeze_revision",
    "notes",
)


class FreezeError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _processed77(repo: Path) -> set[str]:
    ids: set[str] = set()
    for roster_path in (G2_CSV, MODULE_EXCEPTION_CSV, MULTIPLE_SIGNAL_CSV):
        ids.update(row["program_id"] for row in _read_csv(repo / roster_path))
    return ids


def build_freeze_rows(repo: Path = REPO_ROOT) -> list[dict[str, str]]:
    verify_sources(repo)
    final_manifest = json.loads((repo / FINAL_AUDIT_MANIFEST).read_text(encoding="utf-8"))
    _require(
        final_manifest.get("audit_verdict") == FINAL_AUDIT_VERDICT,
        f"final audit verdict drift: {final_manifest.get('audit_verdict')}",
    )
    roster = _read_csv(repo / NEXT_BATCH_ROSTER)
    v2_rows = _read_csv(repo / V2_CSV)
    delta = _read_csv(repo / V2_DELTA)
    _require(len(roster) == TARGET_CELLS, "roster size")
    _require(len(v2_rows) == TARGET_CELLS, "v2 size")
    _require([row["program_id"] for row in roster] == [row["program_id"] for row in v2_rows], "order drift")
    processed = _processed77(repo)
    _require(len(processed) == PREVIOUSLY_FROZEN, "processed77 size")
    _require(not ({row["program_id"] for row in v2_rows} & processed), "intersection with processed77")
    _require(len(delta) == 4, "v1→v2 must be 4 approved field changes")
    _require(len({row["program_id"] for row in delta}) == 2, "affected cells must be 2")

    primary = Counter(row["primary_layer"] for row in v2_rows)
    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    confidence = Counter(row["confidence"] for row in v2_rows)
    _require(dict(primary) == {"UNRESOLVED": 12, "L5": 7, "L2": 1}, f"primary drift {dict(primary)}")
    _require(dict(healer) == {"abstain": 20}, f"healer drift {dict(healer)}")
    _require(dict(confidence) == {"HIGH": 8, "LOW": 12}, f"confidence drift {dict(confidence)}")
    _require(
        all(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in v2_rows),
        "outcome drift",
    )
    _require(
        all(row["adjudication_status"] == ADJUDICATION_IDENTITY for row in v2_rows),
        "adjudication identity drift",
    )

    frozen_rows: list[dict[str, str]] = []
    for rank, (roster_row, adj) in enumerate(zip(roster, v2_rows, strict=True), 1):
        _require(roster_row["program_id"] == adj["program_id"], "program_id mismatch")
        _require(
            roster_row["evaluation_source_sha256"] == adj["source_sha256"],
            "source sha mismatch",
        )
        frozen_rows.append(
            {
                "freeze_rank": str(rank),
                "program_id": adj["program_id"],
                "task_id": adj["task_id"],
                "source_sha256": adj["source_sha256"],
                "seed": adj["seed"],
                "cell_identity_sha256": adj["cell_identity_sha256"],
                "condition": roster_row["condition"],
                "observed_machine_signal": adj["observed_machine_signal"],
                "primary_layer": adj["primary_layer"],
                "secondary_layers": adj["secondary_layers"],
                "mechanism_tags": adj["mechanism_tags"],
                "failure_chain": adj["failure_chain"],
                "outcome_validity": adj["outcome_validity"],
                "healer_eligibility": adj["healer_eligibility"],
                "abstain_reason": adj["abstain_reason"],
                "confidence": adj["confidence"],
                "evidence_citations": adj["evidence_citations"],
                "adjudication_identity": adj["adjudication_identity"],
                "adjudication_status": ADJUDICATION_IDENTITY,
                "frozen_from_revision": V2_DIR.name,
                "freeze_status": STATUS,
            }
        )
    _require(len(frozen_rows) == TARGET_CELLS, "frozen row count")
    _require(len({row["program_id"] for row in frozen_rows}) == TARGET_CELLS, "duplicate freeze")
    return frozen_rows


def _freeze_report(rows: list[dict[str, str]]) -> str:
    primary = Counter(row["primary_layer"] for row in rows)
    return "\n".join(
        [
            "# Frozen batch：remaining121 output/contract-shape 20-cell v2",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Adjudication identity：`{ADJUDICATION_IDENTITY}`**",
            "",
            "## 引用",
            "",
            f"- provisional v2 manifest：`{V2_MANIFEST_SHA256}`",
            f"- provisional v2 csv：`{V2_CSV_SHA256}`",
            f"- final freeze audit manifest：`{FINAL_AUDIT_MANIFEST_SHA256}`",
            f"- final freeze audit verdict：`{FINAL_AUDIT_VERDICT}`",
            f"- next-batch roster：`{NEXT_BATCH_ROSTER_SHA256}`",
            "",
            "## Batch",
            "",
            "- cells=20 / program=20 / source=20 / task=13",
            "- condition=Candidate_B/H0",
            "- processed77 intersection=0",
            "- 20 個 source-level evidence units（跨 13 task），不是 20 個獨立 task",
            "",
            "## 統計",
            "",
            f"- primary：{dict(sorted(primary.items()))}",
            "- secondary：全空",
            "- healer：abstain=20，conditional=0，eligible=0",
            "- outcome：VALID_MODEL_OUTCOME=20",
            "- confidence：HIGH=8，LOW=12",
            "",
            "## Progress",
            "",
            f"- previously frozen={PREVIOUSLY_FROZEN}",
            f"- newly frozen={NEWLY_FROZEN}",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}（{FORMAL_POPULATION}-{TOTAL_FROZEN}）",
            "",
            "已分析並凍結 97 格，剩餘 101 格；本批 20 格全部為 Healer abstain，沒有 eligible 或 conditional 候選。",
            "",
            "## 邊界",
            "",
            "- 本 revision 不覆寫 provisional v1/v2 或任何 audit",
            "- 尚未開始剩餘 101 格；未執行 Healer",
            "",
        ]
    )


def _progress_report() -> str:
    return "\n".join(
        [
            "# Taxonomy v3 frozen progress census v1",
            "",
            f"**狀態：`{PROGRESS_STATUS}`**",
            "",
            "## 總進度",
            "",
            f"- formal unresolved population={FORMAL_POPULATION}",
            f"- previously frozen={PREVIOUSLY_FROZEN}（G2 27 + module_exception 37 + multiple_signal 13）",
            f"- newly frozen this revision={NEWLY_FROZEN}（output/contract-shape 20）",
            f"- total frozen={TOTAL_FROZEN}",
            f"- remaining={REMAINING}",
            "",
            "## 研究敘述",
            "",
            "已分析並凍結 97 格，剩餘 101 格；本批 20 格全部為 Healer abstain，沒有 eligible 或 conditional 候選。",
            "",
            "## Batches",
            "",
            "| Batch | Cells | Notes |",
            "|---|---:|---|",
            "| G2_module provisional | 27 | previously frozen |",
            "| remaining171 module_exception provisional | 37 | previously frozen |",
            "| remaining134 multiple_signal_chain13 provisional | 13 | previously frozen |",
            "| remaining121 output/contract-shape20 frozen_v1 | 20 | this freeze |",
            "",
            "## 邊界",
            "",
            "- 本 census 為新的 immutable progress revision，不覆寫舊 census",
            "- 不得把本批 20 source-level units 描述為 20 個獨立 task",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, dict[str, bytes]]:
    rows = build_freeze_rows(repo)
    primary = Counter(row["primary_layer"] for row in rows)
    healer = Counter(row["healer_eligibility"] for row in rows)
    confidence = Counter(row["confidence"] for row in rows)
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    freeze_summary = {
        "revision": FREEZE_OUTPUT.name,
        "status": STATUS,
        "adjudication_identity": ADJUDICATION_IDENTITY,
        "cells": TARGET_CELLS,
        "unique_program_id": TARGET_CELLS,
        "unique_source_sha256": TARGET_CELLS,
        "unique_task_id": 13,
        "condition": "Candidate_B/H0",
        "processed77_intersection": 0,
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_nonempty_cells": 0,
        "healer_eligibility_distribution": dict(sorted(healer.items())),
        "outcome_validity_distribution": {"VALID_MODEL_OUTCOME": 20},
        "confidence_distribution": dict(sorted(confidence.items())),
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "provisional_v2_csv_sha256": V2_CSV_SHA256,
        "final_freeze_audit_manifest_sha256": FINAL_AUDIT_MANIFEST_SHA256,
        "final_freeze_audit_verdict": FINAL_AUDIT_VERDICT,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "note": "20 source-level evidence units across 13 tasks; not 20 independent tasks.",
    }
    freeze_provenance = {
        **freeze_summary,
        "start_head": START_HEAD,
        "v1_modified": False,
        "v2_modified": False,
        "audits_modified": False,
        **execution_counts,
        "source_hashes_verified": len(SOURCE_HASHES),
    }
    batch_registry = [
        {
            "batch_id": "g2_module_27",
            "cells": "27",
            "unique_program_id": "27",
            "unique_source_sha256": "",
            "unique_task_id": "",
            "source_revision": "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1",
            "source_manifest_sha256": "",
            "freeze_revision": "previously_frozen",
            "notes": "previously frozen",
        },
        {
            "batch_id": "module_exception_37",
            "cells": "37",
            "unique_program_id": "37",
            "unique_source_sha256": "",
            "unique_task_id": "",
            "source_revision": "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1",
            "source_manifest_sha256": "",
            "freeze_revision": "previously_frozen",
            "notes": "previously frozen",
        },
        {
            "batch_id": "multiple_signal_13",
            "cells": "13",
            "unique_program_id": "13",
            "unique_source_sha256": "",
            "unique_task_id": "",
            "source_revision": "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1",
            "source_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
            "freeze_revision": "previously_frozen",
            "notes": "previously frozen",
        },
        {
            "batch_id": "output_contract_shape_20",
            "cells": "20",
            "unique_program_id": "20",
            "unique_source_sha256": "20",
            "unique_task_id": "13",
            "source_revision": V2_DIR.name,
            "source_manifest_sha256": V2_MANIFEST_SHA256,
            "freeze_revision": FREEZE_OUTPUT.name,
            "notes": "this freeze; source-level units, not 20 independent tasks",
        },
    ]
    progress_summary = {
        "revision": PROGRESS_OUTPUT.name,
        "status": PROGRESS_STATUS,
        "formal_population": FORMAL_POPULATION,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "reconciliation": f"{FORMAL_POPULATION}={TOTAL_FROZEN}+{REMAINING}",
        "research_statement_zh": (
            "已分析並凍結97格，剩餘101格；本批20格全部為Healer abstain，沒有eligible或conditional候選。"
        ),
        "output_contract_shape20_freeze_revision": FREEZE_OUTPUT.name,
        "output_contract_shape20_freeze_from_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "final_freeze_audit_verdict": FINAL_AUDIT_VERDICT,
        **execution_counts,
    }
    progress_provenance = {
        **progress_summary,
        "start_head": START_HEAD,
        "immutable_new_revision": True,
        "overwrites_prior_census": False,
        "source_hashes_verified": len(SOURCE_HASHES),
    }
    return {
        "freeze": {
            Path("frozen_adjudication.csv"): _csv_bytes(FROZEN_FIELDS, rows),
            Path("frozen_batch_summary.json"): _json_bytes(freeze_summary),
            Path("frozen_batch_report_zh.md"): _freeze_report(rows).encode("utf-8"),
            Path("execution_counts.json"): _json_bytes(execution_counts),
            Path("provenance.json"): _json_bytes(freeze_provenance),
        },
        "progress": {
            Path("batch_registry.csv"): _csv_bytes(BATCH_REGISTRY_FIELDS, batch_registry),
            Path("frozen_progress_summary.json"): _json_bytes(progress_summary),
            Path("frozen_progress_report_zh.md"): _progress_report().encode("utf-8"),
            Path("execution_counts.json"): _json_bytes(execution_counts),
            Path("provenance.json"): _json_bytes(progress_provenance),
        },
    }


def write_outputs(repo: Path = REPO_ROOT) -> tuple[Path, Path]:
    freeze_dest = repo / FREEZE_OUTPUT
    progress_dest = repo / PROGRESS_OUTPUT
    _require(not freeze_dest.exists(), f"freeze output exists: {freeze_dest}")
    _require(not progress_dest.exists(), f"progress output exists: {progress_dest}")
    # Snapshot immutability of upstream revisions.
    guarded = {
        V1_MANIFEST: V1_MANIFEST_SHA256,
        V1_CSV: V1_CSV_SHA256,
        V2_MANIFEST: V2_MANIFEST_SHA256,
        V2_CSV: V2_CSV_SHA256,
        FINAL_AUDIT_MANIFEST: FINAL_AUDIT_MANIFEST_SHA256,
        POST_AUDIT_MANIFEST: POST_AUDIT_MANIFEST_SHA256,
    }
    before = {path: (repo / path).read_bytes() for path in guarded}
    bundles = build_outputs(repo)
    freeze_dest.mkdir(parents=True)
    progress_dest.mkdir(parents=True)
    freeze_hashes = {p.as_posix(): _sha(d) for p, d in bundles["freeze"].items()}
    progress_hashes = {p.as_posix(): _sha(d) for p, d in bundles["progress"].items()}
    for path, data in bundles["freeze"].items():
        (freeze_dest / path).write_bytes(data)
    for path, data in bundles["progress"].items():
        (progress_dest / path).write_bytes(data)
    freeze_manifest = {
        "revision": FREEZE_OUTPUT.name,
        "status": STATUS,
        "adjudication_identity": ADJUDICATION_IDENTITY,
        "cells": TARGET_CELLS,
        "newly_frozen": NEWLY_FROZEN,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "provisional_v2_manifest_sha256": V2_MANIFEST_SHA256,
        "provisional_v2_csv_sha256": V2_CSV_SHA256,
        "final_freeze_audit_manifest_sha256": FINAL_AUDIT_MANIFEST_SHA256,
        "final_freeze_audit_verdict": FINAL_AUDIT_VERDICT,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "v1_modified": False,
        "v2_modified": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": freeze_hashes,
    }
    progress_manifest = {
        "revision": PROGRESS_OUTPUT.name,
        "status": PROGRESS_STATUS,
        "formal_population": FORMAL_POPULATION,
        "previously_frozen": PREVIOUSLY_FROZEN,
        "newly_frozen": NEWLY_FROZEN,
        "total_frozen": TOTAL_FROZEN,
        "remaining": REMAINING,
        "freeze_revision": FREEZE_OUTPUT.name,
        "overwrites_prior_census": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "outputs_sha256_excluding_manifest": progress_hashes,
    }
    (freeze_dest / "manifest.json").write_bytes(_json_bytes(freeze_manifest))
    (progress_dest / "manifest.json").write_bytes(_json_bytes(progress_manifest))
    for path, expected in before.items():
        _require((repo / path).read_bytes() == expected, f"upstream mutated: {path}")
        _require(_sha(expected) == guarded[path], f"sha drift after write: {path}")
    return freeze_dest, progress_dest


def main() -> None:
    freeze_path, progress_path = write_outputs()
    print(freeze_path)
    print(progress_path)


if __name__ == "__main__":
    main()
