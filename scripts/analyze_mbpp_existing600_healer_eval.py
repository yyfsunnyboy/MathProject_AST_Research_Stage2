#!/usr/bin/env python3
"""Pair frozen H0 results with complete H1 results after manual EvalPlus.

The analyzer is separate from evaluation so no rescue/regression conclusion can
be emitted before all 41 changed H1 cells have formal results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_mbpp_existing600_healer_eval as evaluation_driver  # noqa: E402

PAIR_FIELDS = (
    "program_id", "development_layer", "prompt_condition", "treatment",
    "run_id", "task_id", "seed", "generation_id", "raw_sha256",
    "normalized_source_sha256", "h1_source_sha256", "source_changed",
    "h0_pass", "h1_pass", "transition", "h1_result_basis",
    "per_cell_accept_revert_or_selective_use",
)
SUMMARY_FIELDS = (
    "stratum", "programs", "changed", "unchanged", "h0_pass", "h1_pass",
    "fail_to_fail", "fail_to_pass_rescue", "pass_to_fail_regression",
    "pass_to_pass",
)


class PairedAnalysisError(RuntimeError):
    """Raised before writes when result completeness or identity checks fail."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PairedAnalysisError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def decision_status(*, rescue: int, regression: int) -> str:
    if regression > 0:
        return "healer_candidate_not_qualified"
    if rescue >= 1:
        return "eligible_for_independent_prospective_qualification"
    return "statically_safe_no_observed_functional_benefit"


def build_analysis(
    *, manifest_path: Path, manifest_sha256: str, changed_results_path: Path,
) -> dict[str, Any]:
    manifest, changed_inputs = evaluation_driver.validate_frozen_inputs(
        manifest_path=manifest_path, manifest_sha256=manifest_sha256, parallel=1
    )
    result_dir = changed_results_path.parent
    execution_path = result_dir / "execution_manifest.json"
    _require(changed_results_path.name == "changed_h1_evalplus_results.csv", "unexpected changed-results filename")
    _require(execution_path.is_file(), "evaluation execution manifest missing")
    execution = _read_json(execution_path)
    results_bytes = changed_results_path.read_bytes()
    _require(execution["status"] == "changed_h1_evaluation_complete_pending_paired_analysis", "evaluation completion status drift")
    _require(execution["frozen_manifest_sha256"] == evaluation_driver.FROZEN_MANIFEST_SHA256, "evaluation manifest binding drift")
    _require(execution["changed_h1_cells_evaluated"] == 41, "changed evaluation count drift")
    _require(execution["unchanged_cells_not_re_evaluated"] == 559, "unchanged evaluation count drift")
    _require(execution["parallel"] == 1, "formal evaluation parallel drift")
    _require(execution["results_sha256"] == _sha256_bytes(results_bytes), "changed result bytes drift")
    _require(execution["rescue_regression_conclusion_produced"] is False, "premature conclusion flag drift")

    changed_results = _read_csv(changed_results_path)
    _require(len(changed_results) == 41, "all 41 changed results are required")
    result_by_account = {row["evaluation_account_id"]: row for row in changed_results}
    _require(len(result_by_account) == 41, "duplicate changed result identity")
    input_by_account = {row["evaluation_account_id"]: row for row in changed_inputs}
    _require(set(result_by_account) == set(input_by_account), "changed result identity mismatch or missing result")
    for account_id, result in result_by_account.items():
        source = input_by_account[account_id]
        for field in ("program_id", "run_id", "task_id", "seed", "generation_id", "normalized_source_sha256", "h1_source_sha256"):
            _require(str(result[field]) == str(source[field]), f"changed result provenance drift: {field} {account_id}")
        _require(result["evaluator_version"] == evaluation_driver.EXPECTED_EVALPLUS_VERSION, "changed evaluator version drift")
        _require(result["evaluator_engine"] == evaluation_driver.EXPECTED_EVALUATOR_ENGINE, "changed evaluator engine drift")
        _require(result["h1_evalplus_pass"] in {"true", "false"}, "invalid changed H1 pass result")

    accounts = _read_csv(manifest_path.parent / "h0_h1_accounts.csv")
    reuse = _read_csv(manifest_path.parent / "unchanged_h0_reuse_ledger.csv")
    h0_by_program = {row["program_id"]: row for row in accounts if row["healer_account"] == "H0"}
    h1_by_program = {row["program_id"]: row for row in accounts if row["healer_account"] == "H1"}
    reuse_by_program = {row["program_id"]: row for row in reuse}
    _require(len(h0_by_program) == len(h1_by_program) == 600, "H0/H1 program identity completeness drift")
    _require(len(reuse_by_program) == 559, "reuse identity completeness drift")

    pairs: list[dict[str, str]] = []
    for h0 in (row for row in accounts if row["healer_account"] == "H0"):
        program_id = h0["program_id"]
        h1 = h1_by_program[program_id]
        h0_pass = h0["existing_h0_pass"] == "true"
        changed = h1["source_changed"] == "true"
        if changed:
            result = result_by_account.get(h1["evaluation_account_id"])
            _require(result is not None, f"changed H1 result missing: {program_id}")
            h1_pass = result["h1_evalplus_pass"] == "true"
            basis = "manual_evalplus_changed_h1"
        else:
            ledger = reuse_by_program.get(program_id)
            _require(ledger is not None and ledger["reuse_eligible"] == "true", f"unchanged reuse proof missing: {program_id}")
            _require(ledger["h0_source_state_sha256"] == ledger["h1_source_state_sha256"], f"unchanged source-state hash drift: {program_id}")
            h1_pass = h0_pass
            basis = "exact_source_state_sha256_h0_reuse"
        transition = (
            "pass_to_pass" if h0_pass and h1_pass
            else "pass_to_fail_regression" if h0_pass
            else "fail_to_pass_rescue" if h1_pass
            else "fail_to_fail"
        )
        pairs.append({
            "program_id": program_id,
            "development_layer": h0["development_layer"],
            "prompt_condition": h0["prompt_condition"],
            "treatment": h0["treatment"],
            "run_id": h0["run_id"],
            "task_id": h0["task_id"],
            "seed": h0["seed"],
            "generation_id": h0["generation_id"],
            "raw_sha256": h0["raw_sha256"],
            "normalized_source_sha256": h0["normalized_source_sha256"],
            "h1_source_sha256": h1["evaluation_source_sha256"],
            "source_changed": str(changed).lower(),
            "h0_pass": str(h0_pass).lower(),
            "h1_pass": str(h1_pass).lower(),
            "transition": transition,
            "h1_result_basis": basis,
            "per_cell_accept_revert_or_selective_use": "false",
        })
    _require(len(pairs) == 600, "paired result count must be 600")

    summaries: list[dict[str, str]] = []
    for stratum in ("all", "p0", "scaffold_like"):
        rows = pairs if stratum == "all" else [row for row in pairs if row["prompt_condition"] == stratum]
        transitions = Counter(row["transition"] for row in rows)
        summaries.append({
            "stratum": stratum,
            "programs": str(len(rows)),
            "changed": str(sum(row["source_changed"] == "true" for row in rows)),
            "unchanged": str(sum(row["source_changed"] == "false" for row in rows)),
            "h0_pass": str(sum(row["h0_pass"] == "true" for row in rows)),
            "h1_pass": str(sum(row["h1_pass"] == "true" for row in rows)),
            "fail_to_fail": str(transitions["fail_to_fail"]),
            "fail_to_pass_rescue": str(transitions["fail_to_pass_rescue"]),
            "pass_to_fail_regression": str(transitions["pass_to_fail_regression"]),
            "pass_to_pass": str(transitions["pass_to_pass"]),
        })
    overall = summaries[0]
    rescue = int(overall["fail_to_pass_rescue"])
    regression = int(overall["pass_to_fail_regression"])
    return {
        "pairs": pairs,
        "summaries": summaries,
        "decision": {
            "status": decision_status(rescue=rescue, regression=regression),
            "rescue": rescue,
            "regression": regression,
            "rules_frozen_before_evaluation": True,
            "all_600_accounts_included": True,
            "individual_transformation_withdrawal_or_acceptance": False,
            "source_manifest_sha256": evaluation_driver.FROZEN_MANIFEST_SHA256,
            "changed_results_sha256": _sha256_bytes(results_bytes),
            "source_manifest_status": manifest["status"],
        },
    }


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def write_outputs(
    *, manifest_path: Path, manifest_sha256: str, changed_results_path: Path,
    output_dir: Path,
) -> None:
    _require(not output_dir.exists(), "analysis output exists; retry/resume/overwrite forbidden")
    analysis = build_analysis(
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        changed_results_path=changed_results_path,
    )
    pair_bytes = _csv_bytes(analysis["pairs"], PAIR_FIELDS)
    summary_bytes = _csv_bytes(analysis["summaries"], SUMMARY_FIELDS)
    decision_bytes = (json.dumps(analysis["decision"], indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_bytes = (json.dumps({
        "status": "paired_analysis_complete",
        "programs": 600,
        "output_sha256_excluding_manifest": {
            "paired_cell_results.csv": _sha256_bytes(pair_bytes),
            "stratified_transition_summary.csv": _sha256_bytes(summary_bytes),
            "qualification_decision.json": _sha256_bytes(decision_bytes),
        },
    }, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True)
    for name, content in (
        ("paired_cell_results.csv", pair_bytes),
        ("stratified_transition_summary.csv", summary_bytes),
        ("qualification_decision.json", decision_bytes),
        ("paired_analysis_manifest.json", manifest_bytes),
    ):
        with (output_dir / name).open("xb") as handle:
            handle.write(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--changed-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        write_outputs(
            manifest_path=args.manifest,
            manifest_sha256=args.manifest_sha256,
            changed_results_path=args.changed_results,
            output_dir=args.output_dir,
        )
    except (PairedAnalysisError, evaluation_driver.EvaluationDriverError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
