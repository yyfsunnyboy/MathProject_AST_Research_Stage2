from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import build_mbpp_human_review_packet_zh as packet_zh


REPO_ROOT = Path(__file__).resolve().parents[2]


def _source_evidence():
    census_rows, _ = packet_zh.milestone_1c.build_census(REPO_ROOT)
    _, clusters, _ = packet_zh.milestone_1d.build_packets(REPO_ROOT)
    manual_signatures = {
        row["signature_id"]
        for row in clusters
        if row["proposed_action"] == "manual_review"
    }
    run = REPO_ROOT / packet_zh.RUN_RELATIVE
    plan = json.loads((run / "generation_plan.json").read_text(encoding="utf-8"))
    pipelines = {
        row["generation_id"]: row
        for row in packet_zh._read_jsonl(run / "pipeline_corrected.jsonl")
    }
    tasks = packet_zh._load_active_tasks(REPO_ROOT, plan["task_ids"])
    expected = {}
    for row in census_rows:
        signature = packet_zh.milestone_1d._signature_for_failure(
            row, pipelines[row["cell_id"]], tasks[row["task_id"]]
        )
        if signature in manual_signatures:
            expected[row["cell_id"]] = (row, signature, pipelines[row["cell_id"]], tasks[row["task_id"]])
    return expected


def test_chinese_packet_has_exact_manual_review_scope():
    rows = packet_zh.build_rows(REPO_ROOT)
    expected = _source_evidence()

    assert len(rows) == 33
    assert {row["cell_id"] for row in rows} == set(expected)
    assert Counter(row["failure_category"] for row in rows) == {
        "syntax_failure": 6,
        "missing_or_wrong_entry_point": 1,
        "unknown": 26,
    }


def test_ids_hashes_prompts_and_signatures_match_original_evidence():
    rows = packet_zh.build_rows(REPO_ROOT)
    expected = _source_evidence()

    for row in rows:
        source, signature, pipeline, task = expected[row["cell_id"]]
        assert row["task_id"] == source["task_id"]
        assert row["seed"] == source["seed"]
        assert row["signature_id"] == signature
        assert row["raw_generation_sha256"] == source["raw_generation_sha256"]
        assert row["pipeline_program_sha256"] == source["extracted_program_sha256"]
        assert row["original_prompt_en"] == task["prompt"]
        assert row["code_snippet_original"] in pipeline["pipeline_corrected_output"]


def test_translation_notice_and_human_fields_are_unfilled():
    rows = packet_zh.build_rows(REPO_ROOT)

    assert all(row["translation_notice_zh"] == packet_zh.READING_AID_NOTICE for row in rows)
    assert all(row["prompt_reading_aid_zh"] for row in rows)
    assert all(not row[field] for row in rows for field in packet_zh.HUMAN_FIELDS)


def test_diagnostics_preserve_saved_status_and_exception_text():
    rows = packet_zh.build_rows(REPO_ROOT)

    syntax = [row for row in rows if row["failure_category"] == "syntax_failure"]
    unknown = [row for row in rows if row["failure_category"] == "unknown"]
    entry = [row for row in rows if row["failure_category"] == "missing_or_wrong_entry_point"]
    assert all("SyntaxError.msg=" in row["exception_or_diagnostic_original"] for row in syntax)
    assert all("exception_detail=not_saved" in row["exception_or_diagnostic_original"] for row in unknown)
    assert entry[0]["exception_or_diagnostic_original"] == "expected_entry_point_not_defined"


def test_outputs_are_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    packet_zh.write_outputs(REPO_ROOT, first)
    packet_zh.write_outputs(REPO_ROOT, second)

    for name in ("human_review_packet_zh.md", "human_adjudication_zh.csv"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_english_evidence_hash_failure_precedes_write(tmp_path, monkeypatch):
    monkeypatch.setitem(
        packet_zh.EXPECTED_ENGLISH_EVIDENCE_HASHES,
        "human_review_packet.md",
        "0" * 64,
    )
    output = tmp_path / "must-not-exist"
    with pytest.raises(
        packet_zh.milestone_1c.CensusIntegrityError,
        match="English evidence hash mismatch",
    ):
        packet_zh.write_outputs(REPO_ROOT, output)
    assert not output.exists()


def test_committed_chinese_outputs_match_builder():
    rows = packet_zh.build_rows(REPO_ROOT)
    output = REPO_ROOT / packet_zh.M1D_RELATIVE

    assert (output / "human_review_packet_zh.md").read_bytes() == packet_zh.render_packet(rows)
    assert (output / "human_adjudication_zh.csv").read_bytes() == packet_zh.render_csv(rows)
    parsed = list(
        csv.DictReader(
            io.StringIO((output / "human_adjudication_zh.csv").read_text(encoding="utf-8"))
        )
    )
    assert len(parsed) == 33
