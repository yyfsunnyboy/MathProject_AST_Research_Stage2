"""
Official HumanEval+ dataset provenance helpers.

Fetches and converts the EvalPlus release asset HumanEvalPlus.jsonl.gz into
the repo's runner-facing tasks.jsonl (task_id, prompt, entry_point only).

No model calls. No HumanEval fallback. No network during prepare/convert.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union

OFFICIAL_SOURCE_REPOSITORY = "https://github.com/evalplus/humanevalplus_release"
OFFICIAL_RELEASE_TAG = "v0.1.10"
OFFICIAL_ASSET_NAME = "HumanEvalPlus.jsonl.gz"
OFFICIAL_SOURCE_URL = (
    f"{OFFICIAL_SOURCE_REPOSITORY}/releases/download/"
    f"{OFFICIAL_RELEASE_TAG}/{OFFICIAL_ASSET_NAME}"
)
EXPECTED_TASK_COUNT = 164
TASK_ORDER_POLICY = "official_source_order"
ALLOWED_OUTPUT_KEYS = frozenset({"task_id", "prompt", "entry_point"})


class HumanevalPlusDatasetError(ValueError):
    """Raised on any HumanEval+ dataset invariant violation; fails closed."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Union[str, pathlib.Path]) -> str:
    p = pathlib.Path(path)
    digest = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_sha256(
    path: Union[str, pathlib.Path], expected_sha256: str
) -> None:
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise HumanevalPlusDatasetError(
            f"source SHA256 mismatch for {path}: expected {expected_sha256!r}, "
            f"got {actual!r}"
        )


def load_source_records(path: Union[str, pathlib.Path]) -> List[Dict[str, Any]]:
    """Load official HumanEval+ JSONL records from .jsonl.gz or plain .jsonl."""
    p = pathlib.Path(path)
    if not p.is_file():
        raise HumanevalPlusDatasetError(f"source file not found: {p}")

    records: List[Dict[str, Any]] = []
    if p.suffix.lower() == ".gz" or p.name.endswith(".jsonl.gz"):
        opener = lambda: gzip.open(p, "rt", encoding="utf-8")
    else:
        opener = lambda: open(p, "r", encoding="utf-8")

    with opener() as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise HumanevalPlusDatasetError(
                    f"{p}: line {line_no}: invalid JSON: {exc}"
                ) from exc
            if not isinstance(obj, dict):
                raise HumanevalPlusDatasetError(
                    f"{p}: line {line_no}: expected a JSON object"
                )
            records.append(obj)
    return records


def prepare_tasks_from_source(
    records: Sequence[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Extract runner tasks in official source order without modifying prompts."""
    if len(records) != EXPECTED_TASK_COUNT:
        raise HumanevalPlusDatasetError(
            f"expected exactly {EXPECTED_TASK_COUNT} tasks, got {len(records)}"
        )

    tasks: List[Dict[str, str]] = []
    seen: set[str] = set()

    for index, rec in enumerate(records):
        task_id = rec.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise HumanevalPlusDatasetError(
                f"record {index}: missing or invalid task_id"
            )
        if task_id in seen:
            raise HumanevalPlusDatasetError(f"duplicate task_id {task_id!r}")
        seen.add(task_id)

        prompt = rec.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise HumanevalPlusDatasetError(
                f"task_id={task_id!r}: missing or empty prompt"
            )

        entry_point = rec.get("entry_point")
        if not isinstance(entry_point, str) or not entry_point.strip():
            raise HumanevalPlusDatasetError(
                f"task_id={task_id!r}: missing or empty entry_point"
            )

        tasks.append(
            {
                "task_id": task_id,
                "prompt": prompt,
                "entry_point": entry_point,
            }
        )

    if len(seen) != EXPECTED_TASK_COUNT:
        raise HumanevalPlusDatasetError(
            f"expected {EXPECTED_TASK_COUNT} unique task_id values, got {len(seen)}"
        )

    return tasks


def write_tasks_jsonl(
    tasks: Sequence[Dict[str, str]], path: Union[str, pathlib.Path]
) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        for rec in tasks:
            if set(rec.keys()) != ALLOWED_OUTPUT_KEYS:
                raise HumanevalPlusDatasetError(
                    f"tasks.jsonl record must contain exactly {sorted(ALLOWED_OUTPUT_KEYS)}, "
                    f"got {sorted(rec.keys())}"
                )
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def try_get_evalplus_metadata() -> Dict[str, Optional[str]]:
    """Best-effort EvalPlus package metadata; returns nulls when unavailable."""
    try:
        import evalplus  # noqa: PLC0415
        import evalplus.data as evalplus_data  # noqa: PLC0415
    except ImportError:
        return {
            "evalplus_package_version": None,
            "evalplus_dataset_hash": None,
            "evalplus_cache_path": None,
        }

    version = getattr(evalplus, "__version__", None)
    dataset_hash = None
    cache_path = None
    try:
        dataset_hash = evalplus_data.get_human_eval_plus_hash()
        from evalplus.data.humaneval import HUMANEVAL_PLUS_VERSION  # noqa: PLC0415
        from evalplus.data.utils import CACHE_DIR  # noqa: PLC0415

        cache_path = str(
            pathlib.Path(CACHE_DIR) / f"HumanEvalPlus-{HUMANEVAL_PLUS_VERSION}.jsonl"
        )
    except Exception:
        dataset_hash = None
        cache_path = None

    return {
        "evalplus_package_version": version,
        "evalplus_dataset_hash": dataset_hash,
        "evalplus_cache_path": cache_path,
    }


def _display_path(path: pathlib.Path) -> str:
    """Prefer repo-relative POSIX paths in manifests when possible."""
    try:
        return path.resolve().relative_to(pathlib.Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def build_dataset_manifest(
    *,
    source_path: Union[str, pathlib.Path],
    tasks_path: Union[str, pathlib.Path],
    creation_script: str,
    created_at_utc: Optional[str] = None,
    downloaded_at_utc: Optional[str] = None,
    evalplus_package_version: Optional[str] = None,
    evalplus_dataset_hash: Optional[str] = None,
    evalplus_cache_path: Optional[str] = None,
) -> Dict[str, Any]:
    source_path = pathlib.Path(source_path)
    tasks_path = pathlib.Path(tasks_path)
    return {
        "dataset_name": "HumanEval+",
        "dataset_role": "official_task_prompts_and_evalplus_tests",
        "task_count": EXPECTED_TASK_COUNT,
        "source_repository": OFFICIAL_SOURCE_REPOSITORY,
        "release_tag_or_dataset_version": OFFICIAL_RELEASE_TAG,
        "source_asset_name": OFFICIAL_ASSET_NAME,
        "source_url": OFFICIAL_SOURCE_URL,
        "source_path": _display_path(source_path),
        "source_sha256": sha256_file(source_path),
        "source_file_size_bytes": source_path.stat().st_size,
        "downloaded_at_utc": downloaded_at_utc,
        "tasks_file": _display_path(tasks_path),
        "tasks_sha256": sha256_file(tasks_path),
        "task_order_policy": TASK_ORDER_POLICY,
        "created_at_utc": created_at_utc or utc_now_iso(),
        "creation_script": creation_script,
        "evalplus_package_version": evalplus_package_version,
        "evalplus_dataset_hash": evalplus_dataset_hash,
        "evalplus_cache_path": evalplus_cache_path,
        "notes": [
            "No fallback to original HumanEval",
            "HumanEval+ shares task prompts with HumanEval; Plus refers to expanded evaluation tests",
            "The model receives only the official task prompt, not hidden tests",
            "tasks.jsonl contains only task_id, prompt, and entry_point",
            "source_sha256 is SHA-256 of HumanEvalPlus.jsonl.gz; evalplus_dataset_hash is EvalPlus loader MD5 of decompressed cache JSONL when available",
        ],
    }


def write_json_deterministic(obj: Any, path: Union[str, pathlib.Path]) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    p.write_text(serialised, encoding="utf-8")


def fetch_official_source(
    dest_path: Union[str, pathlib.Path],
    *,
    expected_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """Download the official HumanEvalPlus.jsonl.gz release asset."""
    dest = pathlib.Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.is_file() and expected_sha256 is not None:
        if sha256_file(dest) == expected_sha256.lower():
            return {
                "path": str(dest),
                "sha256": expected_sha256.lower(),
                "file_size_bytes": dest.stat().st_size,
                "downloaded_at_utc": None,
                "skipped_download": True,
            }

    req = urllib.request.Request(OFFICIAL_SOURCE_URL, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            status = resp.getcode()
            body = resp.read()
    except urllib.error.URLError as exc:
        raise HumanevalPlusDatasetError(
            f"failed to download {OFFICIAL_SOURCE_URL}: {exc}"
        ) from exc

    if status != 200:
        raise HumanevalPlusDatasetError(
            f"download {OFFICIAL_SOURCE_URL} returned HTTP {status}"
        )

    dest.write_bytes(body)
    actual = sha256_file(dest)
    if expected_sha256 is not None and actual != expected_sha256.lower():
        dest.unlink(missing_ok=True)
        raise HumanevalPlusDatasetError(
            f"downloaded source SHA256 mismatch: expected {expected_sha256!r}, got {actual!r}"
        )

    return {
        "path": str(dest),
        "sha256": actual,
        "file_size_bytes": dest.stat().st_size,
        "downloaded_at_utc": utc_now_iso(),
        "skipped_download": False,
    }


def prepare_tasks_file(
    *,
    source_path: Union[str, pathlib.Path],
    tasks_path: Union[str, pathlib.Path],
    manifest_path: Union[str, pathlib.Path],
    creation_script: str,
    expected_source_sha256: Optional[str] = None,
    downloaded_at_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Offline conversion: source gzip/jsonl -> tasks.jsonl + manifest."""
    source_path = pathlib.Path(source_path)
    tasks_path = pathlib.Path(tasks_path)
    manifest_path = pathlib.Path(manifest_path)

    if expected_source_sha256 is not None:
        verify_source_sha256(source_path, expected_source_sha256)

    records = load_source_records(source_path)
    tasks = prepare_tasks_from_source(records)
    write_tasks_jsonl(tasks, tasks_path)

    evalplus_meta = try_get_evalplus_metadata()
    manifest = build_dataset_manifest(
        source_path=source_path,
        tasks_path=tasks_path,
        creation_script=creation_script,
        downloaded_at_utc=downloaded_at_utc,
        evalplus_package_version=evalplus_meta["evalplus_package_version"],
        evalplus_dataset_hash=evalplus_meta["evalplus_dataset_hash"],
        evalplus_cache_path=evalplus_meta["evalplus_cache_path"],
    )
    write_json_deterministic(manifest, manifest_path)
    return manifest
