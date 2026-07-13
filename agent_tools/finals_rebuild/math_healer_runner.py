"""Offline, deterministic Ab2g-to-Ab3 source derivation."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Sequence

from core.healers.unified_cleanup_healer import UnifiedCleanupHealer
from core.validators.code_validator import validate_python_code


class MathHealerDerivationError(ValueError):
    pass


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _parse_status(source: str) -> tuple[bool, str | None]:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def _validation(source: str) -> dict[str, Any]:
    valid, message = validate_python_code(source)
    parsed, parse_error = _parse_status(source)
    has_generate = False
    if parsed:
        has_generate = any(
            isinstance(node, ast.FunctionDef) and node.name == "generate"
            for node in ast.parse(source).body
        )
    return {
        "code_validator_success": valid,
        "code_validator_message": message,
        "required_entry_point_present": has_generate,
        "ast_parse_success": parsed,
        "parse_error": parse_error,
    }


def _write_json(path: Path, value: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _unified_trace(healer: Any) -> list[dict[str, Any]]:
    """Expose only the existing UnifiedCleanupHealer action counters."""
    component = "core.healers.unified_cleanup_healer.UnifiedCleanupHealer"
    definitions = (
        ("unified_cleanup_duplicate_definition", "duplicate_definition", "duplicate class/function definition"),
        ("unified_cleanup_shadowed_predefined_name", "shadowed_predefined_name", "assignment shadows a predefined name"),
        ("unified_cleanup_variable_reorder", "variable_reorder", "existing variable-order issue"),
    )
    counters = ("duplicate_count", "shadowing_count", "variable_order_count")
    trace = []
    for (rule_id, change_type, pattern), counter in zip(definitions, counters):
        if getattr(healer, counter, 0) > 0:
            trace.append(
                {
                    "rule_id": rule_id,
                    "healer_component": component,
                    "change_type": change_type,
                    "before_location_or_pattern": pattern,
                    "after_location_or_pattern": "existing structure removed or normalized",
                    "applied": True,
                    "reason": f"existing UnifiedCleanupHealer {counter} > 0",
                }
            )
    return trace


def derive_ab3(
    *,
    source: str | Path,
    output_dir: str | Path,
    run_id: str,
    paired_run_id: str,
    task_id: str,
    model: str,
    condition: str,
    healer_factory: Callable[[], Any] = UnifiedCleanupHealer,
) -> dict[str, Any]:
    """Derive one Ab3 source using only the existing deterministic Core Healer."""
    if condition != "Ab3":
        raise MathHealerDerivationError("derived condition must be Ab3")
    root = Path(output_dir)
    if root.exists():
        raise MathHealerDerivationError("output directory already exists")
    root.mkdir(parents=True)
    started = time.process_time()
    record: dict[str, Any] = {
        "run_id": run_id,
        "paired_run_id": paired_run_id,
        "task_id": task_id,
        "model_tag": model,
        "source_condition": "Ab2g",
        "derived_condition": "Ab3",
        "model_regenerated": False,
        "before_sha256": None,
        "after_sha256": None,
        "source_changed": False,
        "repair_count": 0,
        "applied_rules": [],
        "rejected_rules": [],
        "healer_error": None,
        "before_ast_parse_success": False,
        "after_ast_parse_success": False,
        "before_validation": None,
        "after_validation": None,
        "repair_cpu_seconds": 0.0,
        "source_commit": _source_commit(),
        "status": "failed",
    }
    trace: list[dict[str, Any]] = []
    try:
        before = Path(source).read_text(encoding="utf-8")
        if not before:
            raise MathHealerDerivationError("source is empty")
        (root / "ab2g_source.py").write_text(before, encoding="utf-8")
        record["before_sha256"] = _sha256(before)
        record["before_validation"] = _validation(before)
        record["before_ast_parse_success"] = record["before_validation"]["ast_parse_success"]

        healer = healer_factory()
        after, repair_count = healer.heal(before)
        if not isinstance(after, str):
            raise MathHealerDerivationError("existing healer returned non-string source")
        record["repair_count"] = int(repair_count)
        record["source_changed"] = after != before
        record["after_sha256"] = _sha256(after)
        record["after_validation"] = _validation(after)
        record["after_ast_parse_success"] = record["after_validation"]["ast_parse_success"]

        if record["source_changed"]:
            trace = _unified_trace(healer)
            if not trace:
                trace = [{
                    "rule_id": "unified_cleanup_unclassified_action",
                    "healer_component": "core.healers.unified_cleanup_healer.UnifiedCleanupHealer",
                    "change_type": "deterministic_structural_cleanup",
                    "before_location_or_pattern": "existing UnifiedCleanupHealer action",
                    "after_location_or_pattern": "existing structure removed or normalized",
                    "applied": True,
                    "reason": "existing healer changed source without an exposed action counter",
                }]
            record["applied_rules"] = [rule["rule_id"] for rule in trace]
            record["status"] = "derived"
        else:
            record["status"] = "no_op"
        (root / "ab3_source.py").write_text(after, encoding="utf-8")
    except Exception as exc:
        record["healer_error"] = {"exception_type": type(exc).__name__, "message": str(exc)}
        trace.append(
            {
                "rule_id": None,
                "healer_component": "core.healers.unified_cleanup_healer.UnifiedCleanupHealer",
                "change_type": "derivation_failure",
                "before_location_or_pattern": None,
                "after_location_or_pattern": None,
                "applied": False,
                "reason": str(exc),
            }
        )
    finally:
        record["repair_cpu_seconds"] = time.process_time() - started
        _write_json(root / "repair_trace.json", trace)
        _write_json(root / "derivation_record.json", record)
    return record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    derive = subparsers.add_parser("derive", help="derive offline Ab3 from one Ab2g source")
    derive.add_argument("--source", required=True)
    derive.add_argument("--output-dir", required=True)
    derive.add_argument("--run-id", required=True)
    derive.add_argument("--paired-run-id", required=True)
    derive.add_argument("--task-id", required=True)
    derive.add_argument("--model", required=True)
    derive.add_argument("--condition", required=True, choices=("Ab3",))
    args = parser.parse_args(argv)
    derive_ab3(
        source=args.source,
        output_dir=args.output_dir,
        run_id=args.run_id,
        paired_run_id=args.paired_run_id,
        task_id=args.task_id,
        model=args.model,
        condition=args.condition,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
