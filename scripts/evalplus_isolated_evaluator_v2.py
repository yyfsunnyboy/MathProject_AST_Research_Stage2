"""EvalPlus 0.3.1 evaluator with fresh process isolation per candidate suite.

Unlike the v1 persistent worker, this module never calls ``unsafe_execute``
directly.  It uses EvalPlus's public ``check_correctness`` interface, which in
turn calls ``untrusted_check`` and creates a fresh multiprocessing child for
each base/plus candidate suite.  Candidate mutations therefore cannot change
the evaluator's shared problem inputs.
"""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass
from typing import Any

from evalplus.data import (
    get_human_eval_plus,
    get_human_eval_plus_hash,
    get_mbpp_plus,
    get_mbpp_plus_hash,
)
from evalplus.eval import PASS
from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
from evalplus.evaluate import check_correctness, get_groundtruth

EXPECTED_EVALPLUS_VERSION = "0.3.1"
SOURCE_PREFIX = (
    "from typing import *\n"
    "import math, sys, os, collections, itertools, functools, heapq, bisect\n"
)


@dataclass(frozen=True)
class EvaluationResultV2:
    base_pass: bool
    plus_pass: bool
    final_pass: bool
    base_status: str
    plus_status: str

    def as_tuple(self) -> tuple[bool, bool, bool]:
        return self.base_pass, self.plus_pass, self.final_pass


def require_evalplus_031() -> None:
    actual = importlib.metadata.version("evalplus")
    if actual != EXPECTED_EVALPLUS_VERSION:
        raise RuntimeError(
            f"EvalPlus version mismatch: expected {EXPECTED_EVALPLUS_VERSION}, got {actual}"
        )


def evaluate_problem_isolated_v2(
    *,
    dataset: str,
    problem: dict[str, Any],
    expected_output: dict[str, Any],
    code: str,
    add_standard_prefix: bool = True,
) -> EvaluationResultV2:
    """Evaluate one candidate through EvalPlus's process-isolated public API."""
    require_evalplus_031()
    if not code or not code.strip():
        return EvaluationResultV2(False, False, False, "empty", "empty")

    solution = SOURCE_PREFIX + code if add_standard_prefix else code
    result = check_correctness(
        dataset,
        0,
        problem,
        solution,
        expected_output,
        base_only=False,
        fast_check=True,
    )
    base_status = str(result["base"][0])
    plus_status = str(result["plus"][0])
    base_pass = base_status == PASS
    plus_pass = plus_status == PASS
    return EvaluationResultV2(
        base_pass=base_pass,
        plus_pass=plus_pass,
        final_pass=base_pass and plus_pass,
        base_status=base_status,
        plus_status=plus_status,
    )


class IsolatedEvalPlusEvaluatorV2:
    """Dataset-backed evaluator; every candidate suite runs in fresh children."""

    def __init__(self) -> None:
        require_evalplus_031()
        self._tasks: dict[str, dict[str, dict[str, Any]]] = {}
        self._groundtruth: dict[str, dict[str, dict[str, Any]]] = {}

    def _ensure_dataset(self, dataset: str) -> None:
        if dataset in self._tasks:
            return
        if dataset == "humaneval":
            tasks = get_human_eval_plus()
            groundtruth = get_groundtruth(tasks, get_human_eval_plus_hash(), [])
        elif dataset == "mbpp":
            tasks = get_mbpp_plus()
            groundtruth = get_groundtruth(
                tasks,
                get_mbpp_plus_hash(),
                MBPP_OUTPUT_NOT_NONE_TASKS,
            )
        else:
            raise ValueError(f"unsupported dataset: {dataset}")
        self._tasks[dataset] = tasks
        self._groundtruth[dataset] = groundtruth

    def evaluate(
        self,
        dataset: str,
        task_id: str,
        entry_point: str,
        code: str,
    ) -> EvaluationResultV2:
        self._ensure_dataset(dataset)
        problem = self._tasks[dataset].get(task_id)
        expected_output = self._groundtruth[dataset].get(task_id)
        if problem is None or expected_output is None:
            raise KeyError(f"unknown {dataset} task: {task_id}")
        if problem["entry_point"] != entry_point:
            raise ValueError(
                f"entry point mismatch for {task_id}: "
                f"expected {problem['entry_point']}, got {entry_point}"
            )
        return evaluate_problem_isolated_v2(
            dataset=dataset,
            problem=problem,
            expected_output=expected_output,
            code=code,
        )
