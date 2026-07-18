from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from scripts import build_mbpp_scaffold_v1_candidate_design as design


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / design.OUTPUT_RELATIVE


def test_revalidates_100_unique_pairs_and_four_evidence_groups():
    result = design.build_analysis(REPO_ROOT)
    rows = result["cell_rows"]

    assert len(rows) == 100
    assert len({(row["task_id"], row["seed"]) for row in rows}) == 100
    assert Counter(row["evidence_group"] for row in rows) == {
        "p1_paired_rescue": 17,
        "p1_paired_regression": 17,
        "common_pass": 13,
        "persistent_failure": 53,
    }


def test_per_cell_schema_contains_required_evidence_and_conservative_attribution():
    rows = design.build_analysis(REPO_ROOT)["cell_rows"]
    regressions = [row for row in rows if row["evidence_group"] == "p1_paired_regression"]
    rescues = [row for row in rows if row["evidence_group"] == "p1_paired_rescue"]

    assert len(regressions) == len(rescues) == 17
    assert all(row["direct_evidence"] and row["confidence"] for row in regressions + rescues)
    assert {row["cell_adjudication"] for row in regressions} <= {
        "scaffold_plausibly_related",
        "model_sampling_variation",
        "insufficient_evidence",
    }
    assert Counter(row["cell_adjudication"] for row in rescues) == {
        "format_compliance_rescue": 5,
        "compile_or_entry_improvement": 7,
        "insufficient_evidence": 5,
    }
    assert not any(
        row["p1_failure_taxonomy"] == "unknown"
        and row["remaining_problem_bucket"] == "possibly_evaluator_blind_healer"
        for row in rows
    )
    assert all(row["observable_output_structure_difference"] for row in rows)


def test_v0_instruction_review_is_exact_and_candidate_a_is_conservative():
    result = design.build_analysis(REPO_ROOT)
    reviews = result["instruction_rows"]

    assert len(reviews) == 7
    assert [row["v0_instruction_exact_text"] for row in reviews] == design.CANDIDATE_V0_LINES
    assert all(row["causal_status"] for row in reviews)
    candidate = next(item for item in design.CANDIDATES if item["recommended"])
    assert candidate["candidate_id"] == "v1_candidate_a_conservative_compaction"
    assert candidate["exact_text_utf8"].endswith("\n")
    assert candidate["changes_prompt_composition"] is False


def test_outputs_are_byte_deterministic_and_manifest_hashes_match():
    first = design.build_outputs(REPO_ROOT)
    second = design.build_outputs(REPO_ROOT)

    assert first == second
    for relative, expected in first.items():
        assert (OUTPUT_DIR / relative).read_bytes() == expected
    manifest = json.loads(first[Path("milestone_2c_manifest.json")])
    assert manifest["paired_identity"] == {
        "cells": 100,
        "duplicates": 0,
        "key": ["task_id", "seed"],
        "missing": 0,
    }
    assert manifest["freeze_status"] == "尚不凍結，只保留候選"
    assert manifest["prohibited_actions_attestation"]["model_calls"] == 0
    assert manifest["prohibited_actions_attestation"]["evalplus_executions"] == 0
    for name, metadata in manifest["outputs"].items():
        content = first[Path(name)]
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]


def test_committed_csv_and_report_cover_governance_questions():
    rows = list(
        csv.DictReader(
            io.StringIO(
                (OUTPUT_DIR / "milestone_2c_cell_evidence.csv").read_text(encoding="utf-8")
            )
        )
    )
    report = (OUTPUT_DIR / "scaffold_v1_candidate_design_zh.md").read_text(
        encoding="utf-8"
    )

    assert len(rows) == 100
    assert tuple(rows[0]) == design.CELL_FIELDS
    assert "v0 確定解決了什麼" in report
    assert "17 個 Pipeline regressions 能否歸因於 Scaffold" in report
    assert "尚不凍結，只保留候選" in report
    assert "historical development pool" in report
    assert "本輪不選題、不讀題、不建 split" in report
