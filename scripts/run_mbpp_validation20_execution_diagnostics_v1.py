#!/usr/bin/env python3
"""Diagnostic-only Validation20 Pipeline → Healer execution diagnostics.

Analyzes existing 4B / 9B derivatives without calling models, modifying
candidate source code, re-running Healer, or overwriting existing formal EvalPlus results.

Each candidate/stage evaluation is strictly executed inside an isolated subprocess
with a hard timeout, stdin closed (DEVNULL), and stdout/stderr captured.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze  # noqa: E402
from scripts import preflight_mbpp_validation20_generation_v1 as gen_preflight  # noqa: E402

RUNNER_IDENTITY = "mbpp_validation20_execution_diagnostics_runner_v1"
DIAGNOSTIC_ACK = "I_ACKNOWLEDGE_DIAGNOSTIC_ONLY_REPLAY"

CATEGORIES: tuple[str, ...] = (
    "missing_candidate",
    "syntax_blocked",
    "import_or_load_blocked",
    "entry_point_blocked",
    "runtime_exception",
    "timeout",
    "executed_but_incorrect",
    "passed",
)

TRANSITION_CATEGORIES: tuple[str, ...] = (
    "verified_rescue",
    "execution_rescue",
    "blocker_removed_but_incorrect",
    "preserved_executable",
    "executable_regression",
    "unchanged_blocked",
    "unchanged_incorrect",
    "abstained",
)


class DiagnosticError(RuntimeError):
    """Fail-closed diagnostic runner violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_equal(actual: Any, expected: Any, atol: float = 1e-5) -> bool:
    if actual == expected:
        return True
    if isinstance(actual, float) and isinstance(expected, (int, float)):
        return abs(actual - expected) <= atol
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(actual) != len(expected):
            return False
        return all(_check_equal(a, e, atol) for a, e in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(_check_equal(actual[k], expected[k], atol) for k in actual.items())
    return False


def _worker_eval_entrypoint() -> None:
    """Worker process main entrypoint reading JSON payload from stdin."""
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input)
    except Exception as e:
        sys.stdout.write(
            json.dumps(
                {
                    "category": "runtime_exception",
                    "detail": f"WorkerInputError: {str(e)}",
                    "worker_pid": os.getpid(),
                }
            )
            + "\n"
        )
        sys.exit(0)

    # Disconnect stdin for candidate execution to prevent input() hanging
    sys.stdin = io.StringIO("")

    source = payload.get("source")
    entry_point = payload.get("entry_point", "")
    inputs = payload.get("inputs", [])
    outputs = payload.get("outputs", [])
    atol = payload.get("atol", 1e-5)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    res_category = "runtime_exception"
    res_detail = "unknown_worker_failure"

    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(
        stderr_buf
    ):
        # 1. AST syntax check
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            res_category = "syntax_blocked"
            res_detail = f"SyntaxError: {e.msg} at line {e.lineno}"
            tree = None
        except Exception as e:
            res_category = "syntax_blocked"
            res_detail = f"ASTError: {str(e)}"
            tree = None

        if tree is not None:
            # 2. Compile check
            code_obj = None
            try:
                code_obj = compile(source, filename="<candidate>", mode="exec")
            except (SyntaxError, ValueError) as e:
                res_category = "syntax_blocked"
                res_detail = f"CompileError: {str(e)}"
            except Exception as e:
                res_category = "syntax_blocked"
                res_detail = f"CompileError_{type(e).__name__}: {str(e)}"

            if code_obj is not None:
                # 3. Top-level module execution check
                mod_globals: dict[str, Any] = {"__name__": "__main__"}
                exec_ok = False
                try:
                    exec(code_obj, mod_globals)
                    exec_ok = True
                except (ImportError, ModuleNotFoundError, NameError) as e:
                    res_category = "import_or_load_blocked"
                    res_detail = f"{type(e).__name__}: {str(e)}"
                except Exception as e:
                    res_category = "import_or_load_blocked"
                    res_detail = f"TopLevel_{type(e).__name__}: {str(e)}"

                if exec_ok:
                    # 4. Entry point check
                    if entry_point not in mod_globals or not callable(
                        mod_globals[entry_point]
                    ):
                        res_category = "entry_point_blocked"
                        res_detail = (
                            f"missing_or_uncallable_entry_point: {entry_point}"
                        )
                    else:
                        func = mod_globals[entry_point]
                        # 5. Test suite execution
                        all_passed = True
                        eval_err = None
                        for inp, exp in zip(inputs, outputs):
                            try:
                                res = func(*inp)
                            except TypeError as e:
                                eval_err = (
                                    "entry_point_blocked",
                                    f"TypeError_arity_mismatch: {str(e)}",
                                )
                                break
                            except Exception as e:
                                eval_err = (
                                    "runtime_exception",
                                    f"{type(e).__name__}: {str(e)}",
                                )
                                break

                            if not _check_equal(res, exp, atol):
                                all_passed = False

                        if eval_err is not None:
                            res_category, res_detail = eval_err
                        elif all_passed:
                            res_category = "passed"
                            res_detail = "all_tests_passed"
                        else:
                            res_category = "executed_but_incorrect"
                            res_detail = "output_mismatch"

    captured_out = stdout_buf.getvalue()[:500]
    captured_err = stderr_buf.getvalue()[:500]

    out_payload = {
        "category": res_category,
        "detail": res_detail,
        "worker_pid": os.getpid(),
        "stdout_snippet": captured_out,
        "stderr_snippet": captured_err,
    }
    sys.stdout.write(json.dumps(out_payload) + "\n")
    sys.stdout.flush()
    sys.exit(0)


def run_isolated_stage_eval(
    *,
    source: str | None,
    entry_point: str,
    arities: tuple[int, ...],
    inputs: list[list[Any]],
    outputs: list[Any],
    atol: float = 1e-5,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Runs candidate evaluation in an isolated subprocess with hard timeout."""
    if source is None or not str(source).strip():
        return {
            "category": "missing_candidate",
            "detail": "source_none_or_empty",
            "worker_pid": None,
        }

    payload = {
        "source": source,
        "entry_point": entry_point,
        "arities": list(arities),
        "inputs": inputs,
        "outputs": outputs,
        "atol": atol,
    }

    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker-eval"]
    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        stdout_data, stderr_data = proc.communicate(
            input=json.dumps(payload), timeout=timeout
        )
        if proc.returncode != 0 and not stdout_data.strip():
            return {
                "category": "runtime_exception",
                "detail": f"SubprocessExitError_{proc.returncode}: {stderr_data[:200]}",
                "worker_pid": proc.pid,
            }
        res = json.loads(stdout_data.strip())
        res.setdefault("worker_pid", proc.pid)
        return res
    except subprocess.TimeoutExpired:
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=2.0)
            except Exception:
                pass
        return {
            "category": "timeout",
            "detail": f"timeout_exceeded_{timeout}s",
            "worker_pid": proc.pid if proc else None,
        }
    except Exception as e:
        return {
            "category": "runtime_exception",
            "detail": f"SubprocessLauncherError_{type(e).__name__}: {str(e)}",
            "worker_pid": proc.pid if proc else None,
        }


def classify_transition(pipeline_cat: str, post_cat: str) -> dict[str, Any]:
    is_pipeline_exec = pipeline_cat in ("executed_but_incorrect", "passed")
    is_post_exec = post_cat in ("executed_but_incorrect", "passed")
    is_pipeline_blocked = pipeline_cat in (
        "syntax_blocked",
        "import_or_load_blocked",
        "entry_point_blocked",
        "runtime_exception",
        "timeout",
    )
    is_post_blocked = post_cat in (
        "syntax_blocked",
        "import_or_load_blocked",
        "entry_point_blocked",
        "runtime_exception",
        "timeout",
    )

    verified_rescue = (pipeline_cat != "passed") and (post_cat == "passed")
    execution_rescue = is_pipeline_blocked and is_post_exec
    blocker_removed_but_incorrect = is_pipeline_blocked and (
        post_cat == "executed_but_incorrect"
    )
    preserved_executable = is_pipeline_exec and is_post_exec
    executable_regression = is_pipeline_exec and is_post_blocked
    unchanged_blocked = is_pipeline_blocked and is_post_blocked
    unchanged_incorrect = (pipeline_cat == "executed_but_incorrect") and (
        post_cat == "executed_but_incorrect"
    )
    abstained = (pipeline_cat == "missing_candidate") or (
        post_cat == "missing_candidate"
    )

    if verified_rescue:
        trans_cat = "verified_rescue"
    elif blocker_removed_but_incorrect:
        trans_cat = "blocker_removed_but_incorrect"
    elif execution_rescue:
        trans_cat = "execution_rescue"
    elif executable_regression:
        trans_cat = "executable_regression"
    elif preserved_executable and not unchanged_incorrect:
        trans_cat = "preserved_executable"
    elif unchanged_incorrect:
        trans_cat = "unchanged_incorrect"
    elif unchanged_blocked:
        trans_cat = "unchanged_blocked"
    else:
        trans_cat = "abstained"

    return {
        "transition_category": trans_cat,
        "verified_rescue": str(verified_rescue).lower(),
        "execution_rescue": str(execution_rescue).lower(),
        "blocker_removed_but_incorrect": str(blocker_removed_but_incorrect).lower(),
        "preserved_executable": str(preserved_executable).lower(),
        "executable_regression": str(executable_regression).lower(),
        "unchanged_blocked": str(unchanged_blocked).lower(),
        "unchanged_incorrect": str(unchanged_incorrect).lower(),
        "abstained": str(abstained).lower(),
    }


def zero_candidate_execution_preflight(
    *,
    model: str,
    repo_root: Path = REPO_ROOT,
    require_output_absent: bool = True,
) -> dict[str, Any]:
    model_tag = gen_preflight.resolve_model_tag(model)
    gen_receipt = gen_preflight.zero_model_preflight(
        model=model_tag,
        repo_root=repo_root,
        require_verified_identity=False,
        require_output_absent=False,
    )
    model_key = freeze.MODEL_SPECS[model_tag]["model_key"]
    run_dir = repo_root / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    deriv_dir = run_dir / "derivatives"
    _require(deriv_dir.is_dir(), f"derivatives directory missing: {deriv_dir}")

    out_dir = repo_root / freeze.ARTIFACT_RELATIVE / "diagnostics" / model_key
    if require_output_absent:
        _require(
            not out_dir.exists(),
            f"diagnostics output directory must be absent before run: {out_dir}",
        )

    cells = freeze._read_csv(
        repo_root / freeze.model_dir(model_tag) / "generation_cells.csv"
    )
    _require(len(cells) == 400, f"{model_tag}: expected 400 generation cells")

    return {
        "status": "zero_candidate_execution_diagnostics_preflight_passed",
        "plan_id": freeze.PLAN_ID,
        "model_tag": model_tag,
        "model_key": model_key,
        "planned_candidates": 400,
        "stages_analyzed": ["pipeline_corrected", "post_h1_h2_h3_h4"],
        "derivatives_dir": deriv_dir.as_posix(),
        "output_directory": out_dir.as_posix(),
        "generation_preflight_status": gen_receipt["status"],
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
        "subprocess_isolation": True,
    }


def analyze_cell(
    cell: Mapping[str, str],
    deriv_path: Path,
    task_data: dict[str, Any],
    gt_data: dict[str, Any],
    per_cell_timeout: float = 10.0,
) -> dict[str, Any]:
    derived = _read_json(deriv_path)
    stages = derived["stages"]

    pipeline_stage = stages["pipeline_corrected"]
    post_stage = stages["post_h1_h2_h3_h4"]

    entry_point = cell["expected_entry_point"]
    arities = tuple(
        int(part) for part in cell["expected_positional_arities"].split("|") if part
    )

    inputs = task_data.get("base_input", []) + task_data.get("plus_input", [])
    outputs = gt_data.get("base", []) + gt_data.get("plus", [])
    atol = task_data.get("atol", 1e-5)

    p_res = run_isolated_stage_eval(
        source=pipeline_stage.get("source"),
        entry_point=entry_point,
        arities=arities,
        inputs=inputs,
        outputs=outputs,
        atol=atol,
        timeout=per_cell_timeout,
    )
    h_res = run_isolated_stage_eval(
        source=post_stage.get("source"),
        entry_point=entry_point,
        arities=arities,
        inputs=inputs,
        outputs=outputs,
        atol=atol,
        timeout=per_cell_timeout,
    )

    trans = classify_transition(p_res["category"], h_res["category"])

    return {
        "generation_id": cell["generation_id"],
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": cell["seed"],
        "prompt_condition": cell["prompt_condition"],
        "model_tag": cell["model_tag"],
        "pipeline_corrected_category": p_res["category"],
        "pipeline_corrected_detail": p_res["detail"],
        "post_h1_h2_h3_h4_category": h_res["category"],
        "post_h1_h2_h3_h4_detail": h_res["detail"],
        "transition_category": trans["transition_category"],
        "verified_rescue": trans["verified_rescue"],
        "execution_rescue": trans["execution_rescue"],
        "blocker_removed_but_incorrect": trans["blocker_removed_but_incorrect"],
        "preserved_executable": trans["preserved_executable"],
        "executable_regression": trans["executable_regression"],
        "unchanged_blocked": trans["unchanged_blocked"],
        "unchanged_incorrect": trans["unchanged_incorrect"],
        "abstained": trans["abstained"],
        "first_effective_rule": post_stage.get("first_effective_rule") or "",
        "rules_applied": "|".join(post_stage.get("rules_applied") or []),
    }


def execute_diagnostics(
    *,
    model: str,
    parallel: int = 8,
    resume: bool = False,
    repo_root: Path = REPO_ROOT,
    acknowledgement: str = "",
    per_cell_timeout: float = 10.0,
) -> dict[str, Any]:
    _require(
        acknowledgement == DIAGNOSTIC_ACK, "diagnostic acknowledgement mismatch"
    )
    model_tag = gen_preflight.resolve_model_tag(model)
    model_key = freeze.MODEL_SPECS[model_tag]["model_key"]
    out_dir = repo_root / freeze.ARTIFACT_RELATIVE / "diagnostics" / model_key
    if not resume and out_dir.exists():
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)
    preflight = zero_candidate_execution_preflight(
        model=model_tag, repo_root=repo_root, require_output_absent=False
    )

    from evalplus.data import get_mbpp_plus
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    from evalplus.evaluate import get_groundtruth

    all_problems = get_mbpp_plus(version=freeze.DATASET_VERSION)
    planned_cells = _read_csv(
        repo_root / freeze.model_dir(model_tag) / "generation_cells.csv"
    )
    task_ids = sorted({row["task_id"] for row in planned_cells})
    problems = {task_id: all_problems[task_id] for task_id in task_ids}
    subset_hash = (
        freeze.DATASET_HASH
        + "-"
        + _sha256_bytes("\n".join(task_ids).encode("utf-8"))[:16]
    )
    groundtruth = get_groundtruth(problems, subset_hash, MBPP_OUTPUT_NOT_NONE_TASKS)

    run_dir = repo_root / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    deriv_dir = run_dir / "derivatives"
    out_dir = repo_root / freeze.ARTIFACT_RELATIVE / "diagnostics" / model_key
    j_dir = out_dir / "j"
    j_dir.mkdir(parents=True, exist_ok=True)

    cell_ledger_path = out_dir / "diagnostic_cell_ledger.csv"
    transition_path = out_dir / "pipeline_to_healer_transition.csv"
    summary_path = out_dir / "diagnostic_summary.json"

    # Evaluate cells with per-cell journal persistence for safe resume
    for cell in planned_cells:
        gen_id = cell["generation_id"]
        journal_path = j_dir / f"{gen_id}.json"
        if journal_path.is_file():
            continue
        deriv_path = deriv_dir / f"{gen_id}.json"
        _require(deriv_path.is_file(), f"missing derivative file: {deriv_path}")
        res = analyze_cell(
            cell=cell,
            deriv_path=deriv_path,
            task_data=problems[cell["task_id"]],
            gt_data=groundtruth[cell["task_id"]],
            per_cell_timeout=per_cell_timeout,
        )
        journal_path.write_text(
            json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # Read all cell journals for final aggregation
    cell_results: list[dict[str, Any]] = []
    for cell in planned_cells:
        gen_id = cell["generation_id"]
        journal_path = j_dir / f"{gen_id}.json"
        _require(journal_path.is_file(), f"incomplete diagnostic run: missing journal {journal_path}")
        cell_results.append(_read_json(journal_path))

    # Write diagnostic_cell_ledger.csv
    fields = list(cell_results[0].keys()) if cell_results else []
    with cell_ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(cell_results)

    # Write pipeline_to_healer_transition.csv
    trans_fields = [
        "generation_id",
        "task_id",
        "prompt_condition",
        "seed",
        "pipeline_corrected_category",
        "post_h1_h2_h3_h4_category",
        "transition_category",
        "first_effective_rule",
        "rules_applied",
    ]
    with transition_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trans_fields, lineterminator="\n")
        writer.writeheader()
        for row in cell_results:
            writer.writerow({k: row[k] for k in trans_fields})

    # Summary counts
    p_counts = {cat: 0 for cat in CATEGORIES}
    h_counts = {cat: 0 for cat in CATEGORIES}
    trans_counts = {cat: 0 for cat in TRANSITION_CATEGORIES}

    for row in cell_results:
        p_counts[row["pipeline_corrected_category"]] += 1
        h_counts[row["post_h1_h2_h3_h4_category"]] += 1
        trans_counts[row["transition_category"]] += 1

    summary = {
        "status": "diagnostics_complete",
        "plan_id": freeze.PLAN_ID,
        "runner_identity": RUNNER_IDENTITY,
        "model_tag": model_tag,
        "model_key": model_key,
        "candidates": len(cell_results),
        "stages_analyzed": ["pipeline_corrected", "post_h1_h2_h3_h4"],
        "counts_by_stage": {
            "pipeline_corrected": p_counts,
            "post_h1_h2_h3_h4": h_counts,
        },
        "transition_counts": trans_counts,
        "model_calls": 0,
        "candidate_source_modified": False,
        "healer_rerun": False,
        "evalplus_formal_overwritten": False,
        "subprocess_isolation": True,
    }

    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    if len(argv or sys.argv[1:]) > 0 and (argv or sys.argv[1:])[0] == "--worker-eval":
        _worker_eval_entrypoint()
        return 0

    parser.add_argument("--model", required=True, choices=freeze.ALLOWED_MODEL_TAGS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--per-cell-timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    if args.preflight:
        print(
            json.dumps(
                zero_candidate_execution_preflight(model=args.model),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = execute_diagnostics(
        model=args.model,
        parallel=args.parallel,
        resume=bool(args.resume),
        acknowledgement=args.acknowledgement,
        per_cell_timeout=args.per_cell_timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
