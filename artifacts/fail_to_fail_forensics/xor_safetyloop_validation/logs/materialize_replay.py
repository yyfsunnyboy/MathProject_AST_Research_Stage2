from __future__ import annotations

import ast
import copy
import csv
import difflib
import hashlib
import itertools
import json
import sys
from pathlib import Path


ARTIFACT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from core.healers.ast_healer import ASTHealer  # noqa: E402


CASES = {
    "HumanEval/39": {
        "family": "safety_loop",
        "entry_point": "prime_fib",
        "expected_classification": "structural/runtime-semantics recovery only",
        "raw_semantics": "nested Fibonacci generator is unbounded and yields until its consumer returns",
    },
    "Mbpp/311": {
        "family": "xor",
        "entry_point": "set_left_most_unset_bit",
        "expected_classification": "structural/runtime-semantics recovery only",
        "raw_semantics": "bitwise XOR participates in a bit-manipulation expression",
    },
    "Mbpp/6": {
        "family": "xor",
        "entry_point": "differ_At_One_Bit_Pos",
        "expected_classification": "official base-regression recovery",
        "raw_semantics": "bitwise XOR computes differing bit positions",
    },
    "Mbpp/633": {
        "family": "xor",
        "entry_point": "pair_xor_Sum",
        "expected_classification": "official base-regression recovery",
        "raw_semantics": "bitwise XOR is accumulated over integer pairs",
    },
    "Mbpp/735": {
        "family": "xor",
        "entry_point": "toggle_middle_bits",
        "expected_classification": "structural/runtime-semantics recovery only",
        "raw_semantics": "bitwise XOR toggles a computed mask",
    },
    "Mbpp/739": {
        "family": "safety_loop",
        "entry_point": "find_Index",
        "expected_classification": "structural/runtime-semantics recovery only",
        "raw_semantics": "unbounded search exits through a reachable return",
    },
}

CONDITIONS = ("Raw", "Original_Ab3", "Candidate_Healer_vNext")
MANIFEST_FIELDS = (
    "task_id",
    "strategy",
    "source_path",
    "eval_ready_path",
    "source_sha256",
    "eval_ready_sha256",
    "source_bytes",
    "eval_ready_bytes",
    "extraction_changed",
    "parseable",
    "meaningful_code",
    "entry_point",
    "entry_point_present",
    "materializer_version",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fields: tuple[str, ...] | list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def module_entry_count(source: str, entry_point: str) -> int:
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == entry_point
        for node in ast.parse(source).body
    )


def unified_diff(before: str, after: str, before_name: str, after_name: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
        )
    )


def load_namespace(source: str) -> dict:
    namespace: dict = {}
    exec(compile(source, "<isolated-replay>", "exec"), namespace)
    return namespace


def outcome(function, args: tuple) -> dict:
    try:
        value = function(*args)
        return {"kind": "return", "value": repr(value)}
    except Exception as exc:
        return {"kind": "exception", "value": f"{type(exc).__name__}: {exc}"}


def xor_witness(task_id: str, entry_point: str, sources: dict[str, str]) -> dict:
    functions = {
        condition: load_namespace(source)[entry_point]
        for condition, source in sources.items()
    }
    if task_id == "Mbpp/311":
        arguments = ((value,) for value in range(0, 33))
    elif task_id == "Mbpp/6":
        arguments = itertools.product(range(0, 17), repeat=2)
    elif task_id == "Mbpp/633":
        arguments = ((values, 0) for values in ([1, 2], [2, 3, 4], [0, 7, 8]))
    elif task_id == "Mbpp/735":
        arguments = ((value,) for value in range(3, 33))
    else:
        raise AssertionError(task_id)

    for args in arguments:
        args = tuple(args)
        results = {
            condition: outcome(function, args)
            for condition, function in functions.items()
        }
        if (
            results["Candidate_Healer_vNext"] == results["Raw"]
            and results["Original_Ab3"] != results["Raw"]
        ):
            return {
                "status": "pass",
                "arguments": repr(args),
                "outcomes": results,
                "claim": "Candidate matches Raw runtime XOR semantics and differs from Original Ab3",
            }
    return {"status": "fail", "claim": "no distinguishing witness found"}


def extract_nested_generator(source: str, outer_name: str, nested_name: str):
    tree = ast.parse(source)
    outer = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == outer_name
    )
    nested = next(
        node for node in outer.body
        if isinstance(node, ast.FunctionDef) and node.name == nested_name
    )
    module = ast.Module(body=[copy.deepcopy(nested)], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict = {}
    exec(compile(module, "<nested-generator-witness>", "exec"), namespace)
    return namespace[nested_name]


def safety_loop_witness(task_id: str, entry_point: str, sources: dict[str, str]) -> dict:
    if task_id == "HumanEval/39":
        lengths = {}
        for condition, source in sources.items():
            generator = extract_nested_generator(source, entry_point, "fib")
            lengths[condition] = len(list(itertools.islice(generator(), 1001)))
        passed = (
            lengths["Raw"] == 1001
            and lengths["Candidate_Healer_vNext"] == 1001
            and lengths["Original_Ab3"] == 1000
        )
        return {
            "status": "pass" if passed else "fail",
            "witness": "number of values obtainable from nested fib() with islice(..., 1001)",
            "outcomes": lengths,
            "claim": "Candidate preserves the unbounded generator; Original Ab3 truncates it",
        }

    functions = {
        condition: load_namespace(source)[entry_point]
        for condition, source in sources.items()
    }
    results = {
        condition: outcome(function, (7,))
        for condition, function in functions.items()
    }
    passed = (
        results["Candidate_Healer_vNext"] == results["Raw"]
        and results["Original_Ab3"] != results["Raw"]
    )
    return {
        "status": "pass" if passed else "fail",
        "arguments": "(7,)",
        "outcomes": results,
        "claim": "Candidate preserves reachable-return search semantics beyond 1000 iterations",
    }


def main() -> None:
    reviewed = {
        row["task_id"]: row
        for row in load_rows(REPO_ROOT / "artifacts/fail_to_fail_forensics/qwen8b_forensic_reviewed.csv")
        if row["task_id"] in CASES and row["model"] == "qwen3-8b"
    }
    pairing = {
        row["task_id"]: row
        for row in load_rows(REPO_ROOT / "artifacts/fail_to_fail_forensics/pairing_manifest.csv")
        if row["task_id"] in CASES and row["model"] == "qwen3-8b"
    }
    if set(reviewed) != set(CASES) or set(pairing) != set(CASES):
        raise SystemExit("six-case source inventory is incomplete")

    isolated_root = ARTIFACT_ROOT / "isolated_outputs"
    diff_root = ARTIFACT_ROOT / "diffs"
    manifest_rows: dict[str, list[dict]] = {"humaneval": [], "mbpp": []}
    candidate_rows: list[dict] = []
    forensic_rows: list[dict] = []
    local_results: list[dict] = []

    for task_id, config in CASES.items():
        review = reviewed[task_id]
        pair = pairing[task_id]
        source_paths = {
            "Raw": Path(pair["raw_eval_ready_path"]),
            "Original_Ab3": Path(pair["healed_eval_ready_path"]),
        }
        raw_text = read_text(source_paths["Raw"])
        original_text = read_text(source_paths["Original_Ab3"])
        healer = ASTHealer(
            require_entry_point=False,
            entry_point=config["entry_point"],
            domain_mode="benchmark",
        )
        candidate_text, fixes = healer.heal(raw_text)
        sources = {
            "Raw": raw_text,
            "Original_Ab3": original_text,
            "Candidate_Healer_vNext": candidate_text,
        }

        dataset = review["dataset"]
        filename = task_id.replace("/", "_") + "__s0.py"
        source_origin = {
            "Raw": str(source_paths["Raw"]),
            "Original_Ab3": str(source_paths["Original_Ab3"]),
            "Candidate_Healer_vNext": str(source_paths["Raw"]),
        }
        per_case_conditions = []
        for condition in CONDITIONS:
            normalized = sources[condition].rstrip() + "\n"
            output_path = (
                isolated_root / "eval_ready_outputs" / dataset / "qwen3-8b"
                / condition / filename
            )
            write_text(output_path, normalized)
            entry_count = module_entry_count(normalized, config["entry_point"])
            wsl_path = "/mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/" + str(
                output_path.relative_to(REPO_ROOT)
            ).replace("\\", "/")
            row = {
                "task_id": task_id,
                "strategy": condition,
                "source_path": source_origin[condition],
                "eval_ready_path": wsl_path,
                "source_sha256": sha256_text(normalized),
                "eval_ready_sha256": sha256_text(normalized),
                "source_bytes": len(normalized.encode("utf-8")),
                "eval_ready_bytes": len(normalized.encode("utf-8")),
                "extraction_changed": False,
                "parseable": True,
                "meaningful_code": True,
                "entry_point": config["entry_point"],
                "entry_point_present": entry_count == 1,
                "materializer_version": "xor-safetyloop-counterfactual-1.0",
            }
            manifest_rows[dataset].append(row)
            condition_row = {
                "dataset": dataset,
                "task_id": task_id,
                "sample_idx": 0,
                "condition": condition,
                "entry_point": config["entry_point"],
                "entry_point_count": entry_count,
                "source_path": source_origin[condition],
                "materialized_path": str(output_path.relative_to(REPO_ROOT)),
                "sha256": sha256_text(normalized),
                "ast_parse": "pass",
                "targeted_execution": "pending_witness",
            }
            candidate_rows.append(condition_row)
            per_case_conditions.append(condition_row)

        raw_to_original = unified_diff(
            raw_text, original_text, f"{task_id} Raw", f"{task_id} Original Ab3"
        )
        raw_to_candidate = unified_diff(
            raw_text, candidate_text, f"{task_id} Raw", f"{task_id} Candidate Healer-vNext"
        )
        original_to_candidate = unified_diff(
            original_text,
            candidate_text,
            f"{task_id} Original Ab3",
            f"{task_id} Candidate Healer-vNext",
        )
        stem = task_id.replace("/", "_")
        write_text(diff_root / f"{stem}__raw_to_original.diff", raw_to_original or "# no diff")
        write_text(diff_root / f"{stem}__raw_to_candidate.diff", raw_to_candidate or "# no diff")
        write_text(
            diff_root / f"{stem}__original_to_candidate.diff",
            original_to_candidate or "# no diff",
        )

        witness = (
            xor_witness(task_id, config["entry_point"], sources)
            if config["family"] == "xor"
            else safety_loop_witness(task_id, config["entry_point"], sources)
        )
        for row in per_case_conditions:
            row["targeted_execution"] = witness["status"]
        local_results.append(
            {
                "dataset": dataset,
                "task_id": task_id,
                "family": config["family"],
                "candidate_fixes": fixes,
                "candidate_logs": healer.logs,
                "runtime_semantics_witness": witness,
                "official_replay": "pending",
                "expected_classification": config["expected_classification"],
            }
        )

        second_layer = (
            "plus failure remains in Raw"
            if "base=pass,plus=fail" in review["raw_error"]
            else "base and plus failures already exist in Raw"
        )
        forensic_rows.append(
            {
                "dataset": dataset,
                "task_id": task_id,
                "sample_idx": 0,
                "family": config["family"],
                "raw_result": review["raw_error"],
                "original_ab3_result": review["healed_error"],
                "rules_triggered": review["rules_triggered"],
                "actual_diff": review["normalized_diff_path"],
                "raw_semantics": config["raw_semantics"],
                "runtime_semantics_changed": True,
                "second_layer_error": second_layer,
                "eligibility": review["eligibility"],
                "expected_candidate_type": config["expected_classification"],
                "candidate_gate": "benchmark mode preserves Raw operator/loop semantics",
                "reference_solution_used": False,
            }
        )

    for dataset, rows in manifest_rows.items():
        write_csv(
            isolated_root / f"eval_ready_manifest_{dataset}.csv",
            rows,
            MANIFEST_FIELDS,
        )

    candidate_fields = [
        "dataset", "task_id", "sample_idx", "condition", "entry_point",
        "entry_point_count", "source_path", "materialized_path", "sha256",
        "ast_parse", "targeted_execution",
    ]
    write_csv(ARTIFACT_ROOT / "candidate_manifest.csv", candidate_rows, candidate_fields)
    forensic_fields = [
        "dataset", "task_id", "sample_idx", "family", "raw_result",
        "original_ab3_result", "rules_triggered", "actual_diff", "raw_semantics",
        "runtime_semantics_changed", "second_layer_error", "eligibility",
        "expected_candidate_type", "candidate_gate", "reference_solution_used",
    ]
    write_csv(ARTIFACT_ROOT / "case_forensics.csv", forensic_rows, forensic_fields)

    targeted = {
        "result_name": "Candidate Healer / Healer-vNext XOR and safety-loop counterfactual replay",
        "status": "local_validation_complete_official_pending",
        "candidate_domain_mode": "benchmark",
        "reference_solution_used": False,
        "results": local_results,
    }
    (ARTIFACT_ROOT / "targeted_results.json").write_text(
        json.dumps(targeted, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ARTIFACT_ROOT / "evalplus_results.json").write_text(
        json.dumps(
            {
                "result_name": "Candidate Healer / Healer-vNext official EvalPlus counterfactual replay",
                "status": "pending",
                "requested_task_ids": list(CASES),
                "requested_conditions": list(CONDITIONS),
                "results": [],
                "original_pass_at_1_inclusion": False,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    commands = """\
cd /mnt/c/Users/yehya/Documents/GitHub/AST_experiment
source .venv-wsl/bin/activate
python exp1_benchmark/run_eval.py --dataset humaneval --outputs /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/xor_safetyloop_validation/isolated_outputs --results /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/xor_safetyloop_validation/isolated_results --engine evalplus --task-ids HumanEval/39 --strategies Raw Original_Ab3 Candidate_Healer_vNext
python exp1_benchmark/run_eval.py --dataset mbpp --outputs /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/xor_safetyloop_validation/isolated_outputs --results /mnt/c/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/xor_safetyloop_validation/isolated_results --engine evalplus --task-ids Mbpp/6 Mbpp/311 Mbpp/633 Mbpp/735 Mbpp/739 --strategies Raw Original_Ab3 Candidate_Healer_vNext
"""
    write_text(ARTIFACT_ROOT / "commands.txt", commands)
    (ARTIFACT_ROOT / "logs/materialization.json").write_text(
        json.dumps(
            {
                "case_count": len(CASES),
                "condition_count": len(candidate_rows),
                "all_ast_parse": all(row["ast_parse"] == "pass" for row in candidate_rows),
                "all_entry_points_unique": all(row["entry_point_count"] == 1 for row in candidate_rows),
                "all_runtime_witnesses_pass": all(
                    row["runtime_semantics_witness"]["status"] == "pass"
                    for row in local_results
                ),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
