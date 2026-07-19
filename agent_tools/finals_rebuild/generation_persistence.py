"""Durable, fail-visible persistence for generation artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import secrets
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


def _absolute_path(path: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(os.path.abspath(os.fspath(path)))


def _os_fs_path(path: pathlib.Path) -> str:
    """Return an OS path usable beyond Windows MAX_PATH when needed."""
    absolute = os.path.abspath(os.fspath(path))
    if os.name != "nt":
        return absolute
    if absolute.startswith("\\\\?\\"):
        return absolute
    if absolute.startswith("\\\\"):
        return "\\\\?\\UNC\\" + absolute[2:]
    return "\\\\?\\" + absolute


def _path_exists(path: pathlib.Path) -> bool:
    return os.path.exists(_os_fs_path(path))


def _unlink_path(path: pathlib.Path) -> None:
    os.unlink(_os_fs_path(path))


def _read_bytes(path: pathlib.Path) -> bytes:
    with open(_os_fs_path(path), "rb") as handle:
        return handle.read()


def _fsync_directory(directory: pathlib.Path) -> None:
    """Best-effort parent-directory durability; never fail on Windows limits."""
    try:
        fd = os.open(_os_fs_path(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        try:
            os.fsync(fd)
        except OSError:
            return
    finally:
        os.close(fd)


def _atomic_write_new_bytes(
    path: pathlib.Path, data: bytes, *, record_count: int
) -> PersistenceReceipt:
    """Write a new file through a same-directory temp file and verify it.

    Temporary and target paths share one directory. The temp file is created
    exclusively, written, flushed, fsynced, and fully closed before publish.
    Existing targets are never removed or replaced. On Windows, extended-length
    paths are used so journal names near MAX_PATH remain publishable.
    """
    path = _absolute_path(pathlib.Path(path))
    parent = path.parent
    os.makedirs(_os_fs_path(parent), exist_ok=True)
    if _path_exists(path):
        raise PersistenceError(f"refusing to overwrite existing artifact: {path}")

    temp_path: pathlib.Path | None = None
    fd: int | None = None
    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        for _ in range(64):
            candidate = parent / f".tmp-{secrets.token_hex(8)}.tmp"
            try:
                fd = os.open(_os_fs_path(candidate), flags, 0o644)
            except FileExistsError:
                continue
            temp_path = candidate
            break
        if fd is None or temp_path is None:
            raise PersistenceError(f"exclusive temporary file create failed under {parent}")

        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        if not _path_exists(temp_path):
            raise PersistenceError(
                f"temporary file disappeared before publish: {temp_path}"
            )
        if _path_exists(path):
            raise PersistenceError(f"target appeared before atomic publish: {path}")
        os.rename(_os_fs_path(temp_path), _os_fs_path(path))
        temp_path = None
        _fsync_directory(parent)
    except PermissionError as exc:
        raise PersistenceError(f"permission denied while persisting {path}: {exc}") from exc
    except OSError as exc:
        raise PersistenceError(f"OS error while persisting {path}: {exc}") from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if temp_path is not None and _path_exists(temp_path):
            try:
                _unlink_path(temp_path)
            except OSError:
                pass

    try:
        persisted = _read_bytes(path)
    except PermissionError as exc:
        raise PersistenceError(f"permission denied during read-back of {path}: {exc}") from exc
    except OSError as exc:
        raise PersistenceError(f"OS error during read-back of {path}: {exc}") from exc
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
    parsed = json.loads(_read_bytes(path).decode("utf-8"))
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
        for line in _read_bytes(path).decode("utf-8").splitlines()
        if line
    ]
    if parsed != materialized:
        raise PersistenceError(f"JSONL read-back mismatch after persisting {path}")
    return receipt


def durable_write_text_new(path: pathlib.Path, value: str) -> PersistenceReceipt:
    return _atomic_write_new_bytes(path, value.encode("utf-8"), record_count=1)
