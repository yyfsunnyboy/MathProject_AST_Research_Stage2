#!/usr/bin/env python3
"""Fixed roster + deterministic machine census for remaining 171 taxonomy-v3 cells.

MACHINE_CENSUS_NOT_TAXONOMY_ADJUDICATION

Population (frozen, unique):
  unresolved 198 (classification_preparation / coarse_diagnostics)
  − G2_module 27 (phase == G2_module)
  = remaining 171

Does not use H1 results for sampling, does not include P0, does not emit
primary/secondary taxonomy layers or Healer eligibility decisions.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1"
)
START_HEAD = "047bf3735c7cd34f3f1826c7a9b49a42603ddb5d"
STATUS = "MACHINE_CENSUS_NOT_TAXONOMY_ADJUDICATION"
ANALYZER = Path("scripts/prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1.py")
TESTS = Path(
    "tests/finals_rebuild/test_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1.py"
)

PREPARATION_CSV = preparation.OUTPUT_RELATIVE / "classification_preparation.csv"
PREPARATION_MANIFEST = preparation.OUTPUT_RELATIVE / "manifest.json"
PREPARATION_CSV_SHA256 = "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c"
PREPARATION_MANIFEST_SHA256 = "6c6aa8482348b5aa30d9809d3ba1e4c31e3d16a00a8e2e5b9c8ab723d2d7a142"
G2_PROVISIONAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
G2_PROVISIONAL_CSV_SHA256 = (
    "90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119"
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.FORMAL_RESULTS: preparation.SOURCE_HASHES[preparation.FORMAL_RESULTS],
    preparation.FORMAL_RECEIPT: preparation.SOURCE_HASHES[preparation.FORMAL_RECEIPT],
    PREPARATION_CSV: PREPARATION_CSV_SHA256,
    PREPARATION_MANIFEST: PREPARATION_MANIFEST_SHA256,
    G2_PROVISIONAL_CSV: G2_PROVISIONAL_CSV_SHA256,
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
}

STDLIB = set(sys.stdlib_module_names)

ROSTER_FIELDS = (
    "roster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "condition_account",
    "required_entry_point",
    "frozen_source_path",
    "frozen_source_sha256",
    "evaluation_source_sha256",
    "original_diagnostic_phase",
    "original_diagnostic_exception_class",
    "original_termination",
    "original_outcome_validity",
    "inclusion_reason",
    "exclusion_from_g2_27",
    "source_provenance",
)

EXCLUDED_FIELDS = (
    "exclude_rank",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "diagnostic_phase",
    "exclusion_reason",
    "g2_provisional_review_rank",
)

RECONCILE_FIELDS = (
    "metric",
    "value",
    "definition",
)

CENSUS_FIELDS = (
    "roster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "required_entry_point",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "diagnostic_candidate_line",
    "diagnostic_model_source_ast_node",
    "termination",
    "ipc_status",
    "child_exit_bucket",
    "return_type_bucket",
    "return_shape_bucket",
    "frozen_g1_parse",
    "frozen_g2_execution",
    "frozen_g3e_entry_point",
    "frozen_outcome_validity",
    "diagnostic_evidence_validity",
    "parse_success",
    "compile_success",
    "parse_error_type",
    "entry_point_def_count",
    "entry_point_present",
    "entry_point_ambiguous",
    "required_signature_arity_visible",
    "module_level_executable_node_types",
    "module_level_executable_count",
    "import_modules",
    "import_classification",
    "import_has_stdlib",
    "import_has_third_party_or_local",
    "nameerror_exception_signal",
    "import_or_name_resolution_signal",
    "module_execution_exception_signal",
    "timeout_or_nontermination_signal",
    "completed_return_signal",
    "output_or_contract_shape_signal",
    "truncation_mechanism_candidate",
    "packaging_or_scaffold_residue_signal",
    "traceback_in_frozen_diagnostics",
    "stdout_stderr_in_frozen_diagnostics",
    "hidden_expected_actual_used",
    "h1_result_used_for_sampling",
    "all_observed_machine_signals",
    "operational_cluster",
    "cluster_is_not_taxonomy_layer",
    "primary_failure_layer",
    "secondary_failure_layers",
    "healer_eligibility",
)

CLUSTER_ORDER = (
    "parse_or_compile_signal",
    "missing_or_ambiguous_entry_point_signal",
    "import_or_name_resolution_signal",
    "module_execution_exception_signal",
    "timeout_or_nontermination_signal",
    "test_execution_failure_signal",
    "output_or_contract_shape_signal",
    "no_decisive_machine_signal",
    "multiple_signal_chain",
)


class CensusError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CensusError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for relative, digest in SOURCE_HASHES.items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _root_module(name: str) -> str:
    return name.split(":", 1)[0].split(".", 1)[0]


def _classify_imports(modules: list[str]) -> tuple[str, bool, bool]:
    if not modules:
        return "NONE", False, False
    labels: list[str] = []
    has_stdlib = False
    has_third = False
    for module in modules:
        root = _root_module(module)
        if root in STDLIB:
            labels.append(f"{module}:STDLIB")
            has_stdlib = True
        else:
            labels.append(f"{module}:THIRD_PARTY_OR_LOCAL")
            has_third = True
    return ";".join(labels), has_stdlib, has_third


def _source_features(source: str, entry_point: str) -> dict[str, Any]:
    features: dict[str, Any] = {
        "parse_success": "false",
        "compile_success": "false",
        "parse_error_type": "",
        "entry_point_def_count": "0",
        "entry_point_present": "false",
        "entry_point_ambiguous": "false",
        "required_signature_arity_visible": "",
        "module_level_executable_node_types": "[]",
        "module_level_executable_count": "0",
        "import_modules": "[]",
        "import_classification": "NONE",
        "import_has_stdlib": "false",
        "import_has_third_party_or_local": "false",
        "truncation_mechanism_candidate": "false",
        "packaging_or_scaffold_residue_signal": "false",
    }
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        features["parse_error_type"] = type(exc).__name__
        features["truncation_mechanism_candidate"] = str(
            "truncated" in (exc.msg or "").lower() or source.rstrip().endswith((":", "\\", "("))
        ).lower()
        return features

    features["parse_success"] = "true"
    features["compile_success"] = "true"

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module or ''}:{','.join(alias.name for alias in node.names)}")
    imports = sorted(set(imports))
    classification, has_stdlib, has_third = _classify_imports(imports)
    features["import_modules"] = _compact(imports)
    features["import_classification"] = classification
    features["import_has_stdlib"] = str(has_stdlib).lower()
    features["import_has_third_party_or_local"] = str(has_third).lower()

    defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
    ]
    features["entry_point_def_count"] = str(len(defs))
    features["entry_point_present"] = str(bool(defs)).lower()
    features["entry_point_ambiguous"] = str(len(defs) > 1).lower()
    if len(defs) == 1:
        features["required_signature_arity_visible"] = str(
            len(defs[0].args.args) + len(defs[0].args.posonlyargs)
        )

    module_nodes = [
        type(node).__name__
        for node in tree.body
        if not isinstance(
            node,
            (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        )
    ]
    features["module_level_executable_node_types"] = _compact(module_nodes)
    features["module_level_executable_count"] = str(len(module_nodes))

    scaffold_tokens = ("if __name__", "print(", "# Example", "# Test", "All tests passed")
    features["packaging_or_scaffold_residue_signal"] = str(
        any(token in source for token in scaffold_tokens) or bool(module_nodes)
    ).lower()
    features["truncation_mechanism_candidate"] = "false"
    return features


def _assign_cluster(signals: list[str]) -> str:
    decisive = [name for name in signals if name != "packaging_or_scaffold_residue_signal"]
    if len(decisive) > 1:
        return "multiple_signal_chain"
    if decisive:
        mapping = {
            "parse_or_compile_signal": "parse_or_compile_signal",
            "missing_or_ambiguous_entry_point_signal": "missing_or_ambiguous_entry_point_signal",
            "import_or_name_resolution_signal": "import_or_name_resolution_signal",
            "module_execution_exception_signal": "module_execution_exception_signal",
            "timeout_or_nontermination_signal": "timeout_or_nontermination_signal",
            "test_execution_failure_signal": "test_execution_failure_signal",
            "output_or_contract_shape_signal": "output_or_contract_shape_signal",
        }
        return mapping.get(decisive[0], "no_decisive_machine_signal")
    return "no_decisive_machine_signal"


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    prep_rows = _read_csv(repo / PREPARATION_CSV)
    diagnostics = _read_csv(repo / preparation.FORMAL_RESULTS)
    g2_rows = _read_csv(repo / G2_PROVISIONAL_CSV)
    tasks = {row["task_id"]: row for row in _read_jsonl(repo / preparation.TASKS)}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }

    _require(len(prep_rows) == 198, "preparation row count drift")
    _require(len(diagnostics) == 198, "diagnostics row count drift")
    _require(len(g2_rows) == 27, "G2 provisional row count drift")
    _require(len({row["program_id"] for row in prep_rows}) == 198, "preparation program uniqueness drift")
    _require(
        len({row["cell_identity_sha256"] for row in prep_rows}) == 198,
        "preparation cell uniqueness drift",
    )

    diag_by_program = {row["program_id"]: row for row in diagnostics}
    g2_by_program = {row["program_id"]: row for row in g2_rows}
    g2_from_prep = [row for row in prep_rows if row["diagnostic_phase"] == "G2_module"]
    remaining = [row for row in prep_rows if row["diagnostic_phase"] != "G2_module"]
    _require(len(g2_from_prep) == 27, "G2_module count drift in preparation")
    _require(len(remaining) == 171, "remaining171 count drift")
    _require(set(g2_by_program) == {row["program_id"] for row in g2_from_prep}, "G2 identity set drift")
    _require(
        not ({row["program_id"] for row in remaining} & set(g2_by_program)),
        "remaining ∩ G2 must be empty",
    )
    _require(len(remaining) + len(g2_from_prep) == 198, "198 != 27 + 171")

    # Sort remaining deterministically by program_id.
    remaining_sorted = sorted(remaining, key=lambda row: row["program_id"])
    excluded_sorted = sorted(g2_from_prep, key=lambda row: row["program_id"])

    excluded_ledger: list[dict[str, str]] = []
    for rank, row in enumerate(excluded_sorted, 1):
        g2 = g2_by_program[row["program_id"]]
        excluded_ledger.append(
            {
                "exclude_rank": str(rank),
                "program_id": row["program_id"],
                "cell_identity_sha256": row["cell_identity_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "diagnostic_phase": "G2_module",
                "exclusion_reason": "phase==G2_module_frozen_out_of_remaining171",
                "g2_provisional_review_rank": g2["review_rank"],
            }
        )

    roster: list[dict[str, str]] = []
    census: list[dict[str, str]] = []
    unresolved_issues: list[dict[str, str]] = []

    for rank, row in enumerate(remaining_sorted, 1):
        program_id = row["program_id"]
        diagnostic = diag_by_program[program_id]
        _require(
            diagnostic["cell_identity_sha256"] == row["cell_identity_sha256"],
            f"cell identity drift: {program_id}",
        )
        _require(diagnostic["phase"] == row["diagnostic_phase"], f"phase drift: {program_id}")
        journal = journals.get(program_id)
        task = tasks.get(row["task_id"])
        if journal is None or task is None:
            unresolved_issues.append(
                {
                    "program_id": program_id,
                    "cell_identity_sha256": row["cell_identity_sha256"],
                    "issue": "missing_journal_or_task",
                }
            )
            continue
        _require(
            journal["evaluation_source_sha256"] == row["evaluation_source_sha256"],
            f"journal source sha drift: {program_id}",
        )
        source = journal["evaluation_source"]
        _require(
            _sha(source.encode("utf-8")) == row["evaluation_source_sha256"],
            f"source bytes sha drift: {program_id}",
        )
        entry_point = str(task["entry_point"])
        features = _source_features(source, entry_point)

        phase = row["diagnostic_phase"]
        exc = row["diagnostic_exception_class"]
        termination = row["termination"]
        nameerror = exc == "NameError"
        import_signal = nameerror or exc in {"ImportError", "ModuleNotFoundError"}
        module_exc = phase in {"G2_base", "G2_plus"} and termination == "raised"
        timeout = termination in {"timeout", "nontermination", "killed"}
        completed_return = phase == "completed" and termination == "returned"
        output_shape = completed_return and bool(row["return_type_bucket"] or row["return_shape_bucket"])
        missing_entry = features["entry_point_present"] == "false" or features["entry_point_ambiguous"] == "true"
        parse_fail = features["parse_success"] == "false"

        observed: list[str] = []
        if parse_fail:
            observed.append("parse_or_compile_signal")
        if missing_entry:
            observed.append("missing_or_ambiguous_entry_point_signal")
        if import_signal:
            observed.append("import_or_name_resolution_signal")
        if module_exc:
            observed.append("module_execution_exception_signal")
        if timeout:
            observed.append("timeout_or_nontermination_signal")
        if completed_return:
            # Unresolved cell that completed module/entry execution: operational test/outcome track.
            observed.append("test_execution_failure_signal")
        if output_shape and not completed_return:
            observed.append("output_or_contract_shape_signal")
        elif output_shape and completed_return:
            # Keep as secondary observed tag inside all_observed list only via explicit flag below.
            pass
        if features["packaging_or_scaffold_residue_signal"] == "true":
            observed.append("packaging_or_scaffold_residue_signal")

        # Infrastructure rows: no decisive runtime taxonomy signal.
        if row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE":
            observed = ["no_decisive_machine_signal"]

        # Refine exclusive cluster for completed cells with output shape interest.
        cluster_signals = [name for name in observed if name != "packaging_or_scaffold_residue_signal"]
        if (
            completed_return
            and output_shape
            and cluster_signals == ["test_execution_failure_signal"]
        ):
            # Prefer output/contract shape queue when a return shape was observed.
            cluster_signals = ["output_or_contract_shape_signal"]
            observed = [
                "output_or_contract_shape_signal"
                if name == "test_execution_failure_signal"
                else name
                for name in observed
            ]

        if row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE":
            cluster = "no_decisive_machine_signal"
        else:
            cluster = _assign_cluster(cluster_signals)

        roster.append(
            {
                "roster_rank": str(rank),
                "program_id": program_id,
                "cell_identity_sha256": row["cell_identity_sha256"],
                "task_identity_sha256": row["task_identity_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "generation_id": row["generation_id"],
                "condition_account": "Candidate_B/H0",
                "required_entry_point": entry_point,
                "frozen_source_path": (
                    f"{preparation.JOURNAL.as_posix()}#program_id={program_id};healer_account=H0"
                ),
                "frozen_source_sha256": row["evaluation_source_sha256"],
                "evaluation_source_sha256": row["evaluation_source_sha256"],
                "original_diagnostic_phase": phase,
                "original_diagnostic_exception_class": exc,
                "original_termination": termination,
                "original_outcome_validity": row["outcome_validity"],
                "inclusion_reason": "taxonomy_v3_unresolved198_minus_G2_module",
                "exclusion_from_g2_27": "true",
                "source_provenance": (
                    f"{PREPARATION_CSV.as_posix()}#program_id={program_id};"
                    f"{preparation.FORMAL_RESULTS.as_posix()}#cell_identity_sha256={row['cell_identity_sha256']}"
                ),
            }
        )

        census.append(
            {
                "roster_rank": str(rank),
                "program_id": program_id,
                "cell_identity_sha256": row["cell_identity_sha256"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "required_entry_point": entry_point,
                "diagnostic_phase": phase,
                "diagnostic_exception_class": exc,
                "diagnostic_candidate_line": diagnostic.get("model_source_line", ""),
                "diagnostic_model_source_ast_node": row["model_source_ast_node"],
                "termination": termination,
                "ipc_status": row["ipc_status"],
                "child_exit_bucket": row["child_exit_bucket"],
                "return_type_bucket": row["return_type_bucket"],
                "return_shape_bucket": row["return_shape_bucket"],
                "frozen_g1_parse": row["g1_parse"],
                "frozen_g2_execution": row["g2_execution"],
                "frozen_g3e_entry_point": row["g3e_entry_point"],
                "frozen_outcome_validity": row["outcome_validity"],
                "diagnostic_evidence_validity": row["diagnostic_evidence_validity"],
                **features,
                "nameerror_exception_signal": str(nameerror).lower(),
                "import_or_name_resolution_signal": str(import_signal).lower(),
                "module_execution_exception_signal": str(module_exc).lower(),
                "timeout_or_nontermination_signal": str(timeout).lower(),
                "completed_return_signal": str(completed_return).lower(),
                "output_or_contract_shape_signal": str(
                    "output_or_contract_shape_signal" in observed
                ).lower(),
                "traceback_in_frozen_diagnostics": "NOT_PRESENT_IN_FROZEN_COARSE_DIAGNOSTICS",
                "stdout_stderr_in_frozen_diagnostics": "NOT_PRESENT_IN_FROZEN_COARSE_DIAGNOSTICS",
                "hidden_expected_actual_used": "false",
                "h1_result_used_for_sampling": "false",
                "all_observed_machine_signals": _compact(observed),
                "operational_cluster": cluster,
                "cluster_is_not_taxonomy_layer": "true",
                "primary_failure_layer": "",
                "secondary_failure_layers": "",
                "healer_eligibility": "",
            }
        )

    _require(len(roster) == 171, f"roster size drift: {len(roster)}")
    _require(len(census) == 171, f"census size drift: {len(census)}")
    _require(not unresolved_issues, f"identity/source issues: {unresolved_issues}")
    _require(
        [row["roster_rank"] for row in roster] == [str(i) for i in range(1, 172)],
        "roster_rank not contiguous",
    )
    _require(
        [row["program_id"] for row in roster] == sorted(row["program_id"] for row in roster),
        "roster not sorted by program_id",
    )

    signal_counter: Counter[str] = Counter()
    for row in census:
        for signal in json.loads(row["all_observed_machine_signals"]):
            signal_counter[signal] += 1
    cluster_counter = Counter(row["operational_cluster"] for row in census)
    _require(set(cluster_counter) <= set(CLUSTER_ORDER), "unknown cluster label")

    phase_counter = Counter(row["diagnostic_phase"] for row in census)
    evidence_flags = {
        "cells": 171,
        "hidden_expected_actual_used": 0,
        "h1_result_used_for_sampling": 0,
        "traceback_present_in_frozen_diagnostics": 0,
        "stdout_stderr_present_in_frozen_diagnostics": 0,
        "source_bytes_verified": 171,
        "entry_point_present": sum(row["entry_point_present"] == "true" for row in census),
        "parse_success": sum(row["parse_success"] == "true" for row in census),
        "third_party_or_local_import_cells": sum(
            row["import_has_third_party_or_local"] == "true" for row in census
        ),
        "invalid_infrastructure_cells": sum(
            row["diagnostic_evidence_validity"] == "INVALID_INFRASTRUCTURE" for row in census
        ),
    }

    return {
        "roster": roster,
        "excluded": excluded_ledger,
        "census": census,
        "unresolved_issues": unresolved_issues,
        "signal_counter": signal_counter,
        "cluster_counter": cluster_counter,
        "phase_counter": phase_counter,
        "evidence_flags": evidence_flags,
    }


def _methodology_report(analysis: dict[str, Any]) -> str:
    clusters = analysis["cluster_counter"]
    signals = analysis["signal_counter"]
    phases = analysis["phase_counter"]
    lines = [
        "# Candidate B r003 taxonomy v3：remaining171 machine census v1",
        "",
        f"**明確聲明：`{STATUS}`**",
        "",
        "本 revision 只建立不可變 fixed roster 與 deterministic machine census／operational clusters。",
        "**尚未**完成 L0–L5 逐格裁決；cluster **不是** failure taxonomy；**尚未**判定 Healer eligibility。",
        "未使用 hidden expected／actual，未使用 H1 結果選樣或反推，未進行 correctness 重評。",
        "",
        "## 母體裁定",
        "",
        "- 正式母體：taxonomy v3 unresolved **198**",
        "  （`classification_preparation.csv` ≡ `coarse_diagnostics.csv`）",
        "- 排除：`phase == G2_module` → **27**",
        "- remaining fixed roster：**171**",
        "- 開合：`198 = 27 + 171`",
        "- 不納入 P0；不使用 H1 結果選樣；僅採用 unresolved198−G2_module=remaining171",
        "",
        "## Phase 分布（171）",
        "",
        "| Phase | Cells |",
        "|---|---:|",
    ]
    for key, value in sorted(phases.items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Observed machine signals（非互斥）",
            "",
            "| Signal | Cells |",
            "|---|---:|",
        ]
    )
    for key, value in sorted(signals.items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Operational clusters（互斥工作佇列）",
            "",
            "| Cluster | Cells |",
            "|---|---:|",
        ]
    )
    for key in CLUSTER_ORDER:
        lines.append(f"| `{key}` | {clusters.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## 方法學邊界",
            "",
            "- `primary_failure_layer`／`secondary_failure_layers`／`healer_eligibility` 欄位保留空白",
            "- exception class／phase 不直接等同 taxonomy layer",
            "- truncation 僅為 mechanism candidate",
            "- import 區分 STDLIB 與 THIRD_PARTY_OR_LOCAL，不自動等同 Domain API",
            "- 不執行模型、EvalPlus、diagnostics、validation、Healer",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    reconcile = [
        {
            "metric": "formal_unresolved_population",
            "value": "198",
            "definition": "classification_preparation.csv rows == coarse_diagnostics.csv rows",
        },
        {
            "metric": "excluded_g2_module",
            "value": "27",
            "definition": 'diagnostic_phase == "G2_module"',
        },
        {
            "metric": "remaining_fixed_roster",
            "value": "171",
            "definition": "198 - 27",
        },
        {
            "metric": "reconciliation_identity",
            "value": "198=27+171",
            "definition": "excluded ∪ remaining = unresolved198; intersection empty",
        },
        {
            "metric": "p0_included",
            "value": "0",
            "definition": "Candidate_B taxonomy scope only",
        },
        {
            "metric": "h1_used_for_sampling",
            "value": "0",
            "definition": "H0 frozen sources only for source-feature extraction",
        },
    ]
    signal_summary = [
        {"machine_signal": key, "cells": str(value)}
        for key, value in sorted(analysis["signal_counter"].items())
    ]
    cluster_summary = [
        {"operational_cluster": key, "cells": str(analysis["cluster_counter"].get(key, 0))}
        for key in CLUSTER_ORDER
    ]
    cluster_detail = [
        {
            "roster_rank": row["roster_rank"],
            "program_id": row["program_id"],
            "task_id": row["task_id"],
            "seed": row["seed"],
            "diagnostic_phase": row["diagnostic_phase"],
            "operational_cluster": row["operational_cluster"],
            "all_observed_machine_signals": row["all_observed_machine_signals"],
        }
        for row in analysis["census"]
    ]
    evidence_summary = [
        {"flag": key, "value": str(value)}
        for key, value in sorted(analysis["evidence_flags"].items())
    ]
    source_ledger = [
        {"path": relative.as_posix(), "sha256": digest, "role": "FROZEN_INPUT"}
        for relative, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())
    ]

    provenance = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "taxonomy_adjudication_completed": False,
        "healer_eligibility_decided": False,
        "cluster_is_taxonomy_layer": False,
        "start_head": START_HEAD,
        "formal_population": 198,
        "excluded_g2_module": 27,
        "remaining_roster": 171,
        "reconciliation": "198=27+171",
        "p0_included": False,
        "h1_used_for_sampling": False,
        "hidden_expected_actual_used": False,
        "correctness_reevaluated": False,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "taxonomy_version": preparation.TAXONOMY_VERSION,
        "diagnostics_runner_revision": preparation.DIAGNOSTICS_RUNNER_REVISION,
    }
    execution_manifest = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "correctness_tests_executed": 0,
        "cells_rostered": 171,
        "cells_censused": 171,
    }

    outputs = {
        Path("fixed_roster.csv"): _csv_bytes(ROSTER_FIELDS, analysis["roster"]),
        Path("excluded_g2_27_identity_ledger.csv"): _csv_bytes(EXCLUDED_FIELDS, analysis["excluded"]),
        Path("population_reconciliation.csv"): _csv_bytes(RECONCILE_FIELDS, reconcile),
        Path("machine_census.csv"): _csv_bytes(CENSUS_FIELDS, analysis["census"]),
        Path("machine_signal_summary.csv"): _csv_bytes(
            ("machine_signal", "cells"), signal_summary
        ),
        Path("operational_cluster_summary.csv"): _csv_bytes(
            ("operational_cluster", "cells"), cluster_summary
        ),
        Path("operational_cluster_detail.csv"): _csv_bytes(
            (
                "roster_rank",
                "program_id",
                "task_id",
                "seed",
                "diagnostic_phase",
                "operational_cluster",
                "all_observed_machine_signals",
            ),
            cluster_detail,
        ),
        Path("evidence_availability_summary.csv"): _csv_bytes(
            ("flag", "value"), evidence_summary
        ),
        Path("unresolved_source_or_identity_issues.csv"): _csv_bytes(
            ("program_id", "cell_identity_sha256", "issue"),
            analysis["unresolved_issues"],
        ),
        Path("source_hash_ledger.csv"): _csv_bytes(
            ("path", "sha256", "role"), source_ledger
        ),
        Path("methodology_report_zh.md"): _methodology_report(analysis).encode("utf-8"),
        Path("provenance.json"): _json_bytes(provenance),
        Path("execution_manifest.json"): _json_bytes(execution_manifest),
    }
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    destination = repo / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output already exists: {destination}")
    destination.mkdir(parents=True)
    outputs = build_outputs(repo)
    hashes = {path.as_posix(): _sha(data) for path, data in outputs.items()}
    for path, data in outputs.items():
        (destination / path).write_bytes(data)
    manifest = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "taxonomy_adjudication_completed": False,
        "healer_eligibility_decided": False,
        "formal_population": 198,
        "excluded_g2_module": 27,
        "remaining_roster": 171,
        "reconciliation": "198=27+171",
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
    }
    (destination / "manifest.json").write_bytes(_json_bytes(manifest))
    return destination


def main() -> None:
    path = write_outputs()
    print(path)


if __name__ == "__main__":
    main()
