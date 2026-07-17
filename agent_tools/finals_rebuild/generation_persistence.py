"""Durable, fail-visible persistence for generation artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


class PersistenceError(RuntimeError):
    """Raised when an artifact cannot be durably written and verified."""


@dataclass(frozen=True)
class PersistenceReceipt:
    path: str
    sha256: str
    size_bytes: int
    record_count: int


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write_new_bytes(
    path: pathlib.Path, data: bytes, *, record_count: int
) -> PersistenceReceipt:
    """Write a new file through a same-directory temp file and verify it.

    The temp handle is flushed, fsynced, and closed before publication.
    Existing targets are never removed or replaced.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise PersistenceError(f"refusing to overwrite existing artifact: {path}")

    temp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".tmp-",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_path = pathlib.Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        if path.exists():
            raise PersistenceError(f"target appeared before atomic publish: {path}")
        os.rename(temp_path, path)
        temp_path = None
    except PermissionError as exc:
        raise PersistenceError(f"permission denied while persisting {path}: {exc}") from exc
    except OSError as exc:
        raise PersistenceError(f"OS error while persisting {path}: {exc}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    try:
        persisted = path.read_bytes()
    except PermissionError as exc:
        raise PersistenceError(f"permission denied during read-back of {path}: {exc}") from exc
    if persisted != data:
        raise PersistenceError(f"read-back byte mismatch after persisting {path}")
    expected_hash = sha256_bytes(data)
    actual_hash = sha256_bytes(persisted)
    if actual_hash != expected_hash:
        raise PersistenceError(f"read-back SHA-256 mismatch after persisting {path}")
    return PersistenceReceipt(
        path=str(path),
        sha256=actual_hash,
        size_bytes=len(persisted),
        record_count=record_count,
    )


def durable_write_json_new(path: pathlib.Path, value: Dict[str, Any]) -> PersistenceReceipt:
    data = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    receipt = _atomic_write_new_bytes(path, data, record_count=1)
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if parsed != value:
        raise PersistenceError(f"JSON read-back mismatch after persisting {path}")
    return receipt


def durable_write_jsonl_new(
    path: pathlib.Path, records: Iterable[Dict[str, Any]]
) -> PersistenceReceipt:
    materialized: List[Dict[str, Any]] = list(records)
    data = "".join(
        json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        for record in materialized
    ).encode("utf-8")
    receipt = _atomic_write_new_bytes(path, data, record_count=len(materialized))
    parsed = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if parsed != materialized:
        raise PersistenceError(f"JSONL read-back mismatch after persisting {path}")
    return receipt


def durable_write_text_new(path: pathlib.Path, value: str) -> PersistenceReceipt:
    return _atomic_write_new_bytes(path, value.encode("utf-8"), record_count=1)
