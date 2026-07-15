import ast
import csv
import json
from pathlib import Path

from exp1_benchmark.fail_to_fail_forensics import (
    FORENSIC_INPUT_COLUMNS,
    OBJECTIVE_COLUMNS,
    PairKey,
    ast_signature,
    build_artifact_index,
    build_qwen8b_forensic_input_rows,
    classify_failure_stage,
    find_artifact,
    index_rows,
    normalize_sample_idx,
    normalize_task_id,
    objective_fields,
    parse_bool,
    resolve_columns,
    select_fail_to_fail,
    select_qwen8b_complete_cases,
    split_official_error,
    write_qwen8b_forensic_input,
)


def test_task_id_conversion():
    assert normalize_task_id("HumanEval_12__s0.py") == "HumanEval/12"
    assert normalize_task_id("Mbpp_101__s3.py") == "Mbpp/101"
    assert normalize_task_id("humaneval/7") == "HumanEval/7"


def test_sample_idx_normalization():
    assert normalize_sample_idx("s12") == 12
    assert normalize_sample_idx(3.0) == 3
    assert normalize_sample_idx("") == 0


def test_fail_to_fail_filter_uses_ab2g_and_ab3_only():
    rows = [
        {"task_id": "HumanEval/1", "model": "m", "strategy": "Ab2g", "sample_idx": "0", "passed": "False"},
        {"task_id": "HumanEval/1", "model": "m", "strategy": "Ab3", "sample_idx": "0", "passed": "False"},
        {"task_id": "HumanEval/2", "model": "m", "strategy": "Ab2g", "sample_idx": "0", "passed": "False"},
        {"task_id": "HumanEval/2", "model": "m", "strategy": "Ab3", "sample_idx": "0", "passed": "True"},
    ]
    headers = rows[0].keys()
    columns = resolve_columns(headers)
    selected = select_fail_to_fail(index_rows(rows, columns, "humaneval"), columns)
    assert [(key.task_id, parse_bool(raw[0]["passed"]), parse_bool(healed[0]["passed"])) for key, raw, healed in selected] == [
        ("HumanEval/1", False, False)
    ]


def test_duplicate_rows_are_selected_as_ambiguous_candidates():
    rows = [
        {"task_id": "HumanEval/1", "model": "m", "strategy": "Ab2g", "sample_idx": "0", "passed": "False"},
        {"task_id": "HumanEval/1", "model": "m", "strategy": "Ab2g", "sample_idx": "0", "passed": "False"},
        {"task_id": "HumanEval/1", "model": "m", "strategy": "Ab3", "sample_idx": "0", "passed": "False"},
    ]
    columns = resolve_columns(rows[0].keys())
    selected = select_fail_to_fail(index_rows(rows, columns, "humaneval"), columns)
    assert len(selected) == 1
    assert len(selected[0][1]) == 2


def test_missing_artifact_is_not_guessed(tmp_path):
    index = build_artifact_index(tmp_path / "raw_outputs")
    status, path = find_artifact(index, PairKey("humaneval", "m", "HumanEval/1", 0))
    assert status == "missing"
    assert path is None


def test_duplicate_artifact_is_ambiguous(tmp_path):
    first = tmp_path / "raw_outputs" / "humaneval" / "m" / "Ab2g" / "HumanEval_1__s0.py"
    second = tmp_path / "raw_outputs" / "humaneval" / "m" / "copy" / "HumanEval_1__s0.py"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("def f():\n    return 1\n", encoding="utf-8")
    second.write_text("def f():\n    return 2\n", encoding="utf-8")
    index = build_artifact_index(tmp_path / "raw_outputs")
    status, path = find_artifact(index, PairKey("humaneval", "m", "HumanEval/1", 0))
    assert status == "ambiguous"
    assert path is None


def test_ast_parse_failure_is_reported():
    signature, error = ast_signature("def broken(:\n")
    assert signature == ""
    assert error.startswith("SyntaxError:")
    ok_signature, ok_error = ast_signature("def ok():\n    return 1\n")
    assert ok_error is None
    assert ok_signature == ast.dump(ast.parse("def ok():\n    return 1\n"), annotate_fields=True, include_attributes=False)


def test_csv_header_resolution_does_not_require_column_order(tmp_path):
    path = tmp_path / "table.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["passed", "sample_idx", "strategy", "model", "task_id"])
        writer.writeheader()
        writer.writerow({"task_id": "Mbpp/1", "model": "m", "strategy": "Ab2g", "sample_idx": 0, "passed": False})
    assert resolve_columns(["passed", "sample_idx", "strategy", "model", "task_id"])["task_id"] == "task_id"


def test_split_official_error_and_failure_stage():
    assert split_official_error("fail: base=pass,plus=fail") == ("fail", "base=pass,plus=fail")
    assert classify_failure_stage("fail: base=pass,plus=fail") == "plus"
    assert classify_failure_stage("fail: base=fail,plus=fail") == "base+plus"
    assert classify_failure_stage("fail: base=fail,plus=pass") == "base"
    assert classify_failure_stage("worker_error: entry_point 'x' 實際 0 次") == "worker"
    assert split_official_error("worker_error: entry_point boom")[0] == "worker_error"


def test_objective_fields_are_mechanical_only():
    fields = objective_fields(
        {
            "raw_error": "fail: base=fail,plus=fail",
            "healed_error": "worker_error: entry_point missing",
            "healer_triggered": "true",
            "rules_triggered": "ast;antidup",
            "code_changed": "true",
            "rollback": "",
        }
    )
    assert fields == {
        "raw_failure_stage": "base+plus",
        "healed_failure_stage": "worker",
        "raw_error_type": "fail",
        "healed_error_type": "worker_error",
        "healer_triggered": "true",
        "rules_triggered": "ast;antidup",
        "code_changed": "true",
        "rollback": "false",
    }
    assert set(fields) == set(OBJECTIVE_COLUMNS)
    assert "eligibility" not in fields
    assert "root_cause" not in fields


def test_qwen8b_forensic_input_filters_complete_qwen_only(tmp_path):
    records = [
        {
            "case_id": "qwen8b_humaneval_HumanEval_1__s0",
            "dataset": "humaneval",
            "task_id": "HumanEval/1",
            "sample_idx": 0,
            "model": "qwen3-8b",
            "raw_pass": False,
            "healed_pass": False,
            "raw_error": "fail: base=fail,plus=fail",
            "healed_error": "fail: base=pass,plus=fail",
            "raw_path": "raw.py",
            "healed_path": "healed.py",
            "normalized_diff_path": "",
            "pairing_status": "complete",
            "healer_triggered": "false",
            "rules_triggered": "",
            "code_changed": "false",
            "rollback": "",
        },
        {
            "case_id": "qwen8b_mbpp_Mbpp_2__s0",
            "dataset": "mbpp",
            "task_id": "Mbpp/2",
            "sample_idx": 0,
            "model": "qwen3-8b",
            "raw_pass": False,
            "healed_pass": False,
            "raw_error": "fail: base=fail,plus=fail",
            "healed_error": "fail: base=fail,plus=fail",
            "raw_path": "raw2.py",
            "healed_path": "healed2.py",
            "normalized_diff_path": "diff.txt",
            "pairing_status": "missing",
            "healer_triggered": "true",
            "rules_triggered": "ast",
            "code_changed": "true",
            "rollback": "",
        },
        {
            "case_id": "gemini_humaneval_HumanEval_3__s0",
            "dataset": "humaneval",
            "task_id": "HumanEval/3",
            "sample_idx": 0,
            "model": "google_gemini",
            "raw_pass": False,
            "healed_pass": False,
            "raw_error": "fail: base=fail,plus=fail",
            "healed_error": "fail: base=fail,plus=fail",
            "raw_path": "g.py",
            "healed_path": "gh.py",
            "normalized_diff_path": "",
            "pairing_status": "complete",
            "healer_triggered": "true",
            "rules_triggered": "ast",
            "code_changed": "false",
            "rollback": "",
        },
    ]
    selected = select_qwen8b_complete_cases(records)
    assert [row["case_id"] for row in selected] == ["qwen8b_humaneval_HumanEval_1__s0"]
    rows = build_qwen8b_forensic_input_rows(records)
    assert len(rows) == 1
    assert rows[0]["raw_failure_stage"] == "base+plus"
    assert rows[0]["healed_failure_stage"] == "plus"
    assert rows[0]["rollback"] == "false"
    for forbidden in ("eligibility", "root_cause", "why_fail_to_fail", "failure_layer", "recommended_action"):
        assert forbidden not in rows[0]

    manifest = tmp_path / "pairing_manifest.jsonl"
    output = tmp_path / "qwen8b_forensic_input.csv"
    with manifest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = write_qwen8b_forensic_input(manifest, output)
    assert summary["total"] == 1
    assert summary["humaneval"] == 1
    assert summary["mbpp"] == 0
    with output.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == FORENSIC_INPUT_COLUMNS
        written = list(reader)
    assert len(written) == 1
    assert written[0]["case_id"] == "qwen8b_humaneval_HumanEval_1__s0"
    assert written[0]["raw_error_type"] == "fail"
    assert written[0]["healed_error_type"] == "fail"
