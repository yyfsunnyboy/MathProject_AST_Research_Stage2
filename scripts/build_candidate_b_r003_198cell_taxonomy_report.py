from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
START_HEAD = "00c39eb070c74005f98126ec87a620bcf873c1e6"
REVISION = "candidate_b_r003_taxonomy_v31_complete_198cell_research_report_v1"
VERDICT = "READY_FOR_198CELL_REPORT_INDEPENDENT_AUDIT"

REPORT_PATH = Path(
    "docs/experiments/reports/"
    "Candidate_B_r003_198格失敗分類與Healer安全邊界統整報告.md"
)
SUMMARY_PATH = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_complete_198cell_research_report_v1/"
    "summary.json"
)
BUILDER_PATH = Path("scripts/build_candidate_b_r003_198cell_taxonomy_report.py")

TAXONOMY = Path(
    "C:/Users/yehya/Downloads/"
    "AI_生成程式共同失敗分類標準_實際使用版_v3.1.md"
)
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)
ACCOUNTS = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r003/"
    "h0_h1_accounts.jsonl"
)
COMPLETE_LEDGER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/"
    "complete_cumulative_frozen_identity_ledger.csv"
)
COMPLETE_MANIFEST = COMPLETE_LEDGER.with_name("manifest.json")


RECORD_SPECS: tuple[dict[str, Any], ...] = (
    {
        "batch": "legacy_g2_module_27",
        "kind": "g2",
        "cells": 27,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_g2_module_researcher_review_v1/"
            "researcher_review_worksheet.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_g2_module_researcher_review_v1/"
            "manifest.json"
        ),
    },
    {
        "batch": "legacy_module_exception_37",
        "kind": "legacy_provisional",
        "cells": 37,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining171_"
            "module_exception_provisional_v1/ai_provisional_adjudication.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining171_"
            "module_exception_provisional_v1/manifest.json"
        ),
    },
    {
        "batch": "legacy_multiple_signal_13",
        "kind": "legacy_provisional",
        "cells": 13,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining134_"
            "multiple_signal_chain13_provisional_v1/ai_provisional_adjudication.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining134_"
            "multiple_signal_chain13_provisional_v1/manifest.json"
        ),
    },
    {
        "batch": "legacy_output_contract_shape_20",
        "kind": "legacy_frozen",
        "cells": 20,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining121_"
            "output_contract_shape20_frozen_v1/frozen_adjudication.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v3_remaining121_"
            "output_contract_shape20_frozen_v1/manifest.json"
        ),
    },
    {
        "batch": "batch01",
        "kind": "batch",
        "cells": 20,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_remaining101_"
            "batch01_20cell_frozen_v1/frozen_adjudication.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_remaining101_"
            "batch01_20cell_frozen_v1/manifest.json"
        ),
    },
    {
        "batch": "batch02",
        "kind": "batch",
        "cells": 20,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/"
            "frozen_adjudication.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch02_20cell_frozen_v1/"
            "manifest.json"
        ),
    },
    {
        "batch": "batch03",
        "kind": "batch",
        "cells": 20,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/"
            "frozen_adjudication_records.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1/"
            "manifest.json"
        ),
    },
    {
        "batch": "batch04",
        "kind": "batch",
        "cells": 20,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/"
            "frozen_adjudication_records.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_batch04_20cell_frozen_v1/"
            "manifest.json"
        ),
    },
    {
        "batch": "final_batch05",
        "kind": "batch",
        "cells": 21,
        "path": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_final_batch05_21cell_frozen_v1/"
            "frozen_adjudication_records.csv"
        ),
        "manifest": Path(
            "artifacts/public_benchmark_governance/"
            "candidate_b_r003_taxonomy_v31_final_batch05_21cell_frozen_v1/"
            "manifest.json"
        ),
    },
)


AUTHORITY_HASHES: dict[Path, str] = {
    TAXONOMY: "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    COMPLETE_LEDGER: "7d18c8a04ef47ae3725feeb84636ec2f6fe46490367010851003618db1622bd3",
    COMPLETE_MANIFEST: "749f19fb4464d1a17536d2fd55beae2e0771bdec72a8ddaf92b1364d8ea59b66",
    RECORD_SPECS[0]["path"]: "38694d644d7916aa14a716bfbfdbdb1eaed4b1c2557865bde3aee1d215d2b820",
    RECORD_SPECS[0]["manifest"]: "5e4c7d7c8704902086533cfba8d70b6a7d1382c303687e505481cfc456e68f53",
    RECORD_SPECS[1]["path"]: "8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7",
    RECORD_SPECS[1]["manifest"]: "72b02ab7da59e65db2d5e09cee9344c3d52940a717ea3dfea05310e0529d76c1",
    RECORD_SPECS[2]["path"]: "dc2e7202c048400d32e019fed6940051f65ca1a67b865727152d94dccf302d70",
    RECORD_SPECS[2]["manifest"]: "fd26fdbd103ad216e2a38c8e16b839c9e2b72a242e360713edee8d7762f59336",
    RECORD_SPECS[3]["path"]: "eda69f61051228ff9d976ec57f6dcd9febea95a2c541095edac19f55074eac1f",
    RECORD_SPECS[3]["manifest"]: "a9bc5d19e4a4aa4d3fde4db23a296cb1b2d32b9e51c6ebe9ace5c548691f8eab",
    RECORD_SPECS[4]["path"]: "8f2410122205610f41d4e7dfbbc4b958d05c1e3da40176b9dc9269880512c0cb",
    RECORD_SPECS[4]["manifest"]: "8cbed23b396ba7149fac485abf30160327ad6b483166ca22cccb3a6e1e4210ae",
    RECORD_SPECS[5]["path"]: "dc6d4a4fa0f0027eb87e3af48b3567c72443255fcda2e2779acf7fe0fbf70f04",
    RECORD_SPECS[5]["manifest"]: "41f8f76edf2669ee37494a03cf9d05ec0464bb7379d6ada58a6e2921fbeafee6",
    RECORD_SPECS[6]["path"]: "d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",
    RECORD_SPECS[6]["manifest"]: "af9becc880d45e6969074cf5e2e53e47a3b87b4cbf6a6ecab0cb4b69963f51d9",
    RECORD_SPECS[7]["path"]: "03cf83d8f295815f5f5f66dbdc3eb347556606245e542d052d88d0a50d945028",
    RECORD_SPECS[7]["manifest"]: "b56f1796c9b97bdbb854a5699dcdce38326c26300d9ad7bb8411c9d0499e5ea4",
    RECORD_SPECS[8]["path"]: "22faba56d483e172064338f2649533e4758bfd1110e64467d8ce6eff2a47cf34",
    RECORD_SPECS[8]["manifest"]: "f7d36575b55bb5dc9c3cb94458b0489c4dfcfa7ff99890927f844d5f56f32b9d",
}


class ReportBuildError(RuntimeError):
    pass


def _path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    return _sha(_path(path).read_bytes())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportBuildError(message)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with _path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in _path(path).read_text(encoding="utf-8").splitlines()
        if line
    ]


def _json_or(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _percent(n: int, denominator: int) -> float | None:
    return round(n * 100.0 / denominator, 1) if denominator else None


def _distribution(
    values: Iterable[str], denominator: int, *, labels: Iterable[str] = ()
) -> dict[str, dict[str, int | float | None]]:
    counter = Counter(values)
    ordered = list(dict.fromkeys([*labels, *sorted(counter)]))
    return {
        label: {"n": counter.get(label, 0), "percent": _percent(counter.get(label, 0), denominator)}
        for label in ordered
        if counter.get(label, 0) or label in labels
    }


def verify_authorities() -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for path, expected in AUTHORITY_HASHES.items():
        resolved = _path(path)
        _require(resolved.is_file(), f"missing authority file: {path.as_posix()}")
        actual = _file_sha(path)
        _require(actual == expected, f"authority byte drift: {path.as_posix()}")
        verified.append(
            {
                "path": path.as_posix(),
                "sha256": actual,
                "byte_verified": True,
            }
        )
    return verified


def _benchmark(task_id: str) -> str:
    lowered = task_id.lower()
    if lowered.startswith("mbpp/"):
        return "MBPP+"
    if lowered.startswith("humaneval/"):
        return "HumanEval+"
    return "OTHER_OR_UNKNOWN"


def _secondary(value: str) -> list[str]:
    parsed = _json_or(value, None)
    if isinstance(parsed, list):
        return sorted({str(item) for item in parsed if str(item)})
    return [value] if value else []


def _active_mechanisms(value: str) -> tuple[list[str], dict[str, str]]:
    parsed = _json_or(value, None)
    if not isinstance(parsed, list):
        return ([value] if value else []), ({value: "LEGACY_ACTIVE"} if value else {})
    active: set[str] = set()
    statuses: dict[str, str] = {}
    for item in parsed:
        if isinstance(item, str):
            active.add(item)
            statuses[item] = "LEGACY_ACTIVE"
            continue
        if not isinstance(item, dict) or not item.get("tag"):
            continue
        tag = str(item["tag"])
        status = str(item.get("status") or item.get("strength") or "ACTIVE").upper()
        statuses[tag] = status
        if status != "REJECTED":
            active.add(tag)
    return sorted(active), statuses


def _chain_node_count(value: str) -> int:
    parsed = _json_or(value, None)
    if isinstance(parsed, list):
        return len(parsed)
    if not value.strip():
        return 0
    return len([part for part in value.split("→") if part.strip()])


def _chain_pattern(primary: str, secondary: list[str]) -> str:
    if secondary:
        return f"{primary} + secondary {'/'.join(secondary)}"
    return primary


def _normalize_record(
    row: dict[str, str],
    spec: dict[str, Any],
    prep: dict[str, dict[str, str]],
    h0_accounts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    kind = spec["kind"]
    program_id = row["program_id"]
    _require(program_id in prep, f"program missing from preparation: {program_id}")
    _require(program_id in h0_accounts, f"program missing H0 account: {program_id}")
    meta = prep[program_id]
    account = h0_accounts[program_id]

    if kind == "g2":
        _require(
            row["researcher_review_status"] == "ACCEPT",
            f"unsupported non-ACCEPT G2 row: {program_id}",
        )
        primary = row["ai_proposed_primary_failure_layer"]
        secondary_raw = row["ai_proposed_secondary_failure_layers"]
        mechanisms_raw = row["ai_mechanism_tags"]
        chain = row["ai_failure_chain"]
        outcome = row["ai_outcome_validity"]
        healer = row["ai_proposed_healer_eligibility"]
        confidence = row["ai_confidence"]
        reason = row["ai_rationale"]
        evidence = row["evidence_references"]
    elif kind == "legacy_provisional":
        primary = row["provisional_primary_layer"]
        secondary_raw = row["provisional_secondary_layers"]
        mechanisms_raw = row["mechanism_tags"]
        chain = row["failure_chain"]
        outcome = row["outcome_validity"]
        healer = row["healer_eligibility"]
        confidence = row["confidence"]
        reason = (
            row.get("abstain_reason")
            or row.get("unresolved_reason")
            or row.get("evidence_summary")
            or ""
        )
        evidence = row.get("evidence_source_paths", "")
    elif kind == "legacy_frozen":
        primary = row["primary_layer"]
        secondary_raw = row["secondary_layers"]
        mechanisms_raw = row["mechanism_tags"]
        chain = row["failure_chain"]
        outcome = row["outcome_validity"]
        healer = row["healer_eligibility"]
        confidence = row["confidence"]
        reason = row["abstain_reason"]
        evidence = row["evidence_citations"]
    else:
        primary = row["primary_layer"]
        secondary_raw = row.get("secondary_layer", "")
        mechanisms_raw = row["mechanism_tags_json"]
        chain = row["failure_chain"]
        outcome = row["outcome_validity"]
        healer = row["healer_eligibility"]
        confidence = row["confidence"]
        reason = (
            row.get("reason")
            or row.get("eligibility_reason")
            or row.get("abstain_reason")
            or row.get("unresolved_reason_code")
            or ""
        )
        evidence = row.get("evidence_citations", "")

    cell_id = (
        row.get("cell_identity_sha256")
        or row.get("cell_id")
        or meta["cell_identity_sha256"]
    )
    source_sha = row.get("source_sha256") or meta["evaluation_source_sha256"]
    task_id = row.get("task_id") or meta["task_id"]
    seed = row.get("seed") or meta["seed"]
    condition = row.get("condition") or "Candidate_B/H0"
    _require(
        account["healer_account"] == "H0",
        f"non-H0 authority account selected: {program_id}",
    )
    _require(
        condition in {"Candidate_B/H0", "Candidate_B_H0"},
        f"unexpected frozen condition: {condition}",
    )
    condition = "Candidate_B/H0"
    mechanisms, mechanism_statuses = _active_mechanisms(mechanisms_raw)
    secondary = _secondary(secondary_raw)
    return {
        "batch": spec["batch"],
        "program_id": program_id,
        "cell_identity_sha256": cell_id,
        "source_sha256": source_sha,
        "task_id": task_id,
        "benchmark": _benchmark(task_id),
        "seed": str(seed),
        "condition": condition,
        "model_run": str(account["run_id"]),
        "scaffold_like": "NOT_RECORDED",
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "outcome_validity": outcome,
        "healer": healer,
        "mechanisms": mechanisms,
        "mechanism_statuses": mechanism_statuses,
        "failure_chain": chain,
        "failure_chain_nodes": _chain_node_count(chain),
        "failure_chain_pattern": _chain_pattern(primary, secondary),
        "reason": reason,
        "evidence_citations": evidence,
        "authority_record": spec["path"].as_posix(),
    }


def load_normalized_records() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    authorities = verify_authorities()
    preparation_rows = _read_csv(PREPARATION)
    prep = {row["program_id"]: row for row in preparation_rows}
    h0_accounts = {
        row["program_id"]: row
        for row in _read_jsonl(ACCOUNTS)
        if row.get("healer_account") == "H0"
    }
    ledger = _read_csv(COMPLETE_LEDGER)
    ledger_by_program = {row["program_id"]: row for row in ledger}
    _require(len(prep) == 198, "preparation is not 198 unique programs")
    _require(len(ledger) == len(ledger_by_program) == 198, "ledger program closure failed")

    records: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for spec in RECORD_SPECS:
        rows = _read_csv(spec["path"])
        _require(len(rows) == spec["cells"], f"wrong row count: {spec['batch']}")
        source_counts[spec["batch"]] = len(rows)
        records.extend(_normalize_record(row, spec, prep, h0_accounts) for row in rows)

    _require(len(records) == 198, "normalized record count is not 198")
    by_program = {row["program_id"]: row for row in records}
    by_cell = {row["cell_identity_sha256"]: row for row in records}
    _require(len(by_program) == len(by_cell) == 198, "normalized identity is not unique")
    _require(set(by_program) == set(ledger_by_program), "record/ledger program set mismatch")
    _require(
        set(by_cell) == {row["cell_identity_sha256"] for row in ledger},
        "record/ledger cell set mismatch",
    )
    for program_id, record in by_program.items():
        identity = ledger_by_program[program_id]
        _require(
            record["cell_identity_sha256"] == identity["cell_identity_sha256"],
            f"cell drift: {program_id}",
        )
        _require(
            record["source_sha256"] == identity["source_sha256"],
            f"source drift: {program_id}",
        )
        _require(record["task_id"] == identity["task_id"], f"task drift: {program_id}")

    records.sort(key=lambda row: int(ledger_by_program[row["program_id"]]["freeze_order"]))
    closure = {
        "formal_population": 198,
        "previously_frozen": 177,
        "final_batch05": 21,
        "reconciliation": "198=177+21",
        "unique_program_id": len(by_program),
        "unique_cell_identity": len(by_cell),
        "unique_source_sha256": len({row["source_sha256"] for row in records}),
        "duplicate_programs": 198 - len(by_program),
        "duplicate_cells": 198 - len(by_cell),
        "omissions": len(set(ledger_by_program) - set(by_program)),
        "overlap_frozen177_batch05": 0,
        "remaining": 0,
        "authority_files_verified": len(authorities),
        "batch_cells": source_counts,
    }
    _require(closure["unique_source_sha256"] == 155, "source closure is not 155")
    return records, {"authorities": authorities, "closure": closure}


def _matrix(
    records: list[dict[str, Any]],
    group_key: str,
    outcome_key: str,
    outcome_labels: Iterable[str],
    *,
    group_labels: Iterable[str] = (),
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record[group_key])].append(record)
    result: dict[str, Any] = {}
    labels = list(outcome_labels)
    groups = list(dict.fromkeys([*group_labels, *sorted(grouped)]))
    for group in groups:
        rows = grouped[group]
        counts = Counter(str(row[outcome_key]) for row in rows)
        result[group] = {
            "denominator": len(rows),
            "values": {
                label: {"n": counts[label], "percent": _percent(counts[label], len(rows))}
                for label in labels
            },
        }
    return result


def _mechanism_healer_matrix(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for tag in record["mechanisms"]:
            by_tag[tag].append(record)
    result: dict[str, Any] = {}
    for tag in sorted(by_tag):
        rows = by_tag[tag]
        counts = Counter(row["healer"] for row in rows)
        result[tag] = {
            "denominator": len(rows),
            "values": {
                label: {"n": counts[label], "percent": _percent(counts[label], len(rows))}
                for label in ("eligible", "conditional", "abstain")
            },
        }
    return result


MECHANISM_FAMILY_RULES: dict[str, tuple[str, ...]] = {
    "truncation": ("truncation", "possible_truncation"),
    "entry_point": ("entry_point",),
    "import_or_dependency": ("import", "dependency"),
    "syntax_or_extraction": (
        "syntax",
        "indentation",
        "candidate_extraction",
        "format_contamination",
        "multiple_candidates",
    ),
    "runtime_or_assembly": (
        "runtime",
        "exception",
        "nameerror",
        "undefined",
        "unbound",
        "arity",
        "type_error",
        "missing_return",
        "execution_timeout",
        "nontermination",
        "control_flow",
        "parameter_source",
        "module_level_executable",
    ),
    "semantic_or_algorithm": (
        "algorithm",
        "formula",
        "semantic",
        "boundary",
        "ordering",
        "dedupe",
        "frequency_one",
        "edge_case",
        "predicate",
        "hardcoded",
        "answer_incorrect",
        "mathematical_error",
    ),
}


def _mechanism_families(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for family, needles in MECHANISM_FAMILY_RULES.items():
        matching = [
            row
            for row in records
            if any(any(needle in tag.lower() for needle in needles) for tag in row["mechanisms"])
        ]
        result[family] = {
            "n": len(matching),
            "percent": _percent(len(matching), len(records)),
            "matching_rule": list(needles),
            "non_exclusive": True,
        }
    return result


def _case(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "program_id": record["program_id"],
        "program_id_short": record["program_id"][:12],
        "cell_identity_sha256": record["cell_identity_sha256"],
        "cell_identity_short": record["cell_identity_sha256"][:12],
        "batch": record["batch"],
        "task_id": record["task_id"],
        "primary": record["primary"],
        "secondary": record["secondary"],
        "confidence": record["confidence"],
        "healer": record["healer"],
        "mechanisms": record["mechanisms"],
        "reason": record["reason"],
        "authority_record": record["authority_record"],
    }


def _representative_cases(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    def select(predicate: Any, count: int = 3) -> list[dict[str, Any]]:
        return [_case(row) for row in records if predicate(row)][:count]

    return {
        "eligible": select(lambda row: row["healer"] == "eligible"),
        "conditional": select(lambda row: row["healer"] == "conditional"),
        "abstain": select(lambda row: row["healer"] == "abstain"),
        "algorithm_reconstruction_required": select(
            lambda row: "algorithm_reconstruction_required" in row["mechanisms"]
        ),
        "unresolved": select(lambda row: row["primary"] == "UNRESOLVED"),
        "entry_point": select(
            lambda row: any("entry_point" in tag for tag in row["mechanisms"])
        ),
    }


def build_summary() -> dict[str, Any]:
    records, provenance = load_normalized_records()
    n = len(records)
    secondary_values = [
        layer for record in records for layer in record["secondary"]
    ]
    empty_secondary = sum(not record["secondary"] for record in records)
    mechanism_counts = Counter(
        tag for record in records for tag in record["mechanisms"]
    )
    mechanism_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        for tag, status in record["mechanism_statuses"].items():
            mechanism_status_counts[tag][status] += 1
    stage_buckets = []
    for record in records:
        nodes = record["failure_chain_nodes"]
        stage_buckets.append(
            "0 nodes" if nodes == 0 else "1 node" if nodes == 1 else "2 nodes" if nodes == 2 else "3+ nodes"
        )

    benchmark = _distribution(
        (row["benchmark"] for row in records),
        n,
        labels=("HumanEval+", "MBPP+"),
    )
    condition = _distribution(
        (row["condition"] for row in records),
        n,
        labels=("Candidate_B/H0", "Candidate_B/H1"),
    )
    primary_labels = ("L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED")
    healer_labels = ("eligible", "conditional", "abstain")
    confidence_labels = ("HIGH", "MEDIUM", "LOW")
    outcome_labels = (
        "VALID_MODEL_OUTCOME",
        "INVALID_EVALUATOR",
        "INVALID_CONTRACT",
        "INVALID_INFRASTRUCTURE",
        "PENDING_REVIEW",
    )
    source_groups = Counter(row["source_sha256"] for row in records)
    shared_sources = sorted(
        (
            {
                "source_sha256": source,
                "cells": count,
                "percent_of_cells": _percent(count, n),
            }
            for source, count in source_groups.items()
            if count > 1
        ),
        key=lambda row: (-row["cells"], row["source_sha256"]),
    )

    summary: dict[str, Any] = {
        "revision": REVISION,
        "status": "DETERMINISTIC_REPORT_SUMMARY_BUILT_FROM_FROZEN_RECORDS",
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "method": {
            "unit": "cell/program",
            "percent_rounding": "one_decimal_place",
            "zero_denominator": "NA",
            "mechanism_counting": (
                "每格active mechanism去重；legacy字串視為active；"
                "物件tag只有status/strength非REJECTED才納入已成立機制。"
            ),
            "mechanism_non_exclusive": True,
            "secondary_non_exclusive": True,
            "normalization_without_readjudication": True,
            "scaffold_like_formal_field_available": False,
        },
        "provenance": {
            **provenance,
            "taxonomy_path": TAXONOMY.as_posix(),
            "taxonomy_sha256": AUTHORITY_HASHES[TAXONOMY],
            "builder_path": BUILDER_PATH.as_posix(),
            "builder_sha256": _file_sha(BUILDER_PATH),
            "report_path": REPORT_PATH.as_posix(),
            "summary_path": SUMMARY_PATH.as_posix(),
        },
        "units": {
            "cells": n,
            "programs": len({row["program_id"] for row in records}),
            "sources": len({row["source_sha256"] for row in records}),
            "tasks": len({row["task_id"] for row in records}),
            "shared_source_groups": len(shared_sources),
            "cells_in_shared_source_groups": sum(row["cells"] for row in shared_sources),
            "benchmark": benchmark,
            "condition": condition,
            "seed": _distribution((row["seed"] for row in records), n),
            "model_run": _distribution((row["model_run"] for row in records), n),
            "scaffold_like": {
                "availability": "NOT_RECORDED_IN_FORMAL_FROZEN_RECORDS",
                "recorded_n": 0,
                "unrecorded_n": n,
                "comparison_permitted": False,
            },
            "shared_sources": shared_sources,
        },
        "distributions": {
            "primary": _distribution(
                (row["primary"] for row in records), n, labels=primary_labels
            ),
            "secondary": {
                "denominator": n,
                "empty": {"n": empty_secondary, "percent": _percent(empty_secondary, n)},
                "layers": _distribution(secondary_values, n),
                "non_exclusive": True,
            },
            "confidence": _distribution(
                (row["confidence"] for row in records), n, labels=confidence_labels
            ),
            "outcome_validity": _distribution(
                (row["outcome_validity"] for row in records), n, labels=outcome_labels
            ),
            "healer": _distribution(
                (row["healer"] for row in records), n, labels=healer_labels
            ),
            "mechanisms": {
                tag: {"n": count, "percent": _percent(count, n)}
                for tag, count in sorted(
                    mechanism_counts.items(), key=lambda item: (-item[1], item[0])
                )
            },
            "mechanism_statuses": {
                tag: dict(sorted(counts.items()))
                for tag, counts in sorted(mechanism_status_counts.items())
            },
            "mechanism_families": _mechanism_families(records),
            "failure_chain": {
                "nonempty": {
                    "n": sum(row["failure_chain_nodes"] > 0 for row in records),
                    "percent": _percent(
                        sum(row["failure_chain_nodes"] > 0 for row in records), n
                    ),
                },
                "node_count": _distribution(stage_buckets, n),
                "layer_patterns": _distribution(
                    (row["failure_chain_pattern"] for row in records), n
                ),
            },
        },
        "cross_analysis": {
            "benchmark_by_primary": _matrix(
                records,
                "benchmark",
                "primary",
                primary_labels,
                group_labels=("HumanEval+", "MBPP+"),
            ),
            "benchmark_by_healer": _matrix(
                records,
                "benchmark",
                "healer",
                healer_labels,
                group_labels=("HumanEval+", "MBPP+"),
            ),
            "condition_by_primary": _matrix(
                records,
                "condition",
                "primary",
                primary_labels,
                group_labels=("Candidate_B/H0", "Candidate_B/H1"),
            ),
            "condition_by_healer": _matrix(
                records,
                "condition",
                "healer",
                healer_labels,
                group_labels=("Candidate_B/H0", "Candidate_B/H1"),
            ),
            "layer_by_healer": _matrix(records, "primary", "healer", healer_labels),
            "confidence_by_healer": _matrix(
                records, "confidence", "healer", healer_labels
            ),
            "outcome_by_layer": _matrix(
                records, "outcome_validity", "primary", primary_labels
            ),
            "mechanism_by_healer": _mechanism_healer_matrix(records),
            "scaffold_like": {
                "status": "NA",
                "reason": "formal frozen records沒有scaffold_like欄位，禁止事後推定。",
                "denominator": 0,
            },
        },
        "key_counts": {
            "algorithm_reconstruction_required": mechanism_counts[
                "algorithm_reconstruction_required"
            ],
            "truncation": sum(
                any(tag in {"truncation", "possible_truncation"} for tag in row["mechanisms"])
                for row in records
            ),
            "entry_point": sum(
                any("entry_point" in tag for tag in row["mechanisms"]) for row in records
            ),
            "import_or_dependency": sum(
                any(
                    ("import" in tag.lower() or "dependency" in tag.lower())
                    for tag in row["mechanisms"]
                )
                for row in records
            ),
            "syntax_or_extraction": _mechanism_families(records)[
                "syntax_or_extraction"
            ]["n"],
            "runtime_or_assembly": _mechanism_families(records)[
                "runtime_or_assembly"
            ]["n"],
            "semantic_or_algorithm": _mechanism_families(records)[
                "semantic_or_algorithm"
            ]["n"],
        },
        "representative_cases": _representative_cases(records),
        "execution_counts": {
            "model_calls": 0,
            "candidate_executions": 0,
            "candidate_imports": 0,
            "public_tests": 0,
            "hidden_tests": 0,
            "evalplus": 0,
            "diagnostics": 0,
            "validation": 0,
            "healer": 0,
            "programs_executed": 0,
        },
        "interpretation_guards": {
            "direct_data": (
                "僅使用frozen primary/secondary/confidence/outcome/healer/"
                "mechanism/failure-chain與正式identity。"
            ),
            "reasonable_interpretation": (
                "可說明安全邊界與樣本內關聯，不建立因果或跨模型泛化結論。"
            ),
            "future_hypothesis": (
                "UNRESOLVED diagnostics、deterministic Healer replay與跨模型驗證"
                "只列為後續研究，不視為已完成結果。"
            ),
        },
    }
    return summary


def _fmt_percent(value: float | None) -> str:
    return "NA" if value is None else f"{value:.1f}%"


def _n_pct(cell: dict[str, Any]) -> str:
    if cell["percent"] is None:
        return "NA"
    return f"{cell['n']} ({_fmt_percent(cell['percent'])})"


def _distribution_table(
    title: str, distribution: dict[str, dict[str, Any]], denominator: int
) -> str:
    lines = [
        f"### {title}",
        "",
        f"分母：N={denominator}。",
        "",
        "| 類別 | N | 百分比 |",
        "|---|---:|---:|",
    ]
    for label, cell in distribution.items():
        lines.append(f"| `{label}` | {cell['n']} | {_fmt_percent(cell['percent'])} |")
    return "\n".join(lines)


def _matrix_table(
    title: str, matrix: dict[str, Any], columns: Iterable[str]
) -> str:
    columns = list(columns)
    lines = [
        f"### {title}",
        "",
        "| 分組（列分母） | " + " | ".join(columns) + " |",
        "|---|" + "|".join("---:" for _ in columns) + "|",
    ]
    for group, row in matrix.items():
        cells = [_n_pct(row["values"][column]) for column in columns]
        lines.append(f"| `{group}`（N={row['denominator']}） | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _case_text(case: dict[str, Any]) -> str:
    mechanisms = "、".join(f"`{tag}`" for tag in case["mechanisms"]) or "無active tag"
    return (
        f"`program={case['program_id_short']}…`／"
        f"`cell={case['cell_identity_short']}…`／`{case['task_id']}`："
        f"primary=`{case['primary']}`、Healer=`{case['healer']}`；"
        f"mechanism={mechanisms}。"
    )


def render_report(summary: dict[str, Any]) -> str:
    units = summary["units"]
    closure = summary["provenance"]["closure"]
    dist = summary["distributions"]
    cross = summary["cross_analysis"]
    keys = summary["key_counts"]
    cases = summary["representative_cases"]
    primary = dist["primary"]
    healer = dist["healer"]
    valid = dist["outcome_validity"]["VALID_MODEL_OUTCOME"]
    unresolved = primary["UNRESOLVED"]
    l5 = primary["L5"]

    top_mechanisms = list(dist["mechanisms"].items())[:6]
    findings = [
        (
            f"資料直接顯示：198格已全部完成治理閉合；program與cell各"
            f"{units['programs']}個，source為{units['sources']}個，remaining為"
            f"{closure['remaining']}。"
        ),
        (
            f"資料直接顯示：最多的primary為"
            f"`{max(primary, key=lambda label: primary[label]['n'])}`；"
            f"L5為{l5['n']}格（{_fmt_percent(l5['percent'])}），"
            f"UNRESOLVED為{unresolved['n']}格"
            f"（{_fmt_percent(unresolved['percent'])}）。"
        ),
        (
            f"資料直接顯示：Healer eligible={healer['eligible']['n']}、"
            f"conditional={healer['conditional']['n']}、"
            f"abstain={healer['abstain']['n']}；這是安全門檻的裁決分布，"
            "不是修復執行成敗。"
        ),
        (
            f"資料直接顯示：VALID_MODEL_OUTCOME={valid['n']}格"
            f"（{_fmt_percent(valid['percent'])}）；"
            "outcome validity與failure layer是兩個不同維度。"
        ),
        (
            f"資料直接顯示：`algorithm_reconstruction_required`出現"
            f"{keys['algorithm_reconstruction_required']}格；這些個案不可稱為"
            "deterministic Healer的局部修復。"
        ),
        (
            f"合理解釋：source只有{units['sources']}個而cell/program各有"
            f"{units['cells']}個，反映相同生成來源可依法形成不同seed、條件或"
            "治理cell；共享source不等於重複cell。"
        ),
    ]

    lines = [
        "# Candidate B r003 198格失敗分類與Healer安全邊界統整報告",
        "",
        "> 報告性質：由正式 frozen records 確定性重建的研究統整；"
        "不重新裁決、不執行 candidate、不使用隱藏測試或 oracle 答案。",
        "",
        "## 一、研究摘要",
        "",
        "本階段研究問題是：面對已失敗的 AI 生成 Python 程式，哪些錯誤能在"
        "不猜答案、不改演算法語意的前提下安全交給 deterministic Healer，"
        "哪些只能等待更多證據，哪些應拒絕修改？198格分類的目的，是把"
        "failure layer、具體 mechanism、證據解析度、責任歸因與 Healer "
        "disposition 分開記錄，建立可稽核的安全邊界。研究重點不是要求每個"
        "失敗程式都能被修復。",
        "",
        *[f"- {finding}" for finding in findings],
        "",
        "## 二、資料與實驗單位",
        "",
        f"正式集合為N={units['cells']}個cell、{units['programs']}個program、"
        f"{units['sources']}個source與{units['tasks']}個task。"
        f"集合關係為{closure['reconciliation']}，duplicate program="
        f"{closure['duplicate_programs']}、duplicate cell={closure['duplicate_cells']}、"
        f"omission={closure['omissions']}、remaining={closure['remaining']}。",
        "",
        _distribution_table("Benchmark分布", units["benchmark"], units["cells"]),
        "",
        _distribution_table("正式條件分布", units["condition"], units["cells"]),
        "",
        _distribution_table("Seed分布", units["seed"], units["cells"]),
        "",
        f"資料直接顯示：正式 frozen records 中沒有 scaffold-like 欄位；"
        f"recorded N={units['scaffold_like']['recorded_n']}、unrecorded "
        f"N={units['scaffold_like']['unrecorded_n']}，因此本報告不事後推定"
        "Scaffold-like／非Scaffold-like，也不做該交叉比較。",
        "",
        f"同source多cell共有{units['shared_source_groups']}組，涉及"
        f"{units['cells_in_shared_source_groups']}格。合法原因是研究單位是cell，"
        "cell identity還包含task、seed、condition或治理身分；source相同不會抹除"
        "不同cell/program身分。Candidate B r003位於生成後的development replay、"
        "保存評測結果、靜態taxonomy裁決與Healer安全門檻之間；本報告不是新的"
        "validation或confirmatory run。",
        "",
        "## 三、分類方法",
        "",
        "- L0：研究基礎設施或pipeline失敗，通常不能公平歸因模型。",
        "- L1：無法取得唯一可解析candidate，或Python語法／AST建立失敗。",
        "- L2：可解析但違反明文contract，例如entry point、signature或output packaging。",
        "- L3：明文Domain API／tool-use／required assembly契約的誤用。",
        "- L4：不存在更早L2/L3阻斷時的一般runtime、control-flow或assembly失敗。",
        "- L5：可解析、可執行且介面成立，但答案、公式、邊界或演算法錯誤。",
        "- UNRESOLVED：已完成審查，但合法靜態證據不足以閉合至單一L0–L5；"
        "它不是L6，也不是PENDING_REVIEW。",
        "",
        "`primary`是互斥的最早可證明主層；`secondary`保留後續可證明層。"
        "`confidence`描述裁決把握度，`outcome_validity`描述結果能否公平歸因模型，"
        "兩者都不能代替failure layer。`failure_chain`按順序保存暴露路徑，"
        "`mechanism_tags`則可多選並跨層。",
        "",
        "Truncation只是一個跨層mechanism：截斷後無法解析才是L1；若entry point"
        "缺失可能是L2，runtime資料流缺失可能是L4，可執行但內容不完整可能是L5。"
        "Entry-point根因固定歸L2，但只有唯一結構相容候選與唯一alias／rename／"
        "薄wrapper，且不改主體與資料流時，才可能eligible。",
        "",
        "Healer `eligible`要求唯一、局部、deterministic、answer-free、"
        "task-agnostic、invariant-supported、tested、frozen、evaluator-blind與"
        "可重評估；`conditional`表示明確guard尚待閉合；其他一律`abstain`。"
        "隱藏測試、Plus failure或oracle答案不得反推出修法。修後PASS屬於"
        "Healer outcome，不會改寫raw failure classification。",
        "",
        "## 四、198格完整統計",
        "",
        _distribution_table("Primary failure layer", dist["primary"], units["cells"]),
        "",
        "### Secondary failure layers",
        "",
        f"分母：N={units['cells']}；empty="
        f"{_n_pct(dist['secondary']['empty'])}。Secondary可多選，因此各層百分比"
        "不要求加總為100.0%。",
        "",
        "| Secondary layer | N | 百分比 |",
        "|---|---:|---:|",
        *[
            f"| `{label}` | {cell['n']} | {_fmt_percent(cell['percent'])} |"
            for label, cell in dist["secondary"]["layers"].items()
        ],
        "",
        _distribution_table("Confidence", dist["confidence"], units["cells"]),
        "",
        _distribution_table(
            "Outcome validity", dist["outcome_validity"], units["cells"]
        ),
        "",
        _distribution_table("Healer disposition", dist["healer"], units["cells"]),
        "",
        "### Mechanism tags完整分布",
        "",
        f"分母：N={units['cells']}格。每格可有多個active tag，百分比不互斥；"
        "帶`REJECTED`狀態的假說不計入已成立mechanism。",
        "",
        "| Mechanism tag | N | 佔198格 |",
        "|---|---:|---:|",
        *[
            f"| `{tag}` | {cell['n']} | {_fmt_percent(cell['percent'])} |"
            for tag, cell in dist["mechanisms"].items()
        ],
        "",
        "### Failure-chain主要型態",
        "",
        f"非空chain={_n_pct(dist['failure_chain']['nonempty'])}。",
        "",
        "| Primary／secondary型態 | N | 百分比 |",
        "|---|---:|---:|",
        *[
            f"| `{label}` | {cell['n']} | {_fmt_percent(cell['percent'])} |"
            for label, cell in dist["failure_chain"]["layer_patterns"].items()
        ],
        "",
        "### 指定機制族群（非互斥）",
        "",
        "| 族群 | N | 百分比 |",
        "|---|---:|---:|",
        *[
            f"| `{name}` | {cell['n']} | {_fmt_percent(cell['percent'])} |"
            for name, cell in dist["mechanism_families"].items()
        ],
        "",
        f"`algorithm_reconstruction_required`={keys['algorithm_reconstruction_required']}；"
        f"truncation／possible_truncation={keys['truncation']}；"
        f"entry-point相關={keys['entry_point']}；import/dependency相關="
        f"{keys['import_or_dependency']}；syntax/extraction相關="
        f"{keys['syntax_or_extraction']}；runtime/assembly相關="
        f"{keys['runtime_or_assembly']}；semantic/algorithm相關="
        f"{keys['semantic_or_algorithm']}。這些mechanism族群可重疊，不得相加成198。",
        "",
        "## 五、交叉分析",
        "",
        _matrix_table(
            "Benchmark × Primary",
            cross["benchmark_by_primary"],
            ("L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"),
        ),
        "",
        _matrix_table(
            "Benchmark × Healer",
            cross["benchmark_by_healer"],
            ("eligible", "conditional", "abstain"),
        ),
        "",
        _matrix_table(
            "Condition × Primary",
            cross["condition_by_primary"],
            ("L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"),
        ),
        "",
        _matrix_table(
            "Condition × Healer",
            cross["condition_by_healer"],
            ("eligible", "conditional", "abstain"),
        ),
        "",
        _matrix_table(
            "Failure layer × Healer",
            cross["layer_by_healer"],
            ("eligible", "conditional", "abstain"),
        ),
        "",
        _matrix_table(
            "Confidence × Healer",
            cross["confidence_by_healer"],
            ("eligible", "conditional", "abstain"),
        ),
        "",
        _matrix_table(
            "Outcome validity × Failure layer",
            cross["outcome_by_layer"],
            ("L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"),
        ),
        "",
        "### Mechanism × Healer",
        "",
        "| Mechanism（列分母） | eligible | conditional | abstain |",
        "|---|---:|---:|---:|",
        *[
            (
                f"| `{tag}`（N={row['denominator']}） | "
                f"{_n_pct(row['values']['eligible'])} | "
                f"{_n_pct(row['values']['conditional'])} | "
                f"{_n_pct(row['values']['abstain'])} |"
            )
            for tag, row in cross["mechanism_by_healer"].items()
        ],
        "",
        "HumanEval+與H1的列分母為0時，表內百分比顯示NA；本資料不能據此"
        "比較benchmark或H0/H1效果。Scaffold-like欄位未正式記錄，該比較同樣NA。"
        "小樣本mechanism只做描述，不進行因果或泛化推論。",
        "",
        "## 六、可修與不可修邊界",
        "",
        "### 1. 可安全確定性修復",
        "",
        (
            f"資料直接顯示：eligible={healer['eligible']['n']}格。"
            if not cases["eligible"]
            else "\n".join(f"- {_case_text(case)}" for case in cases["eligible"])
        ),
        "沒有eligible案例時，不能用本批宣稱Healer已有安全修復或verified rescue。",
        "",
        "### 2. 需要額外診斷後才可能修復",
        "",
        f"資料直接顯示：conditional={healer['conditional']['n']}格。代表案例：",
        *[f"- {_case_text(case)}" for case in cases["conditional"]],
        "Conditional不是已核准修復；只有原裁決要求的guard／契約證據閉合後，"
        "才可另建revision評估。",
        "",
        "### 3. 應直接abstain",
        "",
        f"資料直接顯示：abstain={healer['abstain']['n']}格。代表案例：",
        *[f"- {_case_text(case)}" for case in cases["abstain"]],
        "",
        "### 4. 需要重建演算法、不可稱為Healer修復",
        "",
        f"`algorithm_reconstruction_required`共"
        f"{keys['algorithm_reconstruction_required']}格。代表案例：",
        *[
            f"- {_case_text(case)}"
            for case in cases["algorithm_reconstruction_required"]
        ],
        "即使人工能寫出正確演算法，也不等於Healer完成唯一、局部、"
        "oracle-independent修復。",
        "",
        "## 七、Scaffold與Healer的研究發現",
        "",
        "Scaffold處理生成前約束；Healer處理生成後、已定位且修法唯一的局部錯誤。"
        "兩者不可合併計功，prompt/scaffold已避免的錯誤也不得再算Healer rescue。"
        f"本198格沒有正式scaffold-like欄位，且eligible只有"
        f"{healer['eligible']['n']}格，因此對Scaffold效果與Healer實際rescue"
        "均尚無證據。本報告也不宣稱Healer能修復語意或演算法錯誤。",
        "",
        "## 八、UNRESOLVED的意義",
        "",
        f"UNRESOLVED={unresolved['n']}格"
        f"（{_fmt_percent(unresolved['percent'])}）。它不等於L5、不等於沒有錯誤，"
        "而是審查已完成但現有合法靜態證據不足以安全定位。代表案例：",
        *[f"- {_case_text(case)}" for case in cases["unresolved"]],
        "後續diagnostics應只取得能區分competing explanations的最小觀察，並預先"
        "登錄輸入與判準；尚未取得的診斷結果不能寫成既成結論。",
        "",
        "## 九、研究限制",
        "",
        "- 只涵蓋Candidate B r003；共同taxonomy可用於MBPP+與HumanEval+，但本198格"
        "實際只有MBPP+，不能做跨benchmark效果比較。",
        "- 結果受單一model run、prompt、sampling seeds與development資料分布限制。",
        "- 靜態taxonomy能保護不猜測原則，但動態diagnostics可能提供不同解析度；"
        "兩者證據不得混用。",
        f"- {units['shared_source_groups']}組多cell共享source，cell統計不是"
        "完全獨立source樣本；推論時不可把N=198當成155個以上互相獨立來源。",
        "- 高中專題規模、AI-assisted與人工審查資源有限；早期legacy frozen schema"
        "與後期v3.1 schema細節不同，本報告只正規化欄位，不重裁決。",
        f"- abstain={healer['abstain']['n']}格是安全政策結果，不等於Healer"
        "已嘗試後失敗，因此abstain率不能直接解釋成Healer失敗率。",
        "",
        "## 十、可直接用於成果報告的結論",
        "",
        "### 正式學術版",
        "",
        f"本研究以Candidate B r003的{units['cells']}個正式凍結cell為分析單位，"
        f"在{units['programs']}個program與{units['sources']}個unique source上，"
        "依taxonomy v3.1分離failure layer、mechanism、evidence resolution、"
        "outcome validity與Healer disposition。資料顯示"
        f"VALID_MODEL_OUTCOME={valid['n']}格，L5={l5['n']}格，"
        f"UNRESOLVED={unresolved['n']}格；Healer eligible="
        f"{healer['eligible']['n']}、conditional={healer['conditional']['n']}、"
        f"abstain={healer['abstain']['n']}。結果支持「錯誤層級不等於可安全修復性」："
        "只有根因已定位且修法唯一、局部、deterministic與oracle-independent時，"
        "才應考慮Healer介入；語意、演算法或證據未閉合個案應拒絕修改。"
        "此結論限於本development資料，不外推至所有LLM。",
        "",
        "### 高中生口頭報告版",
        "",
        f"我們把{units['cells']}個失敗程式逐一分類，不只是問「錯在哪裡」，"
        "也問「電腦能不能在不偷看答案的情況下安全修」。結果有"
        f"{healer['eligible']['n']}個可以直接列為安全候選、"
        f"{healer['conditional']['n']}個還需要額外條件、"
        f"{healer['abstain']['n']}個應該先不要改。這表示好的Healer不是什麼都修，"
        "而是知道什麼時候證據不夠、應該停手。",
        "",
        "## 十一、後續實驗（僅提出，不執行）",
        "",
        "- 對UNRESOLVED格預先登錄最小diagnostics，再建立新證據revision。",
        "- 依eligible十項規則建置deterministic Healer rule pack。",
        "- 用frozen replay檢驗rescue、partial progress與regression。",
        "- 將prompt／scaffold的生成前效果與Healer生成後效果分離。",
        "- 進行跨模型與HumanEval+／MBPP+外部驗證。",
        "",
        "## 十二、證據治理附錄",
        "",
        f"- 凍結鏈：legacy frozen97 → Batch01–04後frozen177 → Final Batch05 "
        f"{closure['final_batch05']}格 → complete {closure['formal_population']}格。",
        f"- 集合：{closure['reconciliation']}；program={closure['unique_program_id']}、"
        f"cell={closure['unique_cell_identity']}、source="
        f"{closure['unique_source_sha256']}；overlap="
        f"{closure['overlap_frozen177_batch05']}、duplicate="
        f"{closure['duplicate_programs'] + closure['duplicate_cells']}、"
        f"omission={closure['omissions']}、remaining={closure['remaining']}。",
        "- Zero execution：model、candidate execution/import、public/hidden tests、"
        "EvalPlus、diagnostics、validation、Healer與programs executed均為0。",
        "- Builder與targeted governance tests會重建summary與report並逐byte比較；"
        "百分比統一到小數點後1位，分母0顯示NA。",
        f"- Taxonomy SHA：`{summary['provenance']['taxonomy_sha256']}`。",
        f"- Complete ledger SHA：`{AUTHORITY_HASHES[COMPLETE_LEDGER]}`。",
        f"- Complete manifest SHA：`{AUTHORITY_HASHES[COMPLETE_MANIFEST]}`。",
        f"- Builder SHA：`{summary['provenance']['builder_sha256']}`。",
        "",
        "### 權威檔案清單",
        "",
        "| 路徑 | SHA-256 | Byte verified |",
        "|---|---|---:|",
        *[
            f"| `{item['path']}` | `{item['sha256']}` | "
            f"{'是' if item['byte_verified'] else '否'} |"
            for item in summary["provenance"]["authorities"]
        ],
        "",
        "### 解讀層級",
        "",
        "- **資料直接顯示**：summary與frozen records可逐格重建的數量、比例與交叉表。",
        "- **合理解釋**：只描述本樣本的安全邊界與治理含義，不宣稱因果。",
        "- **後續假設**：diagnostics、Healer replay與外部驗證尚未執行。",
        "",
        f"最終狀態：`{VERDICT}`",
        "",
    ]
    return "\n".join(lines)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def build_outputs() -> dict[Path, bytes]:
    summary = build_summary()
    report = render_report(summary)
    return {
        SUMMARY_PATH: _json_bytes(summary),
        REPORT_PATH: report.encode("utf-8"),
    }


def write_outputs() -> dict[Path, bytes]:
    outputs = build_outputs()
    for relative, data in outputs.items():
        destination = _path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return outputs


def main() -> int:
    outputs = write_outputs()
    for path, data in outputs.items():
        print(f"{path.as_posix()} sha256={_sha(data)} bytes={len(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
