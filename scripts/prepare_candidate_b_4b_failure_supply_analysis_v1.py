#!/usr/bin/env python3
"""Freeze and extract the Stage2 MBPP+ qwen3.5:4b failure-supply pilot.

This is a zero-model, zero-evaluation preparation step.  It reads the frozen
200-cell plan and completed journals, verifies all identities and hashes, then
replays the repository's canonical extraction rule.  Ambiguous or missing
extractions remain in the ITT ledger but are never sent to EvalPlus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as frozen  # noqa: E402
from scripts import run_candidate_b_4b_development_failure_supply_pilot_v1 as generation_runner  # noqa: E402

OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_failure_supply_pilot_analysis_v1"
)
RUN_RELATIVE = frozen.RUN_OUTPUT_RELATIVE
EXPECTED_MANIFEST_SHA256 = (
    "955a0b463e2ca6a71b76ed745a266977c5cd7005562e621a1b8091a28fd3eccb"
)
EXPECTED_PIPELINE_SHA256 = (
    "a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf"
)
START_HEAD = "6e759a6cb36b3588f5e59e45fc5ea8cc8bb6721f"
EXPECTED_CELL_COUNT = 200
EXPECTED_EVAL_COUNT = 186
CELL5 = {
    "cell_index": 5,
    "task_id": "Mbpp/633",
    "condition_id": "Ab1_H0",
    "seed": 33,
    "generation_id": "ddf887bc974d8f55f970ad35dfb5a9649507a1a875ceb989e45e088c47be68f5",
    "raw_response_sha256": "2904c66bb5c55dffc616ffee5e12f64ce56f779dd14783cbec68f9e7bb098c23",
}

INVENTORY_FIELDS = (
    "cell_index", "program_id", "cell_identity", "task_id", "seed",
    "condition_id", "generation_id", "journal_path", "journal_sha256",
    "journal_bytes", "raw_response_sha256", "raw_response_utf8_bytes",
    "generation_completed", "raw_response_persisted", "model_tag",
    "model_digest", "manifest_sha256",
)
EXTRACTION_FIELDS = (
    "cell_index", "program_id", "cell_identity", "task_id", "seed",
    "condition_id", "generation_id", "itt_included", "extraction_status",
    "extraction_method", "extracted_code_sha256", "candidate_count",
    "evaluation_disposition", "failure_closed_reason",
)


class PreparationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreparationError(message)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _read_cells() -> list[dict[str, str]]:
    path = REPO_ROOT / frozen.OUTPUT_RELATIVE / "generation_cells.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == EXPECTED_CELL_COUNT, "frozen generation plan is not 200 cells")
    _require([int(row["cell_index"]) for row in rows] == list(range(1, 201)), "cell indexes are not exactly 1..200")
    _require(len({row["generation_id"] for row in rows}) == 200, "duplicate generation_id in frozen plan")
    _require(len({row["cell_identity"] for row in rows}) == 200, "duplicate cell_identity in frozen plan")
    _require(Counter(row["condition_id"] for row in rows) == Counter({"Ab1_H0": 100, "Ab2g_H1": 100}), "condition distribution drift")
    return rows


def _verify_source_gates() -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest_path = REPO_ROOT / frozen.OUTPUT_RELATIVE / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    _require(_sha(manifest_bytes) == EXPECTED_MANIFEST_SHA256, "frozen manifest SHA-256 mismatch")
    manifest = json.loads(manifest_bytes)
    _require(manifest["run_id"] == frozen.RUN_ID, "run_id drift")
    _require(manifest["dataset"] == "MBPP+", "dataset is not MBPP+")
    _require(manifest["model"]["tag"] == "qwen3.5:4b", "model tag drift")
    _require(manifest["model"]["digest"] == frozen.MODEL_DIGEST, "model digest drift")
    _require(manifest["parity_with_9b"]["pipeline_sha256"] == EXPECTED_PIPELINE_SHA256, "canonical extraction hash drift")
    _require(_sha((REPO_ROOT / "agent_tools/finals_rebuild/extraction.py").read_bytes()) == EXPECTED_PIPELINE_SHA256, "extraction.py bytes drift")
    return manifest, _read_cells()


def build_outputs() -> dict[str, bytes]:
    manifest, cells = _verify_source_gates()
    run_dir = REPO_ROOT / RUN_RELATIVE
    journals = sorted((run_dir / "j").glob("*.json"))
    _require(len(journals) == 200, "journal file count is not 200")
    _require({path.stem for path in journals} == {row["generation_id"] for row in cells}, "journal roster differs from frozen plan")

    inventory: list[dict[str, Any]] = []
    extraction_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    extraction_counts: Counter[str] = Counter()

    for cell in cells:
        generation_id = cell["generation_id"]
        journal_path = run_dir / "j" / f"{generation_id}.json"
        journal_bytes = journal_path.read_bytes()
        journal = json.loads(journal_bytes)
        ok, reason = generation_runner.resume_identity_matches(
            cell,
            journal,
            manifest_sha256=EXPECTED_MANIFEST_SHA256,
            protocol_sha256=frozen.EXPECTED_PROTOCOL_SHA256,
        )
        _require(ok, f"journal identity mismatch for cell {cell['cell_index']}: {reason}")
        raw = journal.get("raw_response")
        _require(isinstance(raw, str) and bool(raw), f"raw response missing for cell {cell['cell_index']}")
        raw_sha = _sha(raw.encode("utf-8"))
        if "raw_response_sha256" in journal:
            _require(raw_sha == journal["raw_response_sha256"], f"raw response SHA mismatch for cell {cell['cell_index']}")
        generation_completed = journal.get("generation_completed", journal.get("completion_flag") == "success")
        raw_response_persisted = journal.get("raw_response_persisted", isinstance(raw, str) and bool(raw))
        _require(generation_completed is True, f"generation incomplete for cell {cell['cell_index']}")
        _require(raw_response_persisted is True, f"raw response not persisted for cell {cell['cell_index']}")
        _require(journal["healer_applied"] is False, f"Healer contamination in cell {cell['cell_index']}")
        _require(journal["evaluation_executed"] is False, f"pre-existing evaluation contamination in cell {cell['cell_index']}")

        extracted = extract_code(raw)
        extraction_counts[extracted.extraction_status] += 1
        candidate_count = (
            extracted.diagnostics.get("python_fenced_blocks")
            if extracted.extraction_method == "fenced_python"
            else extracted.diagnostics.get("other_fenced_blocks")
            if extracted.extraction_method == "fenced_other"
            else 1 if extracted.extraction_status == "extracted" else 0
        )

        if int(cell["cell_index"]) == 5:
            for key in ("task_id", "condition_id", "generation_id"):
                _require(cell[key] == CELL5[key], f"Cell 5 {key} drift")
            _require(int(cell["seed"]) == CELL5["seed"], "Cell 5 seed drift")
            _require(raw_sha == CELL5["raw_response_sha256"], "Cell 5 raw response SHA drift")
            _require(extracted.extraction_status == "ambiguous", "Cell 5 must remain extraction ambiguous")
            _require(extracted.extracted_code is None, "Cell 5 candidate selection is forbidden")

        if extracted.extraction_status == "extracted":
            _require(extracted.extracted_code is not None, "extracted status without code")
            if "extraction_succeeded" in journal:
                _require(journal["extraction_succeeded"] is True, f"journal/replay extraction disagreement for cell {cell['cell_index']}")
                _require(journal["extracted_code"] == extracted.extracted_code, f"journal/replay code bytes differ for cell {cell['cell_index']}")
            disposition = "requires_h0_evalplus"
            fail_reason = ""
            eval_rows.append({
                "cell_index": int(cell["cell_index"]),
                "program_id": cell["program_id"],
                "cell_identity": cell["cell_identity"],
                "run_id": frozen.RUN_ID,
                "task_id": cell["task_id"],
                "seed": int(cell["seed"]),
                "condition_id": cell["condition_id"],
                "generation_id": generation_id,
                "sample_index": int(cell["sample_index"]),
                "completion": extracted.extracted_code,
                "evaluation_source_sha256": extracted.extracted_code_hash,
                "evaluation_disposition": disposition,
            })
        else:
            if "extraction_succeeded" in journal:
                _require(journal["extraction_succeeded"] is False, f"journal/replay extraction disagreement for cell {cell['cell_index']}")
                _require(journal["extracted_code"] is None, f"failed extraction carries code for cell {cell['cell_index']}")
            disposition = f"not_evaluated_extraction_{extracted.extraction_status}"
            fail_reason = "fail_closed_no_candidate_selected"

        inventory.append({
            "cell_index": cell["cell_index"],
            "program_id": cell["program_id"],
            "cell_identity": cell["cell_identity"],
            "task_id": cell["task_id"],
            "seed": cell["seed"],
            "condition_id": cell["condition_id"],
            "generation_id": generation_id,
            "journal_path": journal_path.relative_to(REPO_ROOT).as_posix(),
            "journal_sha256": _sha(journal_bytes),
            "journal_bytes": len(journal_bytes),
            "raw_response_sha256": raw_sha,
            "raw_response_utf8_bytes": len(raw.encode("utf-8")),
            "generation_completed": "true",
            "raw_response_persisted": "true",
            "model_tag": journal["model_tag"],
            "model_digest": journal["model_digest"],
            "manifest_sha256": journal["manifest_sha256"],
        })
        extraction_rows.append({
            "cell_index": cell["cell_index"],
            "program_id": cell["program_id"],
            "cell_identity": cell["cell_identity"],
            "task_id": cell["task_id"],
            "seed": cell["seed"],
            "condition_id": cell["condition_id"],
            "generation_id": generation_id,
            "itt_included": "true",
            "extraction_status": extracted.extraction_status,
            "extraction_method": extracted.extraction_method,
            "extracted_code_sha256": extracted.extracted_code_hash or "",
            "candidate_count": candidate_count,
            "evaluation_disposition": disposition,
            "failure_closed_reason": fail_reason,
        })

    _require(extraction_counts == Counter({"extracted": 186, "ambiguous": 14}), f"unexpected extraction distribution: {extraction_counts}")
    _require(len(eval_rows) == EXPECTED_EVAL_COUNT, "EvalPlus input count is not 186")
    ambiguous_cells = [int(row["cell_index"]) for row in extraction_rows if row["extraction_status"] == "ambiguous"]
    _require(5 in ambiguous_cells and len(ambiguous_cells) == 14, "ambiguous extraction roster drift")

    outputs: dict[str, bytes] = {
        "generation_evidence_inventory.csv": _csv_bytes(INVENTORY_FIELDS, inventory),
        "extraction_itt_ledger.csv": _csv_bytes(EXTRACTION_FIELDS, extraction_rows),
        "h0_evalplus_input.jsonl": b"".join(
            (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
            for row in eval_rows
        ),
    }
    preflight = {
        "status": "zero_model_preflight_passed",
        "scope": "Stage2_MBPP+_only",
        "run_id": frozen.RUN_ID,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "cell_count": 200,
        "journal_count": 200,
        "raw_response_count": 200,
        "itt_denominator": 200,
        "extraction_distribution": dict(sorted(extraction_counts.items())),
        "h0_evalplus_cells": 186,
        "fail_closed_cells": ambiguous_cells,
        "model_calls": 0,
        "healer_applied": False,
        "h1_created": False,
        "parallel_required": 1,
    }
    outputs["zero_model_preflight.json"] = _json_bytes(preflight)
    source_hashes = {
        (frozen.OUTPUT_RELATIVE / "manifest.json").as_posix(): EXPECTED_MANIFEST_SHA256,
        (frozen.OUTPUT_RELATIVE / "generation_cells.csv").as_posix(): _sha(
            (REPO_ROOT / frozen.OUTPUT_RELATIVE / "generation_cells.csv").read_bytes()
        ),
        "agent_tools/finals_rebuild/extraction.py": EXPECTED_PIPELINE_SHA256,
        (RUN_RELATIVE / "execution_manifest.json").as_posix(): _sha((run_dir / "execution_manifest.json").read_bytes()),
        (RUN_RELATIVE / "live_model_provenance.json").as_posix(): _sha((run_dir / "live_model_provenance.json").read_bytes()),
    }
    frozen_manifest = {
        "manifest_version": "candidate_b_4b_failure_supply_pilot_analysis_v1",
        "status": "frozen_inputs_ready_for_h0_evalplus",
        "scope": "Stage2_MBPP+_only",
        "start_head": START_HEAD,
        "run_id": frozen.RUN_ID,
        "generation_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "pipeline_sha256": EXPECTED_PIPELINE_SHA256,
        "dataset_version": "v0.2.0",
        "dataset_hash": "ee43ecabebf20deef4bb776a405ac5b1",
        "evalplus_version": "0.3.1",
        "counts": {
            "cells": 200, "journals": 200, "raw_responses": 200,
            "extracted": 186, "ambiguous": 14, "h0_evalplus": 186,
        },
        "cell5_policy": "extraction_ambiguous_no_candidate_selected_itt_retained",
        "fail_closed_ambiguous_cells": ambiguous_cells,
        "model_calls": 0,
        "healer_modifications": 0,
        "h1_results_created": 0,
        "source_sha256": source_hashes,
        "prepared_output_sha256": {name: _sha(data) for name, data in sorted(outputs.items())},
    }
    outputs["frozen_input_manifest.json"] = _json_bytes(frozen_manifest)
    return outputs


def write_outputs(outputs: dict[str, bytes]) -> None:
    output_dir = REPO_ROOT / OUTPUT_RELATIVE
    _require(not output_dir.exists(), f"output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    for name, data in outputs.items():
        (output_dir / name).write_bytes(data)


def check_outputs(outputs: dict[str, bytes]) -> None:
    output_dir = REPO_ROOT / OUTPUT_RELATIVE
    for name, data in outputs.items():
        path = output_dir / name
        _require(path.is_file(), f"prepared output missing: {name}")
        _require(path.read_bytes() == data, f"deterministic rebuild drift: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        check_outputs(outputs)
        print(json.dumps({"status": "deterministic_preparation_rebuild_passed", "file_count": len(outputs)}, sort_keys=True))
    else:
        write_outputs(outputs)
        print(json.dumps({"status": "frozen_inputs_ready_for_h0_evalplus", "cell_count": 200, "evalplus_count": 186}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
