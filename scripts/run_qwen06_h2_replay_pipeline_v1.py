#!/usr/bin/env python3
"""Independent H2 replay pipeline for qwen3:0.6b public-benchmark runs.

Data-flow position (fixed extractor → H2 → four conditions → EvalPlus):

  generation_attempts / treatment.jsonl completions
        │
        ▼
  fixed extractor output (Python completion only; never raw model text)
        │
        ▼
  quarantine_module_assert_entrypoint_selftest(...)   # H2
        │
        ├── Ab1-Raw / Ab2g-Raw   (identity of extracted completion)
        └── Ab1-H2 / Ab2g-H2     (H2Decision.output_source)
        │
        ▼
  EvalPlus base/plus (via run-full-benchmark; never regenerates the model)

Unique full-benchmark entrypoint::

  python scripts/run_qwen06_h2_replay_pipeline_v1.py run-full-benchmark \\
    --dataset all \\
    --output-dir artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1/manual_run_001 \\
    --parallel 1

This module never calls a model, never modifies H2, and never overwrites Ab3
or existing 0.6B run artifacts.  Use ``--dry-run`` to materialize the 2,168
ITT states without invoking EvalPlus.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID,
    RULE_STATUS,
    quarantine_module_assert_entrypoint_selftest,
)

OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/qwen06_h2_replay_pipeline_v1"
)
RULE_RELATIVE = Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py")
EXPECTED_RULE_SHA256 = (
    "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"
)
EXPECTED_RULE_STATUS = "development_candidate_not_frozen"

TASK_FILES = {
    "humaneval": Path("tasks_humaneval.jsonl"),
    "mbpp": Path("tasks_mbpp.jsonl"),
}
RUN_DIRS = {
    "humaneval": Path("runs/he_qwen06"),
    "mbpp": Path("runs/mb_qwen06"),
}
AB3_BASELINES = {
    "humaneval_ab3_core": Path(
        "runs/he_qwen06/public_benchmark_raw/humaneval/evalplus/ab3_core.jsonl"
    ),
    "humaneval_ab3_full": Path(
        "runs/he_qwen06/public_benchmark_raw/humaneval/evalplus/ab3_full.jsonl"
    ),
    "mbpp_ab3_core": Path(
        "runs/mb_qwen06/public_benchmark_raw/mbpp/evalplus/ab3_core.jsonl"
    ),
    "mbpp_ab3_full": Path(
        "runs/mb_qwen06/public_benchmark_raw/mbpp/evalplus/ab3_full.jsonl"
    ),
}

TREATMENTS = ("ab1", "ab2g")
CONDITIONS = ("Ab1-Raw", "Ab1-H2", "Ab2g-Raw", "Ab2g-H2")
PIPELINE_STATUS = "H2_REPLAY_PIPELINE_WIRED_SMOKE_ONLY_NOT_FULL_ITT"
EXPECTED_TASK_COUNTS = {"humaneval": 164, "mbpp": 378}
EXPECTED_ITT_STATES_ALL = 2168  # 542 tasks × 4 conditions
FULL_EVAL_PACKAGE_RELATIVE = Path(
    "artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1"
)
DEFAULT_FULL_RUN_OUTPUT = FULL_EVAL_PACKAGE_RELATIVE / "manual_run_001"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
EVALPLUS_ENGINE = "evalplus_0.3.1_cli_full_benchmark"
PROTECTED_RUN_FILES = (
    Path("runs/he_qwen06/ab1.jsonl"),
    Path("runs/he_qwen06/ab2g.jsonl"),
    Path("runs/he_qwen06/generation_attempts.jsonl"),
    Path("runs/mb_qwen06/ab1.jsonl"),
    Path("runs/mb_qwen06/ab2g.jsonl"),
    Path("runs/mb_qwen06/generation_attempts.jsonl"),
)


class H2ReplayError(RuntimeError):
    """Fail-closed pipeline violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise H2ReplayError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def verify_h2_rule(repo_root: Path = REPO_ROOT) -> str:
    path = repo_root / RULE_RELATIVE
    actual = _sha256_bytes(path.read_bytes())
    _require(actual == EXPECTED_RULE_SHA256, f"H2 rule SHA drift: {actual}")
    _require(RULE_STATUS == EXPECTED_RULE_STATUS, "H2 RULE_STATUS drift")
    _require(RULE_ID == "module_assert_entrypoint_selftest_quarantine_v0", "H2 RULE_ID drift")
    return actual


def ab3_baseline_hashes(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, relative in AB3_BASELINES.items():
        path = repo_root / relative
        _require(path.is_file(), f"missing Ab3 baseline: {relative.as_posix()}")
        out[relative.as_posix()] = _sha256_bytes(path.read_bytes())
    return out


def load_task_roster(
    dataset: str, repo_root: Path = REPO_ROOT
) -> list[dict[str, str]]:
    path = repo_root / TASK_FILES[dataset]
    rows = _read_jsonl(path)
    roster: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        task_id = row["task_id"]
        _require(task_id not in seen, f"duplicate task_id in roster: {task_id}")
        seen.add(task_id)
        entry = row["entry_point"]
        _require(isinstance(entry, str) and entry.isidentifier(), f"bad entry_point: {task_id}")
        roster.append({"task_id": task_id, "entry_point": entry})
    return roster


def load_treatment_completions(
    dataset: str, treatment: str, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    path = repo_root / RUN_DIRS[dataset] / f"{treatment}.jsonl"
    rows = _read_jsonl(path) if path.is_file() else []
    by_task: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = row["task_id"]
        _require(task_id not in by_task, f"duplicate completion for {dataset}/{treatment}/{task_id}")
        by_task[task_id] = row
    return by_task


def load_generation_attempts(
    dataset: str, repo_root: Path = REPO_ROOT
) -> dict[tuple[str, str], dict[str, Any]]:
    path = repo_root / RUN_DIRS[dataset] / "generation_attempts.jsonl"
    rows = _read_jsonl(path)
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["task_id"], row["treatment"])
        _require(key not in index, f"duplicate attempt for {key}")
        index[key] = row
    return index


def _done_reason_from_attempt(attempt: Mapping[str, Any] | None) -> str | None:
    if attempt is None:
        return None
    meta = attempt.get("ollama_response_metadata")
    if isinstance(meta, dict):
        body = meta.get("raw_body")
        if isinstance(body, str) and body.strip():
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and isinstance(parsed.get("done_reason"), str):
                return parsed["done_reason"]
    generation_meta = attempt.get("metadata")
    if isinstance(generation_meta, dict) and isinstance(
        generation_meta.get("done_reason"), str
    ):
        return generation_meta["done_reason"]
    return None


def provenance_flags_from_attempt(
    attempt: Mapping[str, Any] | None,
) -> tuple[bool | None, bool | None]:
    """Derive extraction_unambiguous / source_complete from saved evidence only."""
    if attempt is None:
        return None, None
    status = attempt.get("extraction_status")
    if status == "extracted":
        unambiguous: bool | None = True
    elif status == "ambiguous":
        unambiguous = False
    else:
        unambiguous = None
    done_reason = _done_reason_from_attempt(attempt)
    if done_reason is None:
        complete: bool | None = None
    else:
        complete = done_reason == "stop"
    return unambiguous, complete


def function_segment_hashes(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(source, node)
            if segment is not None:
                out[node.name] = _sha256_text(segment)
    return out


def module_level_assert_count(source: str) -> int:
    tree = ast.parse(source)
    return sum(isinstance(node, ast.Assert) for node in tree.body)


def apply_h2_to_completion(
    *,
    completion: str | None,
    entry_point: str,
    extraction_unambiguous: bool | None,
    source_complete: bool | None,
) -> dict[str, Any]:
    """Apply H2 to one extracted completion. Missing completion stays in ITT."""
    if completion is None or not str(completion).strip():
        return {
            "input_sha256": None,
            "output_sha256": None,
            "output_source": None,
            "rule_id": RULE_ID,
            "rule_sha256": EXPECTED_RULE_SHA256,
            "rule_status": RULE_STATUS,
            "triggered": False,
            "transformed": False,
            "abstained": True,
            "reason": "missing_extracted_completion",
            "guard_results": {
                "extraction_unambiguous": extraction_unambiguous is True,
                "source_complete": source_complete is True,
            },
            "extraction_unambiguous": extraction_unambiguous,
            "source_complete": source_complete,
            "missing_extracted_completion": True,
            "byte_identical_to_input": True,
        }

    decision = quarantine_module_assert_entrypoint_selftest(
        source=completion,
        entry_point=entry_point,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
    )
    output = decision.output_source
    if decision.abstained or not decision.transformed:
        _require(output == completion, "abstain/no-op must be byte-identical to input")
    else:
        _require(output == decision.output_source, "transformed must use H2Decision.output_source")
        ast.parse(output)
        _require(
            function_segment_hashes(completion) == function_segment_hashes(output),
            "function segment hash changed",
        )
        _require(module_level_assert_count(output) == 0, "module-level assert still present")
        # Idempotence: re-running H2 on transformed output must not change again.
        second = quarantine_module_assert_entrypoint_selftest(
            source=output,
            entry_point=entry_point,
            extraction_unambiguous=extraction_unambiguous,
            source_complete=source_complete,
        )
        _require(
            second.output_source == output,
            "H2 idempotence failed",
        )

    return {
        "input_sha256": decision.source_sha256,
        "output_sha256": decision.output_sha256,
        "output_source": output,
        "rule_id": decision.rule_id,
        "rule_sha256": EXPECTED_RULE_SHA256,
        "rule_status": decision.rule_status,
        "triggered": decision.triggered,
        "transformed": decision.transformed,
        "abstained": decision.abstained,
        "reason": decision.reason,
        "guard_results": decision.guard_results,
        "extraction_unambiguous": extraction_unambiguous,
        "source_complete": source_complete,
        "missing_extracted_completion": False,
        "byte_identical_to_input": output == completion,
    }


def build_condition_record(
    *,
    dataset: str,
    task_id: str,
    treatment: str,
    condition: str,
    entry_point: str,
    completion: str | None,
    attempt: Mapping[str, Any] | None,
    apply_healer: bool,
) -> dict[str, Any]:
    unambiguous, complete = provenance_flags_from_attempt(attempt)
    if apply_healer:
        h2 = apply_h2_to_completion(
            completion=completion,
            entry_point=entry_point,
            extraction_unambiguous=unambiguous,
            source_complete=complete,
        )
        return {
            "dataset": dataset,
            "task_id": task_id,
            "treatment": treatment,
            "condition": condition,
            "entry_point": entry_point,
            **h2,
        }

    # Raw condition: identity of extracted completion only.
    if completion is None or not str(completion).strip():
        return {
            "dataset": dataset,
            "task_id": task_id,
            "treatment": treatment,
            "condition": condition,
            "entry_point": entry_point,
            "input_sha256": None,
            "output_sha256": None,
            "output_source": None,
            "rule_id": None,
            "rule_sha256": None,
            "rule_status": None,
            "triggered": False,
            "transformed": False,
            "abstained": True,
            "reason": "missing_extracted_completion",
            "guard_results": {},
            "extraction_unambiguous": unambiguous,
            "source_complete": complete,
            "missing_extracted_completion": True,
            "byte_identical_to_input": True,
        }
    digest = _sha256_text(completion)
    return {
        "dataset": dataset,
        "task_id": task_id,
        "treatment": treatment,
        "condition": condition,
        "entry_point": entry_point,
        "input_sha256": digest,
        "output_sha256": digest,
        "output_source": completion,
        "rule_id": None,
        "rule_sha256": None,
        "rule_status": None,
        "triggered": False,
        "transformed": False,
        "abstained": False,
        "reason": "raw_extracted_completion_identity",
        "guard_results": {},
        "extraction_unambiguous": unambiguous,
        "source_complete": complete,
        "missing_extracted_completion": False,
        "byte_identical_to_input": True,
    }


def build_four_conditions_for_task(
    *,
    dataset: str,
    task: Mapping[str, str],
    completions: Mapping[str, Mapping[str, dict[str, Any]]],
    attempts: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    task_id = task["task_id"]
    entry_point = task["entry_point"]
    records: list[dict[str, Any]] = []
    mapping = (
        ("ab1", "Ab1-Raw", False),
        ("ab1", "Ab1-H2", True),
        ("ab2g", "Ab2g-Raw", False),
        ("ab2g", "Ab2g-H2", True),
    )
    for treatment, condition, apply_healer in mapping:
        row = completions.get(treatment, {}).get(task_id)
        completion = row.get("completion") if isinstance(row, dict) else None
        if completion is not None and not isinstance(completion, str):
            completion = None
        attempt = attempts.get((task_id, treatment))
        records.append(
            build_condition_record(
                dataset=dataset,
                task_id=task_id,
                treatment=treatment,
                condition=condition,
                entry_point=entry_point,
                completion=completion,
                attempt=attempt,
                apply_healer=apply_healer,
            )
        )
    return records


def build_synthetic_smoke_records() -> list[dict[str, Any]]:
    """Small synthetic smoke covering required trigger / transform / abstain cases."""
    cases = [
        {
            "name": "unique_module_selftest_transform",
            "dataset": "synthetic",
            "task_id": "Synthetic/transform",
            "treatment": "ab1",
            "condition": "Ab1-H2",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n",
            "extraction_unambiguous": True,
            "source_complete": True,
            "expect_transformed": True,
        },
        {
            "name": "no_module_assert_noop",
            "dataset": "synthetic",
            "task_id": "Synthetic/noop",
            "treatment": "ab1",
            "condition": "Ab1-H2",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x\n",
            "extraction_unambiguous": True,
            "source_complete": True,
            "expect_transformed": False,
            "expect_reason": "no_module_level_assert",
        },
        {
            "name": "multiple_module_asserts_abstain",
            "dataset": "synthetic",
            "task_id": "Synthetic/multi",
            "treatment": "ab2g",
            "condition": "Ab2g-H2",
            "entry_point": "solve",
            "completion": (
                "def solve(x):\n    return x\n"
                "assert solve(1) == 1\nassert solve(2) == 2\n"
            ),
            "extraction_unambiguous": True,
            "source_complete": True,
            "expect_transformed": False,
            "expect_reason": "module_assert_count_not_one",
        },
        {
            "name": "entry_point_missing_abstain",
            "dataset": "synthetic",
            "task_id": "Synthetic/missing_ep",
            "treatment": "ab1",
            "condition": "Ab1-H2",
            "entry_point": "solve",
            "completion": "def other(x):\n    return x\n\nassert other(1) == 1\n",
            "extraction_unambiguous": True,
            "source_complete": True,
            "expect_transformed": False,
            "expect_reason": "entry_point_missing",
        },
        {
            "name": "ambiguous_extraction_abstain",
            "dataset": "synthetic",
            "task_id": "Synthetic/ambiguous",
            "treatment": "ab1",
            "condition": "Ab1-H2",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x\n\nassert solve(1) == 1\n",
            "extraction_unambiguous": False,
            "source_complete": True,
            "expect_transformed": False,
        },
        {
            "name": "source_complete_unknown_abstain",
            "dataset": "synthetic",
            "task_id": "Synthetic/unknown_complete",
            "treatment": "ab2g",
            "condition": "Ab2g-H2",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x\n\nassert solve(1) == 1\n",
            "extraction_unambiguous": True,
            "source_complete": None,
            "expect_transformed": False,
            "expect_reason": "source_truncated_or_completion_unknown",
        },
        {
            "name": "missing_completion_itt_retained",
            "dataset": "synthetic",
            "task_id": "Synthetic/missing_completion",
            "treatment": "ab1",
            "condition": "Ab1-H2",
            "entry_point": "solve",
            "completion": None,
            "extraction_unambiguous": None,
            "source_complete": None,
            "expect_transformed": False,
            "expect_reason": "missing_extracted_completion",
        },
        {
            "name": "ab2g_raw_identity",
            "dataset": "synthetic",
            "task_id": "Synthetic/ab2g_raw",
            "treatment": "ab2g",
            "condition": "Ab2g-Raw",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x\n",
            "apply_healer": False,
        },
        {
            "name": "ab1_raw_identity",
            "dataset": "synthetic",
            "task_id": "Synthetic/ab1_raw",
            "treatment": "ab1",
            "condition": "Ab1-Raw",
            "entry_point": "solve",
            "completion": "def solve(x):\n    return x + 1\n\nassert solve(1) == 2\n",
            "apply_healer": False,
        },
    ]

    records: list[dict[str, Any]] = []
    for case in cases:
        if case.get("apply_healer") is False:
            completion = case["completion"]
            digest = _sha256_text(completion) if completion else None
            records.append(
                {
                    "smoke_name": case["name"],
                    "dataset": case["dataset"],
                    "task_id": case["task_id"],
                    "treatment": case["treatment"],
                    "condition": case["condition"],
                    "entry_point": case["entry_point"],
                    "input_sha256": digest,
                    "output_sha256": digest,
                    "output_source": completion,
                    "rule_id": None,
                    "rule_sha256": None,
                    "rule_status": None,
                    "triggered": False,
                    "transformed": False,
                    "abstained": False,
                    "reason": "raw_extracted_completion_identity",
                    "guard_results": {},
                    "extraction_unambiguous": True,
                    "source_complete": True,
                    "missing_extracted_completion": completion is None,
                    "byte_identical_to_input": True,
                }
            )
            continue

        result = apply_h2_to_completion(
            completion=case["completion"],
            entry_point=case["entry_point"],
            extraction_unambiguous=case["extraction_unambiguous"],
            source_complete=case["source_complete"],
        )
        if case.get("expect_transformed") is True:
            _require(result["transformed"] is True, f"{case['name']} expected transform")
        if case.get("expect_reason"):
            _require(
                result["reason"] == case["expect_reason"],
                f"{case['name']} reason drift: {result['reason']}",
            )
        records.append(
            {
                "smoke_name": case["name"],
                "dataset": case["dataset"],
                "task_id": case["task_id"],
                "treatment": case["treatment"],
                "condition": case["condition"],
                "entry_point": case["entry_point"],
                **result,
            }
        )
    return records


def build_pipeline_manifest(
    *,
    rule_sha256: str,
    ab3_hashes: Mapping[str, str],
    smoke_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "status": PIPELINE_STATUS,
        "pipeline_id": "qwen06_h2_replay_pipeline_v1",
        "data_flow": (
            "fixed_extractor_completion → H2 quarantine_module_assert_entrypoint_selftest "
            "→ Ab1-Raw / Ab1-H2 / Ab2g-Raw / Ab2g-H2"
        ),
        "model_calls": 0,
        "full_itt_replay_executed": False,
        "evalplus_executed": False,
        "h2_rule": {
            "path": RULE_RELATIVE.as_posix(),
            "rule_id": RULE_ID,
            "rule_status": RULE_STATUS,
            "sha256": rule_sha256,
            "frozen": False,
            "label": "development_candidate_not_frozen",
        },
        "inputs": {
            "tasks_humaneval": TASK_FILES["humaneval"].as_posix(),
            "tasks_mbpp": TASK_FILES["mbpp"].as_posix(),
            "he_ab1": "runs/he_qwen06/ab1.jsonl",
            "he_ab2g": "runs/he_qwen06/ab2g.jsonl",
            "mb_ab1": "runs/mb_qwen06/ab1.jsonl",
            "mb_ab2g": "runs/mb_qwen06/ab2g.jsonl",
            "he_attempts": "runs/he_qwen06/generation_attempts.jsonl",
            "mb_attempts": "runs/mb_qwen06/generation_attempts.jsonl",
        },
        "conditions": list(CONDITIONS),
        "ab3_baselines_unchanged": dict(ab3_hashes),
        "smoke": {
            "cell_count": len(smoke_records),
            "transformed": sum(1 for r in smoke_records if r.get("transformed")),
            "abstained": sum(1 for r in smoke_records if r.get("abstained")),
            "missing_extracted_completion": sum(
                1 for r in smoke_records if r.get("missing_extracted_completion")
            ),
        },
        "non_claims": [
            "full_0.6B_H2_ITT_not_executed",
            "EvalPlus_not_executed",
            "H2_not_frozen",
            "Ab3_not_overwritten",
            "no_entry_point_rename_rule",
        ],
    }


def build_smoke_artifact_bytes(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    rule_sha = verify_h2_rule(repo_root)
    ab3_hashes = ab3_baseline_hashes(repo_root)
    smoke_records = build_synthetic_smoke_records()
    manifest = build_pipeline_manifest(
        rule_sha256=rule_sha,
        ab3_hashes=ab3_hashes,
        smoke_records=smoke_records,
    )
    return {
        "pipeline_manifest.json": _canonical_json(manifest),
        "smoke_cells.jsonl": "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in smoke_records
        ).encode("utf-8"),
        "smoke_summary.json": _canonical_json(
            {
                "status": "synthetic_smoke_passed",
                "model_calls": 0,
                "records": [
                    {
                        "smoke_name": row["smoke_name"],
                        "condition": row["condition"],
                        "triggered": row.get("triggered"),
                        "transformed": row.get("transformed"),
                        "abstained": row.get("abstained"),
                        "reason": row.get("reason"),
                        "missing_extracted_completion": row.get(
                            "missing_extracted_completion"
                        ),
                    }
                    for row in smoke_records
                ],
            }
        ),
        "ab3_baseline_hashes.json": _canonical_json(ab3_hashes),
        "README.md": (
            "# qwen06 H2 replay pipeline v1\n\n"
            f"Status: `{PIPELINE_STATUS}`\n\n"
            "H2 is wired after the fixed extractor completion and before any "
            "evaluator. Conditions: Ab1-Raw, Ab1-H2, Ab2g-Raw, Ab2g-H2.\n\n"
            "This packaging round only materializes synthetic smoke + preflight "
            "artifacts. Full 0.6B ITT H2 replay and EvalPlus are intentionally not "
            "executed here. H2 remains `development_candidate_not_frozen`.\n"
        ).encode("utf-8"),
    }


def write_smoke_outputs(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    outputs = build_smoke_artifact_bytes(repo_root)
    out_dir = repo_root / OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for name, payload in outputs.items():
        path = out_dir / name
        path.write_bytes(payload)
        hashes[name] = _sha256_bytes(payload)
    return hashes


def preflight(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    rule_sha = verify_h2_rule(repo_root)
    ab3 = ab3_baseline_hashes(repo_root)
    for dataset in ("humaneval", "mbpp"):
        _require((repo_root / TASK_FILES[dataset]).is_file(), f"missing {dataset} tasks")
        _require(
            (repo_root / RUN_DIRS[dataset] / "generation_attempts.jsonl").is_file(),
            f"missing {dataset} attempts",
        )
        for treatment in TREATMENTS:
            _require(
                (repo_root / RUN_DIRS[dataset] / f"{treatment}.jsonl").is_file(),
                f"missing {dataset}/{treatment}.jsonl",
            )
    # Ensure Ab3 paths are distinct from H2 output dir.
    out = (repo_root / OUTPUT_RELATIVE).resolve()
    for relative in AB3_BASELINES.values():
        _require((repo_root / relative).resolve() != out, "H2 output collides with Ab3")
    return {
        "status": "zero_model_preflight_passed",
        "model_calls": 0,
        "h2_rule_sha256": rule_sha,
        "h2_rule_status": RULE_STATUS,
        "ab3_baseline_hashes": ab3,
        "output_directory": OUTPUT_RELATIVE.as_posix(),
    }


def replay_itt_roster(
    *,
    dataset: str,
    repo_root: Path = REPO_ROOT,
    max_tasks: int | None = None,
) -> list[dict[str, Any]]:
    """Full ITT four-condition builder for one dataset."""
    roster = load_task_roster(dataset, repo_root)
    if max_tasks is not None:
        roster = roster[:max_tasks]
    completions = {
        treatment: load_treatment_completions(dataset, treatment, repo_root)
        for treatment in TREATMENTS
    }
    attempts = load_generation_attempts(dataset, repo_root)
    records: list[dict[str, Any]] = []
    for task in roster:
        records.extend(
            build_four_conditions_for_task(
                dataset=dataset,
                task=task,
                completions=completions,
                attempts=attempts,
            )
        )
    return records


def resolve_datasets(dataset: str) -> list[str]:
    if dataset == "all":
        return ["humaneval", "mbpp"]
    _require(dataset in TASK_FILES, f"unsupported dataset: {dataset}")
    return [dataset]


def expected_itt_states(datasets: Sequence[str]) -> int:
    return sum(EXPECTED_TASK_COUNTS[name] * len(CONDITIONS) for name in datasets)


def snapshot_protected_inputs(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    hashes = ab3_baseline_hashes(repo_root)
    hashes[RULE_RELATIVE.as_posix()] = verify_h2_rule(repo_root)
    for relative in PROTECTED_RUN_FILES:
        path = repo_root / relative
        _require(path.is_file(), f"missing protected input: {relative.as_posix()}")
        hashes[relative.as_posix()] = _sha256_bytes(path.read_bytes())
    return hashes


def assert_protected_inputs_unchanged(
    before: Mapping[str, str], repo_root: Path = REPO_ROOT
) -> None:
    after = snapshot_protected_inputs(repo_root)
    _require(before == after, "protected H2/Ab3/0.6B inputs changed during run")


def materialize_full_benchmark_cells(
    *,
    datasets: Sequence[str],
    repo_root: Path = REPO_ROOT,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for dataset in datasets:
        roster = load_task_roster(dataset, repo_root)
        _require(
            len(roster) == EXPECTED_TASK_COUNTS[dataset],
            f"{dataset} roster size drift: {len(roster)}",
        )
        cells.extend(replay_itt_roster(dataset=dataset, repo_root=repo_root))
    _require(
        len(cells) == expected_itt_states(datasets),
        f"ITT state count drift: {len(cells)}",
    )
    return cells


def cell_ledger_row(cell: Mapping[str, Any]) -> dict[str, Any]:
    """Serializable per-condition ITT row (omit bulky source body)."""
    return {
        "dataset": cell["dataset"],
        "task_id": cell["task_id"],
        "treatment": cell["treatment"],
        "condition": cell["condition"],
        "entry_point": cell["entry_point"],
        "input_sha256": cell.get("input_sha256"),
        "output_sha256": cell.get("output_sha256"),
        "rule_id": cell.get("rule_id"),
        "rule_sha256": cell.get("rule_sha256"),
        "rule_status": cell.get("rule_status"),
        "triggered": cell.get("triggered"),
        "transformed": cell.get("transformed"),
        "abstained": cell.get("abstained"),
        "reason": cell.get("reason"),
        "guard_results": cell.get("guard_results"),
        "extraction_unambiguous": cell.get("extraction_unambiguous"),
        "source_complete": cell.get("source_complete"),
        "missing_extracted_completion": cell.get("missing_extracted_completion"),
        "byte_identical_to_input": cell.get("byte_identical_to_input"),
    }


def write_condition_samples_jsonl(
    *,
    cells: Sequence[Mapping[str, Any]],
    dataset: str,
    condition: str,
    path: Path,
) -> dict[str, Any]:
    """Write full-ITT EvalPlus samples; missing completions use empty solution."""
    selected = [cell for cell in cells if cell["dataset"] == dataset and cell["condition"] == condition]
    _require(
        len(selected) == EXPECTED_TASK_COUNTS[dataset],
        f"{dataset}/{condition} sample count drift: {len(selected)}",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    missing = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for cell in selected:
            if cell.get("missing_extracted_completion") or not cell.get("output_source"):
                missing += 1
                payload = {"task_id": cell["task_id"], "solution": ""}
            else:
                payload = {
                    "task_id": cell["task_id"],
                    "completion": cell["output_source"],
                }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {
        "path": path.as_posix(),
        "dataset": dataset,
        "condition": condition,
        "task_count": len(selected),
        "missing_extracted_completion": missing,
        "sha256": _sha256_bytes(path.read_bytes()),
    }


def write_full_benchmark_samples(
    *,
    cells: Sequence[Mapping[str, Any]],
    datasets: Sequence[str],
    samples_dir: Path,
) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for dataset in datasets:
        for condition in CONDITIONS:
            path = samples_dir / dataset / f"{condition}.jsonl"
            manifests.append(
                write_condition_samples_jsonl(
                    cells=cells,
                    dataset=dataset,
                    condition=condition,
                    path=path,
                )
            )
    return manifests


def _strict_status(base: str, plus: str) -> str:
    return "pass" if base == "pass" and plus == "pass" else "fail"


def classify_paired_outcome(
    *,
    raw_strict: str,
    h2_strict: str,
    missing: bool,
) -> str:
    if missing:
        return "missing_extracted_completion"
    if raw_strict == "pass" and h2_strict == "pass":
        return "preserved_pass"
    if raw_strict == "pass" and h2_strict != "pass":
        return "regression"
    if raw_strict != "pass" and h2_strict == "pass":
        return "verified_rescue"
    return "unchanged_failure"


def parse_evalplus_result_file(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict) and isinstance(data.get("eval"), dict), f"bad EvalPlus result: {path}")
    out: dict[str, dict[str, str]] = {}
    for task_id, entries in data["eval"].items():
        _require(isinstance(entries, list) and entries, f"missing entries for {task_id}")
        entry = entries[0]
        base = str(entry.get("base_status", "")).lower()
        plus = str(entry.get("plus_status", "")).lower()
        out[task_id] = {
            "base_status": base,
            "plus_status": plus,
            "strict_status": _strict_status(base, plus),
        }
    return out


def invoke_evalplus_cli(
    *,
    dataset: str,
    samples_path: Path,
    timeout_seconds: float = 7200.0,
) -> subprocess.CompletedProcess[str]:
    _require(
        not (os.name == "nt" or sys.platform.startswith("win")),
        "full EvalPlus requires WSL/Linux (native Windows aborted)",
    )
    cmd = [
        sys.executable,
        "-m",
        "evalplus.evaluate",
        "--dataset",
        dataset,
        "--samples",
        str(samples_path),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


EvaluateFn = Callable[..., dict[str, dict[str, str]]]


def default_evaluate_condition(
    *,
    dataset: str,
    condition: str,
    samples_path: Path,
    eval_output_dir: Path,
    parallel: int,
) -> dict[str, dict[str, str]]:
    _require(parallel == 1, "parallel must equal 1")
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    proc = invoke_evalplus_cli(dataset=dataset, samples_path=samples_path)
    (eval_output_dir / "stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (eval_output_dir / "stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    _require(
        proc.returncode == 0,
        f"EvalPlus failed for {dataset}/{condition}: rc={proc.returncode}",
    )
    result_path = samples_path.with_name(samples_path.stem + "_eval_results.json")
    _require(result_path.is_file(), f"missing EvalPlus result: {result_path}")
    # Keep a copy under the run output tree without touching the samples sibling
    # only when results already sit next to samples (EvalPlus default).
    copied = eval_output_dir / "eval_results.json"
    copied.write_bytes(result_path.read_bytes())
    parsed = parse_evalplus_result_file(copied)
    (eval_output_dir / "eval_summary.json").write_bytes(
        _canonical_json(
            {
                "dataset": dataset,
                "condition": condition,
                "task_count": len(parsed),
                "base_pass": sum(v["base_status"] == "pass" for v in parsed.values()),
                "plus_pass": sum(v["plus_status"] == "pass" for v in parsed.values()),
                "strict_pass": sum(v["strict_status"] == "pass" for v in parsed.values()),
                "evaluator_engine": EVALPLUS_ENGINE,
                "evalplus_version": EXPECTED_EVALPLUS_VERSION,
                "parallel": 1,
            }
        )
    )
    return parsed


def build_paired_cell_ledger(
    *,
    cells: Sequence[Mapping[str, Any]],
    eval_by_key: Mapping[tuple[str, str, str], Mapping[str, str]],
) -> list[dict[str, Any]]:
    by_identity: dict[tuple[str, str, str], dict[str, Any]] = {}
    for cell in cells:
        key = (cell["dataset"], cell["task_id"], cell["treatment"])
        by_identity.setdefault(key, {})[cell["condition"]] = cell

    paired: list[dict[str, Any]] = []
    for (dataset, task_id, treatment), cond_map in sorted(by_identity.items()):
        raw_name = "Ab1-Raw" if treatment == "ab1" else "Ab2g-Raw"
        h2_name = "Ab1-H2" if treatment == "ab1" else "Ab2g-H2"
        raw_cell = cond_map[raw_name]
        h2_cell = cond_map[h2_name]
        raw_eval = eval_by_key[(dataset, raw_name, task_id)]
        h2_eval = eval_by_key[(dataset, h2_name, task_id)]
        missing = bool(raw_cell.get("missing_extracted_completion"))
        outcome = classify_paired_outcome(
            raw_strict=raw_eval["strict_status"],
            h2_strict=h2_eval["strict_status"],
            missing=missing,
        )
        paired.append(
            {
                "dataset": dataset,
                "task_id": task_id,
                "treatment": treatment,
                "entry_point": raw_cell["entry_point"],
                "raw_condition": raw_name,
                "h2_condition": h2_name,
                "missing_extracted_completion": missing,
                "triggered": h2_cell.get("triggered"),
                "transformed": h2_cell.get("transformed"),
                "abstained": h2_cell.get("abstained"),
                "reason": h2_cell.get("reason"),
                "guard_results": h2_cell.get("guard_results"),
                "extraction_unambiguous": h2_cell.get("extraction_unambiguous"),
                "source_complete": h2_cell.get("source_complete"),
                "input_sha256": h2_cell.get("input_sha256"),
                "output_sha256": h2_cell.get("output_sha256"),
                "rule_id": h2_cell.get("rule_id"),
                "rule_sha256": h2_cell.get("rule_sha256"),
                "rule_status": h2_cell.get("rule_status"),
                "raw_base_status": raw_eval["base_status"],
                "raw_plus_status": raw_eval["plus_status"],
                "raw_strict_status": raw_eval["strict_status"],
                "h2_base_status": h2_eval["base_status"],
                "h2_plus_status": h2_eval["plus_status"],
                "h2_strict_status": h2_eval["strict_status"],
                "outcome": outcome,
            }
        )
    return paired


def aggregate_full_benchmark_stats(
    *,
    cells: Sequence[Mapping[str, Any]],
    paired: Sequence[Mapping[str, Any]],
    datasets: Sequence[str],
) -> dict[str, Any]:
    h2_cells = [cell for cell in cells if cell["condition"].endswith("-H2")]
    outcome_counts = Counter(row["outcome"] for row in paired)
    return {
        "datasets": list(datasets),
        "task_count": sum(EXPECTED_TASK_COUNTS[name] for name in datasets),
        "itt_states": len(cells),
        "paired_rows": len(paired),
        "conditions": list(CONDITIONS),
        "triggered": sum(1 for cell in h2_cells if cell.get("triggered")),
        "transformed": sum(1 for cell in h2_cells if cell.get("transformed")),
        "abstained": sum(1 for cell in h2_cells if cell.get("abstained")),
        "missing_extracted_completion": sum(
            1 for cell in cells if cell.get("missing_extracted_completion")
        ),
        "verified_rescue": outcome_counts.get("verified_rescue", 0),
        "regression": outcome_counts.get("regression", 0),
        "preserved_pass": outcome_counts.get("preserved_pass", 0),
        "unchanged_failure": outcome_counts.get("unchanged_failure", 0),
        "missing_extracted_completion_paired": outcome_counts.get(
            "missing_extracted_completion", 0
        ),
        "outcomes": dict(sorted(outcome_counts.items())),
        "model_calls": 0,
    }


def run_full_benchmark(
    *,
    dataset: str,
    output_dir: Path,
    parallel: int,
    dry_run: bool = False,
    repo_root: Path = REPO_ROOT,
    evaluate_fn: EvaluateFn | None = None,
) -> dict[str, Any]:
    """Unique full-benchmark path: replay H2 on saved Ab1/Ab2g, then EvalPlus."""
    _require(parallel == 1, "parallel must equal 1")
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()
    else:
        output_dir = output_dir.resolve()
    _require(not output_dir.exists(), f"output exists; refuse overwrite: {output_dir}")

    datasets = resolve_datasets(dataset)
    before = snapshot_protected_inputs(repo_root)
    cells = materialize_full_benchmark_cells(datasets=datasets, repo_root=repo_root)

    output_dir.mkdir(parents=True, exist_ok=False)
    samples_dir = output_dir / "samples"
    sample_manifests = write_full_benchmark_samples(
        cells=cells, datasets=datasets, samples_dir=samples_dir
    )
    ledger_rows = [cell_ledger_row(cell) for cell in cells]
    (output_dir / "cell_ledger.jsonl").write_bytes(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in ledger_rows
        ).encode("utf-8")
    )

    plan = {
        "command": "run-full-benchmark",
        "dataset_arg": dataset,
        "datasets": list(datasets),
        "output_dir": output_dir.as_posix(),
        "parallel": parallel,
        "dry_run": dry_run,
        "itt_states": len(cells),
        "expected_itt_states": expected_itt_states(datasets),
        "sample_files": sample_manifests,
        "conditions": list(CONDITIONS),
        "model_calls": 0,
        "evalplus_engine": EVALPLUS_ENGINE,
        "h2_rule_sha256": before[RULE_RELATIVE.as_posix()],
        "protected_input_sha256": before,
    }
    (output_dir / "execution_plan.json").write_bytes(_canonical_json(plan))

    if dry_run:
        dry_manifest = {
            "status": "dry_run_materialized_not_evaluated",
            "evalplus_executed": False,
            "model_calls": 0,
            "itt_states": len(cells),
            "paired_rows_expected": len(cells) // 2,
            "datasets": list(datasets),
            "sample_files": sample_manifests,
            "stats_preview": {
                "triggered": sum(
                    1
                    for cell in cells
                    if cell["condition"].endswith("-H2") and cell.get("triggered")
                ),
                "transformed": sum(
                    1
                    for cell in cells
                    if cell["condition"].endswith("-H2") and cell.get("transformed")
                ),
                "abstained": sum(
                    1
                    for cell in cells
                    if cell["condition"].endswith("-H2") and cell.get("abstained")
                ),
                "missing_extracted_completion": sum(
                    1 for cell in cells if cell.get("missing_extracted_completion")
                ),
            },
        }
        (output_dir / "dry_run_manifest.json").write_bytes(_canonical_json(dry_manifest))
        assert_protected_inputs_unchanged(before, repo_root)
        return dry_manifest

    evaluator = evaluate_fn or default_evaluate_condition
    eval_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for sample in sample_manifests:
        ds = sample["dataset"]
        condition = sample["condition"]
        samples_path = Path(sample["path"])
        if not samples_path.is_absolute():
            samples_path = repo_root / samples_path
        parsed = evaluator(
            dataset=ds,
            condition=condition,
            samples_path=samples_path,
            eval_output_dir=output_dir / "evalplus" / ds / condition,
            parallel=parallel,
        )
        _require(
            len(parsed) == EXPECTED_TASK_COUNTS[ds],
            f"EvalPlus coverage drift for {ds}/{condition}: {len(parsed)}",
        )
        for task_id, statuses in parsed.items():
            eval_by_key[(ds, condition, task_id)] = dict(statuses)

    paired = build_paired_cell_ledger(cells=cells, eval_by_key=eval_by_key)
    stats = aggregate_full_benchmark_stats(
        cells=cells, paired=paired, datasets=datasets
    )
    (output_dir / "paired_cell_ledger.jsonl").write_bytes(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in paired
        ).encode("utf-8")
    )
    (output_dir / "aggregate_summary.json").write_bytes(_canonical_json(stats))
    execution = {
        "status": "full_benchmark_evalplus_complete",
        "evalplus_executed": True,
        "model_calls": 0,
        "datasets": list(datasets),
        "itt_states": len(cells),
        "paired_rows": len(paired),
        "parallel": parallel,
        "evaluator_engine": EVALPLUS_ENGINE,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "aggregate": stats,
    }
    (output_dir / "execution_record.json").write_bytes(_canonical_json(execution))
    assert_protected_inputs_unchanged(before, repo_root)
    return execution


def build_full_eval_package_readme() -> bytes:
    return (
        "# qwen06 H2 full replay evaluation v1\n\n"
        "Status: `RUNNER_ENABLED_NOT_EXECUTED`\n\n"
        "Unique entrypoint (zero model calls; reads saved Ab1/Ab2g only):\n\n"
        "```bash\n"
        "python scripts/run_qwen06_h2_replay_pipeline_v1.py run-full-benchmark \\\n"
        "  --dataset all \\\n"
        "  --output-dir artifacts/public_benchmark_governance/"
        "qwen06_h2_full_replay_evaluation_v1/manual_run_001 \\\n"
        "  --parallel 1\n"
        "```\n\n"
        "Dry-run (materialize 2,168 ITT states + samples; no EvalPlus):\n\n"
        "```bash\n"
        "python scripts/run_qwen06_h2_replay_pipeline_v1.py run-full-benchmark \\\n"
        "  --dataset all \\\n"
        "  --output-dir /tmp/qwen06_h2_full_dry_run \\\n"
        "  --parallel 1 \\\n"
        "  --dry-run\n"
        "```\n\n"
        "Formal EvalPlus requires WSL/Linux. This packaging round does **not** "
        "execute `manual_run_001`.\n"
    ).encode("utf-8")


def write_full_eval_package_stub(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """Trackable governance stub proving the runner exists but is not executed."""
    out_dir = repo_root / FULL_EVAL_PACKAGE_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "README.md": build_full_eval_package_readme(),
        "runner_status.json": _canonical_json(
            {
                "status": "RUNNER_ENABLED_NOT_EXECUTED",
                "entrypoint": (
                    "python scripts/run_qwen06_h2_replay_pipeline_v1.py "
                    "run-full-benchmark --dataset all "
                    f"--output-dir {DEFAULT_FULL_RUN_OUTPUT.as_posix()} "
                    "--parallel 1"
                ),
                "itt_states_expected": EXPECTED_ITT_STATES_ALL,
                "task_count_expected": 542,
                "conditions": list(CONDITIONS),
                "model_calls": 0,
                "manual_run_001_executed": False,
                "h2_rule_sha256": EXPECTED_RULE_SHA256,
                "h2_rule_status": EXPECTED_RULE_STATUS,
            }
        ),
    }
    hashes: dict[str, str] = {}
    for name, payload in payloads.items():
        path = out_dir / name
        path.write_bytes(payload)
        hashes[name] = _sha256_bytes(payload)
    return hashes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Zero-model path/SHA preflight")
    pre.set_defaults(func=lambda _args: preflight())

    smoke = sub.add_parser("smoke", help="Write synthetic smoke + pipeline manifest")
    smoke.set_defaults(
        func=lambda _args: {
            "status": "smoke_written",
            "artifact_sha256": write_smoke_outputs(),
            "model_calls": 0,
        }
    )

    inspect = sub.add_parser(
        "inspect-wiring",
        help="Show how four conditions are formed (zero writes beyond stdout)",
    )

    def _inspect(_args: argparse.Namespace) -> dict[str, Any]:
        return {
            "status": "wiring_ok",
            "data_flow": (
                "fixed extractor completion → H2 → Ab1-Raw/Ab1-H2/Ab2g-Raw/Ab2g-H2 "
                "→ EvalPlus(base/plus)"
            ),
            "h2_entry": (
                "quarantine_module_assert_entrypoint_selftest("
                "source=completion, entry_point=..., "
                "extraction_unambiguous=..., source_complete=...)"
            ),
            "conditions": list(CONDITIONS),
            "model_calls": 0,
            "full_benchmark_entrypoint": "run-full-benchmark",
            "itt_states_expected_all": EXPECTED_ITT_STATES_ALL,
        }

    inspect.set_defaults(func=_inspect)

    full = sub.add_parser(
        "run-full-benchmark",
        help="Replay H2 on saved Ab1/Ab2g and evaluate EvalPlus base/plus",
    )
    full.add_argument(
        "--dataset",
        required=True,
        choices=("all", "humaneval", "mbpp"),
        help="Benchmark scope; 'all' = HumanEval+164 + MBPP+378",
    )
    full.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh output directory (must not already exist)",
    )
    full.add_argument(
        "--parallel",
        type=int,
        required=True,
        help="Must be 1",
    )
    full.add_argument(
        "--dry-run",
        action="store_true",
        help="Materialize 2,168 ITT states + samples without EvalPlus",
    )

    def _run_full(args: argparse.Namespace) -> dict[str, Any]:
        return run_full_benchmark(
            dataset=args.dataset,
            output_dir=args.output_dir,
            parallel=args.parallel,
            dry_run=args.dry_run,
        )

    full.set_defaults(func=_run_full)

    stub = sub.add_parser(
        "write-full-eval-stub",
        help="Write governance README/status for the unexecuted full runner",
    )
    stub.set_defaults(
        func=lambda _args: {
            "status": "full_eval_stub_written",
            "artifact_sha256": write_full_eval_package_stub(),
            "model_calls": 0,
        }
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
