#!/usr/bin/env python3
"""Build separated Scaffold and Healer evidence packets for MBPP+ run_003."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_mbpp_development_failure_census as milestone_1c  # noqa: E402


RUN_RELATIVE = milestone_1c.RUN_RELATIVE
M1C_RELATIVE = RUN_RELATIVE / "milestone_1c_failure_census"
OUTPUT_RELATIVE = RUN_RELATIVE / "milestone_1d_evidence_review"

EXPECTED_M1C_HASHES = {
    "failure_census.csv": "d6df0132893927b36aa1bdb58fbee00fe660be7cd0745ba3c6fd5c4960b59c94",
    "failure_census_manifest.json": "c4fabfb3cc5640f323cc30610dcf3fa94caded5c870c1126a6255a40340212b7",
    "failure_census_summary.md": "b6b7a0d935b7876c210d06c366e2bb5746424aefefa788f4a5ad4a5fd167452b",
}

SCAFFOLD_FIELDS = (
    "task_id",
    "seed",
    "cell_id",
    "raw_generation_sha256",
    "pipeline_program_sha256",
    "raw_protocol_compliance",
    "raw_protocol_violations",
    "code_fence_marker_count",
    "completed_fenced_block_count",
    "python_fenced_block_count",
    "extra_text_outside_fences",
    "empty_output",
    "multiple_program_segments",
    "generation_truncated",
    "raw_python_compile_status",
    "pipeline_extraction_action",
    "observed_status",
    "pipeline_status",
    "scaffold_evidence_class",
    "scaffold_constraint_candidate",
    "evidence_basis",
    "review_status",
)

CLUSTER_FIELDS = (
    "signature_id",
    "category",
    "cell_count",
    "unique_task_count",
    "representative_cell_ids",
    "proposed_action",
    "semantic_risk",
    "positive_examples",
    "counterexamples",
    "do_not_repair_conditions",
    "classification_evidence",
)

SIGNATURE_ORDER = (
    "extraction_ambiguous_multiple_python_fences",
    "extraction_ambiguous_other_fences",
    "syntax_fstring_parse_error",
    "syntax_unterminated_string",
    "syntax_invalid_plain_text",
    "entrypoint_unique_arity_compatible_candidate",
    "entrypoint_no_unique_candidate",
    "unknown_eval_failure_single_top_level_function",
    "unknown_eval_failure_multiple_top_level_functions",
)

FENCED_BLOCK_RE = re.compile(r"```([^\r\n`]*)\r?\n(.*?)```", re.DOTALL)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise milestone_1c.CensusIntegrityError(message)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_active_tasks(repo_root: Path, selected_ids: list[str]) -> dict[str, dict[str, str]]:
    """Retain prompt and entry point only for the permitted active 20-task set."""
    selected = set(selected_ids)
    tasks: dict[str, dict[str, str]] = {}
    with (repo_root / milestone_1c.TASKS_RELATIVE).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in selected:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"{task_id}: model-visible task schema drift",
            )
            tasks[task_id] = record
    _require(set(tasks) == selected, "active development task set mismatch")
    return tasks


def _raw_compile_status(source: str) -> str:
    try:
        compile(source, "<saved-raw-generation>", "exec")
    except (SyntaxError, ValueError, OverflowError):
        return "fail"
    return "pass"


def _raw_features(raw: dict[str, Any]) -> dict[str, Any]:
    source = raw["raw_response"]
    blocks = list(FENCED_BLOCK_RE.finditer(source))
    labels = [match.group(1).strip().lower() for match in blocks]
    marker_count = source.count("```")
    outside = FENCED_BLOCK_RE.sub("", source)
    empty = not source.strip()
    truncated = raw["generation_metadata"]["done_reason"] != "stop"
    compile_status = _raw_compile_status(source)
    extra_text = bool(marker_count and outside.strip())
    violations: list[str] = []
    if empty:
        violations.append("empty_output")
    if marker_count:
        violations.append("markdown_code_fence")
    if len(blocks) > 1:
        violations.append("multiple_program_segments")
    if marker_count % 2:
        violations.append("unbalanced_code_fence")
    if extra_text:
        violations.append("extra_text_outside_code_fences")
    if truncated:
        violations.append("generation_length_termination")
    if compile_status == "fail":
        violations.append("raw_not_python_compilable")
    return {
        "marker_count": marker_count,
        "block_count": len(blocks),
        "python_blocks": sum(label in {"python", "py"} for label in labels),
        "extra_text": extra_text,
        "empty": empty,
        "multiple": len(blocks) > 1,
        "truncated": truncated,
        "compile_status": compile_status,
        "violations": violations,
        "compliant": not violations,
    }


def _pipeline_action(pipeline: dict[str, Any]) -> str:
    status = pipeline["extraction_status"]
    method = pipeline["extraction_method"]
    if status != "extracted":
        return f"reject_{status}:{method}"
    if pipeline["changed_from_observed"]:
        return f"extract:{method}"
    return f"pass_through:{method}"


def _scaffold_constraints(features: dict[str, Any], pipeline: dict[str, Any]) -> str:
    candidates: list[str] = []
    if features["empty"]:
        candidates.append("require_nonempty_output")
    if features["marker_count"] or features["extra_text"]:
        candidates.append("emit_python_only_without_markdown_or_prose")
    if features["multiple"] or pipeline["extraction_status"] != "extracted":
        candidates.append("emit_exactly_one_program")
    if features["truncated"]:
        candidates.append("emit_complete_program_within_frozen_token_budget")
    if features["compile_status"] == "fail":
        candidates.append("emit_syntactically_complete_python")
    return "|".join(dict.fromkeys(candidates)) or "none_observed"


def _scaffold_class(evaluation: dict[str, str], pipeline: dict[str, Any]) -> str:
    if evaluation["observed_status"] == "fail" and evaluation["pipeline_corrected_status"] == "pass":
        return "verified_pipeline_rescue"
    if pipeline["extraction_status"] != "extracted":
        return "pipeline_extraction_failure"
    if evaluation["pipeline_corrected_status"] == "fail":
        return "pipeline_extracted_evaluation_fail"
    raise milestone_1c.CensusIntegrityError("unexpected Scaffold evidence class")


def _review_status(scaffold_class: str) -> str:
    return {
        "verified_pipeline_rescue": "verified_pipeline_rescue",
        "pipeline_extraction_failure": "scaffold_manual_review_required",
        "pipeline_extracted_evaluation_fail": "healer_evidence_review_required",
    }[scaffold_class]


def _expected_positional_arities(prompt: str, entry_point: str) -> set[int]:
    arities: set[int] = set()
    for line in prompt.splitlines():
        if "assert " not in line:
            continue
        try:
            tree = ast.parse(line.strip())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == entry_point
                and not node.keywords
            ):
                arities.add(len(node.args))
    _require(bool(arities), f"{entry_point}: no model-visible positional call arity")
    return arities


def _accepts_positional_arity(function: ast.FunctionDef | ast.AsyncFunctionDef, arity: int) -> bool:
    arguments = function.args
    positional = len(arguments.posonlyargs) + len(arguments.args)
    required = positional - len(arguments.defaults)
    required_keyword_only = sum(default is None for default in arguments.kw_defaults)
    return (
        required_keyword_only == 0
        and arity >= required
        and (arguments.vararg is not None or arity <= positional)
    )


def _top_level_functions(source: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(source)
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _signature_for_failure(
    census_row: dict[str, str],
    pipeline: dict[str, Any],
    task: dict[str, str],
) -> str:
    category = census_row["failure_category"]
    if category == "extraction_or_format_failure":
        if pipeline["extraction_method"] == "fenced_python":
            return "extraction_ambiguous_multiple_python_fences"
        return "extraction_ambiguous_other_fences"

    source = pipeline["pipeline_corrected_output"]
    _require(isinstance(source, str), f"{census_row['cell_id']}: extracted source missing")
    if category == "syntax_failure":
        try:
            ast.parse(source)
        except SyntaxError as exc:
            if exc.msg.startswith("f-string"):
                return "syntax_fstring_parse_error"
            if "unterminated string literal" in exc.msg:
                return "syntax_unterminated_string"
            return "syntax_invalid_plain_text"
        raise milestone_1c.CensusIntegrityError("syntax census row parsed successfully")

    functions = _top_level_functions(source)
    if category == "missing_or_wrong_entry_point":
        arities = _expected_positional_arities(task["prompt"], task["entry_point"])
        compatible = (
            len(functions) == 1
            and all(_accepts_positional_arity(functions[0], arity) for arity in arities)
        )
        return (
            "entrypoint_unique_arity_compatible_candidate"
            if compatible
            else "entrypoint_no_unique_candidate"
        )

    if category == "unknown":
        return (
            "unknown_eval_failure_multiple_top_level_functions"
            if len(functions) > 1
            else "unknown_eval_failure_single_top_level_function"
        )
    raise milestone_1c.CensusIntegrityError(f"unsupported Milestone 1C category: {category}")


SIGNATURE_METADATA = {
    "extraction_ambiguous_multiple_python_fences": {
        "action": "scaffold_only",
        "risk": "low",
        "do_not": "do not choose or merge competing fenced programs; do not count any extraction as Healer work",
        "evidence": "saved extraction is ambiguous via fenced_python and raw output contains multiple completed program segments",
    },
    "extraction_ambiguous_other_fences": {
        "action": "scaffold_only",
        "risk": "low",
        "do_not": "do not infer a Python payload from mixed or unbalanced non-Python fences",
        "evidence": "saved extraction is ambiguous via fenced_other",
    },
    "syntax_fstring_parse_error": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not rewrite an f-string unless intended interpolation and formatting semantics are independently established",
        "evidence": "AST parser reports a saved f-string syntax error; syntax failure alone is not safe repair evidence",
    },
    "syntax_unterminated_string": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not add a quote when the intended string boundary or truncated content is unknown",
        "evidence": "AST parser reports an unterminated string literal; the intended continuation is not saved",
    },
    "syntax_invalid_plain_text": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not delete leading text as a Healer edit without proving the remaining payload is the unique intended program",
        "evidence": "plain_text extraction and AST parser invalid-syntax outcome are saved; semantic repair is unverified",
    },
    "entrypoint_unique_arity_compatible_candidate": {
        "action": "healer_candidate",
        "risk": "high",
        "do_not": "do not rename or alias when multiple candidate functions exist, positional arity is incompatible, a name conflicts, or any body/control-flow rewrite would be required",
        "evidence": "expected entry point is absent; exactly one top-level function exists and accepts every model-visible positional call arity; candidate action is alias/name-only with no body rewrite",
    },
    "entrypoint_no_unique_candidate": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not synthesize an entry point when there is no unique arity-compatible top-level function",
        "evidence": "expected entry point is absent and the unique arity-compatible candidate requirement is not met",
    },
    "unknown_eval_failure_single_top_level_function": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not repair from a generic evaluator failure; saved evidence does not distinguish assertion failure, import/name error, or runtime exception",
        "evidence": "compile passes and expected entry point exists, but saved EvalPlus outcome is generic failure with one top-level function",
    },
    "unknown_eval_failure_multiple_top_level_functions": {
        "action": "manual_review",
        "risk": "high",
        "do_not": "do not delete, merge, or select functions based on evaluator failure; control-flow and binding intent are unresolved",
        "evidence": "compile passes and expected entry point exists, but saved EvalPlus outcome is generic failure with multiple top-level functions",
    },
}


def build_packets(
    repo_root: Path = REPO_ROOT,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    repo_root = repo_root.resolve()
    run_dir = repo_root / RUN_RELATIVE
    m1c_dir = repo_root / M1C_RELATIVE

    actual_m1c_hashes = {
        name: _sha256_bytes((m1c_dir / name).read_bytes()) for name in EXPECTED_M1C_HASHES
    }
    _require(actual_m1c_hashes == EXPECTED_M1C_HASHES, "Milestone 1C artifact hash mismatch")
    m1c_rows, m1c_manifest = milestone_1c.build_census(repo_root)
    committed_m1c_rows = _read_csv(m1c_dir / "failure_census.csv")
    _require(m1c_rows == committed_m1c_rows, "Milestone 1C CSV does not match its builder")
    _require(len(m1c_rows) == 70, "Milestone 1C failure count mismatch")

    plan = json.loads((run_dir / "generation_plan.json").read_text(encoding="utf-8"))
    raw_rows = _read_jsonl(run_dir / "raw_generations.jsonl")
    pipeline_rows = _read_jsonl(run_dir / "pipeline_corrected.jsonl")
    evaluation_rows = _read_csv(run_dir / "evaluation_results.csv")
    raw_by_id = {row["generation_id"]: row for row in raw_rows}
    pipeline_by_id = {row["generation_id"]: row for row in pipeline_rows}
    evaluation_by_id = {row["generation_id"]: row for row in evaluation_rows}
    _require(len(raw_by_id) == len(pipeline_by_id) == len(evaluation_by_id) == 100, "100-cell account mismatch")
    _require(set(raw_by_id) == set(pipeline_by_id) == set(evaluation_by_id), "cell identifiers differ across accounts")
    tasks = _load_active_tasks(repo_root, plan["task_ids"])

    scaffold_rows: list[dict[str, str]] = []
    for raw in raw_rows:
        cell_id = raw["generation_id"]
        pipeline = pipeline_by_id[cell_id]
        evaluation = evaluation_by_id[cell_id]
        features = _raw_features(raw)
        scaffold_class = _scaffold_class(evaluation, pipeline)
        evidence = (
            f"saved done_reason={raw['generation_metadata']['done_reason']}; "
            f"fence_markers={features['marker_count']}; completed_blocks={features['block_count']}; "
            f"raw_compile={features['compile_status']}; extraction={pipeline['extraction_status']}:{pipeline['extraction_method']}"
        )
        scaffold_rows.append(
            {
                "task_id": raw["task_id"],
                "seed": str(raw["seed"]),
                "cell_id": cell_id,
                "raw_generation_sha256": raw["raw_response_sha256"],
                "pipeline_program_sha256": pipeline["pipeline_corrected_output_sha256"] or "",
                "raw_protocol_compliance": "compliant" if features["compliant"] else "noncompliant",
                "raw_protocol_violations": "|".join(features["violations"]),
                "code_fence_marker_count": str(features["marker_count"]),
                "completed_fenced_block_count": str(features["block_count"]),
                "python_fenced_block_count": str(features["python_blocks"]),
                "extra_text_outside_fences": str(features["extra_text"]).lower(),
                "empty_output": str(features["empty"]).lower(),
                "multiple_program_segments": str(features["multiple"]).lower(),
                "generation_truncated": str(features["truncated"]).lower(),
                "raw_python_compile_status": features["compile_status"],
                "pipeline_extraction_action": _pipeline_action(pipeline),
                "observed_status": evaluation["observed_status"],
                "pipeline_status": evaluation["pipeline_corrected_status"],
                "scaffold_evidence_class": scaffold_class,
                "scaffold_constraint_candidate": _scaffold_constraints(features, pipeline),
                "evidence_basis": evidence,
                "review_status": _review_status(scaffold_class),
            }
        )

    scaffold_counts = Counter(row["scaffold_evidence_class"] for row in scaffold_rows)
    _require(len(scaffold_rows) == 100, "Scaffold ledger must contain 100 rows")
    _require(
        scaffold_counts
        == {
            "verified_pipeline_rescue": 30,
            "pipeline_extraction_failure": 21,
            "pipeline_extracted_evaluation_fail": 49,
        },
        "Scaffold evidence partition mismatch",
    )

    failure_by_signature: dict[str, list[dict[str, str]]] = defaultdict(list)
    for census_row in m1c_rows:
        cell_id = census_row["cell_id"]
        signature = _signature_for_failure(
            census_row, pipeline_by_id[cell_id], tasks[census_row["task_id"]]
        )
        failure_by_signature[signature].append(census_row)
    _require(set(failure_by_signature) == set(SIGNATURE_ORDER), "failure signature set mismatch")

    cluster_rows: list[dict[str, str]] = []
    for signature in SIGNATURE_ORDER:
        cells = failure_by_signature[signature]
        category = cells[0]["failure_category"]
        metadata = SIGNATURE_METADATA[signature]
        positives = [row["cell_id"] for row in cells[:5]]
        counterexamples = [
            row["cell_id"]
            for other_signature in SIGNATURE_ORDER
            if other_signature != signature
            for row in failure_by_signature[other_signature]
            if row["failure_category"] == category
        ][:3]
        cluster_rows.append(
            {
                "signature_id": signature,
                "category": category,
                "cell_count": str(len(cells)),
                "unique_task_count": str(len({row["task_id"] for row in cells})),
                "representative_cell_ids": "|".join(row["cell_id"] for row in cells[:3]),
                "proposed_action": metadata["action"],
                "semantic_risk": metadata["risk"],
                "positive_examples": "|".join(positives),
                "counterexamples": "|".join(counterexamples),
                "do_not_repair_conditions": metadata["do_not"],
                "classification_evidence": metadata["evidence"],
            }
        )

    _require(sum(int(row["cell_count"]) for row in cluster_rows) == 70, "Healer review cell total mismatch")
    _require(
        len({row["task_id"] for rows in failure_by_signature.values() for row in rows}) == 19,
        "Healer review unique task total mismatch",
    )
    action_counts: Counter[str] = Counter()
    for cluster in cluster_rows:
        action_counts[cluster["proposed_action"]] += int(cluster["cell_count"])
    category_counts = Counter(row["failure_category"] for row in m1c_rows)
    manifest = {
        "packet_version": "milestone_1d_v1",
        "run_id": plan["run_id"],
        "scope": "MBPP+ frozen active development subset only",
        "scaffold_ledger_cells": 100,
        "scaffold_partition": dict(sorted(scaffold_counts.items())),
        "healer_review_cells": 70,
        "healer_review_unique_tasks": 19,
        "failure_category_counts": dict(sorted(category_counts.items())),
        "failure_signature_count": len(cluster_rows),
        "proposed_action_cell_counts": dict(sorted(action_counts.items())),
        "pipeline_rescues": 30,
        "pipeline_rescues_are_healer_effect": False,
        "candidate_labels_are_verified_rules": False,
        "m1c_sources": {
            name: {"path": (M1C_RELATIVE / name).as_posix(), "sha256": digest}
            for name, digest in actual_m1c_hashes.items()
        },
        "run_sources": m1c_manifest["source_artifacts"],
        "protocol": m1c_manifest["protocol"],
        "frozen_split": m1c_manifest["frozen_split"],
    }
    return scaffold_rows, cluster_rows, manifest


def _render_csv(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def render_scaffold_ledger(rows: list[dict[str, str]]) -> bytes:
    return _render_csv(rows, SCAFFOLD_FIELDS)


def render_clusters(rows: list[dict[str, str]]) -> bytes:
    return _render_csv(rows, CLUSTER_FIELDS)


def render_manifest(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_human_review_packet(
    clusters: list[dict[str, str]], manifest: dict[str, Any]
) -> bytes:
    lines = [
        "# Milestone 1D: Scaffold / Healer evidence review packet",
        "",
        "## Scope and accounting",
        "",
        "- Scope: frozen MBPP+ active development subset (20 tasks), run `mbpp_qwen35_9b_ab1_dev_run_003` only.",
        "- Scaffold ledger: 100 generation cells.",
        "- Verified Pipeline rescues: 30 Observed-fail / Pipeline-pass cells.",
        "- Pipeline extraction failures: 21 cells.",
        "- Pipeline-extracted / evaluation-fail: 49 cells.",
        "- Healer evidence review: 70 Pipeline-fail cells across 19 tasks.",
        "",
        "The 30 rescues are verified Pipeline correction outcomes, not Healer outcomes. No generation, evaluation, Scaffold construction, Healer construction, or evaluator-guided program edit was performed.",
        "",
        "## Failure signature clusters",
        "",
        "| Signature | Category | Cells | Tasks | Proposed action | Risk |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in clusters:
        lines.append(
            f"| `{row['signature_id']}` | `{row['category']}` | {row['cell_count']} | "
            f"{row['unique_task_count']} | `{row['proposed_action']}` | `{row['semantic_risk']}` |"
        )
    lines.extend(
        [
            "",
            "## Human decisions required",
            "",
            "Syntax errors remain manual-review items: a parse error does not establish a semantically safe edit. Entry-point cells are Healer candidates only when one top-level function exists, every model-visible positional call arity is accepted, and the proposed operation is name/alias-only without a function-body or control-flow rewrite.",
            "",
        ]
    )
    for row in clusters:
        if row["proposed_action"] != "manual_review":
            continue
        lines.extend(
            [
                f"### `{row['signature_id']}`",
                "",
                f"- Cells: {row['cell_count']}; unique tasks: {row['unique_task_count']}",
                f"- Evidence: {row['classification_evidence']}",
                f"- Do not repair: {row['do_not_repair_conditions']}",
                f"- Representative cells: `{row['representative_cell_ids'].replace('|', '`, `')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Candidate interpretation",
            "",
            f"- `scaffold_only`: {manifest['proposed_action_cell_counts'].get('scaffold_only', 0)} cells",
            f"- `healer_candidate`: {manifest['proposed_action_cell_counts'].get('healer_candidate', 0)} cells",
            f"- `manual_review`: {manifest['proposed_action_cell_counts'].get('manual_review', 0)} cells",
            "",
            "Scaffold and Healer candidate labels are separate evidence annotations and may overlap conceptually. Neither label is a validated rule or authorization to modify a program.",
            "",
            "Unknown evaluator failures default to manual review because saved diagnostics do not distinguish functional assertion failure, import/name failure, or runtime exception. Evaluator outcomes were not used to rewrite any program.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def render_summary(manifest: dict[str, Any]) -> bytes:
    lines = [
        "# Milestone 1D evidence summary",
        "",
        "- Scaffold ledger rows: 100",
        "- Verified Pipeline rescues: 30",
        "- Pipeline extraction failures: 21",
        "- Pipeline extracted / evaluation fail: 49",
        "- Healer review cells: 70",
        "- Healer review unique tasks: 19",
        f"- Failure signature clusters: {manifest['failure_signature_count']}",
        f"- Scaffold-only cells: {manifest['proposed_action_cell_counts'].get('scaffold_only', 0)}",
        f"- Healer-candidate cells: {manifest['proposed_action_cell_counts'].get('healer_candidate', 0)}",
        f"- Manual-review cells: {manifest['proposed_action_cell_counts'].get('manual_review', 0)}",
        "",
        "Pipeline correction and Healer evidence are accounted separately. Candidate labels are not verified repair rules.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def write_outputs(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    scaffold_rows, clusters, manifest = build_packets(repo_root)
    rendered = {
        "scaffold_evidence_ledger.csv": render_scaffold_ledger(scaffold_rows),
        "failure_signature_clusters.csv": render_clusters(clusters),
        "human_review_packet.md": render_human_review_packet(clusters, manifest),
        "evidence_manifest.json": render_manifest(manifest),
        "evidence_summary.md": render_summary(manifest),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (output_dir / name).write_bytes(content)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir or repo_root / OUTPUT_RELATIVE
    manifest = write_outputs(repo_root, output_dir)
    print(json.dumps({"output_dir": str(output_dir), **manifest}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
