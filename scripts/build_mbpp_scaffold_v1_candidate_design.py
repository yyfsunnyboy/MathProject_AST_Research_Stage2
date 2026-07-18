#!/usr/bin/env python3
"""Build deterministic Milestone 2C Scaffold v1 candidate-design evidence."""

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

from scripts import build_mbpp_scaffold_v0_paired_analysis as paired_v0  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/pbd/mbpp_sv0/r002/milestone_2c_v1_candidate_design"
)
M2B_RELATIVE = paired_v0.OUTPUT_RELATIVE
SCAFFOLD_V0_RELATIVE = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0.txt")
P0_RELATIVE = paired_v0.P0_RELATIVE
P1_RELATIVE = paired_v0.P1_RELATIVE

EXPECTED_SOURCE_HASHES = {
    "milestone_2b/paired_analysis_manifest.json": "28bbb8fabbd1cbcfafe7e49f4defd6dc62dc526081c4a2d39e4197478685cbc9",
    "milestone_2b/paired_cell_comparison.csv": "78bc6e7c67bb5010f45f65e6655b76778117f28c261a02470ef0bff2e5e18ea6",
    "scaffold_v0.txt": "31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305",
}

SOURCE_PATHS = {
    "milestone_2b/paired_analysis_manifest.json": M2B_RELATIVE
    / "paired_analysis_manifest.json",
    "milestone_2b/paired_cell_comparison.csv": M2B_RELATIVE
    / "paired_cell_comparison.csv",
    "scaffold_v0.txt": SCAFFOLD_V0_RELATIVE,
}

CELL_FIELDS = (
    "evidence_group",
    "task_id",
    "seed",
    "p0_generation_id",
    "p1_generation_id",
    "p0_observed_status",
    "p1_observed_status",
    "p0_pipeline_status",
    "p1_pipeline_status",
    "pipeline_transition",
    "p0_strict_python_only_compliant",
    "p1_strict_python_only_compliant",
    "p0_code_fence_marker_count",
    "p1_code_fence_marker_count",
    "p0_extra_text_outside_fences",
    "p1_extra_text_outside_fences",
    "p0_multiple_program_segments",
    "p1_multiple_program_segments",
    "p0_generation_truncated",
    "p1_generation_truncated",
    "p0_raw_compile_status",
    "p1_raw_compile_status",
    "p0_pipeline_compile_status",
    "p1_pipeline_compile_status",
    "p0_pipeline_entry_point_status",
    "p1_pipeline_entry_point_status",
    "p0_extraction_action",
    "p1_extraction_action",
    "p0_reasoning_leakage",
    "p1_reasoning_leakage",
    "p0_failure_taxonomy",
    "p1_failure_taxonomy",
    "p0_raw_characters",
    "p1_raw_characters",
    "p0_raw_lines",
    "p1_raw_lines",
    "p0_pipeline_top_level_defs",
    "p1_pipeline_top_level_defs",
    "observable_output_structure_difference",
    "cell_adjudication",
    "direct_evidence",
    "confidence",
    "causal_status",
    "remaining_problem_bucket",
)

INSTRUCTION_FIELDS = (
    "instruction_number",
    "v0_instruction_exact_text",
    "direct_effectiveness_evidence",
    "evidence_strength",
    "possible_overconstraint",
    "causal_status",
    "recommended_action",
    "candidate_rewrite",
)

CANDIDATES = [
    {
        "candidate_id": "v1_candidate_a_conservative_compaction",
        "exact_text_utf8": (
            "Return exactly one complete, executable Python source file.\n"
            "Use the exact function name and parameters required by the task, and include required imports.\n"
            "Do not use Markdown code fences or explanatory text.\n"
            "Output only Python code.\n"
        ),
        "design_rationale": (
            "Preserve the directly supported format and entry-point constraints while removing "
            "redundant, potentially distracting prohibitions."
        ),
        "changes_from_v0": [
            "Compacts seven lines to four.",
            "Merges duplicate source-only and entry-point wording.",
            "Removes explicit bans on assertions, tests, print statements, example calls, and alternatives.",
        ],
        "expected_improvement": (
            "Retain plain executable Python delivery while reducing prompt load and possible interference "
            "with semantic solution generation."
        ),
        "regression_risk": (
            "The shorter wording may allow test/example code or public-function redefinition to reappear."
        ),
        "supported_by_current_development_evidence": "partially; format retention is directly supported, semantic benefit is only an inference",
        "changes_prompt_composition": False,
        "prompt_composition_note": "Keep official prompt + fixed separator + appended candidate scaffold.",
        "recommended": True,
    },
    {
        "candidate_id": "v1_candidate_b_minimal_output_contract",
        "exact_text_utf8": (
            "Return one complete executable Python source file implementing the requested function.\n"
            "Use no Markdown fences or explanatory text; output only Python code.\n"
        ),
        "design_rationale": "Test whether the strongest format evidence can be retained with minimal instruction load.",
        "changes_from_v0": [
            "Reduces seven lines to two.",
            "Drops explicit parameter, import, test, print, and redefinition rules.",
        ],
        "expected_improvement": "Lowest instruction burden among candidates.",
        "regression_risk": "Higher risk of missing imports, wrong signature, or extra executable examples.",
        "supported_by_current_development_evidence": "partially; format rules are supported but removal risks are not estimated",
        "changes_prompt_composition": False,
        "prompt_composition_note": "Keep official prompt + fixed separator + appended candidate scaffold.",
        "recommended": False,
    },
    {
        "candidate_id": "v1_candidate_c_signature_emphasis",
        "exact_text_utf8": (
            "Output only one complete executable Python source file, without Markdown fences or explanations.\n"
            "Implement the requested public function exactly once with the required name and parameter list.\n"
            "Include all imports required by the implementation.\n"
        ),
        "design_rationale": "Retain stronger signature protection while shortening the source-only contract.",
        "changes_from_v0": [
            "Reduces seven lines to three.",
            "Retains exact signature, single-definition, import, no-fence, and no-explanation intent.",
            "Drops explicit bans on assertions, tests, prints, examples, and alternatives.",
        ],
        "expected_improvement": "May preserve the observed entry-point improvement with less redundancy.",
        "regression_risk": "The phrase 'exactly once' may still overconstrain legitimate helper patterns or model attention.",
        "supported_by_current_development_evidence": "partially; entry-point improvement is observed but line-level causality is not identified",
        "changes_prompt_composition": False,
        "prompt_composition_note": "Keep official prompt + fixed separator + appended candidate scaffold.",
        "recommended": False,
    },
]


class CandidateDesignError(RuntimeError):
    """Raised before writes when evidence identity or deterministic output drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateDesignError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _index(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in result, f"{label}: duplicate pair {key}")
        result[key] = row
    return result


def _taxonomy_index(rows: list[dict[str, str]]) -> dict[tuple[str, int], str]:
    return {
        (row["task_id"], int(row["seed"])): row["failure_category"] for row in rows
    }


def _top_level_defs(source: str | None) -> str:
    if not source:
        return ""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, OverflowError):
        return "compile_failed"
    names = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return "|".join(names)


def _structure_difference(row: dict[str, str], raw0: str, raw1: str) -> str:
    changes: list[str] = []
    comparisons = (
        ("code_fence_markers", "p0_code_fence_marker_count", "p1_code_fence_marker_count"),
        ("extra_text", "p0_extra_text_outside_fences", "p1_extra_text_outside_fences"),
        ("multiple_programs", "p0_multiple_program_segments", "p1_multiple_program_segments"),
        ("truncation", "p0_generation_truncated", "p1_generation_truncated"),
        ("raw_compile", "p0_raw_compile_status", "p1_raw_compile_status"),
        ("pipeline_entry", "p0_pipeline_entry_point_status", "p1_pipeline_entry_point_status"),
        ("extraction", "p0_extraction_action", "p1_extraction_action"),
        ("reasoning_leakage", "p0_reasoning_leakage", "p1_reasoning_leakage"),
    )
    for label, left, right in comparisons:
        if row[left] != row[right]:
            changes.append(f"{label}:{row[left]}->{row[right]}")
    changes.extend(
        [
            f"raw_chars:{len(raw0)}->{len(raw1)}",
            f"raw_lines:{len(raw0.splitlines())}->{len(raw1.splitlines())}",
        ]
    )
    return "; ".join(changes)


def _remaining_bucket(p1_category: str) -> str:
    if p1_category == "pipeline_pass":
        return "none_pipeline_pass"
    if p1_category == "missing_or_wrong_entry_point":
        return "suitable_for_scaffold"
    if p1_category == "syntax_failure":
        return "possibly_evaluator_blind_healer"
    if p1_category in {
        "functional_test_failure",
        "runtime_exception",
        "import_or_name_failure",
        "timeout_or_resource_failure",
    }:
        return "requires_oracle_or_semantic_information"
    return "insufficient_evidence"


def _adjudicate(
    row: dict[str, str],
    p0_category: str,
    regressions_by_task: Counter[str],
    rescues_by_task: Counter[str],
) -> tuple[str, str, str, str]:
    transition = row["pipeline_transition"]
    structural = (
        f"P0/P1 pipeline compile={row['p0_pipeline_compile_status']}/"
        f"{row['p1_pipeline_compile_status']}; entry="
        f"{row['p0_pipeline_entry_point_status']}/{row['p1_pipeline_entry_point_status']}; "
        f"extraction={row['p0_extraction_action']}/{row['p1_extraction_action']}; "
        f"raw hashes differ={row['p0_raw_response_sha256'] != row['p1_raw_response_sha256']}"
    )
    if transition == "pass_to_fail":
        task_id = row["task_id"]
        if regressions_by_task[task_id] >= 2 and rescues_by_task[task_id] == 0:
            return (
                "scaffold_plausibly_related",
                f"{structural}; this task has {regressions_by_task[task_id]}/5 regressions and no rescues. "
                "Repeated direction is direct paired evidence, but scaffold causality is an inference.",
                "low",
                "inference_not_causal_identification",
            )
        return (
            "model_sampling_variation",
            f"{structural}; this task has regressions={regressions_by_task[task_id]} and "
            f"rescues={rescues_by_task[task_id]}, so the within-task direction is mixed or isolated. "
            "Sampling attribution is a low-confidence inference.",
            "low",
            "inference_not_causal_identification",
        )
    if transition == "fail_to_pass":
        if p0_category == "extraction_or_format_failure":
            return (
                "format_compliance_rescue",
                f"{structural}; P0 taxonomy=extraction_or_format_failure and P1 pipeline passed.",
                "high",
                "direct_mechanistic_evidence_for_evaluability_not_semantic_causality",
            )
        if p0_category in {"syntax_failure", "missing_or_wrong_entry_point"}:
            return (
                "compile_or_entry_improvement",
                f"{structural}; P0 taxonomy={p0_category} and P1 pipeline passed.",
                "high",
                "direct_mechanistic_evidence_for_evaluability_not_semantic_causality",
            )
        return (
            "insufficient_evidence",
            f"{structural}; P0 taxonomy=unknown and saved evaluator diagnostics do not identify why P1 passed.",
            "low",
            "not_identified",
        )
    return (
        "not_applicable",
        f"{structural}; no discordant pipeline transition.",
        "not_applicable",
        "descriptive_only",
    )


def _render_csv(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _render_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _instruction_rows() -> list[dict[str, str]]:
    v0_lines = CANDIDATE_V0_LINES
    values = [
        (
            "One-file delivery is consistent with multiple fenced programs falling 25->0, but line-specific causality is not isolated.",
            "moderate_aggregate_not_line_specific",
            "May be redundant with output-only wording.",
            "inference",
            "shorten_and_merge",
            "Return exactly one complete, executable Python source file.",
        ),
        (
            "Code-fence markers fell 96->0 and P1 extraction was plain-text pass-through in 100/100 cells.",
            "strong_direct_aggregate",
            "Low; this is the clearest supported constraint.",
            "descriptive_association_with_strong_mechanistic_fit",
            "retain_verbatim_or_near_verbatim",
            "Do not use Markdown code fences.",
        ),
        (
            "Extra fence-outside text fell 79->0 and multiple programs fell 25->0; the bundled list prevents line-level attribution.",
            "strong_for_no_explanation_weak_for_each_other_ban",
            "High: banning assertions/tests/prints/examples may compete with task prompts containing assertions and is not separately supported.",
            "part_direct_part_inference",
            "shorten",
            "Do not include explanatory text.",
        ),
        (
            "Pipeline missing-entry failures fell 17->3, but Pipeline correctness stayed 30/100 and line-specific causality is not isolated.",
            "moderate_aggregate",
            "Low to moderate; exact parameter wording may distract when the prompt is ambiguous.",
            "inference",
            "retain_and_shorten",
            "Use the exact function name and parameters required by the task.",
        ),
        (
            "No saved import/name failure was identified in either census; unknown failures cannot be recoded as import failures.",
            "insufficient",
            "Low, but benefit is unobserved.",
            "not_identified",
            "retain_briefly",
            "Include required imports.",
        ),
        (
            "Missing-entry failures fell 17->3, but this line duplicates instruction 4 and redefinition-specific evidence is absent.",
            "weak_redundant",
            "Moderate due redundancy and attention cost.",
            "inference",
            "delete_or_merge_with_4",
            "",
        ),
        (
            "Extra text fell 79->0 and raw compile pass rose 0->94; effect overlaps instructions 1-3.",
            "strong_aggregate_not_line_specific",
            "Moderate due redundancy.",
            "descriptive_association_line_causality_not_identified",
            "shorten_and_merge",
            "Output only Python code.",
        ),
    ]
    return [
        {
            "instruction_number": str(index),
            "v0_instruction_exact_text": line,
            "direct_effectiveness_evidence": value[0],
            "evidence_strength": value[1],
            "possible_overconstraint": value[2],
            "causal_status": value[3],
            "recommended_action": value[4],
            "candidate_rewrite": value[5],
        }
        for index, (line, value) in enumerate(zip(v0_lines, values), start=1)
    ]


CANDIDATE_V0_LINES = [
    "Return exactly one complete Python source file.",
    "Do not use Markdown code fences.",
    "Do not include explanations, analysis, assertions, tests, print statements, example calls, or alternative implementations.",
    "Implement the exact function name and parameter list required by the task.",
    "Include every import required by the submitted program.",
    "Do not rename or redefine the requested public function.",
    "The response must begin with Python code and contain no text outside the source file.",
]


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_hashes = {
        label: _sha256((repo_root / path).read_bytes()) for label, path in SOURCE_PATHS.items()
    }
    _require(source_hashes == EXPECTED_SOURCE_HASHES, "Milestone 2C source artifact hash mismatch")
    _require(
        (repo_root / SCAFFOLD_V0_RELATIVE).read_text(encoding="utf-8").splitlines()
        == CANDIDATE_V0_LINES,
        "Scaffold v0 exact text mismatch",
    )

    base = paired_v0.build_analysis(repo_root)
    _require(
        base["transition_counts"]["pipeline"]
        == {
            "fail_to_fail": 53,
            "fail_to_pass": 17,
            "pass_to_fail": 17,
            "pass_to_pass": 13,
        },
        "Milestone 2B transition count mismatch",
    )
    _require(len(base["paired_rows"]) == 100, "paired row count mismatch")
    keys = {(row["task_id"], int(row["seed"])) for row in base["paired_rows"]}
    _require(len(keys) == 100, "duplicate task_id + seed identity")

    p0_raw = _index(_read_jsonl(repo_root / P0_RELATIVE / "raw_generations.jsonl"), "P0 raw")
    p1_raw = _index(_read_jsonl(repo_root / P1_RELATIVE / "raw_generations.jsonl"), "P1 raw")
    p0_pipe = _index(
        _read_jsonl(repo_root / P0_RELATIVE / "pipeline_corrected.jsonl"), "P0 pipeline"
    )
    p1_pipe = _index(
        _read_jsonl(repo_root / P1_RELATIVE / "pipeline_corrected.jsonl"), "P1 pipeline"
    )
    _require(set(p0_raw) == set(p1_raw) == set(p0_pipe) == set(p1_pipe) == keys, "paired identity mismatch")

    p0_taxonomy = _taxonomy_index(
        _read_csv(repo_root / P0_RELATIVE / "milestone_1c_failure_census/failure_census.csv")
    )
    p1_taxonomy = _taxonomy_index(base["p1_census_rows"])
    regressions_by_task = Counter(
        row["task_id"] for row in base["paired_rows"] if row["pipeline_transition"] == "pass_to_fail"
    )
    rescues_by_task = Counter(
        row["task_id"] for row in base["paired_rows"] if row["pipeline_transition"] == "fail_to_pass"
    )
    groups = {
        "fail_to_pass": "p1_paired_rescue",
        "pass_to_fail": "p1_paired_regression",
        "pass_to_pass": "common_pass",
        "fail_to_fail": "persistent_failure",
    }
    rows: list[dict[str, str]] = []
    for base_row in base["paired_rows"]:
        key = (base_row["task_id"], int(base_row["seed"]))
        raw0, raw1 = p0_raw[key]["raw_response"], p1_raw[key]["raw_response"]
        category0 = p0_taxonomy.get(key, "pipeline_pass")
        category1 = p1_taxonomy.get(key, "pipeline_pass")
        adjudication, evidence, confidence, causal_status = _adjudicate(
            base_row, category0, regressions_by_task, rescues_by_task
        )
        extra = {
            "evidence_group": groups[base_row["pipeline_transition"]],
            "p0_failure_taxonomy": category0,
            "p1_failure_taxonomy": category1,
            "p0_raw_characters": str(len(raw0)),
            "p1_raw_characters": str(len(raw1)),
            "p0_raw_lines": str(len(raw0.splitlines())),
            "p1_raw_lines": str(len(raw1.splitlines())),
            "p0_pipeline_top_level_defs": _top_level_defs(
                p0_pipe[key]["pipeline_corrected_output"]
            ),
            "p1_pipeline_top_level_defs": _top_level_defs(
                p1_pipe[key]["pipeline_corrected_output"]
            ),
            "observable_output_structure_difference": _structure_difference(
                base_row, raw0, raw1
            ),
            "cell_adjudication": adjudication,
            "direct_evidence": evidence,
            "confidence": confidence,
            "causal_status": causal_status,
            "remaining_problem_bucket": _remaining_bucket(category1),
        }
        rows.append({field: extra.get(field, base_row.get(field, "")) for field in CELL_FIELDS})

    group_counts = Counter(row["evidence_group"] for row in rows)
    _require(
        group_counts
        == {
            "p1_paired_rescue": 17,
            "p1_paired_regression": 17,
            "common_pass": 13,
            "persistent_failure": 53,
        },
        "evidence group counts mismatch",
    )
    rescue_counts = Counter(
        row["cell_adjudication"] for row in rows if row["evidence_group"] == "p1_paired_rescue"
    )
    regression_counts = Counter(
        row["cell_adjudication"]
        for row in rows
        if row["evidence_group"] == "p1_paired_regression"
    )
    _require(
        rescue_counts
        == {
            "format_compliance_rescue": 5,
            "compile_or_entry_improvement": 7,
            "insufficient_evidence": 5,
        },
        "rescue adjudication mismatch",
    )
    _require(sum(regression_counts.values()) == 17, "regression adjudication mismatch")
    return {
        "source_hashes": source_hashes,
        "paired_v0_source_hashes": base["source_hashes"],
        "cell_rows": rows,
        "instruction_rows": _instruction_rows(),
        "group_counts": dict(sorted(group_counts.items())),
        "rescue_adjudication_counts": dict(sorted(rescue_counts.items())),
        "regression_adjudication_counts": dict(sorted(regression_counts.items())),
        "remaining_problem_counts": dict(
            sorted(Counter(row["remaining_problem_bucket"] for row in rows).items())
        ),
        "format_summary": base["format_summary"],
    }


def _render_report(result: dict[str, Any]) -> bytes:
    regression = result["regression_adjudication_counts"]
    rescue = result["rescue_adjudication_counts"]
    lines = [
        "# MBPP+ Scaffold v1 候選設計與錯誤歸因分析（Milestone 2C）",
        "",
        "## 範圍與證據界線",
        "",
        "本輪只重讀既有 P0、P1 與 Milestone 2B development artifacts；沒有模型呼叫、程式生成、EvalPlus 重跑、Healer 建置或執行，也沒有讀取 validation、confirmatory 或 sealed reserve。Pipeline correction 不是 Healer。本報告是候選設計與探索性證據整理，不是 Scaffold v1 有效性的證明。",
        "",
        "100 組 `task_id + seed` 身分已重新驗證：無重複、無缺漏；四組為 rescue 17、regression 17、common pass 13、persistent failure 53，與 Milestone 2B 一致。",
        "",
        "## 六個直接回答",
        "",
        "1. **v0 確定解決了什麼？** 它確定改善直接可評估性：code fences 96→0、fence 外文字 79→0、多段程式 25→0、extraction failure 21→0、raw compile pass 0→94；missing entry-point failures 17→3 是強關聯但不能拆解到單一指令。它沒有改善 Pipeline-corrected 總正確率（30/100→30/100）。",
        f"2. **17 個 Pipeline regressions 能否歸因於 Scaffold？** 不能。逐格分類為 `{json.dumps(regression, ensure_ascii=False, sort_keys=True)}`；其中 repeated within-task direction 只支持低信心的 `scaffold_plausibly_related` 推論，沒有因果識別；方向混合／孤立者只作低信心 sampling variation 推論。",
        "3. **v1 最需要處理什麼？** 保留已證實的純 Python／無 fence／正確 entry-point 輸出契約，同時縮短重複與未被單獨支持的禁令，降低對語意解題的注意力干擾風險。",
        "4. **哪些問題不應交給 Scaffold？** unknown evaluator failures、需要 assertion／oracle 才能辨識的功能錯誤、runtime 語意與資源行為不應由 Scaffold 猜修。",
        "5. **現在是否足以凍結 v1？** 不足：尚不凍結，只保留候選。現有 20 題是 pilot，Pipeline 淨增益為 0，且 line-level 與 semantic causality 未識別。",
        "6. **下一輪先凍結 v1 還是先擴充 development？** 先預註冊 development expansion 與候選比較規則，再從 historical development pool 新增 40 題形成 60 題；本輪不選題、不讀題、不建 split。取得更廣 development evidence 後再決定凍結哪個 v1。validation／confirmatory／sealed reserve 維持封存。",
        "",
        "## Rescue 與 regression 歸因",
        "",
        f"17 個 rescues：`{json.dumps(rescue, ensure_ascii=False, sort_keys=True)}`。只有格式或 compile／entry 的可觀察障礙消失時才使用 mechanistic label；5 個 P0 unknown→P1 pass 保持證據不足。任何 rescue 都不是 Healer 效果。",
        "",
        "17 個 regressions 的 P1 輸出皆需依保存的 compile、entry、extraction 與 evaluator 診斷判讀。generic evaluator failure 不被重編為 functional failure；同 task 多 seed 的一致方向只是 scaffold-related plausibility，不是因果證明。逐格直接證據與信心見 `milestone_2c_cell_evidence.csv`。",
        "",
        "## 剩餘問題的治理分流",
        "",
        "- 適合 Scaffold：明確的輸出格式與 requested entry-point 契約。",
        "- 可能適合 evaluator-blind Healer：可由 parser／compiler 直接看見的 syntax defect；仍須另案預註冊且不得使用 evaluator feedback。",
        "- 需要 oracle／語意資訊：已被可靠診斷的功能、runtime、import/name 或資源錯誤；本批 generic unknown 不能擅自放入此類。",
        "- 證據不足：P1 的 generic unknown evaluator failures；不得硬分配給 Healer。",
        "",
        "## v0 指令審查與 v1 候選",
        "",
        "逐條審查見 `scaffold_v0_instruction_review.csv`。最強直接證據支持 no-fence 與 output-only；entry-point 改善是 aggregate association；imports 與禁止 assertions/tests/prints 等沒有各自可識別的直接證據。因 v0 是 bundled treatment，所有 line-level 因果主張均受限。",
        "",
        "最多三個 exact UTF-8 候選見 `scaffold_v1_candidates.json`。推薦最保守的 Candidate A：保留格式、signature、imports 與相同 appended prompt composition，只壓縮重複禁令。這是供下一個獨立、已預註冊 Milestone 評估的候選，不建立 v1 run directory，也不凍結或執行。",
        "",
        "## Development expansion 建議",
        "",
        "把目前 20 題明確標為 pilot。下一輪先預註冊：historical development pool 的資格規則、盲選程序、排除規則、40 題新增數量、固定 seeds、主次指標、paired analysis、停止規則與候選選擇門檻；之後才建立 60 題 development set。不得用 validation、confirmatory 或 sealed reserve 補足題數。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    result = build_analysis(repo_root)
    candidate_payload = {
        "analysis_version": "milestone_2c_scaffold_v1_candidates_v1",
        "candidate_count": len(CANDIDATES),
        "freeze_status": "尚不凍結，只保留候選",
        "recommended_candidate_id": "v1_candidate_a_conservative_compaction",
        "model_calls": 0,
        "evalplus_executions": 0,
        "creates_v1_run_directory": False,
        "candidates": CANDIDATES,
    }
    outputs: dict[Path, bytes] = {
        Path("milestone_2c_cell_evidence.csv"): _render_csv(result["cell_rows"], CELL_FIELDS),
        Path("scaffold_v0_instruction_review.csv"): _render_csv(
            result["instruction_rows"], INSTRUCTION_FIELDS
        ),
        Path("scaffold_v1_candidates.json"): _render_json(candidate_payload),
        Path("scaffold_v1_candidate_design_zh.md"): _render_report(result),
    }
    manifest = {
        "analysis_version": "milestone_2c_scaffold_v1_candidate_design_v1",
        "scope": "existing MBPP+ active development artifacts only",
        "starting_expected_head": "c5731174758e44afb3b2cfda3abc39bb7d13f4ef",
        "p0_run_id": paired_v0.P0_RUN_ID,
        "p1_run_id": paired_v0.P1_RUN_ID,
        "paired_identity": {
            "key": ["task_id", "seed"],
            "cells": 100,
            "duplicates": 0,
            "missing": 0,
        },
        "transition_counts": {
            "fail_to_pass": 17,
            "pass_to_fail": 17,
            "pass_to_pass": 13,
            "fail_to_fail": 53,
        },
        "evidence_group_counts": result["group_counts"],
        "rescue_adjudication_counts": result["rescue_adjudication_counts"],
        "regression_adjudication_counts": result["regression_adjudication_counts"],
        "remaining_problem_counts": result["remaining_problem_counts"],
        "recommended_candidate_id": "v1_candidate_a_conservative_compaction",
        "freeze_status": "尚不凍結，只保留候選",
        "development_expansion": {
            "current_pilot_tasks": 20,
            "future_preregistered_total_tasks": 60,
            "future_historical_development_pool_additions": 40,
            "tasks_selected_this_milestone": 0,
            "split_created_this_milestone": False,
            "validation_confirmatory_sealed_reserve_remain_sealed": True,
        },
        "prohibited_actions_attestation": {
            "model_calls": 0,
            "program_regenerations": 0,
            "evalplus_executions": 0,
            "healer_built_or_executed": False,
            "scaffold_v0_modified": False,
            "scaffold_v1_frozen_or_executed": False,
            "v1_run_directory_created": False,
            "unknown_failures_guessed_as_functional": False,
        },
        "source_artifacts": {
            **{
                label: {"path": SOURCE_PATHS[label].as_posix(), "sha256": digest}
                for label, digest in sorted(result["source_hashes"].items())
            },
            **{
                f"paired_v0/{label}": {
                    "path": paired_v0.SOURCE_PATHS[label].as_posix(),
                    "sha256": digest,
                }
                for label, digest in sorted(result["paired_v0_source_hashes"].items())
            },
        },
        "outputs": {
            path.as_posix(): {"sha256": _sha256(content), "size_bytes": len(content)}
            for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        },
        "builder": "scripts/build_mbpp_scaffold_v1_candidate_design.py",
        "targeted_tests": "tests/finals_rebuild/test_mbpp_scaffold_v1_candidate_design.py",
    }
    outputs[Path("milestone_2c_manifest.json")] = _render_json(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    for relative, content in build_outputs(repo_root).items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing output drift/overwrite: {relative}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_outputs(args.repo_root)
    print(json.dumps({"status": "built", "paired_cells": 100}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
