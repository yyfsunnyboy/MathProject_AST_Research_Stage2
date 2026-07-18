#!/usr/bin/env python3
"""Build development-only readiness assets for the final MBPP+ 2x2 evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

INTEGRATED_RELATIVE = Path(
    "artifacts/public_benchmark_governance/milestone_2g_integrated_development_evidence"
)
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/factorial_evaluation_readiness_v1"
)

LEDGER_RELATIVE = INTEGRATED_RELATIVE / "integrated_development_cell_ledger.csv"
RULES_RELATIVE = INTEGRATED_RELATIVE / "healer_candidate_rule_ledger.csv"
M2G_MANIFEST_RELATIVE = INTEGRATED_RELATIVE / "milestone_2g_manifest.json"

PIPELINE_SPEC = "agent_tools.finals_rebuild.extraction.extract_code"
PIPELINE_SPEC_COMMIT = "c5094bb7"
PLAN_STATUS = "draft_not_activated_pending_final_p1_and_healer_freeze"

TRIGGER_FIELDS = (
    "rule_id", "signature", "recommended_status", "p0_trigger_cells",
    "p0_trigger_unique_tasks", "p0_trigger_task_ids", "scaffold_trigger_cells",
    "scaffold_trigger_unique_tasks", "scaffold_trigger_task_ids",
    "discovery_p0_cells", "expansion_p0_cells", "scaffold_v0_cells",
    "candidate_a_cells", "expected_repairable_signature", "semantic_risk",
    "abstention_conditions", "same_rule_version_required", "development_only",
)

RULE_SIGNATURES = {
    "entrypoint_alias_unique_arity_compatible_v0": "entrypoint_unique_arity_compatible_candidate",
    "syntax_parse_failure_generic": "syntax_parse_failure",
    "truncation_completion": "generation_length_termination",
    "format_packaging_extraction": "format_or_packaging_extraction_failure",
    "generic_unknown_failure": "generic_evaluator_failure_unknown",
    "import_dependency_unknown": "import_or_dependency_failure_uniquely_evidenced",
}


class FactorialReadinessError(RuntimeError):
    """Raised before writes when 2x2 readiness evidence drifts."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FactorialReadinessError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _matches(row: dict[str, str], prefix: str, signature: str) -> bool:
    if signature == "generation_length_termination":
        return row[f"{prefix}_truncated"] == "true"
    return row[f"{prefix}_failure_signature"] == signature


def _support(
    ledger: list[dict[str, str]], prefix: str, signature: str,
    *, layer: str | None = None,
) -> list[dict[str, str]]:
    return [
        row for row in ledger
        if (layer is None or row["development_layer"] == layer)
        and _matches(row, prefix, signature)
    ]


def build_analysis(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ledger = _read_csv(repo_root / LEDGER_RELATIVE)
    rules = _read_csv(repo_root / RULES_RELATIVE)
    manifest = _read_json(repo_root / M2G_MANIFEST_RELATIVE)
    _require(len(ledger) == 300, "integrated identity count drift")
    _require(len({(row["task_id"], row["seed"]) for row in ledger}) == 300, "duplicate identity")
    _require(len({row["task_id"] for row in ledger}) == 60, "task count drift")
    _require(sum(int(row["program_count_represented"]) for row in ledger) == 600, "program count drift")
    _require(manifest["pipeline_correction_is_healer"] is False, "Pipeline/Healer accounting drift")
    _require({row["rule_id"] for row in rules} == set(RULE_SIGNATURES), "rule set drift")

    trigger_rows: list[dict[str, str]] = []
    for rule in rules:
        rule_id = rule["rule_id"]
        signature = RULE_SIGNATURES[rule_id]
        p0 = _support(ledger, "baseline", signature)
        scaffold = _support(ledger, "treatment", signature)
        d_p0 = _support(ledger, "baseline", signature, layer="discovery_development")
        e_p0 = _support(ledger, "baseline", signature, layer="expansion_development")
        sv0 = _support(ledger, "treatment", signature, layer="discovery_development")
        ca = _support(ledger, "treatment", signature, layer="expansion_development")
        p0_tasks = sorted({row["task_id"] for row in p0})
        scaffold_tasks = sorted({row["task_id"] for row in scaffold})
        trigger_rows.append({
            "rule_id": rule_id,
            "signature": signature,
            "recommended_status": rule["recommended_status"],
            "p0_trigger_cells": str(len(p0)),
            "p0_trigger_unique_tasks": str(len(p0_tasks)),
            "p0_trigger_task_ids": "|".join(p0_tasks),
            "scaffold_trigger_cells": str(len(scaffold)),
            "scaffold_trigger_unique_tasks": str(len(scaffold_tasks)),
            "scaffold_trigger_task_ids": "|".join(scaffold_tasks),
            "discovery_p0_cells": str(len(d_p0)),
            "expansion_p0_cells": str(len(e_p0)),
            "scaffold_v0_cells": str(len(sv0)),
            "candidate_a_cells": str(len(ca)),
            "expected_repairable_signature": (
                signature if rule["recommended_status"] == "eligible_for_implementation" else "none_currently"
            ),
            "semantic_risk": rule["semantic_risk"],
            "abstention_conditions": rule["abstention_conditions"],
            "same_rule_version_required": "true",
            "development_only": "true",
        })

    eligible = next(row for row in trigger_rows if row["recommended_status"] == "eligible_for_implementation")
    _require(eligible["rule_id"] == "entrypoint_alias_unique_arity_compatible_v0", "eligible rule drift")
    _require(
        (eligible["p0_trigger_cells"], eligible["p0_trigger_unique_tasks"]) == ("40", "16")
        and (eligible["scaffold_trigger_cells"], eligible["scaffold_trigger_unique_tasks"]) == ("2", "1"),
        "factorial entry-point support drift",
    )
    return {
        "trigger_rows": trigger_rows,
        "source_hashes": {
            relative.as_posix(): _sha256((repo_root / relative).read_bytes())
            for relative in (LEDGER_RELATIVE, RULES_RELATIVE, M2G_MANIFEST_RELATIVE)
        },
    }


def _accounting_spec() -> dict[str, Any]:
    return {
        "spec_version": "mbpp_factorial_accounting_v1_draft",
        "status": PLAN_STATUS,
        "factorial_arms": ["P0_H0", "P0_H1", "P1_H0", "P1_H1"],
        "generation_arms": {
            "P0": "official prompt only",
            "P1": "final frozen Scaffold; exact text and hash pending",
        },
        "normalization": {
            "order": "generation -> frozen Pipeline normalization -> H0/H1 fork",
            "spec": PIPELINE_SPEC,
            "spec_commit": PIPELINE_SPEC_COMMIT,
            "same_version_for_p0_and_p1": True,
            "extraction_fence_stripping_plain_text_normalization_are_healer": False,
            "normalization_result_identity_must_match_across_h0_h1": True,
        },
        "healer_accounts": {
            "H0": "evaluate frozen normalized output unchanged",
            "H1": "apply the final frozen evaluator-blind Healer to the same normalized output, then evaluate",
            "same_healer_version_for_p0_and_p1": True,
            "same_rule_order_for_p0_and_p1": True,
            "same_guards_and_abstention_for_p0_and_p1": True,
            "model_regeneration_for_healer": False,
            "evaluator_used_for_trigger_selection_or_acceptance": False,
        },
        "identity_invariants": {
            "generation_identity": ["prompt_arm", "task_id", "seed", "generation_id"],
            "h0_h1_share_generation_id": True,
            "h0_h1_share_raw_sha256": True,
            "h0_h1_share_pipeline_input_and_normalized_sha256": True,
            "exactly_one_model_attempt_per_prompt_arm_identity": True,
        },
        "itt": {
            "pipeline_extraction_failure_retained": True,
            "healer_abstention_retained": True,
            "protocol_violation_retained": True,
            "selective_retry_or_exclusion": False,
        },
        "raw_deployment_packaging_ablation": {
            "allowed_as_separate_optional_account": True,
            "part_of_formal_factorial": False,
            "may_not_replace_pipeline_or_healer_accounts": True,
            "results_must_be_labeled": "raw_deployment_packaging_ablation_only",
        },
    }


def _prospective_plan() -> dict[str, Any]:
    return {
        "plan_version": "mbpp_validation_2x2_prospective_plan_draft_v1",
        "status": PLAN_STATUS,
        "activation_gate": {
            "final_p1_exact_text_and_sha256_frozen": False,
            "final_healer_source_rule_order_guards_and_sha256_frozen": False,
            "pipeline_source_and_sha256_refrozen": False,
            "validation_identity_manifest_frozen_without_content_review": False,
            "sampling_and_model_protocol_frozen": False,
            "analysis_code_and_claim_rules_frozen": False,
            "formal_execution_allowed_now": False,
        },
        "validation_task_ids": [],
        "validation_task_content_read": False,
        "planned_identity_count": None,
        "generation_design": {
            "per_task_seed_identity": ["one P0 generation", "one P1 generation"],
            "generation_count_per_identity": 2,
            "evaluation_accounts_per_identity": 4,
            "healer_causes_additional_generation": False,
            "same_seeds_and_task_ids_across_p0_p1": True,
        },
        "evaluation_sequence": [
            "persist P0 and P1 raw generations",
            "apply identical frozen Pipeline normalization independently to each generation",
            "fork each normalized output into H0 unchanged and H1 frozen-Healer accounts",
            "persist rule triggers, guards, transformations or abstentions before evaluation",
            "evaluate all four ITT accounts without retry or selective exclusion",
        ],
        "rule_level_reporting": [
            "P0 trigger cells and unique tasks",
            "P1 trigger cells and unique tasks",
            "signature and rule-order position",
            "transformation, guard outcome, semantic-risk and abstention reason",
        ],
        "primary_factorial_reporting": {
            "healer_effect_within_p0": "paired P0_H1 versus P0_H0",
            "healer_effect_within_p1": "paired P1_H1 versus P1_H0",
            "scaffold_effect_with_h0": "P1_H0 versus P0_H0 by task_id+seed",
            "scaffold_effect_with_h1": "P1_H1 versus P0_H1 by task_id+seed",
            "interaction": "difference between the two within-prompt Healer effects; exact method and claim threshold must be frozen before activation",
            "all_regressions_disclosed": True,
        },
        "development_evidence_policy": {
            "offline_build_and_tests_allowed": True,
            "all_current_trigger_counts_labeled_development_only": True,
            "development_results_cannot_set_validation_acceptance_post_hoc": True,
        },
    }


def _report(result: dict[str, Any]) -> bytes:
    rows = {row["rule_id"]: row for row in result["trigger_rows"]}
    entry = rows["entrypoint_alias_unique_arity_compatible_v0"]
    lines = [
        "# MBPP+ 2×2 factorial evaluation readiness v1",
        "",
        "本資產把正式研究目標轉成可機器驗證的帳務與前瞻計畫草案；目前仍是development-only，因final P1與final Healer尚未凍結，所以不得啟用validation。",
        "",
        "## 正式四帳",
        "",
        "- P0+H0：P0 generation經共同frozen Pipeline後直接評估。",
        "- P0+H1：同一份P0 normalized output套用共同Healer後評估。",
        "- P1+H0：P1 generation經同一Pipeline後直接評估。",
        "- P1+H1：同一份P1 normalized output套用同版本Healer後評估。",
        "",
        "H0/H1共享generation ID、raw SHA與Pipeline normalized input；Healer不得重新生成。Pipeline extraction、fence stripping與plain-text normalization不是Healer。",
        "",
        "## Development-only觸發稽核",
        "",
        f"目前唯一eligible窄候選`entrypoint_alias_unique_arity_compatible_v0`在P0輸出觸發{entry['p0_trigger_cells']}格／{entry['p0_trigger_unique_tasks']}題，在既有Scaffold-like輸出觸發{entry['scaffold_trigger_cells']}格／{entry['scaffold_trigger_unique_tasks']}題。低觸發率不允許改變規則：P0與P1必須使用相同版本、順序、guards與abstention。",
        "",
        "其他syntax、truncation與generic unknown仍分別為insufficient evidence或nonrepairable；format/packaging只屬Scaffold或Pipeline。逐規則完整分層統計在CSV。",
        "",
        "## Validation啟用條件",
        "",
        "必須先凍結final P1 exact text/hash、final Healer source/hash/rule order/guards、Pipeline source/hash、validation identities、模型與sampling、分析程式與claim rules。此前validation task清單保持空白，且不得執行正式generation或evaluation。",
        "",
        "## Raw deployment packaging ablation",
        "",
        "可另設raw deployment packaging ablation，但它不是正式2×2 factorial的一部分，不得取代Pipeline或Healer帳，結果必須獨立標示。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_outputs(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    result = build_analysis(repo_root)
    outputs = {
        "healer_factorial_trigger_ledger.csv": _csv_bytes(result["trigger_rows"], TRIGGER_FIELDS),
        "factorial_accounting_spec.json": _json_bytes(_accounting_spec()),
        "prospective_2x2_validation_plan.json": _json_bytes(_prospective_plan()),
        "factorial_readiness_analysis_zh.md": _report(result),
    }
    manifest = {
        "manifest_version": "mbpp_factorial_evaluation_readiness_v1",
        "status": PLAN_STATUS,
        "development_only": True,
        "formal_factorial_arms": ["P0_H0", "P0_H1", "P1_H0", "P1_H1"],
        "development_counts": {"tasks": 60, "task_seed_identities": 300, "programs": 600},
        "model_calls": 0,
        "evalplus_executions": 0,
        "validation_tasks_read_or_selected": 0,
        "candidate_b_development_candidate_frozen": True,
        "final_p1_frozen": False,
        "healer_development_candidate_implemented": True,
        "healer_frozen": False,
        "source_sha256": result["source_hashes"],
        "output_sha256_excluding_manifest": {
            name: _sha256(content) for name, content in sorted(outputs.items())
        },
    }
    outputs["factorial_readiness_manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo_root: Path = REPO_ROOT, check: bool = False) -> None:
    output_dir = repo_root.resolve() / OUTPUT_RELATIVE
    outputs = build_outputs(repo_root)
    if check:
        _require(output_dir.is_dir(), "factorial readiness output directory missing")
        _require({path.name for path in output_dir.iterdir() if path.is_file()} == set(outputs), "output file set drift")
        for name, content in outputs.items():
            _require((output_dir / name).read_bytes() == content, f"deterministic bytes drift: {name}")
        return
    _require(not output_dir.exists(), "factorial readiness output directory exists; overwrite forbidden")
    output_dir.mkdir(parents=True)
    for name, content in outputs.items():
        (output_dir / name).write_bytes(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        write_outputs(check=args.check)
    except FactorialReadinessError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
