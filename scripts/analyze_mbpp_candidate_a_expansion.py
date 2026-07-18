#!/usr/bin/env python3
"""Run the frozen paired analysis after both Milestone 2E evaluations exist."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    PersistenceError,
    durable_write_text_new,
)
from scripts import build_mbpp_scaffold_healer_evidence_packets as evidence  # noqa: E402
from scripts import build_mbpp_scaffold_v0_paired_analysis as paired_math  # noqa: E402
from scripts import freeze_mbpp_candidate_a_expansion_protocol as frozen  # noqa: E402
from scripts import freeze_mbpp_candidate_a_interruption_recovery as recovery  # noqa: E402
from scripts import run_mbpp_candidate_a_expansion as runner  # noqa: E402


class ProspectiveAnalysisError(RuntimeError):
    """Raised when evaluated artifacts do not match the frozen paired plan."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProspectiveAnalysisError(message)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _index(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        _require(key not in indexed, f"duplicate {label} identity: {key}")
        indexed[key] = row
    return indexed


def _status_transition(p0: str, candidate: str) -> str:
    _require(p0 in {"pass", "fail"} and candidate in {"pass", "fail"}, "invalid status")
    return f"{p0}_to_{candidate}"


def build_analysis(p0_run_id: str, candidate_run_id: str) -> dict[str, Any]:
    _require(p0_run_id == frozen.P0_RUN_ID, "P0 run ID differs from frozen plan")
    _require(candidate_run_id == recovery.CA_R002_RUN_ID, "Candidate run ID differs from recovery plan")
    p0_plan = runner.load_frozen_plan("p0")
    ca_plan = runner.load_frozen_plan("candidate_a")
    planned = [(cell["task_id"], cell["seed"]) for cell in p0_plan["cells"]]
    _require(planned == [(cell["task_id"], cell["seed"]) for cell in ca_plan["cells"]], "plan pairing drift")
    expected_keys = set(planned)

    p0_dir = runner.resolve_run_dir("p0", p0_run_id)
    ca_dir = runner.resolve_run_dir("candidate_a", candidate_run_id)
    p0_eval = _index(_read_csv(p0_dir / "evaluation_results.csv"), "P0 evaluation")
    ca_eval = _index(_read_csv(ca_dir / "evaluation_results.csv"), "Candidate evaluation")
    p0_raw = _index(_read_jsonl(p0_dir / "raw_generations.jsonl"), "P0 raw")
    ca_raw = _index(_read_jsonl(ca_dir / "raw_generations.jsonl"), "Candidate raw")
    ca_pipeline = _index(_read_jsonl(ca_dir / "pipeline_corrected.jsonl"), "Candidate pipeline")
    _require(
        set(p0_eval) == set(ca_eval) == set(p0_raw) == set(ca_raw) == set(ca_pipeline) == expected_keys,
        "paired evaluated identities must equal the frozen 200-cell schedule",
    )

    transitions: Counter[str] = Counter()
    rows: list[dict[str, str]] = []
    for task_id, seed in planned:
        key = (task_id, seed)
        p0_status = p0_eval[key]["pipeline_corrected_status"]
        ca_status = ca_eval[key]["pipeline_corrected_status"]
        transition = _status_transition(p0_status, ca_status)
        transitions[transition] += 1
        rows.append(
            {
                "task_id": task_id,
                "seed": str(seed),
                "p0_generation_id": p0_eval[key]["generation_id"],
                "candidate_generation_id": ca_eval[key]["generation_id"],
                "p0_pipeline_status": p0_status,
                "candidate_pipeline_status": ca_status,
                "pipeline_transition": transition,
                "paired_rescue": str(transition == "fail_to_pass").lower(),
                "paired_regression": str(transition == "pass_to_fail").lower(),
                "candidate_protocol_compliant": ca_eval[key]["protocol_compliant"],
                "candidate_reasoning_leakage": ca_eval[key]["reasoning_leakage"],
                "regression_disclosure": (
                    "generic_evaluator_result_only_no_functional_cause_guessed"
                    if transition == "pass_to_fail"
                    else "not_applicable"
                ),
            }
        )

    candidate_features = [evidence._raw_features(ca_raw[key]) for key in planned]
    strict_count = sum(
        feature["compliant"] and ca_eval[key]["reasoning_leakage"] == "false"
        for feature, key in zip(candidate_features, planned)
    )
    fence_count = sum(feature["marker_count"] > 0 for feature in candidate_features)
    extra_count = sum(feature["extra_text"] for feature in candidate_features)
    extraction_count = sum(
        ca_pipeline[key]["extraction_status"] == "extracted" for key in planned
    )
    candidate_pass = sum(row["pipeline_corrected_status"] == "pass" for row in ca_eval.values())
    p0_pass = sum(row["pipeline_corrected_status"] == "pass" for row in p0_eval.values())
    rescues = transitions["fail_to_pass"]
    regressions = transitions["pass_to_fail"]
    p_value = paired_math.exact_mcnemar_p(rescues, regressions)
    rates = {
        "strict_python_only_compliance_rate": strict_count / 200,
        "code_fence_rate": fence_count / 200,
        "extra_text_rate": extra_count / 200,
        "pipeline_extraction_success_rate": extraction_count / 200,
    }
    format_gate = (
        rates["strict_python_only_compliance_rate"] >= 0.90
        and rates["code_fence_rate"] <= 0.05
        and rates["extra_text_rate"] <= 0.05
        and rates["pipeline_extraction_success_rate"] >= 0.95
    )
    regression_rows = [row for row in rows if row["paired_regression"] == "true"]
    safety_gate = (
        candidate_pass >= p0_pass
        and rescues >= regressions
        and len(regression_rows) == regressions
    )
    protocol_gate = (
        len(ca_raw) == 200
        and all(row.get("transport_complete") is True for row in ca_raw.values())
        and all(row.get("retry_count") == 0 for row in ca_raw.values())
    )
    improvement_claim = (
        format_gate
        and safety_gate
        and protocol_gate
        and rescues > regressions
        and p_value < 0.05
    )
    if improvement_claim:
        claim = "Pipeline correctness improvement supported under the preregistered rule"
    elif format_gate and safety_gate and protocol_gate:
        claim = "direct evaluability improvement and Pipeline-corrected non-inferiority only"
    elif not safety_gate:
        claim = "safety gate failed; Candidate A must not be promoted to official Scaffold v1"
    else:
        claim = "promotion gates not fully satisfied; no promotion claim"
    return {
        "paired_rows": rows,
        "regression_rows": regression_rows,
        "transition_counts": {
            name: transitions[name]
            for name in ("fail_to_fail", "fail_to_pass", "pass_to_fail", "pass_to_pass")
        },
        "p0_pipeline_pass_count": p0_pass,
        "candidate_pipeline_pass_count": candidate_pass,
        "format_rates": rates,
        "reasoning_leakage_count": sum(
            row["reasoning_leakage"] == "true" for row in ca_eval.values()
        ),
        "exact_mcnemar_two_sided_p": p_value,
        "gates": {
            "format_gate": format_gate,
            "pipeline_correctness_safety_gate": safety_gate,
            "protocol_gate": protocol_gate,
        },
        "claim": claim,
        "candidate_status_before_decision": frozen.CANDIDATE_STATUS,
    }


def _csv_bytes(rows: list[dict[str, str]]) -> str:
    fields = tuple(rows[0])
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_analysis(p0_run_id: str, candidate_run_id: str) -> None:
    output_dir = REPO_ROOT / recovery.PAIRED_R002_RELATIVE
    _require(not output_dir.exists(), "paired analysis directory exists; overwrite forbidden")
    result = build_analysis(p0_run_id, candidate_run_id)
    durable_write_text_new(output_dir / "paired_cell_results.csv", _csv_bytes(result["paired_rows"]))
    if result["regression_rows"]:
        regression_csv = _csv_bytes(result["regression_rows"])
    else:
        regression_csv = "task_id,seed,pipeline_transition,regression_disclosure\n"
    durable_write_text_new(output_dir / "all_pipeline_regressions.csv", regression_csv)
    durable_write_text_new(
        output_dir / "paired_analysis_manifest.json",
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p0-run-id", required=True)
    parser.add_argument("--candidate-run-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        write_analysis(args.p0_run_id, args.candidate_run_id)
    except (ProspectiveAnalysisError, PersistenceError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
