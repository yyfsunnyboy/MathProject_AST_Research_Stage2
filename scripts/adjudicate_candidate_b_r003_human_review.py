#!/usr/bin/env python3
"""Freeze the 21-case Candidate B r003 human-review adjudication.

This is a source/AST-only governance analysis.  It never executes candidate
programs, EvalPlus, validation, or a model, and it emits no candidate source.
"""

from __future__ import annotations

import argparse
import ast
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
    "candidate_b_r003_failure_census_human_review_adjudication_v1"
)
START_HEAD = "1eb3dcb119ed387d0023ee8b9d5d3f87446fad27"
SOURCE_DIR = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_failure_census_v1"
)
JOURNAL = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
PAIRED = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv"
)
SOURCE_HASHES = {
    str(SOURCE_DIR / "manifest.json").replace("\\", "/"):
        "6e2dfa1ea9fbc3f7362f8f69ff5b02bae9edb57a4134ca3a6ec58cabfa594593",
    str(SOURCE_DIR / "human_review_queue.csv").replace("\\", "/"):
        "d94dc730cc828062db8522229798045b69d13d79209b108cbcdc6ad87c5baffe",
    str(SOURCE_DIR / "candidate_b_r003_failure_census.csv").replace("\\", "/"):
        "289b2d1e562453bb944032254cc02b47d738a504720aca6dc85da6c252c10740",
    str(SOURCE_DIR / "mbpp_plus_taxonomy_adapter_zh.md").replace("\\", "/"):
        "56bd6e55b044adcccb707a21809c51ef5d806325fa823f6463b928d3f2bc30b3",
    str(JOURNAL).replace("\\", "/"):
        "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    str(PAIRED).replace("\\", "/"):
        "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
}

FIELDS = (
    "review_rank", "program_id", "task_id", "seed", "original_layer",
    "original_subtype", "adjudicated_layer", "adjudicated_subtype",
    "layer_subtype_reasonable", "outcome_validity", "mechanical",
    "unique_transformation", "answer_independent", "repairability_tier",
    "healer_action", "rule_family", "guard_requirements",
    "ambiguity_conditions", "regression_risk", "evidence_summary",
    "evaluation_source_sha256", "source_reviewed", "full_source_emitted",
    "abstain",
)


class AdjudicationError(RuntimeError):
    """Fail-closed provenance, identity, or adjudication error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index_unique(rows: list[dict[str, Any]], field: str, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row[field])
        _require(key not in indexed, f"duplicate identity in {label}: {key}")
        indexed[key] = row
    return indexed


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _verify_sources(repo: Path) -> None:
    for relative, expected in SOURCE_HASHES.items():
        path = repo / relative
        _require(path.is_file(), f"missing source: {relative}")
        _require(_sha(path.read_bytes()) == expected, f"hash drift: {relative}")


def _load_selected_h0_sources(repo: Path, wanted: set[str]) -> dict[str, dict[str, Any]]:
    """Scan the frozen journal but JSON-decode only lines for queued IDs."""
    selected: dict[str, dict[str, Any]] = {}
    needles = {program_id: f'"program_id": "{program_id}"' for program_id in wanted}
    with (repo / JOURNAL).open(encoding="utf-8") as handle:
        for line in handle:
            matched = next((pid for pid, needle in needles.items() if needle in line), None)
            if matched is None:
                continue
            row = json.loads(line)
            _require(row["program_id"] == matched, "journal identity mismatch")
            if row["healer_account"] != "H0":
                continue
            _require(matched not in selected, f"duplicate H0 journal identity: {matched}")
            selected[matched] = row
    _require(set(selected) == wanted, "missing or unexpected queued H0 source")
    return selected


def _case(
    layer: str, subtype: str, validity: str, tier: str, family: str,
    evidence: str, guards: str, ambiguity: str, risk: str,
    *, reasonable: bool = True, mechanical: bool = False,
    unique: bool = False, answer_independent: bool = False,
) -> dict[str, Any]:
    exact = tier == "ELIGIBLE_EXACT"
    return {
        "adjudicated_layer": layer,
        "adjudicated_subtype": subtype,
        "layer_subtype_reasonable": str(reasonable).lower(),
        "outcome_validity": validity,
        "mechanical": str(mechanical).lower(),
        "unique_transformation": str(unique).lower(),
        "answer_independent": str(answer_independent).lower(),
        "repairability_tier": tier,
        "healer_action": "EXISTING_V0_EXACT_ONLY" if exact else "ABSTAIN",
        "rule_family": family,
        "guard_requirements": guards,
        "ambiguity_conditions": ambiguity,
        "regression_risk": risk,
        "evidence_summary": evidence,
        "source_reviewed": "true",
        "full_source_emitted": "false",
        "abstain": str(not exact).lower(),
    }


CASES: dict[int, dict[str, Any]] = {
    1: _case("L1", "TRUNCATED_MISSING_FUNCTION_RETURN", "VALID_MODEL_OUTCOME", "INELIGIBLE", "TRUNCATION_ALGORITHM_COMPLETION_REJECTED", "目標函式只有局部分支回傳，後段推理文字結束但無完整回傳路徑。", "禁止由註解重建算法；完整語法與唯一局部修復均須成立。", "缺失輸出表達式與算法步驟不唯一。", "補寫可能改變算法語義。"),
    2: _case("L1", "TRUNCATED_REPEATED_INCOMPLETE_DEFINITIONS", "VALID_MODEL_OUTCOME", "INELIGIBLE", "TRUNCATION_ALGORITHM_COMPLETION_REJECTED", "同名函式多次重啟，最後停在不完整賦值。", "不得選取或完成任一候選實作。", "候選定義與缺失算法均不唯一。", "選錯版本或補寫會造成語義性 regression。"),
    3: _case("L1", "TRUNCATED_MISSING_RECURRENCE_AND_RETURN", "VALID_MODEL_OUTCOME", "INELIGIBLE", "TRUNCATION_ALGORITHM_COMPLETION_REJECTED", "函式在長段推理後缺少完整遞迴與回傳。", "禁止把自然語言轉成算法。", "所需遞迴與回傳不唯一。", "需要答案理解，非機械修復。"),
    4: _case("L1", "TEXT_POLLUTION_PLUS_INCOMPLETE_REASONING", "VALID_MODEL_OUTCOME", "INELIGIBLE", "TEXT_POLLUTION_REMOVAL_REJECTED", "斜線文字污染造成 parse error，且尾端推理本身截斷。", "僅在移除區段可證明是獨立文字且剩餘程式完整時才可清理。", "污染與未完成算法交織；移除後仍無完整實作。", "清理可能留下可解析但錯誤的殘缺程式。"),
    5: _case("L1", "UNTERMINATED_REASONING_DOCSTRING_NO_IMPLEMENTATION", "VALID_MODEL_OUTCOME", "INELIGIBLE", "DOCSTRING_CLOSURE_REJECTED", "函式主體是未終止的推理字串，沒有可執行算法。", "閉合字串後仍須存在獨立完整函式體。", "閉合位置與缺失實作不唯一。", "只修語法會留下無回傳函式。"),
    6: _case("L1", "EMPTY_SUITE_UNIQUE_PASS_INSERTION", "VALID_MODEL_OUTCOME", "CANDIDATE_REVIEW", "EMPTY_SUITE_PASS_INSERTION_REVIEW", "一個 if suite 只有註解，插入 pass 可唯一解除 SyntaxError；後方另有完整函式版本。", "只允許空 suite、插入 pass、不刪改其他 token；需公開測試與跨題證據。", "較早的廢棄程式仍會先執行，語義安全尚未建立。", "可能解除 parse 後暴露前段 runtime/side-effect 問題。", mechanical=True, unique=True, answer_independent=True),
    7: _case("L1", "UNTERMINATED_REASONING_DOCSTRING_NO_IMPLEMENTATION", "VALID_MODEL_OUTCOME", "INELIGIBLE", "DOCSTRING_CLOSURE_REJECTED", "未終止推理字串覆蓋函式主體，沒有完成實作。", "不得以閉合字串代替算法完成。", "閉合點及函式內容皆不唯一。", "語法修補無法保證 contract。"),
    8: _case("L1", "TRUNCATED_DUPLICATE_OVERRIDE_EMPTY_NESTED_SUITE", "VALID_MODEL_OUTCOME", "INELIGIBLE", "DUPLICATE_OVERRIDE_DELETION_REJECTED", "多個同名實作後，最後覆寫版本停在空的巢狀函式 suite。", "不得刪除最後定義或選取先前版本；pass 不得使不完整覆寫生效。", "應保留哪個版本及缺失內容不唯一。", "刪除或補 pass 都可能選錯語義。"),
    9: _case("L1", "TRUNCATED_REPEATED_ATTEMPTS_WITH_EMPTY_SUITE", "VALID_MODEL_OUTCOME", "INELIGIBLE", "DUPLICATE_OVERRIDE_DELETION_REJECTED", "早段有空 while suite，後續多次重寫且最後表達式截斷。", "所有未完成區段須獨立可刪且剩餘唯一完整版本，現況不符。", "多個候選與兩處以上缺口。", "局部修語法可能執行錯誤候選。"),
    10: _case("L2", "REQUIRED_FUNCTION_MISSING_AMBIGUOUS_ENTRYPOINT", "VALID_MODEL_OUTCOME", "INELIGIBLE", "AMBIGUOUS_ENTRYPOINT_ALIAS_REJECTED", "required function 缺失，存在兩個 arity 相容頂層函式。", "唯一相容 callable、無副作用 helper、名稱與 arity 均須唯一。", "兩個相容候選，必須理解語義才能選擇。", "錯誤 alias 會封裝不相干 helper。"),
    11: _case("L2", "SIGNATURE_MISMATCH_WRAPPER_REQUIRES_SEMANTIC_MAPPING", "VALID_MODEL_OUTCOME", "INELIGIBLE", "SIGNATURE_WRAPPER_REJECTED", "公開 contract 為三參數，實作與自測只接受兩參數。", "wrapper 只能做無損、唯一的參數轉送；不得合成參數。", "三參數到兩參數的映射需領域公式。", "wrapper 會猜測參數語義。"),
    12: _case("L2", "SIGNATURE_MISMATCH_WRAPPER_REQUIRES_SEMANTIC_MAPPING", "VALID_MODEL_OUTCOME", "INELIGIBLE", "SIGNATURE_WRAPPER_REJECTED", "與同題另一 seed 相同的三對二參數不相容。", "wrapper 只能做無損、唯一的參數轉送；不得合成參數。", "跨 seed 重複不等於跨題通則，仍需語義映射。", "錯誤參數映射造成系統性錯答。"),
    13: _case("L2", "SIGNATURE_MISMATCH_WRAPPER_REQUIRES_SEMANTIC_MAPPING", "VALID_MODEL_OUTCOME", "INELIGIBLE", "SIGNATURE_WRAPPER_REJECTED", "第三個相同 source 的三對二參數不相容。", "不得利用 task 身份或答案選擇 wrapper 公式。", "僅一個 task，沒有跨題安全證據。", "單題特化風險高。"),
    14: _case("L2", "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS", "VALID_MODEL_OUTCOME", "ELIGIBLE_EXACT", "EXISTING_UNIQUE_ENTRYPOINT_ALIAS_V0", "唯一頂層 callable 與公開 entrypoint arity 相容；既有 H1 做純 alias，正式結果 fail→fail。", "required name 缺失；全域唯一 arity-compatible callable；不改函式體；拒絕多候選。", "只有一個 task，僅證明 packaging 轉換唯一，未證明功能 rescue。", "alias 本身低風險，但可暴露原函式的 L5 錯誤。", mechanical=True, unique=True, answer_independent=True),
    15: _case("L2", "REQUIRED_FUNCTION_MISSING_UNIQUE_ALIAS", "VALID_MODEL_OUTCOME", "ELIGIBLE_EXACT", "EXISTING_UNIQUE_ENTRYPOINT_ALIAS_V0", "另一 seed 亦有唯一 arity-compatible callable；既有 H1 純 alias 後仍 fail→fail。", "與既有 v0 strict alias guards 完全一致。", "兩 cell 仍只跨一個 task。", "不可把 packaging 成功等同功能修復。", mechanical=True, unique=True, answer_independent=True),
    16: _case("UNRESOLVED", "PENDING_EXECUTION_DIAGNOSTIC", "PENDING_REVIEW", "UNRESOLVED", "EXECUTION_DIAGNOSTICS_REQUIRED", "source 可解析且 contract 外觀完整；僅有 base/plus 聚合失敗。", "需要不含 hidden 值的失敗 phase、exception 類型與 source frame。", "無法區分 runtime/data-flow 與算法錯誤。", "無診斷即修補會猜測答案。"),
    17: _case("UNRESOLVED", "PENDING_EXECUTION_DIAGNOSTIC", "PENDING_REVIEW", "UNRESOLVED", "EXECUTION_DIAGNOSTICS_REQUIRED", "source/AST 未呈現唯一 packaging 或 syntax 缺陷，只有聚合測試狀態。", "需 base/plus phase 與回傳 type/shape，不得記錄測試值。", "可能是 edge semantics 或 runtime。", "以隱藏案例反推規則將過擬合。"),
    18: _case("UNRESOLVED", "PENDING_EXECUTION_DIAGNOSTIC", "PENDING_REVIEW", "UNRESOLVED", "EXECUTION_DIAGNOSTICS_REQUIRED", "函式與呼叫結構可解析，無唯一機械缺口。", "需 exception/timeout/return-shape 等最小診斷。", "公式正確性不能由 AST 單獨裁定。", "任何公式改寫都需要答案理解。"),
    19: _case("UNRESOLVED", "PENDING_EXECUTION_DIAGNOSTIC", "PENDING_REVIEW", "UNRESOLVED", "EXECUTION_DIAGNOSTICS_REQUIRED", "完整可解析實作，聚合結果不足以定位 failure layer。", "僅收集 phase、exception class、source frame 與 type/shape。", "邊界條件與資料流錯誤未區分。", "沒有唯一、跨題 transformation。"),
    20: _case("UNRESOLVED", "PENDING_EXECUTION_DIAGNOSTIC", "PENDING_REVIEW", "UNRESOLVED", "EXECUTION_DIAGNOSTICS_REQUIRED", "同名函式覆寫存在，但較早定義不會成為最終 entrypoint；聚合失敗仍無定位。", "需證明實際 failure phase；不得任意刪除任一定義。", "duplicate definition 不等於 failure cause。", "刪除程式可能移除必要初始化或副作用。"),
    21: _case("L4", "SELF_RECURSIVE_OVERRIDE_RUNTIME", "VALID_MODEL_OUTCOME", "INELIGIBLE", "SELF_RECURSION_REWRITE_REJECTED", "最後同名定義以相同參數呼叫自身，覆寫先前版本，形成 source 可觀察的無進展遞迴。", "可分類 L4；修復仍不得選取先前算法或改寫遞迴。", "應刪除覆寫、改名或改算法並不唯一。", "任一修法都需理解預期算法。", reasonable=False),
}


def _verify_structural_evidence(rows: list[dict[str, Any]], sources: dict[str, dict[str, Any]]) -> None:
    for row in rows:
        source = sources[row["program_id"]]["evaluation_source"]
        _require(_sha(source.encode("utf-8")) == row["evaluation_source_sha256"],
                 f"evaluation source hash drift: rank {row['review_rank']}")
        rank = int(row["review_rank"])
        if 1 <= rank <= 9:
            try:
                ast.parse(source)
                parseable = True
            except SyntaxError:
                parseable = False
            if rank >= 4:
                _require(not parseable, f"expected parse failure drift: rank {rank}")
        if rank == 21:
            tree = ast.parse(source)
            functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
            last = functions[-1]
            recursive_same_args = any(
                isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == last.name
                for node in ast.walk(last)
            )
            _require(sum(node.name == last.name for node in functions) >= 2,
                     "rank 21 duplicate override evidence drift")
            _require(recursive_same_args, "rank 21 recursion evidence drift")


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    _verify_sources(repo)
    queue = _read_csv(repo / SOURCE_DIR / "human_review_queue.csv")
    census = _read_csv(repo / SOURCE_DIR / "candidate_b_r003_failure_census.csv")
    _require(len(queue) == 21, "human-review queue row-count drift")
    _require(len({row["program_id"] for row in queue}) == 21, "duplicate queue identity")
    _require({int(row["review_rank"]) for row in queue} == set(CASES), "review rank drift")
    _require("source" not in queue[0] and "evaluation_source" not in queue[0],
             "source leaked into queue")
    census_by_id = _index_unique(census, "program_id", "failure census")
    _require(len(census_by_id) == 300, "census identity drift")
    wanted = {row["program_id"] for row in queue}
    sources = _load_selected_h0_sources(repo, wanted)
    paired = _index_unique(
        [row for row in _read_csv(repo / PAIRED)
         if row["prompt_condition"] == "Candidate_B"],
        "program_id", "paired Candidate B",
    )
    _require(len(paired) == 300, "paired Candidate B identity drift")

    results: list[dict[str, Any]] = []
    for queue_row in sorted(queue, key=lambda row: int(row["review_rank"])):
        rank = int(queue_row["review_rank"])
        pid = queue_row["program_id"]
        original = census_by_id.get(pid)
        _require(original is not None, f"queue identity missing from census: {pid}")
        source_row = sources[pid]
        _require(str(source_row["task_id"]) == queue_row["task_id"], "journal task drift")
        _require(str(source_row["seed"]) == queue_row["seed"], "journal seed drift")
        _require(source_row["evaluation_source_sha256"] == queue_row["evaluation_source_sha256"],
                 "journal/queue source hash drift")
        row = {
            "review_rank": rank,
            "program_id": pid,
            "task_id": queue_row["task_id"],
            "seed": queue_row["seed"],
            "original_layer": original["primary_failure_layer"],
            "original_subtype": original["failure_subtype"],
            "evaluation_source_sha256": queue_row["evaluation_source_sha256"],
            **CASES[rank],
        }
        if rank in (14, 15):
            transition = paired[pid]
            _require(transition["source_changed_by_healer"] == "true", "alias H1 change drift")
            _require(transition["healer_transition"] == "fail_to_fail", "alias outcome drift")
        results.append(row)
    _verify_structural_evidence(results, sources)
    return {"rows": results, "queue": queue}


def _family_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("EXISTING_UNIQUE_ENTRYPOINT_ALIAS_V0", "existing_v0", "唯一 entrypoint alias", "ELIGIBLE_EXACT", "required name 缺失；唯一 arity-compatible callable；純 alias；多候選即 abstain", "只有一個 task，且正式 H1 為 2 個 fail→fail", "低 packaging 風險；不保證功能正確", "保留既有 v0；非新規則"),
        ("EMPTY_SUITE_PASS_INSERTION_REVIEW", "new_candidate", "空 suite 插入 pass", "CANDIDATE_REVIEW", "只插入 pass；不得刪改其他 token；後續須為獨立完整程式", "前段仍可能執行且只有一個 task/cell", "解除 parse 後可能暴露 runtime/side effect", "不實作；收集跨題公開證據"),
    ]
    output = []
    for family, status, mechanism, tier, guard, ambiguity, risk, decision in specs:
        matched = [row for row in rows if row["rule_family"] == family]
        output.append({
            "rule_family": family,
            "new_or_existing": status,
            "mechanism": mechanism,
            "supported_cells": len(matched),
            "unique_tasks": len({row["task_id"] for row in matched}),
            "repairability_tier": tier,
            "safe_cross_task_family": "false",
            "guard_requirements": guard,
            "ambiguity_conditions": ambiguity,
            "regression_risk": risk,
            "formal_observation": "2 fail_to_fail; 0 rescue" if status == "existing_v0" else "not executed",
            "decision": decision,
        })
    return output


def _rejected_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = [
        ("TRUNCATION_ALGORITHM_COMPLETION_REJECTED", "補寫截斷算法/回傳", "需要生成缺失算法，非唯一機械修復"),
        ("TEXT_POLLUTION_REMOVAL_REJECTED", "移除斜線或文字污染", "污染與截斷推理交織，清理後程式仍不完整"),
        ("DOCSTRING_CLOSURE_REJECTED", "閉合推理 docstring", "閉合位置及缺失函式體不唯一"),
        ("DUPLICATE_OVERRIDE_DELETION_REJECTED", "刪除最後重複定義或加 pass", "選擇候選版本需要算法判斷"),
        ("AMBIGUOUS_ENTRYPOINT_ALIAS_REJECTED", "多候選 entrypoint alias", "候選不唯一"),
        ("SIGNATURE_WRAPPER_REJECTED", "三參數到兩參數 wrapper", "需要領域公式與參數語義"),
        ("SELF_RECURSION_REWRITE_REJECTED", "改寫無進展 self recursion", "L4 可定位但修法不唯一"),
        ("EXECUTION_DIAGNOSTICS_REQUIRED", "從聚合 fail 推導語義修補", "無 failure phase/exception，禁止猜測 L5 或答案"),
    ]
    output = []
    for family, candidate, reason in groups:
        matched = [row for row in rows if row["rule_family"] == family]
        output.append({
            "rejected_family": family,
            "candidate_transformation": candidate,
            "reviewed_cells": len(matched),
            "unique_tasks": len({row["task_id"] for row in matched}),
            "rejection_reason": reason,
            "required_abstention_guard": "不得使用 task_id、答案或 hidden tests；非唯一或需算法理解即 abstain",
        })
    return output


def _diagnostic_rows() -> list[dict[str, str]]:
    return [
        {"diagnostic_id": "D01", "field": "failure_phase", "minimum_content": "module_import|entrypoint_lookup|signature_bind|call|base_assert|plus_assert|timeout", "purpose": "區分 L2/L4/可能 L5", "non_leak_guard": "不得記錄測試輸入、expected 或實際答案"},
        {"diagnostic_id": "D02", "field": "exception_class", "minimum_content": "Python exception 類別或 NONE", "purpose": "辨識 runtime/data-flow 類型", "non_leak_guard": "不保存 exception message 中的 hidden 值"},
        {"diagnostic_id": "D03", "field": "model_source_frame", "minimum_content": "最後一個 model-source line number 與 AST node kind", "purpose": "定位 source 可觀察機制", "non_leak_guard": "不保存 evaluator/hidden-test frame 或 source 全文"},
        {"diagnostic_id": "D04", "field": "entrypoint_binding", "minimum_content": "required name found、callable、signature bind success 三個布林值", "purpose": "確認 packaging/contract failure", "non_leak_guard": "只使用公開 contract"},
        {"diagnostic_id": "D05", "field": "termination_and_return_shape", "minimum_content": "returned|raised|timeout 與 return type/shape 類別", "purpose": "區分 timeout、runtime、contract shape", "non_leak_guard": "不得記錄 return value 或 hidden assertion"},
        {"diagnostic_id": "D06", "field": "bounded_io_metadata", "minimum_content": "stdout/stderr 是否存在及 byte length", "purpose": "辨識污染或非預期 side effect", "non_leak_guard": "不保存 stdout/stderr 內容"},
        {"diagnostic_id": "D07", "field": "identity_hashes", "minimum_content": "program/source/evaluator/revision hash", "purpose": "將診斷綁定 frozen cell", "non_leak_guard": "hash drift 必須 fail-closed"},
    ]


def _report(rows: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> str:
    tiers = Counter(row["repairability_tier"] for row in rows)
    layers = Counter(row["adjudicated_layer"] for row in rows)
    validity = Counter(row["outcome_validity"] for row in rows)
    abstain = [str(row["review_rank"]) for row in rows if row["abstain"] == "true"]
    return f"""# Candidate B r003 failure census：human-review adjudication

## 範圍與方法

本裁決只審查 frozen `human_review_queue.csv` 的 21 個代表案例。程式以 program identity 從 r003 frozen H0 journal 擷取這 21 份 source，逐一驗證 source SHA-256；不修改原始資料，也不輸出完整 source。判斷只使用公開 contract 與 source/AST 可觀察證據。本次是 development replay 的治理分析，不是 validation。

執行邊界：`model_calls=0`、`evalplus_executions=0`、`healer_rules_modified=false`、`validation_not_executed=true`。

## 裁決總覽

- 21 案 repairability：ELIGIBLE_EXACT {tiers['ELIGIBLE_EXACT']}、CANDIDATE_REVIEW {tiers['CANDIDATE_REVIEW']}、INELIGIBLE {tiers['INELIGIBLE']}、UNRESOLVED {tiers['UNRESOLVED']}。
- adjudicated layer：{', '.join(f'{key} {value}' for key, value in sorted(layers.items()))}。
- outcome validity：VALID_MODEL_OUTCOME {validity['VALID_MODEL_OUTCOME']}；PENDING_REVIEW {validity['PENDING_REVIEW']}。
- rank 21 可由重複覆寫後的無進展 self recursion 升為 L4；修法仍不唯一，故 INELIGIBLE。

## L1 裁決

未發現「只移除 Markdown／文字污染即可留下完整、唯一程式」的安全案例。rank 4 的文字污染與截斷推理交織；rank 5、7 是未終止推理 docstring 且沒有實作；rank 1–3、8–9 都需要補寫算法或選擇重複候選，必須 abstain。rank 6 的空 suite 插入 `pass` 是唯一局部 token 修復，且不需要答案；但較早程式仍可能先執行，只有 1 cell／1 task，也沒有允許的新 execution 證據，因此只列 CANDIDATE_REVIEW，不實作。

## L2 裁決

rank 14–15 是相同機制的 unique entrypoint alias：公開 required name 缺失、只有一個 arity-compatible 頂層 callable，純 alias 為機械且唯一，因此 2 案升為 ELIGIBLE_EXACT。這是既有 Healer v0 family，不是新規則；正式 H1 兩案均 fail→fail，代表 packaging 轉換精確，不代表功能被救回。rank 10 有兩個相容候選，屬 ambiguous entrypoint。rank 11–13 的三參數 contract 對兩參數實作需要語義性參數映射，wrapper 不安全；3 cells 也只來自 1 task。

## Candidate rule families

沒有至少跨 2 個不同 task、且達到安全與唯一要求的**新** rule family。既有 unique alias 有 2 cells／1 task；空 suite 候選有 1 cell／1 task。所有其他候選均因截斷、歧義、需算法理解或缺 execution diagnostic 而拒絕。

## 必須 abstain 的案例

除 rank 14–15 的既有 exact alias 外，其餘 19 案目前都必須對自動修復 abstain：rank {', '.join(abstain)}。其中 rank 6 可保留作研究候選，但在跨題證據與安全診斷不足前仍不得實作。

## 是否足以設計 Healer v1

不足。21 案沒有安全的跨題新 family；唯一 exact family 已存在於 v0 且沒有 rescue，另一個局部 token 候選只有單一案例。這些證據不足以開始設計或實作 Healer v1，也不得將單題修補宣稱為通則。

## 198 unresolved 的最小診斷

後續若依預先核准流程收集 diagnostics，最小集合應是：failure phase、exception class、最後一個 model-source frame 的 line/AST node、entrypoint/signature binding、termination 與 return type/shape、bounded stdout/stderr metadata，以及完整 identity hashes。只保留類別與形狀，不保存 hidden-test 輸入、expected、實際答案、evaluator frame 或輸出內容。這足以協助區分 L2、L4 與仍待判定的 L5，同時避免用 hidden tests 設計規則。

## 保守結論

可升為 ELIGIBLE_EXACT 的是 2/21，且都只是既有 unique-alias guard 下的 packaging 修復；沒有跨 2 tasks 的安全新 rule family。其餘 19 案 abstain。Candidate B failure census 仍是有價值的 development evidence，但目前不授權 Healer v1 設計、規則修改或 untouched20 validation。
"""


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    analysis = build_analysis(repo)
    rows = analysis["rows"]
    families = _family_rows(rows)
    rejected = _rejected_rows(rows)
    diagnostics = _diagnostic_rows()
    outputs: dict[Path, bytes] = {
        Path("adjudication_results.csv"): _csv_bytes(FIELDS, rows),
        Path("candidate_rule_family_review.csv"): _csv_bytes(tuple(families[0]), families),
        Path("rejected_rule_candidates.csv"): _csv_bytes(tuple(rejected[0]), rejected),
        Path("remaining_diagnostic_requirements.csv"): _csv_bytes(tuple(diagnostics[0]), diagnostics),
        Path("human_review_report_zh.md"): _report(rows, families).encode("utf-8"),
    }
    provenance = {
        "analysis_version": "candidate_b_r003_failure_census_human_review_adjudication_v1",
        "start_head": START_HEAD,
        "source_census_version": "candidate_b_r003_failure_census_v1",
        "candidate_response_source": "r003_only",
        "reviewed_queue_cells": 21,
        "source_extraction": "stream_scan_then_json_decode_queued_program_ids_only_h0",
        "source_modified": False,
        "full_source_emitted": False,
        "public_contract_and_source_ast_only": True,
        "task_id_or_answer_based_rules": False,
        "hidden_tests_used_for_rule_design": False,
        "development_replay_only": True,
    }
    outputs[Path("provenance.json")] = _json_bytes(provenance)
    ledger_rows = [
        {"path": relative, "sha256": expected, "role": "frozen_input"}
        for relative, expected in sorted(SOURCE_HASHES.items())
    ]
    analyzer_relative = "scripts/adjudicate_candidate_b_r003_human_review.py"
    ledger_rows.append({
        "path": analyzer_relative,
        "sha256": _sha((repo / analyzer_relative).read_bytes()),
        "role": "reproducible_analyzer",
    })
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(
        ("path", "sha256", "role"), ledger_rows
    )
    execution = {
        "analysis_mode": "deterministic_source_ast_human_adjudication",
        "reviewed_cells": 21,
        "model_calls": 0,
        "evalplus_executions": 0,
        "healer_rules_modified": False,
        "validation_not_executed": True,
        "candidate_programs_executed": 0,
        "outputs_contain_full_source": False,
    }
    outputs[Path("execution_manifest.json")] = _json_bytes(execution)
    hashes = {str(path).replace("\\", "/"): _sha(data)
              for path, data in sorted(outputs.items(), key=lambda item: str(item[0]))}
    tiers = Counter(row["repairability_tier"] for row in rows)
    manifest = {
        "manifest_version": "candidate_b_r003_failure_census_human_review_adjudication_v1",
        "status": "complete_development_only_no_healer_v1_authorization",
        "reviewed_cells": 21,
        "eligible_exact": tiers["ELIGIBLE_EXACT"],
        "candidate_review": tiers["CANDIDATE_REVIEW"],
        "ineligible": tiers["INELIGIBLE"],
        "unresolved": tiers["UNRESOLVED"],
        "abstain_cells": sum(row["abstain"] == "true" for row in rows),
        "safe_new_rule_families_crossing_two_tasks": 0,
        "unresolved_population_requiring_minimal_diagnostics": 198,
        "model_calls": 0,
        "evalplus_executions": 0,
        "healer_rules_modified": False,
        "validation_not_executed": True,
        "outputs_sha256_excluding_manifest": hashes,
    }
    outputs[Path("manifest.json")] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, content in build_outputs(repo).items():
        (output_dir / relative).write_bytes(content)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    print(write_outputs(args.repo_root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
