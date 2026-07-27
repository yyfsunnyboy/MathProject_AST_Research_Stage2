"""Focused state-isolation tests for the EvalPlus evaluator v2."""

from __future__ import annotations

import copy
import unittest

from scripts.evalplus_isolated_evaluator_v2 import evaluate_problem_isolated_v2


def _problem(base_input, plus_input):
    return {
        "task_id": "Mbpp/synthetic",
        "entry_point": "candidate",
        "base_input": base_input,
        "plus_input": plus_input,
        "atol": 0,
    }


def _expected(base, plus):
    return {
        "base": base,
        "plus": plus,
        "base_time": [0.0] * len(base),
        "plus_time": [0.0] * len(plus),
    }


GOOD = "def candidate(x):\n    return len(x)\n"
BAD = "def candidate(x):\n    return -1\n"


def _evaluate(code: str):
    return evaluate_problem_isolated_v2(
        dataset="mbpp",
        problem=_problem([[[1, 2, 3]]], [[[4, 5]]]),
        expected_output=_expected([3], [2]),
        code=code,
        add_standard_prefix=False,
    )


class EvalPlusIsolatedEvaluatorV2Tests(unittest.TestCase):
    def test_same_source_repeated_is_identical(self) -> None:
        self.assertEqual(_evaluate(GOOD), _evaluate(GOOD))

    def test_equal_raw_and_final_sources_are_identical(self) -> None:
        raw_source = GOOD
        final_source = raw_source
        self.assertEqual(_evaluate(raw_source), _evaluate(final_source))

    def test_candidate_order_does_not_change_results(self) -> None:
        good_then_bad = (_evaluate(GOOD), _evaluate(BAD))
        bad_then_good = (_evaluate(BAD), _evaluate(GOOD))
        self.assertEqual(good_then_bad[0], bad_then_good[1])
        self.assertEqual(good_then_bad[1], bad_then_good[0])

    def test_mutation_does_not_pollute_later_evaluation(self) -> None:
        cases = [
            ("list", [1, 2], "x.clear()", "len(x)", 2),
            ("dict", {"a": 1}, "x.clear()", "len(x)", 1),
            ("set", {1, 2}, "x.clear()", "len(x)", 2),
            ("nested_list", [[1, 2], [3]], "x[0].clear()", "len(x[0])", 2),
        ]
        for name, value, mutation, observation, expected_value in cases:
            with self.subTest(container=name):
                base_inputs = [[copy.deepcopy(value)]]
                plus_inputs = [[copy.deepcopy(value)]]
                original_base = copy.deepcopy(base_inputs)
                original_plus = copy.deepcopy(plus_inputs)
                mutator = f"def candidate(x):\n    {mutation}\n    return 0\n"
                observer = f"def candidate(x):\n    return {observation}\n"
                problem = _problem(base_inputs, plus_inputs)

                mutated_result = evaluate_problem_isolated_v2(
                    dataset="mbpp",
                    problem=problem,
                    expected_output=_expected([0], [0]),
                    code=mutator,
                    add_standard_prefix=False,
                )
                observed_result = evaluate_problem_isolated_v2(
                    dataset="mbpp",
                    problem=problem,
                    expected_output=_expected([expected_value], [expected_value]),
                    code=observer,
                    add_standard_prefix=False,
                )

                self.assertTrue(mutated_result.final_pass)
                self.assertTrue(observed_result.final_pass)
                self.assertEqual(base_inputs, original_base)
                self.assertEqual(plus_inputs, original_plus)


if __name__ == "__main__":
    unittest.main()
