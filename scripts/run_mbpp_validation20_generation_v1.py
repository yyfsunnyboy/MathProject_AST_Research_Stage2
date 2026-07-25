#!/usr/bin/env python3
"""Validation20 per-model generation runner (single --model per invocation).

Modes:
  plan / preflight : zero model calls
  identity-check   : read-only Ollama /api/tags inspect (no generation)
  generate         : formal generation (requires dual acknowledgement)
  resume           : continue one model run with fail-closed identity match

Never auto-runs multiple models. Never pulls 2B. Never runs EvalPlus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    durable_write_json_new,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    OllamaGenerationSettings,
    run_attempt,
)
from scripts import freeze_mbpp_validation20_scaffold_healer_v3 as freeze  # noqa: E402
from scripts import preflight_mbpp_validation20_generation_v1 as preflight_mod  # noqa: E402

RUNNER_IDENTITY = "mbpp_validation20_generation_runner_v1"
GENERATE_ACK = "I_ACKNOWLEDGE_THIS_WILL_CALL_THE_PINNED_VALIDATION20_MODEL"
DEFAULT_TIMEOUT_SECONDS = 600.0


class GenerationRunnerError(RuntimeError):
    """Fail-closed generation runner violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationRunnerError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_model_manifest(model_tag: str, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    path = repo_root / freeze.model_dir(model_tag) / "model_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_cells(model_tag: str, repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    path = repo_root / freeze.model_dir(model_tag) / "generation_cells.csv"
    cells = _read_csv(path)
    _require(len(cells) == 400, "generation cells must be exactly 400")
    return cells


def fetch_live_model_identity(base_url: str, model_tag: str, timeout: float) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        raw = response.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    payload = json.loads(raw.decode("utf-8"))
    models = payload.get("models") or []
    matches = [row for row in models if row.get("name") == model_tag]
    _require(len(matches) == 1, f"model tag not uniquely present in Ollama /api/tags: {model_tag}")
    row = matches[0]
    details = row.get("details") or {}
    digest = row.get("digest")
    _require(isinstance(digest, str) and len(digest) == 64, "live digest missing or truncated")
    return {
        "tag": model_tag,
        "digest": digest,
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
        "family": details.get("family"),
        "format": details.get("format"),
        "size_bytes": row.get("size"),
        "modified_at": row.get("modified_at"),
        "identity_status": "machine_verified_on_execution_host",
        "identity_source": "local_ollama_/api/tags",
    }


def assert_identity_matches_manifest(
    live: Mapping[str, Any],
    manifest_model: Mapping[str, Any],
) -> None:
    if manifest_model.get("identity_status") == "pending_machine_verification":
        raise GenerationRunnerError(
            f"{manifest_model['tag']}: identity still pending_machine_verification; "
            "record live digest/quantization/family into the execution-host identity "
            "receipt before generate"
        )
    _require(live["tag"] == manifest_model["tag"], "live tag mismatch")
    _require(live["digest"] == manifest_model["digest"], "live digest mismatch vs pinned manifest")
    _require(
        live["quantization_level"] == manifest_model["quantization_level"],
        "live quantization mismatch",
    )
    _require(
        live["parameter_size"] == manifest_model["parameter_size"],
        "live parameter_size mismatch",
    )
    _require(live["family"] == manifest_model["family"], "live family mismatch")
    _require(live["format"] == manifest_model["format"], "live format mismatch")


def journal_path(run_dir: Path, generation_id: str) -> Path:
    return run_dir / "j" / f"{generation_id}.json"


def load_journal(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "persisted_complete": False,
            "completion_flag": "corrupt",
            "error_status": "journal_unreadable",
        }


def resume_skip_eligible(
    journal: Mapping[str, Any],
    *,
    cell: Mapping[str, str],
    model_digest: str,
    manifest_sha256: str,
) -> bool:
    required = {
        "cell_identity": cell["cell_identity"],
        "generation_id": cell["generation_id"],
        "model_tag": cell["model_tag"],
        "model_digest": model_digest,
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "prompt_condition": cell["prompt_condition"],
        "seed": int(cell["seed"]),
        "completion_flag": "success",
        "persisted_complete": True,
        "manifest_sha256": manifest_sha256,
    }
    for key, expected in required.items():
        if journal.get(key) != expected:
            return False
    return True


def compose_prompt_for_cell(
    cell: Mapping[str, str],
    prompts: Mapping[str, str],
    ab2g_text: str,
) -> str:
    return freeze.compose_full_prompt(
        official_prompt=prompts[cell["task_id"]],
        prompt_condition=cell["prompt_condition"],
        ab2g_text=ab2g_text,
    )


def write_raw_sha_ledger(run_dir: Path, rows: list[dict[str, Any]]) -> None:
    fields = (
        "generation_id",
        "cell_identity",
        "task_id",
        "seed",
        "prompt_condition",
        "model_tag",
        "model_digest",
        "raw_response_sha256",
        "journal_path",
        "completion_flag",
    )
    path = run_dir / "raw_candidate_sha_ledger.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def cmd_plan(model_tag: str) -> dict[str, Any]:
    manifest = load_model_manifest(model_tag)
    cells = load_cells(model_tag)
    return {
        "status": "plan_only",
        "model_tag": model_tag,
        "run_id": manifest["run_id"],
        "candidates": len(cells),
        "output_directory": manifest["paths"]["generation_output_dir"],
        "identity_status": manifest["model"]["identity_status"],
        "model_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
    }


def cmd_identity_check(model_tag: str, *, base_url: str, timeout: float) -> dict[str, Any]:
    manifest = load_model_manifest(model_tag)
    live = fetch_live_model_identity(base_url, model_tag, timeout)
    pinned = manifest["model"]
    comparable = pinned.get("identity_status") != "pending_machine_verification"
    matches = False
    if comparable:
        try:
            assert_identity_matches_manifest(live, pinned)
            matches = True
        except GenerationRunnerError:
            matches = False
    return {
        "status": "identity_check_complete",
        "model_tag": model_tag,
        "pinned_identity_status": pinned.get("identity_status"),
        "live_identity": live,
        "matches_pinned_manifest": matches,
        "model_calls": 0,
        "ollama_generation_calls": 0,
        "candidate_program_executed": False,
        "evalplus_executed": False,
        "note": (
            "identity-check only inspects /api/tags; it does not generate completions"
        ),
    }


def cmd_generate(
    model_tag: str,
    *,
    base_url: str,
    timeout: float,
    resume: bool,
    acknowledgement: str,
) -> dict[str, Any]:
    _require(acknowledgement == GENERATE_ACK, "generate acknowledgement mismatch")
    _require("2b" not in model_tag.lower(), "2B models are forbidden")

    preflight_mod.zero_model_preflight(
        model=model_tag,
        require_verified_identity=True,
        require_output_absent=not resume,
    )
    manifest = load_model_manifest(model_tag)
    cells = load_cells(model_tag)
    live = fetch_live_model_identity(base_url, model_tag, timeout)
    assert_identity_matches_manifest(live, manifest["model"])

    run_dir = REPO_ROOT / freeze.MODEL_SPECS[model_tag]["run_output_relative"]
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "j").mkdir(parents=True, exist_ok=True)

    tasks = freeze.load_validation_tasks(REPO_ROOT)
    prompts = {task["task_id"]: task["prompt"] for task in tasks}
    ab2g_text = freeze.load_ab2g_text(REPO_ROOT)
    manifest_bytes = (
        REPO_ROOT / freeze.model_dir(model_tag) / "model_manifest.json"
    ).read_bytes()
    manifest_sha256 = _sha256_bytes(manifest_bytes)
    decoding_options_sha256 = manifest["generation_options_sha256"]

    ledger_rows: list[dict[str, Any]] = []
    generated = 0
    skipped = 0
    for cell in cells:
        path = journal_path(run_dir, cell["generation_id"])
        existing = load_journal(path)
        if existing and resume_skip_eligible(
            existing,
            cell=cell,
            model_digest=live["digest"],
            manifest_sha256=manifest_sha256,
        ):
            skipped += 1
            ledger_rows.append(
                {
                    "generation_id": cell["generation_id"],
                    "cell_identity": cell["cell_identity"],
                    "task_id": cell["task_id"],
                    "seed": cell["seed"],
                    "prompt_condition": cell["prompt_condition"],
                    "model_tag": model_tag,
                    "model_digest": live["digest"],
                    "raw_response_sha256": existing.get("raw_response_sha256", ""),
                    "journal_path": path.relative_to(REPO_ROOT).as_posix(),
                    "completion_flag": existing.get("completion_flag", ""),
                }
            )
            continue
        if path.exists():
            raise GenerationRunnerError(
                f"incomplete/mismatched journal present; refuse overwrite: {path}"
            )

        composed = compose_prompt_for_cell(cell, prompts, ab2g_text)
        _require(
            _sha256_text(composed) == cell["composed_prompt_sha256"],
            f"composed prompt SHA drift: {cell['generation_id']}",
        )
        started = _utc_now()
        # Treatment is always "ab1" with a precomposed Validation20 prompt so
        # the shared runner does not double-apply its built-in Ab2g scaffold.
        settings = OllamaGenerationSettings(
            model=model_tag,
            seed=int(cell["seed"]),
            temperature=float(freeze.GENERATION_OPTIONS["temperature"]),
            top_p=float(freeze.GENERATION_OPTIONS["top_p"]),
            top_k=int(freeze.GENERATION_OPTIONS["top_k"]),
            num_predict=int(freeze.GENERATION_OPTIONS["num_predict"]),
            thinking=bool(freeze.GENERATION_OPTIONS["thinking"]),
            context_window=int(freeze.GENERATION_OPTIONS["num_ctx"]),
            stream=bool(freeze.GENERATION_OPTIONS["stream"]),
            expected_digest_prefix=live["digest"],
        )
        task = PublicBenchmarkTask(
            benchmark="mbpp",
            task_id=cell["task_id"],
            prompt=composed,
            entry_point=cell["expected_entry_point"],
            canonical_solution=None,
        )
        attempt = run_attempt(
            task,
            "ab1",
            benchmark="mbpp",
            base_url=base_url,
            timeout_seconds=timeout,
            settings=settings,
            model_digest=live["digest"],
            sample_index=int(cell["sample_index"]),
        )
        raw_response = attempt.get("raw_response") or ""
        ok = attempt.get("status") == "success"
        journal = {
            "cell_identity": cell["cell_identity"],
            "generation_id": cell["generation_id"],
            "task_id": cell["task_id"],
            "seed": int(cell["seed"]),
            "prompt_condition": cell["prompt_condition"],
            "model_tag": model_tag,
            "model_digest": live["digest"],
            "manifest_sha256": manifest_sha256,
            "composed_prompt_sha256": cell["composed_prompt_sha256"],
            "decoding_options_sha256": decoding_options_sha256,
            "runner_identity": RUNNER_IDENTITY,
            "raw_response": raw_response,
            "raw_response_sha256": _sha256_text(raw_response) if raw_response else "",
            "persisted_complete": True,
            "completion_flag": "success" if ok else "failed",
            "generation_status": "complete_single_attempt" if ok else "failed",
            "started_at": started,
            "finished_at": _utc_now(),
            "attempt_record": attempt,
            "retry_count": 0,
            "resume": bool(resume),
        }
        durable_write_json_new(path, journal)
        generated += 1
        ledger_rows.append(
            {
                "generation_id": cell["generation_id"],
                "cell_identity": cell["cell_identity"],
                "task_id": cell["task_id"],
                "seed": cell["seed"],
                "prompt_condition": cell["prompt_condition"],
                "model_tag": model_tag,
                "model_digest": live["digest"],
                "raw_response_sha256": journal["raw_response_sha256"],
                "journal_path": path.relative_to(REPO_ROOT).as_posix(),
                "completion_flag": journal["completion_flag"],
            }
        )

    write_raw_sha_ledger(run_dir, ledger_rows)
    execution_manifest = {
        "status": "generation_complete_pending_derivatives",
        "plan_id": freeze.PLAN_ID,
        "run_id": manifest["run_id"],
        "model_tag": model_tag,
        "model_digest": live["digest"],
        "manifest_sha256": manifest_sha256,
        "cells_total": len(cells),
        "generated_this_invocation": generated,
        "resume_skipped": skipped,
        "model_calls": generated,
        "candidate_program_executed": False,
        "evalplus_executed": False,
        "raw_candidate_sha_ledger": (
            freeze.MODEL_SPECS[model_tag]["run_output_relative"]
            / "raw_candidate_sha_ledger.csv"
        ).as_posix(),
    }
    durable_write_json_new(run_dir / "execution_manifest.json", execution_manifest)
    return execution_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=freeze.ALLOWED_MODEL_TAGS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--identity-check", action="store_true")
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument(
        "--require-verified-identity",
        action="store_true",
        help="For --preflight: require machine-verified digest fields.",
    )
    args = parser.parse_args(argv)

    model_tag = args.model
    _require("2b" not in model_tag.lower(), "2B models are forbidden")

    if args.plan:
        print(json.dumps(cmd_plan(model_tag), indent=2, sort_keys=True))
        return 0
    if args.preflight:
        receipt = preflight_mod.zero_model_preflight(
            model=model_tag,
            require_verified_identity=args.require_verified_identity,
            require_output_absent=True,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    if args.identity_check:
        print(
            json.dumps(
                cmd_identity_check(
                    model_tag, base_url=args.base_url, timeout=args.timeout_seconds
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.generate or args.resume:
        result = cmd_generate(
            model_tag,
            base_url=args.base_url,
            timeout=args.timeout_seconds,
            resume=bool(args.resume),
            acknowledgement=args.acknowledgement,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    raise GenerationRunnerError("no mode selected")


if __name__ == "__main__":
    raise SystemExit(main())
