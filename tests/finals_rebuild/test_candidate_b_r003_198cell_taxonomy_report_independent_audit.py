from __future__ import annotations

import csv
import io
import json

from scripts import audit_candidate_b_r003_198cell_taxonomy_report as audit


def test_baseline_sha_and_independent_identity_closure() -> None:
    verified = audit.verify_hashes()
    records, provenance = audit.independently_rebuild()
    closure = provenance["closure"]

    assert len(verified) == len(audit.EXPECTED_HASHES) == 27
    assert all(item["verified"] for item in verified)
    assert len(records) == 198
    assert closure["reconciliation"] == "198=177+21"
    assert closure["unique_program_id"] == 198
    assert closure["unique_cell_identity"] == 198
    assert closure["unique_source_sha256"] == 155
    assert closure["duplicate_programs"] == closure["duplicate_cells"] == 0
    assert closure["omissions"] == closure["remaining"] == 0
    assert len({row["task_id"] for row in records}) == 50
    assert all(row["benchmark"] == "MBPP+" for row in records)
    assert all(row["condition"] == "Candidate_B/H0" for row in records)


def test_independent_statistics_and_zero_denominator_groups() -> None:
    expected = audit.rebuild_expected()
    distributions = expected["distributions"]
    cross = expected["cross_analysis"]

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
    assert distributions["secondary"]["layers"]["L4"]["n"] == 2
    assert distributions["secondary"]["layers"]["L5"]["n"] == 42
    assert {key: value["n"] for key, value in distributions["confidence"].items()} == {
        "HIGH": 126,
        "LOW": 67,
        "MEDIUM": 5,
    }
    assert distributions["outcome_validity"]["VALID_MODEL_OUTCOME"]["n"] == 198
    assert {key: value["n"] for key, value in distributions["healer"].items()} == {
        "abstain": 175,
        "conditional": 23,
        "eligible": 0,
    }
    assert expected["key_counts"]["algorithm_reconstruction_required"] == 31
    assert cross["benchmark_by_primary"]["HumanEval+"]["denominator"] == 0
    assert cross["condition_by_healer"]["Candidate_B/H1"]["denominator"] == 0
    assert all(
        value["percent"] is None
        for value in cross["benchmark_by_primary"]["HumanEval+"]["values"].values()
    )
    assert cross["scaffold_like"]["status"] == "NA"
    assert cross["scaffold_like"]["denominator"] == 0


def test_summary_report_and_narratives_are_affirmed() -> None:
    analysis = audit.analyze()

    assert analysis["counts"] == {
        "AFFIRMED": 22,
        "NON_MATERIAL": 0,
        "MATERIAL": 0,
    }
    assert analysis["differences"] == []
    assert analysis["numeric_expectations_checked"] == 253
    assert analysis["narrative_rules_checked"] == 7
    assert analysis["verdict"] == "READY_TO_FINALIZE_198CELL_REPORT"
    assert all(row["status"] == "AFFIRMED" for row in analysis["findings"])


def test_difference_ledger_is_empty_and_findings_are_reconstructable() -> None:
    outputs = audit.build_outputs()
    findings = list(
        csv.DictReader(
            io.StringIO(
                outputs[audit.AUDIT_DIR / "audit_findings.csv"].decode("utf-8")
            )
        )
    )
    differences = list(
        csv.DictReader(
            io.StringIO(
                outputs[audit.AUDIT_DIR / "difference_ledger.csv"].decode("utf-8")
            )
        )
    )

    assert len(findings) == 22
    assert {row["status"] for row in findings} == {"AFFIRMED"}
    assert differences == []


def test_deterministic_outputs_manifest_and_zero_execution() -> None:
    before = {path: audit._file_sha(path) for path in audit.EXPECTED_HASHES}
    first = audit.build_outputs()
    second = audit.build_outputs()
    after = {path: audit._file_sha(path) for path in audit.EXPECTED_HASHES}

    assert first == second
    assert before == after
    for relative, data in first.items():
        assert audit._path(relative).read_bytes() == data

    manifest = json.loads(first[audit.AUDIT_DIR / "manifest.json"])
    execution = json.loads(first[audit.AUDIT_DIR / "execution_counts.json"])
    assert manifest["verdict"] == "READY_TO_FINALIZE_198CELL_REPORT"
    assert manifest["affirmed"] == 22
    assert manifest["non_material"] == manifest["material"] == 0
    assert manifest["mbpp_plus"] == manifest["h0"] == 198
    assert manifest["humaneval_plus"] == manifest["h1"] == 0
    assert manifest["eligible"] == 0
    assert manifest["conditional"] == 23
    assert manifest["abstain"] == 175
    assert set(execution.values()) == {0}
