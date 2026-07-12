"""
Fail-closed bridge to the official EvalPlus (HumanEval+/MBPP+) CLI.

Scope
-----
Evaluates exactly one completion JSONL file (one treatment: Ab1, Ab2g,
Ab3-Core, or Ab3-Full — never mixed) against the *official* EvalPlus
dataset and test harness. This module never:

  - rewrites HumanEval+/MBPP+ tests itself
  - converts official tests into this repo's own TestSuite
    (agent_tools.finals_rebuild.test_contract)
  - substitutes execution_evaluator.py/test_evaluator.py for the official
    harness, or treats bare execution success as a test pass
  - fabricates pass@1 — every pass@1 value in the output comes directly
    from the official EvalPlus result file
  - calls a model, calls Core/Spec adapters, or generates completions
  - falls back to the original (non-"+") HumanEval/MBPP dataset, or to a
    local HumanEval.jsonl.gz snapshot, if the official EvalPlus dataset
    loader is unavailable
  - evaluates a caller-selected task_id subset: EvalPlus 0.3.1's
    evaluate() hard-asserts len(completion_id) == len(problems) and
    exposes no CLI flag or public API for partial-benchmark evaluation
    (mini/noextreme only pick a fixed reduced dataset, not arbitrary
    task_ids), so --task-ids fails closed rather than attempting one

Every failure mode below is fail-closed: non-zero process exit, no
`evalplus_summary.json`, and (where reached) a `failure.json` explicitly
stamped with the failing stage's status.

Platform boundary
------------------
EvalPlus's official test harness relies on POSIX process/resource-limit
semantics this bridge does not attempt to replicate on native Windows.
`is_native_windows()` decides this by *Python runtime* (`os.name`,
`sys.platform`), never by inspecting the project path — a `/mnt/c/...`
path under WSL does not make the running interpreter "Windows".

Schema caveat
-------------
The official EvalPlus CLI (`python -m evalplus.evaluate`) writes a result
JSON containing an `"eval"` mapping from task_id to a list of per-sample
outcome dicts. This module's `_extract_task_outcome()` reads that mapping
looking for one of `plus_status`/`base_status`/`status` on the first
entry (n=1, one completion per task). That field-name assumption is
exercised here only against mocked fixtures (evalplus is not installed in
this Windows-only development environment, and could not be invoked here
regardless — see the platform boundary above); it MUST be re-verified
against a real `evalplus`-produced result file the first time this bridge
is run for real in WSL/Linux, before its pass@1 output is trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

DEFAULT_TIMEOUT_SECONDS = 1800.0
ALLOWED_BENCHMARKS = ("humaneval", "mbpp")

_ENGINE = "evalplus_cli_subprocess"

# stage -> manifest/failure "status" value.
_STAGE_STATUS: Dict[str, str] = {
    "platform": "failed_preflight",
    "task_ids": "failed_preflight",
    "samples": "failed_preflight",
    "task_filter": "failed_preflight",
    "evalplus_import": "failed_preflight",
    "dataset_load": "failed_preflight",
    "dataset_task_id_check": "failed_preflight",
    "subprocess": "failed_execution",
    "result_locate": "failed_execution",
    "result_parse": "failed_execution",
}

_WINDOWS_GUARD_MESSAGE = (
    "EvalPlus evaluation is not supported in this native Windows execution path.\n"
    "Run this command inside WSL or Linux.\n"
    "Evaluation aborted without producing benchmark scores."
)

_TASK_IDS_UNSUPPORTED_MESSAGE = (
    "EvalPlus 0.3.1 requires complete benchmark coverage and does not expose "
    "a supported task-subset evaluation path. Partial evaluation was aborted "
    "without producing scores."
)


class EvalPlusBridgeError(Exception):
    """Raised on any fail-closed invariant violation. *stage* selects the
    recorded status ("failed_preflight" vs "failed_execution")."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.status = _STAGE_STATUS[stage]


# ---------------------------------------------------------------------------
# Platform guard
# ---------------------------------------------------------------------------


def is_native_windows() -> bool:
    """True only for a native Windows Python runtime — decided from
    os.name/sys.platform, never from the project's filesystem path (a
    /mnt/c/... path under WSL must not be misread as Windows)."""
    return os.name == "nt" or sys.platform.startswith("win")


def run_windows_preflight_guard() -> None:
    if is_native_windows():
        raise EvalPlusBridgeError("platform", _WINDOWS_GUARD_MESSAGE)


# ---------------------------------------------------------------------------
# --task-ids parsing / filtering
# ---------------------------------------------------------------------------


def parse_task_ids(value: Optional[str]) -> Optional[List[str]]:
    """Parse a comma-separated --task-ids value.

    None (flag omitted) means "no filter, run all samples" and returns
    None. An explicitly empty string is fail-closed (raises), since an
    empty *value* is never the same thing as "not provided". Whitespace
    around each entry is stripped; duplicates are removed while
    preserving first-occurrence order; no entry is ever rewritten.
    """
    if value is None:
        return None
    if value.strip() == "":
        raise EvalPlusBridgeError("task_ids", "--task-ids must not be an empty string")

    seen: set[str] = set()
    result: List[str] = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            raise EvalPlusBridgeError(
                "task_ids", f"--task-ids contains an empty entry: {value!r}"
            )
        if part not in seen:
            seen.add(part)
            result.append(part)
    return result


def filter_samples_by_task_ids(
    samples: Sequence[Dict[str, Any]],
    task_ids: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Return the subset of *samples* whose task_id is in *task_ids*,
    preserving *samples* order.

    task_ids=None means "no filter" (returns all samples). Fails closed if
    any requested task_id has no matching sample, or if the filtered
    result would be empty.
    """
    if task_ids is None:
        return list(samples)

    available = {s["task_id"] for s in samples}
    missing = [t for t in task_ids if t not in available]
    if missing:
        raise EvalPlusBridgeError(
            "task_filter",
            f"--task-ids requested task_id(s) not present in samples: {missing}",
        )

    wanted = set(task_ids)
    filtered = [s for s in samples if s["task_id"] in wanted]
    if not filtered:
        raise EvalPlusBridgeError(
            "task_filter", "--task-ids filtering produced zero samples"
        )
    return filtered


# ---------------------------------------------------------------------------
# Sample loading
# ---------------------------------------------------------------------------


def load_completion_samples(path: pathlib.Path) -> List[Dict[str, str]]:
    """Load a {"task_id": ..., "completion": ...} JSONL file, verbatim.

    UTF-8; each line must be a valid JSON object with non-empty task_id
    and completion strings. This is n=1 pass@1 mode: a task_id may appear
    at most once in the file — a repeated task_id (multiple completions
    for one task) fails closed rather than silently picking one, since
    this bridge does not (yet) support samples-per-task > 1. Never
    concatenates a prompt onto completion, never re-adds a function
    signature, never edits completion content.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise EvalPlusBridgeError("samples", f"samples file not found: {path}")

    text = path.read_text(encoding="utf-8")
    samples: List[Dict[str, str]] = []
    seen_task_ids: set[str] = set()

    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise EvalPlusBridgeError(
                "samples", f"{path}: line {line_no}: invalid JSON: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise EvalPlusBridgeError(
                "samples", f"{path}: line {line_no}: expected a JSON object"
            )

        task_id = obj.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise EvalPlusBridgeError(
                "samples", f"{path}: line {line_no}: missing/empty 'task_id'"
            )
        completion = obj.get("completion")
        if not isinstance(completion, str) or not completion.strip():
            raise EvalPlusBridgeError(
                "samples",
                f"{path}: line {line_no}: task_id={task_id!r}: missing/empty 'completion'",
            )
        if task_id in seen_task_ids:
            raise EvalPlusBridgeError(
                "samples",
                f"{path}: task_id={task_id!r} appears more than once — n=1 "
                f"pass@1 mode requires exactly one completion per task; "
                f"samples-per-task is not supported by this bridge",
            )
        seen_task_ids.add(task_id)
        samples.append({"task_id": task_id, "completion": completion})

    return samples


def compute_samples_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# EvalPlus package / dataset preflight
# ---------------------------------------------------------------------------


def get_evalplus_version() -> str:
    """Import the official evalplus package and return its version.

    Fails closed if evalplus cannot be imported or reports no discoverable
    version — never silently proceeds without a pinned version, since
    that would make the run unreproducible.
    """
    try:
        import evalplus  # noqa: F401 (import-success is what we're checking)
    except Exception as exc:  # ModuleNotFoundError and any import-time error
        raise EvalPlusBridgeError(
            "evalplus_import", f"failed to import evalplus: {exc}"
        ) from exc

    version = getattr(evalplus, "__version__", None)
    if not version:
        try:
            import importlib.metadata as importlib_metadata

            version = importlib_metadata.version("evalplus")
        except Exception as exc:
            raise EvalPlusBridgeError(
                "evalplus_import",
                f"could not determine evalplus package version: {exc}",
            ) from exc
    if not version:
        raise EvalPlusBridgeError(
            "evalplus_import", "evalplus package version could not be determined"
        )
    return version


def load_evalplus_dataset(
    benchmark: str, dataset_version: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """Load the official EvalPlus dataset for *benchmark* via evalplus's
    own dataset loader (never the original HumanEval/MBPP dataset, never a
    local HumanEval.jsonl.gz snapshot).

    Returns (task_id -> problem dict, resolved dataset_version). If
    *dataset_version* is None, this resolves an exact version marker from
    evalplus's own dataset-hash helper rather than silently proceeding
    with an unpinned dataset snapshot.
    """
    try:
        import evalplus.data as evalplus_data  # noqa: PLC0415
    except Exception as exc:
        raise EvalPlusBridgeError(
            "dataset_load", f"failed to import evalplus.data: {exc}"
        ) from exc

    if benchmark == "humaneval":
        loader = getattr(evalplus_data, "get_human_eval_plus", None)
        hash_fn = getattr(evalplus_data, "get_human_eval_plus_hash", None)
    elif benchmark == "mbpp":
        loader = getattr(evalplus_data, "get_mbpp_plus", None)
        hash_fn = getattr(evalplus_data, "get_mbpp_plus_hash", None)
    else:
        raise EvalPlusBridgeError(
            "dataset_load", f"unsupported benchmark {benchmark!r}"
        )

    if loader is None:
        raise EvalPlusBridgeError(
            "dataset_load",
            f"evalplus.data does not expose a dataset loader for {benchmark!r} "
            f"(refusing to fall back to the original, non-'+' dataset)",
        )

    resolved_version = dataset_version
    if resolved_version is None:
        if hash_fn is None:
            raise EvalPlusBridgeError(
                "dataset_load",
                "--dataset-version was not provided and evalplus exposes no "
                "dataset-hash helper to resolve an exact version — refusing "
                "to proceed with an unpinned dataset snapshot",
            )
        try:
            resolved_version = hash_fn()
        except Exception as exc:
            raise EvalPlusBridgeError(
                "dataset_load", f"failed to resolve dataset version/hash: {exc}"
            ) from exc
        if not resolved_version:
            raise EvalPlusBridgeError(
                "dataset_load", "resolved dataset version/hash was empty"
            )

    try:
        dataset = loader()
    except Exception as exc:
        raise EvalPlusBridgeError(
            "dataset_load", f"evalplus dataset loader for {benchmark!r} failed: {exc}"
        ) from exc

    if not isinstance(dataset, dict) or len(dataset) == 0:
        raise EvalPlusBridgeError(
            "dataset_load",
            f"evalplus dataset loader for {benchmark!r} returned no tasks",
        )

    return dataset, resolved_version


def verify_dataset_covers_samples(
    dataset_task_ids: Sequence[str], sample_task_ids: Sequence[str]
) -> None:
    """Every sample's task_id must exist in the official dataset. Fails
    closed on any sample referencing a task_id the dataset does not know
    about — never silently drops it."""
    dataset_set = set(dataset_task_ids)
    unknown = [t for t in sample_task_ids if t not in dataset_set]
    if unknown:
        raise EvalPlusBridgeError(
            "dataset_task_id_check",
            f"sample(s) reference task_id(s) not present in the official "
            f"EvalPlus dataset: {unknown}",
        )


# ---------------------------------------------------------------------------
# Official EvalPlus CLI invocation
# ---------------------------------------------------------------------------


def _invoke_evalplus_cli(
    *, benchmark: str, samples_path: pathlib.Path, timeout_seconds: float
) -> subprocess.CompletedProcess:
    """Invoke the official `python -m evalplus.evaluate` CLI as a list of
    argv tokens (never shell=True). Captures stdout/stderr; a timeout is
    fail-closed (raises), never silently retried or ignored."""
    cmd = [
        sys.executable, "-m", "evalplus.evaluate",
        "--dataset", benchmark,
        "--samples", str(samples_path),
    ]
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired as exc:
        raise EvalPlusBridgeError(
            "subprocess",
            f"official EvalPlus CLI timed out after {timeout_seconds}s",
        ) from exc
    except OSError as exc:
        raise EvalPlusBridgeError(
            "subprocess", f"failed to launch official EvalPlus CLI: {exc}"
        ) from exc


def _locate_official_result_file(samples_path: pathlib.Path) -> pathlib.Path:
    """EvalPlus's own CLI writes `<samples-stem>_eval_results.json` next to
    the samples file. Fails closed if that file is missing."""
    candidate = samples_path.with_name(samples_path.stem + "_eval_results.json")
    if not candidate.is_file():
        raise EvalPlusBridgeError(
            "result_locate",
            f"expected official EvalPlus result file not found: {candidate}",
        )
    return candidate


def _parse_official_result_file(path: pathlib.Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalPlusBridgeError(
            "result_parse",
            f"failed to parse official EvalPlus result file {path}: {exc}",
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("eval"), dict):
        raise EvalPlusBridgeError(
            "result_parse",
            f"official EvalPlus result file {path} is missing the expected "
            f"'eval' task-outcome mapping",
        )
    return data


_PASS_STATUS_VALUES = frozenset({"pass", "success"})
_MAX_ERROR_SUMMARY_LEN = 300


def _extract_task_outcome(task_id: str, entries: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    """Return (passed, error_type, error_message_summary) for one task's
    entries from the official result's "eval" mapping. n=1 mode: reads
    only the first (and only) sample entry. See module docstring's
    "Schema caveat" for the field-name assumption this makes."""
    if not isinstance(entries, list) or not entries:
        raise EvalPlusBridgeError(
            "result_parse",
            f"task_id={task_id!r}: official result has no sample entries",
        )
    entry = entries[0]
    if not isinstance(entry, dict):
        raise EvalPlusBridgeError(
            "result_parse", f"task_id={task_id!r}: sample entry is not an object"
        )

    status = entry.get("plus_status") or entry.get("base_status") or entry.get("status")
    if status is None:
        raise EvalPlusBridgeError(
            "result_parse",
            f"task_id={task_id!r}: no pass/fail status field found in "
            f"official result entry {entry!r}",
        )

    passed = str(status).lower() in _PASS_STATUS_VALUES
    if passed:
        return True, None, None

    error_type = entry.get("error_type") or str(status)
    raw_message = entry.get("error_message") or entry.get("details") or ""
    error_message = str(raw_message).replace("\n", " ").strip()
    if len(error_message) > _MAX_ERROR_SUMMARY_LEN:
        error_message = error_message[:_MAX_ERROR_SUMMARY_LEN] + "…(truncated)"
    return False, str(error_type), (error_message or None)


# ---------------------------------------------------------------------------
# JSON writing
# ---------------------------------------------------------------------------


def _write_json_deterministic(obj: Any, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(serialised)


def _write_text(text: str, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_evalplus_bridge(
    *,
    benchmark: str,
    samples_path: Union[str, pathlib.Path],
    output_dir: Union[str, pathlib.Path],
    task_ids_arg: Optional[str] = None,
    dataset_version: Optional[str] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Run the full fail-closed EvalPlus bridge for one completion JSONL
    (one treatment). Returns the summary dict on success; raises
    EvalPlusBridgeError (and writes failure.json) on any fail-closed
    condition. See module docstring for full scope/boundaries.
    """
    if benchmark not in ALLOWED_BENCHMARKS:
        raise EvalPlusBridgeError(
            "task_ids", f"benchmark must be one of {ALLOWED_BENCHMARKS}, got {benchmark!r}"
        )

    output_dir = pathlib.Path(output_dir)
    samples_path = pathlib.Path(samples_path)
    stdout_text = ""
    stderr_text = ""

    try:
        run_windows_preflight_guard()

        task_ids = parse_task_ids(task_ids_arg)
        if task_ids is not None:
            # EvalPlus 0.3.1's evaluate() hard-asserts
            # len(completion_id) == len(problems) and exposes no CLI flag or
            # public API parameter to evaluate a caller-selected task_id
            # subset (mini/noextreme only select a *fixed* reduced dataset,
            # not arbitrary task_ids). Silently running the full official
            # CLI against a partial samples file would just reproduce that
            # AssertionError, or worse, mislead about scope. Fail closed
            # instead of attempting a subset evaluation this EvalPlus
            # version cannot support without patching/replacing its loader.
            raise EvalPlusBridgeError("task_ids", _TASK_IDS_UNSUPPORTED_MESSAGE)

        samples = load_completion_samples(samples_path)
        original_sample_count = len(samples)
        filtered_samples = filter_samples_by_task_ids(samples, task_ids)

        evalplus_version = get_evalplus_version()
        dataset, resolved_dataset_version = load_evalplus_dataset(benchmark, dataset_version)
        dataset_task_ids = list(dataset.keys())

        sample_task_ids = [s["task_id"] for s in filtered_samples]
        verify_dataset_covers_samples(dataset_task_ids, sample_task_ids)

        proc = _invoke_evalplus_cli(
            benchmark=benchmark, samples_path=samples_path, timeout_seconds=timeout_seconds
        )
        stdout_text = proc.stdout or ""
        stderr_text = proc.stderr or ""
        if proc.returncode != 0:
            raise EvalPlusBridgeError(
                "subprocess",
                f"official EvalPlus CLI exited with return code {proc.returncode}",
            )

        result_path = _locate_official_result_file(samples_path)
        official_result = _parse_official_result_file(result_path)

        wanted_task_ids = set(sample_task_ids)
        eval_mapping = {
            tid: entries for tid, entries in official_result["eval"].items()
            if tid in wanted_task_ids
        }
        missing_in_result = [t for t in sample_task_ids if t not in eval_mapping]
        if missing_in_result:
            raise EvalPlusBridgeError(
                "result_parse",
                f"official result is missing outcome(s) for task_id(s): {missing_in_result}",
            )

        task_results = []
        passed_count = 0
        for task_id in sample_task_ids:
            passed, error_type, error_message = _extract_task_outcome(
                task_id, eval_mapping[task_id]
            )
            if passed:
                passed_count += 1
            task_results.append({
                "task_id": task_id,
                "passed": passed,
                "error_type": error_type,
                "error_message_summary": error_message,
            })

        total = len(task_results)
        failed_count = total - passed_count
        summary = {
            "benchmark": benchmark,
            "total": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_at_1": (passed_count / total) if total else 0.0,
            "status": "success",
        }
        manifest = {
            "benchmark": benchmark,
            "samples_path": str(samples_path),
            "samples_sha256": compute_samples_sha256(samples_path),
            "evalplus_version": evalplus_version,
            "dataset_version": resolved_dataset_version,
            "dataset_task_count": len(dataset_task_ids),
            "requested_task_ids": task_ids,
            "evaluated_task_ids": sample_task_ids,
            "sample_count": len(filtered_samples),
            "original_sample_count": original_sample_count,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "engine": _ENGINE,
            "status": "success",
        }

        _write_json_deterministic(task_results, output_dir / "evalplus_results.json")
        _write_json_deterministic(summary, output_dir / "evalplus_summary.json")
        _write_json_deterministic(manifest, output_dir / "evalplus_manifest.json")
        _write_text(stdout_text, output_dir / "stdout.txt")
        _write_text(stderr_text, output_dir / "stderr.txt")
        return summary

    except EvalPlusBridgeError as exc:
        failure = {
            "status": exc.status,
            "stage": exc.stage,
            "benchmark": benchmark,
            "samples_path": str(samples_path),
            "error_message": str(exc),
        }
        _write_json_deterministic(failure, output_dir / "failure.json")
        _write_text(stdout_text, output_dir / "stdout.txt")
        _write_text(stderr_text, output_dir / "stderr.txt")
        raise

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_tools.finals_rebuild.evalplus_bridge",
        description="Fail-closed bridge to the official EvalPlus CLI.",
    )
    parser.add_argument("--benchmark", required=True, choices=list(ALLOWED_BENCHMARKS))
    parser.add_argument("--samples", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--task-ids", default=None,
        help=(
            "Not supported by EvalPlus 0.3.1 (no task-subset evaluation "
            "path exists); passing this flag fails closed instead of "
            "running a partial evaluation."
        ),
    )
    parser.add_argument("--dataset-version", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        run_evalplus_bridge(
            benchmark=args.benchmark,
            samples_path=args.samples,
            output_dir=args.output_dir,
            task_ids_arg=args.task_ids,
            dataset_version=args.dataset_version,
            timeout_seconds=args.timeout_seconds,
        )
        return 0
    except EvalPlusBridgeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
