#!/usr/bin/env python3
"""Public benchmark cumulative H1->H2->H3->H4 replay runner (development-candidate evidence).

Experiment name for this artifact family: "cumulative H1-H4 candidate replay"
(development-candidate cumulative evaluation). None of H1, H2, H3, or H4 is
frozen or production -- each rule module self-declares
RULE_STATUS/CANDIDATE_STATUS == "development_candidate_not_frozen". This
runner does not change that status; it only offline-replays the existing
frozen *candidate* rule functions, unmodified, against the already-complete
qwen3.5:4b / qwen3.5:9b full public-benchmark Raw generation artifacts.

Supports:
- Models: qwen3.5:4b, qwen3.5:9b (same MODEL_SPECS digest contract as the
  H2-only public benchmark replay runner)
- Datasets: humaneval (328 raw generations), mbpp (756), all (1084)
- Fixed, non-configurable order: Raw -> H1 -> H2 -> H3 -> H4
  (calls agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline.
   run_h1_then_h2_then_h3_then_h4 -- the repository's one cumulative entry
   point -- directly; no rule logic is reimplemented here)
- Zero model calls, zero EvalPlus execution (evalplus stage is the wired,
  non-executing hook already built into the cumulative pipeline module)
- Every layer is evaluator-blind: none of apply_h1_stage/h2/h3/h4 accept a
  task_id-keyed oracle, EvalPlus outcome, hidden test, or canonical solution.
  Arity contract evidence for H1 and assert-fingerprint evidence for H4 are
  derived only from the prompt text already shown to the model.
- Ineligible/ambiguous cells abstain per each rule's own frozen guard; this
  runner never overrides an abstention.
- Writes to a NEW artifact directory, isolated from the existing H2-only
  ablation (qwen35_<tag>_h2_full_replay_v1) and from Raw generation
  artifacts (runs/<ds>_qwen35_<tag>/) -- neither is read-write here, both
  are read-only inputs (Raw) or untouched siblings (H2-only).
- CLI flags: --model, --dataset, --dry-run, --resume, --parallel 1,
  --output-dir
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.extraction import extract_code  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from agent_tools.finals_rebuild.mbpp_evaluator_blind_healer import (  # noqa: E402
    RULE_ID as H1_RULE_ID,
    CANDIDATE_STATUS as H1_RULE_STATUS,
)
from agent_tools.finals_rebuild.mbpp_h2_module_assert_quarantine import (  # noqa: E402
    RULE_ID as H2_RULE_ID,
    RULE_STATUS as H2_RULE_STATUS,
)
from agent_tools.finals_rebuild.mbpp_h3_empty_suite_pass_insertion import (  # noqa: E402
    RULE_ID as H3_RULE_ID,
    RULE_STATUS as H3_RULE_STATUS,
)
from agent_tools.finals_rebuild.mbpp_h4_top_level_demo_print_quarantine import (  # noqa: E402
    RULE_ID as H4_RULE_ID,
    RULE_STATUS as H4_RULE_STATUS,
)
from agent_tools.finals_rebuild.mbpp_h1_h2_cumulative_pipeline import (  # noqa: E402
    run_h1_then_h2_then_h3_then_h4,
)
from scripts import (  # noqa: E402
    run_public_benchmark_h2_replay_v1 as h2_replay,
)
from scripts.prepare_top_level_demo_print_quarantine_development_v1 import (  # noqa: E402
    public_assert_fingerprints,
)

CONDITIONS = ("Ab1", "Ab2g")
ALLOWED_MODELS = ("qwen3.5:4b", "qwen3.5:9b")
ALLOWED_DATASETS = ("humaneval", "mbpp", "all")

# Rule-file content hashes, recorded here purely as drift-detection anchors.
# Pinning a hash is NOT a frozen/production claim -- RULE_STATUS above remains
# "development_candidate_not_frozen" for every layer; this runner never
# changes that string.
EXPECTED_RULE_SHA256 = {
    "H1": (
        pathlib.Path("agent_tools/finals_rebuild/mbpp_evaluator_blind_healer.py"),
        "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44",
    ),
    "H2": (
        pathlib.Path("agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py"),
        "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18",
    ),
    "H3": (
        pathlib.Path("agent_tools/finals_rebuild/mbpp_h3_empty_suite_pass_insertion.py"),
        "8e7f7f36bd390b054b0e7ba5f57c4c0f98d7bce2d397bc53e9f15979be167c6e",
    ),
    "H4": (
        pathlib.Path("agent_tools/finals_rebuild/mbpp_h4_top_level_demo_print_quarantine.py"),
        "1aabe131b7312c9bc1e0b34b20540bef6f7d3ec858c2c2994cf84bc84f85a513",
    ),
    "PIPELINE": (
        pathlib.Path("agent_tools/finals_rebuild/mbpp_h1_h2_cumulative_pipeline.py"),
        "fd8b614234bda70334ac08866983ebf66fc1332b296ea91b59f403d3a79233ef",
    ),
}

RULE_IDS = {"H1": H1_RULE_ID, "H2": H2_RULE_ID, "H3": H3_RULE_ID, "H4": H4_RULE_ID}
RULE_STATUSES = {
    "H1": H1_RULE_STATUS,
    "H2": H2_RULE_STATUS,
    "H3": H3_RULE_STATUS,
    "H4": H4_RULE_STATUS,
}

MODEL_SPECS = {
    "qwen3.5:4b": {
        "model_key": "qwen35_4b",
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_4b_h1_h2_h3_h4_full_replay_v1"
        ),
    },
    "qwen3.5:9b": {
        "model_key": "qwen35_9b",
        "default_output": pathlib.Path(
            "artifacts/public_benchmark_governance/qwen35_9b_h1_h2_h3_h4_full_replay_v1"
        ),
    },
}

# Directories this runner must never write into (existing H2-only ablation +
# Raw generation artifacts). Enforced defensively in run_replay_execution.
FORBIDDEN_OUTPUT_DIRS = {
    "qwen35_4b_h2_full_replay_v1",
    "qwen35_9b_h2_full_replay_v1",
    "qwen35_4b_h2_full_evalplus_v1",
    "qwen35_9b_h2_full_evalplus_v1",
}


class CumulativeReplayError(RuntimeError):
    """Fail-closed error for cumulative replay runner violations."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CumulativeReplayError(message)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_cell_identity(model_tag: str, task_id: str, treatment: str) -> str:
    """Distinct namespace from the H2-only replay's cell_identity (different
    raw string prefix), so identities never collide across the two artifact
    families even though both may reference the same task/treatment."""
    raw = f"cumulative_h1_h2_h3_h4:{model_tag}:{task_id}:{treatment}"
    return _sha256_text(raw)


def verify_rule_files(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    """Zero-execution rule inventory + hash-drift + RULE_ID/STATUS check.

    Confirms current on-disk state without claiming frozen/production.
    """
    report: dict[str, Any] = {}
    for layer, (rel_path, expected_sha) in EXPECTED_RULE_SHA256.items():
        actual_sha = _sha256_file(repo_root / rel_path)
        _require(actual_sha == expected_sha, f"{layer} source SHA drift: {actual_sha}")
        report[layer] = {
            "source_path": rel_path.as_posix(),
            "sha256": actual_sha,
            "rule_id": RULE_IDS.get(layer),
            "rule_status": RULE_STATUSES.get(layer),
        }
    for layer in ("H1", "H2", "H3", "H4"):
        _require(
            report[layer]["rule_status"] == "development_candidate_not_frozen",
            f"{layer} RULE_STATUS is not the expected development-candidate value "
            f"(refusing to silently treat a status change as frozen/production)",
        )
    return report


def _derive_prompt_arity_contract(prompt: str, entry_point: str) -> tuple[int, ...]:
    """Evaluator-blind positional-arity evidence extracted only from
    prompt-visible example invocations of ``entry_point``.

    Two prompt-visible example styles are recognized:
      - MBPP+-style ``assert entry_point(...) == ...`` lines
      - HumanEval-style ``>>> entry_point(...)`` doctest lines

    Returns an empty tuple when no unambiguous evidence is found. An empty
    tuple causes H1's own frozen guard (``missing_or_invalid_arity_evidence``)
    to abstain -- this function never substitutes a guess for missing
    evidence, and never reads hidden tests or canonical solutions.
    """
    arities: set[int] = set()
    for line in prompt.splitlines():
        stripped = line.strip()
        candidate: str | None = None
        if stripped.startswith("assert "):
            candidate = stripped
        elif stripped.startswith(">>> "):
            candidate = stripped[4:]
        if candidate is None:
            continue
        try:
            tree = ast.parse(candidate)
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
    return tuple(sorted(arities))


def _generation_truncated(attempt: dict[str, Any]) -> bool:
    """Whether the Ollama response was cut off before natural completion.

    Derived only from the generation response's own ``done_reason`` (a
    generation-visible fact, not an oracle signal). Unknown/unparseable
    metadata is treated conservatively as truncated=True, which causes H1 to
    abstain rather than risk acting on an incomplete completion.
    """
    orm = attempt.get("ollama_response_metadata") or {}
    raw_body = orm.get("raw_body")
    if not raw_body:
        return True
    try:
        body = json.loads(raw_body)
    except (TypeError, ValueError):
        return True
    return body.get("done_reason") != "stop"


def zero_execution_preflight(
    *,
    model: str,
    dataset: str,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Zero-execution preflight: rule inventory, digest, inventory readiness,
    output-path isolation. No model call, no EvalPlus, no H2-only artifact
    access, no Raw artifact mutation.
    """
    _require(model in ALLOWED_MODELS, f"unsupported model: {model}")
    _require(dataset in ALLOWED_DATASETS, f"unsupported dataset: {dataset}")

    rule_report = verify_rule_files(repo_root=repo_root)

    # Reuse the H2-only replay runner's own frozen digest/inventory audit
    # rather than re-deriving raw-generation bookkeeping logic.
    preflight = h2_replay.zero_model_preflight(model=model, dataset=dataset, repo_root=repo_root)
    inventory = h2_replay.audit_inventory(model, dataset, repo_root=repo_root)
    inventory_summary = {k: v for k, v in inventory.items() if k != "present_raw_map"}

    spec = MODEL_SPECS[model]
    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    _require(
        out_dir.name not in FORBIDDEN_OUTPUT_DIRS,
        f"output directory collides with an existing H2-only ablation artifact: {out_dir.name}",
    )
    _require(
        "h2_full_replay" not in out_dir.as_posix() and "h2_full_evalplus" not in out_dir.as_posix(),
        f"output directory must not alias the H2-only ablation family: {out_dir.as_posix()}",
    )

    return {
        "status": "zero_execution_preflight_passed",
        "model_tag": model,
        "dataset": dataset,
        "rule_inventory": rule_report,
        "h2_only_rule_hash_cross_check": preflight["rule_hash"] == rule_report["H2"]["sha256"],
        "inventory": inventory_summary,
        "output_directory": out_dir.as_posix(),
        "output_directory_isolated": True,
        "fixed_order": ["H1", "H2", "H3", "H4"],
        "model_calls": 0,
        "evalplus_executed": False,
    }


def run_dry_run(
    *,
    model: str,
    dataset: str,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    preflight = zero_execution_preflight(
        model=model, dataset=dataset, output_dir_arg=output_dir_arg, repo_root=repo_root
    )

    spec = MODEL_SPECS[model]
    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    j_dir = out_dir / "j"

    existing_journals = 0
    if j_dir.is_dir():
        existing_journals = len(list(j_dir.glob("*.json")))

    inv = preflight["inventory"]
    planned_pairs = inv["total_tasks"] * 2  # Ab1 + Ab2g per task
    readiness = "READY" if inv["readiness_status"] == "READY" else "NOT_READY"

    return {
        "status": "dry_run_completed",
        "model_tag": model,
        "dataset": dataset,
        "readiness_status": readiness,
        "planned_replay_pairs": planned_pairs,
        "raw_generations_present": inv["present_raw_generations"],
        "raw_generations_missing": inv["missing_raw_generations"],
        "existing_cumulative_journals": existing_journals,
        "output_directory": out_dir.as_posix(),
        "fixed_order": ["H1", "H2", "H3", "H4"],
        "model_calls": 0,
        "evalplus_executed": False,
        "preflight": preflight,
    }


def run_replay_execution(
    *,
    model: str,
    dataset: str,
    resume: bool = True,
    output_dir_arg: str = "",
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict[str, Any]:
    """Executes the cumulative H1->H2->H3->H4 replay, one pass per
    (task_id, treatment) Raw pair. Writes to an isolated output directory;
    never touches Raw generation artifacts or the existing H2-only ablation.
    """
    preflight = zero_execution_preflight(
        model=model, dataset=dataset, output_dir_arg=output_dir_arg, repo_root=repo_root
    )
    inventory = h2_replay.audit_inventory(model, dataset, repo_root=repo_root)
    _require(
        inventory["readiness_status"] == "READY",
        f"raw generations incomplete for {model} on {dataset}: "
        f"missing {inventory['missing_raw_generations']}",
    )

    spec = MODEL_SPECS[model]
    out_dir = repo_root / output_dir_arg if output_dir_arg else repo_root / spec["default_output"]
    j_dir = out_dir / "j"
    j_dir.mkdir(parents=True, exist_ok=True)

    tasks = h2_replay.load_tasks(dataset, repo_root=repo_root)
    present_map = inventory["present_raw_map"]

    executed_cells = 0
    skipped_cells = 0
    seen_cell_ids: set[str] = set()
    duplicate_count = 0
    ledger_rows: list[dict[str, Any]] = []

    for task_rec in tasks:
        tid = task_rec["task_id"]
        ep = task_rec["entry_point"]
        prompt = task_rec.get("prompt", "")
        arities = _derive_prompt_arity_contract(prompt, ep)
        fingerprints = public_assert_fingerprints(prompt)

        for tr in ("ab1", "ab2g"):
            raw_rec = present_map.get((tid, tr))
            _require(raw_rec is not None, f"raw generation missing for task {tid} treatment {tr}")

            cell_id = generate_cell_identity(model, tid, tr)
            seen_before = cell_id in seen_cell_ids
            if seen_before:
                duplicate_count += 1
            seen_cell_ids.add(cell_id)

            j_file = j_dir / f"{cell_id}.json"
            if resume and j_file.is_file():
                try:
                    existing = json.loads(j_file.read_text(encoding="utf-8"))
                    if existing.get("persisted_complete") is True:
                        skipped_cells += 1
                        ledger_rows.append(
                            {
                                "cell_identity": cell_id,
                                "task_id": tid,
                                "treatment": tr,
                                "transform_class": existing.get("transform_class"),
                            }
                        )
                        continue
                except Exception:
                    pass

            raw_resp = raw_rec.get("raw_response") or ""
            ext_res = extract_code(raw_resp)
            is_extracted = ext_res.extraction_status == "extracted"
            ext_code = ext_res.extracted_code if is_extracted else ""
            truncated = _generation_truncated(raw_rec)
            sample_index = raw_rec.get("sample_index")
            generation_id = f"{model}:{tid}:{tr}:{sample_index}"

            result = run_h1_then_h2_then_h3_then_h4(
                normalized_source=ext_code,
                entry_point=ep,
                expected_positional_arities=arities,
                generation_truncated=truncated,
                extraction_unambiguous=is_extracted,
                source_complete=True,
                task_id=tid,
                execute_evalplus=False,
                public_assert_fingerprints=fingerprints,
            )

            stages = {"H1": result.h1, "H2": result.h2, "H3": result.h3, "H4": result.h4}
            layers_changed = [name for name, s in stages.items() if s.changed]
            rules_triggered = [
                RULE_IDS[name]
                for name, s in stages.items()
                if bool(s.extras.get("triggered")) or (name == "H1" and s.extras.get("triggered_rule_ids"))
            ]
            rules_applied = [RULE_IDS[name] for name in layers_changed]
            abstention_reason_by_layer = {name: s.reason for name, s in stages.items()}
            first_effective_rule = RULE_IDS[layers_changed[0]] if layers_changed else None

            try:
                ast.parse(ext_code)
                raw_parse_status = "parseable"
            except (SyntaxError, ValueError):
                raw_parse_status = "unparseable"
            except Exception:
                raw_parse_status = "unparseable"

            final_source = result.final_source or ""
            try:
                ast.parse(final_source)
                cumulative_parse_status = "parseable"
            except (SyntaxError, ValueError):
                cumulative_parse_status = "unparseable"
            except Exception:
                cumulative_parse_status = "unparseable"

            journal = {
                "cell_identity": cell_id,
                "model_tag": model,
                "dataset": "humaneval" if tid.startswith("HumanEval") else "mbpp",
                "task_id": tid,
                "treatment": tr,
                "entry_point": ep,
                "generation_id": generation_id,
                "raw_sha256": result.input_sha256,
                "post_h1_sha256": result.h1_output_sha256,
                "post_h2_sha256": result.h2_output_sha256,
                "post_h3_sha256": result.h3_output_sha256,
                "post_h4_sha256": result.h4_output_sha256,
                "final_sha256": result.final_sha256,
                "layers_invoked": ["H1", "H2", "H3", "H4"],
                "layers_changed": layers_changed,
                "rules_triggered": sorted(set(rules_triggered)),
                "rules_applied": rules_applied,
                "abstention_reason_by_layer": abstention_reason_by_layer,
                "first_effective_rule": first_effective_rule,
                "transform_class": result.transform_class,
                "raw_parse_status": raw_parse_status,
                "cumulative_parse_status": cumulative_parse_status,
                "extraction_status": ext_res.extraction_status,
                "generation_truncated": truncated,
                "arity_contract": list(arities),
                "raw_source": ext_code,
                "final_source": final_source,
                "persisted_complete": True,
                "runner_identity": "public_benchmark_h1_h2_h3_h4_replay_v1",
                "experiment_label": "cumulative_H1_H4_candidate_replay",
            }
            durable_write_json_new(j_file, journal)
            executed_cells += 1
            ledger_rows.append(
                {
                    "cell_identity": cell_id,
                    "task_id": tid,
                    "treatment": tr,
                    "transform_class": result.transform_class,
                }
            )

    _require(duplicate_count == 0, f"duplicate cell_identity detected: {duplicate_count}")

    summary = {
        "status": "cumulative_replay_execution_completed",
        "experiment_label": "cumulative_H1_H4_candidate_replay",
        "model_tag": model,
        "dataset": dataset,
        "output_directory": out_dir.as_posix(),
        "fixed_order": ["H1", "H2", "H3", "H4"],
        "raw_generations": inventory["present_raw_generations"],
        "planned_pairs": len(tasks) * 2,
        "executed_cells": executed_cells,
        "skipped_resume_cells": skipped_cells,
        "missing": 0,
        "duplicate": duplicate_count,
        "model_calls": 0,
        "evalplus_executed": False,
    }

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_path = out_dir / "cell_level_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cell_identity", "task_id", "treatment", "transform_class"])
        for row in ledger_rows:
            writer.writerow([row["cell_identity"], row["task_id"], row["treatment"], row["transform_class"]])

    manifest_path = out_dir / "execution_manifest.json"
    manifest_data = {
        "plan_id": f"{spec['model_key']}_h1_h2_h3_h4_full_replay_v1",
        "experiment_label": "cumulative_H1_H4_candidate_replay",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_tag": model,
        "dataset": dataset,
        "fixed_order": ["H1", "H2", "H3", "H4"],
        "rule_ids": RULE_IDS,
        "rule_statuses": RULE_STATUSES,
        "executed_cells": executed_cells + skipped_cells,
        "model_calls": 0,
        "evalplus_executed": False,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=ALLOWED_MODELS)
    parser.add_argument("--dataset", default="all", choices=ALLOWED_DATASETS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)

    if args.parallel != 1:
        _require(False, "--parallel must be 1 for strict determinism")

    if args.dry_run:
        result = run_dry_run(model=args.model, dataset=args.dataset, output_dir_arg=args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    result = run_replay_execution(
        model=args.model,
        dataset=args.dataset,
        resume=args.resume,
        output_dir_arg=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
