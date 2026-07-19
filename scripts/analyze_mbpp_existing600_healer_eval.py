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
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_mbpp_existing600_healer_eval as evaluation_driver  # noqa: E402

FROZEN_CHANGED_RESULTS_RELATIVE = (
    evaluation_driver.FROZEN_MANIFEST_RELATIVE.parent
    / "manual_evalplus_run_001/changed_h1_evalplus_results.csv"
)
FROZEN_PAIRED_OUTPUT_RELATIVE = (
    evaluation_driver.FROZEN_MANIFEST_RELATIVE.parent / "paired_analysis_run_001"
)
EXPECTED_CHANGED_RESULTS_SHA256 = "4a4b98727e7ae08fb0eabbf74735ce720414b73862fa37c6d9b305b6be683094"

PAIR_FIELDS = (
    "program_id", "development_layer", "prompt_condition", "treatment",
    "run_id", "task_id", "seed", "generation_id", "raw_sha256",
    "normalized_source_sha256", "h1_source_sha256", "source_changed",
    "h0_pass", "h1_pass", "transition", "h1_result_basis",
    "per_cell_accept_revert_or_selective_use",
)
SUMMARY_FIELDS = (
    "stratum", "stratum_type", "programs", "unique_tasks", "changed",
    "unchanged", "rule_triggered", "healer_abstained", "healer_no_trigger",
    "modification_rate", "h0_pass", "h1_pass", "h0_pass_rate",
    "h1_pass_rate", "net_pass_change", "net_pass_rate_change",
    "fail_to_fail", "fail_to_pass_rescue", "pass_to_fail_regression",
    "pass_to_pass", "discordant_pairs", "exact_mcnemar_applicable",
    "exact_mcnemar_two_sided_p",
)

ACCOUNT_RESULT_FIELDS = (
    "program_id", "evaluation_account_id", "healer_account",
    "development_layer", "prompt_condition", "treatment", "run_id",
    "task_id", "seed", "generation_id", "raw_sha256",
    "normalized_source_sha256", "evaluation_source_sha256", "source_changed",
    "evalplus_pass", "result_basis", "pipeline_correction_precedes_healer",
    "pipeline_correction_is_healer", "verified_rescue", "regression",
)

TASK_FIELDS = (
    "task_id", "development_layer", "programs", "changed", "unchanged",
    "p0_programs", "scaffold_like_programs", "h0_pass", "h1_pass",
    "fail_to_fail", "fail_to_pass_rescue", "pass_to_fail_regression",
    "pass_to_pass", "has_verified_rescue", "has_regression",
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


def exact_mcnemar_two_sided(*, rescue: int, regression: int) -> float:
    """Return the exact two-sided sign-test p-value for discordant pairs."""

    discordant = rescue + regression
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(rescue, regression) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def _summary_row(
    *, stratum: str, stratum_type: str, rows: list[dict[str, str]],
    h1_accounts: dict[str, dict[str, str]],
) -> dict[str, str]:
    transitions = Counter(row["transition"] for row in rows)
    programs = len(rows)
    changed = sum(row["source_changed"] == "true" for row in rows)
    h0_pass = sum(row["h0_pass"] == "true" for row in rows)
    h1_pass = sum(row["h1_pass"] == "true" for row in rows)
    rescue = transitions["fail_to_pass_rescue"]
    regression = transitions["pass_to_fail_regression"]
    statuses = Counter(h1_accounts[row["program_id"]]["healer_status"] for row in rows)
    return {
        "stratum": stratum,
        "stratum_type": stratum_type,
        "programs": str(programs),
        "unique_tasks": str(len({row["task_id"] for row in rows})),
        "changed": str(changed),
        "unchanged": str(programs - changed),
        "rule_triggered": str(statuses["transformed"]),
        "healer_abstained": str(statuses["abstained"]),
        "healer_no_trigger": str(statuses["no_trigger"]),
        "modification_rate": f"{changed / programs:.6f}" if programs else "0.000000",
        "h0_pass": str(h0_pass),
        "h1_pass": str(h1_pass),
        "h0_pass_rate": f"{h0_pass / programs:.6f}" if programs else "0.000000",
        "h1_pass_rate": f"{h1_pass / programs:.6f}" if programs else "0.000000",
        "net_pass_change": str(h1_pass - h0_pass),
        "net_pass_rate_change": f"{(h1_pass - h0_pass) / programs:.6f}" if programs else "0.000000",
        "fail_to_fail": str(transitions["fail_to_fail"]),
        "fail_to_pass_rescue": str(rescue),
        "pass_to_fail_regression": str(regression),
        "pass_to_pass": str(transitions["pass_to_pass"]),
        "discordant_pairs": str(rescue + regression),
        "exact_mcnemar_applicable": str(rescue + regression > 0).lower(),
        "exact_mcnemar_two_sided_p": f"{exact_mcnemar_two_sided(rescue=rescue, regression=regression):.12f}",
    }


def build_analysis(
    *, manifest_path: Path, manifest_sha256: str, changed_results_path: Path,
    enforce_frozen_result_path: bool = True,
) -> dict[str, Any]:
    manifest, changed_inputs = evaluation_driver.validate_frozen_inputs(
        manifest_path=manifest_path, manifest_sha256=manifest_sha256, parallel=1
    )
    if enforce_frozen_result_path:
        _require(
            changed_results_path.resolve() == (REPO_ROOT / FROZEN_CHANGED_RESULTS_RELATIVE).resolve(),
            "only the frozen manual EvalPlus result path is accepted",
        )
    result_dir = changed_results_path.parent
    execution_path = result_dir / "execution_manifest.json"
    _require(changed_results_path.name == "changed_h1_evalplus_results.csv", "unexpected changed-results filename")
    _require(execution_path.is_file(), "evaluation execution manifest missing")
    execution = _read_json(execution_path)
    results_bytes = changed_results_path.read_bytes()
    if enforce_frozen_result_path:
        _require(_sha256_bytes(results_bytes) == EXPECTED_CHANGED_RESULTS_SHA256, "changed result frozen SHA-256 drift")
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

    account_results: list[dict[str, str]] = []
    for account in accounts:
        pair = next(row for row in pairs if row["program_id"] == account["program_id"])
        is_h0 = account["healer_account"] == "H0"
        passed = pair["h0_pass"] if is_h0 else pair["h1_pass"]
        basis = (
            "existing_frozen_pipeline_corrected_h0_evaluation"
            if is_h0
            else pair["h1_result_basis"]
        )
        account_results.append({
            "program_id": account["program_id"],
            "evaluation_account_id": account["evaluation_account_id"],
            "healer_account": account["healer_account"],
            "development_layer": account["development_layer"],
            "prompt_condition": account["prompt_condition"],
            "treatment": account["treatment"],
            "run_id": account["run_id"],
            "task_id": account["task_id"],
            "seed": account["seed"],
            "generation_id": account["generation_id"],
            "raw_sha256": account["raw_sha256"],
            "normalized_source_sha256": account["normalized_source_sha256"],
            "evaluation_source_sha256": account["evaluation_source_sha256"],
            "source_changed": account["source_changed"],
            "evalplus_pass": passed,
            "result_basis": basis,
            "pipeline_correction_precedes_healer": "true",
            "pipeline_correction_is_healer": "false",
            "verified_rescue": str(not is_h0 and pair["transition"] == "fail_to_pass_rescue").lower(),
            "regression": str(not is_h0 and pair["transition"] == "pass_to_fail_regression").lower(),
        })
    _require(len(account_results) == 1200, "complete 1200-account reconstruction failed")
    _require(len({row["evaluation_account_id"] for row in account_results}) == 1200, "duplicate reconstructed account identity")

    stratum_specs: list[tuple[str, str, list[dict[str, str]]]] = [
        ("all", "all", pairs),
        ("p0", "prompt_condition", [row for row in pairs if row["prompt_condition"] == "p0"]),
        ("scaffold_like", "prompt_condition", [row for row in pairs if row["prompt_condition"] == "scaffold_like"]),
        ("discovery_development", "development_layer", [row for row in pairs if row["development_layer"] == "discovery_development"]),
        ("expansion_development", "development_layer", [row for row in pairs if row["development_layer"] == "expansion_development"]),
        ("changed", "source_change", [row for row in pairs if row["source_changed"] == "true"]),
        ("unchanged", "source_change", [row for row in pairs if row["source_changed"] == "false"]),
    ]
    for prompt_condition in ("p0", "scaffold_like"):
        for layer in ("discovery_development", "expansion_development"):
            stratum_specs.append((
                f"{prompt_condition}__{layer}",
                "prompt_condition_x_development_layer",
                [row for row in pairs if row["prompt_condition"] == prompt_condition and row["development_layer"] == layer],
            ))
    summaries = [
        _summary_row(stratum=name, stratum_type=kind, rows=rows, h1_accounts=h1_by_program)
        for name, kind, rows in stratum_specs
    ]

    task_rows: list[dict[str, str]] = []
    for task_id in sorted({row["task_id"] for row in pairs}):
        rows = [row for row in pairs if row["task_id"] == task_id]
        transitions = Counter(row["transition"] for row in rows)
        layers = {row["development_layer"] for row in rows}
        _require(len(layers) == 1, f"task spans development layers: {task_id}")
        task_rows.append({
            "task_id": task_id,
            "development_layer": next(iter(layers)),
            "programs": str(len(rows)),
            "changed": str(sum(row["source_changed"] == "true" for row in rows)),
            "unchanged": str(sum(row["source_changed"] == "false" for row in rows)),
            "p0_programs": str(sum(row["prompt_condition"] == "p0" for row in rows)),
            "scaffold_like_programs": str(sum(row["prompt_condition"] == "scaffold_like" for row in rows)),
            "h0_pass": str(sum(row["h0_pass"] == "true" for row in rows)),
            "h1_pass": str(sum(row["h1_pass"] == "true" for row in rows)),
            "fail_to_fail": str(transitions["fail_to_fail"]),
            "fail_to_pass_rescue": str(transitions["fail_to_pass_rescue"]),
            "pass_to_fail_regression": str(transitions["pass_to_fail_regression"]),
            "pass_to_pass": str(transitions["pass_to_pass"]),
            "has_verified_rescue": str(transitions["fail_to_pass_rescue"] > 0).lower(),
            "has_regression": str(transitions["pass_to_fail_regression"] > 0).lower(),
        })
    _require(len(task_rows) == 60, "task-level summary must contain 60 tasks")
    overall = summaries[0]
    rescue = int(overall["fail_to_pass_rescue"])
    regression = int(overall["pass_to_fail_regression"])
    return {
        "pairs": pairs,
        "account_results": account_results,
        "summaries": summaries,
        "task_rows": task_rows,
        "decision": {
            "status": decision_status(rescue=rescue, regression=regression),
            "rescue": rescue,
            "regression": regression,
            "rules_frozen_before_evaluation": True,
            "all_600_accounts_included": True,
            "individual_transformation_withdrawal_or_acceptance": False,
            "source_manifest_sha256": evaluation_driver.FROZEN_MANIFEST_SHA256,
            "changed_results_sha256": _sha256_bytes(results_bytes),
            "exact_mcnemar_two_sided_p": summaries[0]["exact_mcnemar_two_sided_p"],
            "h0_pass": int(summaries[0]["h0_pass"]),
            "h1_pass": int(summaries[0]["h1_pass"]),
            "net_pass_change": int(summaries[0]["net_pass_change"]),
            "tasks_with_verified_rescue": sum(row["has_verified_rescue"] == "true" for row in task_rows),
            "tasks_with_regression": sum(row["has_regression"] == "true" for row in task_rows),
            "source_manifest_status": manifest["status"],
        },
    }


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _report(analysis: dict[str, Any]) -> bytes:
    summary = {row["stratum"]: row for row in analysis["summaries"]}
    overall = summary["all"]
    p0 = summary["p0"]
    scaffold = summary["scaffold_like"]
    discovery = summary["discovery_development"]
    expansion = summary["expansion_development"]
    changed = summary["changed"]
    decision = analysis["decision"]
    text = f"""# Milestone 2J-B：既有600份 development programs Healer H0→H1 paired analysis

## 凍結範圍與帳務

本分析完整納入60個development tasks、600個programs與1200個H0/H1 accounts，沒有排除cell，也沒有依結果調整Healer規則。41個changed H1使用人工WSL EvalPlus 0.3.1結果；559個unchanged H1只在identity與source-state SHA-256完全一致後沿用H0。Pipeline correction先於H0/H1分帳，且不計為Healer；verified rescue只指同一program由H0 fail轉為H1 pass。

## Cell-level主要結果

- H0：{overall['h0_pass']}/600 pass（{float(overall['h0_pass_rate'])*100:.2f}%）。
- H1：{overall['h1_pass']}/600 pass（{float(overall['h1_pass_rate'])*100:.2f}%）。
- 淨變化：+{overall['net_pass_change']} pass，+{float(overall['net_pass_rate_change'])*100:.2f} percentage points。
- fail→pass verified rescue：{overall['fail_to_pass_rescue']}；pass→fail regression：{overall['pass_to_fail_regression']}。
- fail→fail：{overall['fail_to_fail']}；pass→pass：{overall['pass_to_pass']}。
- exact McNemar two-sided p = {overall['exact_mcnemar_two_sided_p']}（discordant pairs={overall['discordant_pairs']}）。
- Healer rule實際修改{overall['changed']}/600（{float(overall['modification_rate'])*100:.2f}%）；abstain {overall['healer_abstained']}；no-trigger {overall['healer_no_trigger']}。
- 41個changed cells中，verified rescue {changed['fail_to_pass_rescue']}、regression {changed['pass_to_fail_regression']}；559個unchanged cells僅作identity reuse。

## P0與Scaffold-like分層

- P0：H0 {p0['h0_pass']}/300 → H1 {p0['h1_pass']}/300；rescue {p0['fail_to_pass_rescue']}、regression {p0['pass_to_fail_regression']}、changed {p0['changed']}。
- Scaffold-like：H0 {scaffold['h0_pass']}/300 → H1 {scaffold['h1_pass']}/300；rescue {scaffold['fail_to_pass_rescue']}、regression {scaffold['pass_to_fail_regression']}、changed {scaffold['changed']}。

Healer的可介入窗口高度集中在P0：39個P0 cells被修改並出現9個verified rescues；Scaffold-like只有2個cells被修改，未觀察到額外rescue或regression。這可保守描述為既有Scaffold-like generations較少留下「唯一函式但entry point名稱缺失」的窄修復窗口；不能據此宣稱一般性的Scaffold × Healer因果交互作用，因本資料是development evidence，且兩種prompt條件對應不同generation outputs。

## Development layer分層

- Discovery development：{discovery['programs']} programs；H0 {discovery['h0_pass']} → H1 {discovery['h1_pass']}；rescue {discovery['fail_to_pass_rescue']}、regression {discovery['pass_to_fail_regression']}。
- Expansion development：{expansion['programs']} programs；H0 {expansion['h0_pass']} → H1 {expansion['h1_pass']}；rescue {expansion['fail_to_pass_rescue']}、regression {expansion['pass_to_fail_regression']}。
- Task-level：{len(analysis['task_rows'])}題完整；有verified rescue的題數為{decision['tasks_with_verified_rescue']}，有regression的題數為{decision['tasks_with_regression']}。

## 保守判定

依評估前固定規則，本輪狀態為`{decision['status']}`：regression為0且rescue至少1，因此此development Healer candidate只取得「可進入獨立prospective qualification」資格，不等於final Healer、不等於validation成功，也不能把個別成功cell用作post-hoc selective acceptance。後續若進行prospective qualification，必須維持相同Healer版本、guards、rule order與完整ITT帳務。
"""
    return text.encode("utf-8")


def build_outputs(
    *, manifest_path: Path, manifest_sha256: str, changed_results_path: Path,
) -> dict[str, bytes]:
    analysis = build_analysis(
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        changed_results_path=changed_results_path,
    )
    outputs = {
        "paired_cell_results.csv": _csv_bytes(analysis["pairs"], PAIR_FIELDS),
        "paired_account_results.csv": _csv_bytes(analysis["account_results"], ACCOUNT_RESULT_FIELDS),
        "stratified_transition_summary.csv": _csv_bytes(analysis["summaries"], SUMMARY_FIELDS),
        "task_transition_summary.csv": _csv_bytes(analysis["task_rows"], TASK_FIELDS),
        "qualification_decision.json": (json.dumps(analysis["decision"], indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "paired_analysis_report_zh.md": _report(analysis),
    }
    execution_path = changed_results_path.parent / "execution_manifest.json"
    analyzer_path = Path(__file__).resolve()
    evaluator_path = Path(evaluation_driver.__file__).resolve()
    source_files = {
        manifest_path.resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes(manifest_path.read_bytes()),
        changed_results_path.resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes(changed_results_path.read_bytes()),
        execution_path.resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes(execution_path.read_bytes()),
        (manifest_path.parent / "h0_h1_accounts.csv").resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes((manifest_path.parent / "h0_h1_accounts.csv").read_bytes()),
        (manifest_path.parent / "changed_h1_eval_input.jsonl").resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes((manifest_path.parent / "changed_h1_eval_input.jsonl").read_bytes()),
        (manifest_path.parent / "unchanged_h0_reuse_ledger.csv").resolve().relative_to(REPO_ROOT).as_posix(): _sha256_bytes((manifest_path.parent / "unchanged_h0_reuse_ledger.csv").read_bytes()),
        analyzer_path.relative_to(REPO_ROOT).as_posix(): _sha256_bytes(analyzer_path.read_bytes()),
        evaluator_path.relative_to(REPO_ROOT).as_posix(): _sha256_bytes(evaluator_path.read_bytes()),
    }
    manifest = {
        "manifest_version": "mbpp_existing600_healer_h0_h1_paired_analysis_v1",
        "status": "paired_analysis_complete_development_only",
        "programs": 600,
        "accounts": 1200,
        "tasks": 60,
        "changed": 41,
        "unchanged": 559,
        "verified_rescue": analysis["decision"]["rescue"],
        "regression": analysis["decision"]["regression"],
        "evalplus_reexecuted": False,
        "model_calls": 0,
        "rules_or_cells_changed_after_results": False,
        "source_sha256": source_files,
        "output_sha256_excluding_manifest": {
            name: _sha256_bytes(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["paired_analysis_manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return outputs


def write_outputs(
    *, manifest_path: Path, manifest_sha256: str, changed_results_path: Path,
    output_dir: Path, check: bool = False,
) -> None:
    _require(
        output_dir.resolve() == (REPO_ROOT / FROZEN_PAIRED_OUTPUT_RELATIVE).resolve(),
        "only the frozen paired-analysis output path is accepted",
    )
    outputs = build_outputs(
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        changed_results_path=changed_results_path,
    )
    if check:
        _require(output_dir.is_dir(), "paired-analysis output directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "paired-analysis output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "analysis output exists; retry/resume/overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        with (output_dir / name).open("xb") as handle:
            handle.write(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--changed-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        write_outputs(
            manifest_path=args.manifest,
            manifest_sha256=args.manifest_sha256,
            changed_results_path=args.changed_results,
            output_dir=args.output_dir,
            check=args.check,
        )
    except (PairedAnalysisError, evaluation_driver.EvaluationDriverError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
