# Candidate Healer / Healer-vNext XOR and Safety-Loop Validation

## Scope

This isolated validation covers exactly four BitXor wrong-transformations and two `while True` safety-loop wrong-transformations from the reviewed Qwen8B public-benchmark forensic set. No model, reference solution, full benchmark, historical workbook, Original Ab3 output, or original pass@1 was modified or used to derive a semantic answer.

Candidate behavior is gated by `ASTHealer(domain_mode=...)`:

- `benchmark` is the default and preserves Python BitXor and `while True` semantics.
- `math_generator` is the only explicit gate that retains the legacy `^ -> **` and fixed-loop transformations.
- Evaluator timeout remains an evaluator responsibility and is not implemented by rewriting the submitted AST.

## Forensic inventory

| Family | Task | Raw official | Original Ab3 official | Actual wrong transformation | Second layer | Eligibility |
|---|---|---|---|---|---|---|
| XOR | Mbpp/6 | base pass / plus fail | base fail / plus fail | `a ^ b` became `a ** b` | Raw plus failure remains | eligible |
| XOR | Mbpp/311 | base fail / plus fail | base fail / plus fail | two bitwise XOR expressions became exponentiation | Raw base+plus defect remains | eligible |
| XOR | Mbpp/633 | base pass / plus fail | base fail / plus fail | pairwise XOR accumulation became exponentiation | Raw plus failure remains | eligible |
| XOR | Mbpp/735 | base fail / plus fail | base fail / plus fail | mask toggle XOR became exponentiation | Raw base+plus defect remains | eligible |
| safety-loop | HumanEval/39 | base pass / plus fail | base pass / plus fail | unbounded nested generator capped at 1000 and synthetic return added | Raw plus failure remains | eligible |
| safety-loop | Mbpp/739 | base pass / plus fail | base pass / plus fail | reachable-return search capped at 1000 and tuple return added | Raw plus failure remains | eligible |

The original diffs are recorded in `case_forensics.csv`; isolated Raw-to-Original, Raw-to-Candidate, and Original-to-Candidate diffs are under `diffs/`.

## Local semantic witnesses

All 18 sources parse and contain exactly one expected module entry point. All six runtime witnesses pass:

- Mbpp/6: with `(0, 0)`, Raw/Candidate return `False`; Original Ab3 returns `True`.
- Mbpp/311: with `(0,)`, Raw/Candidate return `1`; Original Ab3 returns `0`.
- Mbpp/633: with `([1, 2], 0)`, Raw/Candidate return `3`; Original Ab3 returns `1`.
- Mbpp/735: with `(3,)`, Raw/Candidate return `3`; Original Ab3 returns `1`.
- HumanEval/39: Raw/Candidate nested `fib()` supply 1001 requested values; Original Ab3 stops at 1000.
- Mbpp/739: with `(7,)`, Raw/Candidate return `1414`; Original Ab3 returns `(0, 0)` after its fixed cap.

These witnesses establish runtime-semantic preservation without asserting the benchmark's expected answer.

## Official EvalPlus replay

Environment: EvalPlus 0.3.1, Python 3.14.4, WSL2 Linux. HumanEval+ is v0.1.10 (`fe585eb4df8c88d844eeb463ea4d0302`); MBPP+ is v0.2.0 (`ee43ecabebf20deef4bb776a405ac5b1`).

| Task | Raw base/plus | Original Ab3 base/plus | Candidate base/plus | Final classification |
|---|---|---|---|---|
| Mbpp/6 | pass / fail | fail / fail | pass / fail | official base-regression recovery |
| Mbpp/311 | fail / fail | fail / fail | fail / fail | structural/runtime-semantics recovery only |
| Mbpp/633 | pass / fail | fail / fail | pass / fail | official base-regression recovery |
| Mbpp/735 | fail / fail | fail / fail | fail / fail | structural/runtime-semantics recovery only |
| HumanEval/39 | pass / fail | pass / fail | pass / fail | structural/runtime-semantics recovery only |
| Mbpp/739 | pass / fail | pass / fail | pass / fail | structural/runtime-semantics recovery only |

Every aggregate remains fail because plus fails in all six and the runner requires base and plus to pass. This does not erase the two official base recoveries.

## Summary

- Official full rescue: **0**
- Official base-regression recovery: **2**
- Structural/runtime-semantics recovery only: **4**
- No recovery: **0**
- Ineligible / correct refusal: **0**
- Candidate regression versus Raw: **0**

Candidate exactly matches Raw base/plus status for all six cases. The remaining official failures are pre-existing solution defects outside these two conservative Healer rules.
