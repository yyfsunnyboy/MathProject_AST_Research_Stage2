"""Build a static, zero-execution inventory of possible deterministic healers.

The script reads frozen development evidence and parses candidate text with
``ast.parse``.  It never imports, compiles, evaluates, or executes candidate
source, and it does not invoke EvalPlus or a model.
"""

from __future__ import annotations

import ast
import builtins
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "deterministic_healer_candidate_inventory_4b9b_v1"
)
FOUR_B_DIR = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_4b_failure_supply_pilot_analysis_v1"
)
FOUR_B_MANIFEST = FOUR_B_DIR / "frozen_input_manifest.json"
FOUR_B_TAXONOMY = FOUR_B_DIR / "taxonomy_v31_ledger.csv"
FOUR_B_CELLS = FOUR_B_DIR / "cell_itt_ledger.csv"
FOUR_B_INVENTORY = FOUR_B_DIR / "generation_evidence_inventory.csv"
NINE_B_CENSUS_DIR = Path(
    "artifacts/public_benchmark_governance/candidate_b_r003_failure_census_v1"
)
NINE_B_CENSUS_MANIFEST = NINE_B_CENSUS_DIR / "manifest.json"
NINE_B_CENSUS = NINE_B_CENSUS_DIR / "candidate_b_r003_failure_census.csv"
NINE_B_CROSSWALK = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_v3_crosswalk_diagnostics_protocol_v1/"
    "candidate_b_r003_v3_derived_crosswalk.csv"
)
NINE_B_DIAGNOSTIC_INPUT = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_diagnostics_r002_v3/formal198_input_ledger.csv"
)
NINE_B_DIAGNOSTICS = Path(
    "artifacts/public_benchmark_governance/"
    "candidate_b_r003_diagnostics_r002_v3/"
    "manual_formal_diagnostics_run_001/coarse_diagnostics.csv"
)
NINE_B_RAW = Path(
    "artifacts/public_benchmark_development/mbpp_candidate_b_development60/"
    "runs/mbpp_q35_9b_candidate_b_development60_replay_r003/"
    "raw_generations.jsonl"
)
H1_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "healer_h0_h1_functional_evaluation_v1/manifest.json"
)
H2_EVALUATION_MANIFEST = Path(
    "artifacts/public_benchmark_governance/"
    "h2_module_assert_quarantine_functional_evaluation_v1/"
    "evaluation_manifest.json"
)
H2_ROSTER = H2_EVALUATION_MANIFEST.parent / "cell_roster.jsonl"

H1_SHA256 = "cf4d086ca6e3af968f31b0d087ed2479e5ad38be4b7abe5d2ce5516b68000d44"
H2_SHA256 = "dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18"

LEDGER_FIELDS = [
    "cell_id",
    "model",
    "task_id",
    "seed",
    "condition",
    "program_id",
    "mechanism",
    "evidence",
    "candidate_rule",
    "eligibility",
    "abstain_reason",
    "semantic_risk",
    "recommended_priority",
    "source_sha256",
    "source_authority",
    "taxonomy_layer",
    "taxonomy_tags",
    "existing_h1_mechanism_present",
    "existing_h2_mechanism_present",
]

# Only symbols with a single conventional standard-library import are listed.
# An eligible cell must have no other unresolved names and no star import.
UNIQUE_STDLIB_IMPORT = {
    "math": "import math",
    "re": "import re",
    "itertools": "import itertools",
    "collections": "import collections",
    "functools": "import functools",
    "heapq": "import heapq",
    "bisect": "import bisect",
    "statistics": "import statistics",
    "string": "import string",
    "copy": "import copy",
    "sqrt": "from math import sqrt",
    "isqrt": "from math import isqrt",
    "ceil": "from math import ceil",
    "floor": "from math import floor",
    "factorial": "from math import factorial",
    "gcd": "from math import gcd",
    "lcm": "from math import lcm",
    "comb": "from math import comb",
    "perm": "from math import perm",
    "pi": "from math import pi",
    "inf": "from math import inf",
    "Counter": "from collections import Counter",
    "defaultdict": "from collections import defaultdict",
    "deque": "from collections import deque",
    "OrderedDict": "from collections import OrderedDict",
    "combinations": "from itertools import combinations",
    "permutations": "from itertools import permutations",
    "product": "from itertools import product",
    "chain": "from itertools import chain",
    "combinations_with_replacement": (
        "from itertools import combinations_with_replacement"
    ),
    "reduce": "from functools import reduce",
    "lru_cache": "from functools import lru_cache",
    "cache": "from functools import cache",
    "heappush": "from heapq import heappush",
    "heappop": "from heapq import heappop",
    "heapify": "from heapq import heapify",
    "nlargest": "from heapq import nlargest",
    "nsmallest": "from heapq import nsmallest",
    "bisect_left": "from bisect import bisect_left",
    "bisect_right": "from bisect import bisect_right",
    "insort": "from bisect import insort",
    "mean": "from statistics import mean",
    "median": "from statistics import median",
    "mode": "from statistics import mode",
    "ascii_lowercase": "from string import ascii_lowercase",
    "ascii_uppercase": "from string import ascii_uppercase",
    "digits": "from string import digits",
    "deepcopy": "from copy import deepcopy",
    "List": "from typing import List",
    "Tuple": "from typing import Tuple",
    "Optional": "from typing import Optional",
    "Dict": "from typing import Dict",
    "Set": "from typing import Set",
    "Any": "from typing import Any",
}
BUILTIN_NAMES = set(dir(builtins)) | {"__name__"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def prompt_contract(prompt: str) -> tuple[str | None, set[int]]:
    match = re.search(r'"""(.*?)"""', prompt, re.DOTALL)
    public_block = match.group(1) if match else prompt
    calls: list[tuple[str, int]] = []
    for line in public_block.splitlines():
        if not line.lstrip().startswith("assert "):
            continue
        try:
            statement = ast.parse(line.strip()).body[0]
        except (SyntaxError, IndexError):
            continue
        if not isinstance(statement, ast.Assert):
            continue
        for node in ast.walk(statement.test):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.append((node.func.id, len(node.args) + len(node.keywords)))
                break
    if not calls:
        return None, set()
    name_counts = Counter(name for name, _ in calls)
    expected = name_counts.most_common(1)[0][0]
    return expected, {arity for name, arity in calls if name == expected}


def bound_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(
            node.ctx, (ast.Store, ast.Del)
        ):
            names.add(node.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


def signature_accepts_arities(
    function: ast.FunctionDef | ast.AsyncFunctionDef, arities: set[int]
) -> bool:
    positional = len(function.args.posonlyargs) + len(function.args.args)
    required = positional - len(function.args.defaults)
    has_varargs = function.args.vararg is not None
    return bool(arities) and all(
        arity >= required and (has_varargs or arity <= positional)
        for arity in arities
    )


def literal_only(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(literal_only(element) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is None or literal_only(key) for key in node.keys
        ) and all(literal_only(value) for value in node.values)
    if isinstance(node, ast.UnaryOp):
        return literal_only(node.operand)
    return False


def safe_demo_print(
    call: ast.Call, expected_entry_point: str, function_names: set[str]
) -> bool:
    if not isinstance(call.func, ast.Name) or call.func.id != "print":
        return False
    if not call.args:
        return True
    for argument in call.args:
        if literal_only(argument):
            continue
        if (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id == expected_entry_point
            and argument.func.id in function_names
            and all(literal_only(item) for item in argument.args)
            and all(literal_only(keyword.value) for keyword in argument.keywords)
        ):
            continue
        return False
    return all(literal_only(keyword.value) for keyword in call.keywords)


def is_adjacent_to_public_selftest(body: list[ast.stmt], index: int) -> bool:
    neighbors = []
    if index > 0:
        neighbors.append(body[index - 1])
    if index + 1 < len(body):
        neighbors.append(body[index + 1])
    return any(isinstance(statement, ast.Assert) for statement in neighbors)


def response_done_reason(journal: dict[str, Any]) -> str:
    raw_body = journal.get("response_metadata", {}).get("raw_body", "")
    try:
        return str(json.loads(raw_body).get("done_reason", ""))
    except (json.JSONDecodeError, TypeError):
        return ""


def classification(
    *,
    source: str,
    prompt: str,
    extraction_status: str,
    done_reason: str,
    taxonomy_layer: str,
    taxonomy_tags: str,
) -> dict[str, str]:
    expected, arities = prompt_contract(prompt)
    source_has_markdown = "```" in source
    source_has_prose = bool(
        re.search(
            r"(^|\n)\s*(Here(?:'s| is)|Explanation:|The function\b)",
            source,
            re.IGNORECASE,
        )
    )
    if extraction_status == "ambiguous" or source_has_markdown or source_has_prose:
        return decision(
            mechanism="packaging_markdown_extractor",
            evidence=(
                f"formal extraction_status={extraction_status}; "
                f"markdown={source_has_markdown}; prose={source_has_prose}; "
                f"taxonomy={taxonomy_layer}:{taxonomy_tags}"
            ),
            candidate_rule="Scaffold_or_Pipeline_correction",
            eligibility="scaffold_or_pipeline_correction",
            abstain_reason="not a Healer responsibility",
            semantic_risk="candidate selection or text stripping can choose the wrong program",
            priority="none",
            h1=False,
            h2=False,
        )

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        looks_truncated = (
            done_reason == "length"
            or "was never closed" in error.msg
            or source.rstrip().endswith((",", "\\", "(", "[", "{", ":"))
            or (
                "expected an indented block" in error.msg
                and error.lineno is not None
                and error.lineno >= max(1, source.count("\n") - 1)
            )
        )
        if looks_truncated:
            return decision(
                mechanism="truncation",
                evidence=(
                    f"done_reason={done_reason or 'unknown'}; "
                    f"SyntaxError={error.msg}; line={error.lineno}"
                ),
                candidate_rule="none",
                eligibility="not_eligible",
                abstain_reason="incomplete generation has no unique local repair",
                semantic_risk="missing suffix may contain arbitrary algorithmic logic",
                priority="none",
                h1=False,
                h2=False,
            )
        return decision(
            mechanism="other_syntax_or_ast_failure",
            evidence=f"SyntaxError={error.msg}; line={error.lineno}",
            candidate_rule="none",
            eligibility="abstain",
            abstain_reason="no uniquely inferable semantics-preserving edit",
            semantic_risk="multiple syntactic repairs can produce different programs",
            priority="4",
            h1=False,
            h2=False,
        )

    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    function_names = {node.name for node in functions}
    top_level_assert = any(isinstance(node, ast.Assert) for node in tree.body)

    if expected and expected not in function_names:
        compatible = [
            function.name
            for function in functions
            if signature_accepts_arities(function, arities)
        ]
        if len(functions) == 1 and len(compatible) == 1:
            return decision(
                mechanism="unique_entry_point_mismatch",
                evidence=(
                    f"required={expected}; defined={compatible[0]}; "
                    f"public_assert_arities={sorted(arities)}; unique_function=true"
                ),
                candidate_rule="entrypoint_alias_unique_arity_compatible_v0",
                eligibility="excluded_existing_H1",
                abstain_reason="mechanism is already H1 factorial",
                semantic_risk="guarded by H1 unique-function and signature compatibility",
                priority="1",
                h1=True,
                h2=top_level_assert,
            )
        return decision(
            mechanism="entry_point_mismatch_ambiguous",
            evidence=(
                f"required={expected}; top_level_functions={sorted(function_names)}; "
                f"compatible={sorted(compatible)}"
            ),
            candidate_rule="none",
            eligibility="abstain",
            abstain_reason="multiple or zero uniquely safe mappings",
            semantic_risk="renaming or aliasing can expose the wrong implementation",
            priority="1",
            h1=False,
            h2=top_level_assert,
        )

    bound = bound_names(tree)
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    unresolved = loaded - bound - BUILTIN_NAMES
    known_missing = sorted(unresolved & set(UNIQUE_STDLIB_IMPORT))
    unknown_missing = sorted(unresolved - set(known_missing))
    star_import = any(
        isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
        for node in ast.walk(tree)
    )
    if known_missing:
        imports = sorted({UNIQUE_STDLIB_IMPORT[name] for name in known_missing})
        if not unknown_missing and not star_import:
            return decision(
                mechanism="unique_missing_stdlib_import",
                evidence=(
                    f"unbound_standard_symbols={known_missing}; "
                    f"unique_imports={imports}; no_other_unbound_names=true"
                ),
                candidate_rule="insert_unique_standard_library_import_v0",
                eligibility="eligible_candidate",
                abstain_reason="",
                semantic_risk="low only under exact unbound-name and no-star-import guards",
                priority="2",
                h1=False,
                h2=top_level_assert,
            )
        return decision(
            mechanism="missing_import_ambiguous",
            evidence=(
                f"known={known_missing}; unknown={unknown_missing}; "
                f"star_import={star_import}"
            ),
            candidate_rule="none",
            eligibility="abstain",
            abstain_reason="not every unresolved name has one safe stdlib import",
            semantic_risk="an inserted import may shadow an intended task-local name",
            priority="2",
            h1=False,
            h2=top_level_assert,
        )

    eligible_prints: list[str] = []
    unsafe_top_level_calls: list[str] = []
    for index, statement in enumerate(tree.body):
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
        ):
            continue
        call = statement.value
        if (
            expected
            and expected in function_names
            and safe_demo_print(call, expected, function_names)
            and is_adjacent_to_public_selftest(tree.body, index)
        ):
            eligible_prints.append(ast.unparse(statement))
        else:
            unsafe_top_level_calls.append(ast.unparse(statement)[:160])
    if eligible_prints and not unsafe_top_level_calls:
        return decision(
            mechanism="top_level_demo_print_side_effect",
            evidence=(
                f"required_entry_point={expected}; "
                f"adjacent_literal_only_prints={eligible_prints}; "
                f"other_top_level_calls=0; module_assert_excluded_as_H2={top_level_assert}"
            ),
            candidate_rule="top_level_literal_only_demo_print_quarantine_v0",
            eligibility="eligible_candidate",
            abstain_reason="",
            semantic_risk=(
                "low under adjacency, required-entry-point-present, literal-only, "
                "unused-result, and no-other-top-level-call guards"
            ),
            priority="3",
            h1=False,
            h2=top_level_assert,
        )
    if eligible_prints:
        return decision(
            mechanism="top_level_demo_call_mixed_or_ambiguous",
            evidence=(
                f"safe_prints={eligible_prints}; "
                f"other_calls={unsafe_top_level_calls}"
            ),
            candidate_rule="none",
            eligibility="abstain",
            abstain_reason="top-level side effects are not uniquely separable",
            semantic_risk="quarantine could remove required initialization",
            priority="3",
            h1=False,
            h2=top_level_assert,
        )
    if top_level_assert:
        return decision(
            mechanism="module_assert",
            evidence="one or more top-level Assert nodes; residual mechanism absent",
            candidate_rule="module_assert_entrypoint_selftest_quarantine_v0",
            eligibility="excluded_existing_H2",
            abstain_reason="mechanism is already the exact fixed H2 development candidate",
            semantic_risk="governed by H2; no new rule inferred",
            priority="none",
            h1=False,
            h2=True,
        )
    return decision(
        mechanism="semantic_algorithm_boundary_or_no_unique_local_mechanism",
        evidence=(
            f"AST parses; required_entry_point_present={bool(expected and expected in function_names)}; "
            f"no_unique_missing_import=true; no_safe_demo_print=true; "
            f"taxonomy={taxonomy_layer}:{taxonomy_tags}"
        ),
        candidate_rule="none",
        eligibility="not_eligible",
        abstain_reason="no unique local semantics-preserving repair is evidenced",
        semantic_risk="likely algorithmic, boundary, data-flow, or otherwise unlocalized",
        priority="none",
        h1=False,
        h2=False,
    )


def decision(
    *,
    mechanism: str,
    evidence: str,
    candidate_rule: str,
    eligibility: str,
    abstain_reason: str,
    semantic_risk: str,
    priority: str,
    h1: bool,
    h2: bool,
) -> dict[str, str]:
    return {
        "mechanism": mechanism,
        "evidence": evidence,
        "candidate_rule": candidate_rule,
        "eligibility": eligibility,
        "abstain_reason": abstain_reason,
        "semantic_risk": semantic_risk,
        "recommended_priority": priority,
        "existing_h1_mechanism_present": str(h1).lower(),
        "existing_h2_mechanism_present": str(h2).lower(),
    }


def source_hashes(repo_root: Path) -> dict[str, str]:
    paths = [
        FOUR_B_MANIFEST,
        FOUR_B_TAXONOMY,
        FOUR_B_CELLS,
        FOUR_B_INVENTORY,
        NINE_B_CENSUS_MANIFEST,
        NINE_B_CENSUS,
        NINE_B_CROSSWALK,
        NINE_B_DIAGNOSTIC_INPUT,
        NINE_B_DIAGNOSTICS,
        NINE_B_RAW,
        H1_MANIFEST,
        H2_EVALUATION_MANIFEST,
        H2_ROSTER,
    ]
    return {
        path.as_posix(): sha256_bytes((repo_root / path).read_bytes())
        for path in paths
    }


def build_ledger(repo_root: Path) -> list[dict[str, Any]]:
    four_taxonomy = {
        row["cell_identity"]: row for row in load_csv(repo_root / FOUR_B_TAXONOMY)
    }
    four_cells = {
        row["cell_identity"]: row for row in load_csv(repo_root / FOUR_B_CELLS)
    }
    four_inventory = {
        row["cell_identity"]: row for row in load_csv(repo_root / FOUR_B_INVENTORY)
    }
    four_error_ids = {
        cell_id
        for cell_id, row in four_taxonomy.items()
        if row["classification_status"] != "NOT_APPLICABLE_PASS"
    }
    require(len(four_error_ids) == 148, "4B formal error cohort drift")

    rows: list[dict[str, Any]] = []
    for cell_id in sorted(four_error_ids, key=lambda item: int(four_cells[item]["cell_index"])):
        taxonomy = four_taxonomy[cell_id]
        cell = four_cells[cell_id]
        inventory = four_inventory[cell_id]
        journal_path = repo_root / inventory["journal_path"]
        journal_bytes = journal_path.read_bytes()
        require(
            sha256_bytes(journal_bytes) == inventory["journal_sha256"],
            f"4B journal SHA drift: {cell_id}",
        )
        journal = json.loads(journal_bytes)
        source = journal["raw_response"]
        source_sha = sha256_bytes(source.encode("utf-8"))
        require(source_sha == inventory["raw_response_sha256"], "4B source SHA drift")
        prompt = journal["request_metadata"]["messages"][0]["content"]
        result = classification(
            source=source,
            prompt=prompt,
            extraction_status=cell["extraction_status"],
            done_reason=response_done_reason(journal),
            taxonomy_layer=taxonomy["primary_failure_layer"],
            taxonomy_tags=taxonomy["mechanism_tags_json"],
        )
        rows.append(
            {
                "cell_id": cell_id,
                "model": inventory["model_tag"],
                "task_id": cell["task_id"],
                "seed": cell["seed"],
                "condition": cell["condition_id"],
                "program_id": cell["program_id"],
                **result,
                "source_sha256": source_sha,
                "source_authority": inventory["journal_path"],
                "taxonomy_layer": taxonomy["primary_failure_layer"],
                "taxonomy_tags": taxonomy["mechanism_tags_json"],
            }
        )

    nine_census = load_csv(repo_root / NINE_B_CENSUS)
    nine_errors = [
        row for row in nine_census if row["primary_failure_layer"] != "PASSED"
    ]
    require(len(nine_errors) == 224, "9B formal error cohort drift")
    nine_raw: dict[str, dict[str, Any]] = {}
    with (repo_root / NINE_B_RAW).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            nine_raw[record["program_id"]] = record
    require(len(nine_raw) == 300, "9B raw generation population drift")
    for census in sorted(nine_errors, key=lambda item: item["program_id"]):
        raw = nine_raw[census["program_id"]]
        source = raw["raw_response"]
        source_sha = sha256_bytes(source.encode("utf-8"))
        require(source_sha == raw["raw_response_sha256"], "9B source SHA drift")
        result = classification(
            source=source,
            prompt=raw["request"]["messages"][0]["content"],
            extraction_status="extracted",
            done_reason=str(raw["generation_metadata"].get("done_reason", "")),
            taxonomy_layer=census["primary_failure_layer"],
            taxonomy_tags=census["mechanism_tags"],
        )
        rows.append(
            {
                "cell_id": census["program_id"],
                "model": census["model"],
                "task_id": census["task_id"],
                "seed": census["seed"],
                "condition": census["condition"],
                "program_id": census["program_id"],
                **result,
                "source_sha256": source_sha,
                "source_authority": NINE_B_RAW.as_posix(),
                "taxonomy_layer": census["primary_failure_layer"],
                "taxonomy_tags": census["mechanism_tags"],
            }
        )

    require(len(rows) == 372, "combined error cohort drift")
    require(len({(row["model"], row["cell_id"]) for row in rows}) == 372, "duplicate cell")
    return rows


def build_outputs(repo_root: Path) -> dict[str, bytes]:
    h1 = load_json(repo_root / H1_MANIFEST)
    h2 = load_json(repo_root / H2_EVALUATION_MANIFEST)
    require(h1["healer_sha256"] == H1_SHA256, "H1 SHA drift")
    require(h2["rule_sha256"] == H2_SHA256, "H2 SHA drift")
    ledger = build_ledger(repo_root)
    mechanisms = Counter(row["mechanism"] for row in ledger)
    eligibility = Counter(row["eligibility"] for row in ledger)
    eligible = [row for row in ledger if row["eligibility"] == "eligible_candidate"]
    eligible_by_rule = Counter(row["candidate_rule"] for row in eligible)
    eligible_tasks_by_rule = {
        rule: len({row["task_id"] for row in eligible if row["candidate_rule"] == rule})
        for rule in eligible_by_rule
    }
    recommended_rule = "top_level_literal_only_demo_print_quarantine_v0"
    recommended_rows = [
        row for row in eligible if row["candidate_rule"] == recommended_rule
    ]
    require(len(recommended_rows) == 2, "recommended rule cell count drift")
    require(
        {row["task_id"] for row in recommended_rows} == {"Mbpp/138", "Mbpp/787"},
        "recommended rule task evidence drift",
    )
    require(
        not any(
            row["candidate_rule"] == "insert_unique_standard_library_import_v0"
            for row in eligible
        ),
        "unexpected missing-import candidate",
    )

    provenance = {
        "inventory_id": "deterministic_healer_candidate_inventory_4b9b_v1",
        "source_sha256": source_hashes(repo_root),
        "fixed_existing_rules": {
            "H1": H1_SHA256,
            "H2": H2_SHA256,
        },
        "input_policy": {
            "allowed": [
                "formal manifests",
                "formal taxonomy",
                "formal diagnostics",
                "raw candidate and persisted public request metadata",
            ],
            "forbidden": [
                "hidden tests",
                "canonical solution",
                "PASS/FAIL-based rule selection",
                "candidate execution",
                "model calls",
                "EvalPlus execution",
            ],
        },
    }
    summary = {
        "inventory_id": "deterministic_healer_candidate_inventory_4b9b_v1",
        "status": "complete_static_read_only_inventory",
        "cohort": {
            "4B_development_errors": 148,
            "9B_development_errors": 224,
            "total": 372,
            "selection_note": (
                "formal error membership defines the requested cohort; outcome status "
                "is not used as evidence for mechanism detection or recommendation"
            ),
        },
        "mechanism_counts": dict(sorted(mechanisms.items())),
        "eligibility_counts": dict(sorted(eligibility.items())),
        "eligible_rule_counts": dict(sorted(eligible_by_rule.items())),
        "eligible_distinct_tasks_by_rule": dict(sorted(eligible_tasks_by_rule.items())),
        "priority_findings": {
            "1_unique_entry_point_mismatch": (
                "no new candidate; any unique safe case belongs to existing H1, "
                "ambiguous mappings abstain"
            ),
            "2_unique_missing_stdlib_import": "0 eligible cells",
            "3_top_level_demo_call_print": (
                "2 eligible cells across 2 tasks after excluding H2 Assert nodes"
            ),
            "4_other_syntax_ast": (
                "no uniquely inferable semantics-preserving repeated edit"
            ),
        },
        "recommendation": {
            "verdict": "ONE_DEVELOPMENT_CANDIDATE_IDENTIFIED",
            "candidate_rule": recommended_rule,
            "candidate_cells": [row["cell_id"] for row in recommended_rows],
            "tasks": sorted({row["task_id"] for row in recommended_rows}),
            "guards": [
                "module parses without candidate execution",
                "required entry point is present",
                "top-level statement is Expr(print(...))",
                "print is immediately adjacent to a top-level public self-test Assert",
                "each print argument is literal-only or a required-entry-point call with literal-only arguments",
                "print return is unused and there are no other unclassified top-level calls",
                "H2 Assert handling remains separate and unchanged",
            ],
            "status": "recommend_for_separate_preregistration_and_static_audit_only",
            "not_claimed": ["implemented", "frozen", "validated", "confirmatory"],
        },
        "zero_execution": {
            "model_calls": 0,
            "candidate_imports": 0,
            "candidate_executions": 0,
            "EvalPlus_executions": 0,
            "hidden_tests_viewed": 0,
            "canonical_solutions_viewed": 0,
            "H1_modifications": 0,
            "H2_modifications": 0,
            "rule_implementations": 0,
        },
    }
    report = report_zh(summary, recommended_rows)
    outputs = {
        "candidate_ledger.csv": csv_bytes(ledger, LEDGER_FIELDS),
        "summary.json": canonical_json_bytes(summary),
        "provenance.json": canonical_json_bytes(provenance),
        "report_zh.md": report.encode("utf-8"),
    }
    receipt = {
        "receipt_id": "deterministic_healer_candidate_inventory_4b9b_v1",
        "output_sha256_excluding_receipt": {
            name: sha256_bytes(data) for name, data in sorted(outputs.items())
        },
        "row_count": len(ledger),
        "model_calls": 0,
        "candidate_imports": 0,
        "candidate_executions": 0,
        "evalplus_executions": 0,
        "analysis_operations": ["UTF-8 read", "SHA-256", "CSV/JSON parse", "ast.parse"],
    }
    outputs["zero_execution_receipt.json"] = canonical_json_bytes(receipt)
    return outputs


def report_zh(summary: dict[str, Any], recommended_rows: list[dict[str, Any]]) -> str:
    row_lines = "\n".join(
        f"- `{row['task_id']}` seed `{row['seed']}`，cell `{row['cell_id']}`，"
        f"source SHA-256 `{row['source_sha256']}`"
        for row in recommended_rows
    )
    return f"""# 4B／9B 下一條 deterministic Healer 只讀盤點

## 結論

372 個既有 development 錯誤格（4B 148、9B 224）完成逐格靜態盤點。沒有新的 unique entry-point mismatch；唯一安全映射屬於既有 H1，多候選一律 abstain。沒有 uniquely inferable missing standard-library import。Packaging／Markdown／extractor 問題歸 Scaffold 或 Pipeline；truncation、演算法、邊界與無法唯一定位的語意錯誤均不 eligible。

最多推薦一條下一階段 development candidate：`top_level_literal_only_demo_print_quarantine_v0`。它只應進入另一次預登錄與 static audit，本輪未實作、未凍結、未驗證。

## 重複證據

{row_lines}

兩格都有 required entry point、可解析 AST、頂層 public self-test `Assert` 後緊接 `print`；`print` 只含 literal，或以 literal 參數呼叫 required entry point，回傳值未被使用，且沒有其他未分類頂層呼叫。`Assert` 本身仍屬 H2，候選只能處理剩餘 print side effect，不得合併或修改 H2。

## 安全界線

若 required entry point 缺失、存在多個相容函式、print 非相鄰 self-test、參數含非 literal data-flow、結果被使用、存在其他頂層呼叫或需依測試結果判斷，全部 abstain。特別是 `Mbpp/765` 有兩個相容函式，已排除。

本盤點沒有查看 hidden tests 或 canonical solution；錯誤狀態只用來固定使用者要求的既有 error cohort，不作規則選擇證據。模型、candidate import／execution、EvalPlus、H1/H2 修改及規則實作皆為 0。
"""


def write_or_check(repo_root: Path, check: bool) -> None:
    expected = build_outputs(repo_root)
    output_dir = repo_root / OUTPUT_DIR
    if check:
        require(output_dir.is_dir(), "output directory missing")
        require(
            {path.name for path in output_dir.iterdir() if path.is_file()}
            == set(expected),
            "output file set drift",
        )
        for name, data in expected.items():
            require((output_dir / name).read_bytes() == data, f"output drift: {name}")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        (output_dir / name).write_bytes(data)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    write_or_check(args.repo_root.resolve(), args.check)
    print("deterministic_healer_candidate_inventory_4b9b_v1: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
