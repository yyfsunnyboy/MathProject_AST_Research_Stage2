"""Prepare the immutable 91-cell H2 functional-evaluation preregistration."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1"
)
OUTPUT_DIR = REPO_ROOT / OUTPUT_RELATIVE
STATIC_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_development_static_audit_v1"
)
FOUR_B_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_failure_supply_pilot_analysis_v1"
)
NINE_B_PREP_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
NINE_B_ACCOUNTS_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r003/"
    "h0_h1_accounts.jsonl"
)
NINE_B_RAW_RELATIVE = NINE_B_ACCOUNTS_RELATIVE.parent / "raw_generations.jsonl"
RULE_RELATIVE = Path(
    "agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"
)
RUNNER_RELATIVE = Path(
    "scripts/run_h2_module_assert_quarantine_functional_eval_v1.py"
)
EXPECTED_RULE_SHA = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
EXPECTED_RULE_COMMIT = "7f8c2aedf0a9cd7ac58e813bd775b79ec7956c11"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"


class PreregistrationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreregistrationError(message)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(relative: Path) -> str:
    return _sha((REPO_ROOT / relative).read_bytes())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def _load_static() -> tuple[list[dict[str, str]], dict[str, dict[str, Any]], dict]:
    root = REPO_ROOT / STATIC_RELATIVE
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    _require(manifest["status"] == "development_candidate_not_frozen", "static audit status drift")
    for name, digest in manifest["output_sha256_excluding_manifest"].items():
        _require(_sha((root / name).read_bytes()) == digest, f"static audit hash drift: {name}")
    ledger = _read_csv(root / "decision_ledger.csv")
    transformed = {
        row["source_record_id"]: row
        for row in _read_jsonl(root / "transformed_sources.jsonl")
    }
    _require(len(ledger) == 91 and len(transformed) == 71, "static audit cohort count drift")
    _require(len({row["source_record_id"] for row in ledger}) == 91, "static identity duplicate")
    _require(sum(row["transformed"] == "true" for row in ledger) == 71, "static transformed count drift")
    _require(_sha_file(RULE_RELATIVE) == EXPECTED_RULE_SHA, "H2 rule SHA drift")
    return ledger, transformed, manifest


def _formal_nine_b_eval_path(
    nine_ids: set[str],
) -> tuple[Path, dict[str, dict[str, str]]]:
    preparation = {
        row["cell_identity_sha256"]: row
        for row in _read_csv(REPO_ROOT / NINE_B_PREP_RELATIVE)
    }
    _require(nine_ids <= set(preparation), "9B identity absent from formal preparation")
    paths: set[str] = set()
    selected: dict[str, dict[str, str]] = {}
    marker = "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/"
    for identity in nine_ids:
        row = preparation[identity]
        references = json.loads(row["evidence_references"])
        candidates = [
            ref.split("#", 1)[0]
            for ref in references
            if ref.startswith(marker)
            and "manual_evalplus_run_001/evalplus_results.csv#" in ref
        ]
        _require(len(candidates) == 1, f"9B formal EvalPlus source not unique: {identity}")
        paths.add(candidates[0])
        selected[identity] = row
    _require(len(paths) == 1, "9B cells do not share one formal EvalPlus ledger")
    return Path(paths.pop()), selected


def build_outputs() -> dict[str, bytes]:
    static_ledger, transformed_sources, static_manifest = _load_static()
    four_rows = [row for row in static_ledger if row["cohort"] == "4B_all_module_level_assert_cells"]
    nine_rows = [row for row in static_ledger if row["cohort"] == "9B_formal_Conditional23"]
    _require(len(four_rows) == 68 and len(nine_rows) == 23, "cohort split drift")

    four_root = REPO_ROOT / FOUR_B_RELATIVE
    four_frozen_bytes = (four_root / "frozen_input_manifest.json").read_bytes()
    four_frozen = json.loads(four_frozen_bytes)
    for name, digest in four_frozen["prepared_output_sha256"].items():
        _require(_sha((four_root / name).read_bytes()) == digest, f"4B frozen hash drift: {name}")
    four_results_path = four_root / "manual_h0_evalplus_run_001/h0_evalplus_results.csv"
    four_execution_path = four_results_path.parent / "execution_manifest.json"
    four_execution = json.loads(four_execution_path.read_text(encoding="utf-8"))
    _require(_sha(four_results_path.read_bytes()) == four_execution["results_sha256"], "4B result receipt mismatch")
    _require(four_execution["evalplus_version"] == EXPECTED_EVALPLUS_VERSION, "4B evaluator drift")
    four_results = {row["cell_identity"]: row for row in _read_csv(four_results_path)}
    four_inventory = {
        row["generation_id"]: row
        for row in _read_csv(four_root / "generation_evidence_inventory.csv")
    }

    nine_ids = {row["source_record_id"] for row in nine_rows}
    nine_eval_relative, nine_preparation = _formal_nine_b_eval_path(nine_ids)
    nine_results_path = REPO_ROOT / nine_eval_relative
    nine_execution_path = nine_results_path.parent / "execution_manifest.json"
    nine_execution = json.loads(nine_execution_path.read_text(encoding="utf-8"))
    _require(_sha(nine_results_path.read_bytes()) == nine_execution["results_sha256"], "9B result receipt mismatch")
    _require(nine_execution["evalplus_version"] == EXPECTED_EVALPLUS_VERSION, "9B evaluator drift")
    nine_results = {
        row["program_id"]: row
        for row in _read_csv(nine_results_path)
        if row["healer_account"] == "H0"
    }
    nine_accounts = {
        row["program_id"]: row
        for row in _read_jsonl(REPO_ROOT / NINE_B_ACCOUNTS_RELATIVE)
        if row["healer_account"] == "H0"
    }
    nine_raw = {
        row["generation_id"]: row
        for row in _read_jsonl(REPO_ROOT / NINE_B_RAW_RELATIVE)
    }

    roster: list[dict[str, Any]] = []
    eval_input: list[dict[str, Any]] = []
    for row in sorted(
        static_ledger,
        key=lambda item: (item["cohort"], int(item["cell_index"]), item["source_record_id"]),
    ):
        identity = row["source_record_id"]
        if row["cohort"].startswith("4B"):
            raw_result = four_results.get(identity)
            _require(raw_result is not None, f"4B Raw result missing: {identity}")
            _require(raw_result["evaluation_source_sha256"] == row["source_sha256"], "4B pipeline/result SHA mismatch")
            generation_raw_sha = four_inventory[row["generation_id"]]["raw_response_sha256"]
            raw_authority = str(
                FOUR_B_RELATIVE / "manual_h0_evalplus_run_001/h0_evalplus_results.csv"
            ).replace("\\", "/")
        else:
            prep = nine_preparation[identity]
            _require(prep["program_id"] == row["program_id"], "9B preparation/program mismatch")
            raw_result = nine_results.get(row["program_id"])
            account = nine_accounts.get(row["program_id"])
            _require(raw_result is not None and account is not None, f"9B formal account/result missing: {identity}")
            _require(raw_result["evaluation_source_sha256"] == row["source_sha256"], "9B pipeline/result SHA mismatch")
            _require(account["evaluation_source_sha256"] == row["source_sha256"], "9B account/static SHA mismatch")
            raw_record = nine_raw[account["generation_id"]]
            generation_raw_sha = raw_record["raw_response_sha256"]
            raw_authority = str(nine_eval_relative).replace("\\", "/")

        transformed = row["transformed"] == "true"
        if transformed:
            output = transformed_sources[identity]
            post_sha = output["output_sha256"]
            completion = output["output_source"]
            _require(_sha(completion.encode("utf-8")) == post_sha, "Post-H2 output SHA mismatch")
        else:
            _require(row["abstained"] == "true", "non-transformed cell not abstained")
            _require(row["source_sha256"] == row["output_sha256"], "abstained SHA changed")
            post_sha = row["source_sha256"]
            completion = None

        strict = "pass" if raw_result["base_status"] == raw_result["plus_status"] == "pass" else "fail"
        roster_row = {
            "roster_order": len(roster) + 1,
            "source_record_id": identity,
            "cohort": row["cohort"],
            "cell_index": int(row["cell_index"]),
            "program_id": row["program_id"],
            "generation_id": row["generation_id"],
            "task_id": row["task_id"],
            "seed": int(row["seed"]),
            "condition": row["condition"],
            "model": row["model"],
            "entry_point": row["entry_point"],
            "generation_raw_response_sha256": generation_raw_sha,
            "pipeline_source_sha256": row["source_sha256"],
            "post_h2_source_sha256": post_sha,
            "transformed": transformed,
            "abstained": not transformed,
            "raw_base_status": raw_result["base_status"],
            "raw_plus_status": raw_result["plus_status"],
            "raw_strict_status": strict,
            "raw_result_authority": raw_authority,
            "static_decision_reason": row["reason"],
        }
        roster.append(roster_row)
        if transformed:
            eval_input.append(
                {
                    "evaluation_order": len(eval_input) + 1,
                    "source_record_id": identity,
                    "cohort": row["cohort"],
                    "program_id": row["program_id"],
                    "task_id": row["task_id"],
                    "seed": int(row["seed"]),
                    "entry_point": row["entry_point"],
                    "pipeline_source_sha256": row["source_sha256"],
                    "post_h2_source_sha256": post_sha,
                    "transformed": True,
                    "completion": completion,
                }
            )
    _require(len(roster) == 91 and len(eval_input) == 71, "prepared count drift")
    _require(sum(row["raw_strict_status"] == "pass" and row["cohort"].startswith("4B") and row["transformed"] for row in roster) == 25, "4B transformed PASS control count drift")

    roster_bytes = _jsonl_bytes(roster)
    input_bytes = _jsonl_bytes(eval_input)
    preregistration = {
        "preregistration_id": "h2_module_assert_quarantine_functional_evaluation_v1",
        "status": "preregistered_not_executed",
        "scope": "Stage2_MBPP+_only",
        "rule": {
            "rule_id": "module_assert_entrypoint_selftest_quarantine_v0",
            "commit": EXPECTED_RULE_COMMIT,
            "sha256": EXPECTED_RULE_SHA,
            "pre_evaluation_status": "development_candidate_not_frozen",
            "guard_changes_after_preregistration": "forbidden",
        },
        "counts": {
            "roster": 91,
            "transformed_to_execute": 71,
            "abstained_identity_only": 20,
        },
        "frozen_files": {
            "cell_roster.jsonl": _sha(roster_bytes),
            "post_h2_eval_input.jsonl": _sha(input_bytes),
        },
        "source_authorities": {
            "static_audit_manifest": {
                "path": str(STATIC_RELATIVE / "manifest.json").replace("\\", "/"),
                "sha256": _sha_file(STATIC_RELATIVE / "manifest.json"),
            },
            "four_b_frozen_manifest": {
                "path": str(FOUR_B_RELATIVE / "frozen_input_manifest.json").replace("\\", "/"),
                "sha256": _sha(four_frozen_bytes),
            },
            "four_b_raw_results": {
                "path": str(four_results_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": _sha(four_results_path.read_bytes()),
            },
            "nine_b_formal_raw_results": {
                "path": str(nine_eval_relative).replace("\\", "/"),
                "sha256": _sha(nine_results_path.read_bytes()),
            },
            "nine_b_accounts": {
                "path": str(NINE_B_ACCOUNTS_RELATIVE).replace("\\", "/"),
                "sha256": _sha_file(NINE_B_ACCOUNTS_RELATIVE),
            },
        },
        "evaluator": {
            "package": "evalplus",
            "version": EXPECTED_EVALPLUS_VERSION,
            "engine": "evalplus_0.3.1_check_correctness_subset",
            "dataset": "MBPP+",
            "dataset_version": EXPECTED_DATASET_VERSION,
            "dataset_hash": EXPECTED_DATASET_HASH,
            "runner_path": str(RUNNER_RELATIVE).replace("\\", "/"),
            "runner_sha256": _sha_file(RUNNER_RELATIVE),
        },
        "definitions": {
            "base_pass": "EvalPlus base status equals pass",
            "plus_pass": "EvalPlus plus status equals pass",
            "strict_pass": "base_status == pass AND plus_status == pass",
            "blocker_removed": "Post-H2 transformed AST is valid and EvalPlus returns PASS on either suite or at least one per-test detail, proving evaluation advanced beyond module-load assertion",
            "verified_rescue": "Raw strict FAIL -> Post-H2 strict PASS",
            "preserved_pass": "Raw strict PASS -> Post-H2 strict PASS",
            "regression": "Raw strict PASS -> Post-H2 strict FAIL",
            "partial_repair": "Raw strict FAIL -> Post-H2 strict FAIL AND blocker_removed",
            "unchanged_failure": "Raw strict FAIL -> Post-H2 strict FAIL AND NOT blocker_removed",
            "abstained_unchanged": "H2 abstained AND pipeline/output SHA identical; no execution",
        },
        "execution": {
            "os": "WSL2 Ubuntu/Linux",
            "python": "/home/yehya/.venvs/ast_evalplus/bin/python",
            "python_version": "3.14.4",
            "parallel": 1,
            "sandbox": "EvalPlus untrusted_check isolated subprocess reliability guard",
            "timeout": "EvalPlus 0.3.1 per-test adaptive limit; min_time_limit=1.0 seconds; gt_time_limit_factor=4.0",
            "fast_check": True,
            "retry_resume_overwrite": False,
            "candidate_execution_scope": "exactly 71 transformed roster cells",
            "abstained_execution_count": 0,
            "model_calls": 0,
            "candidate_generations": 0,
        },
        "freeze_criteria": {
            "A": "regression=0 AND every Raw PASS preserved AND verified_rescue>=1 AND determinism/idempotence/AST/provenance all pass => module_assert_entrypoint_selftest_quarantine_v1_frozen",
            "B": "regression=0 AND verified_rescue=0 => development_candidate_not_frozen",
            "C": "regression>0 OR any Raw PASS degrades => development_rejected_pending_review",
            "priority": "C, then A, then B",
            "post_outcome_modification": "forbidden",
        },
        "non_actions": {
            "model_calls": 0,
            "candidate_regeneration": 0,
            "h1_modified": False,
            "h2_modified": False,
            "raw_evidence_modified": False,
            "new_algorithm_scaffold_experiment": False,
        },
    }
    return {
        "cell_roster.jsonl": roster_bytes,
        "post_h2_eval_input.jsonl": input_bytes,
        "preregistration.json": _json_bytes(preregistration),
    }


def write_outputs(check: bool = False) -> None:
    outputs = build_outputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        path = OUTPUT_DIR / name
        if check:
            _require(path.is_file() and path.read_bytes() == content, f"prereg rebuild mismatch: {name}")
        else:
            _require(not path.exists(), f"prereg file already exists: {name}")
            path.write_bytes(content)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_outputs(check=args.check)
    print("preregistration_check=pass" if args.check else "preregistration_written=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
