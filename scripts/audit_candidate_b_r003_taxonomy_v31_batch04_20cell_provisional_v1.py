#!/usr/bin/env python3
"""Independent static audit of Batch04 provisional adjudication v1.

Independent expectations are encoded from preserved source, public contracts,
and existing evaluator metadata before comparison with provisional records.
No candidate, test, diagnostic, model, validation, or Healer is executed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1_independent_audit_v1"
)
START_HEAD = "4ef378b6303ff58291acc2c7a60b874ee8c2cc68"
STATUS = "INDEPENDENT_STATIC_AUDIT_COMPLETE_MATERIAL_FINDINGS"
VERDICT = "BATCH04_PROVISIONAL_V2_REVISION_REQUIRED"

ROSTER = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1/batch04_roster.csv"
)
ROSTER_MANIFEST = ROSTER.with_name("manifest.json")
ROSTER_AUDIT_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_remaining41_batch04_20cell_roster_v1_independent_audit_v1/manifest.json"
)
PROVISIONAL_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1"
)
RECORDS = PROVISIONAL_DIR / "adjudication_records.csv"
PROVISIONAL_MANIFEST = PROVISIONAL_DIR / "manifest.json"
PROVISIONAL_SUMMARY = PROVISIONAL_DIR / "adjudication_summary.json"
PROVISIONAL_EVIDENCE = PROVISIONAL_DIR / "per_cell_evidence_ledger.csv"
PROVISIONAL_MECHANISMS = PROVISIONAL_DIR / "mechanism_ledger.csv"
PROVISIONAL_CONDITIONAL = PROVISIONAL_DIR / "conditional_diagnostic_queue.csv"
PROVISIONAL_GAPS = PROVISIONAL_DIR / "unresolved_evidence_gaps.csv"
PROVISIONAL_EXECUTION = PROVISIONAL_DIR / "execution_counts.json"
PROVISIONAL_PROVENANCE = PROVISIONAL_DIR / "provenance.json"
PROVISIONAL_REPORT = PROVISIONAL_DIR / "report_zh.md"
PROVISIONAL_BUILDER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1.py"
)
PROVISIONAL_TEST = Path(
    "tests/finals_rebuild/test_candidate_b_r003_taxonomy_v31_batch04_20cell_provisional_v1.py"
)
ACCOUNTS = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/"
    "mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl"
)
TASKS = Path("data/mbpp_plus/tasks.jsonl")
EVALPLUS = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/"
    "manual_evalplus_run_001/evalplus_results.csv"
)
PREPARATION = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/"
    "classification_preparation.csv"
)

SOURCE_HASHES = {
    ROSTER: "0c77a58de44149c17c2dd33ed310c2ef4e6b81b357874eb9ab21157e59b2ecae",
    ROSTER_MANIFEST: "9de720aba72fa5acb134b93785201aacde0482ef817b71ac6ba3739afbe10719",
    ROSTER_AUDIT_MANIFEST: "cd11f7da198044968773198cb9e66f057b11fb5285e4a12e1f70c7fb8475f3b7",
    RECORDS: "5f61c4fc90f9200376e85c622f3fd54d4fa2fd6f0829e1606fb52a17a6033624",
    PROVISIONAL_MANIFEST: "6d170aa0e8f1c54cccf10159c42b5c61fad00b133c843749d15efab1a15250e4",
    PROVISIONAL_SUMMARY: "8ab1fc6381d7828dbc67cb6c9a759fe6967a939d739883f436a5ab0a3f680d1b",
    PROVISIONAL_EVIDENCE: "85a8ee679816ca931126cec3199139b3523504f7b69b915dad8765ddf2cf362e",
    PROVISIONAL_MECHANISMS: "3002f3833d14935d754dfcfcb0c507e391d2d20cc10f6c901e4ea3028e420465",
    PROVISIONAL_CONDITIONAL: "fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",
    PROVISIONAL_GAPS: "76ad7647b3348705e0069da451af73a601014f8e403b73f85b920ceb46feda48",
    PROVISIONAL_EXECUTION: "a2689e5b6dca7db3a16ca8460cda80476eea60a6907dda92bee875e294f3d4a7",
    PROVISIONAL_PROVENANCE: "3531dcb2aebd1595ee9ed00329b3128864ad0e282b5770e456b00793bc54724c",
    PROVISIONAL_REPORT: "8dc1dbe9c1b842e415ddc4674dbbd257178ec9783efbdcf6b97f4e18ee11c0f9",
    PROVISIONAL_BUILDER: "17d7a5e0986332560b7af99d6604b66d9933abddc86aa651146541f946da373f",
    PROVISIONAL_TEST: "b9d8d265ab4b51553f03bba37acc7cd8e11b145397d7ebf6e905fe7be3f4c808",
    ACCOUNTS: "b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec",
    TASKS: "b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c",
    EVALPLUS: "338e66ecd09f48bcf2b8c8d1c8cf75911755dad92743c99257698d994a01938e",
    PREPARATION: "5b0106b93f2d192d89c740659f83021956c15113397f1a54b70e65b7cc7a128c",
}

TAXONOMY_SHA = "93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0"
MATERIAL_IDS = {
    "9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba",
}

FINDING_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "source_sha256",
    "audit_status", "independent_primary", "provisional_primary",
    "independent_secondary", "provisional_secondary", "independent_confidence",
    "provisional_confidence", "independent_outcome", "provisional_outcome",
    "independent_healer", "provisional_healer", "field_differences_json",
    "independent_evidence", "audit_rationale", "impact",
)
DIFF_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "audit_status",
    "field_name", "provisional_value", "recommended_value", "evidence", "impact",
)
MATERIAL_FIELDS = DIFF_FIELDS + ("recommended_action",)
NON_MATERIAL_FIELDS = DIFF_FIELDS + ("disposition",)
HEALER_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "independent_healer",
    "provisional_healer", "audit_status", "safety_evidence", "minimal_diagnostic",
)
UNRESOLVED_FIELDS = (
    "batch_rank", "program_id", "cell_identity_sha256", "audit_status",
    "competing_explanations_closed", "gap_specificity", "minimal_diagnostic_status",
    "independent_rationale",
)


class AuditError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(repo: Path, path: Path) -> list[dict[str, str]]:
    with (repo / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(repo: Path, path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (repo / path).read_text(encoding="utf-8").splitlines() if line]


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _taxonomy_path_and_sha(repo: Path) -> tuple[Path, str]:
    manifest = json.loads((repo / PROVISIONAL_MANIFEST).read_text(encoding="utf-8"))
    provenance = json.loads((repo / PROVISIONAL_PROVENANCE).read_text(encoding="utf-8"))
    _require(manifest["taxonomy_v31_sha256"] == TAXONOMY_SHA, "manifest taxonomy SHA drift")
    matches = [
        (Path(path), digest)
        for path, digest in provenance["source_hashes"].items()
        if "AI_生成程式共同失敗分類標準" in path
    ]
    _require(len(matches) == 1, "taxonomy path resolution drift")
    path, digest = matches[0]
    _require(digest == TAXONOMY_SHA and path.is_file(), "taxonomy provenance drift")
    _require(_sha(path.read_bytes()) == TAXONOMY_SHA, "authoritative taxonomy byte drift")
    return path, digest


def verify_sources(repo: Path = REPO_ROOT) -> None:
    for path, digest in SOURCE_HASHES.items():
        _require((repo / path).is_file(), f"missing upstream: {path.as_posix()}")
        _require(_sha((repo / path).read_bytes()) == digest, f"upstream byte drift: {path.as_posix()}")
    _taxonomy_path_and_sha(repo)
    provisional_manifest = json.loads((repo / PROVISIONAL_MANIFEST).read_text(encoding="utf-8"))
    _require(
        provisional_manifest["verdict"] == "READY_FOR_BATCH04_PROVISIONAL_INDEPENDENT_AUDIT",
        "provisional verdict drift",
    )


def _exp(
    primary: str,
    mechanisms: dict[str, str],
    evidence: str,
    rationale: str,
    *,
    secondary: str = "",
    confidence: str = "HIGH",
) -> dict[str, Any]:
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "outcome": "VALID_MODEL_OUTCOME",
        "healer": "abstain",
        "mechanisms": mechanisms,
        "evidence": evidence,
        "rationale": rationale,
    }


GENERIC_UNRESOLVED = {
    "public_examples_non_discriminating": "CONFIRMED",
    "plus_failure_not_localized": "CONFIRMED",
    "diagnostic_execution_required": "SUPPORTED",
}

EXPECTATIONS = {
    "8406e78362de082453800aa627d56e53b5170bf464a7358ed301f3612aeb1ff3": _exp(
        "L5",
        {"incorrect_formula": "CONFIRMED", "algorithm_reconstruction_required": "SUPPORTED"},
        "six-face formula for a=3 yields ~23.383, not public ~15.588=a^2*sqrt(3)",
        "Public numeric contract directly falsifies the closed-form formula.",
    ),
    "866739b5b8f57631f1a69318ccccf5b802b31f0fc38b57e6a75e358d9ef9a9c2": _exp(
        "L5",
        {"wrong_boundary_condition": "CONFIRMED", "capital_boundary_detection_error": "CONFIRMED"},
        "i==0 capital path inserts a leading space so 'Python' becomes ' Python'",
        "Public single-word capital example is statically contradicted.",
    ),
    "8be467a87d48ada42b452f75670c330df1e5f4a334816d133ece971a93245e51": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "middle-bit XOR mask satisfies public 9->15 and base; first plus case absent",
        "No preserved static counterexample closes L0-L5 for the plus failure.",
        confidence="LOW",
    ),
    "8c4a86b4c5c2dc7f2ec53338538b0859c10c4920752c5d3fe775a0332148cd44": _exp(
        "L5",
        {"incorrect_formula": "CONFIRMED", "algorithm_reconstruction_required": "SUPPORTED"},
        "a^2*(sqrt(3)/4+sqrt(6)) for a=3 yields ~25.943, not public ~15.588",
        "Public float assert uniquely falsifies the static formula.",
    ),
    "8ef0641f265717551638f61f1daf725c93f863842cab36e6f422970e23d7f298": _exp(
        "UNRESOLVED",
        {**GENERIC_UNRESOLVED, "sublist_semantics_ambiguous": "SUSPECTED"},
        "contiguous-window check satisfies nondiscriminating public False example and base",
        "Public text and preserved outcomes do not close contiguous vs noncontiguous semantics.",
        confidence="LOW",
    ),
    "8f2e043d3ef8a94ec9db97c703ff778ec9a46582d481a979e5cf806434f470fc": _exp(
        "L5",
        {"incorrect_formula": "CONFIRMED", "algorithmic_error": "CONFIRMED"},
        "odd-n branch returns merged[n//2]=12 instead of public average 16.0",
        "Public median example directly falsifies the odd-branch index rule.",
    ),
    "988e14a3191e7bc858a23195cd2356a37acd3408f288a68fe062cc838aa4d738": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "yyyy-mm-dd split reorder satisfies public/base; first plus date absent",
        "Malformed/domain date policy cannot be localized without the failing plus case.",
        confidence="LOW",
    ),
    "9ad0aec70e9293ceb0bd48dd62d61cd09be24b487b3158726bf9b037a4c72d20": _exp(
        "L5",
        {
            "algorithmic_error": "CONFIRMED",
            "wrong_parameter_semantics": "SUPPORTED",
            "incorrect_pair_domain": "SUSPECTED",
        },
        "pair XOR values are XOR-folded (13) instead of summed to public 47",
        "Public pair-XOR sum assertion is statically contradicted.",
    ),
    "9cecbec0d7bbabf0c9111cd5a25e8a8bf100bd34a82e191b68129e9bbef557a3": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "sorted unique DP divisibility chain attains public size 4; first plus list absent",
        "Zeros/negatives/duplicates policy remains unclosed without plus localization.",
        confidence="LOW",
    ),
    "9dbe9166f6ac22cedfafb269276c88ee25a37cf84044e736f7be00d8089464ba": _exp(
        "L5",
        {
            "frequency_one_instead_of_distinct_value": "CONFIRMED",
            "semantic_goal_drift": "CONFIRMED",
        },
        "source omits repeated 1 and returns 20; public result 21 counts each distinct value once",
        "Primary L5 is correct, but the provisional mechanism tag names the inverse behavior.",
    ),
    "a63f9d97cba10e46cb00cd363e9f3de9cec93661af43258ddfd7f9deda1dae91": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "sum of first-n even squares satisfies n=2 and base; first plus input absent",
        "Boundary/domain failure cannot be localized statically.",
        confidence="LOW",
    ),
    "a6a4398773853bd405ef18d191a8182c599b3467aabc2b417f070a11fc93044b": _exp(
        "UNRESOLVED",
        {**GENERIC_UNRESOLVED, "sublist_semantics_ambiguous": "SUSPECTED"},
        "identical contiguous implementation shares source with rank 5; public/base nondiscriminating",
        "Shared-source cell remains unresolved for the same sublist semantic gap.",
        confidence="LOW",
    ),
    "a6b26635210ce9147ed93f1b67d5770d814ac10f06a4819332de022287d457a8": _exp(
        "L5",
        {"wrong_boundary_condition": "CONFIRMED", "duplicate_value_semantics": "CONFIRMED"},
        "strict < binary search routes equality left, computing lower-bound not right insertion",
        "Task requires right insertion; static comparison implements left insertion.",
    ),
    "a6f3b32f10e03fb5ebe7025f863b1bff932bf5459b3d9aae070a3497d37ed62a": _exp(
        "L4",
        {
            "nontermination": "CONFIRMED",
            "control_flow_failure": "CONFIRMED",
            "algorithm_reconstruction_required": "SUPPORTED",
        },
        "while left < right body is only comments/pass; prep records WorkerProcessExit",
        "Parseable entry exists but bounds never move; missing unique-element algorithm is secondary L5.",
        secondary="L5",
    ),
    "b63e3c913c74a74a79cca769520da9b92a2d6bcb640882d2df8a189812e67ef6": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "numeric filter then min yields public 2; first plus heterogeneous list absent",
        "Bool/empty-numeric/non-real policy cannot be closed from preserved evidence.",
        confidence="LOW",
    ),
    "b677e7ee4faca0108c29317a74d6acd3c5f699de647fe062c61ad5efc6dbb2e5": _exp(
        "L5",
        {
            "control_flow_failure": "CONFIRMED",
            "capital_boundary_detection_error": "CONFIRMED",
            "semantic_goal_drift": "SUPPORTED",
        },
        "space-insertion branch appends only ' ' and drops the current capital letter",
        "Capital-word spacing deletes boundary letters contrary to the stated contract.",
    ),
    "b977ada54f0a13704e4e0f3507761d860242d6b745c9d9f44e0750c972d28e2c": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "repeated division yields public 8->'1000'; first plus integer absent",
        "Signed/non-integer domain policy remains unlocalized.",
        confidence="LOW",
    ),
    "ba78506a3e44c95de2ee2e90bcfbebfc58b91703227e9ec65aaf922d046c31cd": _exp(
        "L5",
        {
            "order_sensitive_counter": "CONFIRMED",
            "semantic_goal_drift": "CONFIRMED",
            "algorithm_reconstruction_required": "SUPPORTED",
        },
        "Counter keeps (3,1)!=(1,3) while public expects order-normalized keys",
        "Public mapping requires canonicalize-then-count semantics.",
    ),
    "be02f058d52c050cf5574665a7ed4d56e20d6afde2ef686be3c6c59cc8878352": _exp(
        "L5",
        {"algorithmic_error": "CONFIRMED", "incorrect_search_bound": "CONFIRMED"},
        "for n=5 the loop excludes outer square 3 and returns False although 5=3^2-2^2",
        "Public True assertion is statically falsified by the search bound.",
    ),
    "bf89a824ca07792fc9d14d89cd30b82b2d94122c012226a5b6d6519f19d60cfe": _exp(
        "UNRESOLVED",
        GENERIC_UNRESOLVED,
        "prefix-remainder binary yields public 8->'1000'; first plus integer absent",
        "Signed/input-domain plus failure cannot be localized statically.",
        confidence="LOW",
    ),
}


def build_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    verify_sources(repo)
    roster = _read_csv(repo, ROSTER)
    records = _read_csv(repo, RECORDS)
    accounts = {r["program_id"]: r for r in _read_jsonl(repo, ACCOUNTS) if r["healer_account"] == "H0"}
    tasks = {r["task_id"]: r for r in _read_jsonl(repo, TASKS)}
    evals = {r["program_id"]: r for r in _read_csv(repo, EVALPLUS) if r["healer_account"] == "H0"}
    prep = {r["program_id"]: r for r in _read_csv(repo, PREPARATION)}
    _require(len(roster) == len(records) == 20 and set(EXPECTATIONS) == {r["program_id"] for r in roster}, "20-cell audit closure drift")
    _require([r["program_id"] for r in roster] == [r["program_id"] for r in records], "record order drift")
    _require(len({r["source_sha256"] for r in records}) == 19, "unique source drift")
    shared = [r for r in records if r["batch_rank"] in {"5", "12"}]
    _require(
        len({r["source_sha256"] for r in shared}) == 1 and len({r["cell_identity_sha256"] for r in shared}) == 2,
        "legal shared source drift",
    )

    findings: list[dict[str, str]] = []
    differences: list[dict[str, str]] = []
    material: list[dict[str, str]] = []
    healer_rows: list[dict[str, str]] = []
    unresolved_rows: list[dict[str, str]] = []
    inferred_primary = Counter()
    inferred_secondary = Counter()
    inferred_confidence = Counter()
    inferred_healer = Counter()
    for rr, record in zip(roster, records):
        pid = rr["program_id"]
        exp = EXPECTATIONS[pid]
        _require(record["cell_identity_sha256"] == rr["cell_identity_sha256"], f"cell identity drift: {pid}")
        _require(
            record["source_sha256"]
            == rr["source_sha256"]
            == accounts[pid]["evaluation_source_sha256"]
            == prep[pid]["evaluation_source_sha256"],
            f"source closure drift: {pid}",
        )
        _require(tasks[rr["task_id"]]["task_id"] == rr["task_id"] and pid in evals, f"evidence closure drift: {pid}")
        actual_mechanisms = {item["tag"]: item["strength"] for item in json.loads(record["mechanism_tags_json"])}
        field_diffs: list[str] = []
        comparisons = {
            "primary_layer": (record["primary_layer"], exp["primary"]),
            "secondary_layer": (record["secondary_layer"], exp["secondary"]),
            "confidence": (record["confidence"], exp["confidence"]),
            "outcome_validity": (record["outcome_validity"], exp["outcome"]),
            "healer_eligibility": (record["healer_eligibility"], exp["healer"]),
            "mechanism_tags_json": (actual_mechanisms, exp["mechanisms"]),
        }
        for field, (actual, recommended) in comparisons.items():
            if actual != recommended:
                field_diffs.append(field)
                row = {
                    "batch_rank": record["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": record["cell_identity_sha256"],
                    "audit_status": "MATERIAL",
                    "field_name": field,
                    "provisional_value": (
                        json.dumps(actual, ensure_ascii=False, sort_keys=True)
                        if isinstance(actual, dict)
                        else actual
                    ),
                    "recommended_value": (
                        json.dumps(recommended, ensure_ascii=False, sort_keys=True)
                        if isinstance(recommended, dict)
                        else recommended
                    ),
                    "evidence": exp["evidence"],
                    "impact": (
                        "mechanism direction is reversed; layer/confidence/outcome/Healer distributions remain unchanged"
                        if field == "mechanism_tags_json"
                        else "adjudication field changes"
                    ),
                }
                differences.append(row)
                material.append(
                    {
                        **row,
                        "recommended_action": (
                            "replace inverse tag with frequency_one_instead_of_distinct_value; "
                            "preserve semantic_goal_drift"
                        ),
                    }
                )
        completeness = {
            "failure_chain": bool(record["failure_chain"]),
            "evidence_present": bool(record["evidence_present"]),
            "evidence_missing": bool(record["evidence_missing"]),
            "competing_explanations": bool(record["competing_explanations"]),
            "reason": bool(record["reason"]),
            "citations": all(
                token in record["evidence_citations"]
                for token in (
                    ACCOUNTS.as_posix(),
                    TASKS.as_posix(),
                    EVALPLUS.as_posix(),
                    "AI_生成程式共同失敗分類標準",
                )
            ),
        }
        if exp["primary"] == "UNRESOLVED":
            completeness["minimal_future_diagnostic"] = bool(record["minimal_future_diagnostic"])
        missing_fields = [name for name, ok in completeness.items() if not ok]
        _require(not missing_fields, f"evidence field incomplete {pid}: {missing_fields}")
        status = "MATERIAL" if field_diffs else "AFFIRMED"
        findings.append(
            {
                "batch_rank": record["batch_rank"],
                "program_id": pid,
                "cell_identity_sha256": record["cell_identity_sha256"],
                "source_sha256": record["source_sha256"],
                "audit_status": status,
                "independent_primary": exp["primary"],
                "provisional_primary": record["primary_layer"],
                "independent_secondary": exp["secondary"],
                "provisional_secondary": record["secondary_layer"],
                "independent_confidence": exp["confidence"],
                "provisional_confidence": record["confidence"],
                "independent_outcome": exp["outcome"],
                "provisional_outcome": record["outcome_validity"],
                "independent_healer": exp["healer"],
                "provisional_healer": record["healer_eligibility"],
                "field_differences_json": json.dumps(field_diffs, separators=(",", ":")),
                "independent_evidence": exp["evidence"],
                "audit_rationale": exp["rationale"],
                "impact": "mechanism-only revision required" if field_diffs else "none",
            }
        )
        healer_rows.append(
            {
                "batch_rank": record["batch_rank"],
                "program_id": pid,
                "cell_identity_sha256": record["cell_identity_sha256"],
                "independent_healer": "abstain",
                "provisional_healer": record["healer_eligibility"],
                "audit_status": "AFFIRMED",
                "safety_evidence": (
                    "semantic/algorithm change required"
                    if exp["primary"] in {"L4", "L5"}
                    else "root layer and unique local repair not closed"
                ),
                "minimal_diagnostic": record["minimal_future_diagnostic"] if exp["primary"] == "UNRESOLVED" else "",
            }
        )
        if exp["primary"] == "UNRESOLVED":
            unresolved_rows.append(
                {
                    "batch_rank": record["batch_rank"],
                    "program_id": pid,
                    "cell_identity_sha256": record["cell_identity_sha256"],
                    "audit_status": "AFFIRMED",
                    "competing_explanations_closed": "false",
                    "gap_specificity": "SPECIFIC",
                    "minimal_diagnostic_status": "MINIMAL_NON_ORACLE",
                    "independent_rationale": exp["rationale"],
                }
            )
        inferred_primary[exp["primary"]] += 1
        inferred_secondary[exp["secondary"] or "empty"] += 1
        inferred_confidence[exp["confidence"]] += 1
        inferred_healer[exp["healer"]] += 1

    _require({r["program_id"] for r in findings if r["audit_status"] == "MATERIAL"} == MATERIAL_IDS, "material cell closure drift")
    _require(len(material) == 1 and len(differences) == 1, "field difference closure drift")
    _require(len(unresolved_rows) == 9 and all(r["audit_status"] == "AFFIRMED" for r in healer_rows), "focused audit closure drift")
    _require(
        inferred_primary == Counter({"L5": 10, "UNRESOLVED": 9, "L4": 1}),
        f"inferred primary drift: {inferred_primary}",
    )
    _require(inferred_secondary == Counter({"empty": 19, "L5": 1}), f"inferred secondary drift: {inferred_secondary}")
    _require(inferred_confidence == Counter({"HIGH": 11, "LOW": 9}), f"inferred confidence drift: {inferred_confidence}")
    _require(inferred_healer == Counter({"abstain": 20}), f"inferred healer drift: {inferred_healer}")
    summary = {
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "verdict": VERDICT,
        "cells": 20,
        "affirmed": 19,
        "non_material": 0,
        "material": 1,
        "field_level_differences": 1,
        "identity_source_closure": 20,
        "unique_program_id": 20,
        "unique_cell_identity": 20,
        "unique_source_sha256": len({r["source_sha256"] for r in records}),
        "shared_source_groups": 1,
        "shared_source_explanation": (
            "ranks 5 and 12 share byte-identical generated source but retain distinct "
            "program/cell/generation identities"
        ),
        "inferred_primary_distribution": dict(sorted(inferred_primary.items())),
        "inferred_secondary_distribution": dict(sorted(inferred_secondary.items())),
        "inferred_confidence_distribution": dict(sorted(inferred_confidence.items())),
        "inferred_outcome_distribution": {"VALID_MODEL_OUTCOME": 20},
        "inferred_healer_distribution": {"eligible": 0, "conditional": 0, "abstain": 20},
        "l4_cells_affirmed": 1,
        "l5_cells_affirmed_layer": 10,
        "unresolved_cells_affirmed": 9,
        "rank14_secondary_l5_affirmed": True,
        "healer_dispositions_affirmed": 20,
        "upstream_modified": False,
        "new_runtime_observations": 0,
        "provisional_modified": False,
        "batch05_started": False,
    }
    return {
        "findings": findings,
        "differences": differences,
        "material": material,
        "non_material": [],
        "healer": healer_rows,
        "unresolved": unresolved_rows,
        "summary": summary,
    }


def _report(summary: dict[str, Any], material: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Candidate B r003 taxonomy v3.1：Batch04 provisional v1 獨立audit",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"- AFFIRMED：{summary['affirmed']}",
            f"- NON_MATERIAL：{summary['non_material']}",
            f"- MATERIAL：{summary['material']}",
            "",
            "唯一MATERIAL finding為mechanism方向錯誤（rank 10 / Mbpp/777）：candidate只計出現一次的值，",
            "公開結果要求distinct值各計一次；原tag `dedupe_instead_of_unique_occurrence` 描述相反方向。",
            "建議改為 `frequency_one_instead_of_distinct_value`，保留L5、HIGH、VALID_MODEL_OUTCOME、abstain與",
            "`semantic_goal_drift`。",
            "",
            f"- audit後Primary：{summary['inferred_primary_distribution']}",
            f"- audit後Secondary：{summary['inferred_secondary_distribution']}",
            f"- audit後Healer：{summary['inferred_healer_distribution']}",
            "- 9格UNRESOLVED、1格L4（含rank14 secondary=L5）、10格L5 layer及20格Healer abstain均獨立affirm。",
            "- eligible=0、conditional=0符合安全門檻。",
            "",
            "未執行candidate、imports、tests、EvalPlus、diagnostics、validation、Healer或模型；",
            "未修改provisional/roster/remaining21/taxonomy/frozen；未建立v2、未開始Batch05。",
            "",
            f"欄位級差異：{material[0]['field_name']} @ batch_rank={material[0]['batch_rank']}" if material else "",
        ]
    ) + "\n"


def build_outputs(repo: Path = REPO_ROOT) -> dict[str, bytes]:
    analysis = build_analysis(repo)
    execution = {
        "model_calls": 0,
        "candidate_executions": 0,
        "candidate_imports": 0,
        "public_test_executions": 0,
        "hidden_test_executions": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "validation_executions": 0,
        "healer_executions": 0,
        "programs_executed": 0,
    }
    outputs = {
        "per_cell_audit_findings.csv": _csv_bytes(FINDING_FIELDS, analysis["findings"]),
        "field_level_difference_ledger.csv": _csv_bytes(DIFF_FIELDS, analysis["differences"]),
        "material_findings.csv": _csv_bytes(MATERIAL_FIELDS, analysis["material"]),
        "non_material_findings.csv": _csv_bytes(NON_MATERIAL_FIELDS, analysis["non_material"]),
        "healer_disposition_audit.csv": _csv_bytes(HEALER_FIELDS, analysis["healer"]),
        "unresolved_audit.csv": _csv_bytes(UNRESOLVED_FIELDS, analysis["unresolved"]),
        "audit_summary.json": _json_bytes(analysis["summary"]),
        "execution_counts.json": _json_bytes(execution),
        "report_zh.md": _report(analysis["summary"], analysis["material"]).encode("utf-8"),
    }
    taxonomy_path, taxonomy_sha = _taxonomy_path_and_sha(repo)
    provenance = {
        **analysis["summary"],
        **execution,
        "start_head": START_HEAD,
        "provisional_records_sha256": SOURCE_HASHES[RECORDS],
        "provisional_manifest_sha256": SOURCE_HASHES[PROVISIONAL_MANIFEST],
        "taxonomy_path_resolved_from_provisional_provenance": taxonomy_path.as_posix(),
        "taxonomy_sha256": taxonomy_sha,
        "independent_evidence_scope": (
            "preserved generated source, public task specification, existing evaluator/EvalPlus metadata"
        ),
        "source_hashes": {path.as_posix(): digest for path, digest in SOURCE_HASHES.items()},
        "provisional_modified": False,
        "batch04_frozen": False,
        "batch05_started": False,
        "v2_created": False,
    }
    outputs["provenance.json"] = _json_bytes(provenance)
    manifest = {
        "revision": OUTPUT_RELATIVE.as_posix(),
        "status": STATUS,
        "verdict": VERDICT,
        "start_head": START_HEAD,
        "cells": 20,
        "affirmed": 19,
        "non_material": 0,
        "material": 1,
        "provisional_records_sha256": SOURCE_HASHES[RECORDS],
        "provisional_manifest_sha256": SOURCE_HASHES[PROVISIONAL_MANIFEST],
        "taxonomy_sha256": taxonomy_sha,
        "outputs_sha256_excluding_manifest": {name: _sha(data) for name, data in outputs.items()},
        **execution,
    }
    outputs["manifest.json"] = _json_bytes(manifest)
    return outputs


def write_outputs(repo: Path = REPO_ROOT) -> Path:
    output = repo / OUTPUT_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    for name, data in build_outputs(repo).items():
        (output / name).write_bytes(data)
    return output


def main() -> None:
    output = write_outputs()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    print(f"wrote {output}")
    print(f"findings_sha256={manifest['outputs_sha256_excluding_manifest']['per_cell_audit_findings.csv']}")
    print(f"manifest_sha256={_sha((output / 'manifest.json').read_bytes())}")
    print(f"verdict={manifest['verdict']}")


if __name__ == "__main__":
    main()
