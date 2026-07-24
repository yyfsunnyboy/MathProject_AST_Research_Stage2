from __future__ import annotations

import csv
import json
from collections import Counter

from scripts import audit_candidate_b_4b_failure_supply_analysis_v1 as audit
from scripts import finalize_candidate_b_4b_failure_supply_analysis_v1 as finalize
from scripts import prepare_candidate_b_4b_failure_supply_analysis_v1 as prepare


def _csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_prepared_outputs_rebuild_deterministically():
    expected = prepare.build_outputs()
    prepare.check_outputs(expected)


def test_extraction_is_itt_complete_and_fail_closed():
    root = prepare.REPO_ROOT / prepare.OUTPUT_RELATIVE
    rows = _csv(root / "extraction_itt_ledger.csv")
    assert len(rows) == 200
    assert Counter(row["extraction_status"] for row in rows) == Counter({"extracted": 186, "ambiguous": 14})
    cell5 = next(row for row in rows if row["cell_index"] == "5")
    assert cell5["extraction_status"] == "ambiguous"
    assert cell5["extracted_code_sha256"] == ""
    assert cell5["itt_included"] == "true"


def test_final_outputs_rebuild_and_forbidden_accounts_absent():
    expected = finalize.build_outputs()
    finalize.write_or_check(expected, True)
    root = prepare.REPO_ROOT / prepare.OUTPUT_RELATIVE
    eligibility = _csv(root / "healer_eligibility_ledger.csv")
    assert Counter(row["healer_eligibility"] for row in eligibility) == Counter({"abstain": 200})
    assert all(row["healer_applied"] == row["h1_created"] == "false" for row in eligibility)
    summary = json.loads((root / "aggregate_summary.json").read_text(encoding="utf-8"))
    assert summary["itt_denominator"] == 200
    assert summary["h0_evalplus"]["evaluated"] == 186


def test_independent_audit_passes():
    result = audit.audit()
    assert result["status"] == "PASS"
    assert all(result["checks"].values())
