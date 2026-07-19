#!/usr/bin/env python3
"""Freeze Candidate B r003 journals into H0/H1 accounts and EvalPlus prep.

Offline only: validates r003 journals, rebuilds Pipeline/Healer materialization,
and writes a prepared_not_executed EvalPlus package. Never calls a model and
never imports or invokes EvalPlus. Never modifies the r003 run directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import apply_healer  # noqa: E402
from scripts import freeze_mbpp_candidate_b_development60_replay as frozen  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1"
)
R003_RUN_RELATIVE = frozen.RUN_OUTPUT_RELATIVE
R003_GOVERNANCE_RELATIVE = frozen.OUTPUT_RELATIVE
R001_RUN_RELATIVE = frozen.R001_RUN_OUTPUT_RELATIVE
R002_RUN_RELATIVE = frozen.R002_RUN_OUTPUT_RELATIVE
GENERATION_MANIFEST_RELATIVE = R003_GOVERNANCE_RELATIVE / "manifest.json"
EXPECTED_GENERATION_MANIFEST_SHA256 = (
    "e8d0f8e9198848e8708d910f6c859622c272de850a2b1045d62993c114c98fbd"
)
EXPECTED_HEALER_SHA256 = frozen.EXPECTED_HEALER_SHA256
EXPECTED_PIPELINE_SHA256 = frozen.EXPECTED_PIPELINE_SHA256
EXPECTED_CANDIDATE_TEXT_SHA256 = frozen.EXPECTED_CANDIDATE_TEXT_SHA256
EXPECTED_MODEL_DIGEST = frozen.EXPECTED_MODEL_DIGEST
EXPECTED_QUANTIZATION = frozen.EXPECTED_QUANTIZATION
EXPECTED_HEALER_RULE = frozen.EXPECTED_HEALER_RULE
EXPECTED_CANDIDATE_ID = "mbpp_evaluator_blind_healer_candidate_v0"
EXPECTED_DATASET_VERSION = frozen.EXPECTED_DATASET_VERSION
EXPECTED_DATASET_HASH = frozen.EXPECTED_DATASET_HASH
EXPECTED_EVALUATOR_VERSION = "0.3.1"
EXPECTED_EVALUATOR_ENGINE = "evalplus_0.3.1_check_correctness_subset"
EXPECTED_CHANGED_H1 = 2
EXPECTED_UNCHANGED_H1 = 298
EXPECTED_EVALPLUS_CELLS = 302  # 300 H0 + 2 changed H1
SEEDS = frozen.SEEDS
RUN_ID = frozen.RUN_ID

RAW_FIELDS = (
    "cell_index", "task_id", "seed", "sample_index", "generation_id", "program_id",
    "run_id", "raw_response_sha256", "pipeline_normalized_source_sha256",
    "official_prompt_sha256", "composed_prompt_sha256", "candidate_b_text_sha256",
    "model_digest", "quantization", "temperature", "top_p", "top_k", "num_ctx",
    "num_predict", "thinking", "status", "retry_count", "resume", "first_attempt",
    "selective_retry", "single_attempt_no_retry_no_resume",
)

ACCOUNT_FIELDS = (
    "account_index", "factorial_arm", "prompt_condition", "healer_account",
    "program_id", "evaluation_account_id", "run_id", "task_id", "seed",
    "sample_index", "generation_id", "raw_response_sha256",
    "pipeline_normalized_source_sha256", "evaluation_source_sha256",
    "healer_status", "healer_diagnostic", "healer_rule_id", "healer_sha256",
    "source_changed_by_healer", "same_raw_generation_h0_h1",
    "same_pipeline_normalized_input_h0_h1", "h1_byte_identical_to_h0",
    "evaluator_result_used_by_healer", "evalplus_status", "evaluation_disposition",
)

REUSE_FIELDS = (
    "program_id", "h0_evaluation_account_id", "h1_evaluation_account_id",
    "task_id", "seed", "generation_id", "raw_response_sha256",
    "h0_source_sha256", "h1_source_sha256", "source_sha256_exact_match",
    "reuse_eligible_after_h0_evalplus", "reuse_basis",
    "reuse_requires_h0_result_present", "reuse_independent_of_h0_pass_fail",
)


class PreparationError(RuntimeError):
    """Raised before writes when any frozen invariant fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreparationError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _identity_hash(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows
    ).encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _os_fs_path(path: Path) -> str:
    absolute = os.path.abspath(os.fspath(path))
    if os.name != "nt":
        return absolute
    if absolute.startswith("\\\\?\\"):
        return absolute
    if absolute.startswith("\\\\"):
        return "\\\\?\\UNC\\" + absolute[2:]
    return "\\\\?\\" + absolute


def _read_text(path: Path) -> str:
    with open(_os_fs_path(path), encoding="utf-8") as handle:
        return handle.read()


def _read_bytes(path: Path) -> bytes:
    with open(_os_fs_path(path), "rb") as handle:
        return handle.read()


def _journal_names(journal_dir: Path) -> list[str]:
    _require(journal_dir.is_dir(), "r003 journal directory missing")
    return sorted(os.listdir(_os_fs_path(journal_dir)))


def _load_journal(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _forbid_incident_contamination(
    *, generation_ids: set[str], task_ids: set[str], repo_root: Path,
) -> None:
    mapping_path = repo_root / R003_GOVERNANCE_RELATIVE / "r001_r002_r003_identity_mapping.csv"
    mapping = _read_csv(mapping_path)
    r001_ids = {row["r001_generation_id"] for row in mapping}
    r002_ids = {row["r002_generation_id"] for row in mapping}
    _require(not (generation_ids & r001_ids), "r001 generation ID contamination")
    _require(not (generation_ids & r002_ids), "r002 generation ID contamination")
    for relative in (R001_RUN_RELATIVE, R002_RUN_RELATIVE):
        incident = repo_root / relative
        _require(incident.is_dir(), f"incident directory missing: {relative.as_posix()}")
        journals = _journal_names(incident / "j") if (incident / "j").is_dir() else []
        _require(len(journals) == 0, f"incident journals must remain empty: {relative.as_posix()}")
    banned_prefix = ("HumanEval", "humaneval")
    _require(all(not task_id.startswith(banned_prefix) for task_id in task_ids), "external HumanEval task contamination")
    _require(all(task_id.startswith("Mbpp/") for task_id in task_ids), "non-MBPP task contamination")
    _require(not (repo_root / frozen.VALIDATION_RUN_RELATIVE).exists(), "2K-A validation run must remain absent")


def validate_and_materialize(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    generation_manifest_path = repo_root / GENERATION_MANIFEST_RELATIVE
    generation_bytes = generation_manifest_path.read_bytes()
    _require(
        _sha256_bytes(generation_bytes) == EXPECTED_GENERATION_MANIFEST_SHA256,
        "generation manifest SHA-256 drift",
    )
    generation_manifest = json.loads(generation_bytes)
    _require(generation_manifest["run_id"] == RUN_ID, "generation run ID drift")
    _require(
        generation_manifest["candidate_b"]["exact_text_sha256"] == EXPECTED_CANDIDATE_TEXT_SHA256,
        "Candidate B text hash drift",
    )
    _require(generation_manifest["healer_sha256"] == EXPECTED_HEALER_SHA256, "Healer hash drift")
    _require(generation_manifest["pipeline_sha256"] == EXPECTED_PIPELINE_SHA256, "Pipeline hash drift")
    _require(generation_manifest["model_digest"] == EXPECTED_MODEL_DIGEST, "model digest drift")
    _require(generation_manifest["quantization"] == EXPECTED_QUANTIZATION, "quantization drift")
    _require(generation_manifest["generation_parameters"] == frozen.GENERATION_OPTIONS, "generation parameter drift")
    _require(generation_manifest["seeds"] == list(SEEDS), "seed drift")

    cells = _read_csv(repo_root / R003_GOVERNANCE_RELATIVE / "candidate_b_generation_cells.csv")
    _require(len(cells) == 300, "frozen cell count drift")
    expected_ids = {row["generation_id"]: row for row in cells}
    _require(len(expected_ids) == 300, "duplicate frozen generation identity")
    task_seed = {(row["task_id"], int(row["seed"])) for row in cells}
    _require(len(task_seed) == 300, "duplicate frozen task-seed identity")
    tasks = {row["task_id"] for row in cells}
    _require(len(tasks) == 60, "frozen task count drift")
    _require(Counter(int(row["seed"]) for row in cells) == {seed: 60 for seed in SEEDS}, "seed distribution drift")

    run_dir = repo_root / R003_RUN_RELATIVE
    _require(run_dir.is_dir(), "r003 run directory missing")
    journal_dir = run_dir / "j"
    journal_names = _journal_names(journal_dir)
    _require(len(journal_names) == 300, "journal count must be exactly 300")
    expected_names = {f"{generation_id}.json" for generation_id in expected_ids}
    _require(set(journal_names) == expected_names, "unexpected or missing journal filename(s)")

    provenance = _read_json(run_dir / "model_provenance.json")
    _require(provenance.get("model_digest") == EXPECTED_MODEL_DIGEST, "run provenance digest drift")
    quant = provenance.get("quantization") or provenance.get("quantization_api_value")
    _require(
        isinstance(quant, str) and quant.strip().upper() == EXPECTED_QUANTIZATION,
        "run provenance quantization drift",
    )

    p0 = frozen.load_existing_p0(repo_root)
    prompt_by_task = {row["task_id"]: row["prompt"] for row in p0}
    _require(set(prompt_by_task) == tasks, "development task identity mismatch versus frozen P0 set")

    raw_rows: list[dict[str, Any]] = []
    account_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    reuse_rows: list[dict[str, Any]] = []
    journals_by_id: dict[str, dict[str, Any]] = {}

    for name in journal_names:
        journal = _load_journal(journal_dir / name)
        generation_id = journal.get("generation_id")
        _require(isinstance(generation_id, str) and generation_id in expected_ids, "journal generation_id not in freeze")
        cell = expected_ids[generation_id]
        _require(journal.get("status") == "complete_single_attempt", "journal status must be complete_single_attempt")
        _require(journal.get("retry_count") == 0, "retry_count must be 0")
        _require(journal.get("resume") is False, "resume must be false")
        _require(journal.get("first_attempt") is True, "first_attempt must be true")
        _require(journal.get("selective_retry") is False, "selective_retry must be false")
        _require(journal.get("run_id") == RUN_ID, "journal run_id drift")
        _require(journal.get("task_id") == cell["task_id"], "journal task_id drift")
        _require(int(journal.get("seed")) == int(cell["seed"]), "journal seed drift")
        _require(journal.get("program_id") == cell["program_id"], "journal program_id drift")
        _require(journal.get("model_digest") == EXPECTED_MODEL_DIGEST, "journal model digest drift")
        _require(journal.get("quantization") == EXPECTED_QUANTIZATION, "journal quantization drift")
        _require(journal.get("official_prompt_sha256") == cell["official_prompt_sha256"], "journal official prompt hash drift")
        _require(journal.get("composed_prompt_sha256") == cell["composed_prompt_sha256"], "journal composed prompt hash drift")
        _require(journal.get("candidate_b_text_sha256") == EXPECTED_CANDIDATE_TEXT_SHA256, "journal Candidate B text hash drift")
        raw_response = journal.get("raw_response")
        _require(isinstance(raw_response, str) and bool(raw_response.strip()), "empty raw response")
        _require(_sha256_text(raw_response) == journal.get("raw_response_sha256"), "raw response hash drift")
        request = journal.get("request")
        _require(isinstance(request, dict), "journal request missing")
        options = request.get("options")
        _require(isinstance(options, dict), "journal request options missing")
        for key in ("temperature", "top_p", "top_k", "num_ctx", "num_predict"):
            _require(options.get(key) == frozen.GENERATION_OPTIONS[key], f"generation option drift: {key}")
        _require(request.get("think") is False, "thinking must remain false")
        prompt = prompt_by_task[cell["task_id"]]
        _require(_sha256_text(prompt) == cell["official_prompt_sha256"], "official prompt bytes drift")
        composed = prompt + frozen.SEPARATOR + frozen.CANDIDATE_B_TEXT
        _require(_sha256_text(composed) == cell["composed_prompt_sha256"], "composed prompt bytes drift")
        journals_by_id[generation_id] = journal

        extraction = extract_code(raw_response)
        normalized = extraction.extracted_code if extraction.extraction_status == "extracted" else None
        contract = frozen._prompt_contract(prompt)
        truncated = bool(
            isinstance(journal.get("generation_metadata"), dict)
            and journal["generation_metadata"].get("done_reason") != "stop"
        )
        healed = apply_healer(normalized, contract[0], contract[1], truncated)

        raw_rows.append({
            "cell_index": int(cell["cell_index"]),
            "task_id": cell["task_id"],
            "seed": int(cell["seed"]),
            "sample_index": int(cell["sample_index"]),
            "generation_id": generation_id,
            "program_id": cell["program_id"],
            "run_id": RUN_ID,
            "raw_response_sha256": journal["raw_response_sha256"],
            "pipeline_normalized_source_sha256": (
                _sha256_text(normalized) if normalized is not None else ""
            ),
            "official_prompt_sha256": cell["official_prompt_sha256"],
            "composed_prompt_sha256": cell["composed_prompt_sha256"],
            "candidate_b_text_sha256": EXPECTED_CANDIDATE_TEXT_SHA256,
            "model_digest": EXPECTED_MODEL_DIGEST,
            "quantization": EXPECTED_QUANTIZATION,
            "temperature": frozen.GENERATION_OPTIONS["temperature"],
            "top_p": frozen.GENERATION_OPTIONS["top_p"],
            "top_k": frozen.GENERATION_OPTIONS["top_k"],
            "num_ctx": frozen.GENERATION_OPTIONS["num_ctx"],
            "num_predict": frozen.GENERATION_OPTIONS["num_predict"],
            "thinking": False,
            "status": "complete_single_attempt",
            "retry_count": 0,
            "resume": False,
            "first_attempt": True,
            "selective_retry": False,
            "single_attempt_no_retry_no_resume": True,
        })

        h0_source = normalized
        h1_source = healed.output_source
        h0_sha = _sha256_text(h0_source) if h0_source is not None else ""
        h1_sha = _sha256_text(h1_source) if h1_source is not None else ""
        changed = bool(h1_source != h0_source)
        _require(
            changed == (healed.status == "transformed"),
            "healer status/source-change inconsistency",
        )
        if not changed:
            _require(h0_source == h1_source, "unchanged H1 must be byte-identical to H0")
            _require(h0_sha == h1_sha, "unchanged H1/H0 source hash drift")

        account_ids = {
            arm: _identity_hash({"program_id": cell["program_id"], "healer_account": arm})
            for arm in ("H0", "H1")
        }
        for arm in ("H0", "H1"):
            source = h0_source if arm == "H0" else h1_source
            source_sha = h0_sha if arm == "H0" else h1_sha
            is_h1 = arm == "H1"
            if arm == "H0":
                disposition = "requires_evalplus"
            elif changed:
                disposition = "requires_evalplus_changed_h1"
            else:
                disposition = "reuse_h0_after_evalplus_identity_hash_match"
            account_rows.append({
                "account_index": len(account_rows) + 1,
                "factorial_arm": f"Candidate_B_{arm}",
                "prompt_condition": "Candidate_B",
                "healer_account": arm,
                "program_id": cell["program_id"],
                "evaluation_account_id": account_ids[arm],
                "run_id": RUN_ID,
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "sample_index": int(cell["sample_index"]),
                "generation_id": generation_id,
                "raw_response_sha256": journal["raw_response_sha256"],
                "pipeline_normalized_source_sha256": h0_sha,
                "evaluation_source_sha256": source_sha,
                "healer_status": "not_applied_control" if arm == "H0" else healed.status,
                "healer_diagnostic": "not_applied_control" if arm == "H0" else healed.diagnostic,
                "healer_rule_id": "not_applied_control" if arm == "H0" else EXPECTED_HEALER_RULE,
                "healer_sha256": "not_applied_control" if arm == "H0" else EXPECTED_HEALER_SHA256,
                "source_changed_by_healer": str(changed and is_h1).lower(),
                "same_raw_generation_h0_h1": "true",
                "same_pipeline_normalized_input_h0_h1": "true",
                "h1_byte_identical_to_h0": str((not changed) if is_h1 else True).lower(),
                "evaluator_result_used_by_healer": "false",
                "evalplus_status": "not_executed",
                "evaluation_disposition": disposition,
                "_completion": source,
            })

        eval_rows.append({
            "program_id": cell["program_id"],
            "evaluation_account_id": account_ids["H0"],
            "healer_account": "H0",
            "run_id": RUN_ID,
            "task_id": cell["task_id"],
            "seed": int(cell["seed"]),
            "sample_index": int(cell["sample_index"]),
            "generation_id": generation_id,
            "raw_response_sha256": journal["raw_response_sha256"],
            "pipeline_normalized_source_sha256": h0_sha,
            "evaluation_source_sha256": h0_sha,
            "healer_candidate_id": EXPECTED_CANDIDATE_ID,
            "healer_rule_id": "not_applied_control",
            "completion": h0_source if h0_source is not None else "",
            "evaluation_disposition": "requires_evalplus",
        })
        if changed:
            _require(h1_source is not None, "changed H1 source missing")
            eval_rows.append({
                "program_id": cell["program_id"],
                "evaluation_account_id": account_ids["H1"],
                "healer_account": "H1",
                "run_id": RUN_ID,
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "sample_index": int(cell["sample_index"]),
                "generation_id": generation_id,
                "raw_response_sha256": journal["raw_response_sha256"],
                "pipeline_normalized_source_sha256": h0_sha,
                "evaluation_source_sha256": h1_sha,
                "healer_candidate_id": EXPECTED_CANDIDATE_ID,
                "healer_rule_id": EXPECTED_HEALER_RULE,
                "completion": h1_source,
                "evaluation_disposition": "requires_evalplus_changed_h1",
            })
        else:
            reuse_rows.append({
                "program_id": cell["program_id"],
                "h0_evaluation_account_id": account_ids["H0"],
                "h1_evaluation_account_id": account_ids["H1"],
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "generation_id": generation_id,
                "raw_response_sha256": journal["raw_response_sha256"],
                "h0_source_sha256": h0_sha,
                "h1_source_sha256": h1_sha,
                "source_sha256_exact_match": "true",
                "reuse_eligible_after_h0_evalplus": "true",
                "reuse_basis": "h0_h1_evaluation_source_sha256_exact_match",
                "reuse_requires_h0_result_present": "true",
                "reuse_independent_of_h0_pass_fail": "true",
            })

    _require(len(raw_rows) == 300, "raw ledger count drift")
    _require(len(account_rows) == 600, "Candidate B account count drift")
    _require(len({row["evaluation_account_id"] for row in account_rows}) == 600, "duplicate evaluation account")
    _require(len({row["program_id"] for row in account_rows}) == 300, "Candidate B program count drift")
    _require(len(eval_rows) == EXPECTED_EVALPLUS_CELLS, "EvalPlus input count drift")
    _require(sum(row["healer_account"] == "H0" for row in eval_rows) == 300, "H0 EvalPlus count drift")
    _require(sum(row["healer_account"] == "H1" for row in eval_rows) == EXPECTED_CHANGED_H1, "changed H1 count drift")
    _require(len(reuse_rows) == EXPECTED_UNCHANGED_H1, "unchanged H1 reuse count drift")
    h1_accounts = [row for row in account_rows if row["healer_account"] == "H1"]
    status_counts = Counter(row["healer_status"] for row in h1_accounts)
    _require(status_counts["transformed"] == EXPECTED_CHANGED_H1, "transformed H1 count drift")
    _require(sum(row["source_changed_by_healer"] == "true" for row in h1_accounts) == EXPECTED_CHANGED_H1, "source_changed count drift")

    # Cross-check against run aggregates without rewriting them.
    run_raw = _read_jsonl(run_dir / "raw_generations.jsonl")
    run_pipe = _read_jsonl(run_dir / "pipeline_normalized.jsonl")
    run_accounts = _read_jsonl(run_dir / "h0_h1_accounts.jsonl")
    _require(len(run_raw) == 300 and len(run_pipe) == 300 and len(run_accounts) == 600, "run aggregate count drift")
    run_raw_by_id = {row["generation_id"]: row for row in run_raw}
    for row in raw_rows:
        existing = run_raw_by_id[row["generation_id"]]
        _require(existing["raw_response_sha256"] == row["raw_response_sha256"], "run raw hash drift versus journal rebuild")
        _require(existing["raw_response"] == journals_by_id[row["generation_id"]]["raw_response"], "raw response bytes mutated")
    run_acc_by_id = {row["evaluation_account_id"]: row for row in run_accounts}
    for row in account_rows:
        existing = run_acc_by_id[row["evaluation_account_id"]]
        _require(existing["evaluation_source_sha256"] == row["evaluation_source_sha256"] or (
            existing["evaluation_source_sha256"] is None and row["evaluation_source_sha256"] == ""
        ), "account source hash drift versus run materialization")
        _require(existing["healer_status"] == row["healer_status"], "healer status drift versus run materialization")
        _require(bool(existing["source_changed_by_healer"]) == (row["source_changed_by_healer"] == "true"), "source_changed drift")

    _forbid_incident_contamination(
        generation_ids=set(expected_ids),
        task_ids=tasks,
        repo_root=repo_root,
    )

    source_paths = {
        frozen.HEALER_RELATIVE: EXPECTED_HEALER_SHA256,
        frozen.PIPELINE_RELATIVE: EXPECTED_PIPELINE_SHA256,
        GENERATION_MANIFEST_RELATIVE: EXPECTED_GENERATION_MANIFEST_SHA256,
        R003_GOVERNANCE_RELATIVE / "candidate_b_generation_cells.csv": _sha256_bytes(
            (repo_root / R003_GOVERNANCE_RELATIVE / "candidate_b_generation_cells.csv").read_bytes()
        ),
        R003_RUN_RELATIVE / "raw_generations.jsonl": _sha256_bytes(_read_bytes(run_dir / "raw_generations.jsonl")),
        R003_RUN_RELATIVE / "pipeline_normalized.jsonl": _sha256_bytes(_read_bytes(run_dir / "pipeline_normalized.jsonl")),
        R003_RUN_RELATIVE / "h0_h1_accounts.jsonl": _sha256_bytes(_read_bytes(run_dir / "h0_h1_accounts.jsonl")),
        R003_RUN_RELATIVE / "materialization_manifest.json": _sha256_bytes(
            _read_bytes(run_dir / "materialization_manifest.json")
        ),
    }
    source_hashes = {
        path.as_posix(): digest for path, digest in sorted(source_paths.items(), key=lambda item: item[0].as_posix())
    }
    for relative, digest in source_hashes.items():
        actual = _sha256_bytes(_read_bytes(repo_root / relative))
        _require(actual == digest, f"source hash drift: {relative}")

    p0_reuse = _read_csv(repo_root / R003_GOVERNANCE_RELATIVE / "p0_identity_hash_reuse_ledger.csv")
    _require(len(p0_reuse) == 300, "P0 reuse ledger drift")
    factorial_accounts = _read_csv(repo_root / R003_GOVERNANCE_RELATIVE / "development_2x2_accounts.csv")
    _require(len(factorial_accounts) == 1200, "factorial 2x2 account plan drift")

    return {
        "raw_rows": raw_rows,
        "account_rows": account_rows,
        "eval_rows": eval_rows,
        "reuse_rows": reuse_rows,
        "source_hashes": source_hashes,
        "h1_status_counts": dict(status_counts),
        "tasks": 60,
    }


def _operator_guide(manifest_sha: str = "<MANIFEST_SHA256>") -> bytes:
    command = (
        "/home/yehya/.venvs/ast_evalplus/bin/python "
        "scripts/run_mbpp_candidate_b_r003_evalplus.py "
        "--manifest artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json "
        f"--manifest-sha256 {manifest_sha} --parallel 1 "
        "--output-dir artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001"
    )
    return f"""# Candidate B r003：H0/H1 凍結與 EvalPlus 執行準備操作指南

本輪只凍結 `mbpp_q35_9b_candidate_b_development60_replay_r003` 的300個完整 journal，重建 Candidate B H0/H1 帳目，並準備 fail-closed EvalPlus 輸入。禁止呼叫模型、禁止修改 prompt／Pipeline／Healer、禁止 resume／retry／覆寫 r003、禁止使用 r001／r002 response。

## 凍結結果

- Candidate B programs：300；H0/H1 accounts：600。
- H1 transformed（changed）：{EXPECTED_CHANGED_H1}；unchanged：{EXPECTED_UNCHANGED_H1}（H1 必須與 H0 byte-identical）。
- 待執行 EvalPlus cells：{EXPECTED_EVALPLUS_CELLS}（Candidate B H0 全300 + changed H1 {EXPECTED_CHANGED_H1}）。
- unchanged H1 只能在對應 H0 EvalPlus 結果存在且 identity／source SHA-256 完全一致時重用。
- P0-H0／P0-H1 既有各300帳維持 identity-hash 沿用，形成後續完整2×2（600 programs／1200 accounts）；本輪不做 paired outcome analysis。
- model_calls=0；evalplus_executions=0；正式 EvalPlus output directory 尚未建立。

## 唯一人工 WSL EvalPlus 指令

請在 repository 根目錄的 WSL shell 執行以下唯一一條指令；不得改變 interpreter、manifest、hash、`--parallel 1` 或 output path：

```bash
{command}
```

Driver 只評估上述 {EXPECTED_EVALPLUS_CELLS} 格，拒絕 hash drift、identity mismatch、duplicate／missing、既有 output directory、Windows 本機執行與任何 generation／retry／resume／overwrite 路徑。評估完成後才可另行授權 paired analysis；本指南不判定 Candidate B gate。
""".encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = validate_and_materialize(repo_root)
    account_export = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in analysis["account_rows"]
    ]
    outputs: dict[str, bytes] = {
        "candidate_b_raw_generation_ledger.csv": _csv_bytes(analysis["raw_rows"], RAW_FIELDS),
        "candidate_b_h0_h1_accounts.csv": _csv_bytes(account_export, ACCOUNT_FIELDS),
        "evalplus_input.jsonl": _jsonl_bytes(analysis["eval_rows"]),
        "candidate_b_h1_unchanged_h0_reuse_ledger.csv": _csv_bytes(analysis["reuse_rows"], REUSE_FIELDS),
    }
    evaluation_plan = {
        "plan_id": "candidate_b_r003_h0_h1_evalplus_v1",
        "status": "frozen_waiting_for_manual_evalplus",
        "run_id": RUN_ID,
        "scope": {
            "development_tasks": 60,
            "task_seed_identities": 300,
            "candidate_b_programs": 300,
            "candidate_b_accounts": 600,
            "factorial_programs": 600,
            "factorial_accounts": 1200,
        },
        "evalplus_cells": EXPECTED_EVALPLUS_CELLS,
        "candidate_b_h0_cells": 300,
        "candidate_b_h1_changed_cells": EXPECTED_CHANGED_H1,
        "candidate_b_h1_unchanged_reuse_cells": EXPECTED_UNCHANGED_H1,
        "h1_status_counts": analysis["h1_status_counts"],
        "interpreter": "/home/yehya/.venvs/ast_evalplus/bin/python",
        "parallel": 1,
        "output_relative": (
            OUTPUT_RELATIVE / "manual_evalplus_run_001"
        ).as_posix(),
        "evalplus_executed_during_preparation": False,
        "model_calls": 0,
        "reuse_gate": (
            "exact H0/H1 evaluation_source_sha256 identity plus complete verified H0 EvalPlus result"
        ),
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "rule_order": [EXPECTED_HEALER_RULE],
        "healer_sha256": EXPECTED_HEALER_SHA256,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
        "pass_fail_prefilled": False,
        "evaluator_results_visible_to_healer": False,
    }
    paired_plan = {
        "plan_id": "candidate_b_r003_2x2_paired_analysis_pending_evalplus_v1",
        "status": "blocked_until_evalplus_complete",
        "arms": ["P0_H0", "P0_H1", "Candidate_B_H0", "Candidate_B_H1"],
        "accounts": 1200,
        "programs": 600,
        "gate_decision_this_round": False,
        "excluded_incident_runs": [frozen.R001_RUN_ID, frozen.R002_RUN_ID],
    }
    zero = {
        "status": "zero_model_preflight_frozen",
        "model_calls": 0,
        "evalplus_executions": 0,
        "r003_journals": 300,
        "candidate_b_accounts": 600,
        "evalplus_cells_prepared": EXPECTED_EVALPLUS_CELLS,
        "evalplus_output_directory_absent": True,
        "validation_run_absent": True,
    }
    outputs["evaluation_plan.json"] = _canonical_bytes(evaluation_plan)
    outputs["paired_analysis_plan.json"] = _canonical_bytes(paired_plan)
    outputs["zero_model_preflight.json"] = _canonical_bytes(zero)
    outputs["operator_guide_zh.md"] = _operator_guide()
    manifest = {
        "manifest_version": "candidate_b_r003_h0_h1_evalplus_v1",
        "status": "prepared_not_executed",
        "development_replay_only": True,
        "run_id": RUN_ID,
        "generation_manifest_sha256": EXPECTED_GENERATION_MANIFEST_SHA256,
        "counts": {
            "tasks": 60,
            "task_seed_identities": 300,
            "candidate_b_programs": 300,
            "candidate_b_accounts": 600,
            "candidate_b_h0": 300,
            "candidate_b_h1": 300,
            "h1_changed": EXPECTED_CHANGED_H1,
            "h1_unchanged": EXPECTED_UNCHANGED_H1,
            "evalplus_cells": EXPECTED_EVALPLUS_CELLS,
            "factorial_programs": 600,
            "factorial_accounts": 1200,
        },
        "h1_status_counts": analysis["h1_status_counts"],
        "candidate_b_text_sha256": EXPECTED_CANDIDATE_TEXT_SHA256,
        "healer_sha256": EXPECTED_HEALER_SHA256,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "model_digest": EXPECTED_MODEL_DIGEST,
        "quantization": EXPECTED_QUANTIZATION,
        "generation_parameters": frozen.GENERATION_OPTIONS,
        "seeds": list(SEEDS),
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "rule_order": [EXPECTED_HEALER_RULE],
        "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "evaluator_version": EXPECTED_EVALUATOR_VERSION,
        "evaluator_engine": EXPECTED_EVALUATOR_ENGINE,
        "model_calls": 0,
        "evalplus_executions": 0,
        "new_generation_runs": 0,
        "evalplus_output_directory_created": False,
        "validation_run_directory_touched": False,
        "r001_r002_used_as_result_source": False,
        "source_sha256": analysis["source_hashes"],
        "output_sha256_excluding_manifest_and_operator_guide": {
            name: _sha256_bytes(content)
            for name, content in sorted(outputs.items())
            if name != "operator_guide_zh.md"
        },
    }
    outputs["manifest.json"] = _canonical_bytes(manifest)
    outputs["operator_guide_zh.md"] = _operator_guide(_sha256_bytes(outputs["manifest.json"]))
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, *, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "frozen output directory missing")
        actual = {path.name for path in output_dir.iterdir() if path.is_file()}
        _require(actual == set(outputs), "frozen output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "output directory exists; overwrite forbidden")
    eval_out = output_dir / "manual_evalplus_run_001"
    _require(not eval_out.exists(), "EvalPlus output directory must remain absent during preparation")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except (PreparationError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
