"""
Read-only loader for pilot mechanical-repair audit inputs.

Supports generation_attempts, public_benchmark completion JSONL,
legacy_replay results, and legacy_replay_pilot case_results — grouped
deterministically and never mutating source artifacts.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from agent_tools.finals_rebuild.artifacts import sha256_text

SOURCE_FORMAT_AUTO = "auto"
SOURCE_FORMAT_GENERATION_ATTEMPTS = "generation_attempts"
SOURCE_FORMAT_PUBLIC_BENCHMARK = "public_benchmark"
SOURCE_FORMAT_LEGACY_REPLAY = "legacy_replay"
SOURCE_FORMAT_LEGACY_REPLAY_PILOT = "legacy_replay_pilot"

SUPPORTED_SOURCE_FORMATS: frozenset[str] = frozenset(
    {
        SOURCE_FORMAT_AUTO,
        SOURCE_FORMAT_GENERATION_ATTEMPTS,
        SOURCE_FORMAT_PUBLIC_BENCHMARK,
        SOURCE_FORMAT_LEGACY_REPLAY,
        SOURCE_FORMAT_LEGACY_REPLAY_PILOT,
    }
)

FIDELITY_RAW_RESPONSE = "raw_response_source"
FIDELITY_EXTRACTED_ONLY = "extracted_code_only"

GENERATION_TREATMENTS: frozenset[str] = frozenset({"ab1", "ab2g"})
PUBLIC_BENCHMARK_TREATMENTS: frozenset[str] = frozenset({"ab1", "ab2g"})
LEGACY_TREATMENT = "ab2"

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

_AB2_PATH_RE = re.compile(r"_Ab2_", re.IGNORECASE)


class PilotArtifactLoaderError(Exception):
    """Raised when artifact loading fails closed."""


@dataclass(frozen=True)
class PilotLoadedSample:
    source_id: str
    source_type: str
    source_fidelity: str
    dataset: str
    model_tag: Optional[str]
    task_id: str
    treatment: str
    attempt_kind: str
    first_attempt_selection_status: str
    raw_response: Optional[str]
    extracted_code: Optional[str]
    raw_response_sha256: Optional[str]
    source_artifact_path: str
    source_record_index: int
    entry_point: Optional[str]
    skill_id: Optional[str] = None
    pilot_only: bool = True
    confirmatory_eligible: bool = False


def resolve_repo_root(start: Optional[pathlib.Path] = None) -> pathlib.Path:
    if start is None:
        start = pathlib.Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / ".git").is_dir():
            return parent
    return pathlib.Path.cwd()


def _read_jsonl_records(path: pathlib.Path) -> List[Tuple[int, Dict[str, Any]]]:
    if not path.is_file():
        raise PilotArtifactLoaderError(f"artifact file not found: {path}")

    records: List[Tuple[int, Dict[str, Any]]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
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


def _read_repo_text(repo_root: pathlib.Path, relative_path: str) -> str:
    path = repo_root / relative_path.replace("\\", "/")
    if not path.is_file():
        raise PilotArtifactLoaderError(f"source code file not found: {path}")
    return path.read_text(encoding="utf-8")


def _infer_treatment_from_path(path: str) -> str:
    if _AB2_PATH_RE.search(path):
        return LEGACY_TREATMENT
    return "unknown"


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
            target_line = min(line_no for _, line_no in tied)
            selected = next(pair for pair in indexed_records if pair[0] == target_line)
            return selected, "ambiguous"
        target_line = tied[0][1]
        selected = next(pair for pair in indexed_records if pair[0] == target_line)
        return selected, "ordinal"

    markers = [
        (_is_marked_first_attempt(record), line_no, record)
        for line_no, record in indexed_records
    ]
    explicit_true = [item for item in markers if item[0] is True]
    if explicit_true:
        if len(explicit_true) > 1:
            return (explicit_true[0][1], explicit_true[0][2]), "ambiguous"
        return (explicit_true[0][1], explicit_true[0][2]), "explicit_marker"
    if any(item[0] is False for item in markers) and len(indexed_records) > 1:
        return indexed_records[0], "ambiguous"
    if len(indexed_records) > 1:
        return indexed_records[0], "first_jsonl_record"
    return indexed_records[0], "only_record"


def _normalize_generation_treatment(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotArtifactLoaderError(f"invalid treatment value: {value!r}")
    treatment = value.strip().lower()
    if treatment not in GENERATION_TREATMENTS:
        raise PilotArtifactLoaderError(
            f"unsupported treatment {treatment!r}; expected one of "
            f"{sorted(GENERATION_TREATMENTS)}"
        )
    return treatment


def _treatment_allowed(treatment: str, allowed: Optional[Iterable[str]]) -> bool:
    if allowed is None:
        return True
    return treatment in set(allowed)


def _load_entry_points(root: pathlib.Path) -> Dict[str, str]:
    for name in ("tasks_selected.jsonl", "tasks.json"):
        tasks_path = root / name
        if not tasks_path.is_file():
            continue
        mapping: Dict[str, str] = {}
        if name.endswith(".jsonl"):
            records_iter = (record for _line_no, record in _read_jsonl_records(tasks_path))
        else:
            try:
                data = json.loads(tasks_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise PilotArtifactLoaderError(
                    f"{tasks_path}: invalid JSON: {exc}"
                ) from exc
            if isinstance(data, list):
                records_iter = (record for record in data if isinstance(record, dict))
            elif isinstance(data, dict):
                records_iter = iter([data])
            else:
                raise PilotArtifactLoaderError(
                    f"{tasks_path}: expected JSON array or object"
                )
        for record in records_iter:
            task_id = record.get("task_id")
            entry_point = record.get("entry_point")
            if isinstance(task_id, str) and task_id.strip():
                if isinstance(entry_point, str) and entry_point.strip():
                    mapping[task_id.strip()] = entry_point.strip()
        return mapping
    return {}


def _resolve_generation_attempts_path(root: pathlib.Path) -> pathlib.Path:
    direct = root / "generation_attempts.jsonl"
    if direct.is_file():
        return direct
    nested = root / "humaneval" / "generation_attempts.jsonl"
    if nested.is_file():
        return nested
    raise PilotArtifactLoaderError(
        f"generation_attempts.jsonl not found under {root}"
    )


def _load_manifest_model(root: pathlib.Path) -> Optional[str]:
    for manifest in (root / "generation_manifest.json", root / "humaneval" / "generation_manifest.json"):
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        model = data.get("model") or data.get("model_tag")
        if isinstance(model, str) and model.strip():
            return model.strip()
    return None


def load_generation_attempts_first(
    artifacts_root: Union[str, pathlib.Path],
    *,
    treatments: Optional[Iterable[str]] = None,
) -> List[PilotLoadedSample]:
    root = pathlib.Path(artifacts_root)
    attempts_path = _resolve_generation_attempts_path(root)
    entry_points = _load_entry_points(root.parent if attempts_path.parent.name == "humaneval" else root)
    if not entry_points and attempts_path.parent.name == "humaneval":
        entry_points = _load_entry_points(attempts_path.parent)

    allowed = set(treatments) if treatments is not None else None
    model_tag = _load_manifest_model(root)
    dataset = root.name
    if attempts_path.parent.name == "humaneval":
        dataset = f"{root.name}/humaneval"

    grouped: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any]]]] = {}
    for line_no, record in _read_jsonl_records(attempts_path):
        task_id = record.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise PilotArtifactLoaderError(
                f"{attempts_path}: line {line_no}: missing task_id"
            )
        treatment = _normalize_generation_treatment(record.get("treatment"))
        if not _treatment_allowed(treatment, allowed):
            continue
        grouped.setdefault((task_id, treatment), []).append((line_no, record))

    samples: List[PilotLoadedSample] = []
    for (task_id, treatment), group in sorted(grouped.items()):
        (line_no, record), selection_status = _select_first_attempt(group)
        raw_response = record.get("raw_response")
        if raw_response is not None and not isinstance(raw_response, str):
            raise PilotArtifactLoaderError(
                f"{attempts_path}: line {line_no}: raw_response must be str or null"
            )
        stored_hash = record.get("raw_response_sha256")
        computed_hash = sha256_text(raw_response) if raw_response is not None else None
        if stored_hash is not None and computed_hash is not None and stored_hash != computed_hash:
            raise PilotArtifactLoaderError(
                f"{attempts_path}: line {line_no}: raw_response_sha256 mismatch"
            )
        attempt_kind = record.get("attempt_kind")
        if not isinstance(attempt_kind, str) or not attempt_kind.strip():
            attempt_kind = "first_attempt"
        sample_index = record.get("sample_index", 0)
        meta_model = None
        metadata = record.get("metadata")
        if isinstance(metadata, dict):
            meta_model = metadata.get("model") or metadata.get("model_tag")
        samples.append(
            PilotLoadedSample(
                source_id=f"{task_id}|{treatment}|{sample_index}",
                source_type=SOURCE_FORMAT_GENERATION_ATTEMPTS,
                source_fidelity=FIDELITY_RAW_RESPONSE,
                dataset=dataset,
                model_tag=meta_model if isinstance(meta_model, str) else model_tag,
                task_id=task_id,
                treatment=treatment,
                attempt_kind=str(attempt_kind),
                first_attempt_selection_status=selection_status,
                raw_response=raw_response,
                extracted_code=None,
                raw_response_sha256=stored_hash if stored_hash is not None else computed_hash,
                source_artifact_path=str(attempts_path),
                source_record_index=line_no,
                entry_point=entry_points.get(task_id),
            )
        )
    return samples


def _find_public_benchmark_jsonl(root: pathlib.Path) -> List[pathlib.Path]:
    return sorted(root.glob("**/evalplus/*.jsonl"))


def load_public_benchmark(
    artifacts_root: Union[str, pathlib.Path],
    *,
    treatments: Optional[Iterable[str]] = None,
) -> List[PilotLoadedSample]:
    root = pathlib.Path(artifacts_root)
    jsonl_files = _find_public_benchmark_jsonl(root)
    if not jsonl_files:
        raise PilotArtifactLoaderError(
            f"no public_benchmark evalplus JSONL files found under {root}"
        )

    allowed = set(treatments) if treatments is not None else None
    entry_points = _load_entry_points(root)
    samples: List[PilotLoadedSample] = []

    for jsonl_path in jsonl_files:
        treatment = jsonl_path.stem.lower()
        if treatment not in PUBLIC_BENCHMARK_TREATMENTS:
            continue
        if not _treatment_allowed(treatment, allowed):
            continue
        benchmark = "unknown"
        parts = jsonl_path.parts
        if "humaneval" in parts:
            benchmark = "humaneval"
        elif "mbpp" in parts:
            benchmark = "mbpp"

        for line_no, record in _read_jsonl_records(jsonl_path):
            task_id = record.get("task_id")
            if not isinstance(task_id, str) or not task_id.strip():
                raise PilotArtifactLoaderError(
                    f"{jsonl_path}: line {line_no}: missing task_id"
                )
            completion = record.get("completion")
            if completion is not None and not isinstance(completion, str):
                raise PilotArtifactLoaderError(
                    f"{jsonl_path}: line {line_no}: completion must be str or null"
                )
            if not completion or not completion.strip():
                continue
            entry_point = entry_points.get(task_id)
            if entry_point is None and isinstance(record.get("entry_point"), str):
                entry_point = record["entry_point"]
            samples.append(
                PilotLoadedSample(
                    source_id=f"{task_id}|{treatment}|0",
                    source_type=SOURCE_FORMAT_PUBLIC_BENCHMARK,
                    source_fidelity=FIDELITY_EXTRACTED_ONLY,
                    dataset=benchmark,
                    model_tag=None,
                    task_id=task_id,
                    treatment=treatment,
                    attempt_kind="extracted_completion",
                    first_attempt_selection_status="only_record",
                    raw_response=None,
                    extracted_code=completion,
                    raw_response_sha256=None,
                    source_artifact_path=str(jsonl_path),
                    source_record_index=line_no,
                    entry_point=entry_point,
                )
            )
    return samples


def load_legacy_replay(
    artifacts_root: Union[str, pathlib.Path],
    *,
    treatments: Optional[Iterable[str]] = None,
    repo_root: Optional[pathlib.Path] = None,
) -> List[PilotLoadedSample]:
    root = pathlib.Path(artifacts_root)
    results_path = root / "legacy_replay_results.json"
    if not results_path.is_file():
        raise PilotArtifactLoaderError(
            f"legacy_replay_results.json not found under {root}"
        )
    if treatments is not None and LEGACY_TREATMENT not in set(treatments):
        return []

    repo = repo_root or resolve_repo_root(root)
    records = json.loads(results_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise PilotArtifactLoaderError(
            f"{results_path}: expected a JSON array"
        )

    samples: List[PilotLoadedSample] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            continue
        skill_id = record.get("skill_id")
        source_path = record.get("source_path")
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise PilotArtifactLoaderError(
                f"{results_path}: record {index}: missing skill_id"
            )
        if not isinstance(source_path, str) or not source_path.strip():
            raise PilotArtifactLoaderError(
                f"{results_path}: record {index}: missing source_path"
            )
        treatment = _infer_treatment_from_path(source_path)
        code = _read_repo_text(repo, source_path)
        model_tag = None
        if "gemini" in source_path.lower():
            model_tag = "gemini-3-flash"
        elif "qwen3-14b" in source_path.lower():
            model_tag = "qwen3-14b"
        elif "qwen3-8b" in source_path.lower():
            model_tag = "qwen3-8b"
        elif "qwen2.5-coder-14b" in source_path.lower():
            model_tag = "qwen2.5-coder-14b"
        samples.append(
            PilotLoadedSample(
                source_id=record.get("pair_id") or f"{skill_id}|{index}",
                source_type=SOURCE_FORMAT_LEGACY_REPLAY,
                source_fidelity=FIDELITY_EXTRACTED_ONLY,
                dataset="math_dev",
                model_tag=model_tag,
                task_id=skill_id,
                treatment=treatment,
                attempt_kind="legacy_ab2_source",
                first_attempt_selection_status="only_record",
                raw_response=None,
                extracted_code=code,
                raw_response_sha256=None,
                source_artifact_path=str(results_path),
                source_record_index=index,
                entry_point="generate",
                skill_id=skill_id,
            )
        )
    return samples


def _resolve_case_results_path(root: pathlib.Path) -> pathlib.Path:
    direct = root / "case_results.jsonl"
    if direct.is_file():
        return direct
    matches = sorted(root.glob("*/case_results.jsonl"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise PilotArtifactLoaderError(
            f"ambiguous legacy_replay_pilot layout under {root}: "
            f"multiple case_results.jsonl files"
        )
    raise PilotArtifactLoaderError(
        f"case_results.jsonl not found under {root}"
    )


def load_legacy_replay_pilot(
    artifacts_root: Union[str, pathlib.Path],
    *,
    treatments: Optional[Iterable[str]] = None,
    repo_root: Optional[pathlib.Path] = None,
) -> List[PilotLoadedSample]:
    root = pathlib.Path(artifacts_root)
    case_path = _resolve_case_results_path(root)
    if treatments is not None and LEGACY_TREATMENT not in set(treatments):
        return []

    repo = repo_root or resolve_repo_root(root)
    samples: List[PilotLoadedSample] = []
    for line_no, record in _read_jsonl_records(case_path):
        case_id = record.get("case_id")
        skill_id = record.get("skill_id")
        source_path = record.get("source_ab2_path")
        if not isinstance(case_id, str) or not case_id.strip():
            raise PilotArtifactLoaderError(
                f"{case_path}: line {line_no}: missing case_id"
            )
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise PilotArtifactLoaderError(
                f"{case_path}: line {line_no}: missing skill_id"
            )
        if not isinstance(source_path, str) or not source_path.strip():
            raise PilotArtifactLoaderError(
                f"{case_path}: line {line_no}: missing source_ab2_path"
            )
        treatment = _infer_treatment_from_path(source_path)
        code = _read_repo_text(repo, source_path)
        model_tag = record.get("model_id") if isinstance(record.get("model_id"), str) else None
        samples.append(
            PilotLoadedSample(
                source_id=case_id,
                source_type=SOURCE_FORMAT_LEGACY_REPLAY_PILOT,
                source_fidelity=FIDELITY_EXTRACTED_ONLY,
                dataset="math_dev",
                model_tag=model_tag,
                task_id=skill_id,
                treatment=treatment,
                attempt_kind="legacy_ab2_source",
                first_attempt_selection_status="only_record",
                raw_response=None,
                extracted_code=code,
                raw_response_sha256=None,
                source_artifact_path=str(case_path),
                source_record_index=line_no,
                entry_point="generate",
                skill_id=skill_id,
            )
        )
    return samples


def detect_source_format(artifacts_root: Union[str, pathlib.Path]) -> str:
    """Detect source format from explicit on-disk layout only."""
    root = pathlib.Path(artifacts_root)
    matches: List[str] = []

    if (root / "legacy_replay_results.json").is_file():
        matches.append(SOURCE_FORMAT_LEGACY_REPLAY)
    if (root / "case_results.jsonl").is_file() or list(root.glob("*/case_results.jsonl")):
        matches.append(SOURCE_FORMAT_LEGACY_REPLAY_PILOT)
    if (root / "generation_attempts.jsonl").is_file() or (
        root / "humaneval" / "generation_attempts.jsonl"
    ).is_file():
        matches.append(SOURCE_FORMAT_GENERATION_ATTEMPTS)
    if _find_public_benchmark_jsonl(root):
        matches.append(SOURCE_FORMAT_PUBLIC_BENCHMARK)

    if not matches:
        raise PilotArtifactLoaderError(
            f"cannot auto-detect source format under {root}"
        )
    if len(matches) > 1:
        raise PilotArtifactLoaderError(
            f"ambiguous source format under {root}: {matches}"
        )
    return matches[0]


def load_pilot_samples(
    artifacts_root: Union[str, pathlib.Path],
    *,
    source_format: str = SOURCE_FORMAT_AUTO,
    treatments: Optional[Iterable[str]] = None,
    repo_root: Optional[pathlib.Path] = None,
) -> List[PilotLoadedSample]:
    root = pathlib.Path(artifacts_root)
    fmt = source_format
    if fmt == SOURCE_FORMAT_AUTO:
        fmt = detect_source_format(root)
    if fmt not in SUPPORTED_SOURCE_FORMATS - {SOURCE_FORMAT_AUTO}:
        raise PilotArtifactLoaderError(f"unsupported source_format {fmt!r}")

    if fmt == SOURCE_FORMAT_GENERATION_ATTEMPTS:
        return load_generation_attempts_first(root, treatments=treatments)
    if fmt == SOURCE_FORMAT_PUBLIC_BENCHMARK:
        return load_public_benchmark(root, treatments=treatments)
    if fmt == SOURCE_FORMAT_LEGACY_REPLAY:
        return load_legacy_replay(root, treatments=treatments, repo_root=repo_root)
    if fmt == SOURCE_FORMAT_LEGACY_REPLAY_PILOT:
        return load_legacy_replay_pilot(root, treatments=treatments, repo_root=repo_root)
    raise PilotArtifactLoaderError(f"unsupported source_format {fmt!r}")
