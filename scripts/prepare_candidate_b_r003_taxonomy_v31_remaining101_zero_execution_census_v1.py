#!/usr/bin/env python3
"""Zero-execution census + batch planning for remaining101 (taxonomy v3.1).

ZERO_EXECUTION_CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION

Population:
  formal preparation 198 − frozen97 = remaining101

Does not adjudicate taxonomy, does not decide Healer eligibility, does not
execute candidates, diagnostics, validation, EvalPlus, or models.
Does not rewrite frozen 97 cells or ingest v3.1 into repo governance.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import sys
import tokenize
from collections import Counter, defaultdict
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
    "candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1"
)
START_HEAD = "b5a425bd9fb3b698fd83a66e25b01b979feba96b"
STATUS = "ZERO_EXECUTION_CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION"
PLANNING_ONLY_MARK = "NON_ADJUDICATIVE_PLANNING_ONLY"
ANALYZER = Path(
    "scripts/prepare_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v31_remaining101_zero_execution_census_v1.py"
)

PREP_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1"
)
PREP_CSV = PREP_DIR / "classification_preparation.csv"
PREP_MANIFEST = PREP_DIR / "manifest.json"
PREP_CSV_SHA256 = "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c"
PREP_MANIFEST_SHA256 = "6c6aa8482348b5aa30d9809d3ba1e4c31e3d16a00a8e2e5b9c8ab723d2d7a142"

MACHINE_CENSUS_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1"
)
MACHINE_CENSUS_CSV = MACHINE_CENSUS_DIR / "machine_census.csv"
MACHINE_CENSUS_ROSTER = MACHINE_CENSUS_DIR / "fixed_roster.csv"
MACHINE_CENSUS_MANIFEST = MACHINE_CENSUS_DIR / "manifest.json"
MACHINE_CENSUS_CSV_SHA256 = "284802c8f1aeff92ad70f65b42c4aa7dabc252da592f8ad62011be71537f8a32"
MACHINE_CENSUS_ROSTER_SHA256 = "6e2c6e243fc6ff01c0b0fc2c6939e99cf7f87ef5f17bdf97206adc62ab9af1a5"
MACHINE_CENSUS_MANIFEST_SHA256 = (
    "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
)

G2_PROVISIONAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
G2_PROVISIONAL_CSV_SHA256 = (
    "90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119"
)

MODULE_EXCEPTION_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1"
)
MODULE_EXCEPTION_CSV = MODULE_EXCEPTION_DIR / "ai_provisional_adjudication.csv"
MODULE_EXCEPTION_MANIFEST = MODULE_EXCEPTION_DIR / "manifest.json"
MODULE_EXCEPTION_CSV_SHA256 = (
    "8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7"
)
MODULE_EXCEPTION_MANIFEST_SHA256 = (
    "72b02ab7da59e65db2d5e09cee9344c3d52940a717ea3dfea05310e0529d76c1"
)

MULTIPLE_SIGNAL_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1"
)
MULTIPLE_SIGNAL_CSV = MULTIPLE_SIGNAL_DIR / "ai_provisional_adjudication.csv"
MULTIPLE_SIGNAL_MANIFEST = MULTIPLE_SIGNAL_DIR / "manifest.json"
MULTIPLE_SIGNAL_CSV_SHA256 = (
    "dc2e7202c048400d32e019fed6940051f65ca1a67b865727152d94dccf302d70"
)
MULTIPLE_SIGNAL_MANIFEST_SHA256 = (
    "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336"
)

FREEZE20_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_frozen_v1"
)
FREEZE20_CSV = FREEZE20_DIR / "frozen_adjudication.csv"
FREEZE20_MANIFEST = FREEZE20_DIR / "manifest.json"
FREEZE20_CSV_SHA256 = "eda69f61051228ff9d976ec57f6dcd9febea95a2c541095edac19f55074eac1f"
FREEZE20_MANIFEST_SHA256 = (
    "a9bc5d19e4a4aa4d3fde4db23a296cb1b2d32b9e51c6ebe9ace5c548691f8eab"
)

PROGRESS_CENSUS_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_frozen_progress_census_v1"
)
PROGRESS_CENSUS_MANIFEST = PROGRESS_CENSUS_DIR / "manifest.json"
PROGRESS_CENSUS_MANIFEST_SHA256 = (
    "7eee4c9e94ae8ea3b42bfb8921e546533e12ac618b18703edf7d18993f254e1a"
)

SOURCE_HASHES: dict[Path, str] = {
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    PREP_CSV: PREP_CSV_SHA256,
    PREP_MANIFEST: PREP_MANIFEST_SHA256,
    MACHINE_CENSUS_CSV: MACHINE_CENSUS_CSV_SHA256,
    MACHINE_CENSUS_ROSTER: MACHINE_CENSUS_ROSTER_SHA256,
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    G2_PROVISIONAL_CSV: G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: MODULE_EXCEPTION_CSV_SHA256,
    MODULE_EXCEPTION_MANIFEST: MODULE_EXCEPTION_MANIFEST_SHA256,
    MULTIPLE_SIGNAL_CSV: MULTIPLE_SIGNAL_CSV_SHA256,
    MULTIPLE_SIGNAL_MANIFEST: MULTIPLE_SIGNAL_MANIFEST_SHA256,
    FREEZE20_CSV: FREEZE20_CSV_SHA256,
    FREEZE20_MANIFEST: FREEZE20_MANIFEST_SHA256,
    PROGRESS_CENSUS_MANIFEST: PROGRESS_CENSUS_MANIFEST_SHA256,
}

# External planning reference only; not ingested into repo governance.
V31_REFERENCE_FILENAME = "AI_生成程式共同失敗分類標準_實際使用版_v3.1.md"
V31_REFERENCE_SHA256 = "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0"
V31_REFERENCE_BYTES = 26950
V31_REFERENCE_STATUS = "EXTERNAL_PLANNING_REFERENCE_NOT_INGESTED_INTO_REPO_GOVERNANCE"

# Fixed before population statistics are inspected.
PROPOSED_BATCH_PRIORITY: tuple[str, ...] = (
    "A_parse_tokenize_failure_candidates",
    "B_entry_signature_return_shape_import_candidates",
    "C_existing_runtime_evidence_candidates",
    "D_strong_semantic_indicator_candidates",
    "E_multiple_signal_or_evidence_gap_cases",
)

NEXT_BATCH_TARGET_PRIMARY_BATCH = "B_entry_signature_return_shape_import_candidates"
NEXT_BATCH_TARGET_SIZE = 20
NEXT_BATCH_DEDUPLICATE_BY_SOURCE = True
NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE = True

FROZEN_SETS: tuple[tuple[str, Path, str, int], ...] = (
    ("G2_module", G2_PROVISIONAL_CSV, G2_PROVISIONAL_CSV_SHA256, 27),
    ("module_exception", MODULE_EXCEPTION_CSV, MODULE_EXCEPTION_CSV_SHA256, 37),
    ("multiple_signal_chain", MULTIPLE_SIGNAL_CSV, MULTIPLE_SIGNAL_CSV_SHA256, 13),
    ("output_contract_shape20", FREEZE20_CSV, FREEZE20_CSV_SHA256, 20),
)

TRACKED_SIGNALS: tuple[str, ...] = (
    # A parse / L1 candidates
    "ast_parse_failure",
    "tokenize_failure",
    "unclosed_delimiter",
    "unterminated_string",
    "indentation_failure",
    "invalid_syntax",
    "truncated_and_unparseable",
    # B contract / L2 candidates
    "entry_point_missing",
    "entry_point_unique_candidate",
    "entry_point_multiple_candidates",
    "signature_mismatch",
    "return_shape_mismatch",
    "generator_vs_list",
    "extra_wrapper_or_output",
    "oracle_payload_shape_mismatch",
    # C assembly / L3 candidates
    "missing_required_component",
    "component_binding_mismatch",
    "representation_conversion_suspect",
    "domain_api_missing_or_misbound",
    "helper_defined_but_not_connected",
    # D runtime / L4 candidates (existing logs only)
    "name_error",
    "type_error",
    "arity_error",
    "recursion_overflow",
    "nontermination",
    "invalid_api_call",
    "dependency_or_environment_failure",
    "truncated_but_parseable_runtime_failure",
    # E semantic / L5 candidates
    "hardcoded_answer_suspect",
    "incorrect_formula_suspect",
    "wrong_boundary_condition_suspect",
    "algorithm_reconstruction_required",
    "parseable_complete_but_incorrect",
    # F import subdivision
    "stdlib_import_missing_or_wrong",
    "third_party_dependency_missing",
    "domain_api_import_or_usage_error",
    "environment_only_dependency_failure",
    "import_ambiguous",
    # G evidence-gap
    "insufficient_static_evidence",
    "runtime_vs_semantic_not_closed",
    "multiple_plausible_root_causes",
    "public_examples_non_discriminating",
    "diagnostic_execution_required",
)

PARSE_L1_SIGNALS = frozenset(
    {
        "ast_parse_failure",
        "tokenize_failure",
        "unclosed_delimiter",
        "unterminated_string",
        "indentation_failure",
        "invalid_syntax",
        "truncated_and_unparseable",
    }
)
CONTRACT_L2_SIGNALS = frozenset(
    {
        "entry_point_missing",
        "entry_point_multiple_candidates",
        "signature_mismatch",
        "return_shape_mismatch",
        "generator_vs_list",
        "extra_wrapper_or_output",
        "oracle_payload_shape_mismatch",
        "stdlib_import_missing_or_wrong",
        "third_party_dependency_missing",
        "domain_api_import_or_usage_error",
        "environment_only_dependency_failure",
        "import_ambiguous",
    }
)
RUNTIME_L4_SIGNALS = frozenset(
    {
        "name_error",
        "type_error",
        "arity_error",
        "recursion_overflow",
        "nontermination",
        "invalid_api_call",
        "dependency_or_environment_failure",
        "truncated_but_parseable_runtime_failure",
    }
)
SEMANTIC_L5_SIGNALS = frozenset(
    {
        "hardcoded_answer_suspect",
        "incorrect_formula_suspect",
        "wrong_boundary_condition_suspect",
        "algorithm_reconstruction_required",
        "parseable_complete_but_incorrect",
    }
)
EVIDENCE_GAP_SIGNALS = frozenset(
    {
        "insufficient_static_evidence",
        "runtime_vs_semantic_not_closed",
        "multiple_plausible_root_causes",
        "public_examples_non_discriminating",
        "diagnostic_execution_required",
    }
)
IMPORT_SIGNALS = frozenset(
    {
        "stdlib_import_missing_or_wrong",
        "third_party_dependency_missing",
        "domain_api_import_or_usage_error",
        "environment_only_dependency_failure",
        "import_ambiguous",
    }
)

# Formal adjudication fields that must remain blank this revision.
FORBIDDEN_FORMAL_FIELDS = (
    "primary_layer",
    "secondary_layer",
    "healer_eligibility",
    "abstain_reason",
    "formal_confidence",
    "final_failure_chain",
    "frozen_status",
)

ROSTER_FIELDS = (
    "roster_rank",
    "cell_id",
    "program_id",
    "source_sha256",
    "task_id",
    "dataset",
    "model",
    "condition",
    "seed",
    "generation_id",
    "raw_generation_reference",
    "evaluator_outcome",
    "generation_provenance_reference",
    "processed_frozen_status",
    "evaluation_source_sha256",
    "cell_identity_sha256",
    "task_identity_sha256",
    "required_entry_point",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "termination",
    "outcome_validity",
    "evalplus_base_status",
    "evalplus_plus_status",
    "return_type_bucket",
    "return_shape_bucket",
)

SIGNAL_INVENTORY_FIELDS = (
    "roster_rank",
    "cell_id",
    "program_id",
    "task_id",
    "seed",
    "condition",
    "source_sha256",
    "evaluation_source_sha256",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "termination",
    "return_type_bucket",
    "return_shape_bucket",
    "observed_signals_json",
    "candidate_mechanisms_json",
    "evidence_available_json",
    "evidence_gap_json",
    "review_priority",
    "proposed_primary_batch",
    "proposed_batch_rule",
    "planning_annotation",
    "duplicate_source_group_id",
    "duplicate_source_group_size",
    "is_source_representative",
    *FORBIDDEN_FORMAL_FIELDS,
)

BATCH_PARTITION_FIELDS = (
    "proposed_primary_batch",
    "cells",
    "unique_program_id",
    "unique_task_id",
    "unique_source_sha256",
    "planning_annotation",
)

NEXT_BATCH_FIELDS = (
    "batch_rank",
    "cell_id",
    "program_id",
    "task_id",
    "seed",
    "condition",
    "source_sha256",
    "evaluation_source_sha256",
    "proposed_primary_batch",
    "return_type_bucket",
    "return_shape_bucket",
    "duplicate_source_group_size",
    "observed_signals_json",
    "selection_reason",
    "planning_annotation",
)

STDLIB_ROOTS = set(sys.stdlib_module_names) | {"typing", "__future__"}
DOMAIN_API_ROOTS = frozenset({"numpy", "np", "scipy", "pandas", "torch", "sympy"})


class PlanningError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanningError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(repo: Path = REPO_ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(repo, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _evaluator_outcome(prep: dict[str, str]) -> str:
    base = prep.get("evalplus_base_status") or ""
    plus = prep.get("evalplus_plus_status") or ""
    if prep.get("outcome_validity") == "INVALID_INFRASTRUCTURE":
        return "INVALID_INFRASTRUCTURE"
    if base or plus:
        return f"evalplus_base={base};evalplus_plus={plus}"
    return "UNKNOWN"


def _tokenize_ok(source: str) -> tuple[bool, str]:
    try:
        list(tokenize.generate_tokens(io.StringIO(source).readline))
        return True, ""
    except tokenize.TokenError as exc:
        return False, str(exc)
    except IndentationError as exc:
        return False, f"IndentationError:{exc}"


def _collect_observed_signals(
    *,
    source: str,
    entry_point: str,
    prep: dict[str, str],
    census: dict[str, str],
) -> list[str]:
    signals: set[str] = set()

    if prep.get("outcome_validity") == "INVALID_INFRASTRUCTURE" or census.get(
        "diagnostic_evidence_validity"
    ) == "INVALID_INFRASTRUCTURE":
        signals.add("insufficient_static_evidence")
        signals.add("diagnostic_execution_required")
        return sorted(signals)

    tok_ok, tok_err = _tokenize_ok(source)
    if not tok_ok:
        signals.add("tokenize_failure")
        lower = tok_err.lower()
        if "eof" in lower or "unmatched" in lower or "never closed" in lower:
            signals.add("unclosed_delimiter")
        if "eol" in lower or "unterminated" in lower:
            signals.add("unterminated_string")

    try:
        tree = ast.parse(source)
        parse_ok = True
        parse_exc: SyntaxError | None = None
    except SyntaxError as exc:
        parse_ok = False
        parse_exc = exc
        signals.add("ast_parse_failure")
        signals.add("invalid_syntax")
        msg = (exc.msg or "").lower()
        if "indent" in msg:
            signals.add("indentation_failure")
        if "unterminated" in msg or "eol while scanning" in msg:
            signals.add("unterminated_string")
        if "was never closed" in msg or "unexpected eof" in msg or "unexpected EOF" in (exc.msg or ""):
            signals.add("unclosed_delimiter")
        stripped = source.rstrip()
        if "truncated" in msg or stripped.endswith((":", "\\", "(", "[", "{", ",")):
            signals.add("truncated_and_unparseable")
        return sorted(signals)

    _ = parse_exc
    _require(parse_ok, "parse_ok invariant")

    # Truncation mechanism only if parseable but source looks cut; not auto-L1.
    if source.rstrip().endswith((":", "\\", "(", "[", "{", ",")) and not signals.intersection(
        PARSE_L1_SIGNALS
    ):
        # Mechanism clue only via candidate_mechanisms elsewhere; no L1 signal.
        pass

    defs = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point
    ]
    if not defs:
        signals.add("entry_point_missing")
    elif len(defs) > 1:
        signals.add("entry_point_multiple_candidates")
    else:
        signals.add("entry_point_unique_candidate")
        entry_def = defs[0]
        if any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(entry_def)):
            signals.add("generator_vs_list")
        # Hardcoded / trivial-return suspect (planning clue only).
        body = [n for n in entry_def.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Constant)]
        if len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Constant):
            signals.add("hardcoded_answer_suspect")

    # Import subdivision (static presence only; not executed).
    third_party: set[str] = set()
    domain: set[str] = set()
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots = [node.module.split(".", 1)[0]]
        for root in roots:
            if root in DOMAIN_API_ROOTS:
                domain.add(root)
            elif root not in STDLIB_ROOTS:
                third_party.add(root)
    if third_party:
        signals.add("third_party_dependency_missing")
    if domain:
        signals.add("domain_api_import_or_usage_error")

    helpers = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != entry_point
    }
    if helpers and defs:
        entry_names = {n.id for n in ast.walk(defs[0]) if isinstance(n, ast.Name)}
        if helpers.isdisjoint(entry_names):
            signals.add("helper_defined_but_not_connected")

    # Existing frozen machine / diagnostic evidence (no new execution).
    if census.get("output_or_contract_shape_signal") == "true":
        signals.add("return_shape_mismatch")
        signals.add("oracle_payload_shape_mismatch")
    if census.get("packaging_or_scaffold_residue_signal") == "true":
        signals.add("extra_wrapper_or_output")
    if census.get("completed_return_signal") == "true":
        signals.add("parseable_complete_but_incorrect")

    exc = prep.get("diagnostic_exception_class") or ""
    term = (prep.get("termination") or "").lower()
    phase = prep.get("diagnostic_phase") or ""
    if exc == "NameError" or census.get("nameerror_exception_signal") == "true":
        signals.add("name_error")
    if exc == "TypeError":
        signals.add("type_error")
    if "TypeError" in exc and "argument" in (prep.get("failure_chain") or "").lower():
        signals.add("arity_error")
    if exc == "RecursionError":
        signals.add("recursion_overflow")
    if term in {"timeout", "nontermination", "killed"} or census.get(
        "timeout_or_nontermination_signal"
    ) == "true":
        signals.add("nontermination")
    if phase in {"G2_base", "G2_plus"} and term == "raised" and exc:
        if exc in {"ImportError", "ModuleNotFoundError"}:
            signals.add("dependency_or_environment_failure")
        elif exc not in {"NameError", "TypeError", "RecursionError"}:
            signals.add("invalid_api_call")

    # Evidence-gap heuristics (planning only).
    competing = []
    if signals & CONTRACT_L2_SIGNALS:
        competing.append("contract")
    if signals & RUNTIME_L4_SIGNALS:
        competing.append("runtime")
    if signals & SEMANTIC_L5_SIGNALS and "parseable_complete_but_incorrect" not in (
        signals & SEMANTIC_L5_SIGNALS
    ):
        competing.append("semantic")
    if len(competing) >= 2:
        signals.add("multiple_plausible_root_causes")
        signals.add("runtime_vs_semantic_not_closed")
    if (
        "return_shape_mismatch" in signals
        and "parseable_complete_but_incorrect" in signals
        and not (signals & RUNTIME_L4_SIGNALS)
    ):
        # Completed return + contract-shape only: may need diagnostics to close L2 vs L5.
        signals.add("public_examples_non_discriminating")

    return sorted(signals)


def _candidate_mechanisms(signals: list[str]) -> list[str]:
    signal_set = set(signals)
    mechanisms: list[str] = []
    if "truncated_and_unparseable" in signal_set:
        mechanisms.append("truncation")
    if "return_shape_mismatch" in signal_set or "oracle_payload_shape_mismatch" in signal_set:
        mechanisms.append("output_schema_or_packaging")
    if "extra_wrapper_or_output" in signal_set:
        mechanisms.append("scaffold_or_wrapper_residue")
    if "entry_point_missing" in signal_set or "entry_point_multiple_candidates" in signal_set:
        mechanisms.append("entry_point_binding")
    if signal_set & IMPORT_SIGNALS:
        mechanisms.append("import_resolution")
    if signal_set & RUNTIME_L4_SIGNALS:
        mechanisms.append("existing_runtime_exception")
    if "hardcoded_answer_suspect" in signal_set:
        mechanisms.append("possible_hardcoded_return")
    if "parseable_complete_but_incorrect" in signal_set:
        mechanisms.append("completed_but_incorrect")
    if not mechanisms and "insufficient_static_evidence" in signal_set:
        mechanisms.append("infrastructure_or_missing_frame")
    return mechanisms


def _evidence_available(prep: dict[str, str], census: dict[str, str], signals: list[str]) -> list[str]:
    available = [
        "frozen_raw_generation",
        "public_task_statement",
        "public_entry_point",
        "existing_evaluator_outcome",
        "existing_provenance_and_manifest",
        "static_ast_or_tokenize",
    ]
    if prep.get("diagnostic_exception_class"):
        available.append("existing_diagnostic_exception_class")
    if prep.get("termination"):
        available.append("existing_termination_field")
    if census.get("all_observed_machine_signals"):
        available.append("existing_machine_census_signals")
    if signals:
        available.append("observed_static_signals")
    return available


def _evidence_gap(signals: list[str]) -> list[str]:
    return sorted(set(signals) & EVIDENCE_GAP_SIGNALS)


def _assign_proposed_batch(signals: list[str]) -> tuple[str, str]:
    signal_set = set(signals)
    if "insufficient_static_evidence" in signal_set:
        return (
            "E_multiple_signal_or_evidence_gap_cases",
            "priority:E_insufficient_static_evidence",
        )
    if signal_set & PARSE_L1_SIGNALS:
        return "A_parse_tokenize_failure_candidates", "priority:A_parse_or_tokenize_failure"
    if signal_set & CONTRACT_L2_SIGNALS:
        return (
            "B_entry_signature_return_shape_import_candidates",
            "priority:B_contract_entry_return_or_import",
        )
    if signal_set & RUNTIME_L4_SIGNALS:
        return (
            "C_existing_runtime_evidence_candidates",
            "priority:C_existing_runtime_log_evidence",
        )
    strong_semantic = (signal_set & SEMANTIC_L5_SIGNALS) - {"parseable_complete_but_incorrect"}
    if strong_semantic or "algorithm_reconstruction_required" in signal_set:
        return (
            "D_strong_semantic_indicator_candidates",
            "priority:D_strong_semantic_static_indicator",
        )
    if signal_set & EVIDENCE_GAP_SIGNALS or "multiple_plausible_root_causes" in signal_set:
        return (
            "E_multiple_signal_or_evidence_gap_cases",
            "priority:E_evidence_gap_or_multiple_signal",
        )
    if not signal_set:
        return (
            "E_multiple_signal_or_evidence_gap_cases",
            "priority:E_no_obvious_static_signal",
        )
    return (
        "E_multiple_signal_or_evidence_gap_cases",
        "priority:E_fallback_unassigned_signal_set",
    )


def _review_priority(batch: str, signals: list[str]) -> str:
    if batch.startswith("A_"):
        return "1_parse_closure"
    if batch.startswith("B_") and "entry_point_missing" in signals:
        return "2_entry_point_contract"
    if batch.startswith("B_"):
        return "3_return_shape_or_import_contract"
    if batch.startswith("C_"):
        return "4_existing_runtime_discrimination"
    if batch.startswith("D_"):
        return "5_semantic_abstain_boundary"
    return "6_evidence_gap_or_unresolved_prep"


def _load_frozen97(repo: Path) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    frozen_by_set: dict[str, set[str]] = {}
    audit_rows: list[dict[str, str]] = []
    for set_name, roster_path, roster_sha, expected_n in FROZEN_SETS:
        ids = {row["program_id"] for row in _read_csv(repo / roster_path)}
        _require(len(ids) == expected_n, f"{set_name} count drift: {len(ids)} != {expected_n}")
        frozen_by_set[set_name] = ids
        for program_id in sorted(ids):
            audit_rows.append(
                {
                    "program_id": program_id,
                    "frozen_set": set_name,
                    "source_roster_path": roster_path.as_posix(),
                    "source_roster_sha256": roster_sha,
                }
            )
    all_ids: set[str] = set()
    for set_name, ids in frozen_by_set.items():
        _require(not (all_ids & ids), f"frozen set overlap involving {set_name}")
        all_ids |= ids
    _require(len(all_ids) == 97, f"frozen union must be 97, got {len(all_ids)}")
    return frozen_by_set, audit_rows


def _select_next_batch(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates = [
        row
        for row in inventory
        if row["proposed_primary_batch"] == NEXT_BATCH_TARGET_PRIMARY_BATCH
        and row["is_source_representative"] == "true"
    ]
    _require(candidates, "no candidates for next adjudication batch")
    if NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE:
        by_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in sorted(candidates, key=lambda item: (item["task_id"], item["program_id"])):
            by_bucket[row["return_type_bucket"] or "UNKNOWN"].append(row)
        buckets = sorted(by_bucket)
        selected: list[dict[str, str]] = []
        index = 0
        while len(selected) < NEXT_BATCH_TARGET_SIZE:
            added = False
            for bucket in buckets:
                if index < len(by_bucket[bucket]):
                    selected.append(by_bucket[bucket][index])
                    added = True
                    if len(selected) >= NEXT_BATCH_TARGET_SIZE:
                        break
            if not added:
                break
            index += 1
        selected = sorted(selected, key=lambda item: item["program_id"])
    else:
        selected = sorted(
            candidates,
            key=lambda item: (item["return_type_bucket"], item["task_id"], item["program_id"]),
        )[:NEXT_BATCH_TARGET_SIZE]
    _require(
        15 <= len(selected) <= 25,
        f"next batch size out of range: {len(selected)}",
    )
    return selected


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    frozen_by_set, frozen_audit = _load_frozen97(repo)
    frozen_ids = set().union(*frozen_by_set.values())

    prep_rows = _read_csv(repo / PREP_CSV)
    _require(len(prep_rows) == 198, f"formal population drift: {len(prep_rows)}")
    prep_by_program = {row["program_id"]: row for row in prep_rows}
    _require(len(prep_by_program) == 198, "duplicate program_id in preparation")

    census_rows = _read_csv(repo / MACHINE_CENSUS_CSV)
    census_by_program = {row["program_id"]: row for row in census_rows}

    journals = {
        row["program_id"]: row
        for row in _read_jsonl(repo / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    tasks = {row["task_id"]: row for row in _read_jsonl(repo / preparation.TASKS)}

    remaining_ids = sorted(set(prep_by_program) - frozen_ids)
    _require(len(remaining_ids) == 101, f"remaining101 count drift: {len(remaining_ids)}")
    _require(not (set(remaining_ids) & frozen_ids), "remaining ∩ frozen must be empty")
    _require(len(frozen_ids) + len(remaining_ids) == 198, "97+101 must equal 198")

    roster_rows: list[dict[str, str]] = []
    inventory_rows: list[dict[str, str]] = []

    for rank, program_id in enumerate(remaining_ids, 1):
        prep = prep_by_program[program_id]
        _require(program_id in census_by_program, f"missing machine census row: {program_id}")
        census = census_by_program[program_id]
        journal = journals[program_id]
        task = tasks[prep["task_id"]]
        source = journal["evaluation_source"]
        source_sha = _sha(source.encode("utf-8"))
        _require(
            source_sha == prep["evaluation_source_sha256"],
            f"source sha drift vs preparation: {program_id}",
        )
        _require(
            source_sha == journal["evaluation_source_sha256"],
            f"source sha drift vs journal: {program_id}",
        )

        signals = _collect_observed_signals(
            source=source,
            entry_point=str(task["entry_point"]),
            prep=prep,
            census=census,
        )
        mechanisms = _candidate_mechanisms(signals)
        available = _evidence_available(prep, census, signals)
        gaps = _evidence_gap(signals)
        batch, batch_rule = _assign_proposed_batch(signals)
        cell_id = prep["cell_identity_sha256"]

        roster_rows.append(
            {
                "roster_rank": str(rank),
                "cell_id": cell_id,
                "program_id": program_id,
                "source_sha256": source_sha,
                "task_id": prep["task_id"],
                "dataset": "MBPP+",
                "model": "Qwen2.5-Coder-3B-Instruct/q35_9b_replay_r003",
                "condition": "Candidate_B/H0",
                "seed": prep["seed"],
                "generation_id": prep["generation_id"],
                "raw_generation_reference": (
                    f"{preparation.JOURNAL.as_posix()}#program_id={program_id};healer_account=H0"
                ),
                "evaluator_outcome": _evaluator_outcome(prep),
                "generation_provenance_reference": (
                    f"raw_response_sha256={journal.get('raw_response_sha256','')};"
                    f"generation_id={prep['generation_id']}"
                ),
                "processed_frozen_status": "remaining_not_frozen",
                "evaluation_source_sha256": prep["evaluation_source_sha256"],
                "cell_identity_sha256": prep["cell_identity_sha256"],
                "task_identity_sha256": prep["task_identity_sha256"],
                "required_entry_point": str(task["entry_point"]),
                "diagnostic_phase": prep.get("diagnostic_phase", ""),
                "diagnostic_exception_class": prep.get("diagnostic_exception_class", ""),
                "termination": prep.get("termination", ""),
                "outcome_validity": prep.get("outcome_validity", ""),
                "evalplus_base_status": prep.get("evalplus_base_status", ""),
                "evalplus_plus_status": prep.get("evalplus_plus_status", ""),
                "return_type_bucket": prep.get("return_type_bucket", ""),
                "return_shape_bucket": prep.get("return_shape_bucket", ""),
            }
        )

        blank_formal = {field: "" for field in FORBIDDEN_FORMAL_FIELDS}
        inventory_rows.append(
            {
                "roster_rank": str(rank),
                "cell_id": cell_id,
                "program_id": program_id,
                "task_id": prep["task_id"],
                "seed": prep["seed"],
                "condition": "Candidate_B/H0",
                "source_sha256": source_sha,
                "evaluation_source_sha256": prep["evaluation_source_sha256"],
                "diagnostic_phase": prep.get("diagnostic_phase", ""),
                "diagnostic_exception_class": prep.get("diagnostic_exception_class", ""),
                "termination": prep.get("termination", ""),
                "return_type_bucket": prep.get("return_type_bucket", ""),
                "return_shape_bucket": prep.get("return_shape_bucket", ""),
                "observed_signals_json": _json(signals),
                "candidate_mechanisms_json": _json(mechanisms),
                "evidence_available_json": _json(available),
                "evidence_gap_json": _json(gaps),
                "review_priority": _review_priority(batch, signals),
                "proposed_primary_batch": batch,
                "proposed_batch_rule": batch_rule,
                "planning_annotation": PLANNING_ONLY_MARK,
                "duplicate_source_group_id": "",
                "duplicate_source_group_size": "1",
                "is_source_representative": "true",
                **blank_formal,
            }
        )

    # Stable duplicate-source grouping (not Healer-based).
    source_groups: dict[str, list[str]] = defaultdict(list)
    for row in inventory_rows:
        source_groups[row["source_sha256"]].append(row["program_id"])
    for group_index, (source_sha, program_ids) in enumerate(
        sorted(source_groups.items(), key=lambda item: (-len(item[1]), item[0])),
        1,
    ):
        group_id = f"dup_src_{group_index:03d}"
        group_size = len(program_ids)
        representative = min(program_ids)
        for row in inventory_rows:
            if row["source_sha256"] == source_sha:
                row["duplicate_source_group_id"] = group_id
                row["duplicate_source_group_size"] = str(group_size)
                row["is_source_representative"] = str(row["program_id"] == representative).lower()

    batch_counter = Counter(row["proposed_primary_batch"] for row in inventory_rows)
    _require(sum(batch_counter.values()) == 101, "proposed batch sum must be 101")
    for row in inventory_rows:
        _require(row["proposed_primary_batch"] in PROPOSED_BATCH_PRIORITY, "unknown batch")
        for field in FORBIDDEN_FORMAL_FIELDS:
            _require(row[field] == "", f"formal field leaked: {field}")

    batch_partition = []
    for batch in PROPOSED_BATCH_PRIORITY:
        rows = [row for row in inventory_rows if row["proposed_primary_batch"] == batch]
        batch_partition.append(
            {
                "proposed_primary_batch": batch,
                "cells": str(len(rows)),
                "unique_program_id": str(len({row["program_id"] for row in rows})),
                "unique_task_id": str(len({row["task_id"] for row in rows})),
                "unique_source_sha256": str(len({row["source_sha256"] for row in rows})),
                "planning_annotation": PLANNING_ONLY_MARK,
            }
        )

    signal_counter = Counter()
    for row in inventory_rows:
        for signal in json.loads(row["observed_signals_json"]):
            signal_counter[signal] += 1
    signal_counts = {
        "note": "signal counts may overlap across cells; not a mutually exclusive taxonomy",
        "cells": 101,
        "by_signal": {signal: int(signal_counter.get(signal, 0)) for signal in TRACKED_SIGNALS},
        "category_cell_counts_overlapping": {
            "parse_L1_candidate_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & PARSE_L1_SIGNALS
            ),
            "contract_L2_candidate_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & CONTRACT_L2_SIGNALS
            ),
            "runtime_existing_evidence_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & RUNTIME_L4_SIGNALS
            ),
            "semantic_strong_signal_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & SEMANTIC_L5_SIGNALS
            ),
            "import_subclass_signal_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & IMPORT_SIGNALS
            ),
            "multiple_signal_cells": sum(
                1
                for row in inventory_rows
                if len(json.loads(row["observed_signals_json"])) >= 2
            ),
            "evidence_gap_cells": sum(
                1
                for row in inventory_rows
                if set(json.loads(row["observed_signals_json"])) & EVIDENCE_GAP_SIGNALS
            ),
            "no_obvious_static_signal_cells": sum(
                1 for row in inventory_rows if not json.loads(row["observed_signals_json"])
            ),
        },
        "proposed_primary_batch_exclusive": {
            batch: int(batch_counter.get(batch, 0)) for batch in PROPOSED_BATCH_PRIORITY
        },
        "planning_annotation": PLANNING_ONLY_MARK,
    }

    next_batch_candidates = _select_next_batch(inventory_rows)
    next_batch_rows = []
    for batch_rank, row in enumerate(next_batch_candidates, 1):
        next_batch_rows.append(
            {
                "batch_rank": str(batch_rank),
                "cell_id": row["cell_id"],
                "program_id": row["program_id"],
                "task_id": row["task_id"],
                "seed": row["seed"],
                "condition": row["condition"],
                "source_sha256": row["source_sha256"],
                "evaluation_source_sha256": row["evaluation_source_sha256"],
                "proposed_primary_batch": row["proposed_primary_batch"],
                "return_type_bucket": row["return_type_bucket"],
                "return_shape_bucket": row["return_shape_bucket"],
                "duplicate_source_group_size": row["duplicate_source_group_size"],
                "observed_signals_json": row["observed_signals_json"],
                "selection_reason": (
                    f"primary_batch={NEXT_BATCH_TARGET_PRIMARY_BATCH};"
                    f"source_representative={row['is_source_representative']};"
                    f"dedupe_by_source={NEXT_BATCH_DEDUPLICATE_BY_SOURCE};"
                    f"round_robin_return_type={NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE};"
                    f"stable_sort=program_id_after_selection;"
                    f"not_selected_by_healer_eligibility"
                ),
                "planning_annotation": PLANNING_ONLY_MARK,
            }
        )

    execution_counts = {
        "model_calls": 0,
        "candidate_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }

    return {
        "roster_rows": roster_rows,
        "frozen_audit": frozen_audit,
        "inventory_rows": inventory_rows,
        "batch_partition": batch_partition,
        "batch_counter": batch_counter,
        "signal_counts": signal_counts,
        "next_batch_rows": next_batch_rows,
        "execution_counts": execution_counts,
        "frozen_by_set": frozen_by_set,
        "frozen_ids": frozen_ids,
        "remaining_ids": set(remaining_ids),
        "prep_by_program": prep_by_program,
    }


def _planning_report(analysis: dict[str, Any], roster_hash: str, next_hash: str) -> str:
    roster = analysis["roster_rows"]
    inventory = analysis["inventory_rows"]
    batch = analysis["next_batch_rows"]
    signal_counts = analysis["signal_counts"]
    outcome = Counter(row["evaluator_outcome"] for row in roster)
    cats = signal_counts["category_cell_counts_overlapping"]
    lines = [
        "# Candidate B r003 taxonomy v3.1：remaining101 零執行 census 與批次規劃",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        f"**規劃註記：`{PLANNING_ONLY_MARK}`**",
        "",
        "## 範圍與禁止事項",
        "",
        "- 本輪僅做母體盤點與下一批規劃，不進行正式逐格裁決。",
        "- 不凍結新分類；不執行 candidate／diagnostics／EvalPlus／validation／Healer。",
        "- 不將 UNRESOLVED 視為 L6；不混用 PENDING_REVIEW 與 UNRESOLVED。",
        "- 不因 v3.1 重新裁決既有 97 格；v3.1 僅作外部 planning reference。",
        "- 正式欄位 primary_layer／healer_eligibility 等保持空白。",
        "",
        "## 母體 closure",
        "",
        "- 正式母體：198",
        "- 已凍結：97（G2 27 + module_exception 37 + multiple_signal 13 + output_contract_shape 20）",
        "- 剩餘：101",
        f"- remaining101 roster SHA-256：`{roster_hash}`",
        f"- unique program_id：{len({row['program_id'] for row in roster})}",
        f"- unique source_sha256：{len({row['source_sha256'] for row in roster})}",
        f"- unique task_id：{len({row['task_id'] for row in roster})}",
        "",
        "## Evaluator outcome 分布",
        "",
    ]
    for key, value in sorted(outcome.items()):
        lines.append(f"- `{key}`：{value}")
    lines.extend(
        [
            "",
            "## 靜態 signal 統計（可重疊，非互斥分類）",
            "",
            f"- parse/L1 候選格：{cats['parse_L1_candidate_cells']}",
            f"- contract/L2 候選格：{cats['contract_L2_candidate_cells']}",
            f"- runtime 既有證據候選格：{cats['runtime_existing_evidence_cells']}",
            f"- semantic 強訊號候選格：{cats['semantic_strong_signal_cells']}",
            f"- import 子類訊號格：{cats['import_subclass_signal_cells']}",
            f"- multiple-signal 格（≥2 signals）：{cats['multiple_signal_cells']}",
            f"- evidence-gap 格：{cats['evidence_gap_cells']}",
            f"- 無明顯靜態訊號格：{cats['no_obvious_static_signal_cells']}",
            "",
            "### 各 signal 出現次數",
            "",
        ]
    )
    for signal, count in sorted(
        ((k, v) for k, v in signal_counts["by_signal"].items() if v > 0),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- `{signal}`：{count}")
    lines.extend(
        [
            "",
            "## Proposed primary batch（互斥，合計 101）",
            "",
        ]
    )
    for row in analysis["batch_partition"]:
        lines.append(f"- `{row['proposed_primary_batch']}`：{row['cells']}")
    lines.extend(
        [
            "",
            "## 建議下一個正式裁決批次",
            "",
            f"- 規模：{len(batch)} 格",
            f"- 批次 roster SHA-256：`{next_hash}`",
            f"- 目標 primary batch：`{NEXT_BATCH_TARGET_PRIMARY_BATCH}`",
            "- Selection rule（統計前固定）：",
            f"  1. 僅取 `proposed_primary_batch={NEXT_BATCH_TARGET_PRIMARY_BATCH}`",
            f"  2. 若 `dedupe_by_source={NEXT_BATCH_DEDUPLICATE_BY_SOURCE}`，僅取 source representative",
            f"  3. 若 `round_robin_return_type={NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE}`，"
            "依 return_type_bucket 輪詢至目標 20 格",
            "  4. 選後以 program_id 穩定排序",
            "  5. 不以 Healer 可修性或預期成功率選樣",
            "- 本輪不得開始裁決該批。",
            "",
            "## v3.1 外部參考",
            "",
            f"- 檔名：`{V31_REFERENCE_FILENAME}`",
            f"- SHA-256：`{V31_REFERENCE_SHA256}`",
            f"- 狀態：`{V31_REFERENCE_STATUS}`",
            "",
            "## Execution counts",
            "",
            "- 全部為 0（model／candidate／EvalPlus／diagnostics／validation／Healer／programs）。",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    roster_bytes = _csv_bytes(ROSTER_FIELDS, analysis["roster_rows"])
    inventory_bytes = _csv_bytes(SIGNAL_INVENTORY_FIELDS, analysis["inventory_rows"])
    batch_partition_bytes = _csv_bytes(BATCH_PARTITION_FIELDS, analysis["batch_partition"])
    next_batch_bytes = _csv_bytes(NEXT_BATCH_FIELDS, analysis["next_batch_rows"])
    signal_counts_bytes = _json_bytes(analysis["signal_counts"])
    execution_bytes = _json_bytes(analysis["execution_counts"])
    roster_hash = _sha(roster_bytes)
    next_hash = _sha(next_batch_bytes)
    report_bytes = _planning_report(analysis, roster_hash, next_hash).encode("utf-8")

    outputs_without_manifest = {
        "remaining101_roster.csv": roster_bytes,
        "static_signal_inventory.csv": inventory_bytes,
        "signal_counts.json": signal_counts_bytes,
        "proposed_batch_partition.csv": batch_partition_bytes,
        "next_adjudication_batch_roster.csv": next_batch_bytes,
        "planning_report_zh.md": report_bytes,
        "execution_counts.json": execution_bytes,
    }
    outputs_sha = {name: _sha(data) for name, data in outputs_without_manifest.items()}

    provenance = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "planning_annotation": PLANNING_ONLY_MARK,
        "start_head": START_HEAD,
        "formal_population": 198,
        "frozen_total": 97,
        "remaining_total": 101,
        "frozen_sets": {
            name: {
                "path": path.as_posix(),
                "sha256": sha,
                "cells": expected_n,
            }
            for name, path, sha, expected_n in FROZEN_SETS
        },
        "freeze20_manifest_sha256": FREEZE20_MANIFEST_SHA256,
        "progress_census_manifest_sha256": PROGRESS_CENSUS_MANIFEST_SHA256,
        "taxonomy_v31_planning_reference": {
            "filename": V31_REFERENCE_FILENAME,
            "sha256": V31_REFERENCE_SHA256,
            "bytes": V31_REFERENCE_BYTES,
            "status": V31_REFERENCE_STATUS,
        },
        "proposed_batch_priority": list(PROPOSED_BATCH_PRIORITY),
        "next_batch_selection_rule": {
            "target_primary_batch": NEXT_BATCH_TARGET_PRIMARY_BATCH,
            "target_size": NEXT_BATCH_TARGET_SIZE,
            "deduplicate_by_source": NEXT_BATCH_DEDUPLICATE_BY_SOURCE,
            "round_robin_by_return_type": NEXT_BATCH_ROUND_ROBIN_BY_RETURN_TYPE,
            "healer_eligibility_not_used": True,
        },
        "remaining101_roster_sha256": roster_hash,
        "next_adjudication_batch_roster_sha256": next_hash,
        "next_adjudication_batch_size": len(analysis["next_batch_rows"]),
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        "forbidden_formal_fields_left_blank": list(FORBIDDEN_FORMAL_FIELDS),
        **analysis["execution_counts"],
    }
    provenance_bytes = _json_bytes(provenance)
    outputs_without_manifest["provenance.json"] = provenance_bytes
    outputs_sha["provenance.json"] = _sha(provenance_bytes)

    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "planning_annotation": PLANNING_ONLY_MARK,
        "start_head": START_HEAD,
        "formal_population": 198,
        "frozen_total": 97,
        "remaining_total": 101,
        "remaining101_roster": 101,
        "next_adjudication_batch_size": len(analysis["next_batch_rows"]),
        "remaining101_roster_sha256": roster_hash,
        "next_adjudication_batch_roster_sha256": next_hash,
        "freeze20_manifest_sha256": FREEZE20_MANIFEST_SHA256,
        "progress_census_manifest_sha256": PROGRESS_CENSUS_MANIFEST_SHA256,
        "taxonomy_v31_reference_sha256": V31_REFERENCE_SHA256,
        "outputs_sha256_excluding_manifest": outputs_sha,
        "analyzer": ANALYZER.as_posix(),
        "tests": TESTS.as_posix(),
        **analysis["execution_counts"],
    }
    outputs = dict(outputs_without_manifest)
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output_dir = repo / OUTPUT_RELATIVE
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_outputs(repo)
    for name, data in outputs.items():
        (output_dir / name).write_bytes(data)
    return output_dir


def main() -> None:
    output_dir = write_outputs(REPO_ROOT)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output_dir}")
    print(f"status={manifest['status']}")
    print(f"remaining={manifest['remaining_total']}")
    print(f"next_batch={manifest['next_adjudication_batch_size']}")
    print(f"roster_sha={manifest['remaining101_roster_sha256']}")


if __name__ == "__main__":
    main()
