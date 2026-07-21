#!/usr/bin/env python3
"""Provisional adjudication v2 for remaining121 output/contract-shape 20 cells.

AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW

Applies only the four cell-field changes approved by post-adjudication audit
(Mbpp/237 healer_eligibility conditional→abstain and aligned abstain_reason).
Does not overwrite provisional v1 or any other frozen revision.
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
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
    import prepare_candidate_b_r003_taxonomy_v3_remaining121_census_planning_v1 as planning_prep


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
REVISION_SLUG = OUTPUT_RELATIVE.name
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_provisional_v2.py"
)

NEXT_BATCH_ROSTER = planning_prep.OUTPUT_RELATIVE / "next_batch_roster.csv"
NEXT_BATCH_ROSTER_SHA256 = "b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804"

MACHINE_CENSUS_MANIFEST = census_prep.OUTPUT_RELATIVE / "manifest.json"
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
V1_CITATION = V1_DIR / "evidence_citation_audit.csv"
V1_CLOSURE = V1_DIR / "roster_closure_audit.csv"
V1_MANIFEST_SHA256 = "548486f59c5a42ef03375ace981bbd7219c5f94ae0b374ac3be1c305805fbf8d"
V1_CSV_SHA256 = "87bf9dd0715cac8581028c98ffff0c1d0c6a91154bbfffe9470f244fe741f4f7"
V1_CITATION_SHA256 = "41c0bf5dbb7f909e9be0e59f254dd80df7aa38ccda022d61503773f97f2a6824"
V1_CLOSURE_SHA256 = "1d1c1836846cb0a574f73af0ab0fe8d47d6c8d2051b4c782c06939719f1e9cb2"

POST_AUDIT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_post_adjudication_audit_v1"
)
POST_AUDIT_MANIFEST = POST_AUDIT_DIR / "manifest.json"
POST_AUDIT_PROPOSED = POST_AUDIT_DIR / "proposed_changes.csv"
POST_AUDIT_MANIFEST_SHA256 = (
    "73fc418fe9c15bc35ade4ebe208d436eea516ac89860a962e78bea173bc1b508"
)
POST_AUDIT_PROPOSED_SHA256 = (
    "456b25228aa0e09fa962c84cc24b2cb3f6144f89e808eab44a95cf6d5fc78740"
)

TARGET_CELLS = 20
TARGET_UNIQUE_TASKS = 13
TARGET_UNIQUE_SOURCES = 20

MBPP237_ABSTAIN_REASON = (
    "Primary is L5 semantic/algorithm error (order-sensitive Counter vs public "
    "order-insensitive keys). Multiple safe canonicalizations exist "
    "(e.g. tuple(sorted(t)) vs frozenset); public contract does not uniquely "
    "constrain a generic Healer repair. Further work may only be a task-specific "
    "repairability probe and must not count as proven-repairable or a generic "
    "Healer candidate."
)

# Exactly four approved cell-field changes (post-audit proposed_changes H237-*).
APPROVED_CELL_CHANGES: tuple[dict[str, str], ...] = (
    {
        "change_id": "H237-44",
        "program_id": "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
        "field": "healer_eligibility",
        "old_value": "conditional",
        "new_value": "abstain",
        "audit_evidence": (
            POST_AUDIT_DIR.as_posix()
            + "/mbpp237_healer_eligibility_audit.csv#program_id=70f586aba6f3965f…"
        ),
        "change_reason": (
            "Post-audit: multiple safe key-canonicalizations; not unique bounded "
            "Healer repair; task-specific probe only."
        ),
    },
    {
        "change_id": "H237R-44",
        "program_id": "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
        "field": "abstain_reason",
        "old_value": (
            "Public example uniquely implies order-insensitive counting with sorted-key "
            "form, but tuple arity>2 and key canonicalization are not fully constrained "
            "→ conditional."
        ),
        "new_value": MBPP237_ABSTAIN_REASON,
        "audit_evidence": (
            POST_AUDIT_DIR.as_posix() + "/proposed_changes.csv#change_id=H237R-44"
        ),
        "change_reason": "Align abstain_reason with healer_eligibility=abstain after H237-44.",
    },
    {
        "change_id": "H237-22",
        "program_id": "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
        "field": "healer_eligibility",
        "old_value": "conditional",
        "new_value": "abstain",
        "audit_evidence": (
            POST_AUDIT_DIR.as_posix()
            + "/mbpp237_healer_eligibility_audit.csv#program_id=af469fe5ae58e9b1…"
        ),
        "change_reason": (
            "Post-audit: multiple safe key-canonicalizations; not unique bounded "
            "Healer repair; task-specific probe only."
        ),
    },
    {
        "change_id": "H237R-22",
        "program_id": "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
        "field": "abstain_reason",
        "old_value": (
            "Same order-insensitive counting requirement as sibling source; healer "
            "conditional because canonical key form is not uniquely fixed beyond "
            "public 2-tuples."
        ),
        "new_value": MBPP237_ABSTAIN_REASON,
        "audit_evidence": (
            POST_AUDIT_DIR.as_posix() + "/proposed_changes.csv#change_id=H237R-22"
        ),
        "change_reason": "Align abstain_reason with healer_eligibility=abstain after H237-22.",
    },
)

IMMUTABLE_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "seed",
    "cell_identity_sha256",
    "allowed_evidence",
    "observed_machine_signal",
    "primary_layer",
    "secondary_layers",
    "mechanism_tags",
    "failure_chain",
    "outcome_validity",
    "confidence",
    "evidence_citations",
    "adjudication_identity",
    "evidence_summary",
    "adjudication_status",
)

ADJUDICATION_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "seed",
    "cell_identity_sha256",
    "allowed_evidence",
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
    "evidence_summary",
    "adjudication_status",
)

DELTA_FIELDS = (
    "change_id",
    "program_id",
    "field",
    "old_value",
    "new_value",
    "audit_evidence",
    "change_reason",
)

CITATION_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "citation_kind",
    "citation_path",
    "citation_locator",
)

ROSTER_CLOSURE_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
    "in_fixed_roster",
    "in_processed77",
    "source_sha_verified",
    "primary_layer",
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    V1_MANIFEST: V1_MANIFEST_SHA256,
    V1_CSV: V1_CSV_SHA256,
    V1_CITATION: V1_CITATION_SHA256,
    V1_CLOSURE: V1_CLOSURE_SHA256,
    POST_AUDIT_MANIFEST: POST_AUDIT_MANIFEST_SHA256,
    POST_AUDIT_PROPOSED: POST_AUDIT_PROPOSED_SHA256,
}

G2_PROVISIONAL_CSV = planning_prep.G2_PROVISIONAL_CSV
MODULE_EXCEPTION_CSV = planning_prep.MODULE_EXCEPTION_CSV
MULTIPLE_SIGNAL_CSV = planning_prep.MULTIPLE_SIGNAL_CSV


class RevisionError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RevisionError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    for roster_path in (G2_PROVISIONAL_CSV, MODULE_EXCEPTION_CSV, MULTIPLE_SIGNAL_CSV):
        ids.update(row["program_id"] for row in _read_csv(repo / roster_path))
    return ids


def _verify_v1_immutable(repo: Path, snapshot: dict[str, bytes]) -> None:
    for relative, expected in snapshot.items():
        path = repo / relative
        _require(path.is_file(), f"v1 missing during v2 build: {path}")
        _require(path.read_bytes() == expected, f"v1 mutated during v2 build: {relative}")


def build_rows(repo: Path = REPO_ROOT) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    verify_sources(repo)
    v1_snapshot = {
        V1_MANIFEST.as_posix(): (repo / V1_MANIFEST).read_bytes(),
        V1_CSV.as_posix(): (repo / V1_CSV).read_bytes(),
        V1_CITATION.as_posix(): (repo / V1_CITATION).read_bytes(),
        V1_CLOSURE.as_posix(): (repo / V1_CLOSURE).read_bytes(),
    }
    v1_rows = _read_csv(repo / V1_CSV)
    roster = _read_csv(repo / NEXT_BATCH_ROSTER)
    _require(len(v1_rows) == TARGET_CELLS, f"v1 row count drift: {len(v1_rows)}")
    _require(len(roster) == TARGET_CELLS, f"roster count drift: {len(roster)}")
    roster_ids = {row["program_id"] for row in roster}
    v1_ids = {row["program_id"] for row in v1_rows}
    _require(roster_ids == v1_ids, "v1 program_id set != fixed roster")
    _require(len(v1_ids) == TARGET_CELLS, "program uniqueness drift")
    _require(
        len({row["source_sha256"] for row in v1_rows}) == TARGET_UNIQUE_SOURCES,
        "source uniqueness drift",
    )
    _require(
        len({row["task_id"] for row in v1_rows}) == TARGET_UNIQUE_TASKS,
        "task uniqueness drift",
    )
    processed = _processed77(repo)
    _require(len(processed) == 77, "processed77 size drift")
    _require(not (v1_ids & processed), "processed77 intersection must be empty")

    by_program = {row["program_id"]: dict(row) for row in v1_rows}
    delta_rows: list[dict[str, str]] = []
    for change in APPROVED_CELL_CHANGES:
        program_id = change["program_id"]
        field = change["field"]
        row = by_program[program_id]
        _require(field in ("healer_eligibility", "abstain_reason"), f"disallowed field: {field}")
        _require(
            row[field] == change["old_value"],
            f"old_value mismatch for {program_id}.{field}: {row[field]!r}",
        )
        row[field] = change["new_value"]
        delta_rows.append(
            {
                "change_id": change["change_id"],
                "program_id": program_id,
                "field": field,
                "old_value": change["old_value"],
                "new_value": change["new_value"],
                "audit_evidence": change["audit_evidence"],
                "change_reason": change["change_reason"],
            }
        )

    _require(len(delta_rows) == 4, f"expected exactly 4 cell-field changes, got {len(delta_rows)}")

    # Preserve v1 row order; verify only approved fields changed.
    v2_rows: list[dict[str, str]] = []
    for original in v1_rows:
        updated = by_program[original["program_id"]]
        for field in IMMUTABLE_FIELDS:
            _require(
                updated[field] == original[field],
                f"immutable field mutated: {original['program_id']}.{field}",
            )
        if original["program_id"] not in {
            "70f586aba6f3965fb1463303753ecf4040872364230be73de4b4e51b340b8fb9",
            "af469fe5ae58e9b111c2a5b1d78741fe0dfb9ed0d54b43f939e23ae28c87bcea",
        }:
            _require(
                updated["healer_eligibility"] == original["healer_eligibility"],
                f"unexpected healer change: {original['program_id']}",
            )
            _require(
                updated["abstain_reason"] == original["abstain_reason"],
                f"unexpected abstain_reason change: {original['program_id']}",
            )
        v2_rows.append({field: updated[field] for field in ADJUDICATION_FIELDS})

    healer = Counter(row["healer_eligibility"] for row in v2_rows)
    _require(healer.get("abstain", 0) == 20, f"healer abstain drift: {dict(healer)}")
    _require(healer.get("conditional", 0) == 0, "conditional must be zero in v2")
    _require(healer.get("eligible", 0) == 0, "eligible must be zero in v2")
    primary = Counter(row["primary_layer"] for row in v2_rows)
    _require(primary.get("UNRESOLVED", 0) == 12, "UNRESOLVED drift")
    _require(primary.get("L5", 0) == 7, "L5 drift")
    _require(primary.get("L2", 0) == 1, "L2 drift")
    _require(
        all(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in v2_rows),
        "outcome_validity drift",
    )
    _require(
        all(row["primary_layer"] != "UNRESOLVED" or row["healer_eligibility"] == "abstain" for row in v2_rows),
        "UNRESOLVED must abstain",
    )
    _verify_v1_immutable(repo, v1_snapshot)
    return v2_rows, delta_rows


def _summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    primary = Counter(row["primary_layer"] for row in rows)
    secondary: Counter[str] = Counter()
    mechanisms: Counter[str] = Counter()
    for row in rows:
        for layer in json.loads(row["secondary_layers"]):
            secondary[layer] += 1
        for tag in json.loads(row["mechanism_tags"]):
            mechanisms[tag] += 1
    return {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "parent_revision": V1_DIR.name,
        "cells": TARGET_CELLS,
        "unique_program_id": len({row["program_id"] for row in rows}),
        "unique_source_sha256": len({row["source_sha256"] for row in rows}),
        "unique_task_id": len({row["task_id"] for row in rows}),
        "primary_layer_distribution": dict(sorted(primary.items())),
        "secondary_layer_distribution": dict(sorted(secondary.items())),
        "mechanism_tag_distribution": dict(sorted(mechanisms.items())),
        "outcome_validity_distribution": dict(
            sorted(Counter(row["outcome_validity"] for row in rows).items())
        ),
        "healer_eligibility_distribution": dict(
            sorted(Counter(row["healer_eligibility"] for row in rows).items())
        ),
        "confidence_distribution": dict(
            sorted(Counter(row["confidence"] for row in rows).items())
        ),
        "unresolved_cells": primary.get("UNRESOLVED", 0),
        "cell_field_changes_from_v1": 4,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "note": (
            "20 cells are 20 source-level evidence units across 13 tasks; "
            "do not describe as 20 independent tasks."
        ),
    }


def _summary_zh(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# AI-assisted provisional adjudication summary v2（output/contract-shape 20-cell）",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            "本 revision **不是** ground truth、formal human review 或 Healer 驗證；**尚未凍結**。",
            "",
            "## 相對 v1 的修訂範圍",
            "",
            "- 僅套用 post-adjudication audit 核准的 **4 個 cell-field changes**（Mbpp/237×2）。",
            "- `healer_eligibility`: conditional → abstain（2 格）",
            "- `abstain_reason`: 對齊 abstain 理由（2 格）",
            "- primary / secondary / mechanism / failure_chain / outcome / confidence / citations / identity **未改**",
            "- provisional v1 保持逐 byte 不變",
            "",
            "## 母體",
            "",
            f"- cells={summary['cells']}",
            f"- unique program_id={summary['unique_program_id']}",
            f"- unique source_sha256={summary['unique_source_sha256']}",
            f"- unique task_id={summary['unique_task_id']}",
            f"- {summary['note']}",
            "",
            "## Primary layer",
            "",
            "| Layer | Cells |",
            "|---|---:|",
        ]
        + [f"| `{k}` | {v} |" for k, v in summary["primary_layer_distribution"].items()]
        + [
            "",
            f"- UNRESOLVED={summary['unresolved_cells']}（全部 abstain）",
            "",
            "## Healer eligibility",
            "",
            f"- {summary['healer_eligibility_distribution']}",
            "",
            "## Outcome / Confidence",
            "",
            f"- outcome_validity：{summary['outcome_validity_distribution']}",
            f"- confidence：{summary['confidence_distribution']}",
            "",
            "## Sufficient 定義澄清（見 pre_audit_sufficiency_clarification_zh.md）",
            "",
            "- pre-audit `sufficient` = 足以進行合法裁決（含 UNRESOLVED）",
            "- `sufficient` ≠ 足以閉合至 L2/L3/L4/L5",
            "- 12 格 UNRESOLVED：11 來自 sufficient、1 來自 conditional；不得再描述為「新增 7 格」",
            "",
        ]
    )


def _clarification_zh() -> str:
    return "\n".join(
        [
            "# Pre-audit sufficiency clarification / corrigendum（v2）",
            "",
            "**本文件為 v2 文件層澄清，不覆寫、不竄改原 pre-adjudication audit revision。**",
            "",
            "## 定義",
            "",
            "- pre-audit `evidence_sufficiency=sufficient`：**公開證據足以進行合法的 provisional adjudication**。",
            "- 合法裁決**包含** `primary_layer=UNRESOLVED`（當公開證據不足以閉合 L2/L3/L4/L5 時）。",
            "- `sufficient` **不等於**「足以確定 failure taxonomy layer」。",
            "- `conditional`：可進入裁決，但預期需依賴 abstain/UNRESOLVED 路徑。",
            "",
            "## 與 v1 provisional 的關係",
            "",
            "- provisional v1：UNRESOLVED=12、LOW=12",
            "- 其中 **11** 格 pre-audit=`sufficient` → provisional=`UNRESOLVED`",
            "- 其中 **1** 格 pre-audit=`conditional`（Mbpp/103 seed55）→ provisional=`UNRESOLVED`",
            "- 其餘 closed layers：L5=7、L2=1（來自 pre-audit sufficient 或 conditional 且公開證據可閉合者）",
            "",
            "## 禁止的錯誤敘述",
            "",
            "- 不得再描述為「相對於 pre-audit **新增 7 格 UNRESOLVED**」。",
            "- 不得將 `sufficient` 解讀為「必須判出 L2–L5」。",
            "- 不得為降低 UNRESOLVED 數量而推測 root cause。",
            "",
            "## 原 artifact 狀態",
            "",
            "- `candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1` **保持不變**。",
            "- 本澄清只存在於 provisional **v2** revision。",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    v1_bytes_before = {
        path.as_posix(): (repo / path).read_bytes()
        for path in (V1_MANIFEST, V1_CSV, V1_CITATION, V1_CLOSURE)
    }
    rows, delta_rows = build_rows(repo)
    summary = _summary(rows)
    citations = _read_csv(repo / V1_CITATION)
    closure = _read_csv(repo / V1_CLOSURE)
    # Closure primary_layer unchanged; copy bytes-equivalent content.
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
    }
    provenance = {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "start_head": START_HEAD,
        "parent_revision": V1_DIR.name,
        "parent_manifest_sha256": V1_MANIFEST_SHA256,
        "parent_adjudication_csv_sha256": V1_CSV_SHA256,
        "post_audit_manifest_sha256": POST_AUDIT_MANIFEST_SHA256,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "multiple_signal_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
        "target_cells": TARGET_CELLS,
        "unique_task_id": TARGET_UNIQUE_TASKS,
        "unique_source_sha256": TARGET_UNIQUE_SOURCES,
        "cell_field_changes_from_v1": 4,
        "approved_change_ids": [row["change_id"] for row in delta_rows],
        "formal_human_review": False,
        "ground_truth": False,
        "healer_executed": False,
        "frozen": False,
        "v1_overwritten": False,
        "hidden_expected_actual_used": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "source_hashes_verified": len(SOURCE_HASHES),
        "primary_layer_distribution": summary["primary_layer_distribution"],
        "healer_eligibility_distribution": summary["healer_eligibility_distribution"],
        "unresolved_cells": summary["unresolved_cells"],
    }
    outputs = {
        Path("ai_provisional_adjudication.csv"): _csv_bytes(ADJUDICATION_FIELDS, rows),
        Path("adjudication_summary.json"): _json_bytes(summary),
        Path("adjudication_summary_zh.md"): _summary_zh(summary).encode("utf-8"),
        Path("evidence_citation_audit.csv"): _csv_bytes(CITATION_FIELDS, citations),
        Path("roster_closure_audit.csv"): _csv_bytes(ROSTER_CLOSURE_FIELDS, closure),
        Path("revision_delta_v1_to_v2.csv"): _csv_bytes(DELTA_FIELDS, delta_rows),
        Path("pre_audit_sufficiency_clarification_zh.md"): _clarification_zh().encode("utf-8"),
        Path("execution_counts.json"): _json_bytes(execution_counts),
        Path("provenance.json"): _json_bytes(provenance),
    }
    # Final immutability check for v1.
    for relative, expected in v1_bytes_before.items():
        _require(
            (repo / relative).read_bytes() == expected,
            f"v1 mutated after v2 build: {relative}",
        )
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    summary = json.loads(outputs[Path("adjudication_summary.json")].decode("utf-8"))
    manifest = {
        "revision": REVISION_SLUG,
        "status": STATUS,
        "parent_revision": V1_DIR.name,
        "parent_manifest_sha256": V1_MANIFEST_SHA256,
        "target_cells": TARGET_CELLS,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "cell_field_changes_from_v1": 4,
        "frozen": False,
        "formal_human_review": False,
        "v1_overwritten": False,
        "unresolved_cells": summary["unresolved_cells"],
        "primary_layer_distribution": summary["primary_layer_distribution"],
        "healer_eligibility_distribution": summary["healer_eligibility_distribution"],
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
    }
    (destination / "manifest.json").write_bytes(_json_bytes(manifest))
    # One more v1 immutability check after write.
    _require(
        _sha((repo / V1_MANIFEST).read_bytes()) == V1_MANIFEST_SHA256,
        "v1 manifest mutated",
    )
    _require(_sha((repo / V1_CSV).read_bytes()) == V1_CSV_SHA256, "v1 csv mutated")
    return destination


def main() -> None:
    path = write_outputs()
    print(path)


if __name__ == "__main__":
    main()
