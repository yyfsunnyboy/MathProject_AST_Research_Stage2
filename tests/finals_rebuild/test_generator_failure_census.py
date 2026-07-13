from pathlib import Path
import json
import pytest
from agent_tools.finals_rebuild.generator_failure_census import GeneratorFailureCensusManifestError, _repairability, load_generator_failure_census_manifest, run_generator_failure_census, summarize_generator_failure_census, write_generator_failure_census_jsonl, write_generator_failure_census_summary
from agent_tools.finals_rebuild.generator_evaluator import evaluate_generator_code
from agent_tools.finals_rebuild.generator_failure_census import REQUIRED_DOMAINS, build_generator_failure_census_manifest, stratified_sample_generator_sources, GeneratorSource
ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/generator_failure_census_manifest.json"
def test_manifest_loads_and_is_safe():
    cases = load_generator_failure_census_manifest(MANIFEST, repo_root=ROOT)
    assert len(cases) == 30
    assert len({c.case_id for c in cases}) == len(cases)
    assert all(c.selection_seed == 20260713 and c.source_file.endswith(".py") for c in cases)
def test_manifest_rejects_invalid_shape(tmp_path):
    path = tmp_path / "bad.json"; path.write_text("[]", encoding="utf-8")
    with pytest.raises(GeneratorFailureCensusManifestError): load_generator_failure_census_manifest(path, repo_root=ROOT)
def test_repairability_categories():
    assert _repairability("passed", evaluate_generator_code("def generate(): return {'question_text':'q','correct_answer':'1'}"), "") == ("not_tier1", "already_executable")
    assert _repairability("safety_rejected", evaluate_generator_code("import os"), "") == ("not_tier1", "unsafe_code")
    assert _repairability("runtime_failure", evaluate_generator_code("raise RuntimeError()"), "") == ("not_tier1", "runtime_semantic_failure")
def test_writers_exclude_execution_payloads(tmp_path):
    records = run_generator_failure_census(load_generator_failure_census_manifest(MANIFEST, repo_root=ROOT)[:1], repo_root=ROOT)
    jsonl = tmp_path / "out.jsonl"; summary = tmp_path / "summary.json"
    write_generator_failure_census_jsonl(records, jsonl); write_generator_failure_census_summary(summarize_generator_failure_census(records), summary)
    row = json.loads(jsonl.read_text(encoding="utf-8"))
    assert not {"stdout", "stderr", "error_message", "returned_instance", "source"} & row.keys()
    assert json.loads(summary.read_text(encoding="utf-8"))["total"] == 1
def test_real_manifest_summary_invariants():
    records = run_generator_failure_census(load_generator_failure_census_manifest(MANIFEST, repo_root=ROOT), repo_root=ROOT)
    summary = summarize_generator_failure_census(records)
    assert summary.total == 30 and summary.passed + summary.failed == 30
    assert summary.tier1_candidates + summary.not_tier1 + summary.unknown_repairability == 30
def test_production_sampler_is_stratified_and_deterministic():
    first = build_generator_failure_census_manifest(ROOT / "experiments/results")
    second = build_generator_failure_census_manifest(ROOT / "experiments/results")
    assert first == second and first["selected_counts_by_domain"] == {domain: 10 for domain in REQUIRED_DOMAINS}
    assert len({case["source_file"] for case in first["cases"]}) == 30
def test_sampler_fails_fast_for_insufficient_domain():
    sources = [GeneratorSource(f"x/{i}.py", "applications_of_derivatives", "m", "Ab1") for i in range(9)]
    with pytest.raises(GeneratorFailureCensusManifestError, match="available=9"):
        stratified_sample_generator_sources(sources, ("applications_of_derivatives",), 10, 20260713)
