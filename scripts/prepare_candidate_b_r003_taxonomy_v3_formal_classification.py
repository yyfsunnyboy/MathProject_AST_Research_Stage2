#!/usr/bin/env python3
"""Prepare, but do not adjudicate, Candidate B r003 taxonomy-v3 evidence."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1"
)
START_HEAD = "2c832b8be5b92d755317ada808d86c1c9fabc5dc"
TAXONOMY_VERSION = "AI_GENERATED_PROGRAM_FAILURE_TAXONOMY_V3"
DIAGNOSTICS_RUNNER_REVISION = "r002_v3"

FORMAL_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001"
)
FORMAL_RESULTS = FORMAL_DIR / "coarse_diagnostics.csv"
FORMAL_RECEIPT = FORMAL_DIR / "execution_manifest.json"
DIAGNOSTICS_SOURCE_MANIFEST = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manifest.json"
)
FORMAL_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_diagnostics_r002_v3/formal198_input_ledger.csv"
)
FORMAL_PROTOCOL = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_diagnostics_r002_v3/formal_diagnostics_protocol.json"
)
CROSSWALK = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/"
    "candidate_b_r003_v3_derived_crosswalk.csv"
)
CENSUS = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_failure_census_v1/candidate_b_r003_failure_census.csv"
)
ADJUDICATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_failure_census_human_review_adjudication_v1/adjudication_results.csv"
)
PAIRED = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_formal_paired_analysis_v1/paired_cell_results.csv"
)
EVALPLUS_RESULTS = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/evalplus_results.csv"
)
EVALPLUS_RECEIPT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001/execution_manifest.json"
)
JOURNAL = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
DATASET_MANIFEST = Path("data/mbpp_plus/dataset_manifest.json")
TASKS = Path("data/mbpp_plus/tasks.jsonl")
TAXONOMY_CODEBOOK = Path(
    r"C:\Users\yehya\Downloads\AI 生成程式共同失敗分類標準（實際使用版 v3）.md"
)
ANALYZER = Path("scripts/prepare_candidate_b_r003_taxonomy_v3_formal_classification.py")
TESTS = Path(
    "tests/finals_rebuild/test_candidate_b_r003_taxonomy_v3_formal_classification_preparation.py"
)

SOURCE_HASHES: dict[Path, str] = {
    FORMAL_RESULTS: "dafba357a47341856de32d6766aa27cf37fc4a326c9427b5df6fadef659d8f4c",
    FORMAL_RECEIPT: "e536827a69a7d782406cefa42068c9e1dcb6453385bdd943be8f6516962cdf34",
    DIAGNOSTICS_SOURCE_MANIFEST: "f37c0daa9fb4f3a18d7a2d7fed983f57f2ee0057ef202220643cf7919e362234",
    FORMAL_LEDGER: "d2d62a33b4f51118d0a51b41aadc9445bd64d680c3b1ef5c54117ae180272640",
    FORMAL_PROTOCOL: "d4d0bdb8ae470d10e0746241f24efa806c66e4d089e235b25893a315765e30d9",
    CROSSWALK: "6a083a06b2cbbb5f937b6f1ae343466ae3bc97e35f93323c8902adec4f5658f7",
    CENSUS: "289b2d1e562453bb944032254cc02b47d738a504720aca6dc85da6c252c10740",
    ADJUDICATION: "b244f6c7ca6d291906dadd36992371cf9b5a57bd56a1e59c227b0efbd5468256",
    PAIRED: "425efbf8351cc2d1fbe2a0f22e5c6ae5e2bc29b57ee8da6a7a9adfe88752ae43",
    EVALPLUS_RESULTS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    EVALPLUS_RECEIPT: "4ddb7beda50db18e4c6bf77484c34626c1088753fcfdb68c16e52f851f0b66f7",
    JOURNAL: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    DATASET_MANIFEST: "502e946fb273751805ec74472856a8d2e6cd732368547c9f45e2310495b831be",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    TAXONOMY_CODEBOOK: "7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304",
}

EXPECTED_EVALUATOR_HASH = "6a84a328307f3ce98a49933008aa18da481aae52920238b9204dcf47b1280606"
EXPECTED_PROTOCOL_HASH = SOURCE_HASHES[FORMAL_PROTOCOL]
EXPECTED_INFRASTRUCTURE = {
    (
        "a6f3b32f10e03fb5ebe7025f863b1bff932bf5459b3d9aae070a3497d37ed62a",
        "cc5968165ae1f3b1203b4b1e26a86e9747e1c27f1520d4dbc521458644ab2560",
    ),
    (
        "e34035942f49279e74cc7c14da61099ae2325ec0c816ed64d6e8c2d44e9ad594",
        "b844aa9aaf5a3780e42a405f3cd025a47eec35d811429c5013a8234eabf9fc99",
    ),
}

CLASSIFICATION_FIELDS = (
    "program_id",
    "cell_identity_sha256",
    "task_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "evaluation_source_sha256",
    "task_contract_sha256",
    "evaluator_hash",
    "diagnostics_protocol_sha256",
    "taxonomy_version",
    "diagnostics_runner_revision",
    "evidence_role",
    "diagnostic_evidence_validity",
    "classification_status",
    "primary_failure_layer",
    "secondary_failure_layers",
    "g1_parse",
    "g2_execution",
    "g3_contract",
    "g3e_entry_point",
    "g3a_required_api",
    "g3s_output_schema",
    "g3c_canonical_form",
    "g4_correctness",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "model_source_line",
    "model_source_ast_node",
    "termination",
    "return_type_bucket",
    "return_shape_bucket",
    "ipc_status",
    "child_exit_bucket",
    "evalplus_base_status",
    "evalplus_plus_status",
    "outcome_validity",
    "failure_chain",
    "mechanism_tags",
    "evidence_references",
    "confidence",
    "reviewer_required",
    "review_queue_disposition",
    "machine_proposal",
    "machine_proposal_basis",
    "machine_proposal_status",
    "formal_adjudication_status",
    "formal_adjudicated_primary_layer",
    "formal_reviewer_id",
    "healer_eligibility",
    "healer_decision",
    "healer_outcome",
    "diagnostics_allowed_as_healer_runtime_input",
    "legacy_adjudication_present",
)


class PreparationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreparationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def _verify_one(path: Path, expected: str) -> None:
    _require(path.is_file(), f"missing frozen source: {path}")
    _require(_sha(path.read_bytes()) == expected, f"frozen source hash drift: {path}")


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        _verify_one(_path(repo, relative), digest)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _unique_map(
    rows: list[dict[str, Any]], key: str, label: str, expected_count: int | None = None
) -> dict[str, dict[str, Any]]:
    if expected_count is not None:
        _require(len(rows) == expected_count, f"{label} row count drift")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row[key])
        _require(value and value not in result, f"{label} duplicate or empty {key}")
        result[value] = row
    return result


def load_tables(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    journal_rows = _read_jsonl(repo / JOURNAL)
    task_rows = _read_jsonl(repo / TASKS)
    return {
        "diagnostics": _read_csv(repo / FORMAL_RESULTS),
        "formal_receipt": json.loads((repo / FORMAL_RECEIPT).read_bytes()),
        "source_manifest": json.loads((repo / DIAGNOSTICS_SOURCE_MANIFEST).read_bytes()),
        "formal_ledger": _read_csv(repo / FORMAL_LEDGER),
        "crosswalk": _read_csv(repo / CROSSWALK),
        "census": _read_csv(repo / CENSUS),
        "adjudication": _read_csv(repo / ADJUDICATION),
        "paired": _read_csv(repo / PAIRED),
        "evalplus": _read_csv(repo / EVALPLUS_RESULTS),
        "evalplus_receipt": json.loads((repo / EVALPLUS_RECEIPT).read_bytes()),
        "journal": journal_rows,
        "dataset_manifest": json.loads((repo / DATASET_MANIFEST).read_bytes()),
        "tasks": task_rows,
    }


def _task_contract_hash(task: dict[str, Any]) -> str:
    value = {"entry_point": task["entry_point"], "prompt": task["prompt"], "task_id": task["task_id"]}
    return _sha(_compact(value).encode("utf-8"))


def analyze_tables(tables: dict[str, Any]) -> dict[str, Any]:
    diagnostics = tables["diagnostics"]
    diagnostic_by_program = _unique_map(diagnostics, "program_id", "formal diagnostics", 198)
    _require(len({row["cell_identity_sha256"] for row in diagnostics}) == 198, "formal diagnostics duplicate cell identity")
    receipt = tables["formal_receipt"]
    _require(receipt.get("status") == "r002_v3_formal_complete", "formal receipt status drift")
    _require(receipt.get("cells") == 198, "formal receipt cell count drift")
    _require(receipt.get("results_sha256") == SOURCE_HASHES[FORMAL_RESULTS], "formal receipt results hash drift")
    _require(receipt.get("source_manifest_sha256") == SOURCE_HASHES[DIAGNOSTICS_SOURCE_MANIFEST], "formal receipt source manifest drift")
    _require(receipt.get("model_calls") == 0, "formal receipt model_calls drift")
    _require(receipt.get("evalplus_correctness_executions") == 0, "formal receipt correctness execution drift")
    _require(receipt.get("healer_runtime_input") is False, "diagnostics healer runtime input must be false")
    _require(tables["source_manifest"].get("manifest_version") == "candidate_b_r003_diagnostics_r002_v3", "diagnostics source manifest revision drift")

    ledger = _unique_map(tables["formal_ledger"], "program_id", "formal input ledger", 198)
    crosswalk = _unique_map(tables["crosswalk"], "program_id", "taxonomy crosswalk", 300)
    census = _unique_map(tables["census"], "program_id", "legacy census", 300)
    adjudication = _unique_map(tables["adjudication"], "program_id", "legacy adjudication", 21)
    paired_rows = [row for row in tables["paired"] if row["prompt_condition"] == "Candidate_B"]
    paired = _unique_map(paired_rows, "program_id", "Candidate B paired cells", 300)
    evalplus_rows = [row for row in tables["evalplus"] if row["healer_account"] == "H0"]
    evalplus = _unique_map(evalplus_rows, "program_id", "Candidate B H0 EvalPlus", 300)
    journal_rows = [row for row in tables["journal"] if row["healer_account"] == "H0"]
    journal = _unique_map(journal_rows, "program_id", "Candidate B H0 journal", 300)
    tasks = _unique_map(tables["tasks"], "task_id", "public MBPP+ contracts", 378)
    eval_receipt = tables["evalplus_receipt"]
    _require(eval_receipt.get("results_sha256") == SOURCE_HASHES[EVALPLUS_RESULTS], "EvalPlus receipt results hash drift")
    _require(eval_receipt.get("frozen_manifest_sha256") == EXPECTED_EVALUATOR_HASH, "EvalPlus evaluator identity drift")
    dataset = tables["dataset_manifest"]
    _require(dataset.get("tasks_sha256") == SOURCE_HASHES[TASKS], "public task contract hash drift")
    _require(dataset.get("evalplus_dataset_hash") == "ee43ecabebf20deef4bb776a405ac5b1", "EvalPlus dataset identity drift")

    preparation: list[dict[str, Any]] = []
    infrastructure_rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    join_counts = Counter()
    phase_counts = Counter()
    proposal_counts = Counter()
    infrastructure_identities: set[tuple[str, str]] = set()

    for diagnostic in sorted(diagnostics, key=lambda row: row["program_id"]):
        program_id = diagnostic["program_id"]
        ledger_row = ledger.get(program_id)
        xrow = crosswalk.get(program_id)
        crow = census.get(program_id)
        erow = evalplus.get(program_id)
        prow = paired.get(program_id)
        jrow = journal.get(program_id)
        _require(all(row is not None for row in (ledger_row, xrow, crow, erow, prow, jrow)), "missing required program identity join")
        assert ledger_row is not None and xrow is not None and crow is not None
        assert erow is not None and prow is not None and jrow is not None
        join_counts.update(["formal_ledger", "crosswalk", "census", "evalplus_h0", "paired_candidate_b", "journal_h0"])

        _require(ledger_row["cell_identity_sha256"] == diagnostic["cell_identity_sha256"], "cell identity drift")
        _require(ledger_row["task_identity_sha256"] == diagnostic["task_identity_sha256"], "task identity drift")
        _require(ledger_row["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "formal ledger source hash drift")
        _require(ledger_row["evaluator_hash"] == diagnostic["evaluator_hash"] == EXPECTED_EVALUATOR_HASH, "evaluator hash drift")
        _require(diagnostic["protocol_sha256"] == EXPECTED_PROTOCOL_HASH, "diagnostics protocol hash drift")
        _require(xrow["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "crosswalk source hash drift")
        _require(xrow["generation_id"] == ledger_row["generation_id"], "crosswalk generation identity drift")
        _require(xrow["evaluator_hash"] == f"sha256:{EXPECTED_EVALUATOR_HASH}", "crosswalk evaluator hash drift")
        _require(_sha(xrow["task_id"].encode("utf-8")) == diagnostic["task_identity_sha256"], "crosswalk task identity drift")
        _require(crow["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "census source hash drift")
        _require(erow["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "EvalPlus source hash drift")
        _require(erow["generation_id"] == ledger_row["generation_id"] and erow["task_id"] == xrow["task_id"], "EvalPlus identity drift")
        _require(erow["evalplus_pass"] == "false", "formal classification input must be a frozen correctness failure")
        _require(prow["h0_source_sha256"] == diagnostic["evaluation_source_sha256"], "paired source hash drift")
        _require(prow["task_id"] == xrow["task_id"] and prow["h0_pass"] == "false", "paired identity or correctness drift")
        _require(jrow["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "journal source field drift")
        _require(_sha(jrow["evaluation_source"].encode("utf-8")) == diagnostic["evaluation_source_sha256"], "journal source bytes hash drift")
        _require(jrow["generation_id"] == ledger_row["generation_id"] and jrow["task_id"] == xrow["task_id"], "journal identity drift")
        task = tasks.get(xrow["task_id"])
        _require(task is not None and task.get("prompt") and task.get("entry_point"), "public task contract missing")
        join_counts.update(["public_task_contract"])
        _require(xrow["g1_parse"] == "PASS" and xrow["v3_g3e_entry_point"] == "PASS", "static G1/G3e evidence drift")
        _require(xrow["g3a_required_api"] == "NOT_APPLICABLE" and xrow["g3c_canonical_form"] == "NOT_APPLICABLE", "MBPP+ G3 applicability drift")

        phase = diagnostic["phase"]
        phase_counts[phase] += 1
        is_infrastructure = phase == "infrastructure"
        if is_infrastructure:
            identity = (program_id, diagnostic["cell_identity_sha256"])
            infrastructure_identities.add(identity)
            _require(identity in EXPECTED_INFRASTRUCTURE, "unexpected infrastructure identity")
            _require(
                diagnostic["exception_class"] == "WorkerProcessExit"
                and diagnostic["termination"] == "not_run"
                and diagnostic["ipc_status"] == "result_eof"
                and diagnostic["child_exit_bucket"] == "signal_exit",
                "infrastructure evidence pattern drift",
            )
            _require(not diagnostic["model_source_line"] and not diagnostic["model_source_ast_node"], "infrastructure row unexpectedly has source frame")
            evidence_validity = "INVALID_INFRASTRUCTURE"
            outcome_validity = "INVALID_INFRASTRUCTURE"
            g2 = "NOT_ASSESSED"
            proposal = "ABSTAIN_DIAGNOSTIC_INFRASTRUCTURE"
            proposal_basis = "worker-ready後僅有result_eof/signal_exit；無可信程式層payload，不推定L4"
            confidence = "NOT_CLASSIFIABLE"
            queue_disposition = "EVIDENCE_BLOCKED_INFRASTRUCTURE"
            mechanisms = ["needs_human_review"]
        elif phase == "completed":
            _require(diagnostic["termination"] == "returned" and diagnostic["ipc_status"] == "result_received", "completed diagnostic state drift")
            evidence_validity = "VALID_DIAGNOSTIC_EVIDENCE"
            outcome_validity = "PENDING_REVIEW"
            g2 = "PASS"
            proposal = "REVIEW_OUTPUT_CONTRACT_OR_SEMANTIC"
            proposal_basis = "candidate returned但correctness fail；須先人工排除G3s/contract/evaluator問題，不能直接標L5"
            confidence = "LOW"
            queue_disposition = "HUMAN_REVIEW_QUEUE"
            mechanisms = ["needs_human_review"]
        else:
            _require(phase in {"G2_module", "G2_base", "G2_plus"}, "unknown diagnostics phase")
            _require(diagnostic["termination"] == "raised" and diagnostic["ipc_status"] == "result_received", "raised diagnostic state drift")
            evidence_validity = "VALID_DIAGNOSTIC_EVIDENCE"
            outcome_validity = "PENDING_REVIEW"
            g2 = "FAIL"
            proposal = "REVIEW_RUNTIME_ROOT_CAUSE_AND_EARLIEST_GATE"
            proposal_basis = "diagnostic exception與source frame可供review；phase/exception本身不直接映射L2/L3/L4"
            confidence = "LOW"
            queue_disposition = "HUMAN_REVIEW_QUEUE"
            mechanisms = ["needs_human_review"]
        proposal_counts[(proposal, phase)] += 1

        failure_chain = [
            {
                "gate": "G2",
                "layer": None,
                "observation": "INFRASTRUCTURE_INVALID" if is_infrastructure else ("PASS" if phase == "completed" else "RAISED"),
                "phase": phase,
                "stage": "formal_diagnostics_r002_v3",
            },
            {
                "gate": "G4",
                "layer": None,
                "observation": "FAIL",
                "stage": "frozen_evalplus_correctness",
            },
        ]
        references = [
            f"{FORMAL_RESULTS.as_posix()}#cell_identity_sha256={diagnostic['cell_identity_sha256']}",
            f"{FORMAL_LEDGER.as_posix()}#program_id={program_id}",
            f"{CROSSWALK.as_posix()}#program_id={program_id}",
            f"{EVALPLUS_RESULTS.as_posix()}#program_id={program_id};healer_account=H0",
            f"{JOURNAL.as_posix()}#program_id={program_id};healer_account=H0",
            f"{TASKS.as_posix()}#task_id={xrow['task_id']}",
        ]
        legacy_present = program_id in adjudication
        if legacy_present:
            arow = adjudication[program_id]
            _require(arow["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "legacy adjudication source hash drift")
            references.append(f"{ADJUDICATION.as_posix()}#program_id={program_id}")

        prepared = {
            "program_id": program_id,
            "cell_identity_sha256": diagnostic["cell_identity_sha256"],
            "task_identity_sha256": diagnostic["task_identity_sha256"],
            "task_id": xrow["task_id"],
            "seed": xrow["seed"],
            "generation_id": ledger_row["generation_id"],
            "evaluation_source_sha256": diagnostic["evaluation_source_sha256"],
            "task_contract_sha256": _task_contract_hash(task),
            "evaluator_hash": diagnostic["evaluator_hash"],
            "diagnostics_protocol_sha256": diagnostic["protocol_sha256"],
            "taxonomy_version": TAXONOMY_VERSION,
            "diagnostics_runner_revision": DIAGNOSTICS_RUNNER_REVISION,
            "evidence_role": "development",
            "diagnostic_evidence_validity": evidence_validity,
            "classification_status": "PENDING_REVIEW",
            "primary_failure_layer": "",
            "secondary_failure_layers": "[]",
            "g1_parse": "PASS",
            "g2_execution": g2,
            "g3_contract": "NOT_ASSESSED",
            "g3e_entry_point": "PASS",
            "g3a_required_api": "NOT_APPLICABLE",
            "g3s_output_schema": "NOT_ASSESSED",
            "g3c_canonical_form": "NOT_APPLICABLE",
            "g4_correctness": "FAIL",
            "diagnostic_phase": phase,
            "diagnostic_exception_class": diagnostic["exception_class"],
            "model_source_line": diagnostic["model_source_line"],
            "model_source_ast_node": diagnostic["model_source_ast_node"],
            "termination": diagnostic["termination"],
            "return_type_bucket": diagnostic["return_type_bucket"],
            "return_shape_bucket": diagnostic["return_shape_bucket"],
            "ipc_status": diagnostic["ipc_status"],
            "child_exit_bucket": diagnostic["child_exit_bucket"],
            "evalplus_base_status": erow["base_status"],
            "evalplus_plus_status": erow["plus_status"],
            "outcome_validity": outcome_validity,
            "failure_chain": _compact(failure_chain),
            "mechanism_tags": _compact(mechanisms),
            "evidence_references": _compact(references),
            "confidence": confidence,
            "reviewer_required": "true",
            "review_queue_disposition": queue_disposition,
            "machine_proposal": proposal,
            "machine_proposal_basis": proposal_basis,
            "machine_proposal_status": "PREPARATION_ONLY_NOT_FORMAL_ADJUDICATION",
            "formal_adjudication_status": "NOT_COMPLETED",
            "formal_adjudicated_primary_layer": "",
            "formal_reviewer_id": "",
            "healer_eligibility": "undetermined",
            "healer_decision": "not_run",
            "healer_outcome": "not_assessed",
            "diagnostics_allowed_as_healer_runtime_input": "false",
            "legacy_adjudication_present": str(legacy_present).lower(),
        }
        preparation.append(prepared)
        unresolved.append({
            "program_id": program_id,
            "cell_identity_sha256": diagnostic["cell_identity_sha256"],
            "diagnostic_evidence_validity": evidence_validity,
            "classification_status": "PENDING_REVIEW",
            "primary_failure_layer": "",
            "machine_proposal": proposal,
            "review_queue_disposition": queue_disposition,
            "reviewer_required": "true",
            "evidence_references": _compact(references),
        })
        if is_infrastructure:
            infrastructure_rows.append({
                "program_id": program_id,
                "cell_identity_sha256": diagnostic["cell_identity_sha256"],
                "task_id": xrow["task_id"],
                "seed": xrow["seed"],
                "evaluation_source_sha256": diagnostic["evaluation_source_sha256"],
                "diagnostic_evidence_validity": "INVALID_INFRASTRUCTURE",
                "classification_status": "PENDING_REVIEW",
                "primary_failure_layer": "",
                "outcome_validity": "INVALID_INFRASTRUCTURE",
                "reviewer_required": "true",
                "healer_eligibility": "undetermined",
                "healer_decision": "not_run",
                "healer_outcome": "not_assessed",
                "available_evidence": "worker_ready;result_eof;signal_exit;no_model_source_frame;no_return_payload",
                "prohibited_inference": "signal_exit_not_L4;same_task_not_cross_cell_evidence",
            })

    _require(infrastructure_identities == EXPECTED_INFRASTRUCTURE, "infrastructure identity set drift")
    _require(len(preparation) == len(unresolved) == 198, "preparation completeness drift")
    _require(sum(row["review_queue_disposition"] == "HUMAN_REVIEW_QUEUE" for row in preparation) == 196, "human review queue count drift")
    _require(len(infrastructure_rows) == 2, "infrastructure row count drift")
    _require(all(not row["primary_failure_layer"] for row in preparation), "machine preparation must not adjudicate primary layer")

    proposal_summary = [
        {
            "machine_proposal": proposal,
            "diagnostic_phase": phase,
            "cells": count,
            "formal_adjudication_completed": "false",
            "primary_layer_assigned": "false",
        }
        for (proposal, phase), count in sorted(proposal_counts.items())
    ]
    audit = {
        "status": "identity_hash_safe_join_complete",
        "diagnostics_rows": 198,
        "unique_program_ids": len(diagnostic_by_program),
        "unique_cell_identities": len({row["cell_identity_sha256"] for row in diagnostics}),
        "usable_diagnostics": 196,
        "infrastructure_invalid": 2,
        "human_review_queue": 196,
        "formal_adjudications_completed": 0,
        "join_counts": dict(sorted(join_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "all_source_hashes_verified": True,
        "join_keys": [
            "program_id",
            "cell_identity_sha256",
            "task_identity_sha256",
            "generation_id",
            "evaluation_source_sha256",
            "evaluator_hash",
            "diagnostics_protocol_sha256",
        ],
        "row_order_used_for_join": False,
        "task_name_only_used_for_join": False,
        "seed_only_used_for_join": False,
    }
    return {
        "preparation": preparation,
        "unresolved": unresolved,
        "infrastructure": infrastructure_rows,
        "proposal_summary": proposal_summary,
        "audit": audit,
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    return analyze_tables(load_tables(repo))


def _schema() -> dict[str, Any]:
    return {
        "schema_version": "candidate_b_r003_taxonomy_v3_classification_preparation_v1",
        "row_count": 198,
        "fields": list(CLASSIFICATION_FIELDS),
        "formal_adjudication_completed": False,
        "primary_layer_enum": [None, "L0", "L1", "L2", "L3", "L4", "L5"],
        "classification_status_enum": ["PENDING_REVIEW", "ADJUDICATED"],
        "outcome_validity_enum": [
            "VALID_MODEL_OUTCOME",
            "INVALID_EVALUATOR",
            "INVALID_CONTRACT",
            "INVALID_INFRASTRUCTURE",
            "PENDING_REVIEW",
        ],
        "gate_enum": ["PASS", "FAIL", "NOT_ASSESSED", "NOT_APPLICABLE"],
        "healer_eligibility_enum": ["eligible", "noneligible", "undetermined"],
        "healer_decision_enum": ["transformed", "abstained", "no_trigger", "rejected", "not_run"],
        "healer_outcome_enum": [
            "rescue_to_pass",
            "changed_partial_progress",
            "preserved_pass",
            "unchanged_fail",
            "regression",
            "rollback",
            "not_assessed",
        ],
        "forbidden_output_fields": [
            "source",
            "hidden_input",
            "expected",
            "actual",
            "exception_message",
            "assertion_message",
            "traceback",
            "stdout",
            "stderr",
        ],
        "invariants": {
            "phase_is_not_primary_layer": True,
            "exception_class_alone_is_not_primary_layer": True,
            "completed_returned_is_not_automatic_L5": True,
            "base_plus_failure_is_not_automatic_semantic_failure": True,
            "diagnostics_allowed_as_healer_runtime_input": False,
            "machine_proposal_is_not_formal_adjudication": True,
        },
    }


def _review_guide() -> str:
    return """# Candidate B r003 taxonomy v3 reviewer／adjudication guide

## 範圍

本 revision 是 development evidence 的 machine preparation，不是正式人工 adjudication。`classification_preparation.csv` 的198格均為 `PENDING_REVIEW`、`primary_failure_layer=null`；196格可進人工review queue，2格因diagnostic infrastructure failure維持證據阻塞。

## 人工判定順序

1. 先核對 frozen source hash、公開 task contract、evaluator與diagnostics identity。
2. 依 taxonomy v3 順序檢查 infrastructure → G1 → G3e → G2 → G3s → G3a → G3c → G4。
3. diagnostic phase只表示觀察階段，不等於L0–L5；exception class也不能單獨決定layer。
4. `completed/returned` 加 correctness fail仍須先排除L2 output schema／packaging與evaluator問題，才可能裁決L5。
5. G2 raised案例須查看短source context、公開contract及source-frame；Domain API/tool、stdlib、第三方dependency與environment問題必須分流。
6. evidence不足時保持layer null與PENDING_REVIEW，不猜測。

## Infrastructure兩格

兩格只有worker-ready後result EOF/signal exit，沒有model-source frame或return payload。固定保持 `INVALID_INFRASTRUCTURE`、layer null、Healer not_run；不得標L4、不得局部重跑、不得因同屬Mbpp/119互相推定。

## Healer邊界

diagnostics永遠不得成為Healer runtime input。本輪不執行Healer。Eligibility須 evaluator-blind；truncation原則上abstain；entry-point只有唯一、安全、跨題且answer-free候選才可能eligible，多候選必須ambiguous並abstain。不得從correctness結果反推修法。

人工裁決應另建新revision，保存reviewer、時間、證據與disagreement；不得覆寫本 preparation、legacy census、既有21案adjudication或v3 crosswalk。
"""


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    analysis = build_analysis(repo)
    unresolved_fields = (
        "program_id",
        "cell_identity_sha256",
        "diagnostic_evidence_validity",
        "classification_status",
        "primary_failure_layer",
        "machine_proposal",
        "review_queue_disposition",
        "reviewer_required",
        "evidence_references",
    )
    infrastructure_fields = tuple(analysis["infrastructure"][0])
    proposal_fields = tuple(analysis["proposal_summary"][0])
    outputs: dict[Path, bytes] = {
        Path("classification_preparation.csv"): _csv_bytes(CLASSIFICATION_FIELDS, analysis["preparation"]),
        Path("identity_join_audit.json"): _json_bytes(analysis["audit"]),
        Path("unresolved_evidence_ledger.csv"): _csv_bytes(unresolved_fields, analysis["unresolved"]),
        Path("infrastructure_evidence_review.csv"): _csv_bytes(infrastructure_fields, analysis["infrastructure"]),
        Path("proposed_classification_schema.json"): _json_bytes(_schema()),
        Path("reviewer_adjudication_guide_zh.md"): _review_guide().encode("utf-8"),
        Path("machine_proposal_summary.csv"): _csv_bytes(proposal_fields, analysis["proposal_summary"]),
        Path("provenance.json"): _json_bytes({
            "analysis_version": OUTPUT_RELATIVE.name,
            "start_head": START_HEAD,
            "taxonomy_version": TAXONOMY_VERSION,
            "taxonomy_codebook_sha256": SOURCE_HASHES[TAXONOMY_CODEBOOK],
            "diagnostics_runner_revision": DIAGNOSTICS_RUNNER_REVISION,
            "legacy_artifacts_overwritten": False,
            "formal_diagnostics_outputs_modified": False,
            "machine_preparation_completed": True,
            "formal_human_adjudication_completed": False,
            "evidence_role": "development",
        }),
        Path("execution_manifest.json"): _json_bytes({
            "status": "machine_classification_preparation_complete_human_adjudication_pending",
            "programs_prepared": 198,
            "human_review_queue": 196,
            "infrastructure_unclassified": 2,
            "formal_adjudications_completed": 0,
            "model_calls": 0,
            "evalplus_correctness_executions": 0,
            "formal_diagnostics_executions": 0,
            "partial_diagnostics_executions": 0,
            "healer_executions": 0,
            "validation_executions": 0,
            "diagnostics_allowed_as_healer_runtime_input": False,
        }),
    }
    source_rows = [
        {
            "path": path.as_posix(),
            "role": "external_taxonomy_codebook" if path.is_absolute() else "frozen_input",
            "sha256": digest,
        }
        for path, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())
    ]
    for path in (ANALYZER, TESTS):
        _require((repo / path).is_file(), f"missing reproducibility source: {path.as_posix()}")
        source_rows.append({"path": path.as_posix(), "role": "reproducibility_source", "sha256": _sha((repo / path).read_bytes())})
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), source_rows)

    output_hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    manifest = {
        "manifest_version": OUTPUT_RELATIVE.name,
        "status": "machine_preparation_complete_formal_adjudication_not_completed",
        "taxonomy_version": TAXONOMY_VERSION,
        "diagnostics_runner_revision": DIAGNOSTICS_RUNNER_REVISION,
        "programs": 198,
        "usable_diagnostics": 196,
        "infrastructure_invalid_unclassified": 2,
        "human_review_queue": 196,
        "formal_adjudications_completed": 0,
        "formal_diagnostics_results_sha256": SOURCE_HASHES[FORMAL_RESULTS],
        "formal_diagnostics_execution_manifest_sha256": SOURCE_HASHES[FORMAL_RECEIPT],
        "formal_diagnostics_source_manifest_sha256": SOURCE_HASHES[DIAGNOSTICS_SOURCE_MANIFEST],
        "diagnostics_allowed_as_healer_runtime_input": False,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "formal_diagnostics_executions": 0,
        "partial_diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "source_sha256": {
            ANALYZER.as_posix(): _sha((repo / ANALYZER).read_bytes()),
            TESTS.as_posix(): _sha((repo / TESTS).read_bytes()),
        },
        "outputs_sha256_excluding_manifest": output_hashes,
    }
    outputs[Path("manifest.json")] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    directory = repo / OUTPUT_RELATIVE
    directory.mkdir(parents=True, exist_ok=True)
    for relative, data in build_outputs(repo).items():
        (directory / relative).write_bytes(data)
    return directory


if __name__ == "__main__":
    print(write_outputs())
