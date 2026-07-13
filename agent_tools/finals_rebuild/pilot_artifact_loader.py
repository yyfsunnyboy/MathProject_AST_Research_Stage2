"""
Read-only loader for pilot mechanical-repair audit inputs.

Loads generation attempt artifacts (primarily generation_attempts.jsonl),
groups by task_id + treatment, and deterministically selects the first
attempt per group. Never writes to or mutates source artifacts.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from agent_tools.finals_rebuild.artifacts import sha256_text

SUPPORTED_TREATMENTS: frozenset[str] = frozenset({"ab1", "ab2g"})

_FIRST_ATTEMPT_ORDINAL_FIELDS: Tuple[str, ...] = (
    "attempt_ordinal",
    "attempt_index",
    "attempt_number",
)

_FIRST_ATTEMPT_MARKER_FIELDS: Tuple[str, ...] = (
    "is_first_attempt",
    "first_attempt",
)

_ATTEMPT_KIND_FIRST_VALUES: frozenset[str] = frozenset(
    {"first", "first_attempt", "initial"}
)


class PilotArtifactLoaderError(Exception):
    """Raised when artifact loading fails closed."""


@dataclass(frozen=True)
class PilotLoadedSample:
    source_id: str
    task_id: str
    treatment: str
    attempt_kind: str
    first_attempt_selection_status: str
    raw_response: Optional[str]
    raw_response_sha256: Optional[str]
    source_artifact_path: str
    source_record_index: int
    entry_point: Optional[str]
    pilot_only: bool = True
    confirmatory_eligible: bool = False


def _normalize_treatment(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotArtifactLoaderError(f"invalid treatment value: {value!r}")
    treatment = value.strip().lower()
    if treatment not in SUPPORTED_TREATMENTS:
        raise PilotArtifactLoaderError(
            f"unsupported treatment {treatment!r}; expected one of "
            f"{sorted(SUPPORTED_TREATMENTS)}"
        )
    return treatment


def _read_jsonl_records(path: pathlib.Path) -> List[Tuple[int, Dict[str, Any]]]:
    if not path.is_file():
        raise PilotArtifactLoaderError(f"artifact file not found: {path}")

    records: List[Tuple[int, Dict[str, Any]]] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise PilotArtifactLoaderError(
                f"{path}: line {line_no}: invalid JSON: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise PilotArtifactLoaderError(
                f"{path}: line {line_no}: expected a JSON object"
            )
        records.append((line_no, obj))
    return records


def _ordinal_from_record(record: Dict[str, Any]) -> Optional[int]:
    for field in _FIRST_ATTEMPT_ORDINAL_FIELDS:
        value = record.get(field)
        if value is None:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        raise PilotArtifactLoaderError(
            f"non-integer attempt ordinal in field {field!r}: {value!r}"
        )
    sample_index = record.get("sample_index")
    if isinstance(sample_index, int):
        return sample_index
    return None


def _is_marked_first_attempt(record: Dict[str, Any]) -> Optional[bool]:
    for field in _FIRST_ATTEMPT_MARKER_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if isinstance(value, bool):
            return value
        if value in (0, 1):
            return bool(value)
        raise PilotArtifactLoaderError(
            f"invalid boolean marker {field}={value!r}"
        )

    attempt_kind = record.get("attempt_kind")
    if isinstance(attempt_kind, str):
        normalized = attempt_kind.strip().lower()
        if normalized in _ATTEMPT_KIND_FIRST_VALUES:
            return True
        if normalized:
            return False
    return None


def _select_first_attempt(
    indexed_records: Sequence[Tuple[int, Dict[str, Any]]],
) -> Tuple[Tuple[int, Dict[str, Any]], str]:
    if not indexed_records:
        raise PilotArtifactLoaderError("cannot select first attempt from empty group")

    ordinals: List[Tuple[int, int]] = []
    for line_no, record in indexed_records:
        ordinal = _ordinal_from_record(record)
        if ordinal is not None:
            ordinals.append((ordinal, line_no))

    if ordinals:
        min_ordinal = min(o for o, _ in ordinals)
        tied = [pair for pair in ordinals if pair[0] == min_ordinal]
        if len(tied) > 1:
            return (
                next(
                    pair
                    for pair in indexed_records
                    if pair[0] == min(line_no for _, line_no in tied)
                ),
                "ambiguous",
            )
        target_line = tied[0][1]
        selected = next(pair for pair in indexed_records if pair[0] == target_line)
        return selected, "ordinal"

    markers = [
        (_is_marked_first_attempt(record), line_no, record)
        for line_no, record in indexed_records
    ]
    explicit_true = [item for item in markers if item[0] is True]
    explicit_false = [item for item in markers if item[0] is False]
    if explicit_true:
        if len(explicit_true) > 1:
            return (
                (explicit_true[0][1], explicit_true[0][2]),
                "ambiguous",
            )
        return (explicit_true[0][1], explicit_true[0][2]), "explicit_marker"
    if explicit_false and len(indexed_records) > 1:
        return indexed_records[0], "ambiguous"

    if len(indexed_records) > 1:
        # Multiple rows with no ordinal/marker — only first JSONL row is defensible.
        return indexed_records[0], "first_jsonl_record"

    return indexed_records[0], "only_record"


def _build_source_id(task_id: str, treatment: str, record: Dict[str, Any]) -> str:
    sample_index = record.get("sample_index", 0)
    return f"{task_id}|{treatment}|{sample_index}"


def _record_to_loaded_sample(
    *,
    task_id: str,
    treatment: str,
    line_no: int,
    record: Dict[str, Any],
    source_path: pathlib.Path,
    selection_status: str,
    entry_point: Optional[str],
) -> PilotLoadedSample:
    raw_response = record.get("raw_response")
    if raw_response is not None and not isinstance(raw_response, str):
        raise PilotArtifactLoaderError(
            f"{source_path}: line {line_no}: raw_response must be str or null"
        )

    stored_hash = record.get("raw_response_sha256")
    computed_hash = sha256_text(raw_response) if raw_response is not None else None
    if stored_hash is not None and computed_hash is not None and stored_hash != computed_hash:
        raise PilotArtifactLoaderError(
            f"{source_path}: line {line_no}: raw_response_sha256 mismatch"
        )
    raw_hash = stored_hash if stored_hash is not None else computed_hash

    attempt_kind = record.get("attempt_kind")
    if not isinstance(attempt_kind, str) or not attempt_kind.strip():
        attempt_kind = "first_attempt"

    entry_point_value = entry_point
    if entry_point_value is None:
        ep = record.get("entry_point")
        entry_point_value = ep if isinstance(ep, str) and ep.strip() else None

    return PilotLoadedSample(
        source_id=_build_source_id(task_id, treatment, record),
        task_id=task_id,
        treatment=treatment,
        attempt_kind=str(attempt_kind),
        first_attempt_selection_status=selection_status,
        raw_response=raw_response,
        raw_response_sha256=raw_hash,
        source_artifact_path=str(source_path),
        source_record_index=line_no,
        entry_point=entry_point_value,
    )


def _load_entry_points(artifacts_root: pathlib.Path) -> Dict[str, str]:
    tasks_path = artifacts_root / "tasks_selected.jsonl"
    if not tasks_path.is_file():
        return {}

    mapping: Dict[str, str] = {}
    for line_no, record in _read_jsonl_records(tasks_path):
        task_id = record.get("task_id")
        entry_point = record.get("entry_point")
        if not isinstance(task_id, str) or not task_id.strip():
            continue
        if isinstance(entry_point, str) and entry_point.strip():
            mapping[task_id] = entry_point.strip()
    return mapping


def load_generation_attempts_first(
    artifacts_root: Union[str, pathlib.Path],
    *,
    treatments: Optional[Iterable[str]] = None,
) -> List[PilotLoadedSample]:
    """Load first-attempt samples grouped by task_id + treatment."""
    root = pathlib.Path(artifacts_root)
    attempts_path = root / "generation_attempts.jsonl"
    indexed_records = _read_jsonl_records(attempts_path)
    entry_points = _load_entry_points(root)

    allowed = (
        {_normalize_treatment(t) for t in treatments}
        if treatments is not None
        else set(SUPPORTED_TREATMENTS)
    )

    grouped: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any]]]] = {}
    for line_no, record in indexed_records:
        task_id = record.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise PilotArtifactLoaderError(
                f"{attempts_path}: line {line_no}: missing task_id"
            )
        treatment = _normalize_treatment(record.get("treatment"))
        if treatment not in allowed:
            continue
        grouped.setdefault((task_id, treatment), []).append((line_no, record))

    samples: List[PilotLoadedSample] = []
    for (task_id, treatment), group in sorted(grouped.items()):
        (line_no, record), selection_status = _select_first_attempt(group)
        samples.append(
            _record_to_loaded_sample(
                task_id=task_id,
                treatment=treatment,
                line_no=line_no,
                record=record,
                source_path=attempts_path,
                selection_status=selection_status,
                entry_point=entry_points.get(task_id),
            )
        )
    return samples
