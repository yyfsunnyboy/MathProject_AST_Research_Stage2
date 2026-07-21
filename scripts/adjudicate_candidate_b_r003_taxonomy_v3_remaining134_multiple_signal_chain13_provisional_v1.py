#!/usr/bin/env python3
"""AI-assisted provisional adjudication for remaining134 multiple_signal_chain (13 cells)."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    from scripts import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    import prepare_candidate_b_r003_taxonomy_v3_formal_classification as preparation
    import prepare_candidate_b_r003_taxonomy_v3_remaining171_machine_census_v1 as census_prep


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1"
)
START_HEAD = "c0afac21159c1066e8e2daac10bccaf7fe207569"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining134_multiple_signal_chain13_provisional_v1.py"
)

MACHINE_CENSUS_DIR = census_prep.OUTPUT_RELATIVE
MACHINE_CENSUS_MANIFEST = MACHINE_CENSUS_DIR / "manifest.json"
MACHINE_CENSUS_CSV = MACHINE_CENSUS_DIR / "machine_census.csv"
MACHINE_CENSUS_ROSTER = MACHINE_CENSUS_DIR / "fixed_roster.csv"
MACHINE_CENSUS_MANIFEST_SHA256 = "3def8a5806b20200ade0b5d4a652d3fb6998ecc889bf7277485cd6045831ef07"
MACHINE_CENSUS_CSV_SHA256 = "284802c8f1aeff92ad70f65b42c4aa7dabc252da592f8ad62011be71537f8a32"
MACHINE_CENSUS_ROSTER_SHA256 = "6e2c6e243fc6ff01c0b0fc2c6939e99cf7f87ef5f17bdf97206adc62ab9af1a5"

G2_PROVISIONAL_CSV = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1/"
    "ai_assisted_provisional_adjudication.csv"
)
G2_PROVISIONAL_CSV_SHA256 = (
    "90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119"
)

MODULE_EXCEPTION_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1"
)
MODULE_EXCEPTION_CSV = MODULE_EXCEPTION_DIR / "ai_provisional_adjudication.csv"
MODULE_EXCEPTION_MANIFEST = MODULE_EXCEPTION_DIR / "manifest.json"
MODULE_EXCEPTION_CSV_SHA256 = (
    "8b32d0561c0d42efe07c1bf89bd3bcaf4b7a42657f54bee25922f0be2aca6ab7"
)
MODULE_EXCEPTION_MANIFEST_SHA256 = (
    "72b02ab7da59e65db2d5e09cee9344c3d52940a717ea3dfea05310e0529d76c1"
)

TARGET_CLUSTER = "multiple_signal_chain"
TARGET_CELLS = 13
VALID_PRIMARY_LAYERS = frozenset({"L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED"})
VALID_SECONDARY_LAYERS = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})

SOURCE_HASHES: dict[Path, str] = {
    preparation.FORMAL_RESULTS: preparation.SOURCE_HASHES[preparation.FORMAL_RESULTS],
    preparation.JOURNAL: preparation.SOURCE_HASHES[preparation.JOURNAL],
    preparation.TASKS: preparation.SOURCE_HASHES[preparation.TASKS],
    preparation.TAXONOMY_CODEBOOK: preparation.SOURCE_HASHES[preparation.TAXONOMY_CODEBOOK],
    MACHINE_CENSUS_MANIFEST: MACHINE_CENSUS_MANIFEST_SHA256,
    MACHINE_CENSUS_CSV: MACHINE_CENSUS_CSV_SHA256,
    MACHINE_CENSUS_ROSTER: MACHINE_CENSUS_ROSTER_SHA256,
    G2_PROVISIONAL_CSV: G2_PROVISIONAL_CSV_SHA256,
    MODULE_EXCEPTION_CSV: MODULE_EXCEPTION_CSV_SHA256,
}

ROSTER_FIELDS = (
    "cluster_rank",
    "program_id",
    "cell_identity_sha256",
    "dataset",
    "task_id",
    "condition",
    "seed",
    "generation_id",
    "evaluation_source_sha256",
    "required_entry_point",
    "operational_cluster",
    "frozen_machine_signals",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "diagnostic_candidate_line",
    "inclusion_reason",
    "machine_census_roster_rank",
)

ADJUDICATION_FIELDS = (
    "program_id",
    "cell_identity_sha256",
    "task_id",
    "seed",
    "operational_cluster",
    "all_observed_machine_signals",
    "provisional_primary_layer",
    "provisional_secondary_layers",
    "mechanism_tags",
    "outcome_validity",
    "failure_chain",
    "healer_eligibility",
    "healer_candidate_family",
    "eligibility_reason",
    "proposed_rule_family",
    "required_preconditions",
    "ambiguity_count",
    "oracle_independent_acceptance_check",
    "abstain_reason",
    "ambiguity_status",
    "evidence_summary",
    "alternative_explanations",
    "unresolved_reason",
    "evidence_source_paths",
    "evidence_locator",
    "confidence",
    "adjudication_status",
)

HEALER_CANDIDATE_DETAIL_FIELDS = (
    "program_id",
    "cell_identity_sha256",
    "healer_eligibility",
    "healer_candidate_family",
    "eligibility_reason",
    "proposed_rule_family",
    "required_preconditions",
    "counterexample_notes",
)


class AdjudicationError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue().encode("utf-8")


def _path(repo: Path, relative: Path) -> Path:
    return relative if relative.is_absolute() else repo / relative


def verify_sources(root: Path = ROOT, expected: dict[Path, str] | None = None) -> None:
    for relative, digest in (expected or SOURCE_HASHES).items():
        path = _path(root, relative)
        _require(path.is_file(), f"missing frozen source: {path}")
        _require(_sha(path.read_bytes()) == digest, f"frozen source hash drift: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _decision(
    primary: str,
    secondary: list[str],
    mechanisms: list[str],
    confidence: str,
    eligibility: str,
    ambiguity: str,
    ambiguity_count: int,
    evidence_summary: str,
    chain_layer: str,
    chain_mechanism: str,
    chain_stages: list[dict[str, Any]] | None = None,
    healer_family: str = "",
    eligibility_reason: str = "",
    proposed_rule_family: str = "",
    required_preconditions: str = "",
    abstain_reason: str = "",
    alternative_explanations: str = "",
    unresolved_reason: str = "",
    counterexample_notes: str = "",
    oracle_check: str = "public_contract_and_frozen_h0_source_only",
) -> dict[str, Any]:
    _require(primary in VALID_PRIMARY_LAYERS, f"invalid primary layer: {primary}")
    _require(
        all(layer in VALID_SECONDARY_LAYERS for layer in secondary),
        f"invalid secondary layer(s): {secondary}",
    )
    _require(primary not in secondary, f"primary layer duplicated in secondary: {primary}")
    _require(chain_layer in VALID_PRIMARY_LAYERS, f"invalid chain layer: {chain_layer}")

    if chain_stages is not None:
        chain = list(chain_stages)
    else:
        if primary == "L5":
            stage = "required_function_public_contract_observation"
            gate = "G4"
        elif primary == "UNRESOLVED":
            stage = "raw_module_execution"
            gate = "G2"
        else:
            stage = "raw_module_execution"
            gate = "G2"

        chain = [{
            "stage": stage,
            "gate": gate,
            "layer": chain_layer,
            "mechanism": chain_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
        }]
        if primary == "L5":
            chain[0]["evidence_scope"] = "public_contract_only"
        if "L5" in secondary and primary != "L5":
            chain.append({
                "stage": "required_function_public_contract_observation",
                "gate": "G4",
                "layer": "L5",
                "mechanism": chain_mechanism,
                "outcome_validity": "VALID_MODEL_OUTCOME",
                "evidence_scope": "public_contract_only",
            })

    return {
        "provisional_primary_layer": primary,
        "provisional_secondary_layers": _json(list(secondary)),
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "failure_chain": _json(chain),
        "mechanism_tags": _json(list(mechanisms)),
        "confidence": confidence,
        "healer_eligibility": eligibility,
        "healer_candidate_family": healer_family,
        "eligibility_reason": eligibility_reason,
        "proposed_rule_family": proposed_rule_family if eligibility != "abstain" else "",
        "required_preconditions": required_preconditions,
        "ambiguity_count": ambiguity_count,
        "oracle_independent_acceptance_check": oracle_check,
        "abstain_reason": abstain_reason,
        "ambiguity_status": ambiguity,
        "evidence_summary": evidence_summary,
        "alternative_explanations": alternative_explanations,
        "unresolved_reason": unresolved_reason,
        "counterexample_notes": counterexample_notes,
    }


def _filter_data(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=["L5"],
        mechanisms=[
            "unbound_name",
            "unbound_name_stats",
            "strict_inequality_boundary",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Diagnostics runner executes `prompt + source`. Official Mbpp/722 prompt has 4 "
            "newlines (prompt.count('\\n')=4); model_source_line=6 maps to candidate line "
            "6-4=2. On that line the dict comprehension loads `stats` but never stores it "
            "(unpacks to height, weight), causing unbound name `stats` NameError. H0 journal, "
            "ledger, and diagnostics share SHA c0d3c323…; VALID_MODEL_OUTCOME stays. Public "
            "assert includes weight==70 with min_weight=70 while code uses `>`, supporting "
            "secondary L5 strict_inequality_boundary via public arithmetic, not guessing."
        ),
        chain_layer="L4",
        chain_mechanism="unbound_name_stats",
        chain_stages=[
            {
                "stage": "causal_mechanism",
                "gate": "G1",
                "layer": "L4",
                "mechanism": "unbound_name_stats",
                "outcome_validity": "VALID_MODEL_OUTCOME",
            },
            {
                "stage": "first_observable_failure",
                "gate": "G2",
                "layer": "L4",
                "mechanism": "nameerror_on_unbound_stats",
                "outcome_validity": "VALID_MODEL_OUTCOME",
            },
            {
                "stage": "downstream_public_contract",
                "gate": "G4",
                "layer": "L5",
                "mechanism": "strict_inequality_boundary",
                "outcome_validity": "VALID_MODEL_OUTCOME",
                "evidence_scope": "public_contract_only",
            },
        ],
        healer_family="nameerror_locator_repair",
        eligibility_reason=(
            "Fixing stats→(height,weight) leaves L5 boundary bug; multi-issue; "
            "also `>`→`>=` is semantic."
        ),
        abstain_reason=(
            "Multi-issue repair: binding stats alone leaves public equality failure; "
            "`>`→`>=` is semantic and does not fix NameError."
        ),
        alternative_explanations="",
        unresolved_reason="",
        counterexample_notes=(
            "Changing only `>` to `>=` does not fix NameError; binding stats alone leaves "
            "public equality failure."
        ),
    )


def _find_length(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=[
            "duplicate_definition_override",
            "packaging_or_scaffold_residue",
            "test_execution_failure_signal",
        ],
        confidence="LOW",
        eligibility="abstain",
        ambiguity="UNRESOLVED",
        ambiguity_count=2,
        evidence_summary=(
            "phase=completed with two find_length definitions where the last wins; "
            "module assert is present and module completed, so the public assert path "
            "did not raise. Outcome有效≠layer閉合: duplicate_definition is a mechanism tag, "
            "not automatic L2 (G3e PASS, last-wins, public module assert did not raise). "
            "test_execution_failure_signal proves this is a valid failure cell but the "
            "hidden cause is not inspectable from frozen static evidence. Packaging "
            "residue is visible. Machine census reports ambiguous entry, test_failure, "
            "and packaging signals."
        ),
        chain_layer="UNRESOLVED",
        chain_mechanism="duplicate_definition_public_pass_unresolved",
        healer_family="duplicate_definition_resolution",
        eligibility_reason=(
            "Last-wins definition executes and satisfies public module assert; hidden "
            "test failure path not inspectable from frozen static evidence."
        ),
        abstain_reason=(
            "Outcome validity does not close taxonomy layer; cannot choose which duplicate "
            "definition to keep or whether hidden tests fail for semantic vs packaging "
            "reasons without hidden oracle."
        ),
        alternative_explanations=(
            "Hidden EvalPlus assertion failure vs benign packaging residue vs "
            "alternate duplicate body semantics."
        ),
        unresolved_reason=(
            "Public contract passes at module stage; test_execution_failure_signal "
            "cannot be mapped to a taxonomy layer without hidden tests."
        ),
        counterexample_notes=(
            "Removing first duplicate may not fix hidden tests; L2 not automatic when "
            "G3e PASS and last-wins body executes; outcome有效≠layer閉合."
        ),
    )


def _get_ludic_recursive(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "self_recursive_override",
            "duplicate_definition_override",
            "memory_error",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Two get_ludic definitions; the second calls list(get_ludic(n)) after "
            "overriding the first, causing self-recursion and MemoryError. Machine "
            "signals include ambiguous entry and module_execution_exception."
        ),
        chain_layer="L4",
        chain_mechanism="self_recursive_override",
        healer_family="ludic_algorithm_rebuild",
        eligibility_reason="Repair requires choosing which duplicate to keep and rebuilding ludic algorithm.",
        abstain_reason=(
            "Non-unique duplicate-definition resolution plus full algorithm rebuild; "
            "deleting 2nd vs keeping 1st both leave non-ludic algorithm."
        ),
        counterexample_notes=(
            "Deleting second definition vs keeping first both leave non-ludic algorithm; "
            "intentional recursion counterexample; abstain."
        ),
    )


def _maximize_elements_zip(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "broken_collection_construction",
            "duplicate_definition_override",
            "runtime_type_error",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Two maximize_elements definitions; the last uses broken zip/sorted "
            "construction leading to TypeError at runtime."
        ),
        chain_layer="L4",
        chain_mechanism="broken_zip_sorted_construction",
        healer_family="pairwise_zip_repair",
        eligibility_reason="Fix requires rebuilding pairwise zip/sorted construction, not a single-token patch.",
        abstain_reason=(
            "Duplicate definitions make deterministic healer choice non-unique; "
            "multiple zip/pairwise reconstructions possible."
        ),
        counterexample_notes=(
            "Patching zip alone on last definition ignores which duplicate should survive; "
            "multiple zip/pairwise reconstructions; abstain."
        ),
    )


def _find_kth_partition(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "partition_index_error",
            "duplicate_definition_override",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Two find_kth definitions; the last has an IndexError path visible in "
            "partition index arithmetic."
        ),
        chain_layer="L4",
        chain_mechanism="partition_index_error",
        healer_family="partition_search_repair",
        eligibility_reason="Partition guard repair is non-unique with duplicate definitions present.",
        abstain_reason=(
            "Cannot deterministically select surviving definition and partition fix; "
            "clamp vs loop rewrite vs keep other duplicate all plausible."
        ),
        counterexample_notes=(
            "Index guard on last definition may not match intended algorithm in first "
            "definition; clamp vs loop rewrite vs keep other duplicate; abstain."
        ),
    )


def _capital_words_index(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "index_error",
            "duplicate_definition_override",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Two capital_words_spaces definitions; the last can IndexError on empty "
            "word[0] access."
        ),
        chain_layer="L4",
        chain_mechanism="empty_word_index_error",
        healer_family="empty_token_guard_repair",
        eligibility_reason="Empty-word guard is insufficient without choosing surviving duplicate definition.",
        abstain_reason=(
            "Duplicate definitions block unique deterministic repair; "
            "guard vs rewrite vs other duplicate all plausible."
        ),
        counterexample_notes=(
            "Adding empty-string guard to last definition does not resolve duplicate "
            "override ambiguity; guard vs rewrite vs other duplicate; abstain."
        ),
    )


def _pair_xor_sum(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L5",
        secondary=[],
        mechanisms=[
            "algorithmic_logic_error",
            "xor_accumulate_instead_of_sum",
            "duplicate_definition_override",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "Two pair_xor_Sum definitions; the last uses total ^= nums[i]^nums[j] but "
            "the public name/contract require SUM of pair xors. Public static arithmetic "
            "on example [5,9,7,6]: 5^9+5^7+5^6+9^7+9^6+7^6=47 supports primary L5. "
            "phase=completed. Operator ^=→+= is semantic L5 rewrite; not eligible even "
            "if 'clear'; cannot generalize as Healer without task-specific oracle risk."
        ),
        chain_layer="L5",
        chain_mechanism="xor_accumulate_instead_of_sum",
        healer_family="algorithmic_semantic_repair",
        eligibility_reason=(
            "L5 algorithmic logic error is outside deterministic healer scope; "
            "operator ^=→+= is semantic; cannot generalize without task-specific oracle."
        ),
        abstain_reason=(
            "Changing ^= to += is a semantic operator change, not a deterministic "
            "syntax/healer patch; public arithmetic 47 confirms L5 primary."
        ),
        counterexample_notes=(
            "Initializing total or fixing NameError would not implement pair-xor-sum; "
            "requires algorithm rebuild from public contract; ^=→+= is semantic L5."
        ),
    )


def _maximize_elements_unbound(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "unbound_name",
            "packaging_or_scaffold_residue",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "maximize_elements uses unbound t2 in zip(t1,t2), causing NameError. "
            "Packaging comments are present. This is not an import issue despite the "
            "machine import_or_name_resolution signal."
        ),
        chain_layer="L4",
        chain_mechanism="unbound_name_t2",
        healer_family="pairwise_zip_repair",
        eligibility_reason="Fix requires reconstructing pairwise zip algorithm, not merely binding t2.",
        abstain_reason=(
            "Unbound t2 fix implies algorithm intent reconstruction beyond deterministic "
            "healer; no unique near binding for t2."
        ),
        counterexample_notes=(
            "Binding t2 to an arbitrary iterable does not restore correct maximize_elements "
            "logic; needs tuples2[i] zip algorithm; no unique near binding for t2; abstain."
        ),
    )


def _get_ludic_unbound(_pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "unbound_name",
            "packaging_or_scaffold_residue",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        ambiguity="UNAMBIGUOUS",
        ambiguity_count=0,
        evidence_summary=(
            "get_ludic uses result.append without initializing result, causing NameError. "
            "Module Assign docstring packaging is present; the ludic algorithm is also wrong."
        ),
        chain_layer="L4",
        chain_mechanism="unbound_name_result",
        healer_family="ludic_algorithm_rebuild",
        eligibility_reason=(
            "Initializing result fixes NameError but ludic algorithm remains broken; multi-issue repair."
        ),
        abstain_reason=(
            "NameError initialization alone insufficient; full ludic algorithm rebuild "
            "required; result=[] unique for NameError but leaves broken ludic algorithm."
        ),
        counterexample_notes=(
            "result=[] patch leaves incorrect ludic sequence; adjacent case where result "
            "should be generator; multi-issue repair; abstain."
        ),
    )


FILTER_DATA_PIDS = frozenset({
    "125c6e3294d8d8284451ce7aa9cfe85e0fbffe5c6825436ab01e670ea86bd6e4",
    "24b1527f11421023266b2d27cf4e595d94ac9f7899dea442a361bba5d87d83b3",
    "488d43e2c4a8008d1e3a26b5867ad156317388c6c86aa94943e4db152e7b1091",
    "a1f89435d65b81afbd0d0ba1668834d6ab0b9b50a9a57e28e91b1f4e34e7f713",
    "fe973455ae8aa6d18d84cc677a9789d83520d0257a3d01fa61fa796a4371ac12",
})

DECISIONS: dict[str, dict[str, Any]] = {
    **{pid: _filter_data(pid) for pid in FILTER_DATA_PIDS},
    "7d222fbf55bad2d3b5d9c780f0fab275d7a48eddfe0646b7aec968b0fb898d28": _find_length(
        "7d222fbf55bad2d3b5d9c780f0fab275d7a48eddfe0646b7aec968b0fb898d28"
    ),
    "8699ddc85623d70a3dbe7a1089a83253609f045283508b07921ba71c727553f2": _get_ludic_recursive(
        "8699ddc85623d70a3dbe7a1089a83253609f045283508b07921ba71c727553f2"
    ),
    "8d29dd7b90d6f6d5d40952fa779359cdfdffae349a2878878b394031ed030d8a": _maximize_elements_zip(
        "8d29dd7b90d6f6d5d40952fa779359cdfdffae349a2878878b394031ed030d8a"
    ),
    "9e18ea3b77dec3889b77aee7d178f530cc35c7395c53cb0e6d2c87af57c80dd6": _find_kth_partition(
        "9e18ea3b77dec3889b77aee7d178f530cc35c7395c53cb0e6d2c87af57c80dd6"
    ),
    "a8954da149cf2b2798c61370566a7ffae02a90b9b497e047e36999d7a77a653d": _capital_words_index(
        "a8954da149cf2b2798c61370566a7ffae02a90b9b497e047e36999d7a77a653d"
    ),
    "c0c3cb24fc5d28ad23b148ccbebed6139d95e7086ae028e689fc30b7c0413d4a": _pair_xor_sum(
        "c0c3cb24fc5d28ad23b148ccbebed6139d95e7086ae028e689fc30b7c0413d4a"
    ),
    "e12feb3667f7a809b689e3e42dafe4383bdfdde20626cc3ba890655d92a61d7f": _maximize_elements_unbound(
        "e12feb3667f7a809b689e3e42dafe4383bdfdde20626cc3ba890655d92a61d7f"
    ),
    "e913935149eda6911282b2a55b7d9d5cae085f851c495a40ae567a9ffeccd7a8": _get_ludic_unbound(
        "e913935149eda6911282b2a55b7d9d5cae085f851c495a40ae567a9ffeccd7a8"
    ),
}


def _load_cluster(
    root: Path = ROOT,
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]], set[str], set[str]]:
    verify_sources(root)
    manifest_path = _path(root, MACHINE_CENSUS_MANIFEST)
    _require(
        _sha(manifest_path.read_bytes()) == MACHINE_CENSUS_MANIFEST_SHA256,
        "machine census manifest SHA drift",
    )
    module_exception_manifest = _path(root, MODULE_EXCEPTION_MANIFEST)
    _require(
        _sha(module_exception_manifest.read_bytes()) == MODULE_EXCEPTION_MANIFEST_SHA256,
        "module exception manifest SHA drift",
    )
    census_rows = _read_csv(_path(root, MACHINE_CENSUS_CSV))
    roster_rows = _read_csv(_path(root, MACHINE_CENSUS_ROSTER))
    g2_rows = _read_csv(_path(root, G2_PROVISIONAL_CSV))
    module_exception_rows = _read_csv(_path(root, MODULE_EXCEPTION_CSV))
    roster_by_program = {row["program_id"]: row for row in roster_rows}
    g2_ids = {row["program_id"] for row in g2_rows}
    module_exception_ids = {row["program_id"] for row in module_exception_rows}
    cluster = [
        row
        for row in census_rows
        if row["operational_cluster"] == TARGET_CLUSTER
    ]
    cluster = sorted(cluster, key=lambda row: row["program_id"])
    _require(len(cluster) == TARGET_CELLS, f"cluster cell count drift: expected {TARGET_CELLS}, got {len(cluster)}")
    cluster_ids = {row["program_id"] for row in cluster}
    _require(cluster_ids <= set(roster_by_program), "cluster program outside remaining171 roster")
    _require(not (cluster_ids & g2_ids), "cluster intersects G2_module provisional set")
    _require(not (cluster_ids & module_exception_ids), "cluster intersects module_exception provisional set")
    _require(set(DECISIONS) == cluster_ids, "decision identity set drift")
    return cluster, roster_by_program, g2_ids, module_exception_ids


def build_rows(root: Path = ROOT) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cluster, roster_by_program, _g2_ids, _module_exception_ids = _load_cluster(root)
    diagnostics = {row["program_id"]: row for row in _read_csv(_path(root, preparation.FORMAL_RESULTS))}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(_path(root, preparation.JOURNAL))
        if row["healer_account"] == "H0"
    }

    roster_out: list[dict[str, Any]] = []
    adjudication_out: list[dict[str, Any]] = []

    for rank, census_row in enumerate(cluster, 1):
        program_id = census_row["program_id"]
        roster_row = roster_by_program[program_id]
        diagnostic = diagnostics[program_id]
        journal = journals[program_id]
        source = journal["evaluation_source"]
        _require(
            _sha(source.encode("utf-8"))
            == census_row.get("evaluation_source_sha256", roster_row["evaluation_source_sha256"]),
            f"source identity drift: {program_id}",
        )
        ast.parse(source)
        candidate_line = diagnostic.get("model_source_line", "")
        evidence_paths = [
            preparation.TASKS.as_posix(),
            preparation.JOURNAL.as_posix(),
            preparation.FORMAL_RESULTS.as_posix(),
            MACHINE_CENSUS_CSV.as_posix(),
            preparation.TAXONOMY_CODEBOOK.as_posix(),
        ]
        evidence_locator = (
            f"{preparation.FORMAL_RESULTS.as_posix()}#program_id={program_id};"
            f"phase={census_row['diagnostic_phase']};"
            f"exception_class={census_row['diagnostic_exception_class']};"
            f"line={candidate_line}"
        )
        decision = dict(DECISIONS[program_id])
        decision.pop("counterexample_notes", None)
        roster_out.append(
            {
                "cluster_rank": rank,
                "program_id": program_id,
                "cell_identity_sha256": census_row["cell_identity_sha256"],
                "dataset": "MBPP+",
                "task_id": census_row["task_id"],
                "condition": "Candidate_B/H0",
                "seed": census_row["seed"],
                "generation_id": roster_row["generation_id"],
                "evaluation_source_sha256": roster_row["evaluation_source_sha256"],
                "required_entry_point": census_row["required_entry_point"],
                "operational_cluster": TARGET_CLUSTER,
                "frozen_machine_signals": census_row["all_observed_machine_signals"],
                "diagnostic_phase": census_row["diagnostic_phase"],
                "diagnostic_exception_class": census_row["diagnostic_exception_class"],
                "diagnostic_candidate_line": candidate_line,
                "inclusion_reason": f"operational_cluster=={TARGET_CLUSTER}",
                "machine_census_roster_rank": roster_row["roster_rank"],
            }
        )
        adjudication_out.append(
            {
                "program_id": program_id,
                "cell_identity_sha256": census_row["cell_identity_sha256"],
                "task_id": census_row["task_id"],
                "seed": census_row["seed"],
                "operational_cluster": TARGET_CLUSTER,
                "all_observed_machine_signals": census_row["all_observed_machine_signals"],
                **decision,
                "evidence_source_paths": _json(evidence_paths),
                "evidence_locator": evidence_locator,
                "adjudication_status": STATUS,
            }
        )

    primary_counts = Counter(row["provisional_primary_layer"] for row in adjudication_out)
    _require(
        primary_counts == Counter({"L4": 11, "L5": 1, "UNRESOLVED": 1}),
        "primary layer distribution drift",
    )
    secondary_l5 = sum(
        1 for row in adjudication_out if "L5" in json.loads(row["provisional_secondary_layers"])
    )
    _require(secondary_l5 == 5, "secondary L5 cell count drift")
    mechanism_meec = sum(
        1
        for row in adjudication_out
        if "module_execution_exception" in json.loads(row["mechanism_tags"])
    )
    _require(mechanism_meec == 11, "module_execution_exception mechanism count drift")
    confidence_counts = Counter(row["confidence"] for row in adjudication_out)
    _require(
        confidence_counts == Counter({"HIGH": 12, "LOW": 1}),
        "confidence distribution drift",
    )
    for row in adjudication_out:
        primary = row["provisional_primary_layer"]
        secondary = json.loads(row["provisional_secondary_layers"])
        _require(
            all(layer in VALID_SECONDARY_LAYERS for layer in secondary),
            f"secondary layer schema violation: {row['program_id']}",
        )
        _require(primary not in secondary, f"primary duplicated in secondary: {row['program_id']}")
    _require(
        Counter(row["healer_eligibility"] for row in adjudication_out) == Counter({"abstain": 13}),
        "healer eligibility distribution drift",
    )
    _require(all(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in adjudication_out), "outcome validity drift")
    return roster_out, adjudication_out


def _healer_candidate_detail_rows(adjudication_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in adjudication_rows:
        decision = DECISIONS[row["program_id"]]
        eligibility = row["healer_eligibility"]
        rows.append(
            {
                "program_id": row["program_id"],
                "cell_identity_sha256": row["cell_identity_sha256"],
                "healer_eligibility": eligibility,
                "healer_candidate_family": row["healer_candidate_family"],
                "eligibility_reason": row["eligibility_reason"],
                "proposed_rule_family": "" if eligibility == "abstain" else row["proposed_rule_family"],
                "required_preconditions": row["required_preconditions"],
                "counterexample_notes": decision["counterexample_notes"],
            }
        )
    return rows


def _summary_tables(adjudication_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    primary_counter = Counter(row["provisional_primary_layer"] for row in adjudication_rows)
    primary_rows = [
        {"layer": layer, "cells": primary_counter.get(layer, 0)}
        for layer in ("L0", "L1", "L2", "L3", "L4", "L5", "UNRESOLVED")
    ]

    secondary_counter: Counter[str] = Counter()
    for row in adjudication_rows:
        secondary_counter.update(json.loads(row["provisional_secondary_layers"]))
    secondary_rows = [
        {"layer": layer, "cells": secondary_counter.get(layer, 0)}
        for layer in ("L0", "L1", "L2", "L3", "L4", "L5")
    ]

    mechanism_counter: Counter[str] = Counter()
    for row in adjudication_rows:
        mechanism_counter.update(json.loads(row["mechanism_tags"]))
    mechanism_rows = [{"mechanism_tag": tag, "cells": count} for tag, count in sorted(mechanism_counter.items())]

    outcome_rows = [
        {"outcome_validity": value, "cells": count}
        for value, count in sorted(Counter(row["outcome_validity"] for row in adjudication_rows).items())
    ]
    eligibility_rows = [
        {"healer_eligibility": value, "cells": count}
        for value, count in sorted(Counter(row["healer_eligibility"] for row in adjudication_rows).items())
    ]
    confidence_rows = [
        {"confidence": value, "cells": count}
        for value, count in sorted(Counter(row["confidence"] for row in adjudication_rows).items())
    ]

    chain_counter: Counter[tuple[str, str]] = Counter()
    for row in adjudication_rows:
        chain = json.loads(row["failure_chain"])
        if chain:
            first = chain[0]
            chain_counter[(first.get("layer", ""), first.get("mechanism", ""))] += 1
    failure_chain_rows = [
        {"chain_layer": layer, "chain_mechanism": mechanism, "cells": count}
        for (layer, mechanism), count in sorted(chain_counter.items())
    ]

    crosstab_counter = Counter(
        (row["operational_cluster"], row["provisional_primary_layer"]) for row in adjudication_rows
    )
    crosstab_rows = [
        {
            "operational_cluster": cluster,
            "provisional_primary_layer": layer,
            "cells": count,
        }
        for (cluster, layer), count in sorted(crosstab_counter.items())
    ]

    unresolved_rows = [
        {
            "program_id": row["program_id"],
            "cell_identity_sha256": row["cell_identity_sha256"],
            "provisional_primary_layer": row["provisional_primary_layer"],
            "ambiguity_status": row["ambiguity_status"],
            "confidence": row["confidence"],
            "evidence_summary": row["evidence_summary"],
        }
        for row in adjudication_rows
        if row["ambiguity_status"] == "UNRESOLVED" or row["provisional_primary_layer"] == "UNRESOLVED"
    ]

    evidence_rows = [
        {"flag": "cells", "value": str(len(adjudication_rows))},
        {"flag": "hidden_expected_actual_used", "value": "0"},
        {"flag": "h1_result_used", "value": "0"},
        {"flag": "evalplus_correctness_loaded", "value": "0"},
        {"flag": "healer_runtime_input", "value": "0"},
        {"flag": "new_diagnostics_executed", "value": "0"},
        {"flag": "programs_executed", "value": "0"},
        {"flag": "public_task_contract_only", "value": str(len(adjudication_rows))},
        {"flag": "frozen_h0_source_parsed", "value": str(len(adjudication_rows))},
        {"flag": "coarse_diagnostics_phase_class_line", "value": str(len(adjudication_rows))},
    ]

    return {
        "primary_layer_summary.csv": primary_rows,
        "secondary_layer_summary.csv": secondary_rows,
        "mechanism_tag_summary.csv": mechanism_rows,
        "outcome_validity_summary.csv": outcome_rows,
        "healer_eligibility_summary.csv": eligibility_rows,
        "failure_chain_summary.csv": failure_chain_rows,
        "confidence_summary.csv": confidence_rows,
        "machine_signal_taxonomy_crosstab.csv": crosstab_rows,
        "unresolved_detail.csv": unresolved_rows,
        "evidence_coverage_summary.csv": evidence_rows,
    }


def _methodology_report(primary_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Candidate B r003 taxonomy v3：remaining134 multiple_signal_chain provisional adjudication v1",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "本 revision 針對 remaining171 machine census 中 `operational_cluster == multiple_signal_chain` 的 13 格，",
        "以 frozen H0 source、AST、coarse diagnostics phase/class/line 與 public prompt contract 進行 AI-assisted provisional adjudication。",
        "**不是**正式人工裁決；未載入 H1、hidden expected、新 diagnostics、EvalPlus 或 Healer；未重新執行程式。",
        "",
        "## Primary layer 彙總",
        "",
        "| Layer | Cells |",
        "|---|---:|",
    ]
    for row in primary_rows:
        if int(row["cells"]) > 0:
            lines.append(f"| `{row['layer']}` | {row['cells']} |")
    lines.extend(
        [
            "",
            "## 方法學邊界",
            "",
            "- machine census manifest SHA 已釘選驗證",
            "- 母體為 remaining171 roster；與 G2_module 27 及 module_exception 37 交集均為 0",
            "- machine signals 為輸入線索，不得直接等同 taxonomy layer",
            "- outcome_validity 一律 VALID_MODEL_OUTCOME（模型失敗路徑）",
            "- healer_eligibility 均為 abstain；未宣稱 Healer 安全或充分",
            "- pre-freeze adversarial audit 已執行；修訂後 verdict READY_TO_FREEZE_WITHOUT_CHANGE",
            "- mechanism tag 政策：specific tags 恆保留；frozen diagnostic phase 在 "
            "{G2_base,G2_plus} 且 termination raised 時另加 module_execution_exception",
            "- outcome_validity ≠ taxonomy layer 確定性；VALID_MODEL_OUTCOME 可與 UNRESOLVED primary 並存",
            "",
        ]
    )
    return "\n".join(lines)


def _adjudication_protocol() -> str:
    return "\n".join(
        [
            "# Adjudication protocol（multiple_signal_chain provisional v1）",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            "## 輸入",
            "",
            "- frozen machine census v1（manifest SHA 釘選）",
            "- remaining171 fixed roster",
            "- coarse diagnostics phase / exception_class / model_source_line",
            "- H0 evaluation_source（AST parse only）",
            "- public task contract（prompt + entry point）",
            "",
            "## 禁止",
            "",
            "- 不執行程式、EvalPlus、diagnostics、Healer",
            "- 不載入 H1、hidden expected/actual、exception message、traceback",
            "- 不修改 machine census、G2 provisional 或 module_exception provisional 產物",
            "",
            "## Mechanism tag 政策",
            "",
            "- specific mechanism tags 恆保留（如 unbound_name_stats、self_recursive_override）",
            "- 另加 generic `module_execution_exception` **iff** frozen diagnostic phase 在 "
            "{G2_base, G2_plus} 且 termination 為 raised",
            "- phase=completed 的 cell（如 Mbpp/125 find_length、c0c3cb xor_accumulate）不加 "
            "module_execution_exception",
            "",
            "## Secondary layer 政策",
            "",
            "- L5 secondary 僅在 public arithmetic 可證時標記（如 Mbpp/722 filter_data 五格）",
            "- L4 primary cell 不得無 public 證據猜測 L5 secondary",
            "",
            "## Outcome validity",
            "",
            "- outcome_validity ≠ taxonomy layer 確定性",
            "- VALID_MODEL_OUTCOME 表示模型失敗路徑有效，不強制 primary layer 閉合",
            "",
            "## 輸出",
            "",
            "- 13 列 ai_provisional_adjudication.csv",
            "- fixed_cluster_roster.csv、healer_candidate_detail.csv 與 summary / manifest / provenance",
            "- pre_freeze_adversarial_audit.csv / pre_freeze_adversarial_audit_zh.md",
            "",
        ]
    )


AUDIT_FIELDS = (
    "check_id",
    "affected_program_id",
    "task_id",
    "original_outcome_validity",
    "audited_outcome_validity",
    "original_primary",
    "audited_primary",
    "original_secondary",
    "audited_secondary",
    "original_mechanism_tags",
    "audited_mechanism_tags",
    "original_failure_chain",
    "audited_failure_chain",
    "original_eligibility",
    "audited_eligibility",
    "issue_type",
    "evidence",
    "alternative_explanation",
    "action_required",
    "verdict",
)

_FILTER_DATA_ORIG_MECH = _json(["nameerror_without_locatable_binding", "module_execution_exception"])
_FILTER_DATA_AUD_MECH = _json([
    "unbound_name",
    "unbound_name_stats",
    "strict_inequality_boundary",
    "module_execution_exception",
])
_FILTER_DATA_ORIG_CHAIN = _json([{
    "stage": "raw_module_execution",
    "gate": "G2",
    "layer": "UNRESOLVED",
    "mechanism": "nameerror_without_locatable_binding",
    "outcome_validity": "VALID_MODEL_OUTCOME",
}])
_FILTER_DATA_AUD_CHAIN = _json([
    {
        "stage": "causal_mechanism",
        "gate": "G1",
        "layer": "L4",
        "mechanism": "unbound_name_stats",
        "outcome_validity": "VALID_MODEL_OUTCOME",
    },
    {
        "stage": "first_observable_failure",
        "gate": "G2",
        "layer": "L4",
        "mechanism": "nameerror_on_unbound_stats",
        "outcome_validity": "VALID_MODEL_OUTCOME",
    },
    {
        "stage": "downstream_public_contract",
        "gate": "G4",
        "layer": "L5",
        "mechanism": "strict_inequality_boundary",
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "evidence_scope": "public_contract_only",
    },
])

L4_CELL_PIDS = (
    "8699ddc85623d70a3dbe7a1089a83253609f045283508b07921ba71c727553f2",
    "8d29dd7b90d6f6d5d40952fa779359cdfdffae349a2878878b394031ed030d8a",
    "9e18ea3b77dec3889b77aee7d178f530cc35c7395c53cb0e6d2c87af57c80dd6",
    "a8954da149cf2b2798c61370566a7ffae02a90b9b497e047e36999d7a77a653d",
    "e12feb3667f7a809b689e3e42dafe4383bdfdde20626cc3ba890655d92a61d7f",
    "e913935149eda6911282b2a55b7d9d5cae085f851c495a40ae567a9ffeccd7a8",
)

L4_CELL_TASKS = {
    "8699ddc85623d70a3dbe7a1089a83253609f045283508b07921ba71c727553f2": "Mbpp/603",
    "8d29dd7b90d6f6d5d40952fa779359cdfdffae349a2878878b394031ed030d8a": "Mbpp/259",
    "9e18ea3b77dec3889b77aee7d178f530cc35c7395c53cb0e6d2c87af57c80dd6": "Mbpp/597",
    "a8954da149cf2b2798c61370566a7ffae02a90b9b497e047e36999d7a77a653d": "Mbpp/748",
    "e12feb3667f7a809b689e3e42dafe4383bdfdde20626cc3ba890655d92a61d7f": "Mbpp/259",
    "e913935149eda6911282b2a55b7d9d5cae085f851c495a40ae567a9ffeccd7a8": "Mbpp/603",
}

L4_CELL_MECH_BEFORE = {
    "8699ddc85623d70a3dbe7a1089a83253609f045283508b07921ba71c727553f2": _json([
        "self_recursive_override", "duplicate_definition_override", "memory_error",
    ]),
    "8d29dd7b90d6f6d5d40952fa779359cdfdffae349a2878878b394031ed030d8a": _json([
        "broken_collection_construction", "duplicate_definition_override", "runtime_type_error",
    ]),
    "9e18ea3b77dec3889b77aee7d178f530cc35c7395c53cb0e6d2c87af57c80dd6": _json([
        "partition_index_error", "duplicate_definition_override",
    ]),
    "a8954da149cf2b2798c61370566a7ffae02a90b9b497e047e36999d7a77a653d": _json([
        "index_error", "duplicate_definition_override",
    ]),
    "e12feb3667f7a809b689e3e42dafe4383bdfdde20626cc3ba890655d92a61d7f": _json([
        "unbound_name", "packaging_or_scaffold_residue", "module_execution_exception",
    ]),
    "e913935149eda6911282b2a55b7d9d5cae085f851c495a40ae567a9ffeccd7a8": _json([
        "unbound_name", "packaging_or_scaffold_residue", "module_execution_exception",
    ]),
}

L4_CELL_MECH_AFTER = {
    pid: _json(json.loads(L4_CELL_MECH_BEFORE[pid]) + (
        ["module_execution_exception"]
        if "module_execution_exception" not in json.loads(L4_CELL_MECH_BEFORE[pid])
        else []
    ))
    for pid in L4_CELL_PIDS
}


def _audit_row(
    check_id: str,
    affected_program_id: str,
    task_id: str,
    original_primary: str,
    audited_primary: str,
    original_secondary: str,
    audited_secondary: str,
    original_mechanism_tags: str,
    audited_mechanism_tags: str,
    original_failure_chain: str,
    audited_failure_chain: str,
    issue_type: str,
    evidence: str,
    action_required: str,
    verdict: str,
    original_outcome_validity: str = "VALID_MODEL_OUTCOME",
    audited_outcome_validity: str = "VALID_MODEL_OUTCOME",
    original_eligibility: str = "abstain",
    audited_eligibility: str = "abstain",
    alternative_explanation: str = "",
) -> dict[str, str]:
    return {
        "check_id": check_id,
        "affected_program_id": affected_program_id,
        "task_id": task_id,
        "original_outcome_validity": original_outcome_validity,
        "audited_outcome_validity": audited_outcome_validity,
        "original_primary": original_primary,
        "audited_primary": audited_primary,
        "original_secondary": original_secondary,
        "audited_secondary": audited_secondary,
        "original_mechanism_tags": original_mechanism_tags,
        "audited_mechanism_tags": audited_mechanism_tags,
        "original_failure_chain": original_failure_chain,
        "audited_failure_chain": audited_failure_chain,
        "original_eligibility": original_eligibility,
        "audited_eligibility": audited_eligibility,
        "issue_type": issue_type,
        "evidence": evidence,
        "alternative_explanation": alternative_explanation,
        "action_required": action_required,
        "verdict": verdict,
    }


def _build_pre_freeze_audit_ledger() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pid in sorted(FILTER_DATA_PIDS):
        rows.append(_audit_row(
            check_id="PROV-722",
            affected_program_id=pid,
            task_id="Mbpp/722",
            original_primary="UNRESOLVED",
            audited_primary="L4",
            original_secondary="[]",
            audited_secondary='["L5"]',
            original_mechanism_tags=_FILTER_DATA_ORIG_MECH,
            audited_mechanism_tags=_FILTER_DATA_AUD_MECH,
            original_failure_chain=_FILTER_DATA_ORIG_CHAIN,
            audited_failure_chain=_FILTER_DATA_AUD_CHAIN,
            issue_type="provenance_line_offset_nameerror",
            evidence=(
                "prompt.count('\\n')=4; model_source_line=6 → candidate line 2; "
                "dict comp loads stats but never stores it → NameError; SHA c0d3c323…"
            ),
            alternative_explanation="Mechanical import signal does not explain locatable binding",
            action_required="reclassify primary UNRESOLVED→L4; add secondary L5 strict_inequality_boundary",
            verdict="REVISE",
        ))
    rows.append(_audit_row(
        check_id="MBPP125-001",
        affected_program_id="7d222fbf55bad2d3b5d9c780f0fab275d7a48eddfe0646b7aec968b0fb898d28",
        task_id="Mbpp/125",
        original_primary="UNRESOLVED",
        audited_primary="UNRESOLVED",
        original_secondary="[]",
        audited_secondary="[]",
        original_mechanism_tags=_json([
            "duplicate_definition_override",
            "packaging_or_scaffold_residue",
            "test_execution_failure_signal",
        ]),
        audited_mechanism_tags=_json([
            "duplicate_definition_override",
            "packaging_or_scaffold_residue",
            "test_execution_failure_signal",
        ]),
        original_failure_chain=_json([{
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "UNRESOLVED",
            "mechanism": "duplicate_definition_public_pass_unresolved",
            "outcome_validity": "VALID_MODEL_OUTCOME",
        }]),
        audited_failure_chain=_json([{
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "UNRESOLVED",
            "mechanism": "duplicate_definition_public_pass_unresolved",
            "outcome_validity": "VALID_MODEL_OUTCOME",
        }]),
        issue_type="outcome_valid_layer_unclosed",
        evidence=(
            "phase=completed; G3e PASS; duplicate_definition is mechanism not L2; "
            "test_execution_failure_signal valid but hidden cause not inspectable"
        ),
        alternative_explanation="Hidden EvalPlus failure vs packaging residue",
        action_required="keep UNRESOLVED; strengthen outcome有效≠layer閉合 evidence",
        verdict="ACCEPT",
    ))
    for idx, pid in enumerate(L4_CELL_PIDS, 1):
        rows.append(_audit_row(
            check_id=f"L4-{idx:03d}",
            affected_program_id=pid,
            task_id=L4_CELL_TASKS[pid],
            original_primary="L4",
            audited_primary="L4",
            original_secondary="[]",
            audited_secondary="[]",
            original_mechanism_tags=L4_CELL_MECH_BEFORE[pid],
            audited_mechanism_tags=L4_CELL_MECH_AFTER[pid],
            original_failure_chain="",
            audited_failure_chain="",
            issue_type="l4_primary_abstain_strengthen",
            evidence="primary L4 confirmed; healer abstain counterexamples strengthened",
            action_required="none",
            verdict="ACCEPT",
        ))
    rows.append(_audit_row(
        check_id="L5-XOR",
        affected_program_id="c0c3cb24fc5d28ad23b148ccbebed6139d95e7086ae028e689fc30b7c0413d4a",
        task_id="Mbpp/633",
        original_primary="L5",
        audited_primary="L5",
        original_secondary="[]",
        audited_secondary="[]",
        original_mechanism_tags=_json([
            "algorithmic_logic_error",
            "xor_accumulate_instead_of_sum",
            "duplicate_definition_override",
        ]),
        audited_mechanism_tags=_json([
            "algorithmic_logic_error",
            "xor_accumulate_instead_of_sum",
            "duplicate_definition_override",
        ]),
        original_failure_chain="",
        audited_failure_chain="",
        issue_type="l5_public_arithmetic_primary",
        evidence="public static arithmetic 5^9+5^7+5^6+9^7+9^6+7^6=47 supports primary L5; ^=→+= semantic",
        action_required="none",
        verdict="ACCEPT",
    ))
    rows.append(_audit_row(
        check_id="SEC-EMPTY",
        affected_program_id="ALL_13",
        task_id="",
        original_primary="",
        audited_primary="",
        original_secondary="[]",
        audited_secondary='["L5" x5 on Mbpp/722 filter_data]',
        original_mechanism_tags="",
        audited_mechanism_tags="",
        original_failure_chain="",
        audited_failure_chain="",
        issue_type="secondary_layer_initial_empty",
        evidence="pre-revision all secondary empty; post-revision 5 filter_data cells get L5 secondary",
        action_required=(
            "SECONDARY_REVISION_REQUIRED → applied → ALL_SECONDARY_CONFIRMED_WITH_L5_ON_722"
        ),
        verdict="REVISE",
    ))
    rows.append(_audit_row(
        check_id="MECH-POLICY",
        affected_program_id="ALL_13",
        task_id="",
        original_primary="",
        audited_primary="",
        original_secondary="",
        audited_secondary="",
        original_mechanism_tags="partial module_execution_exception coverage",
        audited_mechanism_tags="11 cells with module_execution_exception (G2_* raised only)",
        original_failure_chain="",
        audited_failure_chain="",
        issue_type="mechanism_tag_policy_consistency",
        evidence=(
            "specific tags always; add generic module_execution_exception iff "
            "frozen phase in {G2_base,G2_plus} and termination raised"
        ),
        action_required="add module_execution_exception to G2_* raised L4 cells lacking tag",
        verdict="ACCEPT",
    ))
    rows.append(_audit_row(
        check_id="HEAL-ALL",
        affected_program_id="ALL_13",
        task_id="",
        original_primary="",
        audited_primary="",
        original_secondary="",
        audited_secondary="",
        original_mechanism_tags="",
        audited_mechanism_tags="",
        original_failure_chain="",
        audited_failure_chain="",
        issue_type="healer_eligibility_consistency",
        evidence="each cell abstain with counterexample_notes citing non-unique repair or semantic rewrite",
        action_required="none",
        verdict="ACCEPT",
    ))
    rows.append(_audit_row(
        check_id="OUT-VALID",
        affected_program_id="ALL_13",
        task_id="",
        original_primary="",
        audited_primary="",
        original_secondary="",
        audited_secondary="",
        original_mechanism_tags="",
        audited_mechanism_tags="",
        original_failure_chain="",
        audited_failure_chain="",
        issue_type="outcome_validity_consistency",
        evidence=(
            "all 13 cells VALID_MODEL_OUTCOME; Mbpp/722 provenance OK after line-offset mapping; "
            "outcome_validity ≠ taxonomy certainty"
        ),
        action_required="none",
        verdict="ACCEPT",
    ))
    return rows


PRE_FREEZE_AUDIT_LEDGER: list[dict[str, str]] = _build_pre_freeze_audit_ledger()


def _audit_report_md(pre_verdict: str, post_verdict: str) -> str:
    revise = sum(1 for row in PRE_FREEZE_AUDIT_LEDGER if row["verdict"] == "REVISE")
    accept = sum(1 for row in PRE_FREEZE_AUDIT_LEDGER if row["verdict"] == "ACCEPT")
    return "\n".join(
        [
            "# Pre-freeze adversarial methodology audit（multiple_signal_chain 13-cell）",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Pre-revision verdict：`{pre_verdict}`**",
            f"**Post-revision verdict：`{post_verdict}`**",
            "",
            f"- Audit rows：{len(PRE_FREEZE_AUDIT_LEDGER)}",
            f"- REVISE findings：{revise}",
            f"- ACCEPT findings：{accept}",
            "",
            "## 修訂摘要",
            "",
            "- Mbpp/722 filter_data 五格：UNRESOLVED→L4 primary；secondary 加 L5 "
            "strict_inequality_boundary（public arithmetic 可證）",
            "- prompt-line offset provenance：prompt.count('\\n')=4；model_source_line=6→candidate line 2",
            "- module_execution_exception 加至 11 格 G2_* raised cell；completed-phase cell 不加",
            "- Mbpp/125 find_length 保留 UNRESOLVED；outcome有效≠layer閉合",
            "",
            "## Mechanism tag 政策",
            "",
            "- specific mechanism tags 恆保留",
            "- 另加 generic `module_execution_exception` **iff** frozen diagnostic phase 在 "
            "{G2_base, G2_plus} 且 termination raised",
            "",
            "## Outcome validity",
            "",
            "- outcome_validity ≠ taxonomy layer 確定性",
            "- VALID_MODEL_OUTCOME 可與 UNRESOLVED primary 並存",
            "",
            "Secondary policy verdict：`ALL_SECONDARY_CONFIRMED_WITH_L5_ON_722`",
            "",
        ]
    )


def build_outputs(root: Path = ROOT) -> dict[Path, bytes]:
    roster_rows, adjudication_rows = build_rows(root)
    summaries = _summary_tables(adjudication_rows)
    primary_rows = summaries["primary_layer_summary.csv"]
    healer_detail_rows = _healer_candidate_detail_rows(adjudication_rows)

    outputs: dict[Path, bytes] = {
        Path("fixed_cluster_roster.csv"): _csv_bytes(ROSTER_FIELDS, roster_rows),
        Path("ai_provisional_adjudication.csv"): _csv_bytes(ADJUDICATION_FIELDS, adjudication_rows),
        Path("healer_candidate_detail.csv"): _csv_bytes(HEALER_CANDIDATE_DETAIL_FIELDS, healer_detail_rows),
        Path("pre_freeze_adversarial_audit.csv"): _csv_bytes(AUDIT_FIELDS, PRE_FREEZE_AUDIT_LEDGER),
        Path("pre_freeze_adversarial_audit_zh.md"): _audit_report_md(
            "REVISION_REQUIRED_BEFORE_FREEZE",
            "READY_TO_FREEZE_WITHOUT_CHANGE",
        ).encode("utf-8"),
        Path("methodology_report_zh.md"): _methodology_report(primary_rows).encode("utf-8"),
        Path("adjudication_protocol_zh.md"): _adjudication_protocol().encode("utf-8"),
    }
    for name, rows in summaries.items():
        if name == "primary_layer_summary.csv":
            outputs[Path(name)] = _csv_bytes(("layer", "cells"), rows)
        elif name == "secondary_layer_summary.csv":
            outputs[Path(name)] = _csv_bytes(("layer", "cells"), rows)
        elif name == "mechanism_tag_summary.csv":
            outputs[Path(name)] = _csv_bytes(("mechanism_tag", "cells"), rows)
        elif name == "outcome_validity_summary.csv":
            outputs[Path(name)] = _csv_bytes(("outcome_validity", "cells"), rows)
        elif name == "healer_eligibility_summary.csv":
            outputs[Path(name)] = _csv_bytes(("healer_eligibility", "cells"), rows)
        elif name == "failure_chain_summary.csv":
            outputs[Path(name)] = _csv_bytes(("chain_layer", "chain_mechanism", "cells"), rows)
        elif name == "confidence_summary.csv":
            outputs[Path(name)] = _csv_bytes(("confidence", "cells"), rows)
        elif name == "machine_signal_taxonomy_crosstab.csv":
            outputs[Path(name)] = _csv_bytes(
                ("operational_cluster", "provisional_primary_layer", "cells"), rows
            )
        elif name == "unresolved_detail.csv":
            outputs[Path(name)] = _csv_bytes(
                (
                    "program_id",
                    "cell_identity_sha256",
                    "provisional_primary_layer",
                    "ambiguity_status",
                    "confidence",
                    "evidence_summary",
                ),
                rows,
            )
        elif name == "evidence_coverage_summary.csv":
            outputs[Path(name)] = _csv_bytes(("flag", "value"), rows)

    provenance = {
        "revision": OUTPUT_RELATIVE.name,
        "start_head": START_HEAD,
        "status": STATUS,
        "adjudication_status": STATUS,
        "taxonomy_version": preparation.TAXONOMY_VERSION,
        "diagnostics_runner_revision": preparation.DIAGNOSTICS_RUNNER_REVISION,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "module_exception_manifest_sha256": MODULE_EXCEPTION_MANIFEST_SHA256,
        "target_operational_cluster": TARGET_CLUSTER,
        "target_cells": TARGET_CELLS,
        "formal_human_adjudication": False,
        "two_human_blind_review_claimed": False,
        "cohens_kappa_computed": False,
        "h1_results_loaded": False,
        "hidden_expected_actual_loaded": False,
        "evalplus_correctness_loaded": False,
        "healer_runtime_input": False,
        "programs_executed": False,
    }
    execution_manifest = {
        "status": STATUS,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "programs_executed": 0,
        "researcher_reviews_completed": 0,
    }
    outputs[Path("provenance.json")] = _json_bytes(provenance)
    outputs[Path("execution_manifest.json")] = _json_bytes(execution_manifest)

    hashes = {path.as_posix(): _sha(data) for path, data in sorted(outputs.items(), key=lambda item: item[0].as_posix())}
    outputs[Path("manifest.json")] = _json_bytes({
        "revision": OUTPUT_RELATIVE.name,
        "status": STATUS,
        "adjudication_status": STATUS,
        "cells": TARGET_CELLS,
        "operational_cluster": TARGET_CLUSTER,
        "machine_census_manifest_sha256": MACHINE_CENSUS_MANIFEST_SHA256,
        "module_exception_manifest_sha256": MODULE_EXCEPTION_MANIFEST_SHA256,
        "primary_layer_counts": {row["layer"]: row["cells"] for row in primary_rows if int(row["cells"]) > 0},
        "healer_eligibility_counts": {"abstain": TARGET_CELLS},
        "source_hashes_verified": len(SOURCE_HASHES),
        "outputs_sha256_excluding_manifest": hashes,
        "model_calls": 0,
        "evalplus_correctness_executions": 0,
        "diagnostics_executions": 0,
        "healer_executions": 0,
        "validation_executions": 0,
        "programs_executed": 0,
        "ai_assisted_adjudication_cells": TARGET_CELLS,
    })
    return outputs


def rewrite_outputs(root: Path = ROOT) -> Path:
    destination = root / OUTPUT_RELATIVE
    if destination.exists():
        for path in sorted(destination.iterdir(), reverse=True):
            if path.is_file():
                path.unlink()
    else:
        destination.mkdir(parents=True)
    for relative, data in build_outputs(root).items():
        (destination / relative).write_bytes(data)
    return destination


def write_outputs(root: Path = ROOT) -> Path:
    destination = root / OUTPUT_RELATIVE
    _require(not destination.exists(), f"output revision already exists: {destination}")
    destination.mkdir(parents=True)
    for relative, data in build_outputs(root).items():
        (destination / relative).write_bytes(data)
    return destination


if __name__ == "__main__":
    print(write_outputs())
