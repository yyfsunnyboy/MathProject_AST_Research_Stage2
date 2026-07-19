#!/usr/bin/env python3
"""Freeze the Candidate B replay over the existing 60-task MBPP+ development set.

This is an offline, zero-model materializer.  It validates the existing P0
generations and H0/H1 results, but never imports EvalPlus and never creates a
generation run directory.
"""

from __future__ import annotations

import argparse
import ast
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

from scripts import prepare_mbpp_existing600_healer_h0_h1 as existing  # noqa: E402


OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/candidate_b_development60_replay_r002_v1"
)
R001_RUN_ID = "mbpp_q35_9b_candidate_b_development60_replay_r001"
R001_RUN_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r001"
)
RUN_ID = "mbpp_q35_9b_candidate_b_development60_replay_r002"
RUN_OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r002"
)
PROTOCOL_RELATIVE = Path("configs/public_benchmark_generation_protocol_v1.json")
HEALER_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py")
PIPELINE_RELATIVE = Path("agent_tools/finals_rebuild/extraction.py")
OLLAMA_RUNNER_RELATIVE = Path("agent_tools/finals_rebuild/ollama_generation_runner.py")
PAIRED_CELLS_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
    "paired_analysis_run_001/paired_cell_results.csv"
)
EXISTING_ACCOUNTS_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
    "h0_h1_accounts.csv"
)
PAIRED_MANIFEST_RELATIVE = Path(
    "artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/"
    "paired_analysis_run_001/paired_analysis_manifest.json"
)
PREPARATION_SOURCE_RELATIVE = Path("scripts/prepare_mbpp_existing600_healer_h0_h1.py")
CANDIDATE_TEXT_SOURCE_RELATIVE = Path(
    "artifacts/public_benchmark_governance/factorial_development_qualification_v1/"
    "candidate_b_exact_text.txt"
)
VALIDATION_RUN_RELATIVE = Path(
    "artifacts/public_benchmark_validation/mbpp_healer_v0_p0/runs/"
    "mbpp_q35_9b_healer_v0_validation_p0_r001"
)
INTERRUPTED_B28_RELATIVE = Path("artifacts/pbd/mbpp_b28")

EXPECTED_HEALER_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
EXPECTED_PIPELINE_SHA256 = "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
EXPECTED_OLLAMA_RUNNER_SHA256 = "9ccaa465c38030a3786a4423fed984b4624f44573ed6b1321e4b4fcbd5071d81"
EXPECTED_PROTOCOL_SHA256 = "987fb107bd6b36703ba6289fbd89a2aa69856031fd82402600794915ae0b583d"
EXPECTED_PAIRED_CELLS_SHA256 = "cb2e12432c1c24abe18e446aaf1eee33b4ebf81f4c4166d083dfeb1540960bee"
EXPECTED_EXISTING_ACCOUNTS_SHA256 = "e6f26c7bfb1418080f3df80a78202808aa2ba9f5992ba397b24d8914df979438"
EXPECTED_CANDIDATE_TEXT_SHA256 = "bd91435816a1aa89afa23f1a1c0f3dc60f5890abfae9acaea6496db4441fb719"
EXPECTED_PAIRED_MANIFEST_SHA256 = "f277e775186ac43086081849aa3563f65892a79e870b7ab77f7e63fc13fcbda5"
EXPECTED_PREPARATION_SOURCE_SHA256 = "c6e26629dc0f2c0c91d864502bd3c600d4b4856fd0b68de8cc9ceb94479eaa55"
EXPECTED_HEALER_RULE = "entrypoint_alias_unique_arity_compatible_v0"
EXPECTED_MODEL = "qwen3.5:9b"
EXPECTED_MODEL_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
EXPECTED_QUANTIZATION = "Q4_K_M"
EXPECTED_DATASET_VERSION = "v0.2.0"
EXPECTED_DATASET_HASH = "ee43ecabebf20deef4bb776a405ac5b1"
SEEDS = (11, 22, 33, 44, 55)
SEPARATOR = "\n\n"
CANDIDATE_B_TEXT = (
    "Return exactly one concise, complete, executable Python source file.\n"
    "Use the exact required function name and parameters, include required imports, "
    "and finish the implementation within the output limit.\n"
    "Do not use Markdown fences or explanatory text; output only Python code.\n"
)
GENERATION_OPTIONS = {
    "num_ctx": 8192,
    "num_predict": 2048,
    "stream": False,
    "temperature": 0.2,
    "thinking": False,
    "top_k": 20,
    "top_p": 0.95,
}
P0_SOURCE_HASHES = {
    Path("artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/mbpp_qwen35_9b_ab1_dev_run_003/generation_plan.json"): "3c4e61db0588bd237e415f7cb0b8fde05d3db67c19a012968a4d676e37a56be5",
    Path("artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/mbpp_qwen35_9b_ab1_dev_run_003/raw_generations.jsonl"): "24cc22a57f252f46a633dba34d53652398f0b2cf213363af774b82f90bcc9964",
    Path("artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/mbpp_qwen35_9b_ab1_dev_run_003/pipeline_corrected.jsonl"): "4a8015fec50b4dd1e0d432f66bb01d6972dc2ed73ec748a36773bed2b10531fa",
    Path("artifacts/public_benchmark_development/mbpp_qwen35_9b_ab1/runs/mbpp_qwen35_9b_ab1_dev_run_003/evaluation_results.csv"): "86525489640c2076dfd4d35e7224a975ca0b5770fe8ad99019476b4d0c1ed54d",
    Path("artifacts/pbd/mbpp_e40/p0/r001/generation_plan.json"): "cee8e9908bfb9759189b290e8b3f13a7609e3ec80395585f07b9c0425f255531",
    Path("artifacts/pbd/mbpp_e40/p0/r001/raw_generations.jsonl"): "2e89154a4723f9b3a95a7605250498079065e65708bfd1c6ede235a0f7e19596",
    Path("artifacts/pbd/mbpp_e40/p0/r001/pipeline_corrected.jsonl"): "7cc419aaa8587e0648e9b198270c2efd388fccd67c8331e0629b0374a8fcf402",
    Path("artifacts/pbd/mbpp_e40/p0/r001/evaluation_results.csv"): "a0e359f292774206343aa8ca7892dd6254433e7b4a105e9bfa83e1f788f592ed",
}

CELL_FIELDS = (
    "cell_index", "development_layer", "run_id", "task_id", "seed",
    "sample_index", "task_seed_identity", "generation_id", "program_id",
    "official_prompt_sha256", "candidate_b_text_sha256",
    "composed_prompt_sha256", "prompt_contract_sha256", "attempt_count",
)
ACCOUNT_FIELDS = (
    "account_index", "factorial_arm", "prompt_condition", "healer_account",
    "program_id", "evaluation_account_id", "development_layer", "run_id",
    "task_id", "seed", "generation_id", "raw_sha256",
    "pipeline_normalized_sha256", "evaluation_source_sha256",
    "result_disposition", "existing_result_status", "healer_rule_id",
    "same_generation_h0_h1", "development_replay_only",
)
REUSE_FIELDS = (
    "program_id", "development_layer", "task_id", "seed", "generation_id",
    "raw_sha256", "pipeline_normalized_sha256", "h0_account_id",
    "h1_account_id", "h0_status", "h1_status", "identity_verified",
    "raw_hash_verified", "normalized_hash_verified", "result_reexecution",
)
IDENTITY_MAPPING_FIELDS = (
    "mapping_index", "development_layer", "task_id", "seed",
    "task_seed_research_identity", "r001_generation_id", "r001_program_id",
    "r002_generation_id", "r002_program_id", "same_task_seed_identity",
    "r001_result_reused", "r001_response_available",
)


class CandidateBFreezeError(RuntimeError):
    """Raised before writes when any replay invariant drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateBFreezeError(message)


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_hash(repo_root: Path, relative: Path, expected_hash: str) -> str:
    actual = _sha256_bytes((repo_root / relative).read_bytes())
    _require(actual == expected_hash, f"source SHA-256 drift: {relative.as_posix()}")
    return actual


def _prompt_contract(prompt: str) -> tuple[str, tuple[int, ...]]:
    calls: list[ast.Call] = []
    for line in prompt.splitlines():
        if not line.strip().startswith("assert "):
            continue
        try:
            tree = ast.parse(line.strip())
        except SyntaxError:
            continue
        calls.extend(
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id not in existing._BUILTIN_CALLS
        )
    names = {call.func.id for call in calls}
    _require(len(names) == 1, "development prompt entry-point contract drift")
    entry = next(iter(names))
    arities = tuple(sorted({len(call.args) for call in calls if call.func.id == entry and not call.keywords}))
    _require(bool(arities), "development prompt arity contract missing")
    return entry, arities


def load_existing_p0(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Mechanically load and cross-check only the two frozen P0 development runs."""
    paired = _read_csv(repo_root / PAIRED_CELLS_RELATIVE)
    paired = [row for row in paired if row["prompt_condition"] == "p0"]
    accounts = _read_csv(repo_root / EXISTING_ACCOUNTS_RELATIVE)
    accounts = [row for row in accounts if row["prompt_condition"] == "p0"]
    _require(len(paired) == 300, "existing P0 paired result count must be 300")
    _require(len(accounts) == 600, "existing P0 H0/H1 account count must be 600")
    _require(len({row["program_id"] for row in paired}) == 300, "duplicate existing P0 program")
    _require(len({row["evaluation_account_id"] for row in accounts}) == 600, "duplicate existing P0 account")
    _require(sum(row["h0_pass"] == "true" for row in paired) == 68, "existing P0 H0 pass count drift")
    _require(sum(row["h1_pass"] == "true" for row in paired) == 77, "existing P0 H1 pass count drift")
    paired_by_key = {(row["task_id"], int(row["seed"])): row for row in paired}
    account_by_key = {
        (row["task_id"], int(row["seed"]), row["healer_account"]): row
        for row in accounts
    }
    _require(len(paired_by_key) == 300 and len(account_by_key) == 600, "existing P0 identity duplication")

    result: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for pairing in existing.RUNS:
        spec = pairing["baseline"]
        run = existing._load_run(repo_root, spec)
        _require(len(run["keys"]) == pairing["expected_cells"], "existing P0 run count drift")
        for task_id, seed in run["keys"]:
            key = (task_id, seed)
            _require(key not in seen, "cross-layer P0 identity duplicate")
            seen.add(key)
            raw = run["raw"][key]
            pipeline = run["pipeline"][key]
            pair = paired_by_key[key]
            h0 = account_by_key[(task_id, seed, "H0")]
            h1 = account_by_key[(task_id, seed, "H1")]
            _require(pair["program_id"] == h0["program_id"] == h1["program_id"], "P0 program identity drift")
            _require(pair["generation_id"] == raw["generation_id"] == h0["generation_id"] == h1["generation_id"], "P0 generation identity drift")
            _require(pair["raw_sha256"] == raw["raw_response_sha256"] == h0["raw_sha256"] == h1["raw_sha256"], "P0 raw hash drift")
            normalized_hash = pipeline["pipeline_corrected_output_sha256"] or ""
            _require(pair["normalized_source_sha256"] == normalized_hash, "P0 normalized hash drift")
            prompt = raw["request"]["messages"][0]["content"]
            contract = _prompt_contract(prompt)
            result.append({
                "development_layer": pairing["development_layer"],
                "run_id": spec["run_id"], "task_id": task_id, "seed": seed,
                "sample_index": int(raw.get("sample_index", SEEDS.index(seed))),
                "generation_id": raw["generation_id"], "program_id": pair["program_id"],
                "raw_sha256": raw["raw_response_sha256"],
                "normalized_sha256": normalized_hash,
                "prompt": prompt, "prompt_sha256": _sha256_text(prompt),
                "prompt_contract": contract,
                "h0_account_id": h0["evaluation_account_id"],
                "h1_account_id": h1["evaluation_account_id"],
                "h0_source_sha256": h0["evaluation_source_sha256"],
                "h1_source_sha256": h1["evaluation_source_sha256"],
                "h0_status": "pass" if pair["h0_pass"] == "true" else "fail",
                "h1_status": "pass" if pair["h1_pass"] == "true" else "fail",
            })
    _require(len(result) == len(seen) == 300, "existing P0 must contain 300 identities")
    _require(len({row["task_id"] for row in result}) == 60, "existing P0 must contain 60 tasks")
    _require(Counter(row["seed"] for row in result) == {seed: 60 for seed in SEEDS}, "P0 seed count drift")
    return result


def _candidate_generation_identity(run_id: str, row: dict[str, Any]) -> tuple[str, str]:
    generation_id = _identity_hash({
        "run_id": run_id, "task_id": row["task_id"], "seed": row["seed"],
        "model_digest": EXPECTED_MODEL_DIGEST,
        "official_prompt_sha256": row["prompt_sha256"],
        "candidate_b_text_sha256": EXPECTED_CANDIDATE_TEXT_SHA256,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
    })
    return generation_id, _identity_hash({"run_id": run_id, "generation_id": generation_id})


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    sources = {
        HEALER_RELATIVE: EXPECTED_HEALER_SHA256,
        PIPELINE_RELATIVE: EXPECTED_PIPELINE_SHA256,
        OLLAMA_RUNNER_RELATIVE: EXPECTED_OLLAMA_RUNNER_SHA256,
        PROTOCOL_RELATIVE: EXPECTED_PROTOCOL_SHA256,
        PAIRED_CELLS_RELATIVE: EXPECTED_PAIRED_CELLS_SHA256,
        EXISTING_ACCOUNTS_RELATIVE: EXPECTED_EXISTING_ACCOUNTS_SHA256,
        CANDIDATE_TEXT_SOURCE_RELATIVE: EXPECTED_CANDIDATE_TEXT_SHA256,
        PAIRED_MANIFEST_RELATIVE: EXPECTED_PAIRED_MANIFEST_SHA256,
        PREPARATION_SOURCE_RELATIVE: EXPECTED_PREPARATION_SOURCE_SHA256,
        **P0_SOURCE_HASHES,
    }
    source_hashes = {
        path.as_posix(): _source_hash(repo_root, path, digest)
        for path, digest in sources.items()
    }
    _require(_sha256_text(CANDIDATE_B_TEXT) == EXPECTED_CANDIDATE_TEXT_SHA256, "Candidate B constant hash drift")
    _require((repo_root / CANDIDATE_TEXT_SOURCE_RELATIVE).read_text(encoding="utf-8") == CANDIDATE_B_TEXT, "Candidate B source bytes drift")
    protocol = json.loads((repo_root / PROTOCOL_RELATIVE).read_text(encoding="utf-8"))
    primary = protocol["models"]["primary_development_model"]
    _require(primary["tag"] == EXPECTED_MODEL, "model tag drift")
    _require(primary["digest"] == EXPECTED_MODEL_DIGEST, "model digest drift")
    _require(primary["quantization"] == EXPECTED_QUANTIZATION, "quantization drift")
    _require(protocol["generation"] == {k: GENERATION_OPTIONS[k] for k in ("num_ctx", "num_predict", "stream", "temperature", "thinking", "top_k", "top_p")}, "generation parameter drift")
    _require(tuple(protocol["seeds"]) == SEEDS, "seed protocol drift")
    _require(not (repo_root / VALIDATION_RUN_RELATIVE).exists(), "Milestone 2K-A validation run must remain unexecuted")

    p0 = load_existing_p0(repo_root)
    cells: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    b_programs: dict[tuple[str, int], dict[str, str]] = {}
    for index, row in enumerate(p0, 1):
        entry, arities = row["prompt_contract"]
        composed = row["prompt"] + SEPARATOR + CANDIDATE_B_TEXT
        generation_id, program_id = _candidate_generation_identity(RUN_ID, row)
        r001_generation_id, r001_program_id = _candidate_generation_identity(R001_RUN_ID, row)
        b_programs[(row["task_id"], row["seed"])] = {
            "generation_id": generation_id, "program_id": program_id,
        }
        cells.append({
            "cell_index": index, "development_layer": row["development_layer"],
            "run_id": RUN_ID, "task_id": row["task_id"], "seed": row["seed"],
            "sample_index": row["sample_index"],
            "task_seed_identity": f"{row['task_id']}|seed={row['seed']}",
            "generation_id": generation_id, "program_id": program_id,
            "official_prompt_sha256": row["prompt_sha256"],
            "candidate_b_text_sha256": EXPECTED_CANDIDATE_TEXT_SHA256,
            "composed_prompt_sha256": _sha256_text(composed),
            "prompt_contract_sha256": _identity_hash({"entry_point": entry, "positional_arities": arities}),
            "attempt_count": 1,
        })
        mappings.append({
            "mapping_index": index, "development_layer": row["development_layer"],
            "task_id": row["task_id"], "seed": row["seed"],
            "task_seed_research_identity": f"{row['task_id']}|seed={row['seed']}",
            "r001_generation_id": r001_generation_id,
            "r001_program_id": r001_program_id,
            "r002_generation_id": generation_id, "r002_program_id": program_id,
            "same_task_seed_identity": "true", "r001_result_reused": "false",
            "r001_response_available": "false",
        })
    _require(len(cells) == len({row["generation_id"] for row in cells}) == 300, "Candidate B generation identity drift")
    _require(len(mappings) == 300, "r001/r002 identity mapping count drift")
    _require(all(row["r001_generation_id"] != row["r002_generation_id"] for row in mappings), "r002 generation IDs must be new")
    _require(all(row["same_task_seed_identity"] == "true" for row in mappings), "task-seed research identity drift")

    accounts: list[dict[str, Any]] = []
    reuse: list[dict[str, Any]] = []
    for row in p0:
        key = (row["task_id"], row["seed"])
        for arm in ("H0", "H1"):
            accounts.append({
                "account_index": len(accounts) + 1,
                "factorial_arm": f"P0_{arm}", "prompt_condition": "P0",
                "healer_account": arm, "program_id": row["program_id"],
                "evaluation_account_id": row[f"{arm.lower()}_account_id"],
                "development_layer": row["development_layer"], "run_id": row["run_id"],
                "task_id": row["task_id"], "seed": row["seed"],
                "generation_id": row["generation_id"], "raw_sha256": row["raw_sha256"],
                "pipeline_normalized_sha256": row["normalized_sha256"],
                "evaluation_source_sha256": row[f"{arm.lower()}_source_sha256"],
                "result_disposition": "reuse_existing_frozen_identity_hash_verified",
                "existing_result_status": row[f"{arm.lower()}_status"],
                "healer_rule_id": EXPECTED_HEALER_RULE if arm == "H1" else "not_applied_control",
                "same_generation_h0_h1": "true", "development_replay_only": "true",
            })
        reuse.append({
            "program_id": row["program_id"], "development_layer": row["development_layer"],
            "task_id": row["task_id"], "seed": row["seed"], "generation_id": row["generation_id"],
            "raw_sha256": row["raw_sha256"], "pipeline_normalized_sha256": row["normalized_sha256"],
            "h0_account_id": row["h0_account_id"], "h1_account_id": row["h1_account_id"],
            "h0_status": row["h0_status"], "h1_status": row["h1_status"],
            "identity_verified": "true", "raw_hash_verified": "true",
            "normalized_hash_verified": "true", "result_reexecution": "false",
        })
        planned = b_programs[key]
        for arm in ("H0", "H1"):
            account_id = _identity_hash({"program_id": planned["program_id"], "healer_account": arm})
            accounts.append({
                "account_index": len(accounts) + 1,
                "factorial_arm": f"Candidate_B_{arm}", "prompt_condition": "Candidate_B",
                "healer_account": arm, "program_id": planned["program_id"],
                "evaluation_account_id": account_id,
                "development_layer": row["development_layer"], "run_id": RUN_ID,
                "task_id": row["task_id"], "seed": row["seed"],
                "generation_id": planned["generation_id"], "raw_sha256": "pending_generation",
                "pipeline_normalized_sha256": "pending_pipeline",
                "evaluation_source_sha256": "pending_materialization",
                "result_disposition": "pending_future_manual_evalplus",
                "existing_result_status": "not_executed",
                "healer_rule_id": EXPECTED_HEALER_RULE if arm == "H1" else "not_applied_control",
                "same_generation_h0_h1": "true", "development_replay_only": "true",
            })
    _require(len(reuse) == 300, "P0 reuse ledger count drift")
    _require(len(accounts) == len({row["evaluation_account_id"] for row in accounts}) == 1200, "2x2 account count or uniqueness drift")
    _require(Counter(row["factorial_arm"] for row in accounts) == {
        "P0_H0": 300, "P0_H1": 300, "Candidate_B_H0": 300, "Candidate_B_H1": 300,
    }, "2x2 arm count drift")
    return {"p0": p0, "cells": cells, "accounts": accounts, "reuse": reuse, "mappings": mappings, "source_hashes": source_hashes}


def _operator_guide(manifest_sha: str = "<MANIFEST_SHA256>") -> bytes:
    command = (
        ".venv\\Scripts\\python.exe scripts\\run_mbpp_candidate_b_development60_replay.py generate "
        "--manifest artifacts\\public_benchmark_governance\\candidate_b_development60_replay_r002_v1\\manifest.json "
        f"--manifest-sha256 {manifest_sha}"
    )
    return f"""# Candidate B：既有60題 development 統一 replay 操作指南

此規格是development replay，不是validation或confirmatory evidence。P0的300份raw及600個H0/H1結果只按identity與SHA-256沿用；不得重新生成或重跑EvalPlus。Candidate B只生成300份raw，H0/H1共享同一raw與Pipeline輸入。

Candidate B文字SHA-256：`{EXPECTED_CANDIDATE_TEXT_SHA256}`。Healer固定為`{EXPECTED_HEALER_RULE}`。Pipeline correction不屬於Healer。

Runner禁止resume、retry、選擇性補跑與overwrite；每格只嘗試一次並以同目錄temporary file、flush、fsync、atomic rename及read-back hash保存journal。300格未全部完成時，不建立aggregate raw、Pipeline或H0/H1帳。Runner不含EvalPlus功能。

r001已永久登記為`ZERO_CELL_PREFLIGHT_INCIDENT`並保持原樣。只讀鑑識顯示其provenance含修復後runner專屬的identity-validation receipt，故可確定目錄由修復後`generate`路徑在模型身份驗證後建立；不是舊quantization-drift路徑，也不是不寫入run directory的zero-model preflight。r001只有frozen manifest、model provenance與空`j`目錄：model calls、generation journals、evaluator executions均登記為0，沒有response可供selective acceptance，不構成generation retry或resume。r002不讀取、沿用或比較r001內容；preflight只確認r001存在且journal仍為0。若r001出現任何journal，r002立即fail-closed並要求人工審查。

唯一人工生成指令（請由repository根目錄的PowerShell手動執行）：

```powershell
{command}
```

完成生成與evaluator-blind H0/H1 materialization後仍不得直接宣告功能結果；須由後續另行授權的EvalPlus與paired analysis依已凍結gate判定。
""".encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo_root)
    outputs = {
        "candidate_b_generation_cells.csv": _csv_bytes(analysis["cells"], CELL_FIELDS),
        "development_2x2_accounts.csv": _csv_bytes(analysis["accounts"], ACCOUNT_FIELDS),
        "p0_identity_hash_reuse_ledger.csv": _csv_bytes(analysis["reuse"], REUSE_FIELDS),
        "r001_to_r002_identity_mapping.csv": _csv_bytes(analysis["mappings"], IDENTITY_MAPPING_FIELDS),
    }
    incident = {
        "incident_id": "candidate_b_development60_r001_zero_cell_preflight_incident",
        "classification": "ZERO_CELL_PREFLIGHT_INCIDENT",
        "run_id": R001_RUN_ID,
        "run_output_relative": R001_RUN_OUTPUT_RELATIVE.as_posix(),
        "preservation_policy": "do_not_delete_move_rename_overwrite_reuse_or_read_as_results",
        "observed_directory_entries": ["frozen_manifest.json", "j/", "model_provenance.json"],
        "model_calls": 0, "generation_journals": 0,
        "evaluator_executions": 0, "candidate_b_responses": 0,
        "selective_acceptance_available": False,
        "generation_retry_or_resume": False,
        "cause_status": "resolved",
        "cause": "fixed_runner_generate_path_after_model_identity_validation_before_first_persisted_generation_journal",
        "cause_evidence": {
            "frozen_manifest_sha256": "cb6c36d5342da1096371946e58c5481291628ac28859a568ded95b11eada49e7",
            "model_provenance_sha256": "ddc1eb489e48de69af9ad6404a51c5dfd9b1b54e36beb715b2fd12cda347c777",
            "fixed_only_receipt_present": "candidate_b_identity_validation",
            "quantization_api_value_type": "str",
            "quantization_api_value": EXPECTED_QUANTIZATION,
            "old_quantization_drift_path_excluded": True,
            "zero_model_preflight_path_excluded": True,
        },
        "r001_content_used_by_r002": False,
    }
    outputs["r001_incident_ledger.json"] = _canonical_bytes(incident)
    execution_spec = {
        "spec_version": "candidate_b_development60_replay_r002_execution_v1",
        "status": "prepared_not_executed", "evidence_role": "development_replay_only",
        "run_id": RUN_ID, "run_output_relative": RUN_OUTPUT_RELATIVE.as_posix(),
        "sequence": ["immutable zero-model preflight", "verify model provenance", "300 single attempts with durable journals", "require all raw complete", "Pipeline all raw", "evaluator-blind H0/H1 fork", "wait for separately authorized EvalPlus"],
        "persistence": {"per_cell_journal": True, "flush_and_fsync": True, "same_directory_temp_file": True, "atomic_rename": True, "read_back_sha256": True},
        "forbidden": {"resume": True, "retry": True, "selective_rerun": True, "overwrite": True, "evalplus": True, "p0_reexecution": True, "validation_access": True},
        "model_identity_preflight": {
            "digest_api": "/api/tags models[].digest",
            "digest_comparison": "exact_string_equality",
            "quantization_api": "/api/tags models[].details.quantization_level",
            "quantization_expected": EXPECTED_QUANTIZATION,
            "quantization_normalization": "require_string_then_strip_then_upper",
            "missing_quantization": "fail_closed",
        },
        "predecessor_incident_policy": {
            "r001_classification": "ZERO_CELL_PREFLIGHT_INCIDENT",
            "r001_must_exist": True, "r001_expected_generation_journals": 0,
            "r001_any_journal": "fail_closed_require_manual_review",
            "r001_result_source": False, "r001_content_comparison": False,
            "r002_existing": "fail_closed_no_resume_retry_or_overwrite",
        },
    }
    analysis_spec = {
        "analysis_version": "candidate_b_development60_2x2_analysis_v1",
        "evidence_role": "development_replay_not_validation_or_confirmatory",
        "comparisons": ["P0_H0_vs_Candidate_B_H0", "P0_H1_vs_Candidate_B_H1", "P0_H0_to_H1", "Candidate_B_H0_to_H1"],
        "metrics": ["strict_python_only", "code_fence", "extra_text", "reasoning_leakage", "compile", "pass_rate", "paired_rescue", "paired_regression", "task_level", "cell_level", "exact_mcnemar_descriptive"],
        "candidate_b_format_gates": {"strict_python_only_min": 0.90, "code_fence_count_max": 0, "reasoning_leakage_count_max": 0, "undisclosed_prompt_contamination_count_max": 0},
        "candidate_b_functional_gate": {"candidate_b_h0_pass_gt_p0_h0": True, "paired_net_change_gt_0": True, "exact_mcnemar": "descriptive_only_no_unseen_data_inference"},
        "healer_results_separate_from_candidate_b_prompt_gate": ["H0_to_H1_rescue", "regression", "changed", "abstain", "no_trigger"],
        "post_result_rule_change_or_cell_exclusion": False,
    }
    zero = {"status": "zero_model_preflight_frozen", "tasks": 60, "existing_p0_programs": 300, "candidate_b_generation_cells": 300, "candidate_b_accounts": 600, "factorial_programs": 600, "factorial_accounts": 1200, "r001_incident_registered": True, "r001_expected_journals": 0, "r001_result_source": False, "r002_run_absent": True, "model_calls": 0, "evalplus_executions": 0, "validation_run_absent": True}
    outputs["execution_spec.json"] = _canonical_bytes(execution_spec)
    outputs["paired_analysis_spec.json"] = _canonical_bytes(analysis_spec)
    outputs["zero_model_preflight.json"] = _canonical_bytes(zero)
    outputs["candidate_b_exact_text.txt"] = CANDIDATE_B_TEXT.encode("utf-8")
    outputs["operator_guide_zh.md"] = _operator_guide()
    manifest = {
        "manifest_version": "candidate_b_development60_replay_r002_v1",
        "status": "prepared_not_executed", "development_replay_only": True,
        "validation_or_confirmatory_evidence": False,
        "counts": {"tasks": 60, "task_seed_identities": 300, "existing_p0_programs": 300, "candidate_b_new_generation_cells": 300, "candidate_b_new_accounts": 600, "factorial_programs": 600, "factorial_accounts": 1200},
        "existing_p0_results": {"h0_pass": 68, "h1_pass": 77, "programs": 300, "reexecuted": False},
        "candidate_b": {"exact_text_sha256": EXPECTED_CANDIDATE_TEXT_SHA256, "separator_utf8": SEPARATOR, "separator_sha256": _sha256_text(SEPARATOR), "generated_once": True},
        "run_id": RUN_ID, "run_output_relative": RUN_OUTPUT_RELATIVE.as_posix(),
        "model": EXPECTED_MODEL, "model_digest": EXPECTED_MODEL_DIGEST,
        "quantization": EXPECTED_QUANTIZATION, "generation_parameters": GENERATION_OPTIONS,
        "seeds": list(SEEDS), "dataset_version": EXPECTED_DATASET_VERSION,
        "dataset_hash": EXPECTED_DATASET_HASH,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "healer_sha256": EXPECTED_HEALER_SHA256, "healer_rule_order": [EXPECTED_HEALER_RULE],
        "model_identity_preflight": {
            "digest_json_path": "models[].digest", "digest_match": "exact",
            "quantization_json_path": "models[].details.quantization_level",
            "quantization_expected": EXPECTED_QUANTIZATION,
            "quantization_normalization": "strip_then_upper",
            "missing_or_non_string": "fail_closed",
        },
        "predecessor_incident": {
            "run_id": R001_RUN_ID,
            "classification": "ZERO_CELL_PREFLIGHT_INCIDENT",
            "model_calls": 0, "generation_journals": 0,
            "evaluator_executions": 0, "candidate_b_responses": 0,
            "selective_acceptance_available": False,
            "generation_retry_or_resume": False,
            "result_source": False,
        },
        "model_calls_during_freeze": 0, "evalplus_executions_during_freeze": 0,
        "validation_run_directory_created": False,
        "interrupted_mbpp_b28_used": False,
        "source_sha256": analysis["source_hashes"],
        "output_sha256_excluding_manifest_and_operator_guide": {
            name: _sha256_bytes(value) for name, value in sorted(outputs.items())
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
        for name, value in outputs.items():
            _require((output_dir / name).read_bytes() == value, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "output directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, value in outputs.items():
        (output_dir / name).write_bytes(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except (CandidateBFreezeError, existing.PreparationError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
