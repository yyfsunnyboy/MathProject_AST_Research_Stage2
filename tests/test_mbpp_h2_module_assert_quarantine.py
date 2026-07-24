from __future__ import annotations

import ast
import csv
import inspect
import io
import json

import pytest

from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (
    RULE_ID,
    RULE_STATUS,
    quarantine_module_assert_entrypoint_selftest,
)
from scripts import build_h2_module_assert_quarantine_static_audit_v1 as audit


def apply(source: str, entry_point: str = "solve", **kwargs):
    facts = {"extraction_unambiguous": True, "source_complete": True}
    facts.update(kwargs)
    return quarantine_module_assert_entrypoint_selftest(
        source, entry_point, **facts
    )


def test_transforms_one_direct_literal_entrypoint_selftest() -> None:
    source = "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n"
    decision = apply(source)

    assert decision.rule_id == RULE_ID
    assert decision.rule_status == RULE_STATUS
    assert decision.triggered and decision.transformed and not decision.abstained
    assert decision.reason == "transformed_module_assert_quarantined"
    assert decision.module_assert_count == 1
    assert decision.entrypoint_status == "unique"
    assert decision.source_sha256 != decision.output_sha256
    assert (
        'if __name__ == "__main__":\n    assert solve(1) == 2\n'
        in decision.output_source
    )
    output_tree = ast.parse(decision.output_source)
    assert not any(isinstance(node, ast.Assert) for node in output_tree.body)
    assert ast.get_source_segment(source, ast.parse(source).body[0]) == (
        ast.get_source_segment(decision.output_source, output_tree.body[0])
    )


def test_accepts_builtin_abs_tolerance_without_external_state() -> None:
    decision = apply(
        "def solve(x):\n    return x\n\nassert abs(solve(5.2) - 5.2) < 1e-6\n"
    )
    assert decision.transformed
    assert ast.parse(decision.output_source)


def test_repeated_entrypoint_call_in_fstring_message_abstains() -> None:
    source = (
        "def solve(x):\n    return x\n\n"
        'assert solve(1) == 2, f"Expected 2, got {solve(1)}"\n'
    )
    decision = apply(source)
    assert decision.abstained
    assert decision.reason == "assert_message_depends_on_external_state"
    assert decision.output_source == source


@pytest.mark.parametrize(
    ("source", "entry_point", "reason"),
    [
        ("def solve(:\n", "solve", "source_unparseable"),
        ("def other(x):\n    return x\nassert other(1) == 1\n", "solve", "entry_point_missing"),
        (
            "def solve(x):\n    return x\ndef solve(y):\n    return y\nassert solve(1) == 1\n",
            "solve",
            "entry_point_multiple",
        ),
        ("def solve(x):\n    return x\n", "solve", "no_module_level_assert"),
        (
            "def solve(x):\n    return x\nassert solve(1) == 1\nassert solve(2) == 2\n",
            "solve",
            "module_assert_count_not_one",
        ),
        (
            "def solve(x):\n    return x\nresult = solve(1)\nassert result == 1\n",
            "solve",
            "assert_not_direct_entrypoint_selftest",
        ),
        (
            "import math\ndef solve(x):\n    return x\nassert math.isclose(solve(1), 1)\n",
            "solve",
            "assert_has_external_or_side_effectful_call",
        ),
        (
            "def solve(x):\n    return x\nx = 1\nassert solve(x) == 1\n",
            "solve",
            "assert_depends_on_external_state",
        ),
        (
            "def solve(x):\n    return x\ndef helper(x):\n    return x\nassert helper(solve(1)) == 1\n",
            "solve",
            "assert_has_external_or_side_effectful_call",
        ),
    ],
)
def test_fail_closed_structural_and_safety_guards(
    source: str, entry_point: str, reason: str
) -> None:
    decision = apply(source, entry_point)
    assert decision.abstained and not decision.transformed
    assert decision.output_source == source
    assert decision.source_sha256 == decision.output_sha256
    assert decision.reason == reason


@pytest.mark.parametrize(
    ("fact", "value", "reason"),
    [
        ("extraction_unambiguous", False, "extraction_ambiguous_or_unknown"),
        ("extraction_unambiguous", None, "extraction_ambiguous_or_unknown"),
        ("source_complete", False, "source_truncated_or_completion_unknown"),
        ("source_complete", None, "source_truncated_or_completion_unknown"),
    ],
)
def test_unknown_or_adverse_provenance_abstains(
    fact: str, value: bool | None, reason: str
) -> None:
    source = "def solve(x):\n    return x\nassert solve(1) == 1\n"
    decision = apply(source, **{fact: value})
    assert decision.abstained
    assert decision.reason == reason
    assert decision.output_source == source


def test_idempotent_and_deterministic() -> None:
    source = "def solve(x):\n    return x\nassert solve(1) == 1\n"
    first = apply(source)
    repeated = apply(source)
    second = apply(first.output_source)

    assert first.record() == repeated.record()
    assert second.abstained
    assert second.reason == "no_module_level_assert"
    assert second.output_source == first.output_source
    assert second.source_sha256 == first.output_sha256


def test_rule_api_has_no_outcome_or_task_identity_input() -> None:
    parameters = inspect.signature(
        quarantine_module_assert_entrypoint_selftest
    ).parameters
    assert set(parameters) == {
        "source",
        "entry_point",
        "extraction_unambiguous",
        "source_complete",
    }
    rule_source = inspect.getsource(quarantine_module_assert_entrypoint_selftest)
    for forbidden in ("task_id", "pass_status", "evalplus", "canonical_solution"):
        assert forbidden not in rule_source.lower()


def test_static_audit_builder_is_deterministic_and_zero_execution() -> None:
    first = audit.build_outputs()
    second = audit.build_outputs()
    assert first == second
    assert set(first) == {
        "aggregate_summary.json",
        "credential_scan.json",
        "decision_ledger.csv",
        "manifest.json",
        "reproducibility_receipt.json",
        "research_report_zh.md",
        "transformed_sources.jsonl",
    }
    summary = json.loads(first["aggregate_summary.json"])
    assert summary["rule_status"] == RULE_STATUS
    assert summary["candidate_execution_count"] == 0
    assert summary["evalplus_execution_count"] == 0
    assert summary["model_call_count"] == 0
    assert summary["cohorts"]["4B_all_module_level_assert_cells"]["cells"] == 68
    assert summary["cohorts"]["9B_formal_Conditional23"]["cells"] == 23
    assert summary["cohorts"]["9B_formal_Conditional23"]["transformed"] == 23
    assert (
        summary["reference_reconciliation"][
            "source_incomplete_and_predicate_complex_overlap"
        ]
        == 3
    )
    ledger = list(
        csv.DictReader(io.StringIO(first["decision_ledger.csv"].decode("utf-8")))
    )
    assert len(ledger) == 91
    assert all(row["rule_id"] == RULE_ID for row in ledger)
    assert all(row["claim"].endswith("no_pass_claim") for row in ledger)
    receipt = json.loads(first["reproducibility_receipt.json"])
    assert not any(receipt["controls"].values())
    scan = json.loads(first["credential_scan.json"])
    assert scan["status"] == "pass" and scan["finding_count"] == 0
