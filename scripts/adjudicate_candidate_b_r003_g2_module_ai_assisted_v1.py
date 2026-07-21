#!/usr/bin/env python3
"""Materialize AI-assisted, non-formal provisional adjudications for G2_module."""

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


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1"
)
START_HEAD = "ae8b65c4049899ec211254695024b86988042fa3"
STATUS = "AI_ASSISTED_PROVISIONAL_NOT_FORMAL_HUMAN_ADJUDICATION"
ANALYZER = Path("scripts/adjudicate_candidate_b_r003_g2_module_ai_assisted_v1.py")
TESTS = Path("tests/finals_rebuild/test_candidate_b_r003_g2_module_ai_assisted_v1.py")

# All 15 frozen inputs are byte-verified, but only the public task contract,
# H0 source journal, coarse diagnostic identity/phase/class/line, and taxonomy
# codebook are parsed by this analyzer. Correctness outputs are never loaded.
SOURCE_HASHES = dict(preparation.SOURCE_HASHES)

FIELDS = (
    "review_rank", "program_id", "cell_identity_sha256", "task_identity_sha256",
    "task_id", "seed", "generation_id", "evaluation_source_sha256",
    "task_contract_sha256", "taxonomy_version", "diagnostics_runner_revision",
    "adjudication_status", "evidence_role", "public_task_contract",
    "required_entry_point", "required_signature", "required_function_source",
    "required_function_start_line", "required_function_end_line",
    "module_level_executable_statements", "diagnostic_source_context_numbered",
    "diagnostic_phase", "diagnostic_exception_class", "diagnostic_candidate_line",
    "diagnostic_statement_ast", "diagnostic_ast_node", "imports", "api_calls",
    "g1_observation", "g2_observation", "g3e_observation", "g3a_observation",
    "g3s_observation", "g3c_observation", "g4_observation",
    "proposed_primary_failure_layer", "proposed_secondary_failure_layers",
    "outcome_validity", "failure_chain", "mechanism_tags", "confidence",
    "uncertainty_notes", "proposed_healer_eligibility",
    "proposed_healer_decision", "rationale", "evidence_references",
    "researcher_review_status", "researcher_notes", "researcher_id",
    "reviewed_at_utc",
)


class AdjudicationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _display_text(value: str) -> str:
    """Preserve textual evidence while removing non-semantic line-end whitespace."""
    return "\n".join(line.rstrip() for line in value.splitlines())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def verify_sources(root: Path = ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = relative if relative.is_absolute() else root / relative
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _node_at(tree: ast.AST, line: int, statement_only: bool = False) -> str:
    base = ast.stmt if statement_only else ast.AST
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, base)
        and hasattr(node, "lineno")
        and int(node.lineno) <= line <= int(getattr(node, "end_lineno", node.lineno))
    ]
    if not nodes:
        return "UNRESOLVED"
    nodes.sort(key=lambda node: (
        int(getattr(node, "end_lineno", line)) - int(node.lineno),
        int(getattr(node, "end_col_offset", 0)) - int(getattr(node, "col_offset", 0)),
    ))
    return type(nodes[0]).__name__


def _imports_and_calls(tree: ast.AST) -> tuple[list[str], list[str]]:
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(f"{node.module or ''}:{','.join(alias.name for alias in node.names)}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                parts: list[str] = [node.func.attr]
                value = node.func.value
                while isinstance(value, ast.Attribute):
                    parts.append(value.attr)
                    value = value.value
                if isinstance(value, ast.Name):
                    parts.append(value.id)
                calls.add(".".join(reversed(parts)))
    return sorted(imports), sorted(calls)


def _numbered_context(lines: list[str], line: int, radius: int = 2) -> str:
    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    return "\n".join(f"{number}: {lines[number - 1]}".rstrip() for number in range(start, end + 1))


def _module_executable_statements(source: str, tree: ast.Module) -> str:
    statements: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        segment = ast.get_source_segment(source, node)
        _require(segment is not None, "module executable statement extraction failed")
        statements.append(f"lines {node.lineno}-{getattr(node, 'end_lineno', node.lineno)}:\n{_display_text(segment)}")
    _require(bool(statements), "missing module executable statement")
    return "\n\n".join(statements)


def _decision(
    primary: str,
    secondary: list[str],
    mechanisms: list[str],
    confidence: str,
    uncertainty: str,
    eligibility: str,
    rationale: str,
    function_mechanism: str,
) -> dict[str, Any]:
    chain: list[dict[str, Any]] = []
    if primary == "L2":
        chain.append({
            "stage": "raw_required_function_output",
            "gate": "G3s",
            "layer": "L2",
            "mechanism": function_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
        chain.append({
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "L4",
            "mechanism": "module_level_executable_assertion",
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
    elif function_mechanism in {"stdlib_regex_pattern_construction", "text_parsing_control_flow_failure"}:
        chain.append({
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "L4",
            "mechanism": function_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
    else:
        chain.append({
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "L4",
            "mechanism": "module_level_executable_assertion",
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
        chain.append({
            "stage": "required_function_public_contract_observation",
            "gate": "G4",
            "layer": "L5",
            "mechanism": function_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
            "evidence_scope": "public_contract_only",
        })
    return {
        "proposed_primary_failure_layer": primary,
        "proposed_secondary_failure_layers": _json(secondary),
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "failure_chain": _json(chain),
        "mechanism_tags": _json(mechanisms),
        "confidence": confidence,
        "uncertainty_notes": uncertainty,
        "proposed_healer_eligibility": eligibility,
        "proposed_healer_decision": "not_run",
        "rationale": rationale,
    }


# Each entry was separately assessed from its public contract and complete H0 source.
DECISIONS: dict[str, dict[str, Any]] = {
    "000357b8ea9e8c7519556e3a8c85625c29516c022be9ed61c9a8fdd3d229c169": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "model_assembly_failure"], "HIGH", "The tolerance assertion is a model-added variant rather than an AST-exact public assertion; it is nevertheless consistent with the public numeric example.", "conditional", "The required function uses a formula inconsistent with the public tetrahedron example, and the model-added executable assertion turns that public mismatch into the observed module-stage failure. Assert removal is only a candidate packaging rule and is not declared safe or sufficient.", "mathematical_error"),
    "01b6bac38cef8f198113a5cd475e8be41beccd60d7c559172443b76df714e34c": _decision("L4", ["L5"], ["module_level_executable_assertion", "semantic_goal_drift", "model_assembly_failure"], "HIGH", "The natural-language phrase 'sum of non-zero powers of 2' can be read broadly, but the public example unambiguously requires 10 to be accepted.", "conditional", "The function implements a single-power-of-two predicate, contradicting the public example; the copied executable assertion exposes that semantic mismatch during module execution. Assert removal remains an unvalidated candidate only.", "semantic_goal_drift"),
    "0460f62eee335e54ae79d20dba3f1c72d36982ade60d364ec6b3f5aa8c80feed": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public example directly fixes the required index convention.", "conditional", "The loop identifies the first n-digit triangular number but returns k-1, conflicting with the public index 4; the public assertion then blocks module execution. Assert removal is not presumed to repair the algorithm.", "algorithmic_error"),
    "0833737e006fd2c6b58fc71e5f03d64bd4b088689b09734f808c776659507990": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "control_flow_failure", "model_assembly_failure"], "MEDIUM", "The exact intended characterization beyond the public example is not fully stated, although the public case is decisive for this observation.", "conditional", "The bit-shift control flow returns false for the public input 10, and the copied assertion exposes that semantic/control-flow error at module load. Assert deletion is only a candidate packaging transformation.", "algorithmic_error"),
    "111a968cb6674525f58b26a0484603b9765056f5566cec9589d61af3733bc4c1": _decision("L4", [], ["text_parsing_control_flow_failure", "control_flow_failure", "model_assembly_failure"], "HIGH", "The contract specifies the public punctuation-bearing example but does not define behavior when no adverb exists.", "abstain", "The anchored regex rejects the public token containing trailing punctuation, so the required function reaches its explicit raise while the module assertion calls it. Repair would require choosing tokenization and position semantics, so no unique mechanical root repair is established.", "text_parsing_control_flow_failure"),
    "147d093943f1f9676c4d779f88a7478b62c2a71021f831900f136291bee3f2eb": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "semantic_goal_drift", "model_assembly_failure"], "HIGH", "The terse natural-language contract omits the intended formula, but the public numeric example is explicit.", "conditional", "The implemented standard vertical-parabola formula does not satisfy the public contract value; the copied assertion exposes the mathematical goal mismatch during module execution. No formula rewrite is Healer-eligible.", "mathematical_error"),
    "1ed09edb92c4da77d9ccb4eac0e420c2cbd4319a9d8a55e3340ea9f1a20544d8": _decision("L4", [], ["stdlib_regex_pattern_construction", "model_assembly_failure"], "HIGH", "A valid regex could be written in multiple ways; source evidence does not establish a unique invariant-preserving token replacement.", "abstain", "The required function constructs a malformed stdlib regular expression before returning, producing the observed G2 failure when called by the module assertion. This is general runtime/API assembly, not Domain API or infrastructure.", "stdlib_regex_pattern_construction"),
    "200edc3e0eec7ea9c2f029ace4027b019b020d97c66d503db848f9ff332ffc06": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public example directly fixes the required index convention.", "conditional", "The function returns k-1 after finding the first n-digit triangular number and conflicts with the public value; its copied assertion then interrupts module execution.", "algorithmic_error"),
    "20eb64bfb9e51b94a4d68b6dc2bbbc981199b59d0671e34d0df1695b0d261879": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "control_flow_failure", "model_assembly_failure"], "HIGH", "The public contract is terse, but the negative-discriminant early return visibly conflicts with the supplied example.", "conditional", "The function returns None for the public parameters before computing a directrix, so the copied assertion exposes a semantic/control-flow failure at module load.", "control_flow_failure"),
    "225def7e7fc2e4f0bdbede03a1813db354a4eff641e2de7b042c07a5608f106e": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "model_assembly_failure"], "HIGH", "The benchmark's integer-valued public example constrains the requested result, while general rounding policy is not described.", "conditional", "The function applies a magnitude-dependent rounding operation that does not satisfy the public surface-area example; the module assertion exposes the numerical error.", "mathematical_error"),
    "29c5dc38a71e4bf24dadf515e157b833b8a0d1b304c47bf98d36a325fbbe4342": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public example directly fixes the required index convention.", "conditional", "The function returns k-1 for the first n-digit triangular number and conflicts with the public example; the assertion exposes this during module execution.", "algorithmic_error"),
    "34f117accef513aaccebfa5edabc725dbc78ef1301e0ac16b4fb794b619a477b": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "edge_case_omission", "model_assembly_failure"], "HIGH", "Only the public example is used; no hidden cases are consulted.", "conditional", "The implementation tracks absolute prefix imbalance rather than the maximum imbalance over every substring, and its public assertion exposes the algorithmic mismatch.", "algorithmic_error"),
    "375d13b5bd61ef0ee7c0e92979f8c002d2ac3e98adb41426e8b9d6e27b176399": _decision("L4", ["L5"], ["module_level_executable_assertion", "control_flow_failure", "semantic_goal_drift", "model_assembly_failure"], "HIGH", "An alternate helper appears later, but the contract names only min_val; no alias inference is needed.", "conditional", "The required function returns None immediately when the first heterogeneous item is nonnumeric, so it never considers later numeric values required by the public example. The unused min_val_v2 does not change the required entry-point result.", "control_flow_failure"),
    "3ad5d1b48a0b82e99b69138c0bbead12450913eb8b7b049c8c101fb9acc5a34b": _decision("L4", ["L5"], ["module_level_executable_assertion", "semantic_goal_drift", "algorithmic_error", "model_assembly_failure"], "HIGH", "The phrase 'non-repeated elements' is potentially ambiguous in isolation, but the public expected sum resolves duplicate-value treatment for this contract.", "conditional", "The function sums only values occurring once, whereas the public example requires each distinct value once; the copied assertion exposes the semantic interpretation error.", "semantic_goal_drift"),
    "4583ad1011027d81314ddfb74bc8ec4cf1ae4feb9a37bac42da76177416c62c7": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The second branch does not alter the public off-by-one result.", "conditional", "Both return branches use k-1 for the first n-digit triangular number, conflicting with the public index; the assertion then interrupts module execution.", "algorithmic_error"),
    "4f6a1f242e4b63146785d435f3e0bcf3a50933bc9aec8a6045795b5d4e998a4b": _decision("L2", ["L4"], ["schema_mismatch", "semantic_goal_drift", "module_level_executable_assertion", "model_assembly_failure"], "HIGH", "The function name starts with is_, but the explicit task description and numeric public result control the contract.", "abstain", "The public contract requires the nth decagonal number, while every normal path returns a boolean predicate. This is an observable numeric-output contract violation; the module assertion is a later failure-chain stage. Fixing it requires replacing the algorithm, not a thin wrapper.", "numeric_output_contract_as_boolean"),
    "525f723f9a1c4712fdebc06ccdc6418f4de3a6e8651646cbec99288c5fee64b2": _decision("L4", ["L5"], ["module_level_executable_assertion", "parameter_semantics_swap", "mathematical_error", "model_assembly_failure"], "MEDIUM", "The natural-language contract does not label the three parameters, but the public example establishes the required observable result.", "conditional", "The function averages the smallest and largest of three values, which yields a value inconsistent with the public median-length example; the assertion exposes that parameter/geometry interpretation error.", "parameter_semantics_swap"),
    "629708e02e0157509188afabd3e23e38bf52328c6ba811dcf12363d83c7621a6": _decision("L4", ["L5"], ["module_level_executable_assertion", "control_flow_failure", "parameter_semantics_swap", "model_assembly_failure"], "HIGH", "The meaning of the third parameter is terse, but the added equality guard is unsupported by the public contract and rejects its example.", "conditional", "The function adds an a+b==c guard and returns None for the public inputs, so the copied assertion exposes an unsupported control-flow condition.", "control_flow_failure"),
    "6367b7adf0dcc6a964ff129d3713184a0bf42b89530700ec8c0e33b1d14d5849": _decision("L4", ["L5"], ["module_level_executable_assertion", "edge_case_omission", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public tuple fixes the position convention for the punctuation-bearing example; no hidden position cases are used.", "conditional", "The regex finds the public adverb, but the function returns an inclusive end index while the public contract expects 7; the copied assertion exposes the position-semantics error.", "edge_case_omission"),
    "730042eea50b8ad4aae34728ece3f1ab16b2bb97771f5b3ddd5e5745c7e71585": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "model_assembly_failure"], "HIGH", "The tolerance assertion is a model-added variant, but it preserves the public numeric target.", "conditional", "The source multiplies a tetrahedron-area expression by four and produces a value inconsistent with the public example; the executable tolerance assertion exposes the formula error.", "mathematical_error"),
    "7738db7659ec9333e7d321294197cb3c3fef5d5fc72f77a196e819256f5ed8b9": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public example directly fixes the required index convention.", "conditional", "The function returns k-1 after finding the first n-digit triangular number and conflicts with the public index; the copied assertion exposes the error.", "algorithmic_error"),
    "77ac3b8fbd623bdf0762d2ed6082720197b57f51a53b8c77fcd77523604f047d": _decision("L4", ["L5"], ["module_level_executable_assertion", "semantic_goal_drift", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public expected sum resolves the possible ambiguity in 'non-repeated elements' for this task.", "conditional", "The function excludes every repeated value instead of counting each distinct value once as required by the public example; the assertion exposes the semantic mismatch.", "semantic_goal_drift"),
    "84f71b53c98028b255fd361fab6deec391cb7e68bf49bd27e8a27950260897d1": _decision("L2", ["L4"], ["schema_mismatch", "semantic_goal_drift", "module_level_executable_assertion", "model_assembly_failure"], "HIGH", "Although the entry-point name is predicate-like, the task description and public expected value explicitly require a number.", "abstain", "The function computes the decagonal value but returns only a boolean about it, violating the public numeric return contract. The executable assertion is a later G2 failure-chain stage; correcting the output requires semantic code change.", "numeric_output_contract_as_boolean"),
    "c9972dbd1c76e4805401c1f08a4e25bf32b46c73b3be0befe79c623426dce6b2": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "model_assembly_failure"], "HIGH", "The public example is sufficient to show the mask is wrong; broader bit-width behavior remains for later correctness evaluation.", "conditional", "The constructed XOR mask toggles the wrong bit positions for the public input, and the copied assertion exposes the bit-mask algorithm error during module execution.", "algorithmic_error"),
    "f59c91131c769f305f410b20a5738e70c14be1ba72df0eba0fb4f7efe6af1987": _decision("L4", ["L5"], ["module_level_executable_assertion", "mathematical_error", "model_assembly_failure"], "MEDIUM", "The public expected integer constrains this cell, but the contract does not separately state a rounding convention.", "conditional", "The function returns the unrounded geometric expression, which does not equal the public contract value, so the copied assertion exposes a numerical-contract mismatch. A rounding or formula rewrite is not uniquely justified.", "mathematical_error"),
    "f85bb6c1efa65465700b139dec03e685dcf850a8f10c477b5c882562b3a06bae": _decision("L4", ["L5"], ["module_level_executable_assertion", "algorithmic_error", "edge_case_omission", "model_assembly_failure"], "HIGH", "The public example alone establishes the observed mismatch; hidden substring cases are not used.", "conditional", "The two passes maximize whole-prefix imbalance without resetting at adverse prefixes, so they do not implement a maximum over arbitrary substrings; the public assertion exposes the error.", "algorithmic_error"),
    "fc6b03344724ba3afc143f9306850b95b0a8abbdb043ee45f33e9635ce88f530": _decision("L4", ["L5"], ["module_level_executable_assertion", "parameter_semantics_swap", "mathematical_error", "model_assembly_failure"], "HIGH", "The parameter roles are terse in prose, but averaging all three visibly contradicts the public example.", "conditional", "The function averages all three inputs rather than the required trapezium median relation indicated by the public result; the copied assertion exposes the parameter-semantics error.", "parameter_semantics_swap"),
}


def build_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    verify_sources(root)
    diagnostics = [
        row for row in _read_csv(root / preparation.FORMAL_RESULTS)
        if row["phase"] == "G2_module"
    ]
    _require(len(diagnostics) == 27, "G2_module row count drift")
    _require(len({row["program_id"] for row in diagnostics}) == 27, "duplicate G2_module program")
    journals = {
        row["program_id"]: row for row in _read_jsonl(root / preparation.JOURNAL)
        if row["healer_account"] == "H0"
    }
    tasks = {row["task_id"]: row for row in _read_jsonl(root / preparation.TASKS)}
    _require(set(DECISIONS) == {row["program_id"] for row in diagnostics}, "decision identity set drift")
    rows: list[dict[str, Any]] = []
    for rank, diagnostic in enumerate(sorted(diagnostics, key=lambda row: row["program_id"]), 1):
        program_id = diagnostic["program_id"]
        journal = journals.get(program_id)
        _require(journal is not None, f"missing H0 source: {program_id}")
        assert journal is not None
        task = tasks.get(journal["task_id"])
        _require(task is not None, f"missing public contract: {program_id}")
        assert task is not None
        source = journal["evaluation_source"]
        _require(_sha(source.encode("utf-8")) == diagnostic["evaluation_source_sha256"], "source identity drift")
        tree = ast.parse(source)
        definitions = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == task["entry_point"]
        ]
        _require(len(definitions) == 1, "required function identity drift")
        definition = definitions[0]
        function_source = ast.get_source_segment(source, definition)
        _require(function_source is not None, "required function source extraction failed")
        imports, calls = _imports_and_calls(tree)
        source_lines = source.splitlines()
        candidate_line = int(diagnostic["model_source_line"]) - task["prompt"].count("\n")
        _require(1 <= candidate_line <= len(source_lines), "diagnostic source line drift")
        entry_signature = ast.unparse(definition.args)
        task_contract_hash = _sha((task["task_id"] + "\n" + task["prompt"] + "\n" + task["entry_point"] + "\n").encode("utf-8"))
        references = [
            f"{preparation.TASKS.as_posix()}#task_id={task['task_id']}",
            f"{preparation.JOURNAL.as_posix()}#program_id={program_id};healer_account=H0",
            f"{preparation.FORMAL_RESULTS.as_posix()}#cell_identity_sha256={diagnostic['cell_identity_sha256']}",
            f"{preparation.TAXONOMY_CODEBOOK.as_posix()}#sha256={SOURCE_HASHES[preparation.TAXONOMY_CODEBOOK]}",
        ]
        row = {
            "review_rank": rank,
            "program_id": program_id,
            "cell_identity_sha256": diagnostic["cell_identity_sha256"],
            "task_identity_sha256": diagnostic["task_identity_sha256"],
            "task_id": task["task_id"],
            "seed": journal["seed"],
            "generation_id": journal["generation_id"],
            "evaluation_source_sha256": diagnostic["evaluation_source_sha256"],
            "task_contract_sha256": task_contract_hash,
            "taxonomy_version": preparation.TAXONOMY_VERSION,
            "diagnostics_runner_revision": preparation.DIAGNOSTICS_RUNNER_REVISION,
            "adjudication_status": STATUS,
            "evidence_role": "development",
            "public_task_contract": _display_text(task["prompt"]),
            "required_entry_point": task["entry_point"],
            "required_signature": entry_signature,
            "required_function_source": _display_text(function_source),
            "required_function_start_line": definition.lineno,
            "required_function_end_line": definition.end_lineno,
            "module_level_executable_statements": _module_executable_statements(source, tree),
            "diagnostic_source_context_numbered": _numbered_context(source_lines, candidate_line),
            "diagnostic_phase": diagnostic["phase"],
            "diagnostic_exception_class": diagnostic["exception_class"],
            "diagnostic_candidate_line": candidate_line,
            "diagnostic_statement_ast": _node_at(tree, candidate_line, True),
            "diagnostic_ast_node": _node_at(tree, candidate_line),
            "imports": _json(imports),
            "api_calls": _json(calls),
            "g1_observation": "PASS",
            "g2_observation": "FAIL",
            "g3e_observation": "PASS",
            "g3a_observation": "NOT_APPLICABLE",
            "g3s_observation": "FAIL" if DECISIONS[program_id]["proposed_primary_failure_layer"] == "L2" else "NOT_ASSESSED",
            "g3c_observation": "NOT_APPLICABLE",
            "g4_observation": "PUBLIC_CONTRACT_OBSERVATION_ONLY_NOT_FORMAL_CORRECTNESS",
            **DECISIONS[program_id],
            "evidence_references": _json(references),
            "researcher_review_status": "",
            "researcher_notes": "",
            "researcher_id": "",
            "reviewed_at_utc": "",
        }
        rows.append(row)
    _require(Counter(row["diagnostic_exception_class"] for row in rows) == Counter({"AssertionError": 25, "PatternError": 1, "ValueError": 1}), "diagnostic class distribution drift")
    _require(Counter(row["proposed_primary_failure_layer"] for row in rows) == Counter({"L4": 25, "L2": 2}), "provisional layer distribution drift")
    _require(Counter(row["proposed_healer_eligibility"] for row in rows) == Counter({"conditional": 23, "abstain": 4}), "provisional eligibility distribution drift")
    _require(all(not row[field] for row in rows for field in ("researcher_review_status", "researcher_notes", "researcher_id", "reviewed_at_utc")), "researcher field must remain blank")
    return rows


def _summary_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    layer_counts = Counter(row["proposed_primary_failure_layer"] for row in rows)
    layer_rows = [{"layer": layer, "cells": layer_counts.get(layer, 0)} for layer in ("L0", "L1", "L2", "L3", "L4", "L5")]
    layer_rows.append({"layer": "UNRESOLVED", "cells": sum(not row["proposed_primary_failure_layer"] for row in rows)})
    mechanisms: Counter[str] = Counter()
    for row in rows:
        mechanisms.update(json.loads(row["mechanism_tags"]))
    mechanism_rows = [{"mechanism_tag": tag, "cells": count} for tag, count in sorted(mechanisms.items())]
    eligibility = Counter(row["proposed_healer_eligibility"] for row in rows)
    eligibility_rows = [{"proposed_healer_eligibility": value, "cells": eligibility.get(value, 0)} for value in ("eligible", "conditional", "abstain")]
    return layer_rows, mechanism_rows, eligibility_rows


def _report(rows: list[dict[str, Any]], layer_rows: list[dict[str, Any]], mechanism_rows: list[dict[str, Any]], eligibility_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3：G2_module AI-assisted provisional adjudication v1",
        "",
        f"狀態：`{STATUS}`。這不是正式人工裁決，也不是兩位真人獨立盲審；不計算 Cohen’s kappa。",
        "",
        "本 revision 只使用公開 task contract、完整 H0 required-function source、module-level executable statements、imports/API 與既有 coarse diagnostic phase/class/line。未使用 hidden expected/actual、correctness 結果、exception message 或 traceback。",
        "",
        "## 彙總",
        "",
        "### Primary layer",
        "",
        "| Layer | Cells |",
        "|---|---:|",
    ]
    lines.extend(f"| {row['layer']} | {row['cells']} |" for row in layer_rows)
    lines.extend(["", "### Proposed Healer eligibility", "", "| Status | Cells |", "|---|---:|"])
    lines.extend(f"| {row['proposed_healer_eligibility']} | {row['cells']} |" for row in eligibility_rows)
    lines.extend(["", "### Mechanism tags（非互斥）", "", "| Tag | Cells |", "|---|---:|"])
    lines.extend(f"| `{row['mechanism_tag']}` | {row['cells']} |" for row in mechanism_rows)
    lines.extend(["", "## 逐格 evidence packet 與 provisional adjudication", ""])
    for row in rows:
        lines.extend([
            f"### {int(row['review_rank']):02d}. `{row['program_id']}`",
            "",
            f"- Identity：task `{row['task_id']}`；seed `{row['seed']}`；cell `{row['cell_identity_sha256']}`",
            f"- Required entry point：`{row['required_entry_point']}({row['required_signature']})`",
            f"- Diagnostic：phase `{row['diagnostic_phase']}`；class `{row['diagnostic_exception_class']}`；candidate line `{row['diagnostic_candidate_line']}`；AST `{row['diagnostic_statement_ast']}/{row['diagnostic_ast_node']}`",
            f"- Imports：`{row['imports']}`",
            f"- API calls：`{row['api_calls']}`",
            "",
            "公開 task contract：",
            "",
            "```text",
            row["public_task_contract"].rstrip(),
            "```",
            "",
            f"Required function完整 source（原行 {row['required_function_start_line']}–{row['required_function_end_line']}）：",
            "",
            "```python",
            row["required_function_source"].rstrip(),
            "```",
            "",
            "Module-level executable statement完整內容：",
            "",
            "```python",
            row["module_level_executable_statements"].rstrip(),
            "```",
            "",
            "Diagnostic最少必要前後文：",
            "",
            "```text",
            row["diagnostic_source_context_numbered"].rstrip(),
            "```",
            "",
            "Provisional adjudication：",
            "",
            f"- Primary：`{row['proposed_primary_failure_layer']}`；secondary：`{row['proposed_secondary_failure_layers']}`",
            f"- Outcome validity：`{row['outcome_validity']}`",
            f"- Failure chain：`{row['failure_chain']}`",
            f"- Mechanisms：`{row['mechanism_tags']}`",
            f"- Confidence：`{row['confidence']}`",
            f"- Uncertainty：{row['uncertainty_notes']}",
            f"- Proposed Healer eligibility／decision：`{row['proposed_healer_eligibility']}`／`{row['proposed_healer_decision']}`",
            f"- Rationale：{row['rationale']}",
            f"- Evidence references：`{row['evidence_references']}`",
            "",
            "Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def build_outputs(root: Path = ROOT) -> dict[Path, bytes]:
    rows = build_rows(root)
    layer_rows, mechanism_rows, eligibility_rows = _summary_rows(rows)
    outputs: dict[Path, bytes] = {
        Path("ai_assisted_provisional_adjudication.csv"): _csv_bytes(FIELDS, rows),
        Path("layer_summary.csv"): _csv_bytes(("layer", "cells"), layer_rows),
        Path("mechanism_tag_summary.csv"): _csv_bytes(("mechanism_tag", "cells"), mechanism_rows),
        Path("healer_eligibility_summary.csv"): _csv_bytes(("proposed_healer_eligibility", "cells"), eligibility_rows),
        Path("ai_assisted_review_report_zh.md"): _report(rows, layer_rows, mechanism_rows, eligibility_rows).encode("utf-8"),
        Path("provenance.json"): _json_bytes({
            "revision": OUTPUT_RELATIVE.name,
            "start_head": START_HEAD,
            "taxonomy_version": preparation.TAXONOMY_VERSION,
            "diagnostics_runner_revision": preparation.DIAGNOSTICS_RUNNER_REVISION,
            "adjudication_status": STATUS,
            "evidence_role": "development",
            "formal_human_adjudication": False,
            "two_human_blind_review_claimed": False,
            "cohens_kappa_computed": False,
            "original_reviewer_worksheets_modified": False,
            "existing_provisional_recommendations_read": False,
            "correctness_results_loaded_or_used": False,
        }),
        Path("execution_manifest.json"): _json_bytes({
            "status": "ai_assisted_provisional_complete_researcher_review_pending",
            "cells": 27,
            "researcher_reviews_completed": 0,
            "model_calls": 0,
            "evalplus_correctness_executions": 0,
            "diagnostics_executions": 0,
            "healer_executions": 0,
            "validation_executions": 0,
            "new_correctness_tests": 0,
            "healer_runtime_input": False,
        }),
    }
    source_rows = [
        {"path": path.as_posix(), "sha256": digest, "access": "HASH_VERIFIED_ONLY" if path not in {preparation.FORMAL_RESULTS, preparation.JOURNAL, preparation.TASKS, preparation.TAXONOMY_CODEBOOK} else "PARSED_ALLOWED_FIELDS_ONLY"}
        for path, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())
    ]
    for path in (ANALYZER, TESTS):
        _require((root / path).is_file(), f"missing reproducibility source: {path}")
        source_rows.append({"path": path.as_posix(), "sha256": _sha((root / path).read_bytes()), "access": "REPRODUCIBILITY_SOURCE"})
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "sha256", "access"), source_rows)
    hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    outputs[Path("manifest.json")] = _json_bytes({
        "revision": OUTPUT_RELATIVE.name,
        "status": "AI_ASSISTED_PROVISIONAL_COMPLETE_FORMAL_HUMAN_ADJUDICATION_PENDING",
        "cells": 27,
        "adjudication_status": STATUS,
        "primary_layer_counts": {row["layer"]: row["cells"] for row in layer_rows},
        "healer_eligibility_counts": {row["proposed_healer_eligibility"]: row["cells"] for row in eligibility_rows},
        "researcher_reviews_completed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
    })
    return outputs


def write_outputs(root: Path = ROOT) -> Path:
    destination = root / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output revision already exists: {destination}")
    destination.mkdir(parents=True)
    for relative, data in build_outputs(root).items():
        (destination / relative).write_bytes(data)
    return destination


if __name__ == "__main__":
    print(write_outputs())
