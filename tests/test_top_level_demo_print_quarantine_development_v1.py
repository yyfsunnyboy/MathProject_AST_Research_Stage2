import csv
import io
import json

from scripts import finalize_top_level_demo_print_quarantine_development_v1 as final
from scripts import prepare_top_level_demo_print_quarantine_development_v1 as prepare


def test_static_audit_is_deterministic_complete_and_zero_execution() -> None:
    first = prepare.build_outputs(prepare.REPO_ROOT)
    second = prepare.build_outputs(prepare.REPO_ROOT)
    assert first == second
    summary = json.loads(first["static_audit_summary.json"])
    assert summary["cohort"] == {"4B": 200, "9B": 300, "total": 500}
    assert summary["static_decisions"]["transformed"] == 21
    assert summary["static_decisions"]["abstained"] == 479
    assert summary["model_calls"] == summary["candidate_executions"] == 0
    rows = list(
        csv.DictReader(io.StringIO(first["static_audit_ledger.csv"].decode()))
    )
    assert len(rows) == 500
    assert len({(row["model"], row["cell_id"]) for row in rows}) == 500


def test_preregistered_arm_scope_and_exact_rule_pins() -> None:
    outputs = prepare.build_outputs(prepare.REPO_ROOT)
    prereg = json.loads(outputs["preregistration.json"])
    assert prereg["execution"]["new_evalplus_cells"] == 50
    assert prereg["execution"]["raw_reused"] == 21
    assert prereg["execution"]["h2_reused"] == 13
    assert prereg["rule"]["sha256"] == prepare.EXPECTED_RULE_SHA
    assert prereg["h2"]["sha256"] == prepare.EXPECTED_H2_SHA
    assert prereg["confirmatory_claim"] is False


def test_finalization_is_deterministic_and_uses_criterion_b() -> None:
    first = final.build_outputs(final.REPO_ROOT)
    second = final.build_outputs(final.REPO_ROOT)
    assert first == second
    summary = json.loads(first["evaluation_summary.json"])
    assert summary["arm_summary"]["demo_print_only"]["verified_rescue"] == 0
    assert summary["arm_summary"]["demo_print_only"]["regression"] == 0
    assert summary["verification"]["all_raw_pass_preserved"] is True
    decision = json.loads(first["freeze_decision.json"])
    assert decision["criterion"] == "B"
    assert decision["decision"] == "development_candidate_not_frozen"
    assert decision["h2_effect_attributed_to_new_rule"] is False
    assert summary["model_calls"] == summary["candidate_generations"] == 0


def test_frozen_outputs_match_both_builders() -> None:
    prepare.write_or_check(prepare.REPO_ROOT, True)
    final.write_or_check(final.REPO_ROOT, True)
