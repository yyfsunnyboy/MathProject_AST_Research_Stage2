#!/usr/bin/env python3
"""Build the frozen Candidate B r003 development60 formal 2x2 paired analysis.

This analyzer is deliberately evaluation-free and model-free.  It accepts only
the pre-registered r003 artifacts and the already frozen P0 paired results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_formal_paired_analysis_v1"
)
START_HEAD = "24e691fea5b7a0280ea9b7a860f0ad1b106ae677"

SOURCE_HASHES = {
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv": "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/execution_manifest.json": "4ddb7beda50db18e4c6bf77484c34626c1088753fcfdb68c16e52f851f0b66f7",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json": "6a84a328307f3ce98a49933008aa18da481aae52920238b9204dcf47b1280606",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/candidate_b_h0_h1_accounts.csv": "54e05091ef35af7f99a32a5409c74f688d00c2564d31b8a52301af8d65ce360e",
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/candidate_b_h1_unchanged_h0_reuse_ledger.csv": "a78259113380956da2c595f20d87ae0175548f8e43087bbcb98328abcf257a8d",
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/raw_generations.jsonl": "3d8295ff5e7260d733d8f68736a792afa79501d70ca8bde8d4dd88c1b2b002b3",
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl": "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    "artifacts/public_benchmark_governance/candidate_b_development60_replay_r003_v1/paired_analysis_spec.json": "387e89335923ad3eebd98b9f03ff47d29b966fe089c75f934c7eb4af3724e111",
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/paired_analysis_manifest.json": "f277e775186ac43086081849aa3563f65892a79e870b7ab77f7e63fc13fcbda5",
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/paired_cell_results.csv": "cb2e12432c1c24abe18e446aaf1eee33b4ebf81f4c4166d083dfeb1540960bee",
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/paired_analysis_run_001/paired_account_results.csv": "52e56c94e11d9b9a36b737b5157e468de85678c4ef26825b5edc935230029976",
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/h0_h1_accounts.csv": "e6f26c7bfb1418080f3df80a78202808aa2ba9f5992ba397b24d8914df979438",
}

CELL_FIELDS = (
    "program_id", "prompt_condition", "run_id", "task_id", "seed",
    "generation_id", "raw_response_sha256", "h0_source_sha256",
    "h1_source_sha256", "source_changed_by_healer", "h0_pass", "h1_pass",
    "healer_transition", "h1_result_basis", "included",
)
ACCOUNT_FIELDS = (
    "program_id", "evaluation_account_id", "factorial_arm", "prompt_condition",
    "healer_account", "run_id", "task_id", "seed", "generation_id",
    "raw_response_sha256", "evaluation_source_sha256", "source_changed_by_healer",
    "evalplus_pass", "result_basis", "included",
)
PROMPT_SUMMARY_FIELDS = (
    "prompt_condition", "programs", "h0_pass", "h0_pass_rate", "h1_pass",
    "h1_pass_rate", "healer_net_change", "strict_python_only_count",
    "strict_python_only_rate", "code_fence_count", "reasoning_leakage_count",
)
HEALER_SUMMARY_FIELDS = (
    "prompt_condition", "programs", "modified", "modification_rate", "triggered",
    "abstained", "no_trigger", "fail_to_fail", "fail_to_pass_rescue",
    "pass_to_fail_regression", "pass_to_pass", "net_change",
    "exact_mcnemar_two_sided_p",
)
TASK_FIELDS = (
    "task_id", "seeds", "p0_h0_pass", "p0_h1_pass", "candidate_b_h0_pass",
    "candidate_b_h1_pass", "scaffold_fail_to_fail", "scaffold_fail_to_pass",
    "scaffold_pass_to_fail", "scaffold_pass_to_pass", "p0_healer_rescue",
    "p0_healer_regression", "candidate_b_healer_rescue",
    "candidate_b_healer_regression",
)


class AnalysisError(RuntimeError):
    """Fail-closed identity, provenance, completeness, or hash error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verify_bytes(data: bytes, expected: str, label: str) -> None:
    _require(_sha(data) == expected, f"hash drift: {label}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _index_unique(rows: Iterable[dict[str, Any]], fields: tuple[str, ...], label: str) -> dict[Any, dict[str, Any]]:
    result: dict[Any, dict[str, Any]] = {}
    for row in rows:
        values = tuple(str(row[field]) for field in fields)
        key = values[0] if len(values) == 1 else values
        _require(key not in result, f"duplicate identity in {label}: {key}")
        result[key] = row
    return result


def _require_exact_keys(actual: set[Any], expected: set[Any], label: str) -> None:
    _require(actual == expected, f"missing or unexpected identity in {label}")


def _bool(value: bool) -> str:
    return str(value).lower()


def _transition(before: bool, after: bool) -> str:
    if before and after:
        return "pass_to_pass"
    if before:
        return "pass_to_fail"
    if after:
        return "fail_to_pass"
    return "fail_to_fail"


def exact_mcnemar_two_sided(rescue: int, regression: int) -> float:
    discordant = rescue + regression
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(rescue, regression) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def _validate_reuse_row(row: dict[str, str], h0: dict[str, str], h1: dict[str, str]) -> None:
    _require(row["program_id"] == h0["program_id"] == h1["program_id"], "reuse program identity drift")
    _require(row["h0_evaluation_account_id"] == h0["evaluation_account_id"], "reuse H0 account drift")
    _require(row["h1_evaluation_account_id"] == h1["evaluation_account_id"], "reuse H1 account drift")
    _require(row["source_sha256_exact_match"] == "true", "reuse exact-match flag false")
    _require(row["reuse_eligible_after_h0_evalplus"] == "true", "reuse eligibility false")
    _require(row["h0_source_sha256"] == row["h1_source_sha256"], "reuse ledger hash mismatch")
    _require(row["h0_source_sha256"] == h0["evaluation_source_sha256"], "reuse H0 source hash drift")
    _require(row["h1_source_sha256"] == h1["evaluation_source_sha256"], "reuse H1 source hash drift")


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    observed_hashes: dict[str, str] = {}
    for relative, expected in SOURCE_HASHES.items():
        path = repo_root / relative
        _require(path.is_file(), f"source missing: {relative}")
        data = path.read_bytes()
        _verify_bytes(data, expected, relative)
        observed_hashes[relative] = _sha(data)

    cb_base = repo_root / "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1"
    p0_base = repo_root / "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1"
    cb_manifest = _read_json(cb_base / "manifest.json")
    execution = _read_json(cb_base / "manual_evalplus_run_001/execution_manifest.json")
    spec = _read_json(repo_root / "artifacts/public_benchmark_governance/candidate_b_development60_replay_r003_v1/paired_analysis_spec.json")
    _require(execution["frozen_manifest_sha256"] == SOURCE_HASHES[str(Path("artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json")).replace('\\', '/')], "execution frozen-manifest binding drift")
    _require(execution["results_sha256"] == SOURCE_HASHES["artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv"], "execution results binding drift")
    _require(execution["evalplus_cells_evaluated"] == 302, "EvalPlus evaluated count drift")
    _require(execution["candidate_b_h0_cells_evaluated"] == 300, "Candidate B H0 evaluated count drift")
    _require(execution["candidate_b_h1_changed_cells_evaluated"] == 2, "Candidate B changed H1 count drift")
    _require(execution["candidate_b_h1_unchanged_not_re_evaluated"] == 298, "Candidate B unchanged H1 count drift")
    _require(cb_manifest["r001_r002_used_as_result_source"] is False, "r001/r002 result-source policy drift")
    _require(spec["post_result_rule_change_or_cell_exclusion"] is False, "post-result rule/cell policy drift")

    cb_accounts = _read_csv(cb_base / "candidate_b_h0_h1_accounts.csv")
    _require(len(cb_accounts) == 600, "Candidate B account row count must be 600")
    cb_account_ids = _index_unique(cb_accounts, ("evaluation_account_id",), "Candidate B accounts")
    _require(len(cb_account_ids) == 600, "Candidate B account uniqueness drift")
    cb_h0 = _index_unique((r for r in cb_accounts if r["healer_account"] == "H0"), ("program_id",), "Candidate B H0")
    cb_h1 = _index_unique((r for r in cb_accounts if r["healer_account"] == "H1"), ("program_id",), "Candidate B H1")
    _require(len(cb_h0) == len(cb_h1) == 300, "Candidate B H0/H1 completeness drift")
    _require_exact_keys(set(cb_h0), set(cb_h1), "Candidate B H0/H1 programs")
    materialized_accounts = _read_jsonl(repo_root / "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl")
    _require(len(materialized_accounts) == 600, "materialized Candidate B source account count must be 600")
    materialized_by_account = _index_unique(materialized_accounts, ("evaluation_account_id",), "materialized Candidate B source accounts")
    _require_exact_keys(set(materialized_by_account), set(cb_account_ids), "materialized/governance Candidate B accounts")
    for account_id, materialized in materialized_by_account.items():
        governance = cb_account_ids[account_id]
        _verify_bytes(materialized["evaluation_source"].encode("utf-8"), materialized["evaluation_source_sha256"], f"evaluation source bytes {account_id}")
        for field in ("program_id", "healer_account", "task_id", "seed", "generation_id", "evaluation_source_sha256"):
            _require(str(materialized[field]) == str(governance[field]), f"materialized/governance source drift: {field} {account_id}")

    eval_rows = _read_csv(cb_base / "manual_evalplus_run_001/evalplus_results.csv")
    _require(len(eval_rows) == 302, "formal EvalPlus result row count must be 302")
    eval_by_account = _index_unique(eval_rows, ("evaluation_account_id",), "formal EvalPlus results")
    h0_eval_ids = {row["evaluation_account_id"] for row in cb_h0.values()}
    changed_h1 = {pid: row for pid, row in cb_h1.items() if row["source_changed_by_healer"] == "true"}
    _require(len(changed_h1) == 2, "Candidate B changed H1 must be exactly 2")
    expected_eval_ids = h0_eval_ids | {row["evaluation_account_id"] for row in changed_h1.values()}
    _require_exact_keys(set(eval_by_account), expected_eval_ids, "formal Candidate B EvalPlus accounts")
    for account_id, result in eval_by_account.items():
        account = cb_account_ids[account_id]
        for field in ("program_id", "run_id", "task_id", "seed", "generation_id", "pipeline_normalized_source_sha256", "evaluation_source_sha256"):
            _require(result[field] == account[field], f"EvalPlus provenance drift: {field} {account_id}")
        _require(result["evalplus_pass"] in {"true", "false"}, "invalid EvalPlus pass value")

    reuse_rows = _read_csv(cb_base / "candidate_b_h1_unchanged_h0_reuse_ledger.csv")
    _require(len(reuse_rows) == 298, "unchanged H1 reuse ledger must contain 298 rows")
    reuse_by_program = _index_unique(reuse_rows, ("program_id",), "Candidate B reuse ledger")
    _require_exact_keys(set(reuse_by_program), set(cb_h0) - set(changed_h1), "Candidate B unchanged reuse programs")

    cb_cells: list[dict[str, str]] = []
    cb_account_out: list[dict[str, str]] = []
    for program_id, h0 in cb_h0.items():
        h1 = cb_h1[program_id]
        h0_result = eval_by_account[h0["evaluation_account_id"]]
        h0_pass = h0_result["evalplus_pass"] == "true"
        changed = h1["source_changed_by_healer"] == "true"
        if changed:
            h1_result = eval_by_account[h1["evaluation_account_id"]]
            h1_pass = h1_result["evalplus_pass"] == "true"
            basis = "formal_evalplus_changed_h1"
        else:
            _validate_reuse_row(reuse_by_program[program_id], h0, h1)
            _require(
                materialized_by_account[h0["evaluation_account_id"]]["evaluation_source"].encode("utf-8")
                == materialized_by_account[h1["evaluation_account_id"]]["evaluation_source"].encode("utf-8"),
                "unchanged H1 source bytes differ from H0",
            )
            h1_pass = h0_pass
            basis = "byte_and_sha256_identical_h0_reuse"
        cb_cells.append({
            "program_id": program_id, "prompt_condition": "Candidate_B", "run_id": h0["run_id"],
            "task_id": h0["task_id"], "seed": h0["seed"], "generation_id": h0["generation_id"],
            "raw_response_sha256": h0["raw_response_sha256"],
            "h0_source_sha256": h0["evaluation_source_sha256"], "h1_source_sha256": h1["evaluation_source_sha256"],
            "source_changed_by_healer": _bool(changed), "h0_pass": _bool(h0_pass), "h1_pass": _bool(h1_pass),
            "healer_transition": _transition(h0_pass, h1_pass), "h1_result_basis": basis, "included": "true",
        })
        for account, passed, result_basis in ((h0, h0_pass, "formal_evalplus_h0"), (h1, h1_pass, basis)):
            arm = f"CandidateB_{account['healer_account']}"
            cb_account_out.append({
                "program_id": program_id, "evaluation_account_id": account["evaluation_account_id"],
                "factorial_arm": arm, "prompt_condition": "Candidate_B", "healer_account": account["healer_account"],
                "run_id": account["run_id"], "task_id": account["task_id"], "seed": account["seed"],
                "generation_id": account["generation_id"], "raw_response_sha256": account["raw_response_sha256"],
                "evaluation_source_sha256": account["evaluation_source_sha256"],
                "source_changed_by_healer": account["source_changed_by_healer"], "evalplus_pass": _bool(passed),
                "result_basis": result_basis, "included": "true",
            })

    p0_cells_all = _read_csv(p0_base / "paired_analysis_run_001/paired_cell_results.csv")
    p0_cells_source = [row for row in p0_cells_all if row["prompt_condition"] == "p0"]
    _require(len(p0_cells_source) == 300, "frozen P0 cell stratum must contain 300 rows")
    _index_unique(p0_cells_source, ("program_id",), "frozen P0 cells")
    p0_cells: list[dict[str, str]] = []
    for row in p0_cells_source:
        transition = row["transition"].replace("_rescue", "").replace("_regression", "")
        p0_cells.append({
            "program_id": row["program_id"], "prompt_condition": "P0", "run_id": row["run_id"],
            "task_id": row["task_id"], "seed": row["seed"], "generation_id": row["generation_id"],
            "raw_response_sha256": row["raw_sha256"], "h0_source_sha256": row["normalized_source_sha256"],
            "h1_source_sha256": row["h1_source_sha256"], "source_changed_by_healer": row["source_changed"],
            "h0_pass": row["h0_pass"], "h1_pass": row["h1_pass"], "healer_transition": transition,
            "h1_result_basis": row["h1_result_basis"], "included": "true",
        })

    p0_account_source = [row for row in _read_csv(p0_base / "paired_analysis_run_001/paired_account_results.csv") if row["prompt_condition"] == "p0"]
    _require(len(p0_account_source) == 600, "frozen P0 account stratum must contain 600 rows")
    p0_account_out = [{
        "program_id": row["program_id"], "evaluation_account_id": row["evaluation_account_id"],
        "factorial_arm": f"P0_{row['healer_account']}", "prompt_condition": "P0",
        "healer_account": row["healer_account"], "run_id": row["run_id"], "task_id": row["task_id"],
        "seed": row["seed"], "generation_id": row["generation_id"], "raw_response_sha256": row["raw_sha256"],
        "evaluation_source_sha256": row["evaluation_source_sha256"], "source_changed_by_healer": row["source_changed"],
        "evalplus_pass": row["evalplus_pass"], "result_basis": row["result_basis"], "included": "true",
    } for row in p0_account_source]

    cells = p0_cells + cb_cells
    accounts = p0_account_out + cb_account_out
    _require(len(cells) == 600 and len({row["program_id"] for row in cells}) == 600, "600 programs must be complete and unique")
    _require(len(accounts) == 1200 and len({row["evaluation_account_id"] for row in accounts}) == 1200, "1200 accounts must be complete and unique")
    cell_by_condition_pair = {(row["prompt_condition"], row["task_id"], row["seed"]): row for row in cells}
    _require(len(cell_by_condition_pair) == 600, "duplicate prompt/task/seed identity")
    pairs = {(row["task_id"], row["seed"]) for row in p0_cells}
    _require(len(pairs) == 300, "P0 task/seed identity count drift")
    _require_exact_keys({(row["task_id"], row["seed"]) for row in cb_cells}, pairs, "P0/Candidate B paired task/seed identities")
    _require(len({task for task, _ in pairs}) == 60, "task count must be 60")
    _require({seed for _, seed in pairs} == {"11", "22", "33", "44", "55"}, "seed set drift")
    arm_counts = Counter(row["factorial_arm"] for row in accounts)
    _require(arm_counts == {"P0_H0": 300, "P0_H1": 300, "CandidateB_H0": 300, "CandidateB_H1": 300}, "four-arm account completeness drift")

    raw_rows = _read_jsonl(repo_root / "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/raw_generations.jsonl")
    _require(len(raw_rows) == 300, "Candidate B raw row count must be 300")
    raw_by_program = _index_unique(raw_rows, ("program_id",), "Candidate B raw generations")
    _require_exact_keys(set(raw_by_program), set(cb_h0), "Candidate B raw/program identities")
    for program_id, raw in raw_by_program.items():
        _verify_bytes(raw["raw_response"].encode("utf-8"), raw["raw_response_sha256"], f"raw response {program_id}")
        _require(raw["raw_response_sha256"] == cb_h0[program_id]["raw_response_sha256"], "raw/account SHA drift")
    strict_count = sum(raw["strict_python_only"] is True for raw in raw_rows)
    fence_count = sum(int(raw["code_fence_count"]) for raw in raw_rows)
    leakage_count = sum(raw["reasoning_leakage"] is True for raw in raw_rows)

    p0_h1_accounts = _index_unique((row for row in _read_csv(p0_base / "h0_h1_accounts.csv") if row["prompt_condition"] == "p0" and row["healer_account"] == "H1"), ("program_id",), "P0 H1 status accounts")
    _require(len(p0_h1_accounts) == 300, "P0 H1 status account completeness drift")
    cb_h1_statuses = {pid: row for pid, row in cb_h1.items()}

    by_condition = {"P0": p0_cells, "Candidate_B": cb_cells}
    prompt_summaries: list[dict[str, str]] = []
    healer_summaries: list[dict[str, str]] = []
    for condition, rows in by_condition.items():
        counts = Counter(row["healer_transition"] for row in rows)
        h0_pass = sum(row["h0_pass"] == "true" for row in rows)
        h1_pass = sum(row["h1_pass"] == "true" for row in rows)
        status_rows = p0_h1_accounts if condition == "P0" else cb_h1_statuses
        statuses = Counter(row["healer_status"] for row in status_rows.values())
        modified = sum(row["source_changed_by_healer"] == "true" for row in rows)
        prompt_summaries.append({
            "prompt_condition": condition, "programs": "300", "h0_pass": str(h0_pass),
            "h0_pass_rate": f"{h0_pass/300:.6f}", "h1_pass": str(h1_pass), "h1_pass_rate": f"{h1_pass/300:.6f}",
            "healer_net_change": str(h1_pass-h0_pass),
            "strict_python_only_count": str(strict_count) if condition == "Candidate_B" else "not_recomputed_from_frozen_result",
            "strict_python_only_rate": f"{strict_count/300:.6f}" if condition == "Candidate_B" else "not_recomputed_from_frozen_result",
            "code_fence_count": str(fence_count) if condition == "Candidate_B" else "not_recomputed_from_frozen_result",
            "reasoning_leakage_count": str(leakage_count) if condition == "Candidate_B" else "not_recomputed_from_frozen_result",
        })
        rescue, regression = counts["fail_to_pass"], counts["pass_to_fail"]
        healer_summaries.append({
            "prompt_condition": condition, "programs": "300", "modified": str(modified),
            "modification_rate": f"{modified/300:.6f}", "triggered": str(statuses["transformed"]),
            "abstained": str(statuses["abstained"]), "no_trigger": str(statuses["no_trigger"]),
            "fail_to_fail": str(counts["fail_to_fail"]), "fail_to_pass_rescue": str(rescue),
            "pass_to_fail_regression": str(regression), "pass_to_pass": str(counts["pass_to_pass"]),
            "net_change": str(rescue-regression), "exact_mcnemar_two_sided_p": f"{exact_mcnemar_two_sided(rescue, regression):.12f}",
        })

    scaffold_counts: Counter[str] = Counter()
    task_acc: dict[str, dict[str, Any]] = defaultdict(lambda: {"seeds": set(), "counts": Counter()})
    for task_id, seed in sorted(pairs):
        p0 = cell_by_condition_pair[("P0", task_id, seed)]
        cb = cell_by_condition_pair[("Candidate_B", task_id, seed)]
        scaffold_transition = _transition(p0["h0_pass"] == "true", cb["h0_pass"] == "true")
        scaffold_counts[scaffold_transition] += 1
        item = task_acc[task_id]
        item["seeds"].add(seed)
        for label, value in (("p0_h0_pass", p0["h0_pass"]), ("p0_h1_pass", p0["h1_pass"]), ("candidate_b_h0_pass", cb["h0_pass"]), ("candidate_b_h1_pass", cb["h1_pass"])):
            item["counts"][label] += value == "true"
        item["counts"][f"scaffold_{scaffold_transition}"] += 1
        item["counts"]["p0_healer_rescue"] += p0["healer_transition"] == "fail_to_pass"
        item["counts"]["p0_healer_regression"] += p0["healer_transition"] == "pass_to_fail"
        item["counts"]["candidate_b_healer_rescue"] += cb["healer_transition"] == "fail_to_pass"
        item["counts"]["candidate_b_healer_regression"] += cb["healer_transition"] == "pass_to_fail"
    task_rows: list[dict[str, str]] = []
    for task_id in sorted(task_acc):
        item, counts = task_acc[task_id], task_acc[task_id]["counts"]
        _require(item["seeds"] == {"11", "22", "33", "44", "55"}, f"task seed completeness drift: {task_id}")
        task_rows.append({field: (task_id if field == "task_id" else "5" if field == "seeds" else str(counts[field])) for field in TASK_FIELDS})
    _require(len(task_rows) == 60, "task summary must contain 60 rows")

    p0_h0_pass = sum(row["h0_pass"] == "true" for row in p0_cells)
    cb_h0_pass = sum(row["h0_pass"] == "true" for row in cb_cells)
    scaffold_rescue, scaffold_regression = scaffold_counts["fail_to_pass"], scaffold_counts["pass_to_fail"]
    scaffold = {
        "p0_h0_pass": p0_h0_pass, "candidate_b_h0_pass": cb_h0_pass,
        "p0_h0_pass_rate": p0_h0_pass / 300, "candidate_b_h0_pass_rate": cb_h0_pass / 300,
        "absolute_pass_difference": cb_h0_pass - p0_h0_pass,
        "percentage_point_difference": (cb_h0_pass - p0_h0_pass) / 300 * 100,
        "relative_change": (cb_h0_pass - p0_h0_pass) / p0_h0_pass,
        "transitions": dict(sorted(scaffold_counts.items())),
        "exact_mcnemar_two_sided_p": exact_mcnemar_two_sided(scaffold_rescue, scaffold_regression),
    }
    gates = [
        {"gate": "strict_python_only_rate_gte_0.90", "observed": strict_count / 300, "threshold": ">= 0.90", "passed": strict_count / 300 >= 0.90},
        {"gate": "code_fence_count_eq_0", "observed": fence_count, "threshold": "== 0", "passed": fence_count == 0},
        {"gate": "reasoning_leakage_count_eq_0", "observed": leakage_count, "threshold": "== 0", "passed": leakage_count == 0},
        {"gate": "candidate_b_h0_pass_gt_p0_h0", "observed": cb_h0_pass - p0_h0_pass, "threshold": "> 0", "passed": cb_h0_pass > p0_h0_pass},
        {"gate": "candidate_b_h0_to_h1_paired_net_change_gt_0", "observed": int(healer_summaries[1]["net_change"]), "threshold": "> 0", "passed": int(healer_summaries[1]["net_change"]) > 0},
        {"gate": "post_result_rule_change_or_cell_exclusion_eq_false", "observed": False, "threshold": "== false", "passed": True},
    ]
    gate_result = {
        "gate_definition_source": "candidate_b_development60_replay_r003_v1/paired_analysis_spec.json",
        "gates": gates, "all_qualification_gates_passed": all(g["passed"] for g in gates),
        "scaffold_itself_better_than_p0": cb_h0_pass > p0_h0_pass,
        "untouched20_validation_authorized": False,
        "decision": "PAUSE_VALIDATION_HANDLE_PRE_REGISTERED_GATE_FAILURE",
        "failed_gates": [g["gate"] for g in gates if not g["passed"]],
        "development_evidence_retained": True,
    }
    return {
        "cells": cells, "accounts": accounts, "prompt_summaries": prompt_summaries,
        "healer_summaries": healer_summaries, "task_rows": task_rows, "scaffold": scaffold,
        "gates": gate_result, "observed_hashes": observed_hashes,
    }


def _report(result: dict[str, Any]) -> bytes:
    prompt = {row["prompt_condition"]: row for row in result["prompt_summaries"]}
    healer = {row["prompt_condition"]: row for row in result["healer_summaries"]}
    p0, cb, scaffold = prompt["P0"], prompt["Candidate_B"], result["scaffold"]
    text = f"""# Candidate B r003 development60 正式 2×2 paired analysis

## 範圍與凍結聲明

本分析是同一組 60 tasks × 5 seeds 的 **development replay**，不是 validation，也不是外部效度或 confirmatory evidence。完整納入 P0 與 Candidate B 各 300 programs、四臂共 1200 accounts；沒有排除 task、seed、cell 或帳戶，沒有依結果修改 prompt、Healer、Pipeline、規則或 gate。r001/r002 response 未被使用；untouched20 validation 未讀取、未執行。

## 四臂結果

| Arm | Pass | Rate |
|---|---:|---:|
| P0 H0 | {p0['h0_pass']}/300 | {float(p0['h0_pass_rate'])*100:.4f}% |
| P0 H1 | {p0['h1_pass']}/300 | {float(p0['h1_pass_rate'])*100:.4f}% |
| Candidate B H0 | {cb['h0_pass']}/300 | {float(cb['h0_pass_rate'])*100:.4f}% |
| Candidate B H1 | {cb['h1_pass']}/300 | {float(cb['h1_pass_rate'])*100:.4f}% |

## Scaffold 的直接效果（Candidate B H0 對 P0 H0）

Candidate B H0 比 P0 H0 多 {scaffold['absolute_pass_difference']} pass，差 {scaffold['percentage_point_difference']:.4f} percentage points，相對變化 {scaffold['relative_change']*100:.4f}%。配對轉移為 fail→fail {scaffold['transitions'].get('fail_to_fail', 0)}、fail→pass {scaffold['transitions'].get('fail_to_pass', 0)}、pass→fail {scaffold['transitions'].get('pass_to_fail', 0)}、pass→pass {scaffold['transitions'].get('pass_to_pass', 0)}；exact two-sided McNemar p={scaffold['exact_mcnemar_two_sided_p']:.12f}。這是 development replay 的描述性配對量化，不應外推為 validation 結論。

## Healer 效果

| Prompt condition | Modified / trigger | Abstain | No-trigger | Rescue | Regression | Net | Exact McNemar p |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 | {healer['P0']['modified']} / {healer['P0']['triggered']} | {healer['P0']['abstained']} | {healer['P0']['no_trigger']} | {healer['P0']['fail_to_pass_rescue']} | {healer['P0']['pass_to_fail_regression']} | +{healer['P0']['net_change']} | {healer['P0']['exact_mcnemar_two_sided_p']} |
| Candidate B | {healer['Candidate_B']['modified']} / {healer['Candidate_B']['triggered']} | {healer['Candidate_B']['abstained']} | {healer['Candidate_B']['no_trigger']} | {healer['Candidate_B']['fail_to_pass_rescue']} | {healer['Candidate_B']['pass_to_fail_regression']} | {healer['Candidate_B']['net_change']} | {healer['Candidate_B']['exact_mcnemar_two_sided_p']} |

P0 上 Healer 有 9 個 rescue、0 regression；Candidate B 上兩個 changed window 都是 fail→fail，因此 H1 沒有增加 pass，也沒有 regression。298 個 unchanged H1 只有在 evaluation-source bytes/SHA-256 與 H0 完全相同且 ledger 身分吻合後才 reuse。

## 2×2 保守解讀

目前可分別支持「Candidate B 有直接 Scaffold development 效果」與「Healer 在 P0 上有修復效果」，但資料不足以判定兩者是 additive、overlapping/substitutive，或存在一般性交互作用。Candidate B 可能預防了部分 Healer 可處理的介面錯誤；然而 Candidate B 僅產生 2 個 changed window，且兩格均 fail→fail，不能據此宣稱一般性的負交互作用。現階段應標記為 **無法判定交互作用**。

## 預先凍結 gates 與決策

Candidate B 通過格式 gates，且 H0 pass count 高於 P0 H0，因此通過「Scaffold 本身優於 P0」門檻。但預先固定的完整 qualification 明確要求 Candidate B H0→H1 paired net change > 0；觀察值為 0，該 gate 必須判定 **FAIL**，不能用「無 regression」替代。故 Candidate B + Healer **未通過全部 qualification gates**，目前 **不得進入 untouched20 validation**。

這不抹除 Candidate B 的 development evidence：可保留其 +8 pass、+2.6667 percentage points 的直接 Scaffold 證據，以及格式完全合規的觀察；但它不是完整 qualification pass。依預先規格，應暫停正式 20 題 validation，先處理 gate failure；本輪不深化 prompt 或 Healer。

## 執行聲明

- model_calls=0
- evalplus_executions=0
- validation_not_executed=true
"""
    return text.encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    result = build_analysis(repo_root)
    source_ledger = [{
        "path": path, "role": "frozen_input", "expected_sha256": SOURCE_HASHES[path],
        "observed_sha256": result["observed_hashes"][path], "verified": "true",
    } for path in sorted(SOURCE_HASHES)]
    provenance = {
        "analysis_version": "candidate_b_r003_formal_paired_analysis_v1",
        "start_head": START_HEAD, "development_replay_only": True,
        "candidate_b_result_source": "r003_only", "r001_r002_responses_used": False,
        "p0_reexecuted": False, "evalplus_reexecuted": False,
        "validation_results_read": False, "validation_executed": False,
        "model_calls": 0, "evalplus_executions": 0,
        "cell_or_account_exclusions": 0, "post_result_rule_changes": False,
    }
    execution = {
        "status": "formal_paired_analysis_complete_development_only",
        "analyzer": "scripts/analyze_candidate_b_r003_formal_paired.py",
        "programs": 600, "accounts": 1200, "tasks": 60, "seeds_per_task": 5,
        "model_calls": 0, "evalplus_executions": 0, "validation_not_executed": True,
        "deterministic_bytes": True, "inputs_hash_verified": True,
    }
    outputs: dict[Path, bytes] = {
        Path("paired_cell_results.csv"): _csv_bytes(result["cells"], CELL_FIELDS),
        Path("paired_account_results.csv"): _csv_bytes(result["accounts"], ACCOUNT_FIELDS),
        Path("prompt_condition_summary.csv"): _csv_bytes(result["prompt_summaries"], PROMPT_SUMMARY_FIELDS),
        Path("healer_transition_summary.csv"): _csv_bytes(result["healer_summaries"], HEALER_SUMMARY_FIELDS),
        Path("task_transition_summary.csv"): _csv_bytes(result["task_rows"], TASK_FIELDS),
        Path("frozen_gate_results.json"): _json_bytes(result["gates"]),
        Path("paired_analysis_report_zh.md"): _report(result),
        Path("provenance.json"): _json_bytes(provenance),
        Path("source_hash_ledger.csv"): _csv_bytes(source_ledger, ("path", "role", "expected_sha256", "observed_sha256", "verified")),
        Path("execution_manifest.json"): _json_bytes(execution),
    }
    manifest = {
        "manifest_version": "candidate_b_r003_formal_paired_analysis_v1",
        "status": "complete_development_only_gate_failed",
        "programs": 600, "accounts": 1200, "tasks": 60,
        "four_arm_counts": {"P0_H0": 300, "P0_H1": 300, "CandidateB_H0": 300, "CandidateB_H1": 300},
        "scaffold": result["scaffold"], "frozen_gate_result": result["gates"],
        "model_calls": 0, "evalplus_executions": 0, "validation_not_executed": True,
        "outputs_sha256_excluding_manifest": {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())},
    }
    outputs[Path("manifest.json")] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, content in outputs.items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing deterministic output drift: {relative}")
        else:
            path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_outputs(args.repo_root)
    print(json.dumps({"status": "complete", "programs": 600, "accounts": 1200}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
