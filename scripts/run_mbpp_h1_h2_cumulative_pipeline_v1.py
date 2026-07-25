#!/usr/bin/env python3
"""Validate the cumulative H1→H2→H3 pipeline against Stage2 development artifacts.

Read-only against existing governance outputs. Never overwrites prior artifacts,
never calls a model, never runs EvalPlus, and never touches validation/confirmatory
corpora.
"""

from __future__ import annotations

import argparse
import ast
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

from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import (  # noqa: E402
    RULE_ID as H1_RULE_ID,
    apply_healer,
)
from agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline import (  # noqa: E402
    run_h1_then_h2,
    run_h1_then_h2_then_h3,
    summarize_transform_classes,
)
from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID as H2_RULE_ID,
)
from agent_tools.finals_rebuild.mbpp_h3_empty_suite_pass_insertion import (  # noqa: E402
    RULE_ID as H3_RULE_ID,
)
from scripts import build_h2_module_assert_quarantine_static_audit_v1 as h2_static  # noqa: E402
from scripts import prepare_mbpp_existing600_healer_h0_h1 as existing600  # noqa: E402

H1_PATH = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
H2_PATH = Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py")
H3_PATH = Path("agent_tools/finals_rebuild/mbpp_h3_empty_suite_pass_insertion.py")
PIPELINE_PATH = Path("agent_tools/finals_rebuild/mbpp_h1_h2_cumulative_pipeline.py")
EXPECTED_H1_SHA = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_H2_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"

PAIRED_CELLS = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/paired_cell_results.csv"
)
CHANGED_H1 = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/changed_h1_eval_input.jsonl"
)
H2_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_development_static_audit_v1/decision_ledger.csv"
)
H2_AGG = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1/aggregate_summary.json"
)


class CumulativeValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CumulativeValidationError(message)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_rule_files(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    h1 = _sha_file(repo_root / H1_PATH)
    h2 = _sha_file(repo_root / H2_PATH)
    h3 = _sha_file(repo_root / H3_PATH)
    _require(h1 == EXPECTED_H1_SHA, f"H1 source SHA drift: {h1}")
    _require(h2 == EXPECTED_H2_SHA, f"H2 source SHA drift: {h2}")
    _require(H1_RULE_ID == "entrypoint_alias_unique_arity_compatible_v0", "H1 RULE_ID drift")
    _require(H2_RULE_ID == "module_assert_entrypoint_selftest_quarantine_v0", "H2 RULE_ID drift")
    _require(H3_RULE_ID == "empty_suite_pass_insertion_v0", "H3 RULE_ID drift")
    return {
        H1_PATH.as_posix(): h1,
        H2_PATH.as_posix(): h2,
        H3_PATH.as_posix(): h3,
        PIPELINE_PATH.as_posix(): _sha_file(repo_root / PIPELINE_PATH),
    }


def iter_existing600_programs(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Rebuild Existing600 H1 inputs without writing any outputs."""
    programs: list[dict[str, Any]] = []
    for pairing in existing600.RUNS:
        baseline = existing600._load_run(repo_root, pairing["baseline"])
        treatment = existing600._load_run(repo_root, pairing["treatment"])
        prompt_contracts: dict[str, tuple[str, tuple[int, ...]]] = {}
        for key in baseline["keys"]:
            prompt = baseline["raw"][key]["request"]["messages"][0]["content"]
            contract = existing600._prompt_contract(prompt)
            prior = prompt_contracts.setdefault(key[0], contract)
            _require(prior == contract, f"prompt contract drift: {key[0]}")
        for condition_spec, run in (
            (pairing["baseline"], baseline),
            (pairing["treatment"], treatment),
        ):
            for task_id, seed in run["keys"]:
                raw = run["raw"][(task_id, seed)]
                pipeline = run["pipeline"][(task_id, seed)]
                evaluation = run["evaluation"][(task_id, seed)]
                expected, arities = prompt_contracts[task_id]
                normalized = pipeline["pipeline_corrected_output"]
                truncated = raw.get("generation_metadata", {}).get("done_reason") != "stop"
                h1 = apply_healer(normalized, expected, arities, truncated)
                program_id = existing600._identity_hash(
                    {
                        "run_id": condition_spec["run_id"],
                        "task_id": task_id,
                        "seed": seed,
                        "generation_id": raw["generation_id"],
                    }
                )
                programs.append(
                    {
                        "program_id": program_id,
                        "task_id": task_id,
                        "seed": seed,
                        "run_id": condition_spec["run_id"],
                        "prompt_condition": condition_spec["prompt_condition"],
                        "expected_entry_point": expected,
                        "expected_positional_arities": arities,
                        "generation_truncated": truncated,
                        "normalized_source": normalized,
                        "normalized_source_sha256": pipeline.get(
                            "pipeline_corrected_output_sha256"
                        ),
                        "h1_source": h1.output_source,
                        "h1_source_sha256": h1.output_sha256,
                        "source_changed": h1.status == "transformed",
                        "healer_status": h1.status,
                        "healer_diagnostic": h1.diagnostic,
                        "h0_pass": evaluation["pipeline_corrected_status"] == "pass",
                        "h0_status": evaluation["pipeline_corrected_status"],
                    }
                )
    _require(len(programs) == 600, f"Existing600 program count drift: {len(programs)}")
    _require(
        sum(1 for row in programs if row["source_changed"]) == 41,
        "Existing600 H1 transformed count drift",
    )
    return programs


def validate_h1_nine_rescues(
    programs: list[dict[str, Any]], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    paired = _read_csv(repo_root / PAIRED_CELLS)
    rescues = [row for row in paired if row["transition"] == "fail_to_pass_rescue"]
    _require(len(rescues) == 9, f"expected 9 verified rescues, got {len(rescues)}")
    by_id = {row["program_id"]: row for row in programs}
    frozen_changed = {
        row["program_id"]: row for row in _read_jsonl(repo_root / CHANGED_H1)
    }

    preserved: list[dict[str, Any]] = []
    for rescue in rescues:
        program_id = rescue["program_id"]
        program = by_id[program_id]
        frozen = frozen_changed[program_id]
        _require(program["source_changed"] is True, f"rescue lost H1 change: {program_id}")
        _require(
            program["h1_source_sha256"] == rescue["h1_source_sha256"],
            f"H1 rescue SHA drift vs paired ledger: {program_id}",
        )
        _require(
            hashlib.sha256(frozen["completion"].encode("utf-8")).hexdigest()
            == rescue["h1_source_sha256"],
            f"H1 rescue SHA drift vs frozen changed_h1 input: {program_id}",
        )

        # Cumulative path: H2 must receive H1 output. For original rescues,
        # H2 must not alter the rescued H1 bytes (else stop).
        cumulative = run_h1_then_h2(
            normalized_source=program["normalized_source"],
            entry_point=program["expected_entry_point"],
            expected_positional_arities=program["expected_positional_arities"],
            generation_truncated=program["generation_truncated"],
            extraction_unambiguous=True,
            source_complete=not program["generation_truncated"],
            task_id=program["task_id"],
        )
        _require(
            cumulative.h1.changed is True
            and cumulative.h1.output_sha256 == rescue["h1_source_sha256"],
            f"cumulative H1 diverged from rescue H1: {program_id}",
        )
        _require(
            cumulative.h2.changed is False
            and cumulative.final_sha256 == rescue["h1_source_sha256"],
            f"H2 altered an Existing600 verified-rescue H1 source; stop: {program_id}",
        )
        preserved.append(
            {
                "program_id": program_id,
                "task_id": program["task_id"],
                "h1_source_sha256": rescue["h1_source_sha256"],
                "cumulative_transform_class": cumulative.transform_class,
                "h2_reason": cumulative.h2.reason,
            }
        )
    return {"verified_rescue_count": 9, "preserved": preserved, "regression_on_rescue_set": 0}


def validate_h2_ninety_one(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    frozen_ledger = _read_csv(repo_root / H2_LEDGER)
    _require(len(frozen_ledger) == 91, f"H2 ledger size drift: {len(frozen_ledger)}")
    frozen_transformed = sum(row["transformed"] == "true" for row in frozen_ledger)
    frozen_unchanged = sum(row["transformed"] == "false" for row in frozen_ledger)
    _require(frozen_transformed == 71, "frozen H2 transformed != 71")
    _require(frozen_unchanged == 20, "frozen H2 unchanged != 20")

    rebuilt = h2_static.build_outputs()
    rebuilt_ledger = list(
        csv.DictReader(
            (rebuilt["decision_ledger.csv"].decode("utf-8")).splitlines()
        )
    )
    _require(len(rebuilt_ledger) == 91, "rebuilt H2 ledger size drift")
    rebuilt_transformed = sum(row["transformed"] == "true" for row in rebuilt_ledger)
    rebuilt_unchanged = sum(row["transformed"] == "false" for row in rebuilt_ledger)
    _require(rebuilt_transformed == 71, "rebuilt H2 transformed != 71")
    _require(rebuilt_unchanged == 20, "rebuilt H2 unchanged != 20")
    _require(
        rebuilt["decision_ledger.csv"] == (repo_root / H2_LEDGER).read_bytes(),
        "H2 decision_ledger deterministic rebuild drift",
    )

    agg = json.loads((repo_root / H2_AGG).read_text(encoding="utf-8"))
    combined = agg["cohorts"]["combined"]
    _require(combined["verified_rescue"] == 0, "H2 verified_rescue must remain 0")
    _require(combined["partial_repair"] == 46, "H2 partial_repair count drift")
    _require(combined["transformed"] == 71, "H2 aggregate transformed drift")
    _require(combined["abstained"] == 20, "H2 aggregate abstained drift")
    _require(
        combined["partial_repair"] != combined.get("verified_rescue"),
        "partial_repair must not be conflated with verified_rescue",
    )
    return {
        "roster": 91,
        "transformed": 71,
        "unchanged": 20,
        "partial_repair": 46,
        "verified_rescue": 0,
        "regression": combined["regression"],
        "partial_repair_not_counted_as_verified_rescue": True,
    }


def run_cumulative_on_existing600(
    programs: list[dict[str, Any]],
) -> dict[str, Any]:
    results = []
    for program in programs:
        # Existing600 H1 path treats stop/non-stop as completeness evidence for
        # the saved generation; H2/H3 provenance mirrors that boolean.
        complete = not program["generation_truncated"]
        # Extraction succeeded whenever Pipeline produced a normalized source.
        unambiguous = program["normalized_source"] is not None
        result = run_h1_then_h2_then_h3(
            normalized_source=program["normalized_source"],
            entry_point=program["expected_entry_point"],
            expected_positional_arities=program["expected_positional_arities"],
            generation_truncated=program["generation_truncated"],
            extraction_unambiguous=unambiguous if unambiguous else None,
            source_complete=complete if unambiguous else None,
            task_id=program["task_id"],
        )
        results.append(result)

    classes = summarize_transform_classes(results)
    # Pairwise outcome accounting stays bound to Existing600 paired analyzer:
    # this wiring round does not re-run EvalPlus, so rescue/regression are
    # reported from the frozen paired ledger, not invented here.
    paired = _read_csv(REPO_ROOT / PAIRED_CELLS)
    outcome_counts = Counter(row["transition"] for row in paired)
    return {
        "cells": len(results),
        "transform_classes": classes,
        "h1_changed": sum(1 for row in results if row.h1.changed),
        "h2_changed": sum(1 for row in results if row.h2.changed),
        "h3_changed": sum(1 for row in results if row.h3.changed),
        "h3_triggered": sum(1 for row in results if row.h3.extras.get("triggered", False)),
        "frozen_paired_transitions": dict(sorted(outcome_counts.items())),
        "frozen_verified_rescue": outcome_counts.get("fail_to_pass_rescue", 0),
        "frozen_regression": outcome_counts.get("pass_to_fail", 0),
        "note": (
            "rescue/regression below are frozen Existing600 H1 paired outcomes; "
            "cumulative H1→H2→H3 did not re-execute EvalPlus"
        ),
    }


def _load_h2_cohort_sources(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Rebuild H2 audit cohort sources without writing artifacts."""
    tasks, _dataset = h2_static._tasks()
    four_b, _ = h2_static._four_b_rows(tasks)
    nine_b, _ = h2_static._nine_b_rows(tasks)
    rows = sorted(
        four_b + nine_b,
        key=lambda row: (
            row["cohort"],
            int(row["cell_index"]),
            str(row["source_record_id"]),
        ),
    )
    _require(len(rows) == 91, f"H2 cohort rebuild size drift: {len(rows)}")

    # Recover pre-H2 source text: abstain ⇒ decision.output_source; transform ⇒
    # invert is unavailable, so reload from the same upstream completion bytes
    # that the static audit consumed (matched by source SHA).
    source_by_sha: dict[str, str] = {}
    four_inputs = _read_jsonl(
        repo_root
        / "artifacts/public_benchmark_governance/candidate_b_4b_failure_supply_pilot_analysis_v1/h0_evalplus_input.jsonl"
    )
    for candidate in four_inputs:
        completion = candidate["completion"]
        if h2_static._module_assert_count(completion) == 0:
            continue
        source_by_sha[hashlib.sha256(completion.encode("utf-8")).hexdigest()] = completion

    accounts_path = (
        repo_root
        / "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
        / "runs/mbpp_q35_9b_candidate_b_development60_replay_r003/"
        / "h0_h1_accounts.jsonl"
    )
    for account in _read_jsonl(accounts_path):
        source = account.get("evaluation_source")
        if isinstance(source, str) and source.strip():
            source_by_sha[hashlib.sha256(source.encode("utf-8")).hexdigest()] = source

    out: list[dict[str, Any]] = []
    for row in rows:
        decision = row["decision"]
        source_sha = decision.source_sha256
        if decision.abstained or not decision.transformed:
            source = decision.output_source
        else:
            source = source_by_sha.get(source_sha)
        _require(source is not None, f"missing H2 cohort source for {row['source_record_id']}")
        _require(
            hashlib.sha256(source.encode("utf-8")).hexdigest() == source_sha,
            f"H2 source SHA mismatch for {row['source_record_id']}",
        )
        out.append(
            {
                "source_record_id": row["source_record_id"],
                "cohort": row["cohort"],
                "task_id": row["task_id"],
                "entry_point": row["entry_point"],
                "source": source,
                "extraction_unambiguous": row["extraction_unambiguous"],
                "source_complete": row["source_complete"],
                "generation_truncated": row.get("completion_reason") not in {None, "stop"},
                "prior_h2_transformed": decision.transformed,
                "prior_h2_output_sha256": decision.output_sha256,
            }
        )
    return out


def run_cumulative_on_h2_roster(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    cohort = _load_h2_cohort_sources(repo_root)
    results = []
    for row in cohort:
        source = row["source"]
        arities: tuple[int, ...] = (0,)
        try:
            tree = ast.parse(source)
            funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
            if len(funcs) == 1:
                positional = len(funcs[0].args.posonlyargs) + len(funcs[0].args.args)
                required = positional - len(funcs[0].args.defaults)
                arities = (max(required, 0),)
            elif any(
                isinstance(node, ast.FunctionDef) and node.name == row["entry_point"]
                for node in tree.body
            ):
                target = next(
                    node
                    for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == row["entry_point"]
                )
                positional = len(target.args.posonlyargs) + len(target.args.args)
                required = positional - len(target.args.defaults)
                arities = (max(required, 0),)
        except SyntaxError:
            arities = (0,)

        result = run_h1_then_h2_then_h3(
            normalized_source=source,
            entry_point=row["entry_point"],
            expected_positional_arities=arities,
            generation_truncated=bool(row["generation_truncated"]),
            extraction_unambiguous=row["extraction_unambiguous"],
            source_complete=row["source_complete"],
            task_id=row["task_id"],
        )
        # H2/H3 stages on the cumulative path must reproduce the prior H2 decision
        # whenever H1 is a no-op / abstain on the same bytes.
        if not result.h1.changed:
            _require(
                result.h2.changed is bool(row["prior_h2_transformed"]),
                f"H2 decision drift on {row['source_record_id']}",
            )
            _require(
                result.h2.output_sha256 == row["prior_h2_output_sha256"],
                f"H2 output SHA drift on {row['source_record_id']}",
            )
        results.append(result)
    return {
        "cells": len(results),
        "transform_classes": summarize_transform_classes(results),
        "h1_changed": sum(1 for row in results if row.h1.changed),
        "h2_changed": sum(1 for row in results if row.h2.changed),
        "h3_changed": sum(1 for row in results if row.h3.changed),
        "h3_triggered": sum(1 for row in results if row.h3.extras.get("triggered", False)),
        "basis": "h2_static_audit_source_replay_with_h3",
    }


def validate_all(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    rule_hashes = verify_rule_files(repo_root)
    programs = iter_existing600_programs(repo_root)
    rescue = validate_h1_nine_rescues(programs, repo_root)
    h2 = validate_h2_ninety_one(repo_root)
    existing600_cumulative = run_cumulative_on_existing600(programs)
    h2_cumulative = run_cumulative_on_h2_roster(repo_root)

    return {
        "status": "cumulative_h1_h2_h3_wiring_validated_development_only",
        "model_calls": 0,
        "evalplus_executed": False,
        "rule_sha256": rule_hashes,
        "h1_rule_id": H1_RULE_ID,
        "h2_rule_id": H2_RULE_ID,
        "h3_rule_id": H3_RULE_ID,
        "h1_paths": {
            "implementation": H1_PATH.as_posix(),
            "existing600_paired": PAIRED_CELLS.as_posix(),
        },
        "h2_paths": {
            "implementation": H2_PATH.as_posix(),
            "static_ledger": H2_LEDGER.as_posix(),
            "functional_aggregate": H2_AGG.as_posix(),
        },
        "h3_paths": {
            "implementation": H3_PATH.as_posix(),
        },
        "existing600_h1_rescue_check": rescue,
        "h2_ninety_one_check": h2,
        "existing600_cumulative": existing600_cumulative,
        "h2_roster_cumulative": h2_cumulative,
        "differences_vs_prior": {
            "h1_verified_rescue_preserved": rescue["verified_rescue_count"] == 9,
            "h2_transformed_unchanged_preserved": h2["transformed"] == 71
            and h2["unchanged"] == 20,
            "h2_partial_repair_not_relabeled_rescue": h2[
                "partial_repair_not_counted_as_verified_rescue"
            ],
            "h3_integrated": True,
            "new_evalplus_outcomes": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-development",
        action="store_true",
        help="Replay H1/H2 checks on Existing600 + H2 development artifacts",
    )
    args = parser.parse_args(argv)
    if not args.validate_development:
        parser.error("pass --validate-development (only supported mode this round)")
    result = validate_all()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
