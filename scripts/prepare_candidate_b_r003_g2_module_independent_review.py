#!/usr/bin/env python3
"""Freeze blinded reviewer worksheets for the 27 G2_module cells."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
except ModuleNotFoundError as exc:  # Support direct execution from scripts/.
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_independent_review_v1"
)
START_HEAD = "3a9ab182f52f00677b7816068d422e592fe1e6da"
PREPARATION_MANIFEST = preparation.OUTPUT_RELATIVE / "manifest.json"
PREPARATION_CSV = preparation.OUTPUT_RELATIVE / "classification_preparation.csv"
PREPARATION_MANIFEST_SHA256 = "6c6aa8482348b5aa30d9809d3ba1e4c31e3d16a00a8e2e5b9c8ab723d2d7a142"
PREPARATION_CSV_SHA256 = "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c"
ANALYZER = Path("scripts/prepare_candidate_b_r003_g2_module_independent_review.py")
TESTS = Path("tests/finals_rebuild/test_candidate_b_r003_g2_module_independent_review.py")
PROVISIONAL_STATUS = "AI_ASSISTED_PROVISIONAL_NOT_FORMAL_ADJUDICATION"

SOURCE_HASHES = {
    **preparation.SOURCE_HASHES,
    PREPARATION_MANIFEST: PREPARATION_MANIFEST_SHA256,
    PREPARATION_CSV: PREPARATION_CSV_SHA256,
}

PACKET_FIELDS = (
    "review_rank",
    "program_id",
    "cell_identity_sha256",
    "task_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "evaluation_source_sha256",
    "task_contract_sha256",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "combined_model_source_line",
    "candidate_source_line",
    "failure_statement_ast",
    "failure_ast_node",
    "failure_location_kind",
    "required_entry_point",
    "static_signature",
    "static_entry_point_present",
    "static_signature_compatible",
    "runtime_entry_point_bound",
    "runtime_signature_binding",
    "import_modules",
    "import_classification",
    "public_assert_relation",
    "public_assert_ast_sha256",
    "source_context_sha256",
    "minimal_source_evidence_summary",
    "g1_observation",
    "g2_observation",
    "g3e_observation",
    "g3a_observation",
    "g3s_observation",
    "g3c_observation",
    "g4_observation",
    "generation_truncated",
    "evidence_completeness",
    "evidence_references",
)

REVIEW_DECISION_FIELDS = (
    "reviewer_decision",
    "primary_failure_layer",
    "secondary_failure_layers",
    "outcome_validity",
    "failure_chain",
    "mechanism_tags",
    "confidence",
    "uncertainty_notes",
    "needs_second_review",
    "healer_eligibility",
    "healer_decision",
    "healer_outcome",
    "reviewer_id",
    "adjudicated_at_utc",
)

WORKSHEET_FIELDS = ("worksheet_role",) + PACKET_FIELDS + REVIEW_DECISION_FIELDS

PROVISIONAL_FIELDS = (
    "review_rank",
    "program_id",
    "cell_identity_sha256",
    "provisional_status",
    "provisional_primary_failure_layer",
    "provisional_secondary_failure_layers",
    "provisional_outcome_validity",
    "provisional_failure_chain",
    "provisional_mechanism_tags",
    "provisional_failure_subtype",
    "provisional_confidence",
    "provisional_uncertainty_notes",
    "provisional_needs_second_review",
    "provisional_healer_eligibility",
    "provisional_healer_decision",
    "provisional_healer_outcome",
    "assert_removal_rule_assessment",
    "recommendation_basis",
    "evidence_references",
)

DISAGREEMENT_FIELDS = (
    "review_rank",
    "program_id",
    "cell_identity_sha256",
    "reviewer_a_id",
    "reviewer_a_decision",
    "reviewer_a_primary_failure_layer",
    "reviewer_a_outcome_validity",
    "reviewer_b_id",
    "reviewer_b_decision",
    "reviewer_b_primary_failure_layer",
    "reviewer_b_outcome_validity",
    "disagreement_present",
    "disagreement_fields",
    "adjudicator_id",
    "adjudication_decision",
    "adjudicated_primary_failure_layer",
    "adjudicated_outcome_validity",
    "adjudication_rationale",
    "adjudicated_at_utc",
)


class ReviewPreparationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewPreparationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unique(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row[key])
        _require(value and value not in result, f"{label} duplicate or missing {key}")
        result[value] = row
    return result


def _node_at(tree: ast.AST, line: int, statement_only: bool) -> str:
    base = ast.stmt if statement_only else ast.AST
    nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, base)
        and hasattr(node, "lineno")
        and int(node.lineno) <= line <= int(getattr(node, "end_lineno", -1))
    ]
    if not nodes:
        return "UNRESOLVED"
    nodes.sort(
        key=lambda node: (
            int(getattr(node, "end_lineno", line)) - int(node.lineno),
            -int(getattr(node, "col_offset", 0)),
        )
    )
    return type(nodes[0]).__name__


def _imports(tree: ast.AST) -> list[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return sorted(modules)


def _import_classification(modules: list[str]) -> str:
    if not modules:
        return "NONE"
    categories = [f"{module}:STDLIB" if module in sys.stdlib_module_names else f"{module}:THIRD_PARTY_OR_LOCAL_REVIEW" for module in modules]
    return ";".join(categories)


def _prompt_asserts(prompt: str) -> list[ast.Assert]:
    assertions: list[ast.Assert] = []
    for line in prompt.splitlines():
        value = line.strip()
        if not value.startswith("assert "):
            continue
        try:
            node = ast.parse(value).body[0]
        except SyntaxError:
            continue
        if isinstance(node, ast.Assert):
            assertions.append(node)
    return assertions


def _top_level_entry_assert(tree: ast.Module, entry_point: str) -> ast.Assert | None:
    for node in tree.body:
        if not isinstance(node, ast.Assert):
            continue
        calls = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        if entry_point in calls:
            return node
    return None


def _assert_relation(candidate: ast.Assert, prompt_asserts: list[ast.Assert]) -> str:
    candidate_dump = ast.dump(candidate, include_attributes=False)
    if candidate_dump in {ast.dump(node, include_attributes=False) for node in prompt_asserts}:
        return "PUBLIC_CONTRACT_ASSERT_AST_EXACT"
    return "REQUIRED_ENTRY_ASSERT_VARIANT_NOT_CONTRACT_EXACT"


def _contract_summary(prompt: str) -> str:
    lines = [line.strip().replace('"', "") for line in prompt.splitlines()]
    for line in lines:
        if line and not line.startswith("assert ") and not line.startswith("def "):
            return re.sub(r"\s+", " ", line)[:180]
    return "PUBLIC_CONTRACT_DESCRIPTION_UNRESOLVED"


def _provisional(packet: dict[str, Any]) -> dict[str, Any]:
    relation = packet["public_assert_relation"]
    location = packet["failure_location_kind"]
    if location == "FUNCTION_RAISE_EXPOSED_BY_MODULE_ASSERT":
        primary_layer = "L4"
        subtype = "STDLIB_TEXT_PARSING_CONTROL_FLOW_RAISE"
        mechanisms = ["control_flow_failure", "model_assembly_failure"]
        confidence = "MEDIUM"
        uncertainty = "公開contract未明定no-match行為；須人工判斷runtime control-flow、output contract或semantic責任邊界。"
        eligibility = "noneligible"
        removal = "ASSERT_REMOVAL_WOULD_ONLY_HIDE_FUNCTION_FAILURE_NOT_A_SAFE_ROOT_FIX"
        basis = "公開contract assert呼叫required function；stdlib文字解析未找到adverb後主動raise，module import因此中斷。"
        chain_mechanism = "text_parsing_control_flow_raise"
    elif location == "FUNCTION_REGEX_PATTERN_ERROR_EXPOSED_BY_MODULE_ASSERT":
        primary_layer = "L4"
        subtype = "STDLIB_REGEX_PATTERN_CONSTRUCTION_ERROR"
        mechanisms = ["model_assembly_failure"]
        confidence = "HIGH"
        uncertainty = "需人工確認一般stdlib API assembly與更早semantic pattern設計之failure chain；不得視為Domain API。"
        eligibility = "noneligible"
        removal = "ASSERT_REMOVAL_WOULD_ONLY_HIDE_REGEX_RUNTIME_FAILURE_NOT_A_SAFE_ROOT_FIX"
        basis = "公開contract要求字串pattern；source使用stdlib re且pattern construction在required function內失敗，無第三方或environment證據。"
        chain_mechanism = "stdlib_regex_pattern_construction"
    elif relation == "PUBLIC_CONTRACT_ASSERT_AST_EXACT":
        primary_layer = ""
        subtype = "PUBLIC_CONTRACT_ASSERTION_EXPOSES_FUNCTION_MISMATCH"
        mechanisms = ["model_assembly_failure", "control_flow_failure"]
        confidence = "MEDIUM"
        uncertainty = "top-level public assert造成最早G2阻斷，但required function的semantic mismatch可能屬後續failure chain；須逐格人工裁決。"
        eligibility = "undetermined"
        removal = "CANDIDATE_ONLY_REQUIRES_INDEPENDENT_SAFETY_REVIEW_NO_TRANSFORMATION_PERFORMED"
        basis = "candidate top-level assert與公開contract assert AST完全一致；AssertionError暴露required function與公開example不一致，同時assert本身阻斷module execution。"
        chain_mechanism = "public_contract_assertion_mismatch"
    else:
        primary_layer = ""
        subtype = "MODEL_ADDED_REQUIRED_ENTRY_ASSERT_VARIANT"
        mechanisms = ["model_assembly_failure", "control_flow_failure"]
        confidence = "LOW"
        uncertainty = "assert呼叫required function但並非公開contract AST全等；須分辨assert條件變體與function semantics，根因不唯一。"
        eligibility = "undetermined"
        removal = "CANDIDATE_ONLY_ROOT_CAUSE_AMBIGUOUS_MUST_ABSTAIN_PENDING_TWO_REVIEWS"
        basis = "model新增required-entry numeric assertion變體；module execution由該assert中斷，但公開證據不足以唯一分離assert條件與function結果責任。"
        chain_mechanism = "model_added_assert_variant"
    chain = [
        {
            "gate": "G2",
            "layer": primary_layer or None,
            "mechanism": "top_level_executable_assertion",
            "stage": "module_execution",
        },
        {
            "gate": "G4",
            "layer": None,
            "mechanism": chain_mechanism,
            "stage": "required_function_behavior",
            "status": "REQUIRES_HUMAN_REVIEW",
        },
    ]
    return {
        "review_rank": packet["review_rank"],
        "program_id": packet["program_id"],
        "cell_identity_sha256": packet["cell_identity_sha256"],
        "provisional_status": PROVISIONAL_STATUS,
        "provisional_primary_failure_layer": primary_layer,
        "provisional_secondary_failure_layers": "[]",
        "provisional_outcome_validity": "VALID_MODEL_OUTCOME",
        "provisional_failure_chain": _compact(chain),
        "provisional_mechanism_tags": _compact(mechanisms),
        "provisional_failure_subtype": subtype,
        "provisional_confidence": confidence,
        "provisional_uncertainty_notes": uncertainty,
        "provisional_needs_second_review": "true",
        "provisional_healer_eligibility": eligibility,
        "provisional_healer_decision": "not_run",
        "provisional_healer_outcome": "not_assessed",
        "assert_removal_rule_assessment": removal,
        "recommendation_basis": basis,
        "evidence_references": packet["evidence_references"],
    }


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    tables = preparation.load_tables(repo)
    prepared_rows = _read_csv(repo / PREPARATION_CSV)
    prepared = _unique(prepared_rows, "program_id", "machine preparation")
    diagnostics = [row for row in tables["diagnostics"] if row["phase"] == "G2_module"]
    _require(len(diagnostics) == 27, "G2_module count drift")
    _require(len({row["program_id"] for row in diagnostics}) == 27, "G2_module duplicate program")
    journal = _unique(
        [row for row in tables["journal"] if row["healer_account"] == "H0"],
        "program_id",
        "H0 journal",
    )
    crosswalk = _unique(tables["crosswalk"], "program_id", "crosswalk")
    tasks = _unique(tables["tasks"], "task_id", "public task contracts")
    packets: list[dict[str, Any]] = []
    relation_counts = Counter()
    location_counts = Counter()
    import_counts = Counter()

    for rank, diagnostic in enumerate(sorted(diagnostics, key=lambda row: row["program_id"]), 1):
        program_id = diagnostic["program_id"]
        prep = prepared.get(program_id)
        source_row = journal.get(program_id)
        xrow = crosswalk.get(program_id)
        _require(prep is not None and source_row is not None and xrow is not None, "G2_module identity join missing")
        assert prep is not None and source_row is not None and xrow is not None
        _require(prep["diagnostic_phase"] == "G2_module", "preparation phase drift")
        _require(prep["classification_status"] == "PENDING_REVIEW" and not prep["primary_failure_layer"], "machine preparation unexpectedly adjudicated")
        _require(prep["cell_identity_sha256"] == diagnostic["cell_identity_sha256"], "cell identity drift")
        _require(prep["evaluation_source_sha256"] == diagnostic["evaluation_source_sha256"], "source identity drift")
        task = tasks.get(xrow["task_id"])
        _require(task is not None, "public task contract missing")
        assert task is not None
        source = source_row["evaluation_source"]
        _require(_sha(source.encode("utf-8")) == diagnostic["evaluation_source_sha256"], "source bytes hash drift")
        tree = ast.parse(source)
        combined_line = int(diagnostic["model_source_line"])
        source_line = combined_line - task["prompt"].count("\n")
        source_lines = source.splitlines()
        _require(1 <= source_line <= len(source_lines), "candidate source line offset unresolved")
        statement = _node_at(tree, source_line, True)
        ast_node = _node_at(tree, source_line, False)
        definitions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == task["entry_point"]
        ]
        _require(len(definitions) == 1, "required entry point definition count drift")
        signature = ast.unparse(definitions[0].args)
        top_assert = _top_level_entry_assert(tree, task["entry_point"])
        _require(top_assert is not None, "module failure lacks required-entry top-level assertion")
        assert top_assert is not None
        relation = _assert_relation(top_assert, _prompt_asserts(task["prompt"]))
        modules = _imports(tree)
        import_classification = _import_classification(modules)
        _require("THIRD_PARTY" not in import_classification, "unexpected non-stdlib import requires separate review")
        machine_evidence = json.loads(xrow["machine_evidence"])
        _require(machine_evidence.get("generation_truncated") is False, "unexpected truncation evidence")
        _require(machine_evidence.get("expected_entry_point_present") is True, "static entry point evidence drift")
        if statement == "Assert" and diagnostic["exception_class"] == "AssertionError":
            location = "TOP_LEVEL_ASSERT_EXECUTION"
            summary = "module-level assert invokes required entry point; assertion operands are not copied into packet"
        elif statement == "Raise" and diagnostic["exception_class"] == "ValueError":
            location = "FUNCTION_RAISE_EXPOSED_BY_MODULE_ASSERT"
            summary = "required function reaches explicit no-match raise; public assert at module level exposes it"
        elif statement == "Return" and diagnostic["exception_class"] == "PatternError":
            location = "FUNCTION_REGEX_PATTERN_ERROR_EXPOSED_BY_MODULE_ASSERT"
            summary = "required function constructs stdlib regex in return path; public assert at module level exposes pattern error"
        else:
            raise ReviewPreparationError("unexpected G2_module evidence pattern")
        relation_counts[relation] += 1
        location_counts[location] += 1
        import_counts[import_classification] += 1
        references = [
            f"{preparation.FORMAL_RESULTS.as_posix()}#cell_identity_sha256={diagnostic['cell_identity_sha256']}",
            f"{preparation.JOURNAL.as_posix()}#program_id={program_id};healer_account=H0",
            f"{preparation.TASKS.as_posix()}#task_id={xrow['task_id']}",
            f"{preparation.CROSSWALK.as_posix()}#program_id={program_id}",
            f"{PREPARATION_CSV.as_posix()}#program_id={program_id}",
        ]
        packet = {
            "review_rank": rank,
            "program_id": program_id,
            "cell_identity_sha256": diagnostic["cell_identity_sha256"],
            "task_identity_sha256": diagnostic["task_identity_sha256"],
            "task_id": xrow["task_id"],
            "seed": xrow["seed"],
            "generation_id": prep["generation_id"],
            "evaluation_source_sha256": diagnostic["evaluation_source_sha256"],
            "task_contract_sha256": prep["task_contract_sha256"],
            "diagnostic_phase": "G2_module",
            "diagnostic_exception_class": diagnostic["exception_class"],
            "combined_model_source_line": combined_line,
            "candidate_source_line": source_line,
            "failure_statement_ast": statement,
            "failure_ast_node": ast_node,
            "failure_location_kind": location,
            "required_entry_point": task["entry_point"],
            "static_signature": signature,
            "static_entry_point_present": "true",
            "static_signature_compatible": "true",
            "runtime_entry_point_bound": diagnostic["entry_point_bound"],
            "runtime_signature_binding": diagnostic["signature_binding"],
            "import_modules": _compact(modules),
            "import_classification": import_classification,
            "public_assert_relation": relation,
            "public_assert_ast_sha256": _sha((ast.dump(top_assert, include_attributes=False) + "\n").encode("utf-8")),
            "source_context_sha256": _sha((source_lines[source_line - 1].strip() + "\n").encode("utf-8")),
            "minimal_source_evidence_summary": summary,
            "g1_observation": "PASS",
            "g2_observation": "FAIL",
            "g3e_observation": "PASS_STATIC_RUNTIME_NOT_REACHED",
            "g3a_observation": "NOT_APPLICABLE",
            "g3s_observation": "NOT_ASSESSED",
            "g3c_observation": "NOT_APPLICABLE",
            "g4_observation": "FROZEN_FAIL_NOT_USED_FOR_LAYER_OR_HEALER",
            "generation_truncated": "false",
            "evidence_completeness": "COMPLETE_FOR_INDEPENDENT_REVIEW_NO_HIDDEN_VALUES",
            "evidence_references": _compact(references),
        }
        packets.append(packet)

    _require(len(packets) == 27, "review packet completeness drift")
    _require(location_counts == Counter({"TOP_LEVEL_ASSERT_EXECUTION": 25, "FUNCTION_RAISE_EXPOSED_BY_MODULE_ASSERT": 1, "FUNCTION_REGEX_PATTERN_ERROR_EXPOSED_BY_MODULE_ASSERT": 1}), "failure location distribution drift")
    _require(relation_counts == Counter({"PUBLIC_CONTRACT_ASSERT_AST_EXACT": 25, "REQUIRED_ENTRY_ASSERT_VARIANT_NOT_CONTRACT_EXACT": 2}), "public assert relation distribution drift")
    worksheets: dict[str, list[dict[str, Any]]] = {}
    for role in ("REVIEWER_A_INDEPENDENT", "REVIEWER_B_INDEPENDENT_BLINDED"):
        worksheets[role] = [
            {"worksheet_role": role, **packet, **{field: "" for field in REVIEW_DECISION_FIELDS}}
            for packet in packets
        ]
    disagreements = [
        {
            "review_rank": packet["review_rank"],
            "program_id": packet["program_id"],
            "cell_identity_sha256": packet["cell_identity_sha256"],
            **{field: "" for field in DISAGREEMENT_FIELDS[3:]},
        }
        for packet in packets
    ]
    provisional = [_provisional(packet) for packet in packets]
    audit = {
        "status": "g2_module_independent_review_materials_complete",
        "cells": 27,
        "fixed_order": "program_id_ascending",
        "reviewer_a_blank_rows": 27,
        "reviewer_b_blank_rows": 27,
        "disagreement_blank_rows": 27,
        "provisional_rows": 27,
        "reviewer_identity_values_present": 0,
        "reviewer_decision_values_present": 0,
        "formal_adjudications_completed": 0,
        "source_hashes_verified": len(SOURCE_HASHES),
        "location_counts": dict(sorted(location_counts.items())),
        "public_assert_relation_counts": dict(sorted(relation_counts.items())),
        "import_classification_counts": dict(sorted(import_counts.items())),
        "all_required_entry_points_present": True,
        "all_static_signatures_compatible": True,
        "truncation_cells": 0,
        "domain_api_import_cells": 0,
        "third_party_import_cells": 0,
        "hidden_expected_actual_message_traceback_used": False,
        "candidate_execution_performed": False,
        "reviewer_b_blinded_from_reviewer_a_decisions": True,
    }
    return {
        "packets": packets,
        "reviewer_A": worksheets["REVIEWER_A_INDEPENDENT"],
        "reviewer_B": worksheets["REVIEWER_B_INDEPENDENT_BLINDED"],
        "disagreements": disagreements,
        "provisional": provisional,
        "audit": audit,
    }


def _guide() -> str:
    return """# G2_module 27格雙人獨立review操作說明

1. Reviewer A與Reviewer B分別取得自己的blank worksheet；兩份表的evidence相同，但在B完成前不得向B顯示A的任何decision。
2. `review_packets.csv`只含公開contract、source/AST最小結構證據與固定identity，不含hidden input、expected/actual、exception message或traceback。
3. `provisional_recommendations.csv`是AI輔助建議，固定標示 `AI_ASSISTED_PROVISIONAL_NOT_FORMAL_ADJUDICATION`；不得預填或複製到reviewer worksheet。
4. 25格top-level assert須逐格判定：公開assert是否精確、required function是否另有semantic問題、assert是否單獨阻斷G2及failure chain是否多層。不得整批貼label。
5. Reviewer須親自查看evidence references後填入reviewer_id與UTC時間；空白不得由script或AI補值。
6. 兩位review完成後才建立比較；有任一欄不一致即填入disagreement表並由第三位adjudicator處理。
7. top-level assert移除僅是候選假說。本輪不得轉換、執行或以移除後結果判定安全性。
8. 本批不執行模型、EvalPlus、diagnostics、Healer或validation。
"""


def build_outputs(repo: Path = REPO_ROOT) -> dict[Path, bytes]:
    analysis = build_analysis(repo)
    outputs: dict[Path, bytes] = {
        Path("review_packets.csv"): _csv_bytes(PACKET_FIELDS, analysis["packets"]),
        Path("reviewer_A_blank.csv"): _csv_bytes(WORKSHEET_FIELDS, analysis["reviewer_A"]),
        Path("reviewer_B_blank.csv"): _csv_bytes(WORKSHEET_FIELDS, analysis["reviewer_B"]),
        Path("disagreement_adjudication_blank.csv"): _csv_bytes(DISAGREEMENT_FIELDS, analysis["disagreements"]),
        Path("provisional_recommendations.csv"): _csv_bytes(PROVISIONAL_FIELDS, analysis["provisional"]),
        Path("evidence_completeness_audit.json"): _json_bytes(analysis["audit"]),
        Path("independent_review_protocol_zh.md"): _guide().encode("utf-8"),
        Path("provenance.json"): _json_bytes({
            "analysis_version": OUTPUT_RELATIVE.name,
            "start_head": START_HEAD,
            "taxonomy_version": preparation.TAXONOMY_VERSION,
            "diagnostics_runner_revision": preparation.DIAGNOSTICS_RUNNER_REVISION,
            "machine_preparation_manifest_sha256": PREPARATION_MANIFEST_SHA256,
            "machine_preparation_modified": False,
            "formal_diagnostics_modified": False,
            "formal_human_adjudication_completed": False,
            "reviewer_id_values_written": False,
            "adjudication_timestamps_written": False,
        }),
        Path("execution_manifest.json"): _json_bytes({
            "status": "independent_reviewer_worksheets_prepared_not_reviewed",
            "cells": 27,
            "reviewer_a_completed": False,
            "reviewer_b_completed": False,
            "formal_adjudications_completed": 0,
            "model_calls": 0,
            "evalplus_correctness_executions": 0,
            "diagnostics_executions": 0,
            "formal_diagnostics_executions": 0,
            "partial_diagnostics_executions": 0,
            "healer_executions": 0,
            "validation_executions": 0,
            "healer_runtime_input": False,
        }),
    }
    source_rows = [
        {
            "path": path.as_posix(),
            "role": "external_taxonomy_codebook" if path.is_absolute() else "frozen_input",
            "sha256": digest,
        }
        for path, digest in sorted(SOURCE_HASHES.items(), key=lambda item: item[0].as_posix())
    ]
    for path in (ANALYZER, TESTS):
        _require((repo / path).is_file(), f"missing reproducibility source: {path.as_posix()}")
        source_rows.append({"path": path.as_posix(), "role": "reproducibility_source", "sha256": _sha((repo / path).read_bytes())})
    outputs[Path("source_hash_ledger.csv")] = _csv_bytes(("path", "role", "sha256"), source_rows)
    output_hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    outputs[Path("manifest.json")] = _json_bytes({
        "manifest_version": OUTPUT_RELATIVE.name,
        "status": "reviewer_worksheets_prepared_formal_adjudication_not_started",
        "cells": 27,
        "reviewer_worksheets": 2,
        "double_independent_review_required": True,
        "provisional_status": PROVISIONAL_STATUS,
        "formal_adjudications_completed": 0,
        "reviewer_id_values_present": 0,
        "adjudication_timestamps_present": 0,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "source_sha256": {
            ANALYZER.as_posix(): _sha((repo / ANALYZER).read_bytes()),
            TESTS.as_posix(): _sha((repo / TESTS).read_bytes()),
        },
        "outputs_sha256_excluding_manifest": output_hashes,
    })
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    directory = repo / OUTPUT_RELATIVE
    directory.mkdir(parents=True, exist_ok=True)
    for relative, data in build_outputs(repo).items():
        (directory / relative).write_bytes(data)
    return directory


if __name__ == "__main__":
    print(write_outputs())
