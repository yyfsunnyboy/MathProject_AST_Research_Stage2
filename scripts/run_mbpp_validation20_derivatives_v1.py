#!/usr/bin/env python3
"""Evaluator-blind Validation20 derivatives: Raw → Pipeline → Post-H1..H4.

Architecture only in this round: preflight and dry planning are allowed.
Formal derivative materialization requires completed raw journals and an
explicit acknowledgement. Never runs EvalPlus. Never calls a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline import (  # noqa: E402
    run_h1_then_h2_then_h3_then_h4,
)
from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze  # noqa: E402
from scripts import prepare_top_level_demo_print_quarantine_development_v1 as demo_fp  # noqa: E402
from scripts import preflight_mbpp_validation20_generation_v1 as gen_preflight  # noqa: E402

DERIVATIVE_ACK = "I_ACKNOWLEDGE_EVALUATOR_BLIND_DERIVATIVES_WITHOUT_EVALPLUS"
RUNNER_IDENTITY = "mbpp_validation20_derivatives_runner_v1"


class DerivativeError(RuntimeError):
    """Fail-closed derivative violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DerivativeError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def zero_execution_preflight(*, model: str, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    model_tag = gen_preflight.resolve_model_tag(model)
    gen_receipt = gen_preflight.zero_model_preflight(
        model=model_tag,
        repo_root=repo_root,
        require_verified_identity=False,
        require_output_absent=False,
    )
    eval_dir = repo_root / freeze.MODEL_SPECS[model_tag]["evalplus_output_relative"]
    _require(not eval_dir.exists(), "EvalPlus output must stay absent during derivatives")
    for banned in freeze.FORBIDDEN_OUTPUT_COLLISION_RELATIVES:
        _require(
            eval_dir.resolve() != (repo_root / banned).resolve(),
            f"EvalPlus path collides with existing formal run: {banned}",
        )
    return {
        "status": "zero_candidate_execution_derivatives_preflight_passed",
        "model_tag": model_tag,
        "generation_preflight": gen_receipt,
        "model_calls": 0,
        "candidate_program_executed": False,
        "candidate_program_imported": False,
        "candidate_program_compiled": False,
        "evalplus_executed": False,
        "healer_uses_pass_fail": False,
    }


def derive_one_cell(
    *,
    cell: Mapping[str, str],
    raw_response: str,
    official_prompt: str,
) -> dict[str, Any]:
    raw_sha = _sha256_text(raw_response)
    extraction = extract_code(raw_response)
    pipeline_source = (
        extraction.extracted_code if extraction.extraction_status == "extracted" else None
    )
    pipeline_sha = _sha256_text(pipeline_source) if isinstance(pipeline_source, str) else None
    extraction_unambiguous = extraction.extraction_status == "extracted"
    source_complete = extraction.extraction_status == "extracted"
    generation_truncated = False
    arities = tuple(int(part) for part in cell["expected_positional_arities"].split("|") if part)
    fingerprints = demo_fp.public_assert_fingerprints(official_prompt)
    cumulative = run_h1_then_h2_then_h3_then_h4(
        normalized_source=pipeline_source,
        entry_point=cell["expected_entry_point"],
        expected_positional_arities=arities,
        generation_truncated=generation_truncated,
        extraction_unambiguous=extraction_unambiguous,
        source_complete=source_complete,
        task_id=cell["task_id"],
        execute_evalplus=False,
        public_assert_fingerprints=fingerprints,
    )
    final_source = cumulative.final_source
    stages = {
        "raw": {
            "stage": "raw",
            "source": raw_response,
            "source_sha256": raw_sha,
        },
        "pipeline_corrected": {
            "stage": "pipeline_corrected",
            "source": pipeline_source,
            "source_sha256": pipeline_sha,
            "extraction_status": extraction.extraction_status,
            "extraction_method": extraction.extraction_method,
            "bytes_identical_to_raw": (
                isinstance(pipeline_source, str) and pipeline_source == raw_response
            ),
        },
        "post_h1_h2_h3_h4": {
            "stage": "post_h1_h2_h3_h4",
            "source": final_source,
            "source_sha256": cumulative.final_sha256,
            "transform_class": cumulative.transform_class,
            "h1": cumulative.h1.to_dict(),
            "h2": cumulative.h2.to_dict(),
            "h3": cumulative.h3.to_dict(),
            "h4": cumulative.h4.to_dict(),
            "first_effective_rule": _first_effective_rule(cumulative),
            "rules_applied": _rules_applied(cumulative),
            "decision": (
                "transformed"
                if any(
                    stage.changed
                    for stage in (cumulative.h1, cumulative.h2, cumulative.h3, cumulative.h4)
                )
                else "abstained"
            ),
        },
    }
    # Strip bulky nested sources from stage traces for ledger size control.
    for key in ("h1", "h2", "h3", "h4"):
        stages["post_h1_h2_h3_h4"][key].pop("input_source", None)
        stages["post_h1_h2_h3_h4"][key].pop("output_source", None)
        stages["post_h1_h2_h3_h4"][key].pop("diff", None)
    return {
        "generation_id": cell["generation_id"],
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "prompt_condition": cell["prompt_condition"],
        "model_tag": cell["model_tag"],
        "stages": stages,
        "runner_identity": RUNNER_IDENTITY,
        "evalplus_executed": False,
        "candidate_program_executed": False,
    }


def _first_effective_rule(cumulative: Any) -> str | None:
    for stage in (cumulative.h1, cumulative.h2, cumulative.h3, cumulative.h4):
        if stage.changed:
            return stage.rule_id
    return None


def _rules_applied(cumulative: Any) -> list[str]:
    return [
        stage.rule_id
        for stage in (cumulative.h1, cumulative.h2, cumulative.h3, cumulative.h4)
        if stage.changed and stage.rule_id
    ]


def materialize(
    *,
    model: str,
    acknowledgement: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    _require(acknowledgement == DERIVATIVE_ACK, "derivatives acknowledgement mismatch")
    model_tag = gen_preflight.resolve_model_tag(model)
    zero_execution_preflight(model=model_tag, repo_root=repo_root)
    run_dir = repo_root / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    cells = _read_csv(repo_root / freeze.model_dir(model_tag) / "generation_cells.csv")
    tasks = {row["task_id"]: row for row in freeze.load_validation_tasks(repo_root)}
    out_dir = run_dir / "derivatives"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    abstained = 0
    for cell in cells:
        journal_path = run_dir / "j" / f"{cell['generation_id']}.json"
        _require(journal_path.is_file(), f"missing raw journal: {journal_path}")
        journal = _read_json(journal_path)
        _require(journal.get("persisted_complete") is True, f"raw journal not persisted_complete: {cell['generation_id']}")
        raw_response = journal["raw_response"]
        _require(
            _sha256_text(raw_response) == journal["raw_response_sha256"],
            f"raw SHA drift: {cell['generation_id']}",
        )
        derived = derive_one_cell(
            cell=cell,
            raw_response=raw_response,
            official_prompt=tasks[cell["task_id"]]["prompt"],
        )
        if derived["stages"]["pipeline_corrected"]["source"] is None:
            abstained += 1
        target = out_dir / f"{cell['generation_id']}.json"
        if target.exists():
            existing = target.read_bytes()
            payload = (json.dumps(derived, indent=2, sort_keys=True) + "\n").encode("utf-8")
            _require(existing == payload, f"derivative drift/overwrite refused: {target}")
        else:
            durable_write_json_new(target, derived)
            written += 1
    receipt = {
        "status": "derivatives_materialized_pending_evalplus",
        "model_tag": model_tag,
        "candidates": len(cells),
        "derivatives_written": written,
        "abstained_candidates": abstained,
        "executable_candidates": len(cells) - abstained,
        "stages": list(freeze.STAGES),
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }
    durable_write_json_new(out_dir / "derivatives_manifest.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=freeze.ALLOWED_MODEL_TAGS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--materialize", action="store_true")
    parser.add_argument("--acknowledgement", default="")
    args = parser.parse_args(argv)
    if args.preflight:
        print(json.dumps(zero_execution_preflight(model=args.model), indent=2, sort_keys=True))
        return 0
    print(
        json.dumps(
            materialize(model=args.model, acknowledgement=args.acknowledgement),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
