#!/usr/bin/env python3
"""Build the Traditional Chinese human-review attachment for Milestone 1D."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_mbpp_development_failure_census as milestone_1c  # noqa: E402
from scripts import build_mbpp_scaffold_healer_evidence_packets as milestone_1d  # noqa: E402


RUN_RELATIVE = milestone_1c.RUN_RELATIVE
M1D_RELATIVE = RUN_RELATIVE / "milestone_1d_evidence_review"

EXPECTED_ENGLISH_EVIDENCE_HASHES = {
    "evidence_manifest.json": "c764bb7b173cd853ba6164046a55e94bbcda0b15b1a8e4bbd21ec9e53b6852ab",
    "evidence_summary.md": "d4d24dcadab8bbcf0fe8437f3d87b5b104bcefe60fe2451ec7812a1a4e3288e0",
    "failure_signature_clusters.csv": "f4e1acdbb8bc5ad09c7af6a5de3afee7259f49f2aad987e57ee16d1b3b66b72c",
    "human_review_packet.md": "6d925455fd14b33b42a851a28732ca7e3918abf629062a0e24198121e0d78ddd",
    "scaffold_evidence_ledger.csv": "ea71e31175e72fc9146299dc2172ec85b8a6cb5c75bbbff55d5533305023f6ad",
}

READING_AID_NOTICE = "閱讀輔助，若有歧義以英文原文為準。"

PROMPT_TRANSLATIONS_ZH = {
    "Mbpp/124": "撰寫一個函式，取得複數的角度。",
    "Mbpp/125": "撰寫一個函式，在給定二進位字串的所有子字串中，找出 0 的數量減去 1 的數量之最大差值。",
    "Mbpp/259": "撰寫一個函式，對給定的兩個 tuple 進行逐位置最大化。",
    "Mbpp/420": "撰寫一個 Python 函式，計算前 n 個偶自然數的立方和。",
    "Mbpp/597": "撰寫一個函式，從給定的兩個已排序 array 中找出第 k 個元素。",
    "Mbpp/603": "撰寫一個函式，取得所有小於或等於給定整數的 lucid numbers（原文用語）。",
    "Mbpp/633": "撰寫一個 Python 函式，計算給定 list 中所有數字配對的 xor 總和。",
    "Mbpp/721": "給定一個以 list of lists 表示的 N×N 方陣，每個 cell 都有特定 cost。path 從左上角開始，每一步只能向右或向下，並在右下角結束。請找出所有既有 paths 中平均值最大的 path；平均值為 path 的 total cost 除以造訪的 cell 數量。",
    "Mbpp/732": "撰寫一個函式，將所有 space、comma 或 dot 替換成 colon。",
    "Mbpp/739": "撰寫一個 Python 函式，找出第一個具有 n 位數之 triangular number 的 index。",
    "Mbpp/765": "撰寫一個函式，找出第 n 個 polite number。",
    "Mbpp/769": "撰寫一個 Python 函式，取得兩個 lists 之間的差集。",
    "Mbpp/777": "撰寫一個 Python 函式，計算給定 list 中未重複元素的總和。",
    "Mbpp/792": "撰寫一個 Python 函式，計算給定 lists 集合中 list 的數量。",
}

ERROR_REASON_ZH = {
    "syntax_fstring_parse_error": "保存的 Pipeline 程式無法通過 Python AST 解析；parser 指向 f-string 語法錯誤。僅憑此訊號無法確定原本預期的插值或格式語意。",
    "syntax_unterminated_string": "保存的 Pipeline 程式無法通過 Python AST 解析；parser 指出字串 literal 未終止。不能在不知道原定字串邊界與內容的情況下直接補上引號。",
    "syntax_invalid_plain_text": "Pipeline 使用 plain_text 路徑保留內容，但保存的內容無法通過 Python AST 解析。不得在未證明剩餘內容是唯一預期程式前，直接刪除文字。",
    "entrypoint_no_unique_candidate": "保存的程式未定義題目要求的 entry point，且不存在唯一、arity 相容的 top-level function，因此未通過 entry-point safety gate。",
    "unknown_eval_failure_single_top_level_function": "保存的程式可編譯且包含預期 entry point，但 EvalPlus 只保存 generic failure。現有證據無法區分 functional assertion failure、import/name failure 或 runtime exception。",
    "unknown_eval_failure_multiple_top_level_functions": "保存的程式可編譯且包含預期 entry point，但同時有多個 top-level functions，而 EvalPlus 只保存 generic failure。不得依 evaluator failure 選擇、刪除或合併函式。",
}

CSV_FIELDS = (
    "task_id",
    "seed",
    "cell_id",
    "failure_category",
    "signature_id",
    "raw_generation_sha256",
    "pipeline_program_sha256",
    "translation_notice_zh",
    "prompt_reading_aid_zh",
    "original_prompt_en",
    "error_reason_zh",
    "snippet_line_start",
    "snippet_line_end",
    "code_snippet_original",
    "exception_or_diagnostic_original",
    "reviewer",
    "decision",
    "semantic_risk",
    "rationale_zh",
    "do_not_repair_conditions_zh",
)

HUMAN_FIELDS = (
    "reviewer",
    "decision",
    "semantic_risk",
    "rationale_zh",
    "do_not_repair_conditions_zh",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise milestone_1c.CensusIntegrityError(message)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _load_active_tasks(repo_root: Path, selected_ids: list[str]) -> dict[str, dict[str, str]]:
    selected = set(selected_ids)
    tasks: dict[str, dict[str, str]] = {}
    with (repo_root / milestone_1c.TASKS_RELATIVE).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") not in selected:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"{record.get('task_id')}: model-visible task schema drift",
            )
            tasks[record["task_id"]] = record
    _require(set(tasks) == selected, "active development task set mismatch")
    return tasks


def _snippet_for_source(source: str, signature_id: str, entry_point: str) -> tuple[int, int, str]:
    lines = source.splitlines()
    _require(bool(lines), "manual-review source is empty")
    if signature_id.startswith("syntax_"):
        try:
            ast.parse(source)
        except SyntaxError as exc:
            line_number = exc.lineno or 1
            start = max(1, line_number - 2)
            end = min(len(lines), line_number + 2)
            return start, end, "\n".join(lines[start - 1 : end])
        raise milestone_1c.CensusIntegrityError("syntax case parsed successfully")

    if signature_id.startswith("unknown_"):
        tree = ast.parse(source)
        matching = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == entry_point
        ]
        _require(bool(matching), f"{entry_point}: expected function missing from unknown case")
        node = matching[0]
        start = node.lineno
        end = min(node.end_lineno or node.lineno, start + 39)
        return start, end, "\n".join(lines[start - 1 : end])

    start = 1
    end = min(len(lines), 40)
    return start, end, "\n".join(lines[:end])


def _diagnostic_original(
    source: str,
    signature_id: str,
    census_row: dict[str, str],
    evaluation: dict[str, str],
) -> str:
    if signature_id.startswith("syntax_"):
        try:
            ast.parse(source)
        except SyntaxError as exc:
            return (
                f"pipeline_corrected_syntax_compile_status={evaluation['pipeline_corrected_syntax_compile_status']}; "
                f"SyntaxError.msg={exc.msg}; lineno={exc.lineno}; offset={exc.offset}"
            )
        raise milestone_1c.CensusIntegrityError("syntax diagnostic unavailable")
    if signature_id == "entrypoint_no_unique_candidate":
        return census_row["exception_type_or_evaluator_outcome"]
    return (
        f"pipeline_corrected_runtime_timeout_status={evaluation['pipeline_corrected_runtime_timeout_status']}; "
        f"pipeline_corrected_evalplus_pass={evaluation['pipeline_corrected_evalplus_pass']}; "
        "exception_detail=not_saved"
    )


def build_rows(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    repo_root = repo_root.resolve()
    m1d_dir = repo_root / M1D_RELATIVE
    actual_hashes = {
        name: _sha256_bytes((m1d_dir / name).read_bytes())
        for name in EXPECTED_ENGLISH_EVIDENCE_HASHES
    }
    _require(
        actual_hashes == EXPECTED_ENGLISH_EVIDENCE_HASHES,
        "Milestone 1D English evidence hash mismatch",
    )

    _, clusters, manifest = milestone_1d.build_packets(repo_root)
    _require(manifest["proposed_action_cell_counts"]["manual_review"] == 33, "manual-review count mismatch")
    manual_signatures = {
        row["signature_id"]
        for row in clusters
        if row["proposed_action"] == "manual_review"
    }
    census_rows, _ = milestone_1c.build_census(repo_root)
    run_dir = repo_root / RUN_RELATIVE
    plan = json.loads((run_dir / "generation_plan.json").read_text(encoding="utf-8"))
    pipeline_by_id = {
        row["generation_id"]: row
        for row in _read_jsonl(run_dir / "pipeline_corrected.jsonl")
    }
    with (run_dir / "evaluation_results.csv").open(encoding="utf-8", newline="") as handle:
        evaluation_by_id = {row["generation_id"]: row for row in csv.DictReader(handle)}
    tasks = _load_active_tasks(repo_root, plan["task_ids"])

    rows: list[dict[str, str]] = []
    for census_row in census_rows:
        cell_id = census_row["cell_id"]
        pipeline = pipeline_by_id[cell_id]
        task = tasks[census_row["task_id"]]
        signature_id = milestone_1d._signature_for_failure(census_row, pipeline, task)
        if signature_id not in manual_signatures:
            continue
        source = pipeline["pipeline_corrected_output"]
        _require(isinstance(source, str), f"{cell_id}: manual-review program missing")
        start, end, snippet = _snippet_for_source(source, signature_id, task["entry_point"])
        rows.append(
            {
                "task_id": census_row["task_id"],
                "seed": census_row["seed"],
                "cell_id": cell_id,
                "failure_category": census_row["failure_category"],
                "signature_id": signature_id,
                "raw_generation_sha256": census_row["raw_generation_sha256"],
                "pipeline_program_sha256": census_row["extracted_program_sha256"],
                "translation_notice_zh": READING_AID_NOTICE,
                "prompt_reading_aid_zh": PROMPT_TRANSLATIONS_ZH[census_row["task_id"]],
                "original_prompt_en": task["prompt"],
                "error_reason_zh": ERROR_REASON_ZH[signature_id],
                "snippet_line_start": str(start),
                "snippet_line_end": str(end),
                "code_snippet_original": snippet,
                "exception_or_diagnostic_original": _diagnostic_original(
                    source, signature_id, census_row, evaluation_by_id[cell_id]
                ),
                "reviewer": "",
                "decision": "",
                "semantic_risk": "",
                "rationale_zh": "",
                "do_not_repair_conditions_zh": "",
            }
        )

    counts = Counter(row["failure_category"] for row in rows)
    _require(len(rows) == 33, "Chinese adjudication ledger must contain 33 rows")
    _require(
        counts == {"syntax_failure": 6, "missing_or_wrong_entry_point": 1, "unknown": 26},
        "Chinese adjudication category counts mismatch",
    )
    _require(len({row["cell_id"] for row in rows}) == 33, "duplicate Chinese adjudication cell")
    _require(set(PROMPT_TRANSLATIONS_ZH) == {row["task_id"] for row in rows}, "translation task set mismatch")
    _require(all(not row[field] for row in rows for field in HUMAN_FIELDS), "human adjudication fields must remain blank")
    return rows


def render_csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def render_packet(rows: list[dict[str, str]]) -> bytes:
    lines = [
        "# Milestone 1D 中文人工審查附件",
        "",
        f"> **{READING_AID_NOTICE}** 中文內容僅協助研究人員閱讀；英文題目、程式碼、識別碼與 exception/diagnostic 原文均保留不變。",
        "",
        "## 簡要判定指南",
        "",
        "1. 先核對 `task_id`、`seed`、`cell_id` 與 SHA-256，確認正在審查正確 cell。",
        "2. 以英文題目為規格來源；中文翻譯只作閱讀輔助。",
        "3. Syntax error 不代表存在語意安全的自動修復。不得只因能通過 parser 就判為可修復。",
        "4. Entry-point repair 必須同時滿足唯一候選函式、呼叫 arity 相容，且不需要改寫 function body 或 control flow。",
        "5. Generic/unknown evaluator failure 不足以區分 functional、import/name 或 runtime 問題，預設應選 `insufficient_evidence` 或 `nonrepairable`，除非另有本附件範圍內的直接證據。",
        "6. 30 次 Pipeline rescue 不屬於本附件的 33 個人工案例，也不得記為 Healer 成效。",
        "7. 請只在 `human_adjudication_zh.csv` 的空白人工欄位填寫結論；本附件未預填任何裁決。",
        "",
        "允許的 `decision`：`scaffold_only`、`healer_candidate`、`nonrepairable`、`insufficient_evidence`。允許的 `semantic_risk`：`low`、`medium`、`high`。",
        "",
        "## 術語表",
        "",
        "| 術語 | 中文說明 |",
        "|---|---|",
        "| Observed | 模型原始輸出的評估帳 |",
        "| Pipeline correction | 既有 deterministic extraction 處理；不是 Healer |",
        "| Scaffold | 約束生成輸出格式或結構的候選機制 |",
        "| Healer candidate | 僅表示值得人工審查的修復候選，不是已驗證規則 |",
        "| entry point | 題目與 evaluator 預期呼叫的函式名稱 |",
        "| safety gate | 對候選修復施加的必要條件；未通過即不可自動修復 |",
        "| semantic risk | 修復改變程式原意或行為的風險 |",
        "| insufficient evidence | 現有保存證據不足以支持修復判定 |",
        "",
        "## 案例索引",
        "",
        "| # | Task | Seed | Category | Signature | Cell ID |",
        "|---:|---|---:|---|---|---|",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | `{row['task_id']}` | {row['seed']} | `{row['failure_category']}` | "
            f"`{row['signature_id']}` | `{row['cell_id']}` |"
        )
    lines.extend(["", "## 個案資料", ""])
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"### {index}. `{row['task_id']}` / seed `{row['seed']}`",
                "",
                f"- Cell ID：`{row['cell_id']}`",
                f"- Category：`{row['failure_category']}`",
                f"- Signature：`{row['signature_id']}`",
                f"- Raw SHA-256：`{row['raw_generation_sha256']}`",
                f"- Pipeline SHA-256：`{row['pipeline_program_sha256']}`",
                "",
                f"**題目閱讀輔助翻譯：** {row['prompt_reading_aid_zh']}",
                "",
                f"> **{row['translation_notice_zh']}**",
                "",
                "**原始英文題目：**",
                "",
                "````text",
                row["original_prompt_en"],
                "````",
                "",
                f"**錯誤原因中文解釋：** {row['error_reason_zh']}",
                "",
                f"**原始 exception／diagnostic：** `{row['exception_or_diagnostic_original']}`",
                "",
                f"**需要檢查的原始程式片段（lines {row['snippet_line_start']}–{row['snippet_line_end']}）：**",
                "",
                "````python",
                row["code_snippet_original"],
                "````",
                "",
                "人工判定欄位請至 `human_adjudication_zh.csv` 填寫；目前均為空白。",
                "",
            ]
        )
    return "\n".join(lines).encode("utf-8")


def write_outputs(repo_root: Path, output_dir: Path) -> None:
    rows = build_rows(repo_root)
    rendered = {
        "human_review_packet_zh.md": render_packet(rows),
        "human_adjudication_zh.csv": render_csv(rows),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (output_dir / name).write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir or repo_root / M1D_RELATIVE
    write_outputs(repo_root, output_dir)
    print(json.dumps({"rows": 33, "output_dir": str(output_dir)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
