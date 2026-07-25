"""Deterministically freeze the Ab2gA-short-v1 development preregistration.

This builder performs no model calls and executes no generated candidate code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


ARTIFACT_DIR = Path(
    "artifacts/public_benchmark_governance/ab2ga_short_v1_preregistration"
)
BASE_PATH = Path("configs/scaffolds/mbpp_generic_code_scaffold_v0.txt")
BASE_MANIFEST_PATH = Path(
    "configs/scaffolds/mbpp_generic_code_scaffold_v0_manifest.json"
)
FOUR_B_MANIFEST_PATH = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_development_failure_supply_pilot_preregistration_v1/"
    "manifest.json"
)
FOUR_B_CELLS_PATH = FOUR_B_MANIFEST_PATH.parent / "generation_cells.csv"
NINE_B_MANIFEST_PATH = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_development60_replay_r003_v1/manifest.json"
)
NINE_B_CELLS_PATH = NINE_B_MANIFEST_PATH.parent / "candidate_b_generation_cells.csv"
PROTOCOL_PATH = Path("configs/public_benchmark_generation_protocol_v1.json")
TASKS_PATH = Path("data/mbpp_plus/tasks.jsonl")
FROZEN_SPLIT_PATH = Path("artifacts/public_benchmark_governance/frozen_split.csv")
H1_MANIFEST_PATH = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/manifest.json"
)
H2_MANIFEST_PATH = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1/evaluation_manifest.json"
)

SOURCE_SHA256 = {
    BASE_PATH.as_posix(): "31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305",
    BASE_MANIFEST_PATH.as_posix(): "b48576bf74c6b5aae1a3f4a4c4266da5ee78e1df8e77f877b67f903e9ada93da",
    FOUR_B_MANIFEST_PATH.as_posix(): "955a0b463e2ca6a71b76ed745a266977c5cd7005562e621a1b8091a28fd3eccb",
    FOUR_B_CELLS_PATH.as_posix(): "1d6c1dfc85d3b607eb99da0b2c2cb055fd56764225c281233a8c3c4e0ff5f7b3",
    NINE_B_MANIFEST_PATH.as_posix(): "e8d0f8e9198848e8708d910f6c859622c272de850a2b1045d62993c114c98fbd",
    NINE_B_CELLS_PATH.as_posix(): "1e7ab332d441f0fff207f8ec80ac24379184b39387f569e2e6985c232c0effc5",
    PROTOCOL_PATH.as_posix(): "987fb107bd6b36703ba6289fbd89a2aa69856031fd82402600794915ae0b583d",
    TASKS_PATH.as_posix(): "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    FROZEN_SPLIT_PATH.as_posix(): "3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4",
    H1_MANIFEST_PATH.as_posix(): "420eb05267f11f4f9f157f63167398e86fbc68322f33b33b9bf5656fb6f24913",
    H2_MANIFEST_PATH.as_posix(): "f7fda43aa37f100925ba704f042159ff0aa94dfef644a832fd5a85529ff90728",
}

BASE_SHA256 = SOURCE_SHA256[BASE_PATH.as_posix()]
H1_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
H2_SHA256 = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
PROMPT_SEPARATOR = "\n\n--- GENERIC CODE SCAFFOLD V0 ---\n\n"
INCREMENTAL_SEPARATOR = "\n"
INCREMENTAL_BLOCK = (
    "Before writing the final code, internally:\n"
    "1. identify an algorithm that handles all valid inputs;\n"
    "2. check important edge cases and index boundaries;\n"
    "3. verify the return value and type;\n"
    "4. mentally test one normal case and one edge case.\n"
)
CONDITION_ID = "Ab2gA-short-v1-Raw"
RUN_ID = "mbpp_q35_4b_9b_ab2ga_short_v1_development_transfer_r001"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return (
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in rows
        )
    ).encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_sources(repo_root: Path) -> None:
    for relative, expected in SOURCE_SHA256.items():
        actual = sha256_bytes((repo_root / relative).read_bytes())
        require(actual == expected, f"source SHA drift: {relative}: {actual}")


def load_authorities(repo_root: Path) -> dict[str, Any]:
    verify_sources(repo_root)
    base_manifest = load_json(repo_root / BASE_MANIFEST_PATH)
    four_b = load_json(repo_root / FOUR_B_MANIFEST_PATH)
    nine_b = load_json(repo_root / NINE_B_MANIFEST_PATH)
    protocol = load_json(repo_root / PROTOCOL_PATH)
    h1 = load_json(repo_root / H1_MANIFEST_PATH)
    h2 = load_json(repo_root / H2_MANIFEST_PATH)

    require(base_manifest["sha256"] == BASE_SHA256, "Ab2g manifest SHA mismatch")
    require(
        base_manifest["prompt_composition_order"]
        == [
            "official_task_prompt_verbatim",
            "fixed_separator",
            "mbpp_generic_code_scaffold_v0",
        ],
        "Ab2g composition order drift",
    )
    require(base_manifest["separator"]["exact_text_utf8"] == PROMPT_SEPARATOR, "separator drift")
    require(four_b["design"]["tasks"] == 20, "4B task count drift")
    require(four_b["design"]["seeds"] == [11, 22, 33, 44, 55], "4B seeds drift")
    require(nine_b["seeds"] == [11, 22, 33, 44, 55], "9B seeds drift")
    require(protocol["seeds"] == [11, 22, 33, 44, 55], "protocol seeds drift")
    require(
        four_b["parity_with_9b"]["generation_options"] == protocol["generation"],
        "4B decoding parameters drift",
    )
    require(nine_b["generation_parameters"] == protocol["generation"], "9B decoding drift")
    require(h1["healer_sha256"] == H1_SHA256, "H1 SHA drift")
    require(h2["rule_sha256"] == H2_SHA256, "H2 rule SHA drift")
    require(
        h2["freeze_decision"] == "development_candidate_not_frozen",
        "H2 role/status drift",
    )
    return {
        "base_manifest": base_manifest,
        "four_b": four_b,
        "nine_b": nine_b,
        "protocol": protocol,
        "h1": h1,
        "h2": h2,
    }


def load_prompts(repo_root: Path, task_ids: list[str]) -> dict[str, str]:
    wanted = set(task_ids)
    prompts: dict[str, str] = {}
    with (repo_root / TASKS_PATH).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] in wanted:
                require(
                    set(row) == {"task_id", "prompt", "entry_point"},
                    f"unexpected task fields: {row['task_id']}",
                )
                prompts[row["task_id"]] = row["prompt"]
    require(set(prompts) == wanted, "missing or extra official prompts")
    return prompts


def verify_pairing_sources(
    repo_root: Path, task_ids: list[str], seeds: list[int], prompts: dict[str, str]
) -> None:
    expected = {(task, str(seed)) for task in task_ids for seed in seeds}
    four_b_rows = [
        row
        for row in load_csv(repo_root / FOUR_B_CELLS_PATH)
        if row["condition_id"] == "Ab2g_H1"
    ]
    require(len(four_b_rows) == 100, "4B Ab2g cell count drift")
    require(
        {(row["task_id"], row["seed"]) for row in four_b_rows} == expected,
        "4B task-seed pairing drift",
    )
    nine_b_rows = [
        row
        for row in load_csv(repo_root / NINE_B_CELLS_PATH)
        if row["task_id"] in set(task_ids)
    ]
    require(len(nine_b_rows) == 100, "9B selected task cell count drift")
    require(
        {(row["task_id"], row["seed"]) for row in nine_b_rows} == expected,
        "9B task-seed pairing drift",
    )
    official_hash = {
        task_id: sha256_bytes(prompts[task_id].encode("utf-8")) for task_id in task_ids
    }
    for row in four_b_rows + nine_b_rows:
        require(
            row["official_prompt_sha256"] == official_hash[row["task_id"]],
            f"official prompt SHA drift: {row['task_id']}",
        )


def build_cells(
    task_ids: list[str],
    seeds: list[int],
    prompts: dict[str, str],
    models: list[dict[str, Any]],
    composite_scaffold: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plan: list[dict[str, Any]] = []
    prompt_rows: list[dict[str, Any]] = []
    cell_index = 0
    for model in models:
        for task_id in task_ids:
            official = prompts[task_id]
            complete_prompt = official + PROMPT_SEPARATOR + composite_scaffold
            official_sha = sha256_bytes(official.encode("utf-8"))
            complete_sha = sha256_bytes(complete_prompt.encode("utf-8"))
            for sample_index, seed in enumerate(seeds, start=1):
                identity_material = {
                    "condition_id": CONDITION_ID,
                    "model_digest": model["digest"],
                    "model_tag": model["tag"],
                    "run_id": RUN_ID,
                    "seed": seed,
                    "task_id": task_id,
                }
                cell_identity = sha256_bytes(
                    json.dumps(
                        identity_material, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8")
                )
                cell_index += 1
                common = {
                    "cell_index": cell_index,
                    "cell_identity": cell_identity,
                    "model_role": model["role"],
                    "model_tag": model["tag"],
                    "model_digest": model["digest"],
                    "quantization": model["quantization"],
                    "task_id": task_id,
                    "seed": seed,
                    "sample_index": sample_index,
                    "condition_id": CONDITION_ID,
                    "official_prompt_sha256": official_sha,
                    "complete_prompt_sha256": complete_sha,
                    "execution_state": "preregistered_not_executed",
                }
                plan.append(common)
                prompt_rows.append({**common, "complete_prompt": complete_prompt})
    require(len(plan) == 200, f"expected 200 cells, got {len(plan)}")
    require(len({row["cell_identity"] for row in plan}) == 200, "cell identity collision")
    require(
        Counter(row["model_tag"] for row in plan)
        == Counter({"qwen3.5:4b": 100, "qwen3.5:9b": 100}),
        "model distribution drift",
    )
    require(
        all(
            Counter(
                (row["task_id"], row["seed"])
                for row in plan
                if row["model_tag"] == model["tag"]
            )
            == Counter((task, seed) for task in task_ids for seed in seeds)
            for model in models
        ),
        "paired design drift",
    )
    return plan, prompt_rows


def build_core_outputs(repo_root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    authority = load_authorities(repo_root)
    four_b = authority["four_b"]
    protocol = authority["protocol"]
    task_ids = four_b["split_policy"]["task_ids"]
    seeds = four_b["design"]["seeds"]
    prompts = load_prompts(repo_root, task_ids)
    verify_pairing_sources(repo_root, task_ids, seeds, prompts)

    base_bytes = (repo_root / BASE_PATH).read_bytes()
    require(sha256_bytes(base_bytes) == BASE_SHA256, "Ab2g base bytes changed")
    require(base_bytes.endswith(b"\n") and b"\r" not in base_bytes, "Ab2g LF contract drift")
    increment_bytes = INCREMENTAL_BLOCK.encode("utf-8")
    composite_bytes = base_bytes + INCREMENTAL_SEPARATOR.encode("utf-8") + increment_bytes
    require(composite_bytes.startswith(base_bytes), "Ab2g is not a bitwise prefix")
    composite_text = composite_bytes.decode("utf-8")
    incremental_sha = sha256_bytes(increment_bytes)
    composite_sha = sha256_bytes(composite_bytes)

    model_order = [
        protocol["models"]["frozen_transfer_model"],
        protocol["models"]["primary_development_model"],
    ]
    plan, prompt_rows = build_cells(
        task_ids, seeds, prompts, model_order, composite_text
    )

    spec = {
        "scaffold_id": "Ab2gA-short-v1",
        "status": "frozen_development_condition_transfer_increment",
        "base": {
            "formal_source": BASE_PATH.as_posix(),
            "formal_manifest": BASE_MANIFEST_PATH.as_posix(),
            "sha256": BASE_SHA256,
            "size_bytes": len(base_bytes),
            "copied_artifact": "frozen_ab2g_base.txt",
            "bitwise_change": False,
        },
        "increment": {
            "sha256": incremental_sha,
            "size_bytes": len(increment_bytes),
            "copied_artifact": "frozen_incremental_block.txt",
            "final_newline": True,
            "line_endings": "LF",
        },
        "composition": {
            "scaffold_order": [
                "frozen_ab2g_base_bytes",
                "incremental_separator",
                "frozen_incremental_block_bytes",
            ],
            "incremental_separator_utf8": INCREMENTAL_SEPARATOR,
            "incremental_separator_hex": INCREMENTAL_SEPARATOR.encode().hex(),
            "composite_scaffold_sha256": composite_sha,
            "complete_prompt_order": [
                "official_task_prompt_verbatim",
                "existing_ab2g_prompt_separator",
                "composite_scaffold",
            ],
            "existing_ab2g_prompt_separator_utf8": PROMPT_SEPARATOR,
            "existing_ab2g_prompt_separator_sha256": sha256_bytes(
                PROMPT_SEPARATOR.encode("utf-8")
            ),
        },
        "prohibitions": {
            "rewrite_delete_or_reformat_ab2g": True,
            "additional_instructional_content": True,
            "cohort_expansion": True,
        },
    }
    preregistration = {
        "preregistration_id": "ab2ga_short_v1_preregistration",
        "status": "preregistered_frozen_not_executed",
        "research_role": "development_condition_transfer_increment",
        "confirmatory_claim_for_unseen_tasks": False,
        "scope": "Stage2_MBPP+_existing_development20_only",
        "primary_comparisons": [
            "Ab2g-Raw vs Ab2gA-short-v1-Raw",
            "Raw vs existing frozen H1",
        ],
        "h1": {
            "role": "existing_frozen_evaluator_blind_healer",
            "rule_order": ["entrypoint_alias_unique_arity_compatible_v0"],
            "sha256": H1_SHA256,
            "modification_allowed": False,
        },
        "h2": {
            "role": "prospectively_fixed_development_candidate_evaluation_only",
            "name_must_not_be_claimed": "frozen Healer",
            "sha256": H2_SHA256,
            "modification_allowed": False,
            "current_status": "development_candidate_not_frozen",
        },
        "models": model_order,
        "generation_parameters": protocol["generation"],
        "tasks": task_ids,
        "seeds": seeds,
        "counts": {"cells": 200, "qwen3.5:4b": 100, "qwen3.5:9b": 100},
        "metrics": [
            "Base pass",
            "Plus pass",
            "strict pass",
            "extractability",
            "parseability",
            "executability",
            "eligible",
            "transformed",
            "abstained",
            "blocker removed",
            "verified rescue",
            "partial repair",
            "regression",
            "preserved pass",
            "failure layer",
            "failure chain",
            "per-cell paired transition",
        ],
        "paired_analysis": {
            "unit": "model_tag × task_id × seed",
            "pairing": "exact",
            "report_counts_and_paired_transitions": True,
            "no_post_outcome_cell_exclusion": True,
        },
        "execution_state": {
            "model_calls": 0,
            "candidate_executions": 0,
            "evalplus_executions": 0,
            "raw_outputs_materialized": 0,
        },
        "forbidden_this_round": [
            "model calls",
            "candidate execution",
            "EvalPlus execution",
            "H1 modification",
            "H2 modification",
            "Ab2g modification",
            "old result modification",
            "fabricated Raw output",
            "cohort expansion",
        ],
    }

    plan_fields = [
        "cell_index",
        "cell_identity",
        "model_role",
        "model_tag",
        "model_digest",
        "quantization",
        "task_id",
        "seed",
        "sample_index",
        "condition_id",
        "official_prompt_sha256",
        "complete_prompt_sha256",
        "execution_state",
    ]
    artifact_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "schema_id": "ab2ga_short_v1_preregistration_schema",
        "cell_plan": {
            "format": "CSV UTF-8 LF",
            "row_count": 200,
            "required_columns_in_order": plan_fields,
            "unique_key": ["cell_identity"],
            "paired_key": ["model_tag", "task_id", "seed"],
        },
        "complete_prompt_manifest": {
            "format": "JSON Lines UTF-8 LF",
            "row_count": 200,
            "required_fields": plan_fields + ["complete_prompt"],
            "sha_contract": "sha256(UTF-8 complete_prompt) == complete_prompt_sha256",
        },
        "scaffold": {
            "base_contract": "frozen_ab2g_base.txt is byte-identical to formal source",
            "composition_contract": (
                "base_bytes + UTF-8 incremental_separator + incremental_block_bytes"
            ),
        },
        "execution_counts": {
            "model_calls": {"const": 0},
            "candidate_executions": {"const": 0},
            "evalplus_executions": {"const": 0},
        },
    }
    unique_prompt_hashes = sorted({row["complete_prompt_sha256"] for row in plan})
    prompt_hash_set_sha = sha256_bytes(("\n".join(unique_prompt_hashes) + "\n").encode())
    context = {
        "task_ids": task_ids,
        "seeds": seeds,
        "incremental_sha256": incremental_sha,
        "composite_scaffold_sha256": composite_sha,
        "unique_complete_prompt_count": len(unique_prompt_hashes),
        "complete_prompt_sha256_set_sha256": prompt_hash_set_sha,
    }
    outputs = {
        "frozen_ab2g_base.txt": base_bytes,
        "frozen_incremental_block.txt": increment_bytes,
        "scaffold_spec.json": canonical_json_bytes(spec),
        "schema.json": canonical_json_bytes(artifact_schema),
        "cell_plan.csv": csv_bytes(plan, plan_fields),
        "complete_prompt_manifest.jsonl": jsonl_bytes(prompt_rows),
        "preregistration.json": canonical_json_bytes(preregistration),
        "preregistration.md": preregistration_markdown(context),
        "research_note_zh.md": research_note_zh(context),
    }
    return outputs, context


def preregistration_markdown(context: dict[str, Any]) -> bytes:
    text = f"""# Ab2gA-short-v1 生成與評測預登錄

狀態：`preregistered_frozen_not_executed`

本研究是 development／condition-transfer 增量實驗，只使用既有 development20；不得宣稱為未見 task 的 confirmatory validation。

## 鷹架凍結

Ab2gA-short-v1 僅由正式凍結 Ab2g 原 bytes、單一 LF 分隔及唯一增量段落組成。Ab2g 不改寫、不刪減、不重新排版。Ab2g SHA-256 為 `{BASE_SHA256}`；增量段落 SHA-256 為 `{context['incremental_sha256']}`；合成鷹架 SHA-256 為 `{context['composite_scaffold_sha256']}`。

## 設計

固定 20 題、seeds 11／22／33／44／55；qwen3.5:4b 與 qwen3.5:9b 各 100 格，共 200 格。模型 digest、Q4_K_M 量化及 temperature=0.2、top_p=0.95、top_k=20、num_ctx=8192、num_predict=2048、thinking=false、stream=false 均沿用正式 manifest，不換題、不換 seed、不改參數。

主要比較為 Ab2g-Raw vs Ab2gA-short-v1-Raw，以及 Raw vs 既有 frozen H1。H2 僅按 SHA `{H2_SHA256}` 作前瞻固定的 development-candidate 評測；其狀態是 `development_candidate_not_frozen`，不得稱為 frozen Healer。

## 指標與配對

預先報告 Base／Plus／strict pass、可抽取率、可解析率、可執行率、eligible、transformed、abstained、blocker removed、verified rescue、partial repair、regression、preserved pass、failure layer、failure chain，以及以 model × task × seed 為單位的逐格配對轉換。

本輪模型呼叫、candidate 執行、EvalPlus、Raw 假資料、cohort 擴充，以及 H1／H2／Ab2g／舊結果修改均為零。
"""
    return text.encode("utf-8")


def research_note_zh(context: dict[str, Any]) -> bytes:
    tasks = "、".join(context["task_ids"])
    text = f"""# Ab2gA-short-v1 中文研究說明

H2 功能評測已於 commit `30ed664e2bf75e8afca612e8eec99e7c75b87f61` 完成，觀察到 71 transformed、46 partial repair、0 rescue、0 regression；決策為 `development_candidate_not_frozen`。本次只凍結下一輪演算法鷹架的設計、完整提示與評測預登錄，不生成答案也不執行程式。

研究問題是：在不改動既有 Ab2g 輸出約束的前提下，加入短版內部演算法檢查段落，是否改善 Raw 語意正確率及失敗分布。這是 development／condition-transfer 證據，不是未見題目的驗證。

固定題目為：{tasks}。每題固定五個 seeds，4B／9B 使用同一題目與 seed 配對，共 200 個唯一 cell identity。完整 prompt 逐格保存在 `complete_prompt_manifest.jsonl`；因 seed 與模型不改變 prompt 文字，200 格對應 {context['unique_complete_prompt_count']} 個唯一 prompt hashes，hash 集合的 SHA-256 為 `{context['complete_prompt_sha256_set_sha256']}`。

H1 保持既有 frozen evaluator-blind healer 角色；H2 保持指定 rule SHA，僅作前瞻固定的 development-candidate 分析。任何後驗規則修改、格子排除或 confirmatory 宣稱都不允許。
"""
    return text.encode("utf-8")


def build_outputs(repo_root: Path) -> dict[str, bytes]:
    outputs, context = build_core_outputs(repo_root)
    core_hashes = {name: sha256_bytes(data) for name, data in sorted(outputs.items())}
    tooling_paths = [
        Path("scripts/build_ab2ga_short_v1_preregistration.py"),
        Path("scripts/preflight_ab2ga_short_v1_preregistration.py"),
        Path("tests/test_ab2ga_short_v1_preregistration.py"),
    ]
    tooling_sha256 = {
        path.as_posix(): sha256_bytes((repo_root / path).read_bytes())
        for path in tooling_paths
    }
    receipt = {
        "receipt_id": "ab2ga_short_v1_deterministic_build_receipt",
        "builder": "scripts/build_ab2ga_short_v1_preregistration.py",
        "status": "deterministic_rebuild_verified_by_byte_comparison",
        "source_sha256": SOURCE_SHA256,
        "tooling_sha256": tooling_sha256,
        "core_output_sha256": core_hashes,
        "counts": {
            "cells": 200,
            "qwen3.5:4b": 100,
            "qwen3.5:9b": 100,
            "unique_complete_prompts": context["unique_complete_prompt_count"],
        },
        "sha256": {
            "ab2g_base": BASE_SHA256,
            "incremental_block": context["incremental_sha256"],
            "composite_scaffold": context["composite_scaffold_sha256"],
            "complete_prompt_hash_set": context["complete_prompt_sha256_set_sha256"],
        },
        "execution_counts": {
            "model_calls": 0,
            "candidate_executions": 0,
            "evalplus_executions": 0,
        },
    }
    outputs["build_receipt.json"] = canonical_json_bytes(receipt)
    artifact_hashes = {name: sha256_bytes(data) for name, data in sorted(outputs.items())}
    artifact_manifest = {
        "manifest_id": "ab2ga_short_v1_preregistration_artifacts",
        "status": "frozen_preregistered_not_executed",
        "artifact_sha256_excluding_manifest": artifact_hashes,
        "source_provenance": SOURCE_SHA256,
    }
    outputs["artifact_manifest.json"] = canonical_json_bytes(artifact_manifest)
    return outputs


def write_or_check(repo_root: Path, *, check: bool) -> None:
    expected = build_outputs(repo_root)
    output_dir = repo_root / ARTIFACT_DIR
    if check:
        actual_names = (
            {path.name for path in output_dir.iterdir() if path.is_file()}
            if output_dir.exists()
            else set()
        )
        require(actual_names == set(expected), "artifact file set drift")
        for name, data in expected.items():
            require((output_dir / name).read_bytes() == data, f"rebuild drift: {name}")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        (output_dir / name).write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(args.repo_root.resolve(), check=args.check)
    print("ab2ga_short_v1_preregistration: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
