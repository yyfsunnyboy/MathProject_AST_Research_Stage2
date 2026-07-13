from __future__ import annotations

import json

import pytest

from agent_tools.finals_rebuild.generator_integration_pilot import GeneratorPilotManifestError, load_generator_pilot_manifest, run_generator_pilot, summarize_generator_pilot


ROOT = __import__("pathlib").Path(__file__).parents[2]
MANIFEST = ROOT / "tests/finals_rebuild/fixtures/generator_pilot_manifest.json"


def test_manifest_loader_rejects_invalid_shapes(tmp_path):
    path=tmp_path / "manifest.json"; path.write_text(json.dumps([{"case_id":"x"}]))
    with pytest.raises(GeneratorPilotManifestError): load_generator_pilot_manifest(path, repo_root=tmp_path)
    path.write_text(json.dumps([])); assert load_generator_pilot_manifest(path, repo_root=tmp_path) == ()


@pytest.mark.parametrize("source_file", ["../outside.py", "missing.py", "not_python.txt"])
def test_manifest_loader_rejects_unsafe_paths(tmp_path, source_file):
    record={"case_id":"x","source_file":source_file,"expected_category":"unknown_baseline","curriculum_level":"g","domain":"d","model":"m","ablation":"a","notes":"n"}
    path=tmp_path / "manifest.json"; path.write_text(json.dumps([record]))
    with pytest.raises(GeneratorPilotManifestError): load_generator_pilot_manifest(path, repo_root=tmp_path)


def test_real_generator_pilot_manifest_runs_without_harness_crash():
    cases=load_generator_pilot_manifest(MANIFEST, repo_root=ROOT)
    results=run_generator_pilot(cases, repo_root=ROOT, timeout_seconds=.5)
    assert len(cases) == len(results) == 3
    assert [result.case.case_id for result in results] == [case.case_id for case in cases]
    assert all(len(result.source_sha256) == 64 and result.source_size_bytes > 0 for result in results)
    summary=summarize_generator_pilot(results)
    assert summary.total == 3 and summary.passed + summary.failed == 3
