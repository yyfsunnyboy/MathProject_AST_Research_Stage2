#!/usr/bin/env python3
"""AI-assisted provisional adjudication for remaining171 module_execution_exception_signal cluster."""

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
    "candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1"
)
START_HEAD = "d3124cc2fa49c13b649a50e2892084a149eb24bd"
STATUS = "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW"
ANALYZER = Path(
    "scripts/adjudicate_candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1.py"
)
TESTS = Path(
    "tests/finals_rebuild/"
    "test_candidate_b_r003_taxonomy_v3_remaining171_module_exception_provisional_v1.py"
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

TARGET_CLUSTER = "module_execution_exception_signal"
TARGET_CELLS = 37
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
}

ROSTER_FIELDS = (
    "cluster_rank",
    "program_id",
    "cell_identity_sha256",
    "task_identity_sha256",
    "task_id",
    "seed",
    "generation_id",
    "required_entry_point",
    "operational_cluster",
    "diagnostic_phase",
    "diagnostic_exception_class",
    "evaluation_source_sha256",
    "inclusion_reason",
    "machine_census_roster_rank",
)

ADJUDICATION_FIELDS = (
    "program_id",
    "cell_identity_sha256",
    "operational_cluster",
    "provisional_primary_layer",
    "provisional_secondary_layers",
    "mechanism_tags",
    "outcome_validity",
    "failure_chain",
    "healer_eligibility",
    "healer_candidate_family",
    "ambiguity_status",
    "evidence_summary",
    "evidence_source_paths",
    "evidence_locator",
    "confidence",
    "adjudication_status",
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
    healer_family: str,
    ambiguity: str,
    evidence_summary: str,
    chain_mechanism: str,
    packaging_mechanism: bool = False,
) -> dict[str, Any]:
    _require(primary in VALID_PRIMARY_LAYERS, f"invalid primary layer: {primary}")
    _require(
        all(layer in VALID_SECONDARY_LAYERS for layer in secondary),
        f"invalid secondary layer(s): {secondary}",
    )
    _require(primary not in secondary, f"primary layer duplicated in secondary: {primary}")
    mechanism_out = list(mechanisms)
    if packaging_mechanism and "packaging_or_scaffold_residue" not in mechanism_out:
        mechanism_out.append("packaging_or_scaffold_residue")
    chain: list[dict[str, Any]] = []
    if primary == "UNRESOLVED":
        chain.append({
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "UNRESOLVED",
            "mechanism": chain_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
    else:
        chain.append({
            "stage": "raw_module_execution",
            "gate": "G2",
            "layer": "L4",
            "mechanism": chain_mechanism,
            "outcome_validity": "VALID_MODEL_OUTCOME",
        })
        if "L5" in secondary:
            chain.append({
                "stage": "required_function_public_contract_observation",
                "gate": "G4",
                "layer": "L5",
                "mechanism": chain_mechanism,
                "outcome_validity": "VALID_MODEL_OUTCOME",
                "evidence_scope": "public_contract_only",
            })
        if packaging_mechanism:
            chain.append({
                "stage": "module_packaging_observation",
                "gate": "G2",
                "layer": "L4",
                "mechanism": "module_level_executable_assertion",
                "outcome_validity": "VALID_MODEL_OUTCOME",
                "evidence_scope": "source_visible_packaging_only",
            })
    return {
        "provisional_primary_layer": primary,
        "provisional_secondary_layers": _json(list(secondary)),
        "outcome_validity": "VALID_MODEL_OUTCOME",
        "failure_chain": _json(chain),
        "mechanism_tags": _json(mechanism_out),
        "confidence": confidence,
        "healer_eligibility": eligibility,
        "healer_candidate_family": healer_family,
        "ambiguity_status": ambiguity,
        "evidence_summary": evidence_summary,
    }


def _angle_complex(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=[
            "stdlib_complex_type_incompatibility",
            "module_execution_exception",
        ],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="algorithm_rewrite_rejected",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Public contract calls angle_complex(0,1j) with two positional arguments matching "
            "the required entry point and arity; Python type annotations on (x: float, y: float) "
            "are non-enforcing. The frozen TypeError is explained by math.atan2 receiving a "
            "complex second argument at runtime, not by an entry-point arity or signature binding "
            "failure. Healer abstain: any repair would require non-unique API redesign "
            "(complex input vs split components) or algorithm intent reconstruction."
        ),
        chain_mechanism="stdlib_atan2_complex_type_error",
    )


def _average_tuple(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=["L5"],
        mechanisms=["zero_division", "aggregation_axis_mismatch", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="aggregation_semantics_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Implementation averages each inner tuple row-wise via sum(inner)/len(inner); "
            "public example expected values [30.5, 34.25, 27.0, 23.25] are consistent with "
            "column-wise aggregation across the outer tuple-of-tuples, and an empty inner "
            "tuple would raise ZeroDivisionError."
        ),
        chain_mechanism="row_vs_column_aggregation_mismatch",
    )


def _dif_square(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["type_error", "complex_sqrt_path", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="numeric_representation_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Loop uses int(diff ** 0.5) on values that can be negative after subtraction, "
            "which can invoke complex intermediates and fail int() conversion with TypeError "
            "during module execution for the public input."
        ),
        chain_mechanism="int_on_complex_from_negative_sqrt",
    )


def _combinations_colors(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["memory_error", "combinatorial_explosion", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="combinatorial_guard_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Function materializes itertools.product(lst, repeat=n) for all combinations; "
            "without input guards this combinatorial expansion can exhaust memory, matching "
            "the frozen MemoryError during module execution."
        ),
        chain_mechanism="combinatorial_product_explosion",
    )


def _remove_occ(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["index_invalidation", "dual_delete_bug", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="index_invalidation_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "After deleting the first occurrence index, deleting last_idx without adjusting "
            "for the earlier deletion can target the wrong position or go out of range, "
            "producing IndexError for the public example remove_Occ(\"hello\",\"l\")."
        ),
        chain_mechanism="dual_delete_index_invalidation",
    )


def _tuple_intersection(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["type_error", "broken_collection_construction", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="collection_construction_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Return expression nests zip/map/set in a way that does not construct a valid "
            "set of tuples; static structure indicates TypeError before any meaningful "
            "intersection logic executes."
        ),
        chain_mechanism="broken_zip_set_construction",
    )


def _get_median(pid: str) -> dict[str, Any]:
    summaries = {
        "3a39e4c2bc18d21f5ef6b152292331c536ec7a9fe591ef819c7ae8f215a015b6": (
            "Merge loop uses parameter n as length bound while also comparing len(list1)!=len(list2); "
            "merge termination can fail and raise ValueError during module execution."
        ),
        "b53eb5394646562e9018fd62140757c361be7e8f56c700b0a93d00b9368a19f9": (
            "Partial merge stops at 2*n-1 elements then indexes merged[-2]/merged[-1]; "
            "insufficient elements produce IndexError for the public median example."
        ),
        "c28319db61e1533961266cde4482f7ff82ea45618db4181d2744e4fc81c0e5df": (
            "Custom target_index and partial merge logic can leave merged too short, "
            "causing IndexError when computing the median for the public inputs."
        ),
        "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019": (
            "Iterative k-walk advances pointers without guarding bounds before nums1[i+1]/nums2[j+1] "
            "access, yielding IndexError under the public example."
        ),
    }
    exc = {
        "3a39e4c2bc18d21f5ef6b152292331c536ec7a9fe591ef819c7ae8f215a015b6": "ValueError",
        "b53eb5394646562e9018fd62140757c361be7e8f56c700b0a93d00b9368a19f9": "IndexError",
        "c28319db61e1533961266cde4482f7ff82ea45618db4181d2744e4fc81c0e5df": "IndexError",
        "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019": "IndexError",
    }
    mechanisms = ["merge_logic_error", "median_index_error", "module_execution_exception"]
    packaging = pid == "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019"
    if packaging:
        mechanisms.append("module_level_executable_assertion")
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=mechanisms,
        confidence="HIGH",
        eligibility="abstain",
        healer_family="merge_median_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=summaries[pid],
        chain_mechanism=f"merge_median_{exc[pid].lower()}",
        packaging_mechanism=packaging,
    )


def _find_kth(pid: str) -> dict[str, Any]:
    if pid == "1b9aabce1a2e8f3075f28d50c19b12680bfd5ed66090a259eb756b911587cdab":
        summary = (
            "Binary-search partition loop assigns to right on the max_left_1 > min_right_2 branch "
            "but the frozen coarse diagnostic records TypeError at the partition update line; "
            "module-level assert packaging is also present."
        )
        mechanism = "partition_type_error"
    else:
        summary = (
            "Partition indices can address nums1[partition1] or nums2[partition2] out of range "
            "before the kth element is found, producing IndexError; module-level assert packaging "
            "is also present."
        )
        mechanism = "partition_index_error"
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["partition_error", "module_execution_exception", "module_level_executable_assertion"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="partition_search_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=summary,
        chain_mechanism=mechanism,
        packaging_mechanism=True,
    )


def _next_perfect_square(pid: str) -> dict[str, Any]:
    unresolved = {
        "782774eab651523e2edbb469876812fbc4ec136263429b1ff7ba40538884dcfd",
        "7d66673b97fe97bcd362fd08195ad2524133a2bfeda9adbfd0ac17505536c035",
        "b7f7b3ad0cd0e64a4a89bfab78560985393b23746de0bfb589d3e5539e1041f2",
    }
    if pid in unresolved:
        packaging = pid in {
            "7d66673b97fe97bcd362fd08195ad2524133a2bfeda9adbfd0ac17505536c035",
            "b7f7b3ad0cd0e64a4a89bfab78560985393b23746de0bfb589d3e5539e1041f2",
        }
        mechanisms = ["module_execution_exception", "value_error_without_visible_guard"]
        if packaging:
            mechanisms.append("packaging_or_scaffold_residue")
        return _decision(
            primary="UNRESOLVED",
            secondary=[],
            mechanisms=mechanisms,
            confidence="LOW",
            eligibility="abstain",
            healer_family="perfect_square_guard_repair",
            ambiguity="UNRESOLVED",
            evidence_summary=(
                "Frozen coarse diagnostic records ValueError, but the visible H0 source only "
                "computes int(math.sqrt(n))+1 squared with no explicit raise ValueError guard; "
                "static evidence alone cannot identify the failing statement."
            ),
            chain_mechanism="value_error_without_visible_source_guard",
            packaging_mechanism=packaging,
        )
    return _decision(
        primary="L4",
        secondary=[],
        mechanisms=["explicit_value_error_guard", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="perfect_square_guard_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Source contains an explicit raise ValueError guard path (non-negative input check "
            "or equivalent) that can fire during module execution before the public assert example."
        ),
        chain_mechanism="explicit_value_error_guard",
    )


def _parabola_directrix(pid: str) -> dict[str, Any]:
    return _decision(
        primary="L4",
        secondary=["L5"],
        mechanisms=["explicit_value_error_guard", "formula_mismatch", "module_execution_exception"],
        confidence="HIGH",
        eligibility="abstain",
        healer_family="parabola_formula_repair",
        ambiguity="UNAMBIGUOUS",
        evidence_summary=(
            "Function guards a==0 with raise ValueError and computes directrix_y = k - 1/(4a); "
            "for the public inputs parabola_directrix(5,3,2) static evaluation yields a result "
            "inconsistent with the public assert target -198, indicating L5 formula mismatch "
            "alongside the L4 guard/execution failure path."
        ),
        chain_mechanism="directrix_formula_mismatch",
    )


def _find_literals(pid: str) -> dict[str, Any]:
    return _decision(
        primary="UNRESOLVED",
        secondary=[],
        mechanisms=["explicit_value_error_guard", "module_execution_exception"],
        confidence="LOW",
        eligibility="abstain",
        healer_family="literal_search_repair",
        ambiguity="UNRESOLVED",
        evidence_summary=(
            "Source uses re.search(re.escape(pattern), text) and raises ValueError when no match, "
            "but the public example pattern 'fox' appears in the provided string at the asserted "
            "indices; static source review alone cannot reconcile the frozen ValueError."
        ),
        chain_mechanism="value_error_despite_visible_literal_match",
    )


DECISIONS: dict[str, dict[str, Any]] = {
    "0340cfda2189318c12c82e9ada35a30fca39776379bce0ae6142e41ea8802141": _angle_complex(
        "0340cfda2189318c12c82e9ada35a30fca39776379bce0ae6142e41ea8802141"
    ),
    "0575f9422adac73031c6aa632aa3843f8adf64069665039333e799ae196a2906": _average_tuple(
        "0575f9422adac73031c6aa632aa3843f8adf64069665039333e799ae196a2906"
    ),
    "17cde64daa996d2f0012be63d02b00b2cd54410f40fd90a1db803633bbc3b4d8": _dif_square(
        "17cde64daa996d2f0012be63d02b00b2cd54410f40fd90a1db803633bbc3b4d8"
    ),
    "1b9aabce1a2e8f3075f28d50c19b12680bfd5ed66090a259eb756b911587cdab": _find_kth(
        "1b9aabce1a2e8f3075f28d50c19b12680bfd5ed66090a259eb756b911587cdab"
    ),
    "24b5e295ca91e1fce3029be6f593ada79d255c2725fc40a02e5a512f4fdb8452": _angle_complex(
        "24b5e295ca91e1fce3029be6f593ada79d255c2725fc40a02e5a512f4fdb8452"
    ),
    "295dfc28979e0fcaa5c908be8ba908d384b224f3ce89dc6044311ca04f12f88f": _combinations_colors(
        "295dfc28979e0fcaa5c908be8ba908d384b224f3ce89dc6044311ca04f12f88f"
    ),
    "318497f8b86f8aaf0ef2932e45dc33bcae8c9676c2df067bf1f27cd2f067510b": _average_tuple(
        "318497f8b86f8aaf0ef2932e45dc33bcae8c9676c2df067bf1f27cd2f067510b"
    ),
    "3a39e4c2bc18d21f5ef6b152292331c536ec7a9fe591ef819c7ae8f215a015b6": _get_median(
        "3a39e4c2bc18d21f5ef6b152292331c536ec7a9fe591ef819c7ae8f215a015b6"
    ),
    "5019f72d2bc2fb86c03177d80a7816f6902d6a5bc4a087dacc99a57cd63baf06": _combinations_colors(
        "5019f72d2bc2fb86c03177d80a7816f6902d6a5bc4a087dacc99a57cd63baf06"
    ),
    "5c2515e4827b878e031b8a5708c4d7559c29cceb035050637e32423b757c46cc": _angle_complex(
        "5c2515e4827b878e031b8a5708c4d7559c29cceb035050637e32423b757c46cc"
    ),
    "60d1ea73f977e4c7f0a1af9894b615d332953a916aceaed7ecc75569bbd91ac2": _angle_complex(
        "60d1ea73f977e4c7f0a1af9894b615d332953a916aceaed7ecc75569bbd91ac2"
    ),
    "667258041def23e75eba7f3d6081918553cec7b9115360a33a4b1f2a3245ef2b": _remove_occ(
        "667258041def23e75eba7f3d6081918553cec7b9115360a33a4b1f2a3245ef2b"
    ),
    "67bb0a715bef627d5cfee1ef1d264236b521326aae40796ed497b905e52a2938": _average_tuple(
        "67bb0a715bef627d5cfee1ef1d264236b521326aae40796ed497b905e52a2938"
    ),
    "69b535628ae6183c0aed1fc85d3a067903c30ff990129c5275093a345c723382": _angle_complex(
        "69b535628ae6183c0aed1fc85d3a067903c30ff990129c5275093a345c723382"
    ),
    "6a3c32bd229b5b4d5db770fba3ef086213563289b97941b9bd12548c149831ec": _combinations_colors(
        "6a3c32bd229b5b4d5db770fba3ef086213563289b97941b9bd12548c149831ec"
    ),
    "7545d939bbed34004192b1b463e1d5afa7a76b846269f93dd9d178209f9ae1c0": _tuple_intersection(
        "7545d939bbed34004192b1b463e1d5afa7a76b846269f93dd9d178209f9ae1c0"
    ),
    "782774eab651523e2edbb469876812fbc4ec136263429b1ff7ba40538884dcfd": _next_perfect_square(
        "782774eab651523e2edbb469876812fbc4ec136263429b1ff7ba40538884dcfd"
    ),
    "7d66673b97fe97bcd362fd08195ad2524133a2bfeda9adbfd0ac17505536c035": _next_perfect_square(
        "7d66673b97fe97bcd362fd08195ad2524133a2bfeda9adbfd0ac17505536c035"
    ),
    "7e48bbab46a558a65bfcda696b6fdd192dd25600c5134c0ea8ae7040ae931298": _parabola_directrix(
        "7e48bbab46a558a65bfcda696b6fdd192dd25600c5134c0ea8ae7040ae931298"
    ),
    "8efb7dab63074d068958eb903bb89b857440f1025c119a6035c2c9a841f50742": _find_literals(
        "8efb7dab63074d068958eb903bb89b857440f1025c119a6035c2c9a841f50742"
    ),
    "911004db3b2b2b4724d3fdf4eef002f43f6e501788d6d24dc9a463d615182161": _next_perfect_square(
        "911004db3b2b2b4724d3fdf4eef002f43f6e501788d6d24dc9a463d615182161"
    ),
    "951a8909d85003fe8b785bf08c8afa0e476f67af5544a8a0896405b66444e9e7": _next_perfect_square(
        "951a8909d85003fe8b785bf08c8afa0e476f67af5544a8a0896405b66444e9e7"
    ),
    "a06202ce4039e2b576f621e42a728c6dc065f9b126fd037f86a6c12666543a32": _parabola_directrix(
        "a06202ce4039e2b576f621e42a728c6dc065f9b126fd037f86a6c12666543a32"
    ),
    "a89776d747b376e8bde41df0d5026a882931a14a9669e84814607c6153de428f": _average_tuple(
        "a89776d747b376e8bde41df0d5026a882931a14a9669e84814607c6153de428f"
    ),
    "b53eb5394646562e9018fd62140757c361be7e8f56c700b0a93d00b9368a19f9": _get_median(
        "b53eb5394646562e9018fd62140757c361be7e8f56c700b0a93d00b9368a19f9"
    ),
    "b6e2db7b77ea67e9897812741b8ed2e18bd37201bdcee87bfa2eb6548dabaaa2": _find_literals(
        "b6e2db7b77ea67e9897812741b8ed2e18bd37201bdcee87bfa2eb6548dabaaa2"
    ),
    "b7f7b3ad0cd0e64a4a89bfab78560985393b23746de0bfb589d3e5539e1041f2": _next_perfect_square(
        "b7f7b3ad0cd0e64a4a89bfab78560985393b23746de0bfb589d3e5539e1041f2"
    ),
    "bdaf6b291abc934fa2ad02af1beddbeba53acd1b5911b00024085d7072919efa": _combinations_colors(
        "bdaf6b291abc934fa2ad02af1beddbeba53acd1b5911b00024085d7072919efa"
    ),
    "c0c06f6fcb5b4dee869e572fda5e23ee98116f5e4c3d5d6a3d3cc96161a7bab0": _average_tuple(
        "c0c06f6fcb5b4dee869e572fda5e23ee98116f5e4c3d5d6a3d3cc96161a7bab0"
    ),
    "c28319db61e1533961266cde4482f7ff82ea45618db4181d2744e4fc81c0e5df": _get_median(
        "c28319db61e1533961266cde4482f7ff82ea45618db4181d2744e4fc81c0e5df"
    ),
    "c2d651467e7abc045cfc9a4c523081d3f7dd86ed356ac965a3793a3b2998e2ed": _remove_occ(
        "c2d651467e7abc045cfc9a4c523081d3f7dd86ed356ac965a3793a3b2998e2ed"
    ),
    "ccbf8fba0e7b409c9570fc1574519a6d4f122847a490ecf0fc62396fcd4e3a22": _find_kth(
        "ccbf8fba0e7b409c9570fc1574519a6d4f122847a490ecf0fc62396fcd4e3a22"
    ),
    "d37bbdccd21d7370a58c1513ddc24b3566c318fd31f0e3b2c724ebc6608f853f": _parabola_directrix(
        "d37bbdccd21d7370a58c1513ddc24b3566c318fd31f0e3b2c724ebc6608f853f"
    ),
    "d79469f17725693a3dbdb8ab981bddf8ed4375e802134524cfa94961d2f17f0f": _remove_occ(
        "d79469f17725693a3dbdb8ab981bddf8ed4375e802134524cfa94961d2f17f0f"
    ),
    "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019": _get_median(
        "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019"
    ),
    "f47af857ade246797c519ba56642b4e03a657f7e005e46f28e08bc78ee364bac": _combinations_colors(
        "f47af857ade246797c519ba56642b4e03a657f7e005e46f28e08bc78ee364bac"
    ),
    "f75a5f9e85fedf004490ef33fc901124086d40f1abc734a904f25afb49a03992": _dif_square(
        "f75a5f9e85fedf004490ef33fc901124086d40f1abc734a904f25afb49a03992"
    ),
}


def _load_cluster(root: Path = ROOT) -> tuple[list[dict[str, str]], dict[str, dict[str, str]], set[str]]:
    verify_sources(root)
    manifest_path = _path(root, MACHINE_CENSUS_MANIFEST)
    _require(
        _sha(manifest_path.read_bytes()) == MACHINE_CENSUS_MANIFEST_SHA256,
        "machine census manifest SHA drift",
    )
    census_rows = _read_csv(_path(root, MACHINE_CENSUS_CSV))
    roster_rows = _read_csv(_path(root, MACHINE_CENSUS_ROSTER))
    g2_rows = _read_csv(_path(root, G2_PROVISIONAL_CSV))
    roster_by_program = {row["program_id"]: row for row in roster_rows}
    g2_ids = {row["program_id"] for row in g2_rows}
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
    _require(set(DECISIONS) == cluster_ids, "decision identity set drift")
    return cluster, roster_by_program, g2_ids


def build_rows(root: Path = ROOT) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cluster, roster_by_program, _g2_ids = _load_cluster(root)
    diagnostics = {row["program_id"]: row for row in _read_csv(_path(root, preparation.FORMAL_RESULTS))}
    journals = {
        row["program_id"]: row
        for row in _read_jsonl(_path(root, preparation.JOURNAL))
        if row["healer_account"] == "H0"
    }
    tasks = {row["task_id"]: row for row in _read_jsonl(_path(root, preparation.TASKS))}

    roster_out: list[dict[str, Any]] = []
    adjudication_out: list[dict[str, Any]] = []

    for rank, census_row in enumerate(cluster, 1):
        program_id = census_row["program_id"]
        roster_row = roster_by_program[program_id]
        diagnostic = diagnostics[program_id]
        journal = journals[program_id]
        task = tasks[census_row["task_id"]]
        source = journal["evaluation_source"]
        _require(
            _sha(source.encode("utf-8")) == census_row.get("evaluation_source_sha256", roster_row["evaluation_source_sha256"]),
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
        decision = DECISIONS[program_id]
        roster_out.append(
            {
                "cluster_rank": rank,
                "program_id": program_id,
                "cell_identity_sha256": census_row["cell_identity_sha256"],
                "task_identity_sha256": roster_row["task_identity_sha256"],
                "task_id": census_row["task_id"],
                "seed": census_row["seed"],
                "generation_id": roster_row["generation_id"],
                "required_entry_point": census_row["required_entry_point"],
                "operational_cluster": TARGET_CLUSTER,
                "diagnostic_phase": census_row["diagnostic_phase"],
                "diagnostic_exception_class": census_row["diagnostic_exception_class"],
                "evaluation_source_sha256": roster_row["evaluation_source_sha256"],
                "inclusion_reason": f"operational_cluster=={TARGET_CLUSTER}",
                "machine_census_roster_rank": roster_row["roster_rank"],
            }
        )
        adjudication_out.append(
            {
                "program_id": program_id,
                "cell_identity_sha256": census_row["cell_identity_sha256"],
                "operational_cluster": TARGET_CLUSTER,
                **decision,
                "evidence_source_paths": _json(evidence_paths),
                "evidence_locator": evidence_locator,
                "adjudication_status": STATUS,
            }
        )

    primary_counts = Counter(row["provisional_primary_layer"] for row in adjudication_out)
    _require(primary_counts == Counter({"L4": 32, "UNRESOLVED": 5}), "primary layer distribution drift")
    for row in adjudication_out:
        primary = row["provisional_primary_layer"]
        secondary = json.loads(row["provisional_secondary_layers"])
        _require(
            all(layer in VALID_SECONDARY_LAYERS for layer in secondary),
            f"secondary layer schema violation: {row['program_id']}",
        )
        _require(primary not in secondary, f"primary duplicated in secondary: {row['program_id']}")
    _require(
        Counter(row["healer_eligibility"] for row in adjudication_out) == Counter({"abstain": 37}),
        "healer eligibility distribution drift",
    )
    _require(all(row["outcome_validity"] == "VALID_MODEL_OUTCOME" for row in adjudication_out), "outcome validity drift")
    return roster_out, adjudication_out


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

    outcome_rows = [{"outcome_validity": value, "cells": count} for value, count in sorted(Counter(row["outcome_validity"] for row in adjudication_rows).items())]
    eligibility_rows = [{"healer_eligibility": value, "cells": count} for value, count in sorted(Counter(row["healer_eligibility"] for row in adjudication_rows).items())]
    confidence_rows = [{"confidence": value, "cells": count} for value, count in sorted(Counter(row["confidence"] for row in adjudication_rows).items())]

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
        "# Candidate B r003 taxonomy v3：remaining171 module_execution_exception_signal provisional adjudication v1",
        "",
        f"**狀態：`{STATUS}`**",
        "",
        "本 revision 針對 remaining171 machine census 中 `operational_cluster == module_execution_exception_signal` 的 37 格，",
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
            "- 母體為 remaining171 roster；與 G2_module 27 交集為 0",
            "- outcome_validity 一律 VALID_MODEL_OUTCOME（模型失敗路徑）",
            "- healer_eligibility 均為 abstain；未宣稱 Healer 安全或充分",
            "",
        ]
    )
    return "\n".join(lines)


def _adjudication_protocol() -> str:
    return "\n".join(
        [
            "# Adjudication protocol（module_execution_exception_signal provisional v1）",
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
            "- 不修改 machine census 或 G2 provisional 產物",
            "",
            "## 輸出",
            "",
            "- 37 列 ai_provisional_adjudication.csv",
            "- fixed_cluster_roster.csv 與 summary / manifest / provenance",
            "",
        ]
    )


AUDIT_FIELDS = (
    "check_id",
    "affected_program_id",
    "original_primary",
    "audited_primary",
    "original_secondary",
    "audited_secondary",
    "issue_type",
    "evidence",
    "action_required",
    "verdict",
)

# Pre-freeze adversarial audit ledger (before revision applied in this script).
PRE_FREEZE_AUDIT_LEDGER: list[dict[str, str]] = [
    {
        "check_id": "SEC-001",
        "affected_program_id": "1b9aabce1a2e8f3075f28d50c19b12680bfd5ed66090a259eb756b911587cdab",
        "original_primary": "L4",
        "audited_primary": "L4",
        "original_secondary": '["packaging_residue"]',
        "audited_secondary": "[]",
        "issue_type": "secondary_layer_schema_violation",
        "evidence": "packaging_residue is a mechanism tag, not L0-L5 layer",
        "action_required": "move to mechanism_tags as packaging_or_scaffold_residue",
        "verdict": "REVISE",
    },
    {
        "check_id": "SEC-001",
        "affected_program_id": "7d66673b97fe97bcd362fd08195ad2524133a2bfeda9adbfd0ac17505536c035",
        "original_primary": "UNRESOLVED",
        "audited_primary": "UNRESOLVED",
        "original_secondary": '["L4","packaging_residue"]',
        "audited_secondary": "[]",
        "issue_type": "secondary_layer_schema_violation",
        "evidence": "packaging_residue is a mechanism tag, not L0-L5 layer",
        "action_required": "move to mechanism_tags as packaging_or_scaffold_residue",
        "verdict": "REVISE",
    },
    {
        "check_id": "SEC-001",
        "affected_program_id": "b7f7b3ad0cd0e64a4a89bfab78560985393b23746de0bfb589d3e5539e1041f2",
        "original_primary": "UNRESOLVED",
        "audited_primary": "UNRESOLVED",
        "original_secondary": '["L4","packaging_residue"]',
        "audited_secondary": "[]",
        "issue_type": "secondary_layer_schema_violation",
        "evidence": "packaging_residue is a mechanism tag, not L0-L5 layer",
        "action_required": "move to mechanism_tags as packaging_or_scaffold_residue",
        "verdict": "REVISE",
    },
    {
        "check_id": "SEC-001",
        "affected_program_id": "ccbf8fba0e7b409c9570fc1574519a6d4f122847a490ecf0fc62396fcd4e3a22",
        "original_primary": "L4",
        "audited_primary": "L4",
        "original_secondary": '["packaging_residue"]',
        "audited_secondary": "[]",
        "issue_type": "secondary_layer_schema_violation",
        "evidence": "packaging_residue is a mechanism tag, not L0-L5 layer",
        "action_required": "move to mechanism_tags as packaging_or_scaffold_residue",
        "verdict": "REVISE",
    },
    {
        "check_id": "SEC-001",
        "affected_program_id": "d8697d88e8233dbbb610e6740b9ded49ddc74701f7c33f8628731fdd58777019",
        "original_primary": "L4",
        "audited_primary": "L4",
        "original_secondary": '["packaging_residue"]',
        "audited_secondary": "[]",
        "issue_type": "secondary_layer_schema_violation",
        "evidence": "packaging_residue is a mechanism tag, not L0-L5 layer",
        "action_required": "move to mechanism_tags as packaging_or_scaffold_residue",
        "verdict": "REVISE",
    },
    {
        "check_id": "L2-001",
        "affected_program_id": "0340cfda2189318c12c82e9ada35a30fca39776379bce0ae6142e41ea8802141",
        "original_primary": "L2",
        "audited_primary": "L4",
        "original_secondary": '["L4"]',
        "audited_secondary": "[]",
        "issue_type": "mbpp124_l2_overclassification",
        "evidence": "angle_complex(0,1j) arity=2 matches entry point; float annotations non-enforcing; TypeError at math.atan2(complex)",
        "action_required": "reclassify primary L2->L4; remove false signature_mismatch",
        "verdict": "REVISE",
    },
    {
        "check_id": "L2-001",
        "affected_program_id": "24b5e295ca91e1fce3029be6f593ada79d255c2725fc40a02e5a512f4fdb8452",
        "original_primary": "L2",
        "audited_primary": "L4",
        "original_secondary": '["L4"]',
        "audited_secondary": "[]",
        "issue_type": "mbpp124_l2_overclassification",
        "evidence": "same as 0340cfda",
        "action_required": "reclassify primary L2->L4",
        "verdict": "REVISE",
    },
    {
        "check_id": "L2-001",
        "affected_program_id": "5c2515e4827b878e031b8a5708c4d7559c29cceb035050637e32423b757c46cc",
        "original_primary": "L2",
        "audited_primary": "L4",
        "original_secondary": '["L4"]',
        "audited_secondary": "[]",
        "issue_type": "mbpp124_l2_overclassification",
        "evidence": "same as 0340cfda",
        "action_required": "reclassify primary L2->L4",
        "verdict": "REVISE",
    },
    {
        "check_id": "L2-001",
        "affected_program_id": "60d1ea73f977e4c7f0a1af9894b615d332953a916aceaed7ecc75569bbd91ac2",
        "original_primary": "L2",
        "audited_primary": "L4",
        "original_secondary": '["L4"]',
        "audited_secondary": "[]",
        "issue_type": "mbpp124_l2_overclassification",
        "evidence": "same as 0340cfda",
        "action_required": "reclassify primary L2->L4",
        "verdict": "REVISE",
    },
    {
        "check_id": "L2-001",
        "affected_program_id": "69b535628ae6183c0aed1fc85d3a067903c30ff990129c5275093a345c723382",
        "original_primary": "L2",
        "audited_primary": "L4",
        "original_secondary": '["L4"]',
        "audited_secondary": "[]",
        "issue_type": "mbpp124_l2_overclassification",
        "evidence": "same as 0340cfda",
        "action_required": "reclassify primary L2->L4",
        "verdict": "REVISE",
    },
    {
        "check_id": "L45-001",
        "affected_program_id": "0575f9422adac73031c6aa632aa3843f8adf64069665039333e799ae196a2906",
        "original_primary": "L4",
        "audited_primary": "L4",
        "original_secondary": '["L5"]',
        "audited_secondary": '["L5"]',
        "issue_type": "l4_l5_boundary_review",
        "evidence": "ZeroDivisionError primary; column-wise public example arithmetic supports L5 secondary",
        "action_required": "none",
        "verdict": "ACCEPT",
    },
    {
        "check_id": "L45-001",
        "affected_program_id": "7e48bbab46a558a65bfcda696b6fdd192dd25600c5134c0ea8ae7040ae931298",
        "original_primary": "L4",
        "audited_primary": "L4",
        "original_secondary": '["L5"]',
        "audited_secondary": '["L5"]',
        "issue_type": "l4_l5_boundary_review",
        "evidence": "ValueError guard visible; public assert -198 vs static formula mismatch supports L5 secondary",
        "action_required": "none",
        "verdict": "ACCEPT",
    },
    {
        "check_id": "HEAL-001",
        "affected_program_id": "ALL_37",
        "original_primary": "",
        "audited_primary": "",
        "original_secondary": "",
        "audited_secondary": "",
        "issue_type": "healer_eligibility_consistency",
        "evidence": "each cell evidence_summary cites non-unique repair, algorithm rebuild, or insufficient evidence",
        "action_required": "none",
        "verdict": "ACCEPT",
    },
    {
        "check_id": "OUT-001",
        "affected_program_id": "ALL_37",
        "original_primary": "",
        "audited_primary": "",
        "original_secondary": "",
        "audited_secondary": "",
        "issue_type": "outcome_validity_consistency",
        "evidence": "G1 PASS, entry point bound, infrastructure valid; UNRESOLVED layer does not invalidate outcome",
        "action_required": "none",
        "verdict": "ACCEPT",
    },
]


def _audit_report_md(pre_verdict: str, post_verdict: str) -> str:
    revise = sum(1 for row in PRE_FREEZE_AUDIT_LEDGER if row["verdict"] == "REVISE")
    accept = sum(1 for row in PRE_FREEZE_AUDIT_LEDGER if row["verdict"] == "ACCEPT")
    return "\n".join(
        [
            "# Pre-freeze adversarial methodology audit",
            "",
            f"**狀態：`{STATUS}`**",
            "",
            f"**Pre-freeze verdict：`{pre_verdict}`**",
            f"**Post-revision verdict：`{post_verdict}`**",
            "",
            f"- Audit rows：{len(PRE_FREEZE_AUDIT_LEDGER)}",
            f"- REVISE findings：{revise}",
            f"- ACCEPT findings：{accept}",
            "",
            "修訂已套用：packaging_residue 移出 secondary layers；Mbpp/124 五格 L2→L4。",
            "UNRESOLVED 五格保留；outcome_validity 仍為 VALID_MODEL_OUTCOME。",
            "",
            "本 audit 在 commit/freeze 前執行；machine cluster 不得等同 taxonomy layer。",
            "",
        ]
    )


def build_outputs(root: Path = ROOT) -> dict[Path, bytes]:
    roster_rows, adjudication_rows = build_rows(root)
    summaries = _summary_tables(adjudication_rows)
    primary_rows = summaries["primary_layer_summary.csv"]

    outputs: dict[Path, bytes] = {
        Path("fixed_cluster_roster.csv"): _csv_bytes(ROSTER_FIELDS, roster_rows),
        Path("ai_provisional_adjudication.csv"): _csv_bytes(ADJUDICATION_FIELDS, adjudication_rows),
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
