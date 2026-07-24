#!/usr/bin/env python3
"""Zero-model migration and repair tool for cell 5 of 4B failure-supply pilot.

Default mode is inspect-only. True migration requires --confirm and matching external SHA gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Safety expectations for Cell 5
EXPECTED_CELL_INDEX = 5
EXPECTED_TASK_ID = "Mbpp/633"
EXPECTED_CONDITION_ID = "Ab1_H0"
EXPECTED_SEED = 33
EXPECTED_RAW_LENGTH = 5096

MIGRATION_TOOL_VERSION = "1.0.0"
MIGRATION_SCHEMA_VERSION = "4B_STATE_DECOUPLE_V1"

# Target paths
RUN_DIR_RELATIVE = Path("artifacts/public_benchmark_development/mbpp_qwen35_4b_failure_supply_pilot/runs/mbpp_q35_4b_dev20_failure_supply_pilot_r001")
JOURNAL_FILENAME = "ddf887bc974d8f55f970ad35dfb5a9649507a1a875ceb989e45e088c47be68f5.json"
QUARANTINE_DIR_RELATIVE = Path("artifacts/fail_to_fail_forensics/quarantine")
GOVERNANCE_RECEIPT_RELATIVE = Path("artifacts/fail_to_fail_forensics/receipt_cell5_repair.json")


def make_long_path(path: Path) -> str:
    abs_path = str(path.resolve())
    if os.name == "nt" and not abs_path.startswith("\\\\?\\\\"):
        return "\\\\?\\\\" + abs_path
    return abs_path


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_text(s: str) -> str:
    return _sha256_bytes(s.encode("utf-8"))


def get_git_head() -> str:
    import subprocess
    real_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=real_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def run_migration(
    confirm: bool,
    expected_before_journal_sha: str,
    expected_raw_response_sha: str,
) -> int:
    journal_path = REPO_ROOT / RUN_DIR_RELATIVE / "j" / JOURNAL_FILENAME
    long_journal_path = make_long_path(journal_path)
    
    if not os.path.isfile(long_journal_path):
        print(f"Error: Journal file not found at {journal_path}")
        return 1

    # 1. Read and hash original journal bytes
    before_bytes = open(long_journal_path, "rb").read()
    before_sha = _sha256_bytes(before_bytes)
    
    # 2. Parse journal JSON
    try:
        journal_data = json.loads(before_bytes.decode("utf-8"))
    except Exception as exc:
        print(f"Error: Failed to parse journal JSON: {exc}")
        return 1

    # Check if already migrated
    if journal_data.get("generation_completed") is True and journal_data.get("persisted_complete") is True:
        print("Journal is already migrated.")
        # Perform idempotency checks
        raw_resp = journal_data.get("raw_response", "")
        raw_sha = _sha256_text(raw_resp)
        if len(raw_resp) != EXPECTED_RAW_LENGTH:
            print("Error: Already migrated journal has unexpected raw response length.")
            return 1
        if raw_sha != expected_raw_response_sha:
            print("Error: Already migrated journal has unexpected raw response SHA.")
            return 1
        print("Idempotency checks passed. Nothing to do.")
        return 0

    # 3. Security gates validation
    if journal_data.get("cell_index") != EXPECTED_CELL_INDEX:
        print(f"Error: cell_index {journal_data.get('cell_index')} != {EXPECTED_CELL_INDEX}")
        return 1
    if journal_data.get("task_id") != EXPECTED_TASK_ID:
        print(f"Error: task_id {journal_data.get('task_id')} != {EXPECTED_TASK_ID}")
        return 1
    if journal_data.get("condition_id") != EXPECTED_CONDITION_ID:
        print(f"Error: condition_id {journal_data.get('condition_id')} != {EXPECTED_CONDITION_ID}")
        return 1
    if journal_data.get("seed") != EXPECTED_SEED:
        print(f"Error: seed {journal_data.get('seed')} != {EXPECTED_SEED}")
        return 1

    raw_response = journal_data.get("raw_response", "")
    raw_length = len(raw_response)
    raw_sha = _sha256_text(raw_response)

    if raw_length != EXPECTED_RAW_LENGTH:
        print(f"Error: Raw response length {raw_length} != {EXPECTED_RAW_LENGTH}")
        return 1

    # Validate against CLI gates
    if before_sha.lower() != expected_before_journal_sha.lower():
        print(f"Error: Before journal SHA gate mismatch.\nExpected: {expected_before_journal_sha}\nActual:   {before_sha}")
        return 1
    if raw_sha.lower() != expected_raw_response_sha.lower():
        print(f"Error: Raw response SHA gate mismatch.\nExpected: {expected_raw_response_sha}\nActual:   {raw_sha}")
        return 1

    # Build the updated journal data
    updated_journal = dict(journal_data)
    updated_journal["persisted_complete"] = True
    updated_journal["generation_status"] = "success"
    updated_journal["error_status"] = "extraction_failed"
    
    # New status model fields
    updated_journal["generation_completed"] = True
    updated_journal["raw_response_persisted"] = True
    updated_journal["extraction_succeeded"] = False
    updated_journal["extraction_status"] = "ambiguous"
    updated_journal["extracted_code"] = None
    updated_journal["postprocess_status"] = "ambiguous"
    updated_journal["error_stage"] = "extraction"

    # Serialize with sort_keys=True and indent=2 to match conventions
    after_text = json.dumps(updated_journal, indent=2, sort_keys=True) + "\n"
    after_bytes = after_text.encode("utf-8")
    after_sha = _sha256_bytes(after_bytes)

    print("=== INSPECT MIGRATION PLAN ===")
    print(f"Cell Index: {EXPECTED_CELL_INDEX} ({EXPECTED_TASK_ID}, {EXPECTED_CONDITION_ID}, seed={EXPECTED_SEED})")
    print(f"Journal File: {journal_path}")
    print(f"Before Journal SHA-256: {before_sha}")
    print(f"After Journal SHA-256:  {after_sha}")
    print(f"Raw Response Length:    {raw_length} chars")
    print(f"Raw Response SHA-256:   {raw_sha}")
    print("New schema fields to be applied:")
    print("  generation_completed   -> True")
    print("  raw_response_persisted -> True")
    print("  extraction_succeeded   -> False")
    print("  extraction_status      -> 'ambiguous'")
    print("  extracted_code         -> null")
    print("  postprocess_status     -> 'ambiguous'")
    print("  error_stage            -> 'extraction'")
    print("==============================")

    if not confirm:
        print("Inspect-only mode. Run with --confirm to apply changes.")
        return 0

    print("Executing migration...")

    # a. Save byte-identical backup
    quarantine_dir = REPO_ROOT / QUARANTINE_DIR_RELATIVE
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    backup_path = quarantine_dir / JOURNAL_FILENAME
    long_backup_path = make_long_path(backup_path)
    
    # Do not overwrite if backup already exists and matches before_sha
    if os.path.isfile(long_backup_path):
        backup_sha = _sha256_bytes(open(long_backup_path, "rb").read())
        if backup_sha != before_sha:
            print(f"Error: Backup file exists at {backup_path} but has different SHA-256 ({backup_sha})!")
            return 1
        print("Backup file already exists and is identical.")
    else:
        open(long_backup_path, "wb").write(before_bytes)
        print(f"Saved original backup to: {backup_path}")

    # b. Verify backup SHA equals original journal SHA
    backup_sha = _sha256_bytes(open(long_backup_path, "rb").read())
    if backup_sha != before_sha:
        print("Error: Backup SHA mismatch after write!")
        return 1

    # c. Write new journal to temp file in same directory
    temp_path = journal_path.parent / f"{journal_path.name}.tmp"
    long_temp_path = make_long_path(temp_path)
    with open(long_temp_path, "wb") as f:
        f.write(after_bytes)
        f.flush()
        # d. fsync
        try:
            os.fsync(f.fileno())
        except OSError as exc:
            print(f"Warning: fsync failed (might not be supported on this mount): {exc}")

    # e. Atomic replace
    os.replace(long_temp_path, long_journal_path)
    print(f"Updated journal atomic replaced at: {journal_path}")

    # f. Write receipt
    receipt = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "migration_tool_version": MIGRATION_TOOL_VERSION,
        "before_journal_sha256": before_sha,
        "after_journal_sha256": after_sha,
        "raw_response_before_sha256": raw_sha,
        "raw_response_after_sha256": raw_sha,
        "raw_response_length": raw_length,
        "migration_time": os.popen("python -c \"from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())\"").read().strip(),
        "git_head": get_git_head(),
        "manifest_sha256": journal_data.get("manifest_sha256"),
        "original_backup_path": backup_path.relative_to(REPO_ROOT).as_posix(),
        "declaration": "No model APIs were called, raw_response was not modified, and no code execution/evaluation was run.",
    }
    
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    
    # Save receipt to run dir
    run_receipt_path = journal_path.parent.parent / "receipt_cell5_repair.json"
    open(make_long_path(run_receipt_path), "wb").write(receipt_bytes)
    print(f"Saved run receipt to: {run_receipt_path}")

    # Save receipt to governance path (tracked in git)
    gov_receipt_path = REPO_ROOT / GOVERNANCE_RECEIPT_RELATIVE
    open(make_long_path(gov_receipt_path), "wb").write(receipt_bytes)
    print(f"Saved governance receipt to: {gov_receipt_path}")

    # g. Re-verify everything
    final_journal_bytes = open(long_journal_path, "rb").read()
    final_journal_sha = _sha256_bytes(final_journal_bytes)
    final_journal_data = json.loads(final_journal_bytes.decode("utf-8"))
    final_raw = final_journal_data.get("raw_response", "")
    final_raw_sha = _sha256_text(final_raw)

    if final_journal_sha != after_sha:
        print("Error: Final journal SHA does not match expected after-SHA!")
        return 1
    if len(final_raw) != EXPECTED_RAW_LENGTH:
        print("Error: Final raw response length changed!")
        return 1
    if final_raw_sha != raw_sha:
        print("Error: Final raw response SHA changed!")
        return 1

    print("Migration successful! Verification checks passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true", help="Apply changes (default is inspect-only)")
    parser.add_argument("--expected-before-journal-sha256", required=True, help="Expected SHA of journal before change")
    parser.add_argument("--expected-raw-response-sha256", required=True, help="Expected SHA of raw response text")
    args = parser.parse_args()
    
    return run_migration(
        confirm=args.confirm,
        expected_before_journal_sha=args.expected_before_journal_sha256,
        expected_raw_response_sha=args.expected_raw_response_sha256,
    )


if __name__ == "__main__":
    sys.exit(main())
