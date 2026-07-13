import json
from pathlib import Path

from agent_tools.finals_rebuild.math_healer_runner import derive_ab3


SOURCE = "def generate(level=1, **kwargs):\n    return {'question_text': 'q', 'correct_answer': 1}\n"
FIXTURES = Path(__file__).parent / "fixtures" / "healer_positive_controls"


def test_positive_control_metadata_excludes_research_estimates():
    for metadata_path in FIXTURES.glob("*.json"):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["positive_control_only"] is True
        assert metadata["excluded_from_research_effect_estimate"] is True


def test_no_rule_match_is_a_hash_preserving_no_op(tmp_path):
    source = FIXTURES / "no_op.py"
    result = derive_ab3(source=source, output_dir=tmp_path / "out", run_id="r", paired_run_id="p", task_id="t", model="m", condition="Ab3")
    assert result["status"] == "no_op"
    assert result["before_sha256"] == result["after_sha256"]
    assert result["applied_rules"] == []
    assert source.read_text(encoding="utf-8") == (FIXTURES / "no_op.py").read_text(encoding="utf-8")
    assert result["model_regenerated"] is False and result["repair_cpu_seconds"] >= 0


def test_existing_unified_cleanup_duplicate_definition_is_traced(tmp_path):
    source = FIXTURES / "duplicate_predefined_class.py"
    result = derive_ab3(source=source, output_dir=tmp_path / "out", run_id="r", paired_run_id="p", task_id="t", model="m", condition="Ab3")
    trace = json.loads((tmp_path / "out" / "repair_trace.json").read_text(encoding="utf-8"))
    assert result["status"] == "derived"
    assert result["applied_rules"] == ["unified_cleanup_duplicate_definition"]
    assert trace[0]["applied"] is True and result["after_ast_parse_success"] is True


def test_existing_unified_cleanup_shadowing_is_traced(tmp_path):
    source = FIXTURES / "shadowed_predefined_name.py"
    result = derive_ab3(source=source, output_dir=tmp_path / "out", run_id="r", paired_run_id="p", task_id="t", model="m", condition="Ab3")
    assert result["status"] == "derived"
    assert result["applied_rules"] == ["unified_cleanup_shadowed_predefined_name"]
    assert result["after_ast_parse_success"] is True


def test_existing_unified_cleanup_duplicate_function_is_traced(tmp_path):
    source = FIXTURES / "duplicate_function.py"
    result = derive_ab3(source=source, output_dir=tmp_path / "out", run_id="r", paired_run_id="p", task_id="t", model="m", condition="Ab3")
    assert result["status"] == "derived"
    assert result["applied_rules"] == ["unified_cleanup_duplicate_definition"]
    assert result["after_ast_parse_success"] is True


def test_healer_exception_persists_failed_record(tmp_path):
    class BrokenHealer:
        def heal(self, _source):
            raise RuntimeError("fixture failure")
    source = tmp_path / "source.py"
    source.write_text(SOURCE, encoding="utf-8")
    result = derive_ab3(source=source, output_dir=tmp_path / "out", run_id="r", paired_run_id="p", task_id="t", model="m", condition="Ab3", healer_factory=BrokenHealer)
    assert result["status"] == "failed"
    assert result["healer_error"]["exception_type"] == "RuntimeError"
    assert (tmp_path / "out" / "derivation_record.json").is_file()
