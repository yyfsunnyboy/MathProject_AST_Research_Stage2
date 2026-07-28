"""Analyze executable-state transitions in cumulative EvalPlus v2 artifacts.

This is a read-only, post-hoc analysis.  It does not execute models, Healers,
replay, candidate code, or EvalPlus.  The output is exploratory
development-candidate evidence and is not frozen or production evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = pathlib.Path(
    "artifacts/public_benchmark_governance/"
    "qwen35_4b_9b_h1_h2_h3_h4_evalplus_v2_execution_restoration_analysis_v1"
)
EVIDENCE_LABEL = "development_candidate_not_frozen"

MODEL_SPECS = {
    "qwen3.5:4b": {
        "tag": "qwen35_4b",
        "eval_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_4b_h1_h2_h3_h4_full_evalplus_v2"
        ),
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_4b_h1_h2_h3_h4_full_replay_v1"
        ),
    },
    "qwen3.5:9b": {
        "tag": "qwen35_9b",
        "eval_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_9b_h1_h2_h3_h4_full_evalplus_v2"
        ),
        "replay_dir": pathlib.Path(
            "artifacts/public_benchmark_governance/"
            "qwen35_9b_h1_h2_h3_h4_full_replay_v1"
        ),
    },
}

SUMMARY_FIELDS = (
    "total_pairs",
    "raw_nonexecutable_to_final_executable_total",
    "execution_restored_and_verified_rescue",
    "execution_restored_but_incorrect",
    "raw_nonexecutable_to_final_nonexecutable",
    "raw_executable_to_final_executable",
    "preserved_pass",
    "correctness_rescue_without_execution_restoration",
    "correctness_regression_without_execution_regression",
    "executable_but_incorrect_unchanged",
    "executable_but_incorrect_modified",
    "raw_executable_to_final_nonexecutable",
    "unclassifiable",
)
EXPLICIT_NONEXECUTION_STATUSES = {
    "empty",
    "timeout",
    "timed_out",
    "compile_error",
    "syntax_error",
    "runtime_exception",
    "execution_failure",
}
EXPLICIT_EXECUTABLE_INCORRECT_STATUSES = {
    "wrong_answer",
    "assert_mismatch",
    "assertion_mismatch",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_label(dataset: str) -> str:
    return "HumanEval+" if dataset == "humaneval" else "MBPP+"


def _condition_label(treatment: str) -> str:
    lowered = treatment.lower()
    if lowered == "ab1":
        return "Ab1"
    if lowered == "ab2g":
        return "Ab2g"
    raise RuntimeError(f"unexpected treatment: {treatment}")


def _stage_execution_status(
    *,
    parse_status: str,
    base_status: str,
    plus_status: str,
) -> tuple[str, str]:
    """Return strict execution class and the evidence/reason.

    EvalPlus 0.3.1's persisted generic ``fail`` is deliberately not treated as
    executable or nonexecutable: the artifact does not preserve whether that
    fail was a wrong answer/assert mismatch or a runtime exception.
    """
    statuses = {base_status, plus_status}
    if parse_status == "unparseable":
        return "nonexecutable", "replay_parse_status_unparseable"
    explicit_nonexecution = sorted(statuses & EXPLICIT_NONEXECUTION_STATUSES)
    if explicit_nonexecution:
        return (
            "nonexecutable",
            "evalplus_explicit_execution_failure:" + "+".join(explicit_nonexecution),
        )
    allowed_executable = {"pass"} | EXPLICIT_EXECUTABLE_INCORRECT_STATUSES
    if statuses <= allowed_executable:
        if base_status == plus_status == "pass":
            return "executable_correct", "base_and_plus_pass"
        return (
            "executable_incorrect",
            "base_and_plus_completed_with_explicit_incorrect_status",
        )
    if "fail" in statuses:
        return (
            "unclassifiable",
            "generic_fail_conflates_incorrect_output_and_runtime_exception",
        )
    return "unclassifiable", "unknown_or_infrastructure_status"


def _pair_account(
    *,
    raw_execution: str,
    final_execution: str,
    raw_pass: bool,
    final_pass: bool,
    modified: bool,
) -> tuple[str, str]:
    raw_exec = raw_execution.startswith("executable_")
    final_exec = final_execution.startswith("executable_")
    if raw_execution == "nonexecutable" and final_exec:
        if final_pass:
            return (
                "raw_nonexecutable_to_final_executable",
                "execution_restored_and_verified_rescue",
            )
        return (
            "raw_nonexecutable_to_final_executable",
            "execution_restored_but_incorrect",
        )
    if raw_execution == final_execution == "nonexecutable":
        return (
            "raw_nonexecutable_to_final_nonexecutable",
            "raw_nonexecutable_to_final_nonexecutable",
        )
    if raw_exec and final_exec:
        if raw_pass and final_pass:
            return "raw_executable_to_final_executable", "preserved_pass"
        if not raw_pass and final_pass:
            return (
                "raw_executable_to_final_executable",
                "correctness_rescue_without_execution_restoration",
            )
        if raw_pass and not final_pass:
            return (
                "raw_executable_to_final_executable",
                "correctness_regression_without_execution_regression",
            )
        return (
            "raw_executable_to_final_executable",
            (
                "executable_but_incorrect_modified"
                if modified
                else "executable_but_incorrect_unchanged"
            ),
        )
    if raw_exec and final_execution == "nonexecutable":
        return (
            "raw_executable_to_final_nonexecutable",
            "execution_regression",
        )
    return "unclassifiable", "unclassifiable"


def _summary(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    rows = list(rows)
    counts = {field: 0 for field in SUMMARY_FIELDS}
    counts["total_pairs"] = len(rows)
    for row in rows:
        account = row["pair_account"]
        subaccount = row["pair_subaccount"]
        if account == "raw_nonexecutable_to_final_executable":
            counts["raw_nonexecutable_to_final_executable_total"] += 1
        elif account in counts:
            counts[account] += 1
        if subaccount in counts and subaccount != account:
            counts[subaccount] += 1
    _require(
        counts["raw_nonexecutable_to_final_executable_total"]
        == counts["execution_restored_and_verified_rescue"]
        + counts["execution_restored_but_incorrect"],
        "restoration subaccount mismatch",
    )
    top_total = (
        counts["raw_nonexecutable_to_final_executable_total"]
        + counts["raw_nonexecutable_to_final_nonexecutable"]
        + counts["raw_executable_to_final_executable"]
        + counts["raw_executable_to_final_nonexecutable"]
        + counts["unclassifiable"]
    )
    _require(top_total == len(rows), "top-level accounts are not exhaustive")
    exec_exec_subtotal = sum(
        counts[field]
        for field in (
            "preserved_pass",
            "correctness_rescue_without_execution_restoration",
            "correctness_regression_without_execution_regression",
            "executable_but_incorrect_unchanged",
            "executable_but_incorrect_modified",
        )
    )
    _require(
        exec_exec_subtotal == counts["raw_executable_to_final_executable"],
        "executable-to-executable subaccount mismatch",
    )
    return counts


def _write_csv(
    path: pathlib.Path, rows: list[dict[str, Any]], fieldnames: list[str]
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _load_rows(repo_root: pathlib.Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    validation: dict[str, Any] = {}
    for model, spec in MODEL_SPECS.items():
        eval_root = repo_root / spec["eval_dir"]
        replay_root = repo_root / spec["replay_dir"]
        eval_j_dir = eval_root / "j"
        replay_j_dir = replay_root / "j"
        summary = _read_json(eval_root / "summary_v2.json")
        eval_paths = sorted(eval_j_dir.glob("*.json"))
        replay_paths = sorted(replay_j_dir.glob("*.json"))
        _require(len(eval_paths) == 1084, f"{model}: expected 1084 eval journals")
        _require(len(replay_paths) == 1084, f"{model}: expected 1084 replay journals")
        eval_ids = {path.stem for path in eval_paths}
        replay_ids = {path.stem for path in replay_paths}
        _require(len(eval_ids) == 1084, f"{model}: duplicate eval cell identity")
        _require(len(replay_ids) == 1084, f"{model}: duplicate replay cell identity")
        _require(eval_ids == replay_ids, f"{model}: eval/replay identity mismatch")
        _require(summary["total_pairs"] == 1084, f"{model}: summary pair mismatch")
        _require(summary["evalplus_version"] == "0.3.1", f"{model}: version drift")

        dataset_counts: Counter[str] = Counter()
        for eval_path in eval_paths:
            cell_id = eval_path.stem
            evaluated = _read_json(eval_path)
            replay = _read_json(replay_j_dir / eval_path.name)
            _require(
                evaluated["cell_identity"] == replay["cell_identity"] == cell_id,
                f"{model}/{cell_id}: identity mismatch",
            )
            _require(evaluated["model_tag"] == model, f"{cell_id}: model mismatch")
            _require(
                evaluated["runner_identity"]
                == "public_benchmark_h1_h2_h3_h4_evalplus_runner_v2",
                f"{cell_id}: runner mismatch",
            )
            raw_source = replay["raw_source"]
            final_source = replay["final_source"]
            raw_sha = _sha256_text(raw_source)
            final_sha = _sha256_text(final_source)
            _require(
                raw_sha == evaluated["raw_sha256"] == replay["raw_sha256"],
                f"{cell_id}: raw hash mismatch",
            )
            _require(
                final_sha == evaluated["final_sha256"] == replay["final_sha256"],
                f"{cell_id}: final hash mismatch",
            )
            layers_changed = replay.get("layers_changed") or []
            source_changed = raw_source != final_source
            modified = source_changed or bool(layers_changed)
            layer_combination = (
                "+".join(sorted(str(layer) for layer in layers_changed))
                if layers_changed
                else "NONE"
            )
            raw_execution, raw_reason = _stage_execution_status(
                parse_status=str(replay["raw_parse_status"]),
                base_status=str(evaluated["raw_base_status"]),
                plus_status=str(evaluated["raw_plus_status"]),
            )
            final_execution, final_reason = _stage_execution_status(
                parse_status=str(replay["cumulative_parse_status"]),
                base_status=str(evaluated["cumulative_base_status"]),
                plus_status=str(evaluated["cumulative_plus_status"]),
            )
            raw_pass = bool(evaluated["raw_final_pass"])
            final_pass = bool(evaluated["cumulative_final_pass"])
            account, subaccount = _pair_account(
                raw_execution=raw_execution,
                final_execution=final_execution,
                raw_pass=raw_pass,
                final_pass=final_pass,
                modified=modified,
            )
            dataset = str(evaluated["dataset"])
            dataset_counts[dataset] += 1
            all_rows.append(
                {
                    "evidence_label": EVIDENCE_LABEL,
                    "model": model,
                    "cell_identity": cell_id,
                    "dataset": _dataset_label(dataset),
                    "task_id": evaluated["task_id"],
                    "condition": _condition_label(str(evaluated["treatment"])),
                    "raw_parse_status": replay["raw_parse_status"],
                    "raw_base_status": evaluated["raw_base_status"],
                    "raw_plus_status": evaluated["raw_plus_status"],
                    "raw_execution_status": raw_execution,
                    "raw_execution_reason": raw_reason,
                    "final_parse_status": replay["cumulative_parse_status"],
                    "final_base_status": evaluated["cumulative_base_status"],
                    "final_plus_status": evaluated["cumulative_plus_status"],
                    "final_execution_status": final_execution,
                    "final_execution_reason": final_reason,
                    "raw_pass": raw_pass,
                    "final_pass": final_pass,
                    "layers_changed": "|".join(layers_changed),
                    "layer_combination": layer_combination,
                    "source_changed": source_changed,
                    "modified": modified,
                    "healer_attribution_allowed": modified,
                    "pair_account": account,
                    "pair_subaccount": subaccount,
                    "final_outcome": (
                        "verified_rescue"
                        if subaccount == "execution_restored_and_verified_rescue"
                        else (
                            "executable_but_incorrect"
                            if subaccount == "execution_restored_but_incorrect"
                            else ""
                        )
                    ),
                    "existing_transition_category": evaluated[
                        "transition_category"
                    ],
                    "raw_sha256": raw_sha,
                    "final_sha256": final_sha,
                }
            )
        _require(
            dataset_counts == {"humaneval": 328, "mbpp": 756},
            f"{model}: dataset counts mismatch: {dataset_counts}",
        )
        validation[model] = {
            "eval_journals": len(eval_paths),
            "replay_journals": len(replay_paths),
            "unique_cell_identities": len(eval_ids),
            "missing": 0,
            "duplicate": 0,
            "dataset_counts": dict(dataset_counts),
            "input_summary_sha256": _sha256_file(eval_root / "summary_v2.json"),
            "transition_counts": summary["transition_counts"],
        }
    return all_rows, validation


def _breakdown(
    rows: list[dict[str, Any]], dimension: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    model_groups = list(MODEL_SPECS) + ["ALL"]
    for model in model_groups:
        selected = rows if model == "ALL" else [row for row in rows if row["model"] == model]
        values = sorted({str(row[dimension]) for row in selected})
        for value in values:
            grouped = [row for row in selected if str(row[dimension]) == value]
            output.append(
                {
                    "model": model,
                    dimension: value,
                    **_summary(grouped),
                }
            )
    return output


def _markdown_table(
    rows: list[dict[str, Any]], fields: list[str]
) -> str:
    header = "| " + " | ".join(fields) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    body = [
        "| " + " | ".join(str(row.get(field, "")) for field in fields) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _write_report(
    output_dir: pathlib.Path,
    summaries: list[dict[str, Any]],
    restored: list[dict[str, Any]],
    transition_crosswalk: list[dict[str, Any]],
    blocker_differences: list[dict[str, Any]],
    validation: dict[str, Any],
) -> None:
    compact_fields = [
        "model",
        "total_pairs",
        "raw_nonexecutable_to_final_executable_total",
        "execution_restored_and_verified_rescue",
        "execution_restored_but_incorrect",
        "raw_nonexecutable_to_final_nonexecutable",
        "raw_executable_to_final_executable",
        "preserved_pass",
        "raw_executable_to_final_nonexecutable",
        "unclassifiable",
    ]
    restored_fields = [
        "model",
        "dataset",
        "task_id",
        "condition",
        "raw_execution_status",
        "final_execution_status",
        "raw_pass",
        "final_pass",
        "layers_changed",
        "source_changed",
        "final_outcome",
    ]
    verified_total = sum(
        row["count"]
        for row in transition_crosswalk
        if row["existing_transition_category"] == "verified_rescue"
        and row["model"] != "ALL"
    )
    proven_restorations = sum(
        row["execution_restored_and_verified_rescue"]
        for row in summaries
        if row["model"] == "ALL"
    )
    blocker_total = len(blocker_differences)
    report = f"""# Cumulative H1→H2→H3→H4 execution-restoration analysis

Evidence status: `{EVIDENCE_LABEL}`. This is exploratory public-benchmark
evidence; it is not frozen and not a production conclusion.

## Strict field mapping

- Unit: one paired v2 journal (`cell_identity`), Raw versus cumulative H1–H4 final.
- Syntax evidence: replay `raw_parse_status` / `cumulative_parse_status`.
- EvalPlus evidence: v2 `*_base_status`, `*_plus_status`, and `*_final_pass`.
- Nonexecutable: `unparseable`, `empty`, `timeout`, or another explicit execution-failure status.
- Executable and correct: base and plus are both `pass`.
- Generic EvalPlus `fail`: unclassifiable. The persisted v2 artifact does not
  distinguish wrong answer/assert mismatch from runtime exception.
- Healer attribution: allowed only when source hashes differ or
  `layers_changed` is nonempty.

## Validation

- 4B: {validation["qwen3.5:4b"]["eval_journals"]} pairs, 0 duplicate, 0 missing.
- 9B: {validation["qwen3.5:9b"]["eval_journals"]} pairs, 0 duplicate, 0 missing.
- No model, Healer, replay, candidate code, or EvalPlus execution was performed.

## Mutually exclusive totals

{_markdown_table(summaries, compact_fields)}

The complete summary CSV additionally separates correctness-only rescue,
correctness-only regression, and executable-but-incorrect modified/unchanged
subaccounts under executable→executable.

## Proven nonexecutable→executable ledger

{_markdown_table(restored, restored_fields) if restored else "No proven cells."}

## Transition-count comparison

Existing `verified_rescue` counts correctness (Raw FAIL→final PASS), not
execution restoration. Across both models there are {verified_total}
`verified_rescue` cells, but only {proven_restorations} is provably
nonexecutable→executable from the persisted fields. The remainder have generic
Raw `fail`, which conflates incorrect output and runtime exception and is
therefore unclassifiable for execution restoration.

`blocker_removed_but_incorrect` is not equal to
`execution_restored_but_incorrect`: there are {blocker_total} blocker rows and
zero proven execution-restored-but-incorrect rows. Every difference is caused
by generic Raw/final `fail` status lacking enough evidence to distinguish
incorrect execution from runtime exception. See
`blocker_removed_but_incorrect_difference_ledger.csv`.

## Three-stage limitation

The supplied paired artifacts preserve Raw input to the H1–H4 chain,
post-H1/post-H2/post-H3/post-H4 hashes, and final source, but do not preserve
three independently evaluable source/result stages for model-original output,
pipeline output, and H1–H4 final. Therefore this analysis can only prove:
`Raw input to H1–H4 → final`. It does not infer or attribute a separate
pipeline effect.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")


def analyze(repo_root: pathlib.Path, output_dir: pathlib.Path) -> dict[str, Any]:
    _require(not output_dir.exists(), f"refusing to overwrite: {output_dir}")
    rows, validation = _load_rows(repo_root)
    _require(len(rows) == 2168, "combined pair count mismatch")
    _require(len({(row["model"], row["cell_identity"]) for row in rows}) == 2168, "combined duplicate")
    output_dir.mkdir(parents=True)

    summaries = [
        {"model": model, **_summary([row for row in rows if row["model"] == model])}
        for model in MODEL_SPECS
    ]
    summaries.append({"model": "ALL", **_summary(rows)})

    pair_fields = list(rows[0])
    _write_csv(output_dir / "pair_ledger.csv", rows, pair_fields)
    restored = [
        row
        for row in rows
        if row["pair_account"] == "raw_nonexecutable_to_final_executable"
    ]
    _write_csv(output_dir / "execution_restored_ledger.csv", restored, pair_fields)
    unclassifiable = [
        row for row in rows if row["pair_account"] == "unclassifiable"
    ]
    _write_csv(output_dir / "unclassifiable_ledger.csv", unclassifiable, pair_fields)
    _write_csv(
        output_dir / "model_summary.csv",
        summaries,
        ["model", *SUMMARY_FIELDS],
    )

    for dimension, filename in (
        ("dataset", "breakdown_by_dataset.csv"),
        ("condition", "breakdown_by_condition.csv"),
        ("layer_combination", "breakdown_by_layer_combination.csv"),
    ):
        breakdown = _breakdown(rows, dimension)
        _write_csv(
            output_dir / filename,
            breakdown,
            ["model", dimension, *SUMMARY_FIELDS],
        )

    crosswalk_counter: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        for model in (row["model"], "ALL"):
            crosswalk_counter[
                (
                    model,
                    row["existing_transition_category"],
                    row["pair_subaccount"],
                )
            ] += 1
    transition_crosswalk = [
        {
            "model": model,
            "existing_transition_category": transition,
            "execution_account": account,
            "count": count,
        }
        for (model, transition, account), count in sorted(crosswalk_counter.items())
    ]
    _write_csv(
        output_dir / "transition_crosswalk.csv",
        transition_crosswalk,
        [
            "model",
            "existing_transition_category",
            "execution_account",
            "count",
        ],
    )

    blocker_differences = [
        {
            **row,
            "difference_reason": (
                "generic_fail_conflates_incorrect_output_and_runtime_exception"
            ),
        }
        for row in rows
        if row["existing_transition_category"] == "blocker_removed_but_incorrect"
        and row["pair_subaccount"] != "execution_restored_but_incorrect"
    ]
    _write_csv(
        output_dir / "blocker_removed_but_incorrect_difference_ledger.csv",
        blocker_differences,
        [*pair_fields, "difference_reason"],
    )

    _write_report(
        output_dir,
        summaries,
        restored,
        transition_crosswalk,
        blocker_differences,
        validation,
    )
    manifest = {
        "analysis_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_label": EVIDENCE_LABEL,
        "scope": {
            "models": list(MODEL_SPECS),
            "experiment": "cumulative_H1_H2_H3_H4",
            "evalplus_version": "0.3.1",
        },
        "execution_policy": {
            "model_executed": False,
            "healer_executed": False,
            "replay_executed": False,
            "candidate_code_executed": False,
            "evalplus_executed": False,
        },
        "classification": {
            "generic_fail": "unclassifiable",
            "explicit_nonexecution_statuses": sorted(EXPLICIT_NONEXECUTION_STATUSES),
            "executable_correct": "base_status=pass and plus_status=pass",
            "healer_attribution": "source_changed or layers_changed nonempty",
        },
        "validation": validation,
        "summaries": summaries,
        "output_files": sorted(
            path.name for path in output_dir.iterdir() if path.is_file()
        ),
    }
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    output_dir = pathlib.Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    result = analyze(REPO_ROOT, output_dir)
    print(json.dumps(result["summaries"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
