#!/usr/bin/env python3
"""Minimal model-parameterized public benchmark H2 EvalPlus runner.

Supports:
- Models: qwen3.5:4b, qwen3.5:9b, qwen3:0.6b
- Datasets: humaneval (656 cells), mbpp (1512 cells), all (2168 cells)
- Planned Eval Cells: 2,168 total per model (HumanEval: 656, MBPP: 1,512)
- Zero LLM model calls (model_calls = 0)
- Reads materialized replay journals from artifacts/public_benchmark_governance/<model_key>_h2_full_replay_v1/j/
- Persistent UTF-8 IPC worker server with auto-recovery and per-cell timeout protection
- Incremental per-cell result logging supporting --resume
- CLI flags: --model, --dataset, --dry-run, --resume, --parallel 1, --output-dir
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import pathlib
import subprocess
import sys
import threading
import types
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Setup Windows compatibility environment BEFORE importing evalplus
os.environ["EVALPLUS_MAX_MEMORY_BYTES"] = "-1"
if "resource" not in sys.modules:
    dummy_resource = types.ModuleType("resource")
    dummy_resource.RLIMIT_AS = 9
    dummy_resource.getrlimit = lambda x: (1, 1)
    dummy_resource.setrlimit = lambda x, y: None
    sys.modules["resource"] = dummy_resource

import evalplus  # noqa: E402
import evalplus.eval  # noqa: E402
import evalplus.eval.utils  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)

EXPECTED_EVALPLUS_VERSION = "0.3.1"
ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")
CONDITIONS = ("Ab1-Raw", "Ab1-H2", "Ab2g-Raw", "Ab2g-H2")

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "replay_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h2_full_replay_v1"),
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h2_full_evalplus_v1"),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "replay_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h2_full_replay_v1"),
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h2_full_evalplus_v1"),
    },
    "qwen3:0.6b": {
        "model_key": "qwen06",
        "replay_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen06_h2_full_replay_evaluation_v1"),
        "default_output": pathlib.Path("artifacts/public_benchmark_governance/qwen06_h2_full_evalplus_v1"),
    },
}


class EvalPlusRunnerError(RuntimeError):
    """Fail-closed error for EvalPlus runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvalPlusRunnerError(message)


def zero_eval_preflight(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes zero-eval preflight verifying environment, EvalPlus version, and replay journals."""
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")

    actual_version = getattr(evalplus, "__version__", "unknown")
    _require(
        actual_version == EXPECTED_EVALPLUS_VERSION,
        f"EvalPlus version mismatch: expected {EXPECTED_EVALPLUS_VERSION}, got {actual_version}",
    )

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"

    planned_he = 656 if dataset in ("humaneval", "all") else 0
    planned_mb = 1512 if dataset in ("mbpp", "all") else 0
    total_planned = planned_he + planned_mb

    return {
        "status": "zero_eval_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": actual_version,
        "planned_eval_cells": total_planned,
        "humaneval_eval_cells": planned_he,
        "mbpp_eval_cells": planned_mb,
        "replay_journal_dir": replay_j_dir.as_posix(),
        "replay_journals_exist": replay_j_dir.is_dir(),
        "model_calls": 0,
        "evalplus_executed": False,
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Performs dry-run readiness audit for EvalPlus execution."""
    preflight = zero_eval_preflight(model=model, dataset=dataset, repo_root=repo_root)

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"

    total_journals = 0
    he_journals = 0
    mb_journals = 0

    if replay_j_dir.is_dir():
        for p in replay_j_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                tid = str(data.get("task_id", ""))
                if dataset == "humaneval" and not tid.startswith("HumanEval"):
                    continue
                if dataset == "mbpp" and not tid.startswith("Mbpp"):
                    continue
                total_journals += 1
                if tid.startswith("HumanEval"):
                    he_journals += 1
                elif tid.startswith("Mbpp"):
                    mb_journals += 1
            except Exception:
                pass

    readiness = "READY" if total_journals == preflight["planned_eval_cells"] else "NOT_READY"

    return {
        "status": "dry_run_completed",
        "model_tag": model,
        "dataset": dataset,
        "readiness_status": readiness,
        "planned_eval_cells": preflight["planned_eval_cells"],
        "humaneval_eval_cells": preflight["humaneval_eval_cells"],
        "mbpp_eval_cells": preflight["mbpp_eval_cells"],
        "present_replay_journals": total_journals,
        "humaneval_present_journals": he_journals,
        "mbpp_present_journals": mb_journals,
        "missing_replay_journals": preflight["planned_eval_cells"] - total_journals,
        "model_calls": 0,
        "evalplus_executed": False,
    }


WORKER_SCRIPT = """
import os, sys, types, json, contextlib
os.environ['EVALPLUS_MAX_MEMORY_BYTES'] = '-1'

real_stdout = sys.stdout
sys.stdout = sys.stderr

m = types.ModuleType('resource')
m.RLIMIT_AS = 9
m.getrlimit = lambda x: (1, 1)
m.setrlimit = lambda x, y: None
sys.modules['resource'] = m

import evalplus.eval.utils
import evalplus.eval

def noop_guard(maximum_memory_bytes=None):
    pass

evalplus.eval.utils.reliability_guard = noop_guard
evalplus.eval.reliability_guard = noop_guard

@contextlib.contextmanager
def dummy_time_limit(seconds: float):
    yield

evalplus.eval.utils.time_limit = dummy_time_limit
evalplus.eval.time_limit = dummy_time_limit

from evalplus.data import get_human_eval_plus, get_human_eval_plus_hash, get_mbpp_plus, get_mbpp_plus_hash
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
from evalplus.evaluate import get_groundtruth

he_tasks = get_human_eval_plus()
he_gt = get_groundtruth(he_tasks, get_human_eval_plus_hash(), [])
mb_tasks = get_mbpp_plus()
mb_gt = get_groundtruth(mb_tasks, get_mbpp_plus_hash(), MBPP_OUTPUT_NOT_NONE_TASKS)

sys.stdout = real_stdout
sys.stdout.write('READY\\n')
sys.stdout.flush()

for line in sys.stdin:
    if not line.strip():
        continue
    req = json.loads(line)
    dataset = req['dataset']
    task_id = req['task_id']
    entry_point = req['entry_point']
    code = req['code']

    tasks = he_tasks if dataset == 'humaneval' else mb_tasks
    gt = he_gt if dataset == 'humaneval' else mb_gt

    problem = tasks.get(task_id)
    gt_item = gt.get(task_id)

    if not problem or not gt_item or not code or not code.strip():
        res = {'base_pass': False, 'plus_pass': False, 'final_pass': False}
    else:
        prefix = 'from typing import *\\nimport math, sys, os, collections, itertools, functools, heapq, bisect\\n'
        full_code = prefix + code

        import multiprocessing
        stat_base = multiprocessing.Value('i', 0)
        details_base = multiprocessing.Array('b', [False for _ in range(len(problem['base_input']))])
        progress_base = multiprocessing.Value('i', 0)
        time_limits_base = [1.0 for _ in problem['base_input']]

        evalplus.eval.unsafe_execute(
            dataset,
            entry_point,
            full_code,
            problem['base_input'],
            gt_item['base'],
            time_limits_base,
            problem['atol'],
            True,
            stat_base,
            details_base,
            progress_base
        )

        stat_plus = multiprocessing.Value('i', 0)
        details_plus = multiprocessing.Array('b', [False for _ in range(len(problem['plus_input']))])
        progress_plus = multiprocessing.Value('i', 0)
        time_limits_plus = [1.0 for _ in problem['plus_input']]

        evalplus.eval.unsafe_execute(
            dataset,
            entry_point,
            full_code,
            problem['plus_input'],
            gt_item['plus'],
            time_limits_plus,
            problem['atol'],
            True,
            stat_plus,
            details_plus,
            progress_plus
        )

        base_pass = (stat_base.value == 0 and len(details_base) >= len(problem['base_input']) and all(details_base[:len(problem['base_input'])]))
        plus_pass = (stat_plus.value == 0 and len(details_plus) >= len(problem['plus_input']) and all(details_plus[:len(problem['plus_input'])]))
        res = {'base_pass': base_pass, 'plus_pass': plus_pass, 'final_pass': base_pass and plus_pass}

    sys.stdout.write(json.dumps(res) + '\\n')
    sys.stdout.flush()
"""


class PersistentEvalWorker:
    """Persistent UTF-8 IPC worker server with threaded per-cell timeout protection."""

    def __init__(self, per_cell_timeout: float = 3.0) -> None:
        self.per_cell_timeout = per_cell_timeout
        self.proc: subprocess.Popen[str] | None = None
        self._start_worker()

    def _start_worker(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-c", WORKER_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if not line or "READY" in line:
                break

    def evaluate(self, dataset: str, task_id: str, entry_point: str, code: str) -> tuple[bool, bool, bool]:
        if not code or not code.strip():
            return False, False, False

        if self.proc is None or self.proc.poll() is not None:
            self._start_worker()

        req = {
            "dataset": dataset,
            "task_id": task_id,
            "entry_point": entry_point,
            "code": code,
        }

        try:
            assert self.proc is not None and self.proc.stdin is not None and self.proc.stdout is not None
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()

            line_res: list[str | None] = [None]

            def read_target():
                try:
                    if self.proc and self.proc.stdout:
                        line_res[0] = self.proc.stdout.readline()
                except Exception:
                    pass

            t = threading.Thread(target=read_target)
            t.daemon = True
            t.start()
            t.join(self.per_cell_timeout)

            if t.is_alive() or not line_res[0]:
                if self.proc:
                    self.proc.kill()
                    self.proc.wait()
                self.proc = None
                return False, False, False

            data = json.loads(line_res[0].strip())
            return bool(data.get("base_pass")), bool(data.get("plus_pass")), bool(data.get("final_pass"))
        except Exception:
            if self.proc:
                try:
                    self.proc.kill()
                    self.proc.wait()
                except Exception:
                    pass
            self.proc = None

        return False, False, False

    def close(self) -> None:
        if self.proc:
            try:
                self.proc.kill()
                self.proc.wait()
            except Exception:
                pass
            self.proc = None


def run_evalplus_execution(
    *,
    model: str,
    dataset: str,
    resume: bool = True,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes formal EvalPlus evaluation on materialized replay journals."""
    dry_audit = run_dry_run(model=model, dataset=dataset, repo_root=repo_root)
    _require(
        dry_audit["readiness_status"] == "READY",
        f"replay journals incomplete for {model} on {dataset}: missing {dry_audit['missing_replay_journals']} journals",
    )

    spec = MODEL_SPECS[model]
    replay_j_dir = repo_root / spec["replay_dir"] / "j"

    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    eval_j_dir = out_dir / "j"
    eval_j_dir.mkdir(parents=True, exist_ok=True)

    j_files = sorted(list(replay_j_dir.glob("*.json")))

    eval_journals: list[dict[str, Any]] = []
    executed_count = 0
    skipped_count = 0

    worker = PersistentEvalWorker(per_cell_timeout=3.0)

    try:
        for j_file in j_files:
            rj = json.loads(j_file.read_text(encoding="utf-8"))
            tid = str(rj.get("task_id", ""))
            cond = str(rj.get("condition", ""))
            cid = str(rj.get("cell_identity", ""))
            ep = str(rj.get("entry_point", ""))
            src = rj.get("output_source", "") or ""

            if dataset == "humaneval" and not tid.startswith("HumanEval"):
                continue
            if dataset == "mbpp" and not tid.startswith("Mbpp"):
                continue

            ej_file = eval_j_dir / f"{cid}.json"

            if resume and ej_file.is_file():
                try:
                    existing = json.loads(ej_file.read_text(encoding="utf-8"))
                    if existing.get("persisted_complete") is True:
                        skipped_count += 1
                        eval_journals.append(existing)
                        continue
                except Exception:
                    pass

            ds_type = "humaneval" if tid.startswith("HumanEval") else "mbpp"

            base_pass, plus_pass, final_pass = worker.evaluate(
                ds_type, tid, ep, src
            )

            ej = {
                "cell_identity": cid,
                "model_tag": model,
                "dataset": ds_type,
                "task_id": tid,
                "condition": cond,
                "entry_point": ep,
                "output_source": src,
                "has_output_source": bool(src and src.strip()),
                "evalplus_base_pass": base_pass,
                "evalplus_plus_pass": plus_pass,
                "evalplus_final_pass": final_pass,
                "persisted_complete": True,
                "runner_identity": "public_benchmark_h2_evalplus_runner_v1",
            }
            durable_write_json_new(ej_file, ej)
            executed_count += 1
            eval_journals.append(ej)
    finally:
        worker.close()

    total_eval = len(eval_journals)

    cell_map: dict[tuple[str, str], dict[str, Any]] = {}
    for ej in eval_journals:
        cell_map[(ej["task_id"], ej["condition"])] = ej

    def compute_stats(task_filter: str) -> dict[str, Any]:
        tasks_subset = {ej["task_id"] for ej in eval_journals if ej["task_id"].startswith(task_filter)}
        
        ab1_raw_pass = sum(1 for tid in tasks_subset if cell_map.get((tid, "Ab1-Raw"), {}).get("evalplus_final_pass"))
        ab1_h2_pass = sum(1 for tid in tasks_subset if cell_map.get((tid, "Ab1-H2"), {}).get("evalplus_final_pass"))
        ab2g_raw_pass = sum(1 for tid in tasks_subset if cell_map.get((tid, "Ab2g-Raw"), {}).get("evalplus_final_pass"))
        ab2g_h2_pass = sum(1 for tid in tasks_subset if cell_map.get((tid, "Ab2g-H2"), {}).get("evalplus_final_pass"))

        ab1_outcomes = {"verified_rescue": 0, "preserved_pass": 0, "unchanged_failure": 0, "regression": 0, "abstained_or_missing": 0}
        ab2g_outcomes = {"verified_rescue": 0, "preserved_pass": 0, "unchanged_failure": 0, "regression": 0, "abstained_or_missing": 0}

        for tid in tasks_subset:
            # Ab1 pair
            r1 = cell_map.get((tid, "Ab1-Raw"))
            h1 = cell_map.get((tid, "Ab1-H2"))
            if not r1 or not h1 or not r1.get("has_output_source"):
                ab1_outcomes["abstained_or_missing"] += 1
            else:
                rp, hp = r1.get("evalplus_final_pass", False), h1.get("evalplus_final_pass", False)
                if not rp and hp: ab1_outcomes["verified_rescue"] += 1
                elif rp and hp: ab1_outcomes["preserved_pass"] += 1
                elif not rp and not hp: ab1_outcomes["unchanged_failure"] += 1
                elif rp and not hp: ab1_outcomes["regression"] += 1

            # Ab2g pair
            r2 = cell_map.get((tid, "Ab2g-Raw"))
            h2 = cell_map.get((tid, "Ab2g-H2"))
            if not r2 or not h2 or not r2.get("has_output_source"):
                ab2g_outcomes["abstained_or_missing"] += 1
            else:
                rp, hp = r2.get("evalplus_final_pass", False), h2.get("evalplus_final_pass", False)
                if not rp and hp: ab2g_outcomes["verified_rescue"] += 1
                elif rp and hp: ab2g_outcomes["preserved_pass"] += 1
                elif not rp and not hp: ab2g_outcomes["unchanged_failure"] += 1
                elif rp and not hp: ab2g_outcomes["regression"] += 1

        return {
            "pass_counts": {
                "Ab1-Raw": ab1_raw_pass,
                "Ab1-H2": ab1_h2_pass,
                "Ab2g-Raw": ab2g_raw_pass,
                "Ab2g-H2": ab2g_h2_pass,
            },
            "paired_outcomes": {
                "ab1": ab1_outcomes,
                "ab2g": ab2g_outcomes,
            },
        }

    he_stats = compute_stats("HumanEval") if dataset in ("humaneval", "all") else {}
    mb_stats = compute_stats("Mbpp") if dataset in ("mbpp", "all") else {}
    overall_stats = compute_stats("")

    summary = {
        "status": "evalplus_execution_completed",
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "output_directory": out_dir.as_posix(),
        "total_evaluated_cells": total_eval,
        "expected_eval_cells": dry_audit["planned_eval_cells"],
        "missing": 0,
        "duplicate": 0,
        "executed_cells": executed_count,
        "skipped_resume_cells": skipped_count,
        "model_calls": 0,
        "evalplus_executed": True,
        "pass_counts": overall_stats["pass_counts"],
        "paired_outcomes": overall_stats["paired_outcomes"],
        "breakdown": {
            "humaneval": he_stats,
            "mbpp": mb_stats,
        },
    }

    # Write summary manifest
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Write cell_level_ledger.csv
    ledger_path = out_dir / "cell_level_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cell_identity", "task_id", "condition", "evalplus_base_pass", "evalplus_plus_pass", "evalplus_final_pass"])
        for ej in eval_journals:
            writer.writerow([
                ej["cell_identity"],
                ej["task_id"],
                ej["condition"],
                ej["evalplus_base_pass"],
                ej["evalplus_plus_pass"],
                ej["evalplus_final_pass"],
            ])

    # Write execution_manifest.json
    manifest_path = out_dir / "execution_manifest.json"
    manifest_data = {
        "plan_id": f"{spec['model_key']}_h2_full_evalplus_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_tag": model,
        "dataset": dataset,
        "evalplus_version": EXPECTED_EVALPLUS_VERSION,
        "total_evaluated_cells": total_eval,
        "model_calls": 0,
        "evalplus_executed": True,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)

    if args.parallel != 1:
        _require(False, "--parallel must be 1 for strict determinism")

    if args.dry_run:
        result = run_dry_run(model=args.model, dataset=args.dataset)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    result = run_evalplus_execution(
        model=args.model,
        dataset=args.dataset,
        resume=args.resume,
        output_dir_arg=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
