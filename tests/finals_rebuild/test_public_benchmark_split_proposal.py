from __future__ import annotations

import csv
import hashlib
import io
import pathlib
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import build_public_benchmark_split_proposal as builder


def _build() -> builder.SplitProposalBuild:
    return builder.build_split_proposal(REPO_ROOT)


def test_dataset_and_role_counts_match_proposal_contract():
    build = _build()
    dataset_counts = Counter(row["dataset"] for row in build.rows)
    role_counts = Counter(row["proposed_role"] for row in build.rows)

    assert dataset_counts == {"HumanEval+": 164, "MBPP+": 378}
    assert role_counts == builder.EXPECTED_ROLE_COUNTS
    assert len(build.rows) == 542
    assert len({(row["dataset"], row["task_id"]) for row in build.rows}) == 542


def test_active_development_subset_and_candidate_attestation():
    rows = _build().rows
    active = [row for row in rows if row["active_development_generation_subset"] == "true"]
    candidates = [
        row
        for row in rows
        if row["proposed_role"]
        in {"external_confirmatory_candidate", "internal_confirmatory_candidate"}
    ]

    assert len(active) == 20
    assert all(row["dataset"] == "MBPP+" for row in active)
    assert all(row["proposed_role"] == "historical_development_pool" for row in active)
    assert len(candidates) == 168
    assert all(row["formal_status"] == "awaiting_manual_attestation" for row in candidates)
    assert all(row["requires_manual_attestation"] == "true" for row in candidates)
    assert all(row["formal_status"] != "frozen" for row in rows)


def test_selection_hashes_use_exact_formula_and_pool_ranks():
    rows = _build().rows
    for row in rows:
        payload = "|".join(
            (
                builder.SPLIT_VERSION,
                row["dataset"],
                row["dataset_version"],
                row["task_id"],
                builder.SALT,
            )
        )
        assert row["selection_hash"] == hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert len(row["selection_hash"]) == 64

    pools = (
        [row for row in rows if row["dataset"] == "HumanEval+" and row["proposed_role"] == "excluded_historical"],
        [row for row in rows if row["dataset"] == "HumanEval+" and row["proposed_role"] == "external_confirmatory_candidate"],
        [row for row in rows if row["dataset"] == "MBPP+" and row["proposed_role"] == "historical_development_pool"],
        [row for row in rows if row["dataset"] == "MBPP+" and row["proposed_role"] in {"validation", "internal_confirmatory_candidate", "sealed_reserve"}],
    )
    for pool in pools:
        assert [row["selection_hash"] for row in pool] == sorted(
            row["selection_hash"] for row in pool
        )
        assert [int(row["selection_rank_within_pool"]) for row in pool] == list(
            range(1, len(pool) + 1)
        )


def test_csv_schema_excludes_sensitive_and_formal_eligibility_fields():
    csv_bytes = builder.render_proposal_csv(_build())
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))

    assert tuple(rows[0]) == builder.CSV_FIELDS
    assert "confirmatory_eligible" not in rows[0]
    assert not ({"prompt", "answer", "tests", "output", "canonical_solution"} & set(rows[0]))
    assert all(row["formal_status"] != "frozen" for row in rows)


def test_csv_is_byte_deterministic_across_two_script_runs(tmp_path):
    first_csv = tmp_path / "first.csv"
    second_csv = tmp_path / "second.csv"
    first_summary = tmp_path / "first.md"
    second_summary = tmp_path / "second.md"
    common = [
        "--repo-root",
        str(REPO_ROOT),
        "--starting-commit",
        "e6201938b824f96429fdbf35db02fad2291dc024",
        "--generated-date",
        "2026-07-16",
    ]

    assert builder.main(common + ["--csv-out", str(first_csv), "--summary-out", str(first_summary)]) == 0
    assert builder.main(common + ["--csv-out", str(second_csv), "--summary-out", str(second_summary)]) == 0
    assert first_csv.read_bytes() == second_csv.read_bytes()


def test_summary_keeps_candidate_pools_unfrozen():
    build = _build()
    summary = builder.render_summary(
        build,
        repo_root=REPO_ROOT,
        starting_commit="e6201938b824f96429fdbf35db02fad2291dc024",
        generated_date="2026-07-16",
    )

    assert "proposal only; no formal confirmatory set is frozen" in summary
    assert "formal_status=awaiting_manual_attestation" in summary
    assert "None is frozen or formally confirmatory" in summary
    assert "confirmatory_eligible=true" in summary
