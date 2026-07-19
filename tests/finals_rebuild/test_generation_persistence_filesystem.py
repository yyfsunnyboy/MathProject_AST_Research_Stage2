"""Real-filesystem tests for durable generation journal persistence.

These tests intentionally avoid the formal Candidate B r001/r002/r003 run
directories and exercise temporary directories only.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile

import pytest

from agent_tools.finals_rebuild import generation_persistence as persistence


def _journal_payload(index: int) -> dict[str, object]:
    return {
        "cell_index": index,
        "generation_id": f"{index:064x}",
        "status": "complete_single_attempt",
        "raw_response": f"def cell_{index}():\n    return {index}\n",
    }


def test_single_json_journal_publishes_after_handle_close(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "j" / "single.json"
    rename_saw_closed = {"ok": False}
    original_rename = persistence.os.rename

    def rename_spy(source: str, target: str) -> None:
        # Temp must still exist as a closed readable file at publish time.
        with open(source, "rb") as handle:
            handle.read(1)
        rename_saw_closed["ok"] = True
        return original_rename(source, target)

    monkeypatch.setattr(persistence.os, "rename", rename_spy)
    receipt = persistence.durable_write_json_new(path, _journal_payload(1))
    assert rename_saw_closed["ok"] is True
    assert path.is_file()
    assert receipt.sha256 == persistence.sha256_bytes(path.read_bytes())
    assert json.loads(path.read_text(encoding="utf-8")) == _journal_payload(1)
    assert list(path.parent.glob(".tmp-*.tmp")) == []


def test_temp_and_target_share_directory(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "same_dir" / "cell.json"
    observed: dict[str, str] = {}
    original_open = os.open
    original_rename = persistence.os.rename

    def spy_open(name: str, flags: int, mode: int = 0o777, *args: object, **kwargs: object):
        if ".tmp-" in name and name.endswith(".tmp"):
            observed["temp"] = name
        return original_open(name, flags, mode, *args, **kwargs)

    def spy_rename(source: str, target: str) -> None:
        observed["source"] = source
        observed["target"] = target
        return original_rename(source, target)

    monkeypatch.setattr(persistence.os, "open", spy_open)
    monkeypatch.setattr(persistence.os, "rename", spy_rename)
    persistence.durable_write_json_new(path, {"ok": True})
    assert "temp" in observed and "source" in observed and "target" in observed
    temp_parent = pathlib.Path(observed["source"].removeprefix("\\\\?\\")).parent
    target_parent = pathlib.Path(observed["target"].removeprefix("\\\\?\\")).parent
    assert temp_parent == target_parent == path.parent.resolve()


def test_target_exists_fails_closed_without_overwrite(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "j" / "exists.json"
    first = {"v": 1}
    persistence.durable_write_json_new(path, first)
    digest = persistence.sha256_bytes(path.read_bytes())
    with pytest.raises(persistence.PersistenceError, match="refusing to overwrite"):
        persistence.durable_write_json_new(path, {"v": 2})
    assert persistence.sha256_bytes(path.read_bytes()) == digest
    assert json.loads(path.read_text(encoding="utf-8")) == first


def test_temp_missing_before_publish_fails_closed(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "j" / "missing_temp.json"
    original_exists = persistence._path_exists
    calls = {"n": 0}

    def exists_spy(candidate: pathlib.Path) -> bool:
        result = original_exists(candidate)
        if candidate.name.startswith(".tmp-") and candidate.name.endswith(".tmp"):
            calls["n"] += 1
            if calls["n"] == 1:
                # First existence check after write/close: claim temp vanished.
                return False
        return result

    monkeypatch.setattr(persistence, "_path_exists", exists_spy)
    with pytest.raises(persistence.PersistenceError, match="disappeared before publish"):
        persistence.durable_write_json_new(path, {"ok": True})
    assert not path.exists()
    assert list(path.parent.glob(".tmp-*.tmp")) == [] if path.parent.exists() else True


def test_failure_injection_leaves_no_half_written_journal(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "j" / "half.json"

    def boom(source: str, target: str) -> None:
        raise OSError(3, "injected publish failure", source, None, target)

    monkeypatch.setattr(persistence.os, "rename", boom)
    with pytest.raises(persistence.PersistenceError, match="OS error"):
        persistence.durable_write_json_new(path, {"half": True})
    assert not path.exists()
    assert path.parent.exists()
    assert list(path.parent.glob(".tmp-*.tmp")) == []


def test_windows_max_path_length_journal_publish(tmp_path: pathlib.Path) -> None:
    """Exact regression for Candidate B r002: target path length == 260."""
    record = {"generation_id": "a" * 64, "response": "synthetic only"}
    target_name = ("a" * 64) + ".json"
    need = 260 - 1 - len(target_name)
    padding = "p" * max(1, need - len(str(tmp_path)) - 1)
    parent = tmp_path / padding
    while len(str(parent / target_name)) < 260:
        padding += "x"
        parent = tmp_path / padding
    while len(str(parent / target_name)) > 260:
        padding = padding[:-1]
        parent = tmp_path / padding
    parent.mkdir(parents=True)
    path = parent / target_name
    assert len(str(path)) == 260

    receipt = persistence.durable_write_json_new(path, record)
    persisted = persistence._read_bytes(path)
    assert receipt.sha256 == persistence.sha256_bytes(persisted)
    assert json.loads(persisted.decode("utf-8")) == record
    assert list(parent.glob(".tmp-*.tmp")) == []
    persistence._unlink_path(path)


def test_three_hundred_distinct_journals_leave_no_temps(tmp_path: pathlib.Path) -> None:
    journal_dir = tmp_path / "batch_j"
    receipts: list[persistence.PersistenceReceipt] = []
    for index in range(1, 301):
        path = journal_dir / f"{index:064x}.json"
        payload = _journal_payload(index)
        receipt = persistence.durable_write_json_new(path, payload)
        receipts.append(receipt)
        assert receipt.sha256 == persistence.sha256_bytes(persistence._read_bytes(path))
        assert json.loads(persistence._read_bytes(path).decode("utf-8")) == payload

    assert len(receipts) == 300
    assert len({receipt.sha256 for receipt in receipts}) == 300
    assert len(list(journal_dir.glob("*.json"))) == 300
    assert list(journal_dir.glob(".tmp-*.tmp")) == []
