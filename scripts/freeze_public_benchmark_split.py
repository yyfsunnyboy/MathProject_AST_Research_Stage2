#!/usr/bin/env python3
"""Freeze the public-benchmark split after researcher attestation."""

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

ATTESTATION_DATE = "2026-07-16"
ATTESTATION_SCOPE = "project-process contamination"
ATTESTATION_TEXT = (
    "「我確認研究團隊未在 repository 之外逐題檢視 108 題 HumanEval+ external candidates "
    "與 60 題 MBPP+ internal candidates 的題目內容、答案、測試或模型輸出，也未利用這些題目建置或修改 "
    "Scaffold／Healer。已知的只有資料集名稱、題數、task ID 與治理欄位。先前執行過的題目僅限 "
    "contamination manifest 已記錄並排除的歷史題目。」"
)

CONTAMINATION_MANIFEST = (
    "artifacts/public_benchmark_governance/contamination_manifest.csv"
)
SPLIT_PROPOSAL = "artifacts/public_benchmark_governance/split_proposal.csv"
ATTESTATION = "artifacts/public_benchmark_governance/researcher_attestation.md"
DATASET_MANIFESTS = {
    "HumanEval+": "data/humaneval_plus/dataset_manifest.json",
    "MBPP+": "data/mbpp_plus/dataset_manifest.json",
}

CONFIRMATORY_ROLES = {
    "external_confirmatory_candidate",
    "internal_confirmatory_candidate",
}

CSV_FIELDS = (
    "dataset",
    "dataset_version",
    "task_id",
    "task_numeric_id",
    "source_contamination_classification",
    "source_contamination_status",
    "selection_hash",
    "selection_rank_within_pool",
    "proposed_role",
    "active_development_generation_subset",
    "proposal_formal_status",
    "proposal_requires_manual_attestation",
    "split_assignment_status",
    "confirmatory_eligible",
    "project_contamination_status",
    "attestation_date",
    "attestation_scope",
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
class FrozenSplitBuild:
    rows: tuple[dict[str, str], ...]


def _repo_path(repo_root: pathlib.Path, relative_path: str) -> pathlib.Path:
    return repo_root / pathlib.PurePosixPath(relative_path)


def _read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _validate_attestation(repo_root: pathlib.Path) -> None:
    text = _repo_path(repo_root, ATTESTATION).read_text(encoding="utf-8")
    required = (
        ATTESTATION_TEXT,
        f"attestation_date: `{ATTESTATION_DATE}`",
        f"scope: `{ATTESTATION_SCOPE}`",
        "model pretraining",
        "must not be overwritten",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise ValueError(f"researcher attestation is incomplete: {missing}")


def _dataset_versions(repo_root: pathlib.Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for dataset, relative_path in DATASET_MANIFESTS.items():
        metadata = json.loads(_repo_path(repo_root, relative_path).read_text(encoding="utf-8"))
        if metadata.get("dataset_name") != dataset:
            raise ValueError(f"dataset manifest name mismatch for {dataset}")
        version = metadata.get("release_tag_or_dataset_version")
        if not isinstance(version, str) or not version:
            raise ValueError(f"dataset version missing for {dataset}")
        versions[dataset] = version
    return versions


def build_frozen_split(repo_root: pathlib.Path = REPO_ROOT) -> FrozenSplitBuild:
    repo_root = repo_root.resolve()
    _validate_attestation(repo_root)
    versions = _dataset_versions(repo_root)
    contamination_rows = _read_csv(_repo_path(repo_root, CONTAMINATION_MANIFEST))
    proposal_rows = _read_csv(_repo_path(repo_root, SPLIT_PROPOSAL))

    contamination_by_key = {
        (row["dataset"], row["task_id"]): row for row in contamination_rows
    }
    proposal_keys = [(row["dataset"], row["task_id"]) for row in proposal_rows]
    if len(contamination_rows) != 542 or len(proposal_rows) != 542:
        raise ValueError("freeze sources must each contain 542 rows")
    if len(contamination_by_key) != 542 or len(set(proposal_keys)) != 542:
        raise ValueError("freeze sources must contain 542 unique dataset/task keys")
    if set(contamination_by_key) != set(proposal_keys):
        raise ValueError("contamination and proposal task keys do not match")

    frozen: list[dict[str, str]] = []
    for proposal in proposal_rows:
        key = (proposal["dataset"], proposal["task_id"])
        contamination = contamination_by_key[key]
        if proposal["dataset_version"] != versions[proposal["dataset"]]:
            raise ValueError(f"proposal dataset version mismatch for {key}")
        source_status = contamination["confirmatory_eligible"]
        if source_status not in {"false", "pending"}:
            raise ValueError(f"unsupported source contamination status for {key}")
        eligible = proposal["proposed_role"] in CONFIRMATORY_ROLES
        if eligible and source_status != "pending":
            raise ValueError(f"confirmatory candidate was not pending attestation: {key}")
        frozen.append(
            {
                "dataset": proposal["dataset"],
                "dataset_version": proposal["dataset_version"],
                "task_id": proposal["task_id"],
                "task_numeric_id": proposal["task_numeric_id"],
                "source_contamination_classification": contamination[
                    "contamination_status"
                ],
                "source_contamination_status": source_status,
                "selection_hash": proposal["selection_hash"],
                "selection_rank_within_pool": proposal[
                    "selection_rank_within_pool"
                ],
                "proposed_role": proposal["proposed_role"],
                "active_development_generation_subset": proposal[
                    "active_development_generation_subset"
                ],
                "proposal_formal_status": proposal["formal_status"],
                "proposal_requires_manual_attestation": proposal[
                    "requires_manual_attestation"
                ],
                "split_assignment_status": "frozen",
                "confirmatory_eligible": "true" if eligible else "false",
                "project_contamination_status": (
                    "attested_no_project_exposure"
                    if eligible
                    else "not_applicable_non_confirmatory"
                ),
                "attestation_date": ATTESTATION_DATE,
                "attestation_scope": ATTESTATION_SCOPE,
            }
        )

    build = FrozenSplitBuild(rows=tuple(frozen))
    validate_frozen_split(build)
    return build


def validate_frozen_split(build: FrozenSplitBuild) -> None:
    if len(build.rows) != 542:
        raise ValueError("frozen split must contain 542 rows")
    keys = [(row["dataset"], row["task_id"]) for row in build.rows]
    if len(keys) != len(set(keys)):
        raise ValueError("frozen split must contain unique dataset/task keys")
    if any(row["split_assignment_status"] != "frozen" for row in build.rows):
        raise ValueError("all split assignments must be frozen")
    role_counts = Counter(row["proposed_role"] for row in build.rows)
    if role_counts != Counter(EXPECTED_ROLE_COUNTS):
        raise ValueError(f"frozen role counts differ from proposal: {dict(role_counts)}")
    eligible = [row for row in build.rows if row["confirmatory_eligible"] == "true"]
    if len(eligible) != 168:
        raise ValueError("frozen split must contain 168 confirmatory tasks")
    eligible_counts = Counter(row["dataset"] for row in eligible)
    if eligible_counts != Counter({"HumanEval+": 108, "MBPP+": 60}):
        raise ValueError(f"unexpected confirmatory dataset counts: {dict(eligible_counts)}")
    if any(row["proposed_role"] not in CONFIRMATORY_ROLES for row in eligible):
        raise ValueError("non-candidate role was marked confirmatory eligible")
    if any(
        row["project_contamination_status"] != "attested_no_project_exposure"
        for row in eligible
    ):
        raise ValueError("confirmatory tasks lack attested project status")
    if sum(row["confirmatory_eligible"] == "false" for row in build.rows) != 374:
        raise ValueError("frozen split must contain 374 non-confirmatory tasks")


def render_frozen_csv(build: FrozenSplitBuild) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(build.rows)
    return buffer.getvalue().encode("utf-8")


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_summary(
    build: FrozenSplitBuild,
    *,
    repo_root: pathlib.Path,
    starting_commit: str,
    generated_date: str,
) -> str:
    role_counts = Counter(row["proposed_role"] for row in build.rows)
    eligible = [row for row in build.rows if row["confirmatory_eligible"] == "true"]
    eligible_counts = Counter(row["dataset"] for row in eligible)
    source_paths = (
        CONTAMINATION_MANIFEST,
        SPLIT_PROPOSAL,
        ATTESTATION,
        *DATASET_MANIFESTS.values(),
    )
    lines = [
        "# Frozen Public Benchmark Split",
        "",
        f"- Generated: {generated_date} (Asia/Taipei)",
        f"- Starting Git commit: `{starting_commit}`",
        f"- Attestation date: `{ATTESTATION_DATE}`",
        f"- Attestation scope: `{ATTESTATION_SCOPE}`",
        "- Split assignment status: `frozen`",
        "",
        "## Source evidence",
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
            "## Frozen counts",
            "",
            "| Measure | Count |",
            "|---|---:|",
            f"| Total unique tasks | {len(build.rows)} |",
            f"| Frozen assignments | {sum(row['split_assignment_status'] == 'frozen' for row in build.rows)} |",
            f"| Confirmatory eligible | {len(eligible)} |",
            f"| HumanEval+ confirmatory | {eligible_counts['HumanEval+']} |",
            f"| MBPP+ confirmatory | {eligible_counts['MBPP+']} |",
            f"| Non-confirmatory | {sum(row['confirmatory_eligible'] == 'false' for row in build.rows)} |",
            "",
            "## Roles preserved from proposal",
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
            "Only the 108 HumanEval+ external candidates and 60 MBPP+ internal candidates are `confirmatory_eligible=true`; validation, reserve, historical development, and excluded tasks remain false.",
            "",
            "The original pre-attestation `pending/false` value is preserved as `source_contamination_status`. Selection hashes, ranks, and proposed roles are unchanged from `split_proposal.csv`.",
            "",
            "## Scope and limitations",
            "",
            "- The attestation establishes no known project-process exposure for the 168 confirmatory tasks.",
            "- It cannot establish whether model pretraining encountered these public benchmarks.",
            "- The original contamination manifest and split proposal remain immutable source evidence and are not overwritten.",
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
        default=REPO_ROOT / "artifacts/public_benchmark_governance/frozen_split.csv",
    )
    parser.add_argument(
        "--summary-out",
        type=pathlib.Path,
        default=REPO_ROOT / "artifacts/public_benchmark_governance/frozen_split_summary.md",
    )
    parser.add_argument("--starting-commit", default=None)
    parser.add_argument("--generated-date", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    build = build_frozen_split(repo_root)
    starting_commit = args.starting_commit or _git_head(repo_root)
    generated_date = args.generated_date or dt.datetime.now(
        ZoneInfo("Asia/Taipei")
    ).date().isoformat()
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.write_bytes(render_frozen_csv(build))
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
                "confirmatory_eligible": sum(
                    row["confirmatory_eligible"] == "true" for row in build.rows
                ),
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
