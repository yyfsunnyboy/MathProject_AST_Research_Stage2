"""Plan and run a sandboxed diagnosis of transformed cumulative H1--H4 failures.

This is exploratory ``development_candidate_not_frozen`` evidence.  Its
preflight mode is deliberately data-only: it reads the existing replay/v2
journals and writes a fresh 130-cell manifest, but never parses, imports, or
executes a candidate.  Execution is opt-in and is refused unless a Linux
bubblewrap+cgroup sandbox is available.

The diagnostic worker uses EvalPlus 0.3.1's public ``check_correctness`` path
against the real HumanEval+/MBPP+ tests.  It never invents entry-point inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_LABEL = "development_candidate_not_frozen"
SOURCE_PREFIX = "from typing import *\nimport math, sys, os, collections, itertools, functools, heapq, bisect\n"
EXPECTED_COUNTS = {"qwen3.5:4b": 78, "qwen3.5:9b": 52}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())
MODEL_SPECS = {
    "qwen3.5:4b": {
        "eval_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h1_h2_h3_h4_full_evalplus_v2"),
        "replay_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_4b_h1_h2_h3_h4_full_replay_v1"),
    },
    "qwen3.5:9b": {
        "eval_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h1_h2_h3_h4_full_evalplus_v2"),
        "replay_dir": pathlib.Path("artifacts/public_benchmark_governance/qwen35_9b_h1_h2_h3_h4_full_replay_v1"),
    },
}
OUTCOME_CATEGORIES = (
    "parse_failure",
    "entrypoint_callability_signature_failure",
    "runtime_exception",
    "timeout",
    "test_assertion_wrong_answer",
    "pass",
    "other_unclassifiable",
)

# Work directory must live under a path that already exists after the writable
# /tmp tmpfs is mounted. Creating /work on the read-only host root fails with
# "bwrap: Can't mkdir /work: Read-only file system".
SANDBOX_WORK_DIR = "/tmp/stage2-work"

# Written into a read-only file and run only inside the future OS sandbox.
# It deliberately uses the actual EvalPlus 0.3.1 task and ground-truth APIs;
# there are no synthetic arguments or hand-written assertions here.
WORKER = r'''
import ast, inspect, json, sys, traceback
from evalplus.data import get_human_eval_plus, get_human_eval_plus_hash, get_mbpp_plus, get_mbpp_plus_hash
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
from evalplus.evaluate import check_correctness, get_groundtruth

def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)

def trace(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    candidate = next((f for f in reversed(frames) if f.filename == "<candidate>"), None)
    return "exception_type=%s; candidate_line=%s" % (type(exc).__name__, candidate.lineno if candidate else "unavailable")

request = json.load(open(sys.argv[1], encoding="utf-8"))
source = request["source"]
try:
    tree = ast.parse(source, filename="<candidate>")
except SyntaxError as exc:
    emit({"phase":"parse", "exception_class":"SyntaxError", "parse_result":"failure", "detail":"candidate_line=%s" % exc.lineno})
    raise SystemExit(0)
try:
    if request["dataset"] == "humaneval":
        tasks = get_human_eval_plus(); groundtruth = get_groundtruth(tasks, get_human_eval_plus_hash(), [])
    elif request["dataset"] == "mbpp":
        tasks = get_mbpp_plus(); groundtruth = get_groundtruth(tasks, get_mbpp_plus_hash(), MBPP_OUTPUT_NOT_NONE_TASKS)
    else:
        raise ValueError("unsupported dataset")
    problem, expected = tasks[request["task_id"]], groundtruth[request["task_id"]]
    if problem["entry_point"] != request["entry_point"]:
        emit({"phase":"entrypoint", "exception_class":"EntryPointMismatch", "parse_result":"success", "detail":"journal entry point differs from actual EvalPlus task"})
        raise SystemExit(0)
    namespace = {"__name__": "__isolated_diagnosis__", "__file__": "<candidate>"}
    try:
        exec(compile(tree, "<candidate>", "exec"), namespace, namespace)
    except BaseException as exc:
        emit({"phase":"module_load", "exception_class":type(exc).__name__, "parse_result":"success", "detail":trace(exc)})
        raise SystemExit(0)
    entry = namespace.get(request["entry_point"])
    if entry is None or not callable(entry):
        emit({"phase":"entrypoint", "exception_class":"MissingOrNonCallableEntryPoint", "parse_result":"success", "detail":"actual EvalPlus entry point absent or non-callable"})
        raise SystemExit(0)
    try:
        inspect.signature(entry)
    except (TypeError, ValueError) as exc:
        emit({"phase":"entrypoint", "exception_class":type(exc).__name__, "parse_result":"success", "detail":"entry point has no inspectable callable signature"})
        raise SystemExit(0)
    result = check_correctness(request["dataset"], 0, problem, source, expected, base_only=False, fast_check=True)
    base, plus = str(result["base"][0]), str(result["plus"][0])
    emit({"phase":"evalplus_tests", "exception_class":"NONE", "parse_result":"success", "base_status":base, "plus_status":plus, "detail":"actual EvalPlus base/plus completed"})
except SystemExit:
    raise
except BaseException as exc:
    emit({"phase":"runtime", "exception_class":type(exc).__name__, "parse_result":"unknown", "detail":trace(exc)})
'''


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dataset(value: str) -> str:
    labels = {"humaneval": "HumanEval+", "mbpp": "MBPP+"}
    _require(value in labels, f"unknown dataset {value!r}")
    return labels[value]


def _condition(value: str) -> str:
    labels = {"ab1": "Ab1", "ab2g": "Ab2g"}
    _require(value in labels, f"unknown treatment {value!r}")
    return labels[value]


def load_130_cell_manifest(repo_root: pathlib.Path = REPO_ROOT) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read journals only and select exactly ``layers_changed != [] && !final_pass``."""
    rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {"models": {}, "selection": "layers_changed_nonempty AND cumulative_final_pass_false"}
    for model, spec in MODEL_SPECS.items():
        eval_paths = sorted((repo_root / spec["eval_dir"] / "j").glob("*.json"))
        replay_dir = repo_root / spec["replay_dir"] / "j"
        _require(len(eval_paths) == 1084, f"{model}: expected 1084 EvalPlus v2 journals, found {len(eval_paths)}")
        selected: list[dict[str, Any]] = []
        transition_counts: Counter[str] = Counter()
        for eval_path in eval_paths:
            replay_path = replay_dir / eval_path.name
            _require(replay_path.is_file(), f"{model}: replay journal missing for {eval_path.name}")
            evaluated, replay = _read_json(eval_path), _read_json(replay_path)
            layers = replay.get("layers_changed") or []
            final_pass = bool(evaluated["cumulative_final_pass"])
            raw_source, final_source = replay["raw_source"], replay["final_source"]
            _require(_sha256(raw_source) == replay["raw_sha256"] == evaluated["raw_sha256"], f"{eval_path.name}: raw hash drift")
            _require(_sha256(final_source) == replay["final_sha256"] == evaluated["final_sha256"], f"{eval_path.name}: final hash drift")
            if not layers or final_pass:
                continue
            transition = str(evaluated["transition_category"])
            transition_counts[transition] += 1
            selected.append({
                "evidence_label": EVIDENCE_LABEL,
                "model": model,
                "cell_identity": evaluated["cell_identity"],
                "dataset": _dataset(evaluated["dataset"]),
                "task_id": evaluated["task_id"],
                "condition": _condition(evaluated["treatment"]),
                "layers_changed": "|".join(layers),
                "layer_combination": "+".join(sorted(layers)),
                "existing_transition_category": transition,
                "raw_sha256": replay["raw_sha256"],
                "final_sha256": replay["final_sha256"],
                "raw_base_status": evaluated["raw_base_status"],
                "raw_plus_status": evaluated["raw_plus_status"],
                "raw_final_pass": bool(evaluated["raw_final_pass"]),
                "final_base_status": evaluated["cumulative_base_status"],
                "final_plus_status": evaluated["cumulative_plus_status"],
                "final_pass": final_pass,
                "entry_point": replay["entry_point"],
                # Sources remain in memory only and are never written to a manifest.
                "_raw_source": raw_source,
                "_final_source": final_source,
            })
        _require(len(selected) == EXPECTED_COUNTS[model], f"{model}: expected {EXPECTED_COUNTS[model]} transformed final-fail cells, found {len(selected)}")
        audit["models"][model] = {
            "v2_journal_count": len(eval_paths),
            "selected": len(selected),
            "transition_counts": dict(sorted(transition_counts.items())),
            "ablation_counts": dict(sorted(Counter(row["condition"] for row in selected).items())),
            "layer_counts": dict(sorted(Counter(row["layers_changed"] for row in selected).items())),
        }
        rows.extend(selected)
    identities = [(row["model"], row["cell_identity"]) for row in rows]
    _require(len(rows) == EXPECTED_TOTAL, f"expected {EXPECTED_TOTAL} total cells, found {len(rows)}")
    _require(len(set(identities)) == EXPECTED_TOTAL, "duplicate selected cell identity")
    all_transitions = Counter(row["existing_transition_category"] for row in rows)
    _require(all_transitions["modified_but_still_failed"] == 118, "expected 118 modified_but_still_failed cells")
    _require(all_transitions["blocker_removed_but_incorrect"] == 12, "expected 12 blocker_removed_but_incorrect cells")
    audit["combined"] = {
        "selected": len(rows), "duplicates": len(identities) - len(set(identities)),
        "missing": EXPECTED_TOTAL - len(rows), "transition_counts": dict(sorted(all_transitions.items())),
    }
    return rows, audit


def sandbox_preflight() -> dict[str, Any]:
    """Check prerequisites without starting a sandbox or touching a candidate."""
    system = platform.system()
    bwrap = shutil.which("bwrap")
    systemd_run = shutil.which("systemd-run")
    setpriv = shutil.which("setpriv")
    cgroup_v2 = pathlib.Path("/sys/fs/cgroup/cgroup.controllers")
    ready = system == "Linux" and bwrap is not None and systemd_run is not None and setpriv is not None and cgroup_v2.is_file()
    return {
        "required_platform": "Linux",
        "actual_platform": system,
        "bubblewrap": bwrap or "unavailable",
        "systemd_run": systemd_run or "unavailable",
        "setpriv": setpriv or "unavailable",
        "cgroup_v2_controllers": str(cgroup_v2) if cgroup_v2.is_file() else "unavailable",
        "ready_for_candidate_execution": ready,
        "policy": {
            "network": "bubblewrap --unshare-net",
            "root_filesystem": "bubblewrap --ro-bind / /",
            "writable_storage": (
                "only sandbox /tmp tmpfs and per-cell "
                f"{SANDBOX_WORK_DIR} tmpfs (never mkdir on the read-only host root)"
            ),
            "cpu_memory_pids": (
                "systemd-run transient cgroup: CPUQuota=100%, MemoryMax=512M, "
                "MemorySwapMax=0, TasksMax=64"
            ),
            "privileges": "bubblewrap user namespace, --cap-drop ALL, --new-session, then setpriv --no-new-privs",
            "timeout": "parent subprocess timeout per raw/final cell",
            "sandbox_work_dir": SANDBOX_WORK_DIR,
        },
        "limitations": [
            "This runner intentionally refuses execution when these Linux primitives are unavailable; Windows alone is not an equivalent security boundary.",
            "The host must permit unprivileged bubblewrap user namespaces and systemd transient cgroups; preflight checks presence, execution validates command success.",
            "Kernel vulnerabilities and a malicious host administrator are outside this sandbox threat model.",
        ],
    }


def build_bubblewrap_command(*, python_executable: str, worker_path: str, request_path: str) -> list[str]:
    """Build the future per-cell OS-sandbox command; does not execute it.

    Mount order is intentional: bind the host root read-only, replace ``/tmp``
    with a writable tmpfs, then create the per-cell work tmpfs under that
    already-writable ``/tmp``. Never ask bwrap to ``mkdir /work`` on the
    read-only root.
    """
    work = SANDBOX_WORK_DIR
    worker_in_sandbox = f"{work}/worker.py"
    request_in_sandbox = f"{work}/request.json"
    return [
        "systemd-run", "--user", "--scope", "--quiet",
        "-p", "CPUQuota=100%",
        "-p", "MemoryMax=512M",
        "-p", "MemorySwapMax=0",
        "-p", "TasksMax=64",
        "bwrap", "--die-with-parent", "--new-session", "--unshare-all", "--cap-drop", "ALL",
        "--ro-bind", "/", "/",
        "--tmpfs", "/tmp",
        "--tmpfs", work,
        "--proc", "/proc",
        "--dev", "/dev",
        "--chdir", work,
        "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "HOME", work,
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "PYTHONNOUSERSITE", "1",
        "--ro-bind", worker_path, worker_in_sandbox,
        "--ro-bind", request_path, request_in_sandbox,
        "setpriv", "--no-new-privs", "--",
        python_executable, "-I", worker_in_sandbox, request_in_sandbox,
    ]


def _classify_execution(result: dict[str, Any]) -> str:
    """Classify only structured sandbox/EvalPlus evidence, never a generic journal fail."""
    phase = result.get("phase")
    if phase == "timeout":
        return "timeout"
    if phase == "parse":
        return "parse_failure"
    if phase == "entrypoint":
        return "entrypoint_callability_signature_failure"
    if phase in {"module_load", "runtime"}:
        return "runtime_exception"
    if phase != "evalplus_tests":
        return "other_unclassifiable"
    base, plus = result.get("base_status"), result.get("plus_status")
    if base == "pass" and plus == "pass":
        return "pass"
    if base in {"timeout", "timed_out"} or plus in {"timeout", "timed_out"}:
        return "timeout"
    # This category is permitted only because the real EvalPlus base/plus
    # suites completed and emitted their explicit test outcome, not from a
    # persisted generic fail in an old journal.
    if base == "fail" or plus == "fail":
        return "test_assertion_wrong_answer"
    return "other_unclassifiable"


def _execute_one_source(*, row: dict[str, Any], source: str, timeout_seconds: float) -> dict[str, Any]:
    """Future execution path: one source, one cgroup+bubblewrap subprocess."""
    readiness = sandbox_preflight()
    _require(readiness["ready_for_candidate_execution"], "OS sandbox preflight is not satisfied")
    dataset_id = "humaneval" if row["dataset"] == "HumanEval+" else "mbpp"
    with tempfile.TemporaryDirectory(prefix="evalplus_v2_diagnosis_host_") as temp_dir:
        host = pathlib.Path(temp_dir)
        worker_path, request_path = host / "worker.py", host / "request.json"
        worker_path.write_text(WORKER, encoding="utf-8")
        request_path.write_text(json.dumps({"dataset": dataset_id, "task_id": row["task_id"], "entry_point": row["entry_point"], "source": SOURCE_PREFIX + source}), encoding="utf-8")
        command = build_bubblewrap_command(python_executable=sys.executable, worker_path=str(worker_path), request_path=str(request_path))
        try:
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired:
            return {"phase": "timeout", "exception_class": "NONE", "detail": "parent per-cell timeout", "timeout_flag": True}
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or len(lines) != 1:
        return {"phase": "sandbox_or_worker_error", "exception_class": "SandboxProtocolError", "detail": "sandbox returned no unique diagnostic record", "timeout_flag": False}
    try:
        result = json.loads(lines[0])
    except json.JSONDecodeError:
        result = {"phase": "sandbox_or_worker_error", "exception_class": "SandboxProtocolError", "detail": "invalid diagnostic JSON"}
    result["timeout_flag"] = False
    return result


def _public_manifest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if not key.startswith("_")} for row in rows]


def _write_csv(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    _require(bool(rows), "cannot write empty manifest")
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def write_preflight(repo_root: pathlib.Path, output_dir: pathlib.Path) -> dict[str, Any]:
    """Write only a new diagnostics-plan directory.  Never loads a candidate."""
    _require(not output_dir.exists(), f"refusing to overwrite existing output: {output_dir}")
    rows, cohort_audit = load_130_cell_manifest(repo_root)
    output_dir.mkdir(parents=True)
    public_rows = _public_manifest_rows(rows)
    _write_csv(output_dir / "diagnostic_130_cell_manifest.csv", public_rows)
    record = {
        "analysis_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_label": EVIDENCE_LABEL,
        "mode": "preflight_only_no_candidate_parse_import_or_execution",
        "cohort_audit": cohort_audit,
        "sandbox": sandbox_preflight(),
        "execution_contract": {
            "requires_explicit_execute_flag": True,
            "per_cell": "raw and final are separate OS-sandboxed invocations",
            "tests": "actual EvalPlus 0.3.1 HumanEval+/MBPP+ base and plus tests via public check_correctness",
            "no_self_designed_entrypoint_inputs": True,
            "formal_artifacts_modified": False,
            "candidate_sources_written_to_output": False,
        },
        "classification_evidence": {
            "parse_failure": "sandbox worker AST SyntaxError",
            "entrypoint_callability_signature_failure": "real EvalPlus task entry point missing/non-callable/signature mismatch before tests",
            "runtime_exception": "sandbox worker or EvalPlus structured exception class during actual test execution",
            "timeout": "per-cell parent timeout or EvalPlus timeout status",
            "test_assertion_wrong_answer": "actual EvalPlus base/plus test completed with explicit assertion/fail outcome after a callable invocation",
            "pass": "actual EvalPlus base and plus PASS",
            "other_unclassifiable": "no mutually-exclusive structured evidence",
        },
    }
    (output_dir / "preflight_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def diagnose(repo_root: pathlib.Path, output_dir: pathlib.Path, timeout_seconds: float) -> dict[str, Any]:
    """Future reviewed mode: diagnose raw and final separately in fresh sandboxes."""
    _require(timeout_seconds > 0, "timeout must be positive")
    _require(sandbox_preflight()["ready_for_candidate_execution"], "OS sandbox preflight is not satisfied")
    _require(not output_dir.exists(), f"refusing to overwrite existing output: {output_dir}")
    rows, cohort_audit = load_130_cell_manifest(repo_root)
    output_dir.mkdir(parents=True)
    output: list[dict[str, Any]] = []
    for row in rows:
        raw = _execute_one_source(row=row, source=row["_raw_source"], timeout_seconds=timeout_seconds)
        final = _execute_one_source(row=row, source=row["_final_source"], timeout_seconds=timeout_seconds)
        output.append({
            **_public_manifest_rows([row])[0],
            "raw_phase": raw.get("phase"), "raw_exception_class": raw.get("exception_class"),
            "raw_timeout_flag": raw.get("timeout_flag", False), "raw_evidence": raw.get("detail"),
            "raw_category": _classify_execution(raw),
            "final_phase": final.get("phase"), "final_exception_class": final.get("exception_class"),
            "final_timeout_flag": final.get("timeout_flag", False), "final_evidence": final.get("detail"),
            "final_category": _classify_execution(final),
        })
    _require(len(output) == EXPECTED_TOTAL, "diagnostic output count drift")
    _require(len({(r["model"], r["cell_identity"]) for r in output}) == EXPECTED_TOTAL, "duplicate output identity")
    _write_csv(output_dir / "raw_final_diagnostic_ledger.csv", output)
    counts = {model: Counter(row["final_category"] for row in output if row["model"] == model) for model in [*MODEL_SPECS, "ALL"]}
    summary = [{"model": model, "total": sum(counts[model].values()), **{category: counts[model][category] for category in OUTCOME_CATEGORIES}} for model in counts]
    _write_csv(output_dir / "final_category_summary.csv", summary)
    manifest = {"evidence_label": EVIDENCE_LABEL, "mode": "executed_os_sandboxed_actual_evalplus_tests", "cohort_audit": cohort_audit, "sandbox": sandbox_preflight(), "per_cell_timeout_seconds": timeout_seconds, "category_counts": summary}
    (output_dir / "diagnosis_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="write a new data-only 130-cell diagnostic manifest")
    parser.add_argument("--output-dir", required=True, help="must be a new diagnostics directory")
    parser.add_argument("--execute", action="store_true", help="run reviewed raw/final OS-sandbox diagnostics")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args(argv)
    if args.preflight == args.execute:
        parser.error("select exactly one of --preflight or --execute")
    output_dir = pathlib.Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    if args.preflight:
        result = write_preflight(REPO_ROOT, output_dir)
        print(json.dumps({"selected": result["cohort_audit"]["combined"]["selected"], "sandbox_ready": result["sandbox"]["ready_for_candidate_execution"]}, sort_keys=True))
    else:
        result = diagnose(REPO_ROOT, output_dir, args.timeout_seconds)
        print(json.dumps(result["category_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
