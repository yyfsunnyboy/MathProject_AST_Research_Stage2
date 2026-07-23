from __future__ import annotations

import json
import re
from collections import Counter

from scripts import build_candidate_b_r003_198cell_taxonomy_report as report


def test_authority_sha_and_198cell_identity_closure() -> None:
    authorities = report.verify_authorities()
    records, provenance = report.load_normalized_records()
    closure = provenance["closure"]

    assert len(authorities) == len(report.AUTHORITY_HASHES) == 23
    assert all(item["byte_verified"] for item in authorities)
    assert len(records) == 198
    assert closure == {
        "formal_population": 198,
        "previously_frozen": 177,
        "final_batch05": 21,
        "reconciliation": "198=177+21",
        "unique_program_id": 198,
        "unique_cell_identity": 198,
        "unique_source_sha256": 155,
        "duplicate_programs": 0,
        "duplicate_cells": 0,
        "omissions": 0,
        "overlap_frozen177_batch05": 0,
        "remaining": 0,
        "authority_files_verified": 23,
        "batch_cells": {
            "legacy_g2_module_27": 27,
            "legacy_module_exception_37": 37,
            "legacy_multiple_signal_13": 13,
            "legacy_output_contract_shape_20": 20,
            "batch01": 20,
            "batch02": 20,
            "batch03": 20,
            "batch04": 20,
            "final_batch05": 21,
        },
    }
    assert len({row["task_id"] for row in records}) == 50
    assert all(row["condition"] == "Candidate_B/H0" for row in records)
    assert all(row["benchmark"] == "MBPP+" for row in records)


def test_distributions_are_rebuilt_from_frozen_records() -> None:
    records, _ = report.load_normalized_records()
    summary = report.build_summary()
    distributions = summary["distributions"]

    assert Counter(row["primary"] for row in records) == {
        key: value["n"]
        for key, value in distributions["primary"].items()
        if value["n"]
    }
    assert Counter(
        tag for row in records for tag in row["mechanisms"]
    ) == {
        key: value["n"] for key, value in distributions["mechanisms"].items()
    }
    assert {key: value["n"] for key, value in distributions["primary"].items()} == {
        "L0": 0,
        "L1": 0,
        "L2": 7,
        "L3": 0,
        "L4": 70,
        "L5": 54,
        "UNRESOLVED": 67,
    }
    assert distributions["secondary"]["empty"]["n"] == 154
    assert {
        key: value["n"] for key, value in distributions["secondary"]["layers"].items()
    } == {"L4": 2, "L5": 42}
    assert {key: value["n"] for key, value in distributions["confidence"].items()} == {
        "HIGH": 126,
        "LOW": 67,
        "MEDIUM": 5,
    }
    assert distributions["outcome_validity"]["VALID_MODEL_OUTCOME"]["n"] == 198
    assert {
        key: value["n"] for key, value in distributions["healer"].items()
    } == {"abstain": 175, "conditional": 23, "eligible": 0}
    assert summary["key_counts"] == {
        "algorithm_reconstruction_required": 31,
        "truncation": 0,
        "entry_point": 0,
        "import_or_dependency": 0,
        "syntax_or_extraction": 0,
        "runtime_or_assembly": 80,
        "semantic_or_algorithm": 109,
    }
    assert distributions["failure_chain"]["nonempty"] == {
        "n": 198,
        "percent": 100.0,
    }


def test_cross_analysis_denominators_percentages_and_na_groups() -> None:
    summary = report.build_summary()
    cross = summary["cross_analysis"]

    assert cross["benchmark_by_primary"]["MBPP+"]["denominator"] == 198
    assert cross["benchmark_by_primary"]["HumanEval+"]["denominator"] == 0
    assert all(
        cell["percent"] is None
        for cell in cross["benchmark_by_primary"]["HumanEval+"]["values"].values()
    )
    assert cross["condition_by_healer"]["Candidate_B/H0"]["denominator"] == 198
    assert cross["condition_by_healer"]["Candidate_B/H1"]["denominator"] == 0
    assert cross["layer_by_healer"]["L4"]["values"]["conditional"] == {
        "n": 23,
        "percent": 32.9,
    }
    assert cross["layer_by_healer"]["L5"]["values"]["abstain"] == {
        "n": 54,
        "percent": 100.0,
    }
    assert cross["scaffold_like"]["status"] == "NA"
    assert cross["scaffold_like"]["denominator"] == 0


def test_mechanisms_and_representative_cases_preserve_frozen_decisions() -> None:
    summary = report.build_summary()
    mechanisms = summary["distributions"]["mechanisms"]
    cases = summary["representative_cases"]

    assert mechanisms["algorithm_reconstruction_required"] == {
        "n": 31,
        "percent": 15.7,
    }
    assert len(cases["eligible"]) == 0
    assert len(cases["conditional"]) == 3
    assert len(cases["abstain"]) == 3
    assert len(cases["algorithm_reconstruction_required"]) == 3
    assert len(cases["unresolved"]) == 3
    assert all(case["healer"] == "conditional" for case in cases["conditional"])
    assert all(case["primary"] == "UNRESOLVED" for case in cases["unresolved"])


def test_report_sections_numbers_and_interpretation_guards() -> None:
    summary = report.build_summary()
    markdown = report.render_report(summary)

    for heading in (
        "## 一、研究摘要",
        "## 二、資料與實驗單位",
        "## 三、分類方法",
        "## 四、198格完整統計",
        "## 五、交叉分析",
        "## 六、可修與不可修邊界",
        "## 七、Scaffold與Healer的研究發現",
        "## 八、UNRESOLVED的意義",
        "## 九、研究限制",
        "## 十、可直接用於成果報告的結論",
        "## 十一、後續實驗（僅提出，不執行）",
        "## 十二、證據治理附錄",
    ):
        assert heading in markdown
    for fragment in (
        "L5為54格（27.3%）",
        "UNRESOLVED為67格（33.8%）",
        "Healer eligible=0、conditional=23、abstain=175",
        "`algorithm_reconstruction_required`出現31格",
        "| `HumanEval+`（N=0） | NA |",
        "| `Candidate_B/H1`（N=0） | NA |",
        "正式 frozen records 中沒有 scaffold-like 欄位",
        "不能直接解釋成Healer失敗率",
        "不外推至所有LLM",
        f"最終狀態：`{report.VERDICT}`",
    ):
        assert fragment in markdown
    assert all(
        re.fullmatch(r"\d+\.\d%", token)
        for token in re.findall(r"\d+(?:\.\d+)?%", markdown)
    )


def test_deterministic_rebuild_matches_files_and_zero_execution() -> None:
    before = {path: report._file_sha(path) for path in report.AUTHORITY_HASHES}
    first = report.build_outputs()
    second = report.build_outputs()
    after = {path: report._file_sha(path) for path in report.AUTHORITY_HASHES}

    assert first == second
    assert before == after
    for relative, data in first.items():
        assert report._path(relative).read_bytes() == data

    summary = json.loads(first[report.SUMMARY_PATH])
    assert set(summary["execution_counts"].values()) == {0}
    assert summary["verdict"] == "READY_FOR_198CELL_REPORT_INDEPENDENT_AUDIT"
