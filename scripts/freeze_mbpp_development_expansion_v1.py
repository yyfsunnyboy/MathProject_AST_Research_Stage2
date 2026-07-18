#!/usr/bin/env python3
"""Freeze the deterministic MBPP+ development-expansion overlay (Milestone 2D)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/development_expansion_v1"
)
FROZEN_SPLIT = Path("artifacts/public_benchmark_governance/frozen_split.csv")
FROZEN_SPLIT_SUMMARY = Path(
    "artifacts/public_benchmark_governance/frozen_split_summary.md"
)
CONTAMINATION_MANIFEST = Path(
    "artifacts/public_benchmark_governance/contamination_manifest.csv"
)
M2C_MANIFEST = Path(
    "artifacts/pbd/mbpp_sv0/r002/milestone_2c_v1_candidate_design/"
    "milestone_2c_manifest.json"
)
M2C_CANDIDATES = Path(
    "artifacts/pbd/mbpp_sv0/r002/milestone_2c_v1_candidate_design/"
    "scaffold_v1_candidates.json"
)

SOURCE_PATHS = {
    "frozen_split.csv": FROZEN_SPLIT,
    "frozen_split_summary.md": FROZEN_SPLIT_SUMMARY,
    "contamination_manifest.csv": CONTAMINATION_MANIFEST,
    "milestone_2c_manifest.json": M2C_MANIFEST,
    "scaffold_v1_candidates.json": M2C_CANDIDATES,
}
EXPECTED_SOURCE_HASHES = {
    "frozen_split.csv": "3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4",
    "frozen_split_summary.md": "b3aa7f56726d2d001903e54a9899e02ee51db8a1d3b4a999e3d3b308a2790786",
    "contamination_manifest.csv": "d19a136ab6c58c5f52e803b6351290cc628db73ff202e1546e7eea931bf18857",
    "milestone_2c_manifest.json": "3a6acb130affb5414228594367fc9fc41a9229e510ea1da9198efd57ad9b8ef3",
    "scaffold_v1_candidates.json": "6a19996316031697699f9ea9f3447d4a3df286e28e5c132a57cb8c6c65d6a54a",
}

STARTING_HEAD = "08764eb643947bbe23009bf4867e284f6500c0b7"
DATASET = "MBPP+"
DATASET_VERSION = "v0.2.0"
SOURCE_ROLE = "historical_development_pool"
SELECTION_SEED = "20260718"
SELECTION_SALT = "MathProject_AST_Research_Stage2|MBPP+|development_expansion_v1"
SELECTION_ALGORITHM = (
    "sha256(utf8(salt + LF + seed + LF + dataset + LF + dataset_version + LF + "
    "frozen_role + LF + task_id + LF)); sort by (selection_hash, task_id) ascending; "
    "select first 40 of the 96 non-active historical-development candidates"
)
SEEDS = (11, 22, 33, 44, 55)
EXPECTED_HISTORICAL_POOL = 116
EXPECTED_DISCOVERY = 20
EXPECTED_REMAINING = 96
EXPECTED_EXPANSION = 40
EXPECTED_TOTAL = 60
EXPECTED_IDENTITIES = 300
EXPECTED_CANDIDATE_A_TEXT_SHA256 = (
    "bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058"
)

ALLOWED_FROZEN_FIELDS = {
    "dataset",
    "dataset_version",
    "task_id",
    "proposed_role",
    "active_development_generation_subset",
    "split_assignment_status",
}
ALLOWED_CONTAMINATION_FIELDS = {
    "dataset",
    "task_id",
    "contamination_status",
    "confirmatory_eligible",
}
FORBIDDEN_SELECTION_FIELDS = {
    "prompt",
    "answer",
    "tests",
    "test",
    "canonical_solution",
    "solution",
    "model_output",
    "output",
    "failure_category",
    "pass_status",
    "evaluation_result",
}

CSV_FIELDS = (
    "dataset",
    "dataset_version",
    "task_id",
    "source_frozen_governance_role",
    "development_layer",
    "original_active_development_subset",
    "selection_eligible",
    "selection_hash",
    "selection_rank_within_remaining_pool",
    "selection_seed",
    "selection_salt",
    "overlay_assignment_status",
)


class DevelopmentExpansionError(RuntimeError):
    """Raised before writes when frozen governance evidence or selection drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DevelopmentExpansionError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv_fields(
    path: Path, allowed_fields: set[str], required_fields: set[str]
) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or ())
        _require(required_fields <= fieldnames, f"missing governance fields in {path}")
        _require(not (FORBIDDEN_SELECTION_FIELDS & allowed_fields), "forbidden field allowlist")
        return [
            {field: row[field] for field in allowed_fields}
            for row in reader
        ]


def selection_preimage(row: dict[str, str]) -> bytes:
    """Return the public, exact UTF-8 preimage used for candidate ordering."""
    values = (
        SELECTION_SALT,
        SELECTION_SEED,
        row["dataset"],
        row["dataset_version"],
        row["proposed_role"],
        row["task_id"],
    )
    return ("\n".join(values) + "\n").encode("utf-8")


def selection_hash(row: dict[str, str]) -> str:
    return _sha256_bytes(selection_preimage(row))


def _source_hashes(repo_root: Path) -> dict[str, str]:
    hashes = {
        label: _sha256_bytes((repo_root / path).read_bytes())
        for label, path in SOURCE_PATHS.items()
    }
    _require(hashes == EXPECTED_SOURCE_HASHES, "source governance artifact hash mismatch")
    return hashes


def _validate_candidate_a(repo_root: Path) -> dict[str, Any]:
    m2c_manifest = json.loads((repo_root / M2C_MANIFEST).read_text(encoding="utf-8"))
    candidates = json.loads((repo_root / M2C_CANDIDATES).read_text(encoding="utf-8"))
    _require(
        m2c_manifest["freeze_status"] == "尚不凍結，只保留候選",
        "Milestone 2C freeze status changed",
    )
    _require(
        candidates["freeze_status"] == "尚不凍結，只保留候選",
        "candidate freeze status changed",
    )
    _require(
        candidates["recommended_candidate_id"]
        == "v1_candidate_a_conservative_compaction",
        "Candidate A identity changed",
    )
    candidate = next(
        item
        for item in candidates["candidates"]
        if item["candidate_id"] == "v1_candidate_a_conservative_compaction"
    )
    text_bytes = candidate["exact_text_utf8"].encode("utf-8")
    _require(
        _sha256_bytes(text_bytes) == EXPECTED_CANDIDATE_A_TEXT_SHA256,
        "Candidate A exact UTF-8 text changed",
    )
    _require(candidates["creates_v1_run_directory"] is False, "unexpected v1 run status")
    _require(candidates["model_calls"] == 0, "unexpected model call record")
    _require(candidates["evalplus_executions"] == 0, "unexpected EvalPlus record")
    return {
        "candidate_id": candidate["candidate_id"],
        "status": "candidate_only_not_frozen",
        "exact_text_sha256": _sha256_bytes(text_bytes),
        "exact_text_size_bytes": len(text_bytes),
        "source_path": M2C_CANDIDATES.as_posix(),
        "generation_plan_created": False,
    }


def build_expansion(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_hashes = _source_hashes(repo_root)
    candidate_a = _validate_candidate_a(repo_root)
    frozen_rows = _read_csv_fields(
        repo_root / FROZEN_SPLIT,
        ALLOWED_FROZEN_FIELDS,
        ALLOWED_FROZEN_FIELDS,
    )
    contamination_rows = _read_csv_fields(
        repo_root / CONTAMINATION_MANIFEST,
        ALLOWED_CONTAMINATION_FIELDS,
        ALLOWED_CONTAMINATION_FIELDS,
    )
    _require(len(frozen_rows) == 542, "frozen split row count changed")
    frozen_keys = [(row["dataset"], row["task_id"]) for row in frozen_rows]
    _require(len(frozen_keys) == len(set(frozen_keys)), "frozen split keys are not unique")
    _require(
        all(row["split_assignment_status"] == "frozen" for row in frozen_rows),
        "source split is not fully frozen",
    )

    contamination_by_key = {
        (row["dataset"], row["task_id"]): row for row in contamination_rows
    }
    _require(len(contamination_by_key) == 542, "contamination manifest identity drift")
    _require(set(contamination_by_key) == set(frozen_keys), "governance source key mismatch")

    mbpp = [row for row in frozen_rows if row["dataset"] == DATASET]
    historical = [row for row in mbpp if row["proposed_role"] == SOURCE_ROLE]
    discovery = [
        row
        for row in historical
        if row["active_development_generation_subset"] == "true"
    ]
    remaining = [
        row
        for row in historical
        if row["active_development_generation_subset"] != "true"
    ]
    _require(len(mbpp) == 378, "MBPP+ frozen task count changed")
    _require(len(historical) == EXPECTED_HISTORICAL_POOL, "historical pool must be 116")
    _require(len(discovery) == EXPECTED_DISCOVERY, "discovery subset must be 20")
    _require(len(remaining) == EXPECTED_REMAINING, "remaining pool must be 96")
    _require(
        len({row["task_id"] for row in historical}) == EXPECTED_HISTORICAL_POOL,
        "historical pool task IDs are not unique",
    )
    for row in historical:
        contamination = contamination_by_key[(row["dataset"], row["task_id"])]
        _require(
            contamination["confirmatory_eligible"] == "false",
            f"historical task unexpectedly confirmatory eligible: {row['task_id']}",
        )
        _require(
            contamination["contamination_status"].startswith("excluded_"),
            f"historical task lacks historical contamination evidence: {row['task_id']}",
        )

    ranked = sorted(
        ((selection_hash(row), row["task_id"], row) for row in remaining),
        key=lambda item: (item[0], item[1]),
    )
    rank_by_id = {
        task_id: {"hash": digest, "rank": rank}
        for rank, (digest, task_id, _) in enumerate(ranked, start=1)
    }
    expansion = [item[2] for item in ranked[:EXPECTED_EXPANSION]]

    overlay_rows: list[dict[str, str]] = []
    for layer, rows in (
        ("discovery_development", discovery),
        ("expansion_development", expansion),
    ):
        for row in rows:
            ranked_value = rank_by_id.get(row["task_id"])
            overlay_rows.append(
                {
                    "dataset": row["dataset"],
                    "dataset_version": row["dataset_version"],
                    "task_id": row["task_id"],
                    "source_frozen_governance_role": row["proposed_role"],
                    "development_layer": layer,
                    "original_active_development_subset": (
                        "true" if layer == "discovery_development" else "false"
                    ),
                    "selection_eligible": (
                        "not_applicable_preserved_discovery"
                        if layer == "discovery_development"
                        else "true"
                    ),
                    "selection_hash": ranked_value["hash"] if ranked_value else "",
                    "selection_rank_within_remaining_pool": (
                        str(ranked_value["rank"]) if ranked_value else ""
                    ),
                    "selection_seed": (
                        SELECTION_SEED if layer == "expansion_development" else ""
                    ),
                    "selection_salt": (
                        SELECTION_SALT if layer == "expansion_development" else ""
                    ),
                    "overlay_assignment_status": "frozen",
                }
            )

    keys = [(row["dataset"], row["task_id"]) for row in overlay_rows]
    _require(len(overlay_rows) == EXPECTED_TOTAL, "overlay must contain 60 tasks")
    _require(len(keys) == len(set(keys)) == EXPECTED_TOTAL, "overlay tasks are not unique")
    _require(
        {row["task_id"] for row in discovery}
        <= {row["task_id"] for row in overlay_rows},
        "original discovery subset was not preserved",
    )

    forbidden_roles = {
        "validation",
        "internal_confirmatory_candidate",
        "external_confirmatory_candidate",
        "excluded_historical",
        "sealed_reserve",
    }
    forbidden_keys = {
        (row["dataset"], row["task_id"])
        for row in frozen_rows
        if row["proposed_role"] in forbidden_roles
    }
    _require(not (set(keys) & forbidden_keys), "development overlay overlaps forbidden roles")
    _require(
        all(row["source_frozen_governance_role"] == SOURCE_ROLE for row in overlay_rows),
        "overlay contains a non-historical task",
    )

    identities = [
        {
            "dataset": row["dataset"],
            "task_id": row["task_id"],
            "seed": seed,
            "identity": f"{row['task_id']}|seed={seed}",
        }
        for row in overlay_rows
        for seed in SEEDS
    ]
    identity_keys = {(row["task_id"], row["seed"]) for row in identities}
    _require(
        len(identities) == len(identity_keys) == EXPECTED_IDENTITIES,
        "future task-seed identities must be 300 unique pairs",
    )

    role_counts = Counter(row["proposed_role"] for row in frozen_rows)
    return {
        "source_hashes": source_hashes,
        "candidate_a": candidate_a,
        "overlay_rows": overlay_rows,
        "identities": identities,
        "selected_expansion_task_ids": [row["task_id"] for row in expansion],
        "selection_records": [
            {
                "task_id": task_id,
                "selection_hash": digest,
                "selection_rank_within_remaining_pool": rank,
                "selected": rank <= EXPECTED_EXPANSION,
            }
            for rank, (digest, task_id, _) in enumerate(ranked, start=1)
        ],
        "frozen_role_counts": dict(sorted(role_counts.items())),
        "forbidden_overlap_count": len(set(keys) & forbidden_keys),
    }


def _render_csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _render_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _render_summary(result: dict[str, Any]) -> bytes:
    selected = result["selection_records"][:EXPECTED_EXPANSION]
    lines = [
        "# MBPP+ development expansion 預註冊與名單凍結（Milestone 2D）",
        "",
        "## 治理範圍",
        "",
        "本 addendum 不改寫原 frozen split；它引用原 split hash 與 starting HEAD，僅凍結 development expansion overlay。本輪沒有模型呼叫、EvalPlus 執行、run directory、Scaffold v1 generation plan 或 Healer 建置。Candidate A 保持 candidate-only，exact UTF-8 text 未修改。",
        "",
        "選取只使用 dataset 名稱／版本、task_id、frozen governance role 與固定公開 seed/salt；未讀取 prompt、答案、tests、canonical solution、模型輸出、錯誤類別或通過結果。",
        "",
        "## 凍結統計",
        "",
        "- Historical development pool：116 題。",
        "- Discovery development：原20題，完整保留。",
        "- 剩餘可選候選：96題。",
        "- Expansion development：deterministic 選取40題。",
        "- 合計：60個 unique task IDs。",
        "- 未來每個 treatment 的 identities：60 × 5 seeds = 300 unique `task_id + seed`；本輪只凍結 identity 規格，不建立 run。",
        "- 與 validation、internal/external confirmatory、excluded、sealed reserve 重疊：0。",
        "",
        "## 公開 deterministic selection 規格",
        "",
        f"- Selection seed：`{SELECTION_SEED}`",
        f"- Selection salt：`{SELECTION_SALT}`",
        f"- Algorithm：`{SELECTION_ALGORITHM}`",
        "- 無人工 override、換題或例外名單。",
        "",
        "Exact preimage 是以下六欄以 LF 連接並保留最後 LF：`salt`、`seed`、`dataset`、`dataset_version`、`frozen_role`、`task_id`。",
        "",
        "## 新增40題凍結名單",
        "",
        "| Rank | task_id | Selection SHA-256 |",
        "|---:|---|---|",
    ]
    for row in selected:
        lines.append(
            f"| {row['selection_rank_within_remaining_pool']} | {row['task_id']} | "
            f"`{row['selection_hash']}` |"
        )
    lines.extend(
        [
            "",
            "## Immutable references 與後續限制",
            "",
            f"- Original frozen split SHA-256：`{result['source_hashes']['frozen_split.csv']}`。",
            f"- Original frozen split HEAD reference：`23a430538f44fbe8e57a025a19ca0f49778e1ab1`；本 addendum starting HEAD：`{STARTING_HEAD}`。",
            f"- Candidate A exact text SHA-256：`{result['candidate_a']['exact_text_sha256']}`；狀態為 `candidate_only_not_frozen`。",
            "- 未來 treatment 的生成與評測必須另立預註冊 milestone；本 addendum 不授權模型、EvalPlus、Scaffold v1 或 Healer 執行。",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    result = build_expansion(repo_root)
    csv_bytes = _render_csv(result["overlay_rows"])
    summary_bytes = _render_summary(result)
    outputs: dict[Path, bytes] = {
        Path("development_expansion_manifest.csv"): csv_bytes,
        Path("development_expansion_summary_zh.md"): summary_bytes,
    }
    manifest = {
        "manifest_version": "mbpp_development_expansion_v1",
        "milestone": "2D",
        "status": "frozen_development_expansion_overlay",
        "starting_head": STARTING_HEAD,
        "source_frozen_split": {
            "path": FROZEN_SPLIT.as_posix(),
            "sha256": result["source_hashes"]["frozen_split.csv"],
            "original_freeze_head": "23a430538f44fbe8e57a025a19ca0f49778e1ab1",
            "modified": False,
        },
        "source_artifacts": {
            label: {"path": SOURCE_PATHS[label].as_posix(), "sha256": digest}
            for label, digest in sorted(result["source_hashes"].items())
        },
        "dataset": DATASET,
        "dataset_version": DATASET_VERSION,
        "counts": {
            "historical_development_pool": EXPECTED_HISTORICAL_POOL,
            "discovery_development": EXPECTED_DISCOVERY,
            "remaining_historical_candidates": EXPECTED_REMAINING,
            "expansion_development": EXPECTED_EXPANSION,
            "total_development": EXPECTED_TOTAL,
            "unique_task_seed_identities_per_future_treatment": EXPECTED_IDENTITIES,
        },
        "seeds": list(SEEDS),
        "selection": {
            "seed": SELECTION_SEED,
            "salt": SELECTION_SALT,
            "algorithm": SELECTION_ALGORITHM,
            "preimage_fields": [
                "salt",
                "seed",
                "dataset",
                "dataset_version",
                "frozen_role",
                "task_id",
            ],
            "encoding": "UTF-8",
            "separator": "LF",
            "final_lf": True,
            "candidate_pool_size": EXPECTED_REMAINING,
            "selected_count": EXPECTED_EXPANSION,
            "manual_override_allowed": False,
            "records": result["selection_records"],
        },
        "development_tasks": result["overlay_rows"],
        "future_task_seed_identities": result["identities"],
        "zero_overlap": {
            "validation": 0,
            "internal_confirmatory_candidate": 0,
            "external_confirmatory_candidate": 0,
            "excluded_historical": 0,
            "sealed_reserve": 0,
            "verified_total_forbidden_overlap": result["forbidden_overlap_count"],
        },
        "candidate_a": result["candidate_a"],
        "prohibited_actions_attestation": {
            "prompt_answer_tests_or_solution_fields_read_for_selection": False,
            "model_outputs_or_evaluation_results_read_for_selection": False,
            "model_calls": 0,
            "evalplus_executions": 0,
            "run_directory_created": False,
            "scaffold_v1_built_or_frozen": False,
            "scaffold_v1_generation_plan_created": False,
            "healer_built": False,
        },
        "outputs": {
            path.as_posix(): {"sha256": _sha256_bytes(content), "size_bytes": len(content)}
            for path, content in sorted(outputs.items(), key=lambda item: item[0].as_posix())
        },
        "builder": "scripts/freeze_mbpp_development_expansion_v1.py",
        "targeted_tests": "tests/finals_rebuild/test_mbpp_development_expansion_v1.py",
    }
    outputs[Path("development_expansion_manifest.json")] = _render_json(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    for relative, content in build_outputs(repo_root).items():
        path = output_dir / relative
        if path.exists():
            _require(path.read_bytes() == content, f"refusing output drift/overwrite: {relative}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    write_outputs(args.repo_root)
    print(
        json.dumps(
            {
                "status": "frozen_development_expansion_overlay",
                "development_tasks": EXPECTED_TOTAL,
                "future_identities_per_treatment": EXPECTED_IDENTITIES,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
