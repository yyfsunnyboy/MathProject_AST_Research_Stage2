#!/usr/bin/env python3
"""Build the Milestone 0A public-benchmark contamination manifest.

This script inventories repository evidence only. It does not create a formal
development/validation/confirmatory split and does not inspect model outputs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from zoneinfo import ZoneInfo

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from agent_tools.finals_rebuild import ollama_generation_runner as smoke_runner  # noqa: E402


HUMANEVAL_TASKS = "data/humaneval_plus/tasks.jsonl"
HUMANEVAL_DATASET_MANIFEST = "data/humaneval_plus/dataset_manifest.json"
SMOKE_RUNNER = "agent_tools/finals_rebuild/ollama_generation_runner.py"
FORENSIC_CSV = "artifacts/fail_to_fail_forensics/qwen8b_forensic_reviewed.csv"
RULE_MANIFESTS = (
    "artifacts/fail_to_fail_forensics/import_preservation_validation/candidate_manifest.csv",
    "artifacts/fail_to_fail_forensics/xor_safetyloop_validation/candidate_manifest.csv",
    "artifacts/fail_to_fail_forensics/healer_vnext_evalplus_replay/replay_manifest.csv",
)
FORENSIC_SUMMARY = (
    "artifacts/fail_to_fail_forensics/healer_vnext_public_benchmark_final_summary_zh.md"
)
SOURCE_PATHS = (
    HUMANEVAL_TASKS,
    HUMANEVAL_DATASET_MANIFEST,
    SMOKE_RUNNER,
    FORENSIC_CSV,
    *RULE_MANIFESTS,
    FORENSIC_SUMMARY,
)

EXPECTED_HUMANEVAL_TOTAL = 164
EXPECTED_SMOKE_COUNT = 20
EXPECTED_HUMANEVAL_FORENSIC = 38
EXPECTED_SMOKE_FORENSIC_OVERLAP = {"HumanEval/10", "HumanEval/19"}
EXPECTED_HUMANEVAL_EXCLUDED_UNION = 56
EXPECTED_HUMANEVAL_UNREVIEWED = 108
EXPECTED_MBPP_FORENSIC = 116

CSV_FIELDS = (
    "dataset",
    "task_id",
    "task_numeric_id",
    "generated_only",
    "aggregate_evaluated",
    "individually_reviewed",
    "failure_census_source",
    "rule_development_source",
    "contamination_status",
    "contamination_sources",
    "confirmatory_eligible",
    "evidence_paths",
    "notes",
)

CONTAMINATION_SOURCE_ORDER = (
    "engineering_smoke",
    "individual_review",
    "failure_census",
    "rule_development",
)

STATUS_ORDER = (
    "excluded_rule_development",
    "excluded_failure_census",
    "excluded_individual_review",
    "excluded_engineering_smoke",
    "pending_generated_or_aggregate_only",
    "unreviewed_candidate",
    "evidence_ambiguous",
)

MBPP_COMPLETE_MANIFEST_CANDIDATES = (
    ("data/mbpp_plus/tasks.jsonl", "data/mbpp_plus/dataset_manifest.json"),
    ("data/mbpp/tasks.jsonl", "data/mbpp/dataset_manifest.json"),
)


@dataclass(frozen=True)
class GovernanceBuild:
    rows: tuple[dict[str, str], ...]
    humaneval_task_ids: tuple[str, ...]
    smoke_task_ids: tuple[str, ...]
    humaneval_forensic_ids: frozenset[str]
    mbpp_forensic_ids: frozenset[str]
    rule_development_paths: dict[str, tuple[str, ...]]
    humaneval_metadata: dict[str, object]
    mbpp_total: int | None
    mbpp_manifest_paths: tuple[str, ...]


def _repo_path(repo_root: pathlib.Path, relative_path: str) -> pathlib.Path:
    return repo_root / pathlib.PurePosixPath(relative_path)


def _read_task_ids(path: pathlib.Path) -> list[str]:
    task_ids: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        task_id = record.get("task_id")
        if not isinstance(task_id, str):
            raise ValueError(f"{path}:{line_number}: missing string task_id")
        task_ids.append(task_id)
    if len(task_ids) != len(set(task_ids)):
        raise ValueError(f"duplicate task IDs in {path}")
    return task_ids


def task_numeric_id(task_id: str) -> int:
    try:
        return int(task_id.rsplit("/", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"task ID has no numeric suffix: {task_id!r}") from exc


def _read_forensic_ids(repo_root: pathlib.Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {"humaneval": set(), "mbpp": set()}
    path = _repo_path(repo_root, FORENSIC_CSV)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            dataset = (row.get("dataset") or "").strip().lower()
            task_id = (row.get("task_id") or "").strip()
            if dataset not in result or not task_id:
                raise ValueError(f"unexpected forensic row: dataset={dataset!r}, task_id={task_id!r}")
            result[dataset].add(task_id)
    return result


def _read_rule_development_paths(repo_root: pathlib.Path) -> dict[str, tuple[str, ...]]:
    evidence: dict[str, set[str]] = defaultdict(set)
    for relative_path in RULE_MANIFESTS:
        path = _repo_path(repo_root, relative_path)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or "task_id" not in reader.fieldnames:
                raise ValueError(f"{relative_path} has no task_id column")
            for row in reader:
                task_id = (row.get("task_id") or "").strip()
                if not task_id:
                    raise ValueError(f"empty task_id in {relative_path}")
                evidence[task_id].add(relative_path)
    return {task_id: tuple(sorted(paths)) for task_id, paths in evidence.items()}


def _find_complete_mbpp_manifest(
    repo_root: pathlib.Path,
) -> tuple[list[str] | None, tuple[str, ...]]:
    for tasks_rel, manifest_rel in MBPP_COMPLETE_MANIFEST_CANDIDATES:
        tasks_path = _repo_path(repo_root, tasks_rel)
        manifest_path = _repo_path(repo_root, manifest_rel)
        if not tasks_path.is_file() or not manifest_path.is_file():
            continue
        metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
        task_ids = _read_task_ids(tasks_path)
        declared_count = metadata.get("task_count")
        if declared_count != len(task_ids):
            raise ValueError(
                f"MBPP manifest count mismatch: declared={declared_count!r}, actual={len(task_ids)}"
            )
        if not task_ids or any(not task_id.startswith("Mbpp/") for task_id in task_ids):
            raise ValueError("candidate MBPP manifest does not contain a complete Mbpp/* task list")
        return task_ids, (tasks_rel, manifest_rel)
    return None, ()


def _evidence_flag(value: bool) -> str:
    return "true" if value else "false"


def classify_contamination_status(
    *,
    engineering_smoke: bool = False,
    generated_only: bool = False,
    aggregate_evaluated: bool = False,
    individually_reviewed: bool = False,
    failure_census_source: bool = False,
    rule_development_source: bool = False,
    evidence_ambiguous: bool = False,
) -> str:
    """Apply the fixed, most-restrictive-first status precedence."""
    if evidence_ambiguous:
        return "evidence_ambiguous"
    if rule_development_source:
        return "excluded_rule_development"
    if failure_census_source:
        return "excluded_failure_census"
    if engineering_smoke:
        return "excluded_engineering_smoke"
    if individually_reviewed:
        return "excluded_individual_review"
    if generated_only or aggregate_evaluated:
        return "pending_generated_or_aggregate_only"
    return "unreviewed_candidate"


def _build_row(
    *,
    dataset: str,
    task_id: str,
    engineering_smoke: bool,
    forensic_reviewed: bool,
    rule_paths: tuple[str, ...],
    base_evidence_paths: tuple[str, ...],
) -> dict[str, str]:
    individually_reviewed = engineering_smoke or forensic_reviewed
    failure_census_source = forensic_reviewed
    rule_development_source = bool(rule_paths)

    source_flags = {
        "engineering_smoke": engineering_smoke,
        "individual_review": individually_reviewed,
        "failure_census": failure_census_source,
        "rule_development": rule_development_source,
    }
    contamination_sources = [
        source for source in CONTAMINATION_SOURCE_ORDER if source_flags[source]
    ]

    status = classify_contamination_status(
        engineering_smoke=engineering_smoke,
        individually_reviewed=individually_reviewed,
        failure_census_source=failure_census_source,
        rule_development_source=rule_development_source,
    )

    excluded = individually_reviewed or failure_census_source or rule_development_source
    confirmatory_eligible = "false" if excluded else "pending"
    lower_level = "false" if individually_reviewed else "unknown"

    evidence_paths = sorted(set(base_evidence_paths) | set(rule_paths))
    if status == "unreviewed_candidate":
        notes = (
            "No task-level review evidence was found in the repository sources; "
            "candidate only, not confirmatory. Unknown lower-level history is not proof of absence."
        )
    elif engineering_smoke and not forensic_reviewed:
        notes = "Official-order engineering smoke task; excluded from confirmatory use."
    else:
        notes = "Task appears in the individually reviewed fail-to-fail forensic census."
    if rule_development_source:
        notes += " Structured candidate/replay evidence directly links it to rule development."

    return {
        "dataset": dataset,
        "task_id": task_id,
        "task_numeric_id": str(task_numeric_id(task_id)),
        "generated_only": lower_level,
        "aggregate_evaluated": lower_level,
        "individually_reviewed": _evidence_flag(individually_reviewed),
        "failure_census_source": _evidence_flag(failure_census_source),
        "rule_development_source": _evidence_flag(rule_development_source),
        "contamination_status": status,
        "contamination_sources": ";".join(contamination_sources),
        "confirmatory_eligible": confirmatory_eligible,
        "evidence_paths": ";".join(evidence_paths),
        "notes": notes,
    }


def build_governance(repo_root: pathlib.Path = REPO_ROOT) -> GovernanceBuild:
    repo_root = repo_root.resolve()
    he_manifest = json.loads(
        _repo_path(repo_root, HUMANEVAL_DATASET_MANIFEST).read_text(encoding="utf-8")
    )
    humaneval_task_ids = _read_task_ids(_repo_path(repo_root, HUMANEVAL_TASKS))
    smoke_task_ids = [
        task["task_id"]
        for task in smoke_runner.select_tasks_official_first_n(
            [{"task_id": task_id} for task_id in humaneval_task_ids],
            smoke_runner.SMOKE_TASK_COUNT,
        )
    ]
    forensic = _read_forensic_ids(repo_root)
    rule_paths = _read_rule_development_paths(repo_root)
    mbpp_task_ids, mbpp_manifest_paths = _find_complete_mbpp_manifest(repo_root)

    rows: list[dict[str, str]] = []
    smoke_set = set(smoke_task_ids)
    for task_id in humaneval_task_ids:
        base_paths = [HUMANEVAL_DATASET_MANIFEST, HUMANEVAL_TASKS]
        if task_id in smoke_set:
            base_paths.append(SMOKE_RUNNER)
        if task_id in forensic["humaneval"]:
            base_paths.append(FORENSIC_CSV)
        rows.append(
            _build_row(
                dataset="HumanEval+",
                task_id=task_id,
                engineering_smoke=task_id in smoke_set,
                forensic_reviewed=task_id in forensic["humaneval"],
                rule_paths=rule_paths.get(task_id, ()),
                base_evidence_paths=tuple(base_paths),
            )
        )

    mbpp_rows = mbpp_task_ids if mbpp_task_ids is not None else sorted(
        forensic["mbpp"], key=task_numeric_id
    )
    for task_id in mbpp_rows:
        base_paths = list(mbpp_manifest_paths)
        if task_id in forensic["mbpp"]:
            base_paths.append(FORENSIC_CSV)
        rows.append(
            _build_row(
                dataset="MBPP+",
                task_id=task_id,
                engineering_smoke=False,
                forensic_reviewed=task_id in forensic["mbpp"],
                rule_paths=rule_paths.get(task_id, ()),
                base_evidence_paths=tuple(base_paths),
            )
        )

    rows.sort(key=lambda row: (row["dataset"], int(row["task_numeric_id"])))
    result = GovernanceBuild(
        rows=tuple(rows),
        humaneval_task_ids=tuple(humaneval_task_ids),
        smoke_task_ids=tuple(smoke_task_ids),
        humaneval_forensic_ids=frozenset(forensic["humaneval"]),
        mbpp_forensic_ids=frozenset(forensic["mbpp"]),
        rule_development_paths=rule_paths,
        humaneval_metadata=he_manifest,
        mbpp_total=len(mbpp_task_ids) if mbpp_task_ids is not None else None,
        mbpp_manifest_paths=mbpp_manifest_paths,
    )
    validate_known_facts(result)
    return result


def validate_known_facts(build: GovernanceBuild) -> None:
    if len(build.humaneval_task_ids) != EXPECTED_HUMANEVAL_TOTAL:
        raise ValueError("HumanEval+ total does not equal 164")
    if build.humaneval_metadata.get("task_count") != EXPECTED_HUMANEVAL_TOTAL:
        raise ValueError("HumanEval+ dataset manifest does not declare 164 tasks")
    if smoke_runner.SMOKE_TASK_COUNT != EXPECTED_SMOKE_COUNT:
        raise ValueError("runner SMOKE_TASK_COUNT does not equal 20")
    if len(build.smoke_task_ids) != EXPECTED_SMOKE_COUNT:
        raise ValueError("official-order smoke selection does not contain 20 tasks")
    if len(build.humaneval_forensic_ids) != EXPECTED_HUMANEVAL_FORENSIC:
        raise ValueError("HumanEval forensic reviewed unique does not equal 38")
    overlap = set(build.smoke_task_ids) & set(build.humaneval_forensic_ids)
    if overlap != EXPECTED_SMOKE_FORENSIC_OVERLAP:
        raise ValueError(f"unexpected smoke/forensic overlap: {sorted(overlap)}")
    excluded = set(build.smoke_task_ids) | set(build.humaneval_forensic_ids)
    if len(excluded) != EXPECTED_HUMANEVAL_EXCLUDED_UNION:
        raise ValueError("HumanEval excluded union does not equal 56")
    if len(build.humaneval_task_ids) - len(excluded) != EXPECTED_HUMANEVAL_UNREVIEWED:
        raise ValueError("HumanEval unreviewed candidate count does not equal 108")
    if len(build.mbpp_forensic_ids) != EXPECTED_MBPP_FORENSIC:
        raise ValueError("MBPP forensic reviewed unique does not equal 116")
    if any(row["confirmatory_eligible"] == "true" for row in build.rows):
        raise ValueError("Milestone 0A must not mark any row confirmatory_eligible=true")
    if any(row["contamination_status"] not in STATUS_ORDER for row in build.rows):
        raise ValueError("manifest contains an unsupported contamination status")
    known_reviewed = set(build.humaneval_forensic_ids) | set(build.mbpp_forensic_ids)
    if not set(build.rule_development_paths).issubset(known_reviewed):
        raise ValueError("rule-development manifest contains a task outside reviewed census")


def render_manifest_csv(build: GovernanceBuild) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(build.rows)
    return buffer.getvalue().encode("utf-8")


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_hashes(repo_root: pathlib.Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        (relative_path, sha256_file(_repo_path(repo_root, relative_path)))
        for relative_path in SOURCE_PATHS
    )


def render_summary(
    build: GovernanceBuild,
    *,
    repo_root: pathlib.Path,
    starting_commit: str,
    generated_date: str,
) -> str:
    smoke = set(build.smoke_task_ids)
    forensic_he = set(build.humaneval_forensic_ids)
    overlap = smoke & forensic_he
    excluded = smoke | forensic_he
    unreviewed = len(build.humaneval_task_ids) - len(excluded)
    status_counts = Counter(row["contamination_status"] for row in build.rows)

    lines = [
        "# Public Benchmark Contamination Summary",
        "",
        f"- Generated: {generated_date} (Asia/Taipei)",
        f"- Starting Git commit: `{starting_commit}`",
        "- Milestone: 0A data-governance inventory only",
        "",
        "## Dataset versions",
        "",
        "| Dataset | Version evidence | Manifest status |",
        "|---|---|---|",
        (
            f"| HumanEval+ | release `{build.humaneval_metadata.get('release_tag_or_dataset_version')}`; "
            f"EvalPlus `{build.humaneval_metadata.get('evalplus_package_version')}` | complete, 164 tasks |"
        ),
        (
            "| MBPP+ | targeted replay records reference `v0.2.0` | "
            + (f"complete, {build.mbpp_total} tasks |" if build.mbpp_total is not None else "complete task manifest unavailable |")
        ),
        "",
        "## Repository evidence and SHA-256",
        "",
        "| Repository path | SHA-256 |",
        "|---|---|",
    ]
    for relative_path, digest in source_hashes(repo_root):
        lines.append(f"| `{relative_path}` | `{digest}` |")

    lines.extend(
        [
            "",
            "## HumanEval+ counts",
            "",
            "| Measure | Count |",
            "|---|---:|",
            f"| Total tasks | {len(build.humaneval_task_ids)} |",
            f"| Engineering smoke, official first-N | {len(smoke)} |",
            f"| Forensic reviewed unique | {len(forensic_he)} |",
            f"| Smoke/forensic overlap | {len(overlap)} |",
            f"| Excluded union | {len(excluded)} |",
            f"| Unreviewed candidate | {unreviewed} |",
            "",
            "Overlap IDs: `HumanEval/10`, `HumanEval/19`.",
            "",
            "The 108 remaining HumanEval+ tasks are `unreviewed_candidate` with "
            "`confirmatory_eligible=pending`; they are not a formal confirmatory set.",
            "",
            "## MBPP+ counts",
            "",
            "| Measure | Count |",
            "|---|---:|",
            f"| Forensic reviewed unique | {len(build.mbpp_forensic_ids)} |",
            f"| Total tasks | {build.mbpp_total if build.mbpp_total is not None else 'unavailable'} |",
            "",
            "All 116 listed MBPP+ rows are individually reviewed failure-census sources and "
            "have `confirmatory_eligible=false`.",
            "",
            "## Contamination status counts",
            "",
            "| Status | Count |",
            "|---|---:|",
        ]
    )
    for status in STATUS_ORDER:
        lines.append(f"| `{status}` | {status_counts.get(status, 0)} |")

    lines.extend(
        [
            "",
            "## Governance statements",
            "",
            "- This milestone does not establish a formal development, validation, or confirmatory split.",
            "- `unreviewed_candidate` does not mean confirmatory or clean.",
            "- `generated_only` is not automatically treated as individual contamination.",
            "- Formal task eligibility must be decided by the next milestone.",
            "- No row in this manifest has `confirmatory_eligible=true`.",
            "",
            "## Limitations",
            "",
            "- The repository contains no reliable complete MBPP/MBPP+ task manifest, so MBPP+ total and remaining-task counts are unavailable and are not inferred.",
            "- Repository evidence cannot prove that an apparently unreviewed task was never generated or viewed elsewhere; lower-level history is therefore `unknown` for unreviewed candidates.",
            "- Rule-development attribution is limited to task IDs directly present in the structured candidate/replay manifests listed above.",
            "- The inventory does not inspect new model outputs, task solutions, cloud-drive history, or formal EvalPlus results.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_head(repo_root: pathlib.Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument(
        "--manifest-out",
        type=pathlib.Path,
        default=REPO_ROOT / "artifacts/public_benchmark_governance/contamination_manifest.csv",
    )
    parser.add_argument(
        "--summary-out",
        type=pathlib.Path,
        default=REPO_ROOT / "artifacts/public_benchmark_governance/contamination_summary.md",
    )
    parser.add_argument("--starting-commit", default=None)
    parser.add_argument("--generated-date", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    build = build_governance(repo_root)
    starting_commit = args.starting_commit or _git_head(repo_root)
    generated_date = args.generated_date or dt.datetime.now(
        ZoneInfo("Asia/Taipei")
    ).date().isoformat()

    manifest_bytes = render_manifest_csv(build)
    summary = render_summary(
        build,
        repo_root=repo_root,
        starting_commit=starting_commit,
        generated_date=generated_date,
    )
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_bytes(manifest_bytes)
    args.summary_out.write_bytes(summary.encode("utf-8"))
    print(
        json.dumps(
            {
                "manifest": str(args.manifest_out),
                "rows": len(build.rows),
                "summary": str(args.summary_out),
                "starting_commit": starting_commit,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
