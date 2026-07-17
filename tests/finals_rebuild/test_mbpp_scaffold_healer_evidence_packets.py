from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import build_mbpp_scaffold_healer_evidence_packets as packets


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_scaffold_ledger_is_complete_and_partitioned():
    scaffold, _, manifest = packets.build_packets(REPO_ROOT)
    counts = Counter(row["scaffold_evidence_class"] for row in scaffold)

    assert len(scaffold) == 100
    assert len({row["cell_id"] for row in scaffold}) == 100
    assert counts == {
        "verified_pipeline_rescue": 30,
        "pipeline_extraction_failure": 21,
        "pipeline_extracted_evaluation_fail": 49,
    }
    assert manifest["scaffold_ledger_cells"] == 100
    assert all(row["observed_status"] == "fail" for row in scaffold)


def test_scaffold_features_and_pipeline_account_are_objective():
    scaffold, _, _ = packets.build_packets(REPO_ROOT)

    assert tuple(scaffold[0]) == packets.SCAFFOLD_FIELDS
    assert all(len(row["raw_generation_sha256"]) == 64 for row in scaffold)
    assert all(
        not row["pipeline_program_sha256"] or len(row["pipeline_program_sha256"]) == 64
        for row in scaffold
    )
    assert all(
        row["scaffold_evidence_class"] != "verified_pipeline_rescue"
        or (row["observed_status"] == "fail" and row["pipeline_status"] == "pass")
        for row in scaffold
    )
    assert all("done_reason=" in row["evidence_basis"] for row in scaffold)


def test_healer_review_covers_only_pipeline_failures():
    _, clusters, manifest = packets.build_packets(REPO_ROOT)

    assert tuple(clusters[0]) == packets.CLUSTER_FIELDS
    assert [row["signature_id"] for row in clusters] == list(packets.SIGNATURE_ORDER)
    assert sum(int(row["cell_count"]) for row in clusters) == 70
    assert manifest["healer_review_cells"] == 70
    assert manifest["healer_review_unique_tasks"] == 19
    assert manifest["pipeline_rescues_are_healer_effect"] is False
    assert manifest["candidate_labels_are_verified_rules"] is False


def test_signature_counts_and_candidate_safety_gate():
    _, clusters, manifest = packets.build_packets(REPO_ROOT)
    counts = {row["signature_id"]: int(row["cell_count"]) for row in clusters}

    assert counts == {
        "extraction_ambiguous_multiple_python_fences": 20,
        "extraction_ambiguous_other_fences": 1,
        "syntax_fstring_parse_error": 1,
        "syntax_unterminated_string": 2,
        "syntax_invalid_plain_text": 3,
        "entrypoint_unique_arity_compatible_candidate": 16,
        "entrypoint_no_unique_candidate": 1,
        "unknown_eval_failure_single_top_level_function": 24,
        "unknown_eval_failure_multiple_top_level_functions": 2,
    }
    assert manifest["proposed_action_cell_counts"] == {
        "healer_candidate": 16,
        "manual_review": 33,
        "scaffold_only": 21,
    }
    syntax = [row for row in clusters if row["category"] == "syntax_failure"]
    assert all(row["proposed_action"] == "manual_review" for row in syntax)
    unknown = [row for row in clusters if row["category"] == "unknown"]
    assert all(row["proposed_action"] == "manual_review" for row in unknown)


def test_outputs_are_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    packets.write_outputs(REPO_ROOT, first)
    packets.write_outputs(REPO_ROOT, second)

    for name in (
        "scaffold_evidence_ledger.csv",
        "failure_signature_clusters.csv",
        "human_review_packet.md",
        "evidence_manifest.json",
        "evidence_summary.md",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_input_hash_failure_precedes_output_write(tmp_path, monkeypatch):
    monkeypatch.setitem(packets.EXPECTED_M1C_HASHES, "failure_census.csv", "0" * 64)
    output = tmp_path / "must-not-exist"

    with pytest.raises(packets.milestone_1c.CensusIntegrityError, match="1C artifact hash mismatch"):
        packets.write_outputs(REPO_ROOT, output)

    assert not output.exists()


def test_committed_outputs_match_builder():
    scaffold, clusters, manifest = packets.build_packets(REPO_ROOT)
    output = REPO_ROOT / packets.OUTPUT_RELATIVE

    assert (output / "scaffold_evidence_ledger.csv").read_bytes() == packets.render_scaffold_ledger(scaffold)
    assert (output / "failure_signature_clusters.csv").read_bytes() == packets.render_clusters(clusters)
    assert json.loads((output / "evidence_manifest.json").read_text(encoding="utf-8")) == manifest
    parsed = list(
        csv.DictReader(
            io.StringIO((output / "scaffold_evidence_ledger.csv").read_text(encoding="utf-8"))
        )
    )
    assert len(parsed) == 100
