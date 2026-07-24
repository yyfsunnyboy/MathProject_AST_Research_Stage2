#!/usr/bin/env python3
"""Controlled runner for the 4B development-only failure-supply pilot.

Modes:
- plan / inspect: show the frozen 200-cell plan (zero model, zero writes)
- preflight: offline freeze/manifest/split/isolation checks
- generate: formal crash-safe generation path (requires explicit dual confirmation)
- resume-check: offline resume identity matrix

This module enables the generate path but does not itself execute a live run.
Live model calls occur only when an operator invokes generate with all safety
flags and a matching frozen manifest SHA.

Safety invariants:
- never modifies Healer
- never evaluates with EvalPlus
- never executes candidate code
- never overwrites 9B / foreign artifacts
- never expands beyond the frozen 200-cell plan
- resume skip only on full identity match + persisted_complete=true
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild.benchmarks_adapter import PublicBenchmarkTask  # noqa: E402
from agent_tools.finals_rebuild.generation_persistence import (  # noqa: E402
    PersistenceError,
    durable_write_json_new,
)
from agent_tools.finals_rebuild.ollama_generation_runner import (  # noqa: E402
    DEFAULT_BASE_URL,
    fetch_ollama_provenance,
    load_generation_protocol,
    protocol_settings,
    run_attempt,
)
from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as freeze  # noqa: E402
from scripts import (  # noqa: E402
    preflight_candidate_b_4b_development_failure_supply_pilot_v1 as preflight_mod,
)

RUNNER_STATUS = "RUNNER_ENABLED_NOT_EXECUTED"
RUNNER_IDENTITY = "candidate_b_4b_development_failure_supply_pilot_runner_v1"
EXECUTION_ACKNOWLEDGEMENT = (
    "I_ACKNOWLEDGE_THIS_WILL_CALL_QWEN35_4B_FOR_200_DEVELOPMENT_ONLY_CELLS"
)
DEFAULT_TIMEOUT_SECONDS = 600.0
DECODING_OPTIONS_SHA256 = hashlib.sha256(
    json.dumps(freeze.GENERATION_OPTIONS, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
).hexdigest()

# Pinned after freeze; resolved from disk when None.
FROZEN_MANIFEST_SHA256: str | None = None

ProvenanceFn = Callable[..., dict[str, Any]]
GenerateCellFn = Callable[..., dict[str, Any]]


class PilotRunError(RuntimeError):
    """Fail-closed runner violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotRunError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_manifest_sha256(repo_root: Path = REPO_ROOT) -> str:
    global FROZEN_MANIFEST_SHA256
    if FROZEN_MANIFEST_SHA256 is None:
        FROZEN_MANIFEST_SHA256 = _sha256_bytes(
            (repo_root / freeze.OUTPUT_RELATIVE / "manifest.json").read_bytes()
        )
    return FROZEN_MANIFEST_SHA256


def load_frozen_manifest(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads(
        (repo_root / freeze.OUTPUT_RELATIVE / "manifest.json").read_text(encoding="utf-8")
    )


def load_frozen_cells(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    cells = _read_csv(repo_root / freeze.OUTPUT_RELATIVE / "generation_cells.csv")
    _require(len(cells) == freeze.EXPECTED_CELL_COUNT, "frozen cell plan != 200")
    return cells


def resolve_run_dir(repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / freeze.RUN_OUTPUT_RELATIVE


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


def assert_no_foreign_overwrite(repo_root: Path) -> None:
    pilot = (repo_root / freeze.RUN_OUTPUT_RELATIVE).resolve()
    governance = (repo_root / freeze.OUTPUT_RELATIVE).resolve()
    _require(pilot != governance, "pilot output must not write into governance freeze dir")
    for relative in (
        freeze.NINE_B_RUN_RELATIVE,
        freeze.NINE_B_AB1_RUN_RELATIVE,
        freeze.NINE_B_SCAFFOLD_RUN_RELATIVE,
        freeze.OUTPUT_RELATIVE,
    ):
        other = (repo_root / relative).resolve()
        _require(other != pilot, f"refusing pilot path collision with {relative.as_posix()}")


def assert_development_only_cells(cells: Sequence[Mapping[str, str]]) -> None:
    task_ids = [row["task_id"] for row in cells]
    _require(sorted(set(task_ids)) == sorted(freeze.ACTIVE_TASK_IDS), "task list drift")
    _require(all(row["development_only"] == "true" for row in cells), "non-development cell")
    for row in cells:
        for banned in freeze.FORBIDDEN_ROLES:
            _require(banned not in row["task_id"], f"forbidden role token in task_id: {banned}")
            _require(
                banned not in row.get("condition_id", ""),
                f"forbidden role token in condition: {banned}",
            )


def _git_head(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotRunError(f"failed to resolve git HEAD: {exc}") from exc
    head = (proc.stdout or "").strip()
    _require(proc.returncode == 0 and bool(head), "git rev-parse HEAD failed")
    return head


def compose_prompt_for_cell(
    official_prompt: str,
    cell: Mapping[str, str],
    scaffold_text: str,
) -> str:
    if cell["scaffold_mode"] == "bare":
        return official_prompt
    _require(
        cell["scaffold_mode"] == "generic_scaffold_v0",
        f"unknown scaffold_mode: {cell['scaffold_mode']}",
    )
    return official_prompt + freeze.PROMPT_SEPARATOR + scaffold_text


def load_official_prompts(repo_root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    path = repo_root / freeze.TASKS_RELATIVE
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id not in freeze.ACTIVE_TASK_IDS:
                continue
            _require(
                set(record) == {"task_id", "prompt", "entry_point"},
                f"unexpected model-visible fields for {task_id}",
            )
            found[task_id] = record["prompt"]
    missing = [task_id for task_id in freeze.ACTIVE_TASK_IDS if task_id not in found]
    _require(not missing, f"missing prompts: {missing}")
    return found


def load_entry_points(repo_root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    path = repo_root / freeze.TASKS_RELATIVE
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            task_id = record.get("task_id")
            if task_id in freeze.ACTIVE_TASK_IDS:
                found[task_id] = record["entry_point"]
    return found


def required_journal_fields() -> tuple[str, ...]:
    return (
        "cell_identity",
        "task_id",
        "seed",
        "condition_id",
        "model_tag",
        "model_digest",
        "manifest_sha256",
        "composed_prompt_sha256",
        "decoding_options_sha256",
        "runner_identity",
        "protocol_sha256",
        "raw_response",
        "persisted_complete",
        "completion_flag",
        "generation_status",
        "started_at",
        "completed_at",
    )


def journal_is_complete(journal: Mapping[str, Any]) -> bool:
    if journal.get("persisted_complete") is not True:
        return False
    raw = journal.get("raw_response")
    if not isinstance(raw, str) or not raw.strip():
        return False
    if "raw_response_sha256" in journal:
        if _sha256_text(raw) != journal["raw_response_sha256"]:
            return False

    # Check for new vs legacy format
    new_fields = [
        "generation_completed",
        "raw_response_persisted",
        "extraction_succeeded",
        "extraction_status",
        "extracted_code",
        "error_stage",
    ]
    present_new = [f in journal for f in new_fields]
    if any(present_new):
        # Fail closed: if one new field is present, ALL must be present
        if not all(present_new):
            return False
        # Verify new format completion logic
        if journal.get("generation_completed") is not True:
            return False
        if journal.get("raw_response_persisted") is not True:
            return False
        # extracted_code must be string if extraction_succeeded is True, else must be None
        if journal.get("extraction_succeeded") is True:
            if not isinstance(journal.get("extracted_code"), str):
                return False
        else:
            if journal.get("extracted_code") is not None:
                return False
        # error_stage must be one of none, generation, persistence, extraction
        if journal.get("error_stage") not in ("none", "generation", "persistence", "extraction"):
            return False
    else:
        # Legacy format verification
        if journal.get("completion_flag") != "success":
            return False
        if journal.get("generation_status") != "success":
            return False

    for field in required_journal_fields():
        if field not in journal:
            return False
    return True


def resume_identity_matches(
    cell: Mapping[str, str],
    journal: Mapping[str, Any],
    *,
    manifest_sha256: str,
    protocol_sha256: str,
) -> tuple[bool, str]:
    """Return (ok, message). ok means safe to skip as complete."""
    if not journal_is_complete(journal):
        return False, "journal incomplete or missing required completion fields"

    checks: dict[str, tuple[Any, Any]] = {
        "cell_identity": (cell["cell_identity"], journal.get("cell_identity")),
        "task_id": (cell["task_id"], journal.get("task_id")),
        "seed": (int(cell["seed"]), int(journal.get("seed", -1))),
        "condition_id": (cell["condition_id"], journal.get("condition_id")),
        "model_tag": (cell["model_tag"], journal.get("model_tag")),
        "model_digest": (cell["model_digest"], journal.get("model_digest")),
        "manifest_sha256": (manifest_sha256, journal.get("manifest_sha256")),
        "composed_prompt_sha256": (
            cell["composed_prompt_sha256"],
            journal.get("composed_prompt_sha256"),
        ),
        "decoding_options_sha256": (
            DECODING_OPTIONS_SHA256,
            journal.get("decoding_options_sha256"),
        ),
        "runner_identity": (RUNNER_IDENTITY, journal.get("runner_identity")),
        "protocol_sha256": (protocol_sha256, journal.get("protocol_sha256")),
        "generation_id": (cell["generation_id"], journal.get("generation_id")),
        "run_id": (freeze.RUN_ID, journal.get("run_id")),
    }
    for name, (expected, actual) in checks.items():
        if expected != actual:
            return False, f"resume identity mismatch on {name}: {actual!r} != {expected!r}"
    return True, "ok"


def _partial_identity_conflict(
    cell: Mapping[str, str],
    journal: Mapping[str, Any],
    *,
    manifest_sha256: str,
) -> str | None:
    """If an incomplete journal conflicts on pinned identity, return error."""
    pinned = {
        "cell_identity": (cell["cell_identity"], journal.get("cell_identity")),
        "task_id": (cell["task_id"], journal.get("task_id")),
        "seed": (
            int(cell["seed"]),
            int(journal["seed"]) if journal.get("seed") is not None else None,
        ),
        "condition_id": (cell["condition_id"], journal.get("condition_id")),
        "model_tag": (cell["model_tag"], journal.get("model_tag")),
        "model_digest": (cell["model_digest"], journal.get("model_digest")),
        "manifest_sha256": (manifest_sha256, journal.get("manifest_sha256")),
        "composed_prompt_sha256": (
            cell["composed_prompt_sha256"],
            journal.get("composed_prompt_sha256"),
        ),
        "generation_id": (cell["generation_id"], journal.get("generation_id")),
    }
    for name, (expected, actual) in pinned.items():
        if actual is None:
            continue
        if actual != expected:
            return f"incomplete journal identity conflict on {name}: {actual!r} != {expected!r}"
    return None


def decide_resume_action(
    cell: Mapping[str, str],
    run_dir: Path,
    *,
    manifest_sha256: str | None = None,
    protocol_sha256: str | None = None,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Return 'skip', 'generate', or 'retry_incomplete'. Raise on mismatch."""
    manifest_sha = manifest_sha256 or resolve_manifest_sha256(repo_root)
    protocol_sha = protocol_sha256 or freeze.EXPECTED_PROTOCOL_SHA256
    path = journal_path(run_dir, cell["generation_id"])
    journal = load_journal(path)
    if journal is None:
        return "generate"
    if journal_is_complete(journal):
        ok, message = resume_identity_matches(
            cell,
            journal,
            manifest_sha256=manifest_sha,
            protocol_sha256=protocol_sha,
        )
        if not ok:
            raise PilotRunError(message)
        return "skip"
    conflict = _partial_identity_conflict(
        cell, journal, manifest_sha256=manifest_sha
    )
    if conflict:
        raise PilotRunError(conflict)
    return "retry_incomplete"


def quarantine_incomplete_journal(path: Path, run_dir: Path) -> Path:
    quarantine_dir = run_dir / "j_incomplete_quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = quarantine_dir / f"{path.stem}.{stamp}.json"
    _require(not target.exists(), f"quarantine target exists: {target}")
    shutil.move(str(path), str(target))
    return target


def fetch_live_model_identity(
    *,
    base_url: str,
    timeout_seconds: float,
    expected_tag: str = freeze.MODEL_TAG,
    expected_digest: str = freeze.MODEL_DIGEST,
) -> dict[str, Any]:
    """Read-only /api/tags + /api/version check. Never calls generation."""
    try:
        provenance = fetch_ollama_provenance(
            base_url,
            timeout_seconds,
            model=expected_tag,
            expected_digest_prefix=expected_digest,
        )
    except Exception as exc:  # noqa: BLE001 - fail closed on any transport error
        raise PilotRunError(
            f"live model identity gate failed (service/metadata unavailable): {exc}"
        ) from exc
    digest = provenance.get("model_digest")
    tag = provenance.get("model_tag") or provenance.get("model_name")
    _require(tag == expected_tag, f"model tag mismatch: {tag!r} != {expected_tag!r}")
    _require(
        digest == expected_digest,
        f"model digest mismatch: {digest!r} != {expected_digest!r}",
    )
    runtime_version = provenance.get("runtime_version") or provenance.get("ollama_version")
    _require(
        isinstance(runtime_version, str) and bool(runtime_version.strip()),
        "live runtime version missing",
    )
    return {
        "model_tag": tag,
        "model_digest": digest,
        "quantization": provenance.get("quantization"),
        "model_size": provenance.get("model_size"),
        "model_modified_at": provenance.get("model_modified_at"),
        "runtime": provenance.get("runtime"),
        "runtime_version": runtime_version,
        "api_base_url": base_url,
        "protocol_ollama_version_pin": freeze.PROTOCOL_OLLAMA_VERSION,
        "note": (
            "protocol_ollama_version_pin is a compatibility pin only; "
            "runtime_version is the live observed Ollama version and must not be "
            "confused with the pin or any historical prereg observation."
        ),
        "checked_at": _utc_now(),
        "generation_endpoint_called": False,
    }


def build_execution_manifest(
    *,
    repo_root: Path,
    argv: Sequence[str],
    manifest_sha256: str,
    live_identity: Mapping[str, Any],
    safety_flags: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": RUNNER_STATUS,
        "runner_identity": RUNNER_IDENTITY,
        "run_id": freeze.RUN_ID,
        "output_directory": freeze.RUN_OUTPUT_RELATIVE.as_posix(),
        "frozen_governance_directory": freeze.OUTPUT_RELATIVE.as_posix(),
        "frozen_manifest_sha256": manifest_sha256,
        "protocol_sha256": freeze.EXPECTED_PROTOCOL_SHA256,
        "decoding_options_sha256": DECODING_OPTIONS_SHA256,
        "decoding_options": freeze.GENERATION_OPTIONS,
        "git_head": _git_head(repo_root),
        "command_argv": list(argv),
        "safety_confirmation": dict(safety_flags),
        "live_model_identity": dict(live_identity),
        "cell_plan_source": (
            freeze.OUTPUT_RELATIVE / "generation_cells.csv"
        ).as_posix(),
        "expected_cell_count": freeze.EXPECTED_CELL_COUNT,
        "healer_modification_allowed": False,
        "evaluation_allowed": False,
        "candidate_code_execution_allowed": False,
        "auto_expand_to_60_forbidden": True,
        "created_at": _utc_now(),
    }


def build_success_journal(
    *,
    cell: Mapping[str, str],
    raw_response: str,
    manifest_sha256: str,
    protocol_sha256: str,
    live_identity: Mapping[str, Any],
    request_metadata: Mapping[str, Any] | None,
    response_metadata: Mapping[str, Any] | None,
    started_at: str,
    completed_at: str,
    extracted_code: str,
) -> dict[str, Any]:
    _require(isinstance(raw_response, str) and raw_response.strip(), "empty raw_response")
    return {
        "generation_id": cell["generation_id"],
        "program_id": cell["program_id"],
        "run_id": freeze.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "condition_id": cell["condition_id"],
        "generation_condition": cell["generation_condition"],
        "scaffold_mode": cell["scaffold_mode"],
        "healer_account_mapping": cell["healer_account_mapping"],
        "prompt_condition": cell["prompt_condition"],
        "official_prompt_sha256": cell["official_prompt_sha256"],
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "scaffold_sha256": cell.get("scaffold_sha256", ""),
        "model_tag": cell["model_tag"],
        "model_digest": cell["model_digest"],
        "manifest_sha256": manifest_sha256,
        "protocol_sha256": protocol_sha256,
        "decoding_options_sha256": DECODING_OPTIONS_SHA256,
        "decoding_options": freeze.GENERATION_OPTIONS,
        "runner_identity": RUNNER_IDENTITY,
        "development_only": True,
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_text(raw_response),
        "request_metadata": dict(request_metadata or {}),
        "response_metadata": dict(response_metadata or {}),
        "live_model_identity": {
            "model_tag": live_identity.get("model_tag"),
            "model_digest": live_identity.get("model_digest"),
            "runtime_version": live_identity.get("runtime_version"),
            "quantization": live_identity.get("quantization"),
        },
        "started_at": started_at,
        "completed_at": completed_at,
        "persisted_complete": True,
        "completion_flag": "success",
        "generation_status": "success",
        "error_status": None,
        "error_message": None,
        "healer_applied": False,
        "candidate_code_executed": False,
        "evaluation_executed": False,
        
        "generation_completed": True,
        "raw_response_persisted": True,
        "extraction_succeeded": True,
        "extraction_status": "success",
        "extracted_code": extracted_code,
        "postprocess_status": "success",
        "error_stage": "none",
    }


def build_extraction_failed_journal(
    *,
    cell: Mapping[str, str],
    raw_response: str,
    manifest_sha256: str,
    protocol_sha256: str,
    live_identity: Mapping[str, Any],
    request_metadata: Mapping[str, Any] | None,
    response_metadata: Mapping[str, Any] | None,
    started_at: str,
    completed_at: str,
    extraction_status: str,
    error_message: str,
) -> dict[str, Any]:
    _require(isinstance(raw_response, str) and raw_response.strip(), "empty raw_response")
    return {
        "generation_id": cell["generation_id"],
        "program_id": cell["program_id"],
        "run_id": freeze.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "condition_id": cell["condition_id"],
        "generation_condition": cell["generation_condition"],
        "scaffold_mode": cell["scaffold_mode"],
        "healer_account_mapping": cell["healer_account_mapping"],
        "prompt_condition": cell["prompt_condition"],
        "official_prompt_sha256": cell["official_prompt_sha256"],
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "scaffold_sha256": cell.get("scaffold_sha256", ""),
        "model_tag": cell["model_tag"],
        "model_digest": cell["model_digest"],
        "manifest_sha256": manifest_sha256,
        "protocol_sha256": protocol_sha256,
        "decoding_options_sha256": DECODING_OPTIONS_SHA256,
        "decoding_options": freeze.GENERATION_OPTIONS,
        "runner_identity": RUNNER_IDENTITY,
        "development_only": True,
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_text(raw_response),
        "request_metadata": dict(request_metadata or {}),
        "response_metadata": dict(response_metadata or {}),
        "live_model_identity": {
            "model_tag": live_identity.get("model_tag"),
            "model_digest": live_identity.get("model_digest"),
            "runtime_version": live_identity.get("runtime_version"),
            "quantization": live_identity.get("quantization"),
        },
        "started_at": started_at,
        "completed_at": completed_at,
        "persisted_complete": True,
        "completion_flag": "error",
        "generation_status": "success",
        "error_status": "extraction_failed",
        "error_message": error_message,
        "healer_applied": False,
        "candidate_code_executed": False,
        "evaluation_executed": False,
        
        "generation_completed": True,
        "raw_response_persisted": True,
        "extraction_succeeded": False,
        "extraction_status": extraction_status,
        "extracted_code": None,
        "postprocess_status": extraction_status,
        "error_stage": "extraction",
    }


def build_error_journal(
    *,
    cell: Mapping[str, str],
    manifest_sha256: str,
    protocol_sha256: str,
    live_identity: Mapping[str, Any],
    started_at: str,
    completed_at: str,
    error_message: str,
    request_metadata: Mapping[str, Any] | None = None,
    response_metadata: Mapping[str, Any] | None = None,
    raw_response: str | None = None,
) -> dict[str, Any]:
    return {
        "generation_id": cell["generation_id"],
        "program_id": cell["program_id"],
        "run_id": freeze.RUN_ID,
        "cell_index": int(cell["cell_index"]),
        "cell_identity": cell["cell_identity"],
        "task_id": cell["task_id"],
        "seed": int(cell["seed"]),
        "sample_index": int(cell["sample_index"]),
        "condition_id": cell["condition_id"],
        "model_tag": cell["model_tag"],
        "model_digest": cell["model_digest"],
        "manifest_sha256": manifest_sha256,
        "protocol_sha256": protocol_sha256,
        "decoding_options_sha256": DECODING_OPTIONS_SHA256,
        "runner_identity": RUNNER_IDENTITY,
        "composed_prompt_sha256": cell["composed_prompt_sha256"],
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_text(raw_response) if raw_response else None,
        "request_metadata": dict(request_metadata or {}),
        "response_metadata": dict(response_metadata or {}),
        "live_model_identity": {
            "model_tag": live_identity.get("model_tag"),
            "model_digest": live_identity.get("model_digest"),
            "runtime_version": live_identity.get("runtime_version"),
        },
        "started_at": started_at,
        "completed_at": completed_at,
        "persisted_complete": False,
        "completion_flag": "error",
        "generation_status": "failed",
        "error_status": "generation_failed",
        "error_message": error_message,
        "healer_applied": False,
        "candidate_code_executed": False,
        "evaluation_executed": False,
        
        "generation_completed": False,
        "raw_response_persisted": False,
        "extraction_succeeded": False,
        "extraction_status": "error",
        "extracted_code": None,
        "postprocess_status": "error",
        "error_stage": "generation",
    }


def persist_journal(run_dir: Path, cell: Mapping[str, str], record: Mapping[str, Any]) -> None:
    _require(
        record["generation_id"] == cell["generation_id"],
        "journal generation_id mismatch",
    )
    path = journal_path(run_dir, cell["generation_id"])
    try:
        durable_write_json_new(path, dict(record))
    except PersistenceError as exc:
        raise PilotRunError(f"atomic journal persist failed: {exc}") from exc


def live_generate_cell(
    *,
    cell: Mapping[str, str],
    composed_prompt: str,
    entry_point: str,
    base_url: str,
    timeout_seconds: float,
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """One-cell live Ollama generation using the battle-tested run_attempt path.

    Treatment is always 'ab1' with a precomposed prompt so Ab2g does not double-apply
    the inline AB2G_SCAFFOLD (parity with the scaffold v0 runner pattern).
    """
    settings = protocol_settings(
        dict(protocol),
        model_role="frozen_transfer_model",
        seed=int(cell["seed"]),
    )
    _require(settings.model == freeze.MODEL_TAG, "protocol settings model tag drift")
    task = PublicBenchmarkTask(
        benchmark="mbpp",
        task_id=cell["task_id"],
        prompt=composed_prompt,
        entry_point=entry_point,
        canonical_solution=None,
    )
    attempt = run_attempt(
        task,
        "ab1",
        benchmark="mbpp",
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        settings=settings,
        model_digest=freeze.MODEL_DIGEST,
        sample_index=int(cell["sample_index"]),
    )
    return attempt


def run_generate(
    *,
    repo_root: Path = REPO_ROOT,
    argv: Sequence[str],
    manifest_sha256: str,
    execute_model: bool,
    i_understand: bool,
    execution_acknowledgement: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    provenance_fn: ProvenanceFn | None = None,
    generate_fn: GenerateCellFn | None = None,
    max_cells: int | None = None,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    """Formal generate path with crash-safe per-cell journals."""
    _require(execute_model is True, "generate refused: missing --execute-model")
    _require(
        i_understand is True,
        "generate refused: missing --i-understand-this-calls-the-model",
    )
    _require(
        execution_acknowledgement == EXECUTION_ACKNOWLEDGEMENT,
        "generate refused: missing/incorrect --execution-acknowledgement",
    )
    expected_sha = resolve_manifest_sha256(repo_root)
    _require(
        manifest_sha256 == expected_sha,
        f"generate refused: manifest SHA mismatch: {manifest_sha256} != {expected_sha}",
    )

    assert_no_foreign_overwrite(repo_root)
    preflight_mod.zero_model_preflight(
        repo_root=repo_root,
        manifest_sha256=manifest_sha256,
        require_output_absent=False,
    )

    cells = load_frozen_cells(repo_root)
    assert_development_only_cells(cells)
    if max_cells is not None:
        _require(1 <= max_cells <= len(cells), "max_cells out of range")
        cells = cells[:max_cells]

    protocol_path = repo_root / freeze.PROTOCOL_RELATIVE
    protocol = load_generation_protocol(protocol_path)
    protocol_sha = freeze.EXPECTED_PROTOCOL_SHA256
    _require(
        _sha256_bytes(protocol_path.read_bytes()) == protocol_sha,
        "protocol SHA drift",
    )

    provenance_fn = provenance_fn or fetch_live_model_identity
    live_identity = provenance_fn(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        expected_tag=freeze.MODEL_TAG,
        expected_digest=freeze.MODEL_DIGEST,
    )
    _require(
        live_identity["model_digest"] == freeze.MODEL_DIGEST,
        "live digest gate failed",
    )
    _require(
        live_identity["model_tag"] == freeze.MODEL_TAG,
        "live tag gate failed",
    )

    out_dir = run_dir or resolve_run_dir(repo_root)
    if run_dir is None:
        _require(
            out_dir.resolve() == resolve_run_dir(repo_root).resolve(),
            "run_dir must equal frozen pilot output directory",
        )
    else:
        # Test harness may redirect writes; still forbid collision with 9B paths.
        assert_no_foreign_overwrite(repo_root)
        _require(
            out_dir.resolve() != (repo_root / freeze.OUTPUT_RELATIVE).resolve(),
            "test run_dir must not write into governance freeze dir",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "j").mkdir(parents=True, exist_ok=True)

    execution_manifest = build_execution_manifest(
        repo_root=repo_root,
        argv=argv,
        manifest_sha256=manifest_sha256,
        live_identity=live_identity,
        safety_flags={
            "execute_model": execute_model,
            "i_understand_this_calls_the_model": i_understand,
            "execution_acknowledgement": execution_acknowledgement,
            "manifest_sha256": manifest_sha256,
        },
    )
    exec_path = out_dir / "execution_manifest.json"
    if exec_path.exists():
        existing = json.loads(exec_path.read_text(encoding="utf-8"))
        _require(
            existing.get("frozen_manifest_sha256") == manifest_sha256,
            "execution_manifest frozen SHA mismatch; refuse to continue",
        )
        _require(
            existing.get("live_model_identity", {}).get("model_digest")
            == live_identity["model_digest"],
            "execution_manifest live digest mismatch; refuse to continue",
        )
    else:
        durable_write_json_new(exec_path, execution_manifest)

    provenance_path = out_dir / "live_model_provenance.json"
    if not provenance_path.exists():
        durable_write_json_new(provenance_path, dict(live_identity))

    official_prompts = load_official_prompts(repo_root)
    entry_points = load_entry_points(repo_root)
    scaffold_text = (repo_root / freeze.SCAFFOLD_RELATIVE).read_text(encoding="utf-8")

    def _default_generate(**kwargs: Any) -> dict[str, Any]:
        return live_generate_cell(protocol=protocol, **kwargs)

    cell_generate = generate_fn or _default_generate

    skipped = 0
    generated = 0
    retried = 0
    failed = 0
    for cell in cells:
        action = decide_resume_action(
            cell,
            out_dir,
            manifest_sha256=manifest_sha256,
            protocol_sha256=protocol_sha,
            repo_root=repo_root,
        )
        if action == "skip":
            skipped += 1
            continue
        if action == "retry_incomplete":
            quarantine_incomplete_journal(
                journal_path(out_dir, cell["generation_id"]), out_dir
            )
            retried += 1

        official = official_prompts[cell["task_id"]]
        composed = compose_prompt_for_cell(official, cell, scaffold_text)
        _require(
            _sha256_text(official) == cell["official_prompt_sha256"],
            "official prompt SHA drift",
        )
        _require(
            _sha256_text(composed) == cell["composed_prompt_sha256"],
            "composed prompt SHA drift",
        )

        started_at = _utc_now()
        try:
            attempt = cell_generate(
                cell=cell,
                composed_prompt=composed,
                entry_point=entry_points[cell["task_id"]],
                base_url=base_url,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            completed_at = _utc_now()
            error_journal = build_error_journal(
                cell=cell,
                manifest_sha256=manifest_sha256,
                protocol_sha256=protocol_sha,
                live_identity=live_identity,
                started_at=started_at,
                completed_at=completed_at,
                error_message=str(exc),
            )
            try:
                persist_journal(out_dir, cell, error_journal)
            except Exception:
                pass
            failed += 1
            raise PilotRunError(
                f"generation failed at cell {cell['cell_index']}/200 "
                f"({cell['task_id']} {cell['condition_id']} seed={cell['seed']}): {exc}"
            ) from exc

        completed_at = _utc_now()
        raw_response = attempt.get("raw_response") if isinstance(attempt, dict) else None
        transport = (
            attempt.get("ollama_response_metadata")
            if isinstance(attempt, dict)
            else None
        )
        status = attempt.get("status") if isinstance(attempt, dict) else None
        
        if isinstance(raw_response, str) and raw_response.strip():
            # Generation succeeded (non-empty raw response received)
            if status == "success":
                # Extraction succeeded
                journal = build_success_journal(
                    cell=cell,
                    raw_response=raw_response,
                    manifest_sha256=manifest_sha256,
                    protocol_sha256=protocol_sha,
                    live_identity=live_identity,
                    request_metadata=(
                        transport.get("request_payload")
                        if isinstance(transport, dict)
                        else attempt.get("request_metadata")
                    ),
                    response_metadata=(
                        transport
                        if isinstance(transport, dict)
                        else attempt.get("response_metadata")
                    ),
                    started_at=started_at,
                    completed_at=completed_at,
                    extracted_code=attempt.get("completion") or "",
                )
            else:
                # Extraction failed
                extr_status = attempt.get("extraction_status") or "error"
                journal = build_extraction_failed_journal(
                    cell=cell,
                    raw_response=raw_response,
                    manifest_sha256=manifest_sha256,
                    protocol_sha256=protocol_sha,
                    live_identity=live_identity,
                    request_metadata=(
                        transport.get("request_payload")
                        if isinstance(transport, dict)
                        else attempt.get("request_metadata")
                    ),
                    response_metadata=(
                        transport
                        if isinstance(transport, dict)
                        else attempt.get("response_metadata")
                    ),
                    started_at=started_at,
                    completed_at=completed_at,
                    extraction_status=extr_status,
                    error_message=str(attempt.get("failure_reason") or "extraction failed"),
                )
            try:
                persist_journal(out_dir, cell, journal)
            except Exception as exc:
                raise PilotRunError(f"durable persistence failed: {exc}") from exc
            generated += 1
        else:
            # Generation failed (empty raw response or transport failed)
            error_journal = build_error_journal(
                cell=cell,
                manifest_sha256=manifest_sha256,
                protocol_sha256=protocol_sha,
                live_identity=live_identity,
                started_at=started_at,
                completed_at=completed_at,
                error_message=str(
                    attempt.get("failure_reason")
                    if isinstance(attempt, dict)
                    else "invalid/empty attempt payload"
                ),
                request_metadata=(
                    transport.get("request_payload")
                    if isinstance(transport, dict)
                    else None
                ),
                response_metadata=transport if isinstance(transport, dict) else None,
                raw_response=raw_response if isinstance(raw_response, str) else None,
            )
            try:
                persist_journal(out_dir, cell, error_journal)
            except Exception:
                pass
            failed += 1
            raise PilotRunError(
                f"incomplete generation at cell {cell['cell_index']}/200; "
                "incomplete journal persisted with persisted_complete=false"
            )

    _require(failed == 0, "internal failed counter drift")
    return {
        "status": (
            "generate_completed"
            if skipped + generated == len(cells)
            else "generate_unexpected_count"
        ),
        "runner_status": RUNNER_STATUS,
        "run_id": freeze.RUN_ID,
        "output_directory": out_dir.as_posix(),
        "cells_considered": len(cells),
        "skipped_complete": skipped,
        "generated_now": generated,
        "retried_incomplete": retried,
        "failed": failed,
        "model_tag": freeze.MODEL_TAG,
        "model_digest": freeze.MODEL_DIGEST,
        "runtime_version": live_identity.get("runtime_version"),
        "healer_modified": False,
        "evaluation_executed": False,
        "candidate_code_executed": False,
        "stopped_after_plan_cells": True,
        "auto_expand_to_60": False,
        "frozen_plan_cell_count": freeze.EXPECTED_CELL_COUNT,
    }


def cmd_plan(args: argparse.Namespace) -> dict[str, Any]:
    assert_no_foreign_overwrite(REPO_ROOT)
    cells = load_frozen_cells()
    assert_development_only_cells(cells)
    manifest_sha = resolve_manifest_sha256()
    return {
        "status": "plan_inspect_ok",
        "runner_status": RUNNER_STATUS,
        "run_id": freeze.RUN_ID,
        "manifest_sha256": manifest_sha,
        "output_directory": freeze.RUN_OUTPUT_RELATIVE.as_posix(),
        "cell_count": len(cells),
        "task_count": len({row["task_id"] for row in cells}),
        "seeds": list(freeze.SEEDS),
        "conditions": ["Ab1_H0", "Ab2g_H1"],
        "model_tag": freeze.MODEL_TAG,
        "model_digest": freeze.MODEL_DIGEST,
        "model_calls": 0,
        "writes": 0,
        "first_cell": {
            "task_id": cells[0]["task_id"],
            "seed": cells[0]["seed"],
            "condition_id": cells[0]["condition_id"],
            "generation_id": cells[0]["generation_id"],
        },
        "last_cell": {
            "task_id": cells[-1]["task_id"],
            "seed": cells[-1]["seed"],
            "condition_id": cells[-1]["condition_id"],
            "generation_id": cells[-1]["generation_id"],
        },
    }


def cmd_preflight(args: argparse.Namespace) -> dict[str, Any]:
    assert_no_foreign_overwrite(REPO_ROOT)
    return preflight_mod.zero_model_preflight(
        repo_root=REPO_ROOT,
        manifest_sha256=args.manifest_sha256 or resolve_manifest_sha256(),
        require_output_absent=not args.allow_existing_output,
    )


def cmd_generate(args: argparse.Namespace) -> dict[str, Any]:
    return run_generate(
        repo_root=REPO_ROOT,
        argv=["generate", *([a for a in sys.argv[2:] if a])],
        manifest_sha256=args.manifest_sha256 or "",
        execute_model=bool(args.execute_model),
        i_understand=bool(args.i_understand_this_calls_the_model),
        execution_acknowledgement=args.execution_acknowledgement or "",
        base_url=args.base_url,
        timeout_seconds=float(args.timeout_seconds),
        max_cells=args.max_cells,
    )


def cmd_resume_check(args: argparse.Namespace) -> dict[str, Any]:
    cells = load_frozen_cells()
    run_dir = Path(args.run_dir) if args.run_dir else resolve_run_dir()
    manifest_sha = resolve_manifest_sha256()
    decisions: list[dict[str, str]] = []
    for cell in cells:
        try:
            action = decide_resume_action(
                cell,
                run_dir,
                manifest_sha256=manifest_sha,
                protocol_sha256=freeze.EXPECTED_PROTOCOL_SHA256,
            )
            decisions.append(
                {
                    "generation_id": cell["generation_id"],
                    "action": action,
                    "status": "ok",
                }
            )
        except PilotRunError as exc:
            decisions.append(
                {
                    "generation_id": cell["generation_id"],
                    "action": "fail_closed",
                    "status": str(exc),
                }
            )
    failures = [row for row in decisions if row["action"] == "fail_closed"]
    if failures:
        raise PilotRunError(
            f"resume mismatch fail-closed on {len(failures)} cells; "
            f"first={failures[0]['status']}"
        )
    return {
        "status": "resume_check_passed",
        "cell_count": len(decisions),
        "skip_count": sum(row["action"] == "skip" for row in decisions),
        "generate_count": sum(row["action"] == "generate" for row in decisions),
        "retry_incomplete_count": sum(
            row["action"] == "retry_incomplete" for row in decisions
        ),
        "model_calls": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Inspect frozen 200-cell plan (zero model)")
    plan.set_defaults(func=cmd_plan)
    inspect = sub.add_parser("inspect", help="Alias of plan")
    inspect.set_defaults(func=cmd_plan)

    pre = sub.add_parser("preflight", help="Zero-model preflight")
    pre.add_argument("--manifest-sha256", default=None)
    pre.add_argument("--allow-existing-output", action="store_true")
    pre.set_defaults(func=cmd_preflight)

    gen = sub.add_parser(
        "generate",
        help="Formal crash-safe generation (requires dual confirmation + manifest SHA)",
    )
    gen.add_argument("--manifest-sha256", required=True)
    gen.add_argument("--i-understand-this-calls-the-model", action="store_true")
    gen.add_argument("--execute-model", action="store_true")
    gen.add_argument(
        "--execution-acknowledgement",
        default="",
        help=f"Must equal {EXECUTION_ACKNOWLEDGEMENT!r}",
    )
    gen.add_argument("--base-url", default=DEFAULT_BASE_URL)
    gen.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    gen.add_argument(
        "--max-cells",
        type=int,
        default=None,
        help=argparse.SUPPRESS,  # test-only; hidden from operators
    )
    gen.set_defaults(func=cmd_generate)

    resume = sub.add_parser("resume-check", help="Offline resume identity check")
    resume.add_argument("--run-dir", default=None)
    resume.set_defaults(func=cmd_resume_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
