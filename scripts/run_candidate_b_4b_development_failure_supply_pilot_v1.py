#!/usr/bin/env python3
"""Controlled entry for the 4B development-only failure-supply pilot.

Default commands are zero-model. The generate path exists for a future
explicit execution round, but this packaging round must not call it.

Safety:
- never modifies Healer
- never overwrites foreign 9B / scaffold artifacts
- resume skip only when cell identity, model fingerprint, prompt SHA,
  condition, seed, and completion flag all match; otherwise fail closed
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import freeze_candidate_b_4b_development_failure_supply_pilot_v1 as freeze  # noqa: E402
from scripts import (  # noqa: E402
    preflight_candidate_b_4b_development_failure_supply_pilot_v1 as preflight,
)

# Pinned after first successful freeze write; tests recompute via freeze.build_outputs.
FROZEN_MANIFEST_SHA256: str | None = None


class PilotRunError(RuntimeError):
    """Fail-closed runner violation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotRunError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def load_frozen_cells(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    return _read_csv(repo_root / freeze.OUTPUT_RELATIVE / "generation_cells.csv")


def journal_path(run_dir: Path, generation_id: str) -> Path:
    return run_dir / "j" / f"{generation_id}.json"


def load_journal(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resume_identity_matches(
    cell: dict[str, str],
    journal: dict[str, Any],
) -> tuple[bool, str]:
    checks = {
        "cell_identity": (cell["cell_identity"], journal.get("cell_identity")),
        "model_tag": (cell["model_tag"], journal.get("model_tag")),
        "model_digest": (cell["model_digest"], journal.get("model_digest")),
        "composed_prompt_sha256": (
            cell["composed_prompt_sha256"],
            journal.get("composed_prompt_sha256"),
        ),
        "condition_id": (cell["condition_id"], journal.get("condition_id")),
        "seed": (int(cell["seed"]), int(journal.get("seed", -1))),
        "completion_flag": ("success", journal.get("completion_flag")),
    }
    for name, (expected, actual) in checks.items():
        if expected != actual:
            return False, f"resume identity mismatch on {name}: {actual!r} != {expected!r}"
    if journal.get("generation_status") != "success":
        return False, "resume requires generation_status=success"
    if not isinstance(journal.get("raw_response"), str) or not journal["raw_response"].strip():
        return False, "resume requires non-empty raw_response"
    return True, "ok"


def decide_resume_action(
    cell: dict[str, str],
    run_dir: Path,
) -> str:
    """Return 'skip' or 'generate'. Raise on identity mismatch."""
    path = journal_path(run_dir, cell["generation_id"])
    journal = load_journal(path)
    if journal is None:
        return "generate"
    ok, message = resume_identity_matches(cell, journal)
    if not ok:
        raise PilotRunError(message)
    return "skip"


def assert_no_foreign_overwrite(repo_root: Path) -> None:
    for relative in (
        freeze.NINE_B_RUN_RELATIVE,
        freeze.NINE_B_AB1_RUN_RELATIVE,
        freeze.NINE_B_SCAFFOLD_RUN_RELATIVE,
    ):
        path = repo_root / relative
        _require(
            path.resolve() != (repo_root / freeze.RUN_OUTPUT_RELATIVE).resolve(),
            f"refusing pilot path collision with {relative.as_posix()}",
        )


def cmd_preflight(args: argparse.Namespace) -> dict[str, Any]:
    assert_no_foreign_overwrite(REPO_ROOT)
    receipt = preflight.zero_model_preflight(
        repo_root=REPO_ROOT,
        manifest_sha256=args.manifest_sha256 or resolve_manifest_sha256(),
        require_output_absent=not args.allow_existing_output,
    )
    return receipt


def cmd_generate(args: argparse.Namespace) -> dict[str, Any]:
    """Controlled generate entry.

    This packaging round must not invoke model generation. The command remains
    fail-closed unless --i-understand-this-calls-the-model is supplied, and even
    then it still refuses unless the operator also passes --execute-model.
    """
    assert_no_foreign_overwrite(REPO_ROOT)
    preflight.zero_model_preflight(
        repo_root=REPO_ROOT,
        manifest_sha256=args.manifest_sha256 or resolve_manifest_sha256(),
        require_output_absent=False,
    )
    _require(
        args.i_understand_this_calls_the_model and args.execute_model,
        "generate refused: this packaging round keeps model execution gated; "
        "pass both --i-understand-this-calls-the-model and --execute-model "
        "only in a future explicit execution round",
    )
    # Future execution round would call Ollama here. Still refuse for now so a
    # partially implemented generate path cannot silently produce results.
    raise PilotRunError(
        "generate path is preregistered but not enabled in this packaging commit; "
        "no model calls performed"
    )


def cmd_resume_check(args: argparse.Namespace) -> dict[str, Any]:
    """Offline resume matrix check against optional journal directory."""
    cells = load_frozen_cells()
    run_dir = Path(args.run_dir) if args.run_dir else (REPO_ROOT / freeze.RUN_OUTPUT_RELATIVE)
    decisions: list[dict[str, str]] = []
    for cell in cells:
        try:
            action = decide_resume_action(cell, run_dir)
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
        "model_calls": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Zero-model preflight")
    pre.add_argument("--manifest-sha256", default=None)
    pre.add_argument("--allow-existing-output", action="store_true")
    pre.set_defaults(func=cmd_preflight)

    gen = sub.add_parser("generate", help="Gated model generation entry (disabled this round)")
    gen.add_argument("--manifest-sha256", default=None)
    gen.add_argument("--i-understand-this-calls-the-model", action="store_true")
    gen.add_argument("--execute-model", action="store_true")
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
