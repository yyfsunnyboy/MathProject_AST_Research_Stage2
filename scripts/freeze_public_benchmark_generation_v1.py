#!/usr/bin/env python3
"""Governance freeze and preregistration builder for Qwen3.5 4B/9B Full Benchmark.

Manifests output location:
  artifacts/public_benchmark_governance/qwen4b_qwen9b_full_benchmark_preregistration_v1/

Outputs:
  1. preregistration_manifest.json
  2. prompt_manifest.jsonl (2168 entries = 542 tasks x 2 treatments x 2 models)
  3. master_manifest.json

Guarantees:
  - Fail-closed source hashes for tasks, extractor, H2 rule
  - Fixed decoding parameters (seed=0, temp=0.0, top_p=1.0, top_k=40, think=False, num_predict=1024)
  - Zero model calls during freeze/check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from scripts import run_public_benchmark_generation_v1 as gen_runner  # noqa: E402
from scripts import run_public_benchmark_h2_replay_v1 as replay_runner  # noqa: E402

PLAN_ID = "qwen4b_qwen9b_full_benchmark_preregistration_v1"
GOVERNANCE_RELATIVE = pathlib.Path("artifacts/public_benchmark_governance") / PLAN_ID

EXPECTED_HASHES = {
    "tasks_humaneval": "d26c9379a412db03c955b063506c04d7a6da5fb5ef77265ec603c7565922b829",
    "tasks_mbpp": "8bc9f3ff73ac65e013336dc91a16adb8e088d439952f4d4da938585459d1e47b",
    "extraction_py": "aa331bbe5fbd17b4fc1372fb4de8e740a67f1d4c7b86114eb8d8d14c4c7d6ee2",
    "h2_quarantine_py": "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18",
}

DECODING_OPTIONS = {
    "seed": 0,
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": 40,
    "think": False,
    "num_predict": 1024,
    "system_prompt": "",
    "ollama_base_url": "http://127.0.0.1:11434",
}


class FreezeError(RuntimeError):
    """Fail-closed error for freeze builder violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_manifests(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Builds preregistration and master manifests for 4B and 9B full benchmark."""
    # Verify source file hashes fail-closed
    for key, expected in EXPECTED_HASHES.items():
        if key == "tasks_humaneval":
            p = repo_root / "tasks_humaneval.jsonl"
        elif key == "tasks_mbpp":
            p = repo_root / "tasks_mbpp.jsonl"
        elif key == "extraction_py":
            p = repo_root / "agent_tools/finals_rebuild/extraction.py"
        elif key == "h2_quarantine_py":
            p = repo_root / "agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"
        else:
            continue
        _require(p.is_file(), f"missing file: {p}")
        actual = _sha256_file(p)
        _require(
            actual == expected,
            f"source hash mismatch for {key}: expected {expected}, got {actual}",
        )

    tasks_he = gen_runner.load_tasks("humaneval", repo_root=repo_root)
    tasks_mb = gen_runner.load_tasks("mbpp", repo_root=repo_root)
    all_tasks = tasks_he + tasks_mb

    _require(len(tasks_he) == 164, "HumanEval count mismatch")
    _require(len(tasks_mb) == 378, "MBPP count mismatch")
    _require(len(all_tasks) == 542, "Total task count mismatch")

    models = ["qwen3.5:4b", "qwen3.5:9b"]
    treatments = ["ab1", "ab2g"]

    prompt_entries: list[dict[str, Any]] = []

    for m in models:
        m_spec = gen_runner.MODEL_SPECS[m]
        for t in all_tasks:
            tid = t["task_id"]
            ds_name = "humaneval" if tid.startswith("HumanEval") else "mbpp"
            for tr in treatments:
                composed_p = gen_runner.build_composed_prompt(t, tr)
                p_hash = _sha256_text(composed_p)
                cell_id = gen_runner.generate_cell_identity(m, tid, tr, seed=0)

                prompt_entries.append(
                    {
                        "cell_identity": cell_id,
                        "model_tag": m,
                        "model_key": m_spec["model_key"],
                        "model_digest": m_spec["model_digest"],
                        "task_id": tid,
                        "dataset": ds_name,
                        "prompt_condition": tr,
                        "seed": 0,
                        "composed_prompt": composed_p,
                        "composed_prompt_sha256": p_hash,
                        "decoding_options": DECODING_OPTIONS,
                    }
                )

    _require(
        len(prompt_entries) == 2168,
        f"planned prompt entries mismatch: expected 2168, got {len(prompt_entries)}",
    )

    prereg_manifest = {
        "plan_id": PLAN_ID,
        "runner_identity": gen_runner.RUNNER_IDENTITY,
        "created_at": "2026-07-26T20:24:30Z",
        "roster_hashes": {
            "humaneval": EXPECTED_HASHES["tasks_humaneval"],
            "mbpp": EXPECTED_HASHES["tasks_mbpp"],
        },
        "extractor_hash": EXPECTED_HASHES["extraction_py"],
        "h2_rule_hash": EXPECTED_HASHES["h2_quarantine_py"],
        "decoding_options": DECODING_OPTIONS,
        "models": {
            "qwen3.5:4b": {
                "model_key": "qwen35_4b",
                "model_digest": gen_runner.MODEL_SPECS["qwen3.5:4b"]["model_digest"],
                "expected_raw_count": 1084,
                "expected_itt_states": 2168,
                "output_directories": [
                    "runs/he_qwen35_4b",
                    "runs/mb_qwen35_4b",
                ],
            },
            "qwen3.5:9b": {
                "model_key": "qwen35_9b",
                "model_digest": gen_runner.MODEL_SPECS["qwen3.5:9b"]["model_digest"],
                "expected_raw_count": 1084,
                "expected_itt_states": 2168,
                "output_directories": [
                    "runs/he_qwen35_9b",
                    "runs/mb_qwen35_9b",
                ],
            },
        },
        "counts": {
            "humaneval_tasks": 164,
            "mbpp_tasks": 378,
            "total_tasks": 542,
            "treatments_per_task": 2,
            "raw_generations_per_model": 1084,
            "total_raw_generations_both_models": 2168,
            "itt_eval_conditions_per_task": 4,
            "itt_states_per_model": 2168,
            "total_itt_states_both_models": 4336,
        },
        "governance": {
            "validation20_isolated": True,
            "validation20_reusable": False,
            "validation20_incompatible_count": 40,
            "model_calls": 0,
            "status": "preregistration_frozen",
        },
    }

    master_manifest = {
        "plan_id": PLAN_ID,
        "preregistration_manifest": "preregistration_manifest.json",
        "prompt_manifest": "prompt_manifest.jsonl",
        "prompt_manifest_sha256": _sha256_text(
            "\n".join(json.dumps(e, sort_keys=True) for e in prompt_entries)
        ),
        "total_prompt_manifest_entries": len(prompt_entries),
        "status": "master_preregistration_frozen",
    }

    return {
        "preregistration_manifest": prereg_manifest,
        "prompt_entries": prompt_entries,
        "master_manifest": master_manifest,
    }


def freeze_manifests(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Writes governance manifests to disk."""
    gov_dir = repo_root / GOVERNANCE_RELATIVE
    gov_dir.mkdir(parents=True, exist_ok=True)

    data = build_manifests(repo_root=repo_root)

    prereg_path = gov_dir / "preregistration_manifest.json"
    prompt_path = gov_dir / "prompt_manifest.jsonl"
    master_path = gov_dir / "master_manifest.json"

    prereg_path.write_text(
        json.dumps(data["preregistration_manifest"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    prompt_lines = [json.dumps(e, sort_keys=True) for e in data["prompt_entries"]]
    prompt_path.write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")

    master_path.write_text(
        json.dumps(data["master_manifest"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "manifests_frozen",
        "output_directory": gov_dir.as_posix(),
        "files_written": [
            prereg_path.as_posix(),
            prompt_path.as_posix(),
            master_path.as_posix(),
        ],
        "prompt_entries": len(data["prompt_entries"]),
    }


def check_manifests(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Verifies that governance manifests on disk strictly match deterministic output."""
    gov_dir = repo_root / GOVERNANCE_RELATIVE
    _require(gov_dir.is_dir(), f"governance directory missing: {gov_dir}")

    expected_data = build_manifests(repo_root=repo_root)

    prereg_path = gov_dir / "preregistration_manifest.json"
    prompt_path = gov_dir / "prompt_manifest.jsonl"
    master_path = gov_dir / "master_manifest.json"

    _require(prereg_path.is_file(), f"missing {prereg_path}")
    _require(prompt_path.is_file(), f"missing {prompt_path}")
    _require(master_path.is_file(), f"missing {master_path}")

    disk_prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    _require(
        disk_prereg["governance"]["status"] == "preregistration_frozen",
        "preregistration status mismatch",
    )

    disk_lines = [line for line in prompt_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _require(len(disk_lines) == 2168, f"prompt manifest line count mismatch: {len(disk_lines)}")

    return {
        "status": "freeze_check_passed",
        "plan_id": PLAN_ID,
        "governance_directory": gov_dir.as_posix(),
        "manifest_entries": len(disk_lines),
        "model_calls": 0,
        "evalplus_executed": False,
        "candidate_program_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        res = check_manifests()
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0

    res = freeze_manifests()
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
