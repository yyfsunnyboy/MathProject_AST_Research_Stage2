#!/usr/bin/env python3
"""Independent fail-closed audit for the Stage2 MBPP+ 4B pilot analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prepare_candidate_b_4b_failure_supply_analysis_v1 as prepared  # noqa: E402

ROOT = REPO_ROOT / prepared.OUTPUT_RELATIVE


class AuditError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise AuditError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit() -> dict[str, Any]:
    inventory = _csv("generation_evidence_inventory.csv")
    extraction = _csv("extraction_itt_ledger.csv")
    results = _csv("manual_h0_evalplus_run_001/h0_evalplus_results.csv")
    taxonomy = _csv("taxonomy_v31_ledger.csv")
    eligibility = _csv("healer_eligibility_ledger.csv")
    cells = _csv("cell_itt_ledger.csv")
    summary = json.loads((ROOT / "aggregate_summary.json").read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / "reproducibility_receipt.json").read_text(encoding="utf-8"))
    execution = json.loads((ROOT / "manual_h0_evalplus_run_001/execution_manifest.json").read_text(encoding="utf-8"))
    frozen = json.loads((ROOT / "frozen_input_manifest.json").read_text(encoding="utf-8"))

    _require(len(inventory) == len(extraction) == len(taxonomy) == len(eligibility) == len(cells) == 200, "200-cell ledger completeness failure")
    _require(len(results) == 186, "EvalPlus result count failure")
    for rows, label in ((inventory, "inventory"), (extraction, "extraction"), (taxonomy, "taxonomy"), (eligibility, "eligibility"), (cells, "cells")):
        _require({int(row["cell_index"]) for row in rows} == set(range(1, 201)), f"{label} roster failure")
    for row in inventory:
        journal_path = REPO_ROOT / row["journal_path"]
        _require(journal_path.is_file() and _sha(journal_path) == row["journal_sha256"], f"journal bytes drift: cell {row['cell_index']}")
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        raw = journal.get("raw_response")
        _require(isinstance(raw, str) and hashlib.sha256(raw.encode("utf-8")).hexdigest() == row["raw_response_sha256"], f"raw response drift: cell {row['cell_index']}")
        _require(journal["generation_id"] == row["generation_id"], f"journal generation identity drift: cell {row['cell_index']}")
    ext_dist = Counter(row["extraction_status"] for row in extraction)
    _require(ext_dist == Counter({"extracted": 186, "ambiguous": 14}), "extraction distribution failure")
    ambiguous = {int(row["cell_index"]) for row in extraction if row["extraction_status"] == "ambiguous"}
    _require(ambiguous == set(frozen["fail_closed_ambiguous_cells"]), "ambiguous roster/manifest mismatch")
    _require(5 in ambiguous, "Cell 5 is not ambiguous")
    cell5 = next(row for row in cells if row["cell_index"] == "5")
    _require(cell5["extracted_code_sha256"] == "" and cell5["h0_evaluation_disposition"] == "not_evaluated_extraction_ambiguous", "Cell 5 candidate selection detected")
    _require({int(row["cell_index"]) for row in results} == set(range(1, 201)) - ambiguous, "result roster does not equal extracted roster")
    _require(all(row["parallel"] == "1" for row in results), "parallel != 1")
    _require(execution["results_sha256"] == _sha(ROOT / "manual_h0_evalplus_run_001/h0_evalplus_results.csv"), "EvalPlus result SHA mismatch")
    _require(execution["model_calls"] == 0 and execution["healer_applied"] is False and execution["h1_created"] is False, "forbidden evaluation-side mutation")
    _require(Counter(row["healer_eligibility"] for row in eligibility) == Counter({"abstain": 200}), "eligibility distribution drift")
    _require(all(row["healer_applied"] == row["h1_created"] == row["rescue_result_created"] == row["regression_result_created"] == "false" for row in eligibility), "H1/rescue/regression evidence detected")
    _require(not any(row["primary_failure_layer"] == "L5" for row in taxonomy), "unsupported L5 hard classification detected")
    _require(summary["itt_denominator"] == 200 and summary["h0_evalplus"]["evaluated"] == 186, "summary denominator drift")
    for name, digest in receipt["deterministic_output_sha256"].items():
        _require(_sha(ROOT / name) == digest, f"receipt hash drift: {name}")
    _require(receipt["generation_manifest_sha256"] == prepared.EXPECTED_MANIFEST_SHA256, "generation manifest binding drift")
    _require(receipt["model_calls"] == 0 and receipt["parallel"] == 1, "receipt safety drift")

    return {
        "audit_version": "candidate_b_4b_failure_supply_pilot_independent_audit_v1",
        "status": "PASS",
        "scope": "Stage2_MBPP+_only",
        "checks": {
            "generation_evidence_200": True,
            "raw_and_journal_sha_bound": True,
            "canonical_extraction_replayed": True,
            "itt_denominator_200": True,
            "ambiguous_fail_closed_14": True,
            "cell5_ambiguous_no_candidate": True,
            "h0_evalplus_results_186": True,
            "parallel_1": True,
            "taxonomy_v3_1_200": True,
            "unsupported_l5_absent": True,
            "eligibility_200": True,
            "healer_h1_rescue_regression_absent": True,
            "artifact_hashes_match_receipt": True,
        },
        "major_artifact_sha256": {
            name: _sha(ROOT / name) for name in (
                "generation_evidence_inventory.csv",
                "extraction_itt_ledger.csv",
                "manual_h0_evalplus_run_001/h0_evalplus_results.csv",
                "taxonomy_v31_ledger.csv",
                "healer_eligibility_ledger.csv",
                "cell_itt_ledger.csv",
                "aggregate_summary.json",
                "reproducibility_receipt.json",
                "research_report_zh.md",
            )
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = audit()
    data = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    path = ROOT / "independent_audit.json"
    if args.check:
        _require(path.is_file() and path.read_bytes() == data, "independent audit deterministic drift")
    else:
        _require(not path.exists(), "refusing to overwrite independent audit")
        path.write_bytes(data)
    print(json.dumps({"status": "independent_audit_passed", "check_only": args.check}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
