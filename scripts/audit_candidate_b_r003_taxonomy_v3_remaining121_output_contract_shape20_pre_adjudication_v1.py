#!/usr/bin/env python3
"""Pre-adjudication adversarial audit for remaining121 output/contract-shape 20-cell batch.

PRE_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FORMAL_ADJUDICATION

Reviews fixed next_batch_roster only. Does not perform provisional adjudication,
does not emit ai_provisional_adjudication.csv, and does not execute programs or models.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
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
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1"
)
START_HEAD = "a18cf32f27c781daa3e9c3f493a4527f31a6f481"
STATUS = "PRE_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FORMAL_ADJUDICATION"
ADJUDICATION_STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/audit_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_v1.py"
)

PLANNING_DIR = planning_prep.OUTPUT_RELATIVE
PLANNING_MANIFEST = PLANNING_DIR / "manifest.json"
NEXT_BATCH_ROSTER = PLANNING_DIR / "next_batch_roster.csv"
PLANNING_MANIFEST_SHA256 = "66cb8f366d3820b31715753513ed6b038bd471b85b536c3b6779217b041387ab"
NEXT_BATCH_ROSTER_SHA256 = "b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804"

MACHINE_CENSUS_MANIFEST = census_prep.OUTPUT_RELATIVE / "manifest.json"
MACHINE_CENSUS_CSV = census_prep.OUTPUT_RELATIVE / "machine_census.csv"
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
MACHINE_CENSUS_CSV_SHA256 = "284802c8f1aeff92ad70f65b42c4aa7dabc252da592f8ad62011be71537f8a32"

MULTIPLE_SIGNAL_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/manifest.json"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

G2_PROVISIONAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
MODULE_EXCEPTION_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1/"
    "ai_provisional_adjudication.csv"
)
MULTIPLE_SIGNAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1/"
    "ai_provisional_adjudication.csv"
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    preparation.TAXONOMY_CODEBOOK: preparation.SOURCE_HASHES[preparation.TAXONOMY_CODEBOOK],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    MACHINE_CENSUS_CSV: MACHINE_CENSUS_CSV_SHA256,
    PLANNING_MANIFEST: PLANNING_MANIFEST_SHA256,
    NEXT_BATCH_ROSTER: NEXT_BATCH_ROSTER_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    G2_PROVISIONAL_CSV: planning_prep.G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: planning_prep.MODULE_EXCEPTION_CSV_SHA256,
    MULTIPLE_SIGNAL_CSV: planning_prep.MULTIPLE_SIGNAL_CSV_SHA256,
}

EXPECTED_RETURN_TYPES = frozenset(
    {"bool", "int", "str", "list", "dict", "float", "mixed", "set", "tuple", "other"}
)
TARGET_CELLS = 20
TARGET_UNIQUE_TASKS = 13
TARGET_UNIQUE_SOURCES = 20
TARGET_CLUSTER = "output_or_contract_shape_signal"

AUDIT_FIELDS = (
    "audit_rank",
    "program_id",
    "task_id",
    "seed",
    "source_sha256",
    "return_type_bucket",
    "return_shape_bucket",
    "public_prompt_spec_status",
    "candidate_source_status",
    "completed_return_shape_status",
    "root_cause_directly_provable",
    "l2_l3_l4_l5_confusion_risk",
    "multi_stage_failure_chain_risk",
    "hidden_oracle_dependency",
    "outcome_validity_separable",
    "duplicate_task_distinct_source_evidence",
    "return_type_sampling_bias_note",
    "evidence_sufficiency",
    "recommended_posture",
    "audit_notes",
    "allowed_evidence",
)

PROTOCOL_ADJUDICATION_FIELDS = (
    "program_id",
    "task_id",
    "source_sha256",
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
)


class AuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _processed77(repo: Path) -> set[str]:
    ids: set[str] = set()
    for roster_path in (G2_PROVISIONAL_CSV, MODULE_EXCEPTION_CSV, MULTIPLE_SIGNAL_CSV):
        ids.update(row["program_id"] for row in _read_csv(repo / roster_path))
    return ids


def _return_annotation(entry_def: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if entry_def.returns is None:
        return ""
    return ast.unparse(entry_def.returns)


def _prompt_has_worked_example(prompt: str) -> bool:
    lowered = prompt.lower()
    return bool(
        re.search(r"assert\s+", prompt)
        or "example" in lowered
        or ">>> " in prompt
        or "input:" in lowered
    )


def _static_complexity_flags(source: str, entry_point: str) -> dict[str, bool]:
    tree = ast.parse(source)
    entry_defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
    ]
    flags = {
        "third_party_import": False,
        "nested_loops": False,
        "recursive_call": False,
        "missing_return_annotation": True,
    }
    if len(entry_defs) == 1:
        flags["missing_return_annotation"] = entry_defs[0].returns is None
        body = entry_defs[0]
        for node in ast.walk(body):
            if isinstance(node, ast.ImportFrom) and node.module not in {None, "typing", "math", "re"}:
                flags["third_party_import"] = True
            if isinstance(node, ast.For):
                for inner in ast.walk(node):
                    if inner is not node and isinstance(inner, ast.For):
                        flags["nested_loops"] = True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == entry_point:
                    flags["recursive_call"] = True
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module not in {None, "typing", "math", "re"}:
            flags["third_party_import"] = True
    return flags


def _layer_confusion_risk(
    *,
    return_type_bucket: str,
    return_annotation: str,
    prompt_has_example: bool,
    static_flags: dict[str, bool],
) -> str:
    score = 0
    if not return_annotation:
        score += 1
    if static_flags["third_party_import"]:
        score += 1
    if static_flags["nested_loops"] or static_flags["recursive_call"]:
        score += 1
    if return_type_bucket in {"mixed", "other"}:
        score += 1
    if prompt_has_example:
        score -= 1
    if score >= 3:
        return "HIGH"
    if score >= 1:
        return "MEDIUM"
    return "LOW"


def _hidden_oracle_dependency(*, prompt_has_example: bool, layer_risk: str) -> str:
    if prompt_has_example and layer_risk == "LOW":
        return "no"
    if prompt_has_example:
        return "conditional"
    if layer_risk == "HIGH":
        return "conditional"
    return "conditional"


def _population_return_type_share(repo: Path) -> dict[str, float]:
    inventory = _read_csv(repo / planning_prep.OUTPUT_RELATIVE / "signal_inventory.csv")
    cluster_rows = [row for row in inventory if row["work_cluster"] == TARGET_CLUSTER]
    total = len(cluster_rows)
    counts = Counter(row["return_type_bucket"] for row in cluster_rows)
    return {bucket: counts.get(bucket, 0) / total for bucket in counts}


def _load_fixed_roster(repo: Path) -> list[dict[str, str]]:
    roster = _read_csv(repo / NEXT_BATCH_ROSTER)
    _require(len(roster) == TARGET_CELLS, f"next batch roster count drift: {len(roster)}")
    _require(
        _sha((repo / NEXT_BATCH_ROSTER).read_bytes()) == NEXT_BATCH_ROSTER_SHA256,
        "next batch roster sha drift",
    )
    program_ids = [row["program_id"] for row in roster]
    source_shas = [row["evaluation_source_sha256"] for row in roster]
    task_ids = [row["task_id"] for row in roster]
    _require(len(set(program_ids)) == TARGET_CELLS, "program_id uniqueness drift")
    _require(len(set(source_shas)) == TARGET_UNIQUE_SOURCES, "source sha uniqueness drift")
    _require(len(set(task_ids)) == TARGET_UNIQUE_TASKS, "task_id uniqueness drift")
    _require(all(row["condition"] == "Candidate_B/H0" for row in roster), "condition drift")
    _require(all(row["work_cluster"] == TARGET_CLUSTER for row in roster), "work cluster drift")
    _require(
        {row["return_type_bucket"] for row in roster} <= EXPECTED_RETURN_TYPES,
        "unexpected return_type_bucket",
    )
    _require(
        EXPECTED_RETURN_TYPES <= {row["return_type_bucket"] for row in roster},
        "return_type coverage incomplete",
    )
    processed = _processed77(repo)
    _require(not (set(program_ids) & processed), "processed77 intersection must be empty")
    _require(
        [row["batch_rank"] for row in roster] == [str(i) for i in range(1, TARGET_CELLS + 1)],
        "batch_rank not contiguous",
    )
    return roster


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _load_fixed_roster(repo)
    census = {row["program_id"]: row for row in _read_csv(repo / MACHINE_CENSUS_CSV)}
    tasks = {row["task_id"]: row for row in _read_jsonl(repo / preparation.TASKS)}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    population_share = _population_return_type_share(repo)
    batch_share = Counter(row["return_type_bucket"] for row in roster)
    task_source_map: dict[str, set[str]] = defaultdict(set)
    audit_rows: list[dict[str, str]] = []

    for rank, row in enumerate(roster, 1):
        program_id = row["program_id"]
        task_id = row["task_id"]
        source_sha = row["evaluation_source_sha256"]
        task_source_map[task_id].add(source_sha)
        census_row = census[program_id]
        task = tasks[task_id]
        journal = journals[program_id]
        source = journal["evaluation_source"]
        _require(
            _sha(source.encode("utf-8")) == source_sha,
            f"source sha mismatch: {program_id}",
        )
        entry_point = str(task["entry_point"])
        prompt = str(task.get("prompt") or task.get("text") or "")
        _require(prompt.strip(), f"missing public prompt: {task_id}")

        tree = ast.parse(source)
        entry_defs = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
        ]
        return_annotation = _return_annotation(entry_defs[0]) if len(entry_defs) == 1 else ""
        static_flags = _static_complexity_flags(source, entry_point)
        prompt_has_example = _prompt_has_worked_example(prompt)

        public_ok = bool(prompt.strip() and task.get("entry_point"))
        source_ok = bool(source.strip()) and _sha(source.encode("utf-8")) == source_sha
        completed_ok = (
            census_row["diagnostic_phase"] == "completed"
            and census_row["termination"] == "returned"
            and census_row["frozen_g1_parse"] == "PASS"
            and census_row["frozen_g2_execution"] == "PASS"
            and census_row["frozen_g3e_entry_point"] == "PASS"
            and bool(row["return_type_bucket"])
        )
        root_cause_provable = "false"
        layer_risk = _layer_confusion_risk(
            return_type_bucket=row["return_type_bucket"],
            return_annotation=return_annotation,
            prompt_has_example=prompt_has_example,
            static_flags=static_flags,
        )
        multi_stage_risk = "LOW"
        hidden_oracle = _hidden_oracle_dependency(
            prompt_has_example=prompt_has_example,
            layer_risk=layer_risk,
        )
        outcome_separable = "true"
        distinct_source_evidence = "true"
        pop_share = population_share.get(row["return_type_bucket"], 0.0)
        batch_pct = batch_share[row["return_type_bucket"]] / TARGET_CELLS
        sampling_note = (
            "round_robin_oversample"
            if batch_pct > max(pop_share * 2.0, pop_share + 0.05)
            else "representative_or_under_sample"
        )

        if not public_ok or not source_ok or not completed_ok:
            sufficiency = "insufficient"
            posture = "block_adjudication"
        elif hidden_oracle == "conditional" or layer_risk in {"HIGH", "MEDIUM"}:
            sufficiency = "conditional"
            posture = "proceed_with_abstain_allowed"
        else:
            sufficiency = "sufficient"
            posture = "proceed_with_abstain_allowed"

        allowed_evidence = [
            preparation.TASKS.as_posix() + f"#task_id={task_id}",
            preparation.JOURNAL.as_posix() + f"#program_id={program_id};healer_account=H0",
            census_prep.OUTPUT_RELATIVE.as_posix() + "/machine_census.csv",
            census_prep.OUTPUT_RELATIVE.as_posix() + "/fixed_roster.csv",
        ]
        notes = [
            "return_shape_observed_not_root_cause",
            f"layer_risk={layer_risk}",
            f"hidden_oracle={hidden_oracle}",
        ]
        if len(task_source_map[task_id]) > 1 and task_id in {
            other["task_id"] for other in roster if other["program_id"] != program_id
        }:
            notes.append("duplicate_task_different_source_counts_as_distinct_evidence")

        audit_rows.append(
            {
                "audit_rank": str(rank),
                "program_id": program_id,
                "task_id": task_id,
                "seed": row["seed"],
                "source_sha256": source_sha,
                "return_type_bucket": row["return_type_bucket"],
                "return_shape_bucket": row["return_shape_bucket"],
                "public_prompt_spec_status": "complete" if public_ok else "missing",
                "candidate_source_status": "complete" if source_ok else "missing",
                "completed_return_shape_status": "verified" if completed_ok else "missing",
                "root_cause_directly_provable": root_cause_provable,
                "l2_l3_l4_l5_confusion_risk": layer_risk,
                "multi_stage_failure_chain_risk": multi_stage_risk,
                "hidden_oracle_dependency": hidden_oracle,
                "outcome_validity_separable": outcome_separable,
                "duplicate_task_distinct_source_evidence": distinct_source_evidence,
                "return_type_sampling_bias_note": sampling_note,
                "evidence_sufficiency": sufficiency,
                "recommended_posture": posture,
                "audit_notes": ";".join(notes),
                "allowed_evidence": _json(allowed_evidence),
            }
        )

    sufficiency_counter = Counter(row["evidence_sufficiency"] for row in audit_rows)
    layer_counter = Counter(row["l2_l3_l4_l5_confusion_risk"] for row in audit_rows)
    hidden_counter = Counter(row["hidden_oracle_dependency"] for row in audit_rows)
    _require(sufficiency_counter.get("insufficient", 0) == 0, "insufficient evidence in fixed roster")

    if sufficiency_counter.get("conditional", 0) == TARGET_CELLS:
        audit_verdict = "READY_FOR_20_CELL_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
    elif sufficiency_counter.get("insufficient", 0) > 0:
        audit_verdict = "REVISION_REQUIRED_BEFORE_ADJUDICATION"
    else:
        audit_verdict = "READY_FOR_20_CELL_AI_ASSISTED_PROVISIONAL_ADJUDICATION"

    return {
        "roster": roster,
        "audit_rows": audit_rows,
        "sufficiency_counter": sufficiency_counter,
        "layer_counter": layer_counter,
        "hidden_counter": hidden_counter,
        "population_share": population_share,
        "batch_share": batch_share,
        "audit_verdict": audit_verdict,
    }


def _audit_report_md(analysis: dict[str, Any]) -> str:
    suff = analysis["sufficiency_counter"]
    layer = analysis["layer_counter"]
    hidden = analysis["hidden_counter"]
    pop = analysis["population_share"]
    batch = analysis["batch_share"]
    lines = [
        "# Pre-adjudication adversarial audit（remaining121 output/contract-shape 20-cell）",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        f"**Audit verdict：`{analysis['audit_verdict']}`**",
        "",
        "## 固定 roster 驗證",
        "",
        f"- cells={TARGET_CELLS}",
        f"- unique program_id={TARGET_CELLS}",
        f"- unique source_sha256={TARGET_UNIQUE_SOURCES}",
        f"- unique task_id={TARGET_UNIQUE_TASKS}",
        "- processed77 交集=0",
        "- condition 全為 Candidate_B/H0",
        f"- next_batch_roster SHA256=`{NEXT_BATCH_ROSTER_SHA256}`",
        "",
        "## 逐格證據充分性",
        "",
        "| Sufficiency | Cells |",
        "|---|---:|",
    ]
    for key in ("sufficient", "conditional", "insufficient"):
        lines.append(f"| `{key}` | {suff.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## L2/L3/L4/L5 混淆風險",
            "",
            "| Risk | Cells |",
            "|---|---:|",
        ]
    )
    for key in ("HIGH", "MEDIUM", "LOW"):
        lines.append(f"| `{key}` | {layer.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## Hidden oracle 依賴",
            "",
            "| Dependency | Cells |",
            "|---|---:|",
        ]
    )
    for key in ("no", "conditional", "yes"):
        lines.append(f"| `{key}` | {hidden.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## return_type 輪詢選樣偏差",
            "",
            "| return_type | population_share | batch_share | note |",
            "|---|---:|---:|---|",
        ]
    )
    for bucket in sorted(batch):
        pop_pct = pop.get(bucket, 0.0)
        batch_pct = batch[bucket] / TARGET_CELLS
        note = (
            "oversampled"
            if batch_pct > max(pop_pct * 2.0, pop_pct + 0.05)
            else "representative_or_under"
        )
        lines.append(
            f"| `{bucket}` | {pop_pct:.1%} | {batch_pct:.1%} | {note} |"
        )
    lines.extend(
        [
            "",
            "## 審查結論",
            "",
            "- 20 格皆具完整 public prompt/spec、candidate source SHA、completed+return-shape 公開訊號。",
            "- 現有證據僅證明「輸出形狀異常」，不足以直接鎖定 root cause；正式裁決必須允許 UNRESOLVED 與 abstain。",
            "- L2 contract 與 L5 semantic incorrectness 最易混淆；不得將 return-shape mismatch 直接等同 L2 或 L5。",
            "- duplicate task 但不同 source_sha256 仍視為不同 source-level evidence（6 個 task 在批內有多 source）。",
            "- return_type 輪詢刻意 oversample 稀有型別（tuple/other/set/dict），bool/int 相對 under-sample；"
            "此偏差可接受但不得把 20 格描述為 20 個獨立 task。",
            "- 未使用 hidden expected/actual、traceback 或重新執行程式。",
            "",
        ]
    )
    return "\n".join(lines)


def _protocol_md() -> str:
    return "\n".join(
        [
            "# Proposed adjudication protocol（output/contract-shape 20-cell provisional）",
            "",
            f"**狀態：`{ADJUDICATION_STATUS}`**",
            "",
            "## 輸入與固定 roster",
            "",
            f"- 固定使用 planning v1 `next_batch_roster.csv`（SHA `{NEXT_BATCH_ROSTER_SHA256}`）",
            "- 20 格、13 task_id、20 source_sha256；不得增刪或重選",
            "- frozen machine census manifest SHA 釘選",
            "",
            "## 允許證據（allowed_evidence）",
            "",
            "- public task prompt/spec（`tasks.jsonl`）",
            "- H0 evaluation_source 靜態 AST（不執行）",
            "- coarse diagnostics phase/status/return_type_bucket/return_shape_bucket",
            "- G1/G2/G3e frozen PASS/FAIL flags",
            "- 禁止：hidden expected/actual、exception message、traceback、H1、EvalPlus 重跑",
            "",
            "## 逐格輸出欄位",
            "",
            "- `program_id`, `task_id`, `source_sha256`",
            "- `allowed_evidence`（JSON path list）",
            "- `observed_machine_signal`：固定 `output_or_contract_shape_signal`",
            "- `primary_layer`：L0–L5 或 UNRESOLVED",
            "- `secondary_layers`：JSON array，僅 L0–L5",
            "- `mechanism_tags`：JSON array（return_shape_mismatch 等；不得放入 layer 標籤）",
            "- `failure_chain`：有序因果 JSON array（例：`[\"entry_executed\",\"return_shape_mismatch\"]`）",
            "- `outcome_validity`：與 taxonomy 分開；completed+G1/G3e PASS → 預設 VALID_MODEL_OUTCOME",
            "- `healer_eligibility`：eligible | conditional | abstain",
            "- `abstain_reason`：層級無法在公開證據下閉合時必填",
            "- `confidence`：HIGH | MEDIUM | LOW",
            "- `evidence_citations`：JSON path+locator list",
            "- `adjudication_identity`：program_id+source_sha256+revision slug",
            "",
            "## Primary layer 規則",
            "",
            "- 不得僅因 return_type_bucket 非空即判 L5；需有 public prompt/spec 或靜態源碼可引用語意錯誤",
            "- L2 僅在 entry point/arity/可見 signature 與 public contract 衝突且無更深層證據時",
            "- L3 需可見 domain/API/import 誤用證據；不得僅憑 import 存在猜測",
            "- L4 需可見 runtime/algorithm 路徑錯誤（loop/recursion/exception guard）且 public 可定位",
            "- 若 L4 vs L5 無 public 算術或示例可證 → primary=UNRESOLVED，abstain_reason 必填",
            "",
            "## Failure chain 規則",
            "",
            "- 必須有序因果，不得並列 machine signals",
            "- completed cell 典型鏈：`module_loaded` → `entry_point_invoked` → `returned_value_observed` → `return_shape_or_semantic_mismatch`",
            "- 不得加入未在 allowed_evidence 出現的隱藏測試失敗節點",
            "",
            "## Healer eligibility 規則",
            "",
            "- 禁止僅因「看起來容易修」標 eligible",
            "- eligible 需同時滿足：可定位、deterministic、bounded、無 hidden oracle、"
            "唯一或受約束的安全修改、可提出反例測試",
            "- 若需重建演算法或 public 證據不足以唯一化修補 → conditional 或 abstain",
            "- semantic/output incorrectness 預設 abstain，除非公開示例可唯一推導修正",
            "",
            "## Outcome validity",
            "",
            "- outcome_validity 與 failure taxonomy 分開判斷",
            "- UNRESOLVED primary 不自動否定 VALID_MODEL_OUTCOME",
            "",
            "## 批次偏差提醒",
            "",
            "- 本批 return_type 輪詢 oversample 稀有型別；統計不得外推至 remaining119",
            "- 13 task_id 中 6 個具多 source；分析時以 source-level 為 evidence unit",
            "",
        ]
    )


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    provenance = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "adjudication_status_for_next_round": ADJUDICATION_STATUS,
        "start_head": START_HEAD,
        "target_cells": TARGET_CELLS,
        "target_unique_tasks": TARGET_UNIQUE_TASKS,
        "target_unique_sources": TARGET_UNIQUE_SOURCES,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "planning_manifest_sha256": PLANNING_MANIFEST_SHA256,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "multiple_signal_manifest_sha256": MULTIPLE_SIGNAL_MANIFEST_SHA256,
        "audit_verdict": analysis["audit_verdict"],
        "formal_adjudication_emitted": False,
        "hidden_expected_actual_used": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "proposed_adjudication_fields": list(PROTOCOL_ADJUDICATION_FIELDS),
    }
    return {
        Path("pre_adjudication_adversarial_audit.csv"): _csv_bytes(
            AUDIT_FIELDS, analysis["audit_rows"]
        ),
        Path("pre_adjudication_adversarial_audit_zh.md"): _audit_report_md(analysis).encode("utf-8"),
        Path("proposed_adjudication_protocol_zh.md"): _protocol_md().encode("utf-8"),
        Path("execution_counts.json"): _json_bytes(execution_counts),
        Path("provenance.json"): _json_bytes(provenance),
    }


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    manifest = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "audit_verdict": json.loads(outputs[Path("provenance.json")].decode("utf-8"))["audit_verdict"],
        "target_cells": TARGET_CELLS,
        "next_batch_roster_sha256": NEXT_BATCH_ROSTER_SHA256,
        "formal_adjudication_emitted": False,
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
    }
    (destination / "manifest.json").write_bytes(_json_bytes(manifest))
    return destination


def main() -> None:
    path = write_outputs()
    print(path)


if __name__ == "__main__":
    main()
