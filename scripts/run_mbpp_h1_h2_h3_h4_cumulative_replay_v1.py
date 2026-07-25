#!/usr/bin/env python3
"""H1->H2->H3->H4 deterministic replay, three cohorts kept strictly separate.

  A. Existing600 (600 cells)           -- frozen H1 paired-analysis population
  B. H2 91-cell roster (4B 68 + 9B Conditional23 23) -- independent of A
  C. demo-print original development cohort (4B 200 + 9B 300 = 500) --
     independent of A and B; this is the population the pre-existing
     top_level_literal_only_demo_print_quarantine_v0 evidence was built on.

Deterministic only: source transformation, AST parse, rule/provenance trace,
SHA comparison, and known-pass modification checks against each cohort's own
authoritative raw-status source. No candidate execution, no EvalPlus.

public_assert_fingerprints are computed per task_id directly from the public
MBPP+ prompt text in data/mbpp_plus/tasks.jsonl (reusing
prepare_top_level_demo_print_quarantine_development_v1.public_assert_fingerprints),
never from candidate output, never from any already-known transformed/hit
cell list, and never from Raw PASS/FAIL execution outcome -- H4's own guard
chain (agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py)
contains no reference to execution status; eligibility is purely structural
(H2 provenance + AST content-safety guards).

Eligibility bookkeeping (per cohort, never merged):
  h2_provenance_candidate_count -- cells where H2 itself reports changed=True;
      the only cells H4 can possibly act on.
  h4_eligible_count -- cells (subset of the above) where every H4 guard
      passes. In this rule's deterministic design there is no state where a
      cell passes every guard but is not transformed, so this count is
      always identical to h4_transformed_count; both are reported to make
      that identity externally checkable rather than assumed.
  h4_transformed_count / h4_abstained_count -- as named.

H4_ONLY is structurally impossible under the current stage contract: H4
requires h2_changed=True as its first gate, so every H4 transformation is
necessarily paired with an H2 change, landing in H2_AND_H4 or a
multi-stage class that includes H2. This script asserts that invariant
rather than merely stating it.
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

from agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline import (  # noqa: E402
    run_h1_then_h2_then_h3_then_h4,
)
from agent_tools.finals_rebuild.mbpp_top_level_demo_print_quarantine import (  # noqa: E402
    _is_main_guard,
)
from scripts import prepare_mbpp_existing600_healer_h0_h1 as existing600  # noqa: E402
from scripts import run_mbpp_h1_h2_cumulative_pipeline_v1 as h1h2h3_runner  # noqa: E402
from scripts import build_h2_module_assert_quarantine_static_audit_v1 as h2_static  # noqa: E402
from scripts import (  # noqa: E402
    prepare_top_level_demo_print_quarantine_development_v1 as demo_print_prep,
)

TASKS_RELATIVE = Path("data/mbpp_plus/tasks.jsonl")
H2_FUNCTIONAL_EVAL_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1/paired_cell_ledger.jsonl"
)
ARTIFACT_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/h4_top_level_demo_print_quarantine_development_replay_v1"
)

TRIGGERED_LEDGER_FIELDS = [
    "cell_id",
    "cohort",
    "task_id",
    "h2_provenance_candidate",
    "h4_transformed",
    "raw_known_pass",
    "raw_known_pass_authority",
    "execution_safety_status",
    "input_sha256",
    "h2_input_sha256",
    "post_h2_sha256",
    "post_h3_sha256",
    "final_sha256",
    "h2_moved_assert_line",
    "h4_moved_print_line",
    "public_fingerprint_evidence_path",
    "h2_provenance_confirmed",
    "first_effective_rule",
    "rules_applied",
    "parse_before",
    "parse_after_h1",
    "parse_after_h2",
    "parse_after_h3",
    "parse_after_h4",
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_tasks(repo_root: Path = REPO_ROOT) -> dict[str, dict[str, str]]:
    rows = _read_jsonl(repo_root / TASKS_RELATIVE)
    return {row["task_id"]: row for row in rows}


def _parseable(source: str | None) -> bool:
    if not source:
        return False
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False


def _guard_assert_line(source: str | None) -> int | None:
    """Line number of the Assert inside the (sole) H2-created __main__ guard."""
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if _is_main_guard(node) and node.body and isinstance(node.body[0], ast.Assert):
            return node.body[0].lineno
    return None


def _top_level_print_line(source: str | None) -> int | None:
    """Line number of the (sole) top-level print statement, pre-H2."""
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        ):
            return node.lineno
    return None


def _sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    """Hash the file's actual on-disk bytes, not a text-decoded/re-encoded
    copy -- read_text() applies universal-newline translation on read, which
    silently normalizes CRLF written by write_text() on Windows and produces
    a hash that does not match the real file content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_result_row(
    *,
    cell_id: str,
    cohort: str,
    task_id: str,
    source: str,
    entry_point: str,
    arities: tuple[int, ...],
    truncated: bool,
    prompt: str,
    raw_known_pass: bool | None,
    raw_known_pass_authority: str,
) -> dict[str, Any]:
    fingerprints = demo_print_prep.public_assert_fingerprints(prompt)
    result = run_h1_then_h2_then_h3_then_h4(
        normalized_source=source,
        entry_point=entry_point,
        expected_positional_arities=arities,
        generation_truncated=truncated,
        extraction_unambiguous=True,
        source_complete=not truncated,
        task_id=task_id,
        execute_evalplus=False,
        public_assert_fingerprints=fingerprints,
    )

    h2_provenance_candidate = result.h2.changed
    h2_provenance_confirmed = result.h4.extras.get("guard_results", {}).get(
        "h2_guard_provenance_confirmed", False
    )
    h4_transformed = result.h4.changed

    row = {
        "cell_id": cell_id,
        "cohort": cohort,
        "task_id": task_id,
        "h2_provenance_candidate": h2_provenance_candidate,
        "h4_transformed": h4_transformed,
        "h4_reason": result.h4.reason,
        "raw_known_pass": raw_known_pass,
        "raw_known_pass_authority": raw_known_pass_authority,
        "execution_safety_status": "not_established",
        "input_sha256": result.input_sha256,
        "h2_input_sha256": result.h1_output_sha256,
        "post_h2_sha256": result.h2_output_sha256,
        "post_h3_sha256": result.h3_output_sha256,
        "final_sha256": result.final_sha256,
        "h2_moved_assert_line": (
            _guard_assert_line(result.h3.output_source) if h4_transformed else None
        ),
        "h4_moved_print_line": (
            _top_level_print_line(result.h1.output_source) if h4_transformed else None
        ),
        "public_fingerprint_evidence_path": f"{TASKS_RELATIVE.as_posix()}#{task_id}",
        "h2_provenance_confirmed": h2_provenance_confirmed,
        "transform_class": result.transform_class,
        "first_effective_rule": (
            result.h1.rule_id if result.h1.changed else
            result.h2.rule_id if result.h2.changed else
            result.h3.rule_id if result.h3.changed else
            result.h4.rule_id if result.h4.changed else None
        ),
        "rules_applied": [
            stage.rule_id
            for stage in (result.h1, result.h2, result.h3, result.h4)
            if stage.changed
        ],
        "parse_before": _parseable(source),
        "parse_after_h1": _parseable(result.h1.output_source),
        "parse_after_h2": _parseable(result.h2.output_source),
        "parse_after_h3": _parseable(result.h3.output_source),
        "parse_after_h4": _parseable(result.h4.output_source),
    }
    return row


def _cohort_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    cohort_size = len(results)
    h2_provenance_candidate_count = sum(1 for r in results if r["h2_provenance_candidate"])
    h4_eligible_count = sum(
        1
        for r in results
        if r["h2_provenance_candidate"] and r["h4_transformed"]
    )
    h4_transformed_count = sum(1 for r in results if r["h4_transformed"])
    assert h4_eligible_count == h4_transformed_count, (
        "h4_eligible_count must equal h4_transformed_count in this deterministic "
        "rule (no guard-passed-but-not-transformed state exists); mismatch "
        "indicates a bug, not a reporting choice"
    )
    h4_abstained_count = cohort_size - h4_transformed_count

    for r in results:
        if r["h4_transformed"]:
            assert r["h2_provenance_candidate"], "H4 transformed without H2 provenance candidacy"
            assert "H2" in r["transform_class"], (
                f"H4 transformed cell has transform_class={r['transform_class']!r} "
                "without H2 in it -- contradicts H2-provenance-gated design"
            )

    transform_classes = dict(sorted(Counter(r["transform_class"] for r in results).items()))
    h4_only_present = transform_classes.get("H4_ONLY", 0)
    assert h4_only_present == 0, "H4_ONLY observed -- contradicts structural-impossibility claim"

    parse_rescue_by_stage = {
        "h1": sum(1 for r in results if not r["parse_before"] and r["parse_after_h1"]),
        "h2": sum(1 for r in results if r["parse_after_h1"] is False and r["parse_after_h2"]),
        "h3": sum(1 for r in results if r["parse_after_h2"] is False and r["parse_after_h3"]),
        "h4": sum(1 for r in results if r["parse_after_h3"] is False and r["parse_after_h4"]),
    }

    transformed_known_pass = sum(
        1 for r in results if r["h4_transformed"] and r["raw_known_pass"] is True
    )
    preserved_known_pass_end_to_end = sum(
        1
        for r in results
        if r["raw_known_pass"] is True and r["final_sha256"] == r["input_sha256"]
    )

    return {
        "cohort_size": cohort_size,
        "h2_provenance_candidate_count": h2_provenance_candidate_count,
        "h4_eligible_count": h4_eligible_count,
        "h4_transformed_count": h4_transformed_count,
        "h4_abstained_count": h4_abstained_count,
        "h4_only_structurally_impossible_under_current_stage_contract": True,
        "h4_only_observed_count": h4_only_present,
        "transform_classes": transform_classes,
        "parse_rescue_by_stage": parse_rescue_by_stage,
        "parse_rescue_total": sum(parse_rescue_by_stage.values()),
        "transformed_known_pass": transformed_known_pass,
        "preserved_known_pass_end_to_end_unchanged_bytes": preserved_known_pass_end_to_end,
        "execution_safety_status": "not_established",
        "new_execution_regression": "not_evaluated",
        "note_on_transformed_known_pass": (
            "transformed_known_pass counts cells whose SOURCE BYTES changed and "
            "whose raw status is known PASS; H4's own function_segments_unchanged "
            "guard structurally guarantees the tested function body is "
            "byte-identical, but whether the transformed source still evaluates "
            "to PASS is NOT verified in this round (no EvalPlus execution)."
        ),
    }


def _abstain_reason_distribution(results: list[dict[str, Any]]) -> dict[str, int]:
    return dict(
        sorted(Counter(r["h4_reason"] for r in results if not r["h4_transformed"]).items())
    )


# ---------------------------------------------------------------------------
# Cohort A: Existing600
# ---------------------------------------------------------------------------


def replay_existing600(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    tasks = _load_tasks(repo_root)
    programs = h1h2h3_runner.iter_existing600_programs(repo_root)
    results = []
    for program in programs:
        task_id = program["task_id"]
        prompt = tasks[task_id]["prompt"]
        row = _build_result_row(
            cell_id=program["program_id"],
            cohort="Existing600",
            task_id=task_id,
            source=program["normalized_source"],
            entry_point=program["expected_entry_point"],
            arities=program["expected_positional_arities"],
            truncated=program["generation_truncated"],
            prompt=prompt,
            raw_known_pass=program["h0_pass"],
            raw_known_pass_authority=(
                "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
                "paired_analysis_run_001/paired_cell_results.csv"
            ),
        )
        results.append(row)
    return {"stats": _cohort_stats(results), "abstain_reasons": _abstain_reason_distribution(results), "results": results}


# ---------------------------------------------------------------------------
# Cohort B: H2 91-cell roster (4B 68 + 9B Conditional23 23)
# ---------------------------------------------------------------------------


def _load_h2_roster_sources(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """generation_id -> raw pre-H1 source text, for exactly the 91-cell roster.

    Reuses h2_static's own path constants (not new guesses) to reopen the
    same underlying jsonl files _four_b_rows/_nine_b_rows already read, so
    the raw text is recovered without duplicating any decision logic.
    """
    sources: dict[str, str] = {}

    four_b_root = repo_root / h2_static.FOUR_B_RELATIVE
    for row in _read_jsonl(four_b_root / "h0_evalplus_input.jsonl"):
        sources[row["generation_id"]] = row["completion"]

    nine_b_roster_root = repo_root / h2_static.NINE_B_ROSTER_RELATIVE
    roster = _read_csv(nine_b_roster_root / "conditional23_candidate_roster.csv")
    account_paths = {row["pipeline_corrected_artifact_path"] for row in roster}
    assert len(account_paths) == 1, "Conditional23 has multiple account sources"
    accounts_relative = Path(account_paths.pop())
    for row in _read_jsonl(repo_root / accounts_relative):
        if row.get("healer_account") == "H0":
            sources[row["generation_id"]] = row["evaluation_source"]

    return sources


def replay_h2_roster(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    tasks = _load_tasks(repo_root)
    four_b, _ = h2_static._four_b_rows(tasks)
    nine_b, _ = h2_static._nine_b_rows(tasks)
    roster_rows = four_b + nine_b
    assert len(roster_rows) == 91, f"H2 roster size drift: {len(roster_rows)}"

    source_by_generation_id = _load_h2_roster_sources(repo_root)
    raw_status_ledger = {
        row["source_record_id"]: row["raw_strict_status"]
        for row in _read_jsonl(repo_root / H2_FUNCTIONAL_EVAL_LEDGER)
    }

    results = []
    for row in roster_rows:
        generation_id = row["generation_id"]
        source = source_by_generation_id.get(generation_id)
        if source is None:
            continue
        task_id = row["task_id"]
        prompt = tasks[task_id]["prompt"]
        try:
            _, arities = existing600._prompt_contract(prompt)
        except Exception:
            arities = (1,)
        truncated = row.get("diagnostic_source_incomplete", False)
        raw_status = raw_status_ledger.get(row["source_record_id"])
        result_row = _build_result_row(
            cell_id=row["source_record_id"],
            cohort=row["cohort"],
            task_id=task_id,
            source=source,
            entry_point=row["entry_point"],
            arities=arities,
            truncated=truncated,
            prompt=prompt,
            raw_known_pass=(raw_status == "pass") if raw_status is not None else None,
            raw_known_pass_authority=str(H2_FUNCTIONAL_EVAL_LEDGER).replace("\\", "/"),
        )
        results.append(result_row)
    return {"stats": _cohort_stats(results), "abstain_reasons": _abstain_reason_distribution(results), "results": results}


# ---------------------------------------------------------------------------
# Cohort C: demo-print original development cohort (4B 200 + 9B 300 = 500)
# ---------------------------------------------------------------------------


def replay_demo_print_cohort(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    tasks = _load_tasks(repo_root)
    records = demo_print_prep.four_b_records(repo_root, tasks) + demo_print_prep.nine_b_records(
        repo_root, tasks
    )
    assert len(records) == 500, f"demo-print cohort size drift: {len(records)}"

    results = []
    for row in records:
        task_id = row["task_id"]
        prompt = tasks[task_id]["prompt"]
        try:
            _, arities = existing600._prompt_contract(prompt)
        except Exception:
            arities = (1,)
        raw_result = row["raw_result"]
        raw_known_pass = None
        if raw_result:
            raw_known_pass = (
                raw_result["base_status"] == "pass" and raw_result["plus_status"] == "pass"
            )
        result_row = _build_result_row(
            cell_id=row["cell_id"],
            cohort=row["cohort"],
            task_id=task_id,
            source=row["source"],
            entry_point=row["entry_point"],
            arities=arities,
            truncated=not row["source_complete"],
            prompt=prompt,
            raw_known_pass=raw_known_pass,
            raw_known_pass_authority=row["raw_result_authority"],
        )
        results.append(result_row)
    return {"stats": _cohort_stats(results), "abstain_reasons": _abstain_reason_distribution(results), "results": results}


# ---------------------------------------------------------------------------
# Artifact writing
# ---------------------------------------------------------------------------


def write_development_artifacts(
    output: dict[str, dict[str, Any]], repo_root: Path = REPO_ROOT
) -> dict[str, str]:
    """Write summary.json, triggered_cell_ledger.csv, abstain_reason_distribution.json,
    and replay_manifest.json under ARTIFACT_OUTPUT_RELATIVE. Returns {filename: sha256}.
    """
    out_dir = repo_root / ARTIFACT_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        cohort_key: cohort_data["stats"] for cohort_key, cohort_data in output.items()
    }
    summary["cross_cohort_note"] = (
        "Existing600 (A), H2 91-cell roster (B), and the demo-print original "
        "500-cell cohort (C) are independent populations and are never summed "
        "into a single count. Each cohort's stats above are self-contained."
    )
    summary["fixed_conclusions"] = {
        "evalplus_executed": False,
        "new_verified_rescue": 0,
        "new_execution_regression": "not_evaluated",
        "qualification_status": "development_candidate_not_frozen",
        "engineering_status": "functionally_demonstrated",
        "execution_safety_status": "not_established",
    }

    abstain_distributions = {
        cohort_key: cohort_data["abstain_reasons"] for cohort_key, cohort_data in output.items()
    }

    ledger_rows = []
    for cohort_key, cohort_data in output.items():
        for r in cohort_data["results"]:
            if r["h4_transformed"]:
                ledger_rows.append(
                    {
                        field: (
                            ";".join(r[field]) if field == "rules_applied" else r.get(field)
                        )
                        for field in TRIGGERED_LEDGER_FIELDS
                    }
                )

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    ledger_path = out_dir / "triggered_cell_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIGGERED_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(ledger_rows)

    abstain_path = out_dir / "abstain_reason_distribution.json"
    abstain_path.write_text(
        json.dumps(abstain_distributions, indent=2, sort_keys=True), encoding="utf-8"
    )

    manifest = {
        "artifact_id": "h4_top_level_demo_print_quarantine_development_replay_v1",
        "purpose": (
            "Deterministic H1->H2->H3->H4 replay across three independent "
            "cohorts; no model calls, no EvalPlus, no candidate execution."
        ),
        "generator_script": "scripts/run_mbpp_h1_h2_h3_h4_cumulative_replay_v1.py",
        "rule_files": {
            "h4": "agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py",
            "pipeline": "agent_tools/finals_rebuild/mbpp_h1_h2_cumulative_pipeline.py",
        },
        "cohorts": {
            "Existing600": {"size": 600, "authority": "healer_h0_h1_functional_evaluation_v1"},
            "H2_roster": {"size": 91, "authority": "h2_module_assert_quarantine_development_static_audit_v1"},
            "demo_print_cohort": {"size": 500, "authority": "top_level_demo_print_quarantine_development_v1"},
        },
        "public_assert_fingerprint_source": "data/mbpp_plus/tasks.jsonl (public prompt text only; no hidden tests/canonical solutions per dataset_manifest.json)",
        "eligibility_uses_execution_outcome": False,
        "model_calls": 0,
        "evalplus_executions": 0,
        "candidate_executions": 0,
        "fixed_conclusions": {
            "evalplus_executed": False,
            "new_verified_rescue": 0,
            "new_execution_regression": "not_evaluated",
            "qualification_status": "development_candidate_not_frozen",
            "engineering_status": "functionally_demonstrated",
            "execution_safety_status": "not_established",
        },
    }
    manifest["output_files_sha256"] = {
        "summary.json": _sha256_file(summary_path),
        "triggered_cell_ledger.csv": _sha256_file(ledger_path),
        "abstain_reason_distribution.json": _sha256_file(abstain_path),
    }
    # replay_manifest.json intentionally never records a hash of itself here
    # (that would be circular: the hash would change the bytes, which would
    # change the hash). Its own on-disk hash is reported by the caller after
    # this function returns, computed the same way as the other three files.
    manifest_path = out_dir / "replay_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "summary.json": manifest["output_files_sha256"]["summary.json"],
        "triggered_cell_ledger.csv": manifest["output_files_sha256"]["triggered_cell_ledger.csv"],
        "abstain_reason_distribution.json": manifest["output_files_sha256"]["abstain_reason_distribution.json"],
        "replay_manifest.json": _sha256_file(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="H1->H2->H3->H4 deterministic replay (3 separate cohorts)")
    parser.add_argument("--write-artifacts", action="store_true", help="Persist formal development artifacts")
    args = parser.parse_args()

    output: dict[str, Any] = {}
    print("Replaying cohort A: Existing600 (600 cells)...", file=sys.stderr)
    output["existing600"] = replay_existing600()
    print(f"  stats: {output['existing600']['stats']}", file=sys.stderr)

    print("Replaying cohort B: H2 91-cell roster...", file=sys.stderr)
    output["h2_roster"] = replay_h2_roster()
    print(f"  stats: {output['h2_roster']['stats']}", file=sys.stderr)

    print("Replaying cohort C: demo-print original development cohort (500 cells)...", file=sys.stderr)
    output["demo_print_cohort"] = replay_demo_print_cohort()
    print(f"  stats: {output['demo_print_cohort']['stats']}", file=sys.stderr)

    if args.write_artifacts:
        shas = write_development_artifacts(output)
        print("Artifact SHA-256:", file=sys.stderr)
        for name, sha in shas.items():
            print(f"  {name}: {sha}", file=sys.stderr)
    else:
        print(json.dumps({k: v["stats"] for k, v in output.items()}, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
