"""Replay stored Ab2d failures through the existing deterministic Ab3 healer."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from agent_tools.finals_rebuild.math_boundary_pilot import classify_response
from agent_tools.finals_rebuild.math_healer_runner import derive_ab3

INPUTS = (
    ROOT / "docs/experiments/results/ab2d_qwen3_4b_l1_seed_20260714_smoke.jsonl",
    ROOT / "docs/experiments/results/ab2d_qwen3_8b_l1_seed_20260714_smoke.jsonl",
)
RESULT = ROOT / "docs/experiments/results/deterministic_ab3_replay_ab2d_failures_seed_20260714.jsonl"
SUMMARY = ROOT / "docs/experiments/deterministic_ab3_replay_ab2d_failures_seed_20260714_summary.md"
RUN_STATUS = "engineering_diagnostic_replay"
ORACLE_TYPES = {
    "polynomial_division_quotient_remainder": "polynomial_division_exact",
    "largest_proper_divisor_reasoning": "largest_proper_divisor_logic",
    "rpm_circumference_to_kph": "rpm_circumference_kph",
    "alternating_training_progression_threshold": "alternating_sequence_threshold",
}
PRE_FAILURE_TYPES = {
    ("qwen3:4b-instruct-2507-q4_K_M", "polynomial_division_quotient_remainder"): "prompt_contract_misunderstanding",
    ("qwen3:4b-instruct-2507-q4_K_M", "largest_proper_divisor_reasoning"): "model_logic_error",
    ("qwen3:4b-instruct-2507-q4_K_M", "rpm_circumference_to_kph"): "runtime_or_api_misuse",
    ("qwen3:4b-instruct-2507-q4_K_M", "alternating_training_progression_threshold"): "model_logic_error",
    ("qwen3:8b", "polynomial_division_quotient_remainder"): "extraction_and_schema_failure",
    ("qwen3:8b", "largest_proper_divisor_reasoning"): "extraction_and_schema_failure",
    ("qwen3:8b", "alternating_training_progression_threshold"): "model_logic_error",
}


def _append(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_failures() -> list[dict[str, Any]]:
    rows = []
    for path in INPUTS:
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if not row["oracle_pass"]:
                rows.append(row)
    expected = [
        ("qwen3:4b-instruct-2507-q4_K_M", family)
        for family in ORACLE_TYPES
    ] + [
        ("qwen3:8b", family)
        for family in (
            "polynomial_division_quotient_remainder",
            "largest_proper_divisor_reasoning",
            "alternating_training_progression_threshold",
        )
    ]
    actual = [(row["model_tag"], row["task_family"]) for row in rows]
    if actual != expected:
        raise ValueError(f"unexpected replay set: {actual!r}")
    return rows


def _base(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_model_tag": source["model_tag"],
        "source_task_family": source["task_family"],
        "source_seed": source["seed"],
        "source_difficulty": source["difficulty"],
        "source_candidate_extracted": source["candidate_extracted"],
        "pre_ab3_evaluable": source["evaluable"],
        "pre_ab3_oracle_pass": source["oracle_pass"],
        "pre_ab3_failure_category": source["failure_category"],
        "pre_ab3_failure_detail": source.get("failure_detail"),
        "pre_failure_type": PRE_FAILURE_TYPES[(source["model_tag"], source["task_family"])],
        "healer_name": "UnifiedCleanupHealer",
        "retry_count": 0,
        "run_status": RUN_STATUS,
    }


def _not_applicable(source: dict[str, Any]) -> dict[str, Any]:
    row = _base(source)
    row.update({
        "applicability": "not_applicable_pre_extraction", "repair_attempted": False,
        "healer_input_source": None, "healer_output_source": None,
        "healer_changed_source": None, "healer_exception": None,
        "post_ab3_evaluable": None, "post_ab3_oracle_pass": None,
        "post_ab3_failure_category": None, "post_ab3_failure_detail": None,
        "repair_success": False, "execution_timeout": None, "repair_call_count": 0,
    })
    return row


def _replay(source: dict[str, Any]) -> dict[str, Any]:
    candidate = source["candidate_extracted"]
    if candidate is None:
        return _not_applicable(source)
    row = _base(source)
    row.update({
        "applicability": "applicable", "repair_attempted": True,
        "healer_input_source": candidate, "healer_output_source": None,
        "healer_changed_source": None, "healer_exception": None,
        "post_ab3_evaluable": False, "post_ab3_oracle_pass": False,
        "post_ab3_failure_category": None, "post_ab3_failure_detail": None,
        "repair_success": False, "execution_timeout": False, "repair_call_count": 1,
    })
    with tempfile.TemporaryDirectory(prefix="deterministic_ab3_replay_") as root:
        temp_root = Path(root)
        input_path = temp_root / "candidate.py"
        output_dir = temp_root / "derived"
        input_path.write_text(candidate, encoding="utf-8")
        derivation = derive_ab3(
            source=input_path, output_dir=output_dir, run_id="deterministic-ab3-20260714",
            paired_run_id="ab2d-l1-seed-20260714", task_id=source["task_id"],
            model=source["model_tag"], condition="Ab3",
        )
        row["healer_exception"] = derivation["healer_error"]
        output_path = output_dir / "ab3_source.py"
        if not output_path.is_file():
            row["post_ab3_failure_category"] = "healer_failure"
            row["post_ab3_failure_detail"] = "deterministic derivation produced no output source"
            return row
        healed = output_path.read_text(encoding="utf-8")
        row["healer_output_source"] = healed
        row["healer_changed_source"] = derivation["source_changed"]
        task = {"skill_id": source["task_family"], "oracle_type": ORACLE_TYPES[source["task_family"]]}
        frozen = {"oracle_payload": source["task_parameters"]}
        outcome, _extracted, detail = classify_response(healed, frozen, task)
        row["post_ab3_evaluable"] = outcome not in {
            "empty_response", "catastrophic_truncation", "extraction_failure", "parse_minor",
            "missing_entry_point", "infrastructure_failure",
        }
        row["post_ab3_oracle_pass"] = outcome == "passed"
        row["post_ab3_failure_category"] = None if outcome == "passed" else outcome
        row["post_ab3_failure_detail"] = (
            detail.get("runtime_error") or detail.get("parse_error") or detail.get("oracle_error")
        )
        row["execution_timeout"] = bool(
            row["post_ab3_failure_detail"] and "execution_timeout" in row["post_ab3_failure_detail"]
        )
        row["repair_success"] = row["post_ab3_evaluable"] and row["post_ab3_oracle_pass"]
    return row


def _summary(rows: list[dict[str, Any]]) -> str:
    applicable = [row for row in rows if row["applicability"] == "applicable"]
    repaired = [row for row in applicable if row["repair_success"]]
    lines = [
        "# Deterministic Ab3 replay of Ab2d failures — 2026-07-14", "",
        "This engineering diagnostic calls the existing `derive_ab3()` once for each pre-extracted candidate. No model or Ollama request was made.", "",
        "| source_model | task_family | pre_failure_type | applicability | healer_changed_source | post_evaluable | post_oracle_pass | repair_success | post_failure |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| {source_model_tag} | {source_task_family} | {pre_failure_type} | {applicability} | {healer_changed_source} | {post_ab3_evaluable} | {post_ab3_oracle_pass} | {repair_success} | {post_ab3_failure_category} |".format(**row))
    by_type = lambda kind: [row for row in applicable if row["pre_failure_type"] == kind]
    lines += [
        "", "## Counts", "",
        f"- Applicable cases: {len(applicable)}",
        f"- Not applicable pre-extraction: {sum(row['applicability'] == 'not_applicable_pre_extraction' for row in rows)}",
        f"- Successful repairs / applicable: {len(repaired)} / {len(applicable)}",
        f"- No-op cases: {sum(not row['healer_changed_source'] for row in applicable)}",
        f"- Changed-but-still-failed cases: {sum(row['healer_changed_source'] and not row['repair_success'] for row in applicable)}",
        f"- Contract/schema repairs: {sum(row['repair_success'] for row in by_type('prompt_contract_misunderstanding') + by_type('extraction_and_schema_failure'))} / {len(by_type('prompt_contract_misunderstanding') + by_type('extraction_and_schema_failure'))}",
        f"- Runtime/API repairs: {sum(row['repair_success'] for row in by_type('runtime_or_api_misuse'))} / {len(by_type('runtime_or_api_misuse'))}",
        f"- Model-logic repairs: {sum(row['repair_success'] for row in by_type('model_logic_error'))} / {len(by_type('model_logic_error'))}",
        "", "## Intervention boundary", "",
        "`derive_ab3()` accepts a pre-existing source path and applies `UnifiedCleanupHealer` after extraction. It cannot intervene before extraction; the two 8B ambiguous-fence records therefore remain not applicable without selecting or rewriting a candidate.",
        "", "`UnifiedCleanupHealer` is a structural cleanup pass. This replay records whether it changed each source and evaluates the result through the unchanged production sandbox and independent oracle; it does not supply a capability claim beyond these seven records.", "",
    ]
    return "\n".join(lines)


def main() -> int:
    if RESULT.exists() or SUMMARY.exists():
        raise FileExistsError("replay outputs already exist; refusing to overwrite")
    rows = []
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text("", encoding="utf-8")
    for source in _load_failures():
        row = _replay(source)
        _append(RESULT, row)
        rows.append(row)
    if len(rows) != 7:
        raise AssertionError(f"expected 7 records, got {len(rows)}")
    SUMMARY.write_text(_summary(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
