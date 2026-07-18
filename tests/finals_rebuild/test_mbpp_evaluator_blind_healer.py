from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json

from agent_tools.finals_rebuild import mbpp_evaluator_blind_healer as healer
from scripts import build_mbpp_healer_candidate_v0_development_audit as audit


def _rows(value: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"))))


def test_public_api_has_no_treatment_or_evaluator_input() -> None:
    assert tuple(inspect.signature(healer.apply_healer).parameters) == (
        "normalized_source",
        "expected_entry_point",
        "expected_positional_arities",
        "generation_truncated",
    )
    assert healer.RULE_ORDER == ("entrypoint_alias_unique_arity_compatible_v0",)


def test_safe_unique_function_gets_alias_only() -> None:
    source = "import math\n\ndef model_name(x, y=0):\n    return math.ceil(x + y)\n"
    result = healer.apply_healer(source, "expected_name", {1, 2}, False)
    assert result.status == "transformed"
    assert result.triggered_rule_ids == result.applied_rule_ids == healer.RULE_ORDER
    assert result.ast_prefix_preserved is True
    assert result.output_source is not None
    before = ast.parse(source)
    after = ast.parse(result.output_source)
    assert ast.dump(ast.Module(body=after.body[:-1], type_ignores=[])) == ast.dump(before)
    assert result.output_source.endswith("\n\nexpected_name = model_name\n")


def test_present_entry_point_is_no_trigger_and_byte_identical() -> None:
    source = "def expected_name(x):\n    return x\n"
    result = healer.apply_healer(source, "expected_name", {1}, False)
    assert result.status == "no_trigger"
    assert result.diagnostic == "expected_entry_point_present"
    assert result.output_source == source
    assert result.input_sha256 == result.output_sha256


def test_unsafe_cases_abstain_and_do_not_change_source() -> None:
    cases = [
        (None, "expected", {1}, False, "pipeline_output_unavailable"),
        ("def other(x):\n    return x\n", "expected", {1}, True, "generation_truncated"),
        ("def broken(:\n", "expected", {1}, False, "syntax_parse_failure"),
        ("expected = 3\ndef other(x):\n    return x\n", "expected", {1}, False, "target_name_already_bound"),
        ("async def other(x):\n    return x\n", "expected", {1}, False, "async_function_ambiguity"),
        ("def a(x): return x\ndef b(x): return x\n", "expected", {1}, False, "top_level_function_count_not_one"),
        ("@staticmethod\ndef other(x): return x\n", "expected", {1}, False, "decorated_function"),
        ("def other(x): return x\n", "expected", {2}, False, "positional_arity_incompatible"),
        ("def other(x): return x\n", "expected", set(), False, "missing_or_invalid_arity_evidence"),
    ]
    for source, expected, arities, truncated, diagnostic in cases:
        result = healer.apply_healer(source, expected, arities, truncated)
        assert result.status == "abstained"
        assert result.output_source == source
        assert result.triggered_rule_ids == result.applied_rule_ids == ()
        assert result.diagnostic == diagnostic


def test_nested_or_conditional_target_binding_forces_abstention() -> None:
    source = "if FLAG:\n    expected = 1\n\ndef other(x):\n    return x\n"
    result = healer.apply_healer(source, "expected", {1}, False)
    assert result.status == "abstained"
    assert result.diagnostic == "target_name_already_bound"


def test_transform_is_deterministic() -> None:
    source = "def other(x):\n    return x\n"
    assert healer.apply_healer(source, "expected", {1}, False) == healer.apply_healer(
        source, "expected", [1, 1], False
    )


def test_offline_audit_has_600_programs_and_two_equal_conditions() -> None:
    outputs = audit.build_outputs()
    rows = _rows(outputs["healer_candidate_v0_cell_ledger.csv"])
    assert len(rows) == 600
    assert len({(row["task_id"], row["seed"]) for row in rows}) == 300
    assert len({row["task_id"] for row in rows}) == 60
    assert sum(row["prompt_condition"] == "p0" for row in rows) == 300
    assert sum(row["prompt_condition"] == "scaffold" for row in rows) == 300
    assert all(row["pipeline_precedes_healer"] == "true" for row in rows)
    assert all(row["evaluator_input_used"] == "false" for row in rows)


def test_rule_summary_reports_p0_and_scaffold_cells_and_tasks() -> None:
    outputs = audit.build_outputs()
    rows = _rows(outputs["healer_candidate_v0_rule_summary.csv"])
    assert len(rows) == 1
    row = rows[0]
    assert row["rule_id"] == healer.RULE_ID
    assert row["p0_static_signature_cells_before_truncation_guard"] == "40"
    assert row["scaffold_static_signature_cells_before_truncation_guard"] == "2"
    assert row["p0_trigger_cells"] == "39"
    assert row["scaffold_trigger_cells"] == "2"
    assert int(row["p0_trigger_cells"]) >= int(row["p0_trigger_unique_tasks"]) > 0
    assert int(row["scaffold_trigger_cells"]) >= int(row["scaffold_trigger_unique_tasks"]) > 0
    assert row["same_version_order_guards"] == "true"
    assert row["verified_functional_repair"] == "false"


def test_manifest_proves_offline_development_only_accounting() -> None:
    outputs = audit.build_outputs()
    manifest = json.loads(outputs["healer_candidate_v0_development_audit_manifest.json"])
    assert manifest["counts"] == {"programs": 600, "task_seed_identities": 300, "tasks": 60}
    assert manifest["prompt_condition_programs"] == {"p0": 300, "scaffold": 300}
    assert manifest["pipeline_precedes_healer"] is True
    assert manifest["same_healer_version_rule_order_guards"] is True
    assert manifest["evaluator_inputs_used"] is False
    assert manifest["functional_correctness_re_evaluated"] is False
    assert manifest["model_calls"] == manifest["evalplus_executions"] == 0


def test_deterministic_outputs_and_hashes() -> None:
    first = audit.build_outputs()
    second = audit.build_outputs()
    assert first == second
    manifest = json.loads(first["healer_candidate_v0_development_audit_manifest.json"])
    for name, digest in manifest["output_sha256_excluding_manifest"].items():
        assert hashlib.sha256(first[name]).hexdigest() == digest


def test_frozen_bytes_match_builder() -> None:
    audit.write_outputs(check=True)
