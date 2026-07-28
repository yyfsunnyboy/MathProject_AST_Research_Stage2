"""Preflight and fail-closed sandbox diagnostics for MBPP+ external failures.

The data-only roster mode never loads candidate source.  Sandbox execution is
separately gated by a native-Linux bwrap+cgroup safety probe; no host fallback
is permitted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_LABEL = "development_candidate_not_frozen"
EXPECTED_TOTAL = 94
EXPECTED_MODELS = {"qwen3.5:4b": 58, "qwen3.5:9b": 36}
EXPECTED_LAYERS = {"H1": 20, "H2": 47, "H2+H4": 26, "H3": 1}
EXPECTED_STATUS_PAIRS = {("pass", "fail"): 45, ("fail", "pass"): 1, ("fail", "fail"): 48}
EXPECTED_MBPP_TASKS = 378
EXPECTED_DEVELOPMENT_TASKS = 60
EXPECTED_EXTERNAL_TASKS = 318
BWRAP = pathlib.PurePosixPath("/usr/bin/bwrap")
SYSTEMD_RUN = pathlib.PurePosixPath("/usr/bin/systemd-run")
BWRAP_GUEST_OUTPUT = pathlib.PurePosixPath("/tmp/out")
BWRAP_MEMORY_BYTES = 512 * 1024 * 1024
BWRAP_PIDS = 64
BWRAP_CPU_QUOTA = "100%"
EXPECTED_EVALPLUS_VERSION = "0.3.1"
ISOLATED_BOOTSTRAP = (
    "import runpy,sys;"
    "sys.path.insert(0,sys.argv[1]);"
    "sys.argv=[sys.argv[2],sys.argv[3]];"
    "runpy.run_path(sys.argv[0],run_name='__main__')"
)

MODEL_SPECS = {
    "qwen3.5:4b": "qwen35_4b",
    "qwen3.5:9b": "qwen35_9b",
}
GOVERNANCE = pathlib.Path("artifacts/public_benchmark_governance")
DEVELOPMENT_CELLS = GOVERNANCE / "candidate_b_development60_replay_r003_v1/candidate_b_generation_cells.csv"
CONTAMINATION_MANIFEST = GOVERNANCE / "contamination_manifest.csv"
MBPP_DATASET_MANIFEST = pathlib.Path("data/mbpp_plus/dataset_manifest.json")
MBPP_TASKS = pathlib.Path("data/mbpp_plus/tasks.jsonl")
FROZEN_ROSTER = (
    GOVERNANCE
    / "mbpp_external94_h1_h4_modified_final_failures_diagnostic_v1"
    / "preflight_run_001"
    / "diagnostic_94_cell_ledger.csv"
)

LEDGER_FIELDS = (
    "model", "condition", "task_id", "cell_identity", "layers_changed",
    "base_status", "plus_status", "final_source_sha256", "final_phase",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


BWRAP_PROBE_WORKER = r'''
import json, os, pathlib, socket

def cg(name):
    entries = [
        line.split("::", 1)[1]
        for line in pathlib.Path("/proc/self/cgroup").read_text().splitlines()
        if line.startswith("0::")
    ]
    if len(entries) != 1:
        raise RuntimeError("expected exactly one cgroup v2 0:: entry")
    relative = entries[0].lstrip("/")
    controller = pathlib.Path("/sys/fs/cgroup") / relative / name
    if not controller.is_file():
        raise FileNotFoundError(str(controller))
    return controller.read_text().strip()

network_blocked = False
try:
    sock = socket.socket(); sock.settimeout(1); sock.connect(("1.1.1.1", 53))
except OSError:
    network_blocked = True
finally:
    try: sock.close()
    except NameError: pass
project_write_blocked = False
try:
    open(os.environ["STAGE2_PROJECT_PROBE"], "w").write("must fail")
except OSError:
    project_write_blocked = True
result = {
    "marker": "BWRAP_PROBE_OK",
    "uid": os.getuid(),
    "network_blocked": network_blocked,
    "project_write_blocked": project_write_blocked,
    "memory_max": cg("memory.max"),
    "pids_max": cg("pids.max"),
    "cpu_max": cg("cpu.max"),
}
pathlib.Path("/tmp/out/probe_result.json").write_text(json.dumps(result, sort_keys=True))
print(json.dumps({"marker": "BWRAP_PROBE_OK"}, sort_keys=True), flush=True)
'''

BWRAP_TIMEOUT_WORKER = "import time; time.sleep(60)\n"

CANDIDATE_WORKER = r'''
import ast, contextlib, importlib.metadata, io, json, os, pathlib, traceback

request = json.loads(pathlib.Path("/tmp/out/request.json").read_text())
source = request["source"]

def safe_exception(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    candidate = next((f for f in reversed(frames) if f.filename == "<candidate>"), None)
    return {
        "exception_class": type(exc).__name__,
        "exception_summary": (
            "candidate_line=%s;function=%s"
            % (candidate.lineno, candidate.name)
            if candidate else "candidate_frame=unavailable"
        ),
    }

def finish(payload):
    payload.setdefault("sandbox_started", True)
    payload.setdefault("sandbox_completed", True)
    target = pathlib.Path("/tmp/out/result.json")
    temporary = pathlib.Path("/tmp/out/result.json.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True))
    os.replace(temporary, target)

try:
    try:
        tree = ast.parse(source, filename="<candidate>")
        code = compile(tree, "<candidate>", "exec")
    except (SyntaxError, ValueError, TypeError) as exc:
        finish({"phase": "parse_or_compile", "parse_status": "fail", "compile_status": "fail", **safe_exception(exc)})
        raise SystemExit(0)
    namespace = {"__name__": "__external94_diagnostic__", "__file__": "<candidate>"}
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(code, namespace, namespace)
    except BaseException as exc:
        finish({"phase": "module_load", "parse_status": "pass", "compile_status": "pass", "runtime_status": "fail", **safe_exception(exc)})
        raise SystemExit(0)
    entry = namespace.get(request["entry_point"])
    if not callable(entry):
        finish({"phase": "entry_point", "parse_status": "pass", "compile_status": "pass", "runtime_status": "pass", "entry_point_status": "missing_or_noncallable", "exception_class": "NONE", "exception_summary": "NONE"})
        raise SystemExit(0)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from evalplus.data import get_mbpp_plus, get_mbpp_plus_hash
            from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
            from evalplus.evaluate import check_correctness, get_groundtruth
            tasks = get_mbpp_plus()
            expected = get_groundtruth(tasks, get_mbpp_plus_hash(), MBPP_OUTPUT_NOT_NONE_TASKS)
            problem = tasks[request["task_id"]]
            if problem["entry_point"] != request["entry_point"]:
                raise RuntimeError("entry_point_contract_mismatch")
            result = check_correctness("mbpp", 0, problem, source, expected[request["task_id"]], base_only=False, fast_check=True)
        finish({
            "phase": "evalplus_tests", "parse_status": "pass", "compile_status": "pass",
            "runtime_status": "pass", "entry_point_status": "callable",
            "base_status": str(result["base"][0]), "plus_status": str(result["plus"][0]),
            "evalplus_version": importlib.metadata.version("evalplus"),
            "exception_class": "NONE", "exception_summary": "NONE",
        })
    except BaseException as exc:
        finish({"phase": "diagnostic_infrastructure", "parse_status": "pass", "compile_status": "pass", "runtime_status": "pass", "entry_point_status": "callable", **safe_exception(exc)})
except SystemExit:
    raise
except BaseException as exc:
    finish({"phase": "diagnostic_infrastructure", **safe_exception(exc)})
'''

TERMINAL_CLASSIFICATIONS = (
    "executable_and_base_plus_pass",
    "executable_but_base_fail",
    "executable_base_pass_plus_fail",
    "parse_or_compile_failure",
    "import_or_runtime_failure",
    "missing_entry_point",
    "timeout",
    "sandbox_failure",
    "diagnostic_infrastructure_failure",
)


def build_bwrap_command(
    *,
    host_output_dir: pathlib.Path,
    worker_name: str,
    request_name: str,
    evalplus_site_packages: pathlib.Path | None = None,
) -> list[str]:
    """Native-Linux bwrap command; there is deliberately no host fallback."""
    command = [
        str(SYSTEMD_RUN), "--user", "--scope", "--quiet",
        "-p", "CPUQuota=100%", "-p", "MemoryMax=512M",
        "-p", "MemorySwapMax=0", "-p", "TasksMax=64",
        str(BWRAP), "--die-with-parent", "--new-session",
        "--unshare-user", "--unshare-ipc", "--unshare-pid",
        "--unshare-net", "--unshare-uts",
        "--uid", "65534", "--gid", "65534", "--cap-drop", "ALL",
        "--ro-bind", "/", "/",
        "--tmpfs", "/tmp",
        "--dir", str(BWRAP_GUEST_OUTPUT),
        "--bind", str(host_output_dir), str(BWRAP_GUEST_OUTPUT),
        "--chdir", str(BWRAP_GUEST_OUTPUT), "--proc", "/proc", "--dev", "/dev",
        "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "STAGE2_PROJECT_PROBE", str(REPO_ROOT / ".bwrap_write_must_fail"),
    ]
    if evalplus_site_packages is None:
        command.extend([
            sys.executable, "-I", "-B",
            str(BWRAP_GUEST_OUTPUT / worker_name),
            str(BWRAP_GUEST_OUTPUT / request_name),
        ])
    else:
        command.extend([
            sys.executable, "-I", "-B", "-c", ISOLATED_BOOTSTRAP,
            str(evalplus_site_packages),
            str(BWRAP_GUEST_OUTPUT / worker_name),
            str(BWRAP_GUEST_OUTPUT / request_name),
        ])
    return command


def resolve_evalplus_site_packages() -> pathlib.Path:
    import evalplus

    version = importlib.metadata.version("evalplus")
    _require(version == EXPECTED_EVALPLUS_VERSION, f"EvalPlus version mismatch: {version}")
    site_packages = pathlib.Path(evalplus.__file__).resolve().parents[1]
    _require(site_packages.is_dir(), "EvalPlus site-packages unavailable")
    return site_packages


def bwrap_preflight(*, timeout_seconds: float) -> dict[str, Any]:
    """Validate all safety gates with fixed harmless workers only."""
    if (
        os.name != "posix"
        or not pathlib.Path(BWRAP).is_file()
        or not pathlib.Path(SYSTEMD_RUN).is_file()
    ):
        return {"status": "BLOCKED", "reason": "native_linux_bwrap_or_systemd_run_unavailable"}
    with tempfile.TemporaryDirectory(prefix="external94_bwrap_probe_") as temp_dir:
        root = pathlib.Path(temp_dir)
        root.chmod(0o777)
        request = root / "request.json"
        request.write_text("{}", encoding="utf-8")
        probe = root / "probe.py"
        probe.write_text(BWRAP_PROBE_WORKER, encoding="utf-8")
        command = build_bwrap_command(
            host_output_dir=root,
            worker_name=probe.name,
            request_name=request.name,
        )
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired:
            return {"status": "BLOCKED", "reason": "security_probe_wall_timeout"}
        lines = [line for line in run.stdout.splitlines() if line.strip()]
        if run.returncode != 0 or len(lines) != 1:
            return {"status": "BLOCKED", "reason": "security_probe_protocol", "return_code": run.returncode, "stdout": run.stdout[-2048:], "stderr": run.stderr[-2048:]}
        result_path = root / "probe_result.json"
        if not result_path.is_file():
            return {"status": "BLOCKED", "reason": "security_probe_result_missing"}
        try:
            evidence = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "BLOCKED", "reason": "security_probe_invalid_json", "error": str(exc)}
        cpu_parts = evidence.get("cpu_max", "").split()
        cpu_limited = len(cpu_parts) == 2 and cpu_parts[0] != "max"
        checks = {
            "marker": evidence.get("marker") == "BWRAP_PROBE_OK",
            "non_root": evidence.get("uid") not in (None, 0),
            "network_isolated": evidence.get("network_blocked") is True,
            "project_read_only": evidence.get("project_write_blocked") is True,
            "memory_limited": evidence.get("memory_max") == str(BWRAP_MEMORY_BYTES),
            "pids_limited": evidence.get("pids_max") == str(BWRAP_PIDS),
            "cpu_limited": cpu_limited,
        }
        if not all(checks.values()):
            return {"status": "BLOCKED", "reason": "security_assertion_failed", "checks": checks, "evidence": evidence}
        sleeper = root / "timeout.py"
        sleeper.write_text(BWRAP_TIMEOUT_WORKER, encoding="utf-8")
        try:
            subprocess.run(
                build_bwrap_command(
                    host_output_dir=root,
                    worker_name=sleeper.name,
                    request_name=request.name,
                ),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            checks["wall_time_enforced"] = True
        else:
            checks["wall_time_enforced"] = False
        if not checks["wall_time_enforced"]:
            return {"status": "BLOCKED", "reason": "wall_time_not_enforced", "checks": checks}
        return {"status": "READY", "checks": checks, "evidence": evidence}


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_frozen_final_sources(
    repo_root: pathlib.Path = REPO_ROOT,
    *,
    roster_path: pathlib.Path | None = None,
    source_field: str = "final_source",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load, but never execute, the exact frozen 94 rows by cell identity."""
    roster_file = roster_path or (repo_root / FROZEN_ROSTER)
    roster = _read_csv(roster_file)
    _require(len(roster) == EXPECTED_TOTAL, f"frozen roster must contain 94 rows, found {len(roster)}")
    keys = [(row["model"], row["cell_identity"]) for row in roster]
    _require(len(set(keys)) == EXPECTED_TOTAL, "frozen roster has duplicate model/cell_identity")
    loaded: list[dict[str, Any]] = []
    for row_number, row in enumerate(roster, start=2):
        model = row["model"]
        _require(model in MODEL_SPECS, f"row {row_number}: unknown model")
        short = MODEL_SPECS[model]
        identity = row["cell_identity"]
        replay_path = repo_root / GOVERNANCE / f"{short}_h1_h2_h3_h4_full_replay_v1/j" / f"{identity}.json"
        eval_path = repo_root / GOVERNANCE / f"{short}_h1_h2_h3_h4_full_evalplus_v2/j" / f"{identity}.json"
        _require(replay_path.is_file() and eval_path.is_file(), f"row {row_number}: source journal missing")
        replay, evaluated = _read_json(replay_path), _read_json(eval_path)
        expected_condition = {"Ab1": "ab1", "Ab2g": "ab2g"}.get(row["condition"])
        _require(expected_condition is not None, f"row {row_number}: invalid frozen condition")
        _require(replay["cell_identity"] == evaluated["cell_identity"] == identity, f"row {row_number}: identity mismatch")
        _require(replay["model_tag"] == evaluated["model_tag"] == model, f"row {row_number}: model mismatch")
        _require(replay["treatment"] == evaluated["treatment"] == expected_condition, f"row {row_number}: condition mismatch")
        _require(replay["task_id"] == evaluated["task_id"] == row["task_id"], f"row {row_number}: task mismatch")
        _require(replay["dataset"] == evaluated["dataset"] == "mbpp", f"row {row_number}: non-MBPP dataset")
        layers = replay.get("layers_changed") or []
        _require(bool(layers) and evaluated.get("layers_changed") == layers, f"row {row_number}: not modified")
        _require("+".join(layers) == row["layers_changed"], f"row {row_number}: layer mismatch")
        _require(evaluated.get("cumulative_final_pass") is False, f"row {row_number}: final is not failure")
        _require(source_field == "final_source", f"row {row_number}: source field must be final_source")
        source = replay.get(source_field)
        _require(isinstance(source, str), f"row {row_number}: {source_field} missing")
        digest = _sha256_text(source)
        expected_digest = row["final_source_sha256"]
        _require(digest == replay["final_sha256"] == evaluated["final_sha256"] == expected_digest, f"row {row_number}: final source hash mismatch")
        loaded.append({
            **row,
            "source_journal_path": str(replay_path.relative_to(repo_root)),
            "source_row_key": f"{model}|{identity}",
            "source_field": "final_source",
            "source_sha256": digest,
            "entry_point": replay["entry_point"],
            "_final_source": source,
        })
    _require(len(loaded) == EXPECTED_TOTAL, "frozen loader missing rows")
    audit = {
        "status": "READY",
        "total": len(loaded),
        "unique_model_cell_identity": len(set(keys)),
        "missing": EXPECTED_TOTAL - len(loaded),
        "duplicates": len(keys) - len(set(keys)),
        "datasets": {"mbpp": len(loaded)},
        "models": dict(sorted(Counter(row["model"] for row in loaded).items())),
        "source_field": "final_source",
        "hash_verified": len(loaded),
        "candidate_source_emitted": False,
    }
    return loaded, audit


def classify_execution(result: dict[str, Any]) -> str:
    if result.get("timeout"):
        return "timeout"
    if result.get("phase") == "sandbox_failure":
        return "sandbox_failure"
    if result.get("phase") == "parse_or_compile":
        return "parse_or_compile_failure"
    if result.get("phase") == "module_load":
        return "import_or_runtime_failure"
    if result.get("phase") == "entry_point":
        return "missing_entry_point"
    if result.get("phase") != "evalplus_tests":
        return "diagnostic_infrastructure_failure"
    base, plus = result.get("base_status"), result.get("plus_status")
    if base == "pass" and plus == "pass":
        return "executable_and_base_plus_pass"
    if base == "pass" and plus == "fail":
        return "executable_base_pass_plus_fail"
    if base == "fail":
        return "executable_but_base_fail"
    if base in {"timeout", "timed_out"} or plus in {"timeout", "timed_out"}:
        return "timeout"
    return "diagnostic_infrastructure_failure"


def execute_one_frozen_cell(
    row: dict[str, Any], *, timeout_seconds: float, evalplus_site_packages: pathlib.Path
) -> dict[str, Any]:
    """Pass source to one sandbox; never compile/import/execute it on the host."""
    with tempfile.TemporaryDirectory(prefix="external94_cell_") as temp_dir:
        root = pathlib.Path(temp_dir)
        root.chmod(0o777)
        worker = root / "worker.py"
        request = root / "request.json"
        worker.write_text(CANDIDATE_WORKER, encoding="utf-8")
        request.write_text(json.dumps({
            "source": row["_final_source"],
            "task_id": row["task_id"],
            "entry_point": row["entry_point"],
        }), encoding="utf-8")
        try:
            run = subprocess.run(
                build_bwrap_command(
                    host_output_dir=root,
                    worker_name=worker.name,
                    request_name=request.name,
                    evalplus_site_packages=evalplus_site_packages,
                ),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "phase": "timeout", "sandbox_started": True,
                "sandbox_completed": False, "timeout": True,
                "exception_class": "TimeoutExpired",
                "exception_summary": "parent_wall_time_exceeded",
            }
        result_path = root / "result.json"
        if run.returncode != 0 or not result_path.is_file():
            return {
                "phase": "sandbox_failure", "sandbox_started": True,
                "sandbox_completed": False, "timeout": False,
                "exception_class": "SandboxProcessError",
                "exception_summary": f"return_code={run.returncode};stderr_bytes={len(run.stderr.encode('utf-8', 'replace'))}",
            }
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "phase": "diagnostic_infrastructure",
                "sandbox_started": True, "sandbox_completed": True,
                "timeout": False, "exception_class": "InvalidWorkerJSON",
                "exception_summary": "result_json_decode_failed",
            }
        result["timeout"] = False
        return result


def _journal_name(row: dict[str, Any]) -> str:
    return hashlib.sha256(row["source_row_key"].encode("utf-8")).hexdigest() + ".json"


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _public_cell_record(row: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    classification = classify_execution(result)
    _require(classification in TERMINAL_CLASSIFICATIONS, "non-terminal classification")
    return {
        "model": row["model"], "cell_identity": row["cell_identity"],
        "condition": row["condition"], "task_id": row["task_id"],
        "source_journal_path": row["source_journal_path"],
        "source_row_key": row["source_row_key"],
        "source_field": row["source_field"], "source_sha256": row["source_sha256"],
        "sandbox_started": bool(result.get("sandbox_started")),
        "sandbox_completed": bool(result.get("sandbox_completed")),
        "parse_status": result.get("parse_status", "not_reached"),
        "compile_status": result.get("compile_status", "not_reached"),
        "runtime_status": result.get("runtime_status", "not_reached"),
        "entry_point_status": result.get("entry_point_status", "not_reached"),
        "base_status": result.get("base_status", "not_reached"),
        "plus_status": result.get("plus_status", "not_reached"),
        "timeout": bool(result.get("timeout")),
        "exception_class": result.get("exception_class", "NONE"),
        "exception_summary": result.get("exception_summary", "NONE"),
        "final_execution_classification": classification,
        "terminal": True,
    }


def run_execution_loop(
    loaded: list[dict[str, Any]],
    *,
    output_dir: pathlib.Path,
    timeout_seconds: float,
    cell_executor: Any = execute_one_frozen_cell,
    evalplus_site_packages: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Execute/resume 94 independently sandboxed cells and finalize atomically."""
    _require(len(loaded) == EXPECTED_TOTAL, "execution requires exactly 94 loaded cells")
    output_dir.mkdir(parents=True, exist_ok=True)
    journal_dir = output_dir / "j"
    journal_dir.mkdir(exist_ok=True)
    expected = {_journal_name(row): row for row in loaded}
    existing_paths = list(journal_dir.glob("*.json"))
    _require(len(existing_paths) == len({path.name for path in existing_paths}), "duplicate journal filename")
    _require(set(path.name for path in existing_paths).issubset(expected), "unexpected journal present")
    completed_by_key: dict[str, dict[str, Any]] = {}
    for path in existing_paths:
        record = _read_json(path)
        row = expected[path.name]
        _require(record.get("source_row_key") == row["source_row_key"], "journal row key mismatch")
        _require(record.get("source_sha256") == row["source_sha256"], "journal source hash mismatch")
        if record.get("terminal") is True:
            _require(record["source_row_key"] not in completed_by_key, "duplicate completed journal")
            completed_by_key[record["source_row_key"]] = record
    site_packages = evalplus_site_packages
    for row in loaded:
        if row["source_row_key"] in completed_by_key:
            continue
        if site_packages is None:
            site_packages = resolve_evalplus_site_packages()
        result = cell_executor(
            row, timeout_seconds=timeout_seconds,
            evalplus_site_packages=site_packages,
        )
        record = _public_cell_record(row, result)
        _atomic_json(journal_dir / _journal_name(row), record)
        completed_by_key[row["source_row_key"]] = record
    _require(len(completed_by_key) == EXPECTED_TOTAL, "cannot finalize before 94 terminal journals")
    records = [completed_by_key[row["source_row_key"]] for row in loaded]
    counts = Counter(row["final_execution_classification"] for row in records)
    manifest = {
        "status": "CANDIDATE_EXECUTION_COMPLETED",
        "total": EXPECTED_TOTAL,
        "source_records": [{
            key: row[key] for key in (
                "model", "condition", "task_id", "cell_identity",
                "source_journal_path", "source_row_key", "source_field",
                "source_sha256",
            )
        } for row in records],
    }
    jsonl = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in records) + "\n"
    jsonl_tmp = output_dir / "per_cell_diagnostics.jsonl.tmp"
    jsonl_tmp.write_text(jsonl, encoding="utf-8")
    os.replace(jsonl_tmp, output_dir / "per_cell_diagnostics.jsonl")
    _atomic_json(output_dir / "execution_manifest.json", manifest)
    _atomic_json(output_dir / "aggregate_summary.json", {
        "total": EXPECTED_TOTAL,
        "classification_counts": {
            category: counts[category] for category in TERMINAL_CLASSIFICATIONS
        },
    })
    completion = {
        "status": "CANDIDATE_EXECUTION_COMPLETED",
        "terminal_journals": EXPECTED_TOTAL,
        "source_hashes_verified": EXPECTED_TOTAL,
    }
    _atomic_json(output_dir / "execution_completion.json", completion)
    return completion


def _journal_dirs(repo_root: pathlib.Path, short_model: str) -> tuple[pathlib.Path, pathlib.Path]:
    base = repo_root / GOVERNANCE
    return (
        base / f"{short_model}_h1_h2_h3_h4_full_evalplus_v2/j",
        base / f"{short_model}_h1_h2_h3_h4_full_replay_v1/j",
    )


def load_external_task_scope(repo_root: pathlib.Path = REPO_ROOT) -> tuple[set[str], dict[str, dict[str, str]], dict[str, Any]]:
    """Return the 318 MBPP+ task IDs after excluding exactly development60."""
    dataset_manifest = _read_json(repo_root / MBPP_DATASET_MANIFEST)
    _require(dataset_manifest.get("dataset_name") == "MBPP+", "dataset manifest is not MBPP+")
    _require(dataset_manifest.get("task_count") == EXPECTED_MBPP_TASKS, "MBPP+ task count drift")

    task_ids = {
        json.loads(line)["task_id"]
        for line in (repo_root / MBPP_TASKS).read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    _require(len(task_ids) == EXPECTED_MBPP_TASKS, "MBPP+ task file count drift")
    _require(all(task_id.startswith("Mbpp/") for task_id in task_ids), "non-MBPP task in MBPP+ task file")

    development_rows = _read_csv(repo_root / DEVELOPMENT_CELLS)
    development_ids = {row["task_id"] for row in development_rows}
    _require(len(development_ids) == EXPECTED_DEVELOPMENT_TASKS, "development60 task count drift")
    _require(development_ids.issubset(task_ids), "development task absent from MBPP+ task file")

    manifest_rows = _read_csv(repo_root / CONTAMINATION_MANIFEST)
    mbpp_manifest = {row["task_id"]: row for row in manifest_rows if row["dataset"] == "MBPP+"}
    _require(len(mbpp_manifest) == EXPECTED_MBPP_TASKS, "contamination manifest MBPP+ count drift")
    _require(set(mbpp_manifest) == task_ids, "contamination manifest and MBPP+ task file disagree")
    _require(development_ids.issubset(mbpp_manifest), "development task absent from contamination manifest")

    external_ids = task_ids - development_ids
    _require(len(external_ids) == EXPECTED_EXTERNAL_TASKS, "MBPP+ external318 task count drift")
    return external_ids, mbpp_manifest, {
        "mbpp_task_count": len(task_ids),
        "development_task_count": len(development_ids),
        "external_task_count": len(external_ids),
        "development_contamination_statuses": dict(sorted(Counter(mbpp_manifest[x]["contamination_status"] for x in development_ids).items())),
    }


def build_roster(repo_root: pathlib.Path = REPO_ROOT) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Rebuild the exact external94 roster from corrected ledgers and replays."""
    external_ids, manifest, scope_audit = load_external_task_scope(repo_root)
    rows: list[dict[str, str]] = []
    journal_counts: dict[str, int] = {}
    for model, short_model in MODEL_SPECS.items():
        eval_dir, replay_dir = _journal_dirs(repo_root, short_model)
        eval_paths = sorted(eval_dir.glob("*.json"))
        _require(len(eval_paths) == 1084, f"{model}: corrected ledger journal count drift")
        journal_counts[model] = len(eval_paths)
        for eval_path in eval_paths:
            replay_path = replay_dir / eval_path.name
            _require(replay_path.is_file(), f"{model}: missing H1-H4 replay journal {eval_path.name}")
            corrected = _read_json(eval_path)
            replay = _read_json(replay_path)
            _require(corrected["dataset"] == replay["dataset"], f"{eval_path.name}: dataset mismatch")
            _require(corrected["task_id"] == replay["task_id"], f"{eval_path.name}: task mismatch")
            _require(corrected["cell_identity"] == replay["cell_identity"], f"{eval_path.name}: identity mismatch")
            _require(corrected["final_sha256"] == replay["final_sha256"], f"{eval_path.name}: final hash mismatch")
            _require(corrected["layers_changed"] == replay["layers_changed"], f"{eval_path.name}: layer mismatch")
            if corrected["dataset"] != "mbpp" or corrected["task_id"] not in external_ids:
                continue
            layers = corrected["layers_changed"]
            if not layers or bool(corrected["cumulative_final_pass"]):
                continue
            base_status = str(corrected["cumulative_base_status"])
            plus_status = str(corrected["cumulative_plus_status"])
            _require((base_status, plus_status) in EXPECTED_STATUS_PAIRS, f"{eval_path.name}: unexpected final status pair")
            _require(corrected["task_id"] in manifest, f"{eval_path.name}: absent MBPP+ contamination record")
            rows.append({
                "model": model,
                "condition": {"ab1": "Ab1", "ab2g": "Ab2g"}[corrected["treatment"]],
                "task_id": corrected["task_id"],
                "cell_identity": corrected["cell_identity"],
                "layers_changed": "+".join(layers),
                "base_status": base_status,
                "plus_status": plus_status,
                "final_source_sha256": corrected["final_sha256"],
                "final_phase": "preflight_only_no_candidate_load_or_execution",
            })

    rows.sort(key=lambda row: (row["model"], row["cell_identity"]))
    identities = [(row["model"], row["cell_identity"]) for row in rows]
    model_counts = Counter(row["model"] for row in rows)
    layer_counts = Counter(row["layers_changed"] for row in rows)
    status_counts = Counter((row["base_status"], row["plus_status"]) for row in rows)
    _require(len(rows) == EXPECTED_TOTAL, f"external94 total drift: {len(rows)}")
    _require(dict(model_counts) == EXPECTED_MODELS, f"external94 model counts drift: {dict(model_counts)}")
    _require(dict(layer_counts) == EXPECTED_LAYERS, f"external94 layer counts drift: {dict(layer_counts)}")
    _require(dict(status_counts) == EXPECTED_STATUS_PAIRS, f"external94 status counts drift: {dict(status_counts)}")
    _require(len(set(identities)) == EXPECTED_TOTAL, "external94 cell identity is not unique per model")
    return rows, {
        "scope": scope_audit,
        "corrected_ledger_journal_counts": journal_counts,
        "total": len(rows),
        "model_counts": dict(sorted(model_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "status_pair_counts": {
            "base_PASS_plus_FAIL": status_counts[("pass", "fail")],
            "base_FAIL_plus_PASS": status_counts[("fail", "pass")],
            "base_FAIL_plus_FAIL": status_counts[("fail", "fail")],
        },
        "unique_model_cell_identity_count": len(set(identities)),
    }


def write_preflight(output_dir: pathlib.Path, rows: list[dict[str, str]], audit: dict[str, Any]) -> None:
    _require(not output_dir.exists(), f"output directory already exists: {output_dir}")
    staging = output_dir.with_name(output_dir.name + ".staging")
    _require(not staging.exists(), f"staging directory already exists: {staging}")
    staging.mkdir(parents=True)
    try:
        with (staging / "diagnostic_94_cell_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        manifest = {
            "analysis_id": "mbpp_external94_h1_h4_modified_final_failures_diagnostic_v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "preflight_only_no_candidate_load_or_execution",
            "candidate_source_policy": "No candidate source is compiled, imported, evaluated, or emitted.",
            "source_inputs": {
                "corrected_ledgers": [str(GOVERNANCE / f"{short}_h1_h2_h3_h4_full_evalplus_v2/j") for short in MODEL_SPECS.values()],
                "h1_h4_replay_journals": [str(GOVERNANCE / f"{short}_h1_h2_h3_h4_full_replay_v1/j") for short in MODEL_SPECS.values()],
                "contamination_manifest": str(CONTAMINATION_MANIFEST),
                "development60_roster": str(DEVELOPMENT_CELLS),
            },
            "assertions": audit,
        }
        (staging / "diagnostic_summary.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (staging / "preflight_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        staging.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def write_loader_preflight(
    output_dir: pathlib.Path, loaded: list[dict[str, Any]], audit: dict[str, Any]
) -> None:
    """Write new provenance-only execution preparation; never emit source text."""
    _require(not output_dir.exists(), f"output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    records = [
        {
            "model": row["model"],
            "condition": row["condition"],
            "task_id": row["task_id"],
            "cell_identity": row["cell_identity"],
            "source_journal_path": row["source_journal_path"],
            "source_row_key": row["source_row_key"],
            "source_field": row["source_field"],
            "source_sha256": row["source_sha256"],
        }
        for row in loaded
    ]
    manifest = {
        "analysis_id": "mbpp_external94_frozen_final_source_loader_preflight_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "data_only_loader_preflight_no_candidate_execution",
        "frozen_roster_path": str(FROZEN_ROSTER),
        "audit": audit,
        "source_records": records,
    }
    (output_dir / "execution_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--loader-preflight", action="store_true", help="validate frozen 94 final_source mappings without execution")
    mode.add_argument("--bwrap-probe", action="store_true", help="run fixed harmless native-Linux bwrap safety probe")
    mode.add_argument("--execute", action="store_true", help="execute only after the complete bwrap safety gate")
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()
    _require(args.timeout_seconds > 0, "timeout must be positive")
    if args.bwrap_probe:
        result = bwrap_preflight(timeout_seconds=args.timeout_seconds)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        if result["status"] != "READY":
            raise SystemExit(2)
        return
    if args.loader_preflight:
        loaded, audit = load_frozen_final_sources()
        write_loader_preflight(args.output_dir, loaded, audit)
        print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
        return
    if args.execute:
        result = bwrap_preflight(timeout_seconds=args.timeout_seconds)
        if result["status"] != "READY":
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            raise SystemExit(2)
        loaded, audit = load_frozen_final_sources()
        completion = run_execution_loop(
            loaded,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps({
            **completion,
            "safety_probe": result,
            "loader": audit,
        }, ensure_ascii=False, sort_keys=True))
        return
    rows, audit = build_roster()
    write_preflight(args.output_dir, rows, audit)


if __name__ == "__main__":
    main()
