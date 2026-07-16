#!/usr/bin/env python3
"""Build a deterministic public-benchmark split proposal from governance data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import subprocess
from collections import Counter
from dataclasses import dataclass
from zoneinfo import ZoneInfo

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

SPLIT_VERSION = "public_benchmark_split_proposal_v1"
SALT = "2026-07-16|e6201938b824f96429fdbf35db02fad2291dc024"
CONTAMINATION_MANIFEST = (
    "artifacts/public_benchmark_governance/contamination_manifest.csv"
)
DATASET_MANIFESTS = {
    "HumanEval+": "data/humaneval_plus/dataset_manifest.json",
    "MBPP+": "data/mbpp_plus/dataset_manifest.json",
}

CSV_FIELDS = (
    "dataset",
    "dataset_version",
    "task_id",
    "task_numeric_id",
    "contamination_status",
    "selection_hash",
    "selection_rank_within_pool",
    "proposed_role",
    "active_development_generation_subset",
    "formal_status",
    "requires_manual_attestation",
)

EXPECTED_ROLE_COUNTS = {
    "excluded_historical": 56,
    "external_confirmatory_candidate": 108,
    "historical_development_pool": 116,
    "validation": 20,
    "internal_confirmatory_candidate": 60,
    "sealed_reserve": 182,
}


@dataclass(frozen=True)
class SplitProposalBuild:
    rows: tuple[dict[str, str], ...]
    dataset_versions: dict[str, str]


def _repo_path(repo_root: pathlib.Path, relative_path: str) -> pathlib.Path:
    return repo_root / pathlib.PurePosixPath(relative_path)


def selection_hash(
    *, dataset: str, dataset_version: str, task_id: str
) -> str:
    payload = "|".join(
        (SPLIT_VERSION, dataset, dataset_version, task_id, SALT)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_dataset_versions(repo_root: pathlib.Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for dataset, relative_path in DATASET_MANIFESTS.items():
        metadata = json.loads(_repo_path(repo_root, relative_path).read_text(encoding="utf-8"))
        if metadata.get("dataset_name") != dataset:
            raise ValueError(f"dataset manifest name mismatch for {dataset}")
        version = metadata.get("release_tag_or_dataset_version")
        if not isinstance(version, str) or not version:
            raise ValueError(f"dataset manifest has no version for {dataset}")
        versions[dataset] = version
    return versions


def _load_governance_rows(repo_root: pathlib.Path) -> list[dict[str, str]]:
    path = _repo_path(repo_root, CONTAMINATION_MANIFEST)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "dataset",
        "task_id",
        "task_numeric_id",
        "contamination_status",
        "confirmatory_eligible",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("contamination manifest is missing required governance fields")
    if any(row["confirmatory_eligible"] not in {"false", "pending"} for row in rows):
        raise ValueError("split proposal source contains an unsupported eligibility value")
    if any(row["confirmatory_eligible"] == "true" for row in rows):
        raise ValueError("split proposal source must not contain confirmatory_eligible=true")
    task_keys = [(row["dataset"], row["task_id"]) for row in rows]
    if len(task_keys) != len(set(task_keys)):
        raise ValueError("contamination manifest contains duplicate dataset/task IDs")
    return rows


def _base_row(
    source: dict[str, str], dataset_version: str
) -> dict[str, str]:
    return {
        "dataset": source["dataset"],
        "dataset_version": dataset_version,
        "task_id": source["task_id"],
        "task_numeric_id": source["task_numeric_id"],
        "contamination_status": source["contamination_status"],
        "selection_hash": selection_hash(
            dataset=source["dataset"],
            dataset_version=dataset_version,
            task_id=source["task_id"],
        ),
    }


def _rank_pool(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ranked = sorted(rows, key=lambda row: row["selection_hash"])
    for rank, row in enumerate(ranked, 1):
        row["selection_rank_within_pool"] = str(rank)
    return ranked


def _finish_row(
    row: dict[str, str],
    *,
    proposed_role: str,
    active_development: bool = False,
    requires_attestation: bool = False,
) -> dict[str, str]:
    row["proposed_role"] = proposed_role
    row["active_development_generation_subset"] = (
        "true" if active_development else "false"
    )
    row["formal_status"] = (
        "awaiting_manual_attestation" if requires_attestation else "proposal_only"
    )
    row["requires_manual_attestation"] = (
        "true" if requires_attestation else "false"
    )
    return row


def build_split_proposal(
    repo_root: pathlib.Path = REPO_ROOT,
) -> SplitProposalBuild:
    repo_root = repo_root.resolve()
    versions = _load_dataset_versions(repo_root)
    source_rows = _load_governance_rows(repo_root)

    by_dataset = {
        dataset: [row for row in source_rows if row["dataset"] == dataset]
        for dataset in DATASET_MANIFESTS
    }
    if len(by_dataset["HumanEval+"]) != 164 or len(by_dataset["MBPP+"]) != 378:
        raise ValueError("unexpected dataset totals in contamination manifest")

    output: list[dict[str, str]] = []

    he_excluded = _rank_pool(
        [
            _base_row(row, versions["HumanEval+"])
            for row in by_dataset["HumanEval+"]
            if row["confirmatory_eligible"] == "false"
        ]
    )
    output.extend(
        _finish_row(row, proposed_role="excluded_historical")
        for row in he_excluded
    )

    he_pending = _rank_pool(
        [
            _base_row(row, versions["HumanEval+"])
            for row in by_dataset["HumanEval+"]
            if row["confirmatory_eligible"] == "pending"
        ]
    )
    output.extend(
        _finish_row(
            row,
            proposed_role="external_confirmatory_candidate",
            requires_attestation=True,
        )
        for row in he_pending
    )

    mbpp_historical = _rank_pool(
        [
            _base_row(row, versions["MBPP+"])
            for row in by_dataset["MBPP+"]
            if row["confirmatory_eligible"] == "false"
        ]
    )
    output.extend(
        _finish_row(
            row,
            proposed_role="historical_development_pool",
            active_development=rank <= 20,
        )
        for rank, row in enumerate(mbpp_historical, 1)
    )

    mbpp_pending = _rank_pool(
        [
            _base_row(row, versions["MBPP+"])
            for row in by_dataset["MBPP+"]
            if row["confirmatory_eligible"] == "pending"
        ]
    )
    for rank, row in enumerate(mbpp_pending, 1):
        if rank <= 20:
            output.append(_finish_row(row, proposed_role="validation"))
        elif rank <= 80:
            output.append(
                _finish_row(
                    row,
                    proposed_role="internal_confirmatory_candidate",
                    requires_attestation=True,
                )
            )
        else:
            output.append(_finish_row(row, proposed_role="sealed_reserve"))

    build = SplitProposalBuild(rows=tuple(output), dataset_versions=versions)
    validate_proposal(build)
    return build


def validate_proposal(build: SplitProposalBuild) -> None:
    if len(build.rows) != 542:
        raise ValueError("split proposal must contain 542 rows")
    keys = [(row["dataset"], row["task_id"]) for row in build.rows]
    if len(keys) != len(set(keys)):
        raise ValueError("each dataset/task ID must appear exactly once")
    role_counts = Counter(row["proposed_role"] for row in build.rows)
    if role_counts != Counter(EXPECTED_ROLE_COUNTS):
        raise ValueError(f"unexpected proposed-role counts: {dict(role_counts)}")
    active = [
        row
        for row in build.rows
        if row["active_development_generation_subset"] == "true"
    ]
    if len(active) != 20 or any(
        row["proposed_role"] != "historical_development_pool" for row in active
    ):
        raise ValueError("active development generation subset must be 20 historical MBPP+ tasks")
    if any(row["formal_status"] == "frozen" for row in build.rows):
        raise ValueError("proposal must not freeze any task")
    if any(len(row["selection_hash"]) != 64 for row in build.rows):
        raise ValueError("selection hash must be full SHA-256 hex")
    candidates = {
        "external_confirmatory_candidate",
        "internal_confirmatory_candidate",
    }
    for row in build.rows:
        expected = row["proposed_role"] in candidates
        if (row["requires_manual_attestation"] == "true") != expected:
            raise ValueError("manual-attestation flag does not match candidate role")
        if expected and row["formal_status"] != "awaiting_manual_attestation":
            raise ValueError("confirmatory candidates must await manual attestation")


def render_proposal_csv(build: SplitProposalBuild) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(build.rows)
    return buffer.getvalue().encode("utf-8")


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_summary(
    build: SplitProposalBuild,
    *,
    repo_root: pathlib.Path,
    starting_commit: str,
    generated_date: str,
) -> str:
    role_counts = Counter(row["proposed_role"] for row in build.rows)
    source_paths = (CONTAMINATION_MANIFEST, *DATASET_MANIFESTS.values())
    lines = [
        "# Public Benchmark Deterministic Split Proposal",
        "",
        f"- Generated: {generated_date} (Asia/Taipei)",
        f"- Starting Git commit: `{starting_commit}`",
        f"- Split version: `{SPLIT_VERSION}`",
        f"- Salt: `{SALT}`",
        "- Status: proposal only; no formal confirmatory set is frozen",
        "",
        "## Deterministic selection",
        "",
        "Each task is ordered by the full ascending SHA-256 of:",
        "",
        "`split_version|dataset|dataset_version|task_id|salt`",
        "",
        "No prompt, model output, answer, test, Python built-in hash, or manual task selection is used.",
        "",
        "## Source files",
        "",
        "| Repository path | SHA-256 |",
        "|---|---|",
    ]
    for relative_path in source_paths:
        lines.append(
            f"| `{relative_path}` | `{_sha256_file(_repo_path(repo_root, relative_path))}` |"
        )
    lines.extend(
        [
            "",
            "## Proposed roles",
            "",
            "| Proposed role | Count |",
            "|---|---:|",
        ]
    )
    for role in EXPECTED_ROLE_COUNTS:
        lines.append(f"| `{role}` | {role_counts[role]} |")
    lines.extend(
        [
            "",
            "The historical MBPP+ development pool contains 116 tasks; its first 20 by selection hash are marked `active_development_generation_subset=true`.",
            "",
            "All 108 HumanEval+ external candidates and 60 MBPP+ internal candidates have `formal_status=awaiting_manual_attestation`. None is frozen or formally confirmatory.",
            "",
            "## Governance limits",
            "",
            "- This artifact is a deterministic grouping proposal, not a frozen development/validation/confirmatory split.",
            "- No row has `formal_status=frozen` or `confirmatory_eligible=true`.",
            "- Manual attestation remains required before either candidate pool can receive any formal status.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_head(repo_root: pathlib.Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument(
        "--csv-out",
        type=pathlib.Path,
        default=REPO_ROOT / "artifacts/public_benchmark_governance/split_proposal.csv",
    )
    parser.add_argument(
        "--summary-out",
        type=pathlib.Path,
        default=REPO_ROOT / "artifacts/public_benchmark_governance/split_proposal_summary.md",
    )
    parser.add_argument("--starting-commit", default=None)
    parser.add_argument("--generated-date", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    build = build_split_proposal(repo_root)
    starting_commit = args.starting_commit or _git_head(repo_root)
    generated_date = args.generated_date or dt.datetime.now(
        ZoneInfo("Asia/Taipei")
    ).date().isoformat()
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.write_bytes(render_proposal_csv(build))
    args.summary_out.write_bytes(
        render_summary(
            build,
            repo_root=repo_root,
            starting_commit=starting_commit,
            generated_date=generated_date,
        ).encode("utf-8")
    )
    print(
        json.dumps(
            {
                "rows": len(build.rows),
                "csv": str(args.csv_out),
                "summary": str(args.summary_out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
