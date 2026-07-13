from __future__ import annotations

from pathlib import Path

from agent_tools.finals_rebuild.generator_healer_pilot import run_generator_healer_pilot, summarize_generator_healer_pilot
from agent_tools.finals_rebuild.generator_integration_pilot import load_generator_pilot_manifest


ROOT=Path(__file__).parents[2]
MANIFEST=ROOT / "tests/finals_rebuild/fixtures/generator_pilot_manifest.json"


def test_real_generator_healer_pilot_runs_and_preserves_prior_passes():
    cases=load_generator_pilot_manifest(MANIFEST,repo_root=ROOT)
    results=run_generator_healer_pilot(cases,repo_root=ROOT,timeout_seconds=.5)
    assert len(results) == 3
    assert all(len(result.source_sha256) == 64 for result in results)
    for result in results:
        if result.before_evaluation.success:
            assert result.after_evaluation.success
    summary=summarize_generator_healer_pilot(results)
    assert summary.total == 3
    assert sum((summary.rescued,summary.preserved_pass,summary.regressed,summary.changed_but_not_rescued,summary.unchanged_failure,summary.healer_error)) == 3


def test_batch_order_and_empty_summary():
    cases=load_generator_pilot_manifest(MANIFEST,repo_root=ROOT)
    results=run_generator_healer_pilot(cases,repo_root=ROOT,timeout_seconds=.5)
    assert [result.case.case_id for result in results] == [case.case_id for case in cases]
    summary=summarize_generator_healer_pilot(())
    assert summary.total == summary.before_passed == summary.after_passed == 0
