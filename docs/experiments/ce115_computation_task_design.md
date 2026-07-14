# CE115 Computation-Only Task Family Design

## 1. Scope Statement

This document defines four computation-only math task families derived from the 115 CAP
(會考) paper, questions 3, 5, 7, and 9. The scope is restricted to domains that are fully
formalizable with exact arithmetic and verifiable by deterministic, generator-independent
oracles: IntegerOps, FractionOps, RadicalOps, and PolynomialOps. No models are executed
in this phase; only samplers, contracts, oracles, invariants, and targeted tests are built.

## 2. Why Questions 3, 5, 7, 9

| Source | Concept | Reason for inclusion |
|---|---|---|
| Q3 | √504 = a√b simplest radical form | Pure integer factorization + canonical radical output; exact oracle trivial |
| Q5 | 2.45×98.7 − (−0.55)×98.7 | Exact terminating-decimal rational arithmetic with distributive structure |
| Q7 | (4x²−3x−5) ÷ (x+2) quotient/remainder | Polynomial long division with a deterministic division identity |
| Q9 | 2x(x+7) − 10(x+7) = 0 roots | Factorization over rationals; roots exactly checkable by substitution |

All four admit parameterization, difficulty scaling, and exact-equality contracts.

## 3. Why Context / Geometry / Literacy Tasks Were Excluded

Excluded categories (situational modeling, figure reading, geometry, tables/charts,
long literacy passages, cross-representation reasoning) either require vision input,
depend on information not expressible in a frozen JSON payload, or lack a deterministic
single-valued oracle. They cannot be validated by exact dictionary equality without
one-off per-question adjudication, which would violate the no per-task-solver policy.

## 4. Task Family Definitions

| Family ID (task_id prefix) | skill_id / oracle_type | Source |
|---|---|---|
| `ce115_calc_radical_simplification` | `radical_simplification` | Q3 |
| `ce115_calc_exact_rational_expression` | `exact_rational_expression` | Q5 |
| `ce115_calc_polynomial_division` | `polynomial_division_general` | Q7 |
| `ce115_calc_polynomial_factor_roots` | `polynomial_factor_roots` | Q9 |

Each family has three manifest rows (`_l1`, `_l2`, `_l3`) in
`tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl`, following the
existing CE115 pilot row schema (parameter_ranges, oracle_type, randomization contract).

Note: `polynomial_division_general` is a **new** oracle_type; the existing production
`polynomial_division_exact` (scalar `remainder`, `divisor_root` payload) is left untouched.
No migration of the legacy contract is performed or needed — the two coexist and are
selected per task row.

## 5. Operational L1/L2/L3 Definitions

**Radical simplification**
- L1: radicand = k²·m with a single small square factor, k ∈ [2,5], m ∈ {2,3,5,6,7,10}; one extraction step.
- L2: composite square coefficient k ∈ {6,10,12,14,15} (multiple prime squares), larger radicand; requires full prime factorization or repeated extraction.
- L3: adds an outer integer coefficient c ∈ [2,5] multiplying the root (answer coefficient = c·k); k ∈ [4,12].

**Exact rational expression**
- L1: two products sharing one right factor (three decimal digits, e.g. 88.7–99.9), left operands constructed so the pair sums to a small integer (2–5); two-step distributive evaluation.
- L2: two-to-three products sharing a right factor, mixed random signs, two-decimal left operands in (1.01–8.99); result generally a non-integer reduced fraction.
- L3: three-to-four products with independent right factors and mixed signs; multi-step exact accumulation.

**Polynomial division**
- L1: degree-2 dividend, monic linear divisor, integer coefficients in [−8,8].
- L2: degree-3 dividend with one forced zero middle coefficient (missing term), monic divisor, coefficients in [−9,9].
- L3: degree-3 dividend, non-monic divisor leading ∈ {−2,2,3}; rational quotient coefficients possible; exact arithmetic mandatory.

**Polynomial factorization and roots**
- L1: two distinct integer roots in [−6,6], overall factor ∈ {1,2} (common-factor structure).
- L2: integer roots in [−9,9], overall factor ∈ {2,3} (larger expanded coefficients).
- L3: at least one rational root (denominators {2,3,5}); two-step factorization.

## 6. Sampler Fields (frozen oracle_payload)

| Family | Payload fields |
|---|---|
| radical_simplification | `radicand` (= k²·m), optional `outer_coefficient` (L3) |
| exact_rational_expression | `products`: list of `{sign: ±1, left: "d.dd", right: "d.d"}` exact decimal strings |
| polynomial_division_general | `dividend_coefficients` (highest degree first), `divisor_coefficients` ([leading, constant]) |
| polynomial_factor_roots | `quadratic_coefficients` ([a, b, c]) |

All sampling is deterministic per (task_id, seed) via the existing `_rng` SHA-256 local
RNG. Degenerate cases are rejected in-sampler: perfect-square radicands, zero-valued
expressions, zero leading/divisor coefficients, repeated roots.

## 7. Answer Contracts

- radical: `{"coefficient": int, "radicand": int}` — radicand square-free, coefficient > 0.
- rational: `{"value": str}` — canonical integer string or irreducible `p/q`, positive denominator, no decimals.
- division: `{"quotient_coefficients": list[int|"p/q"], "remainder_coefficients": list[int|"p/q"]}` — highest degree first; remainder list length = divisor degree (1).
- roots: `{"roots": list[int|"p/q"]}` — exactly two distinct roots, **ascending numeric order**, repeated roots are disallowed by the sampler and rejected by the oracle.

All four use exact dictionary equality, no tolerance, no floats. Canonical number encoding
matches the existing pilot style: Python `int` when integral, otherwise irreducible `"p/q"` string.

## 8. Oracle Rules

Each oracle recomputes the expected answer independently from the frozen payload
(`agent_tools/finals_rebuild/math_task_oracles.py`), never reading generator code:

- `evaluate_radical_simplification`: independent trial-division factorization; fails closed on perfect squares or non-positive inputs.
- `evaluate_exact_rational_expression`: `Fraction(decimal_string)` exact accumulation; fails closed on zero totals or non-string operands.
- `evaluate_polynomial_division_general`: exact synthetic long division over `Fraction`; fails closed on non-linear or zero-leading divisors.
- `evaluate_polynomial_factor_roots`: integer discriminant + `isqrt` perfect-square check; fails closed on irrational, complex, or repeated roots.

## 9. Deterministic Invariants (tested)

1. Radical: `(coefficient/outer)² × square_free_radicand == radicand`, radicand square-free.
2. Rational: expected value exactly equals the Fraction sum; reduced; no decimal point in output.
3. Division identity: `dividend == divisor × quotient + remainder`, `deg(remainder) < deg(divisor)`.
4. Roots: each root satisfies `a·r² + b·r + c == 0`, two distinct roots, ascending order.

## 10. Domain Mapping (routing)

Direct manifest aliases only (no fuzzy fallback, thresholds untouched):

| skill_id alias | Target skill |
|---|---|
| `radical_simplification` | `jh_數學2上_FourOperationsOfRadicals` |
| `exact_rational_expression` | `jh_數學1上_FourArithmeticOperationsOfNumbers` |
| `polynomial_division_general` | `jh_數學2上_FourArithmeticOperationsOfPolynomial` |
| `polynomial_factor_roots` | `jh_數學2上_FourArithmeticOperationsOfPolynomial` |

## 11. Capability Gap Table

| Family | Gap type | Notes |
|---|---|---|
| radical_simplification | NO_GAP | `RadicalOps.simplify` / `simplify_term` / `get_prime_factors` already cover simplification; plain Python also suffices |
| exact_rational_expression | NO_GAP | `fractions.Fraction` + `FractionOps` fully sufficient |
| polynomial_division | NO_GAP (resolved) | `PolynomialOps.div_qr` implemented, runtime-registered, and prompt-exposed; see §12 |
| polynomial_factor_roots | MODEL_SHOULD_IMPLEMENT_WITH_NORMAL_PYTHON | Integer discriminant + `isqrt` is a ten-line exact routine; a factoring primitive is not justified yet |

Domain sufficiency: IntegerOps ✅, FractionOps ✅, RadicalOps ✅, PolynomialOps ✅.

## 12. Primitive Recommendations

- `PolynomialOps.div_qr(dividend_coefficients, divisor_coefficients) -> (quotient_coefficients, remainder_coefficients)`:
  **implemented** (`core/prompts/domain_function_library.py`, both the runtime-injected
  class and the `POLYNOMIALOPS_HELPERS` prompt copy).
  - Coefficient order: highest degree first, inputs and outputs.
  - Inputs: `int`, `Fraction`, or irreducible `"p/q"` strings; floats, bools, decimal
    strings, malformed fractions, zero denominators, empty lists, and zero divisors all
    raise `ValueError` (fail closed).
  - Exact arithmetic via `fractions.Fraction`; outputs canonical (`int` when integral,
    otherwise irreducible `"p/q"` with positive denominator), leading zeros removed,
    zero polynomial is `[0]`.
  - Supports monic and non-monic divisors of **any** degree (not restricted to linear).
  - Invariants `dividend = divisor × quotient + remainder` and
    `degree(remainder) < degree(divisor)` are test-enforced.
  - Prompt exposure: an Ab2d-only `REUSABLE` block appended after
    `=== SKILL_END_PROMPT ===` in the Polynomial SKILL.md — picked up by the Ab2d
    reusable-section loader but outside the Ab2g base-rules split, so the frozen
    Ab2g prompt is byte-unchanged (regression-tested).
  - Tests: `tests/test_polynomial_div_qr.py` (44 tests: correctness, canonicalization,
    invariants, fail-closed, runtime injection, prompt exposure, Ab1/Ab2g regression).
- No radical, rational, or factoring primitives are added: existing APIs plus standard
  library cover them.
- No per-question solvers.

## 13. Development / Validation Freeze Policy

These twelve task rows are **development set** artifacts. The original CAP numbers
(504; 2.45/0.55/98.7; 4x²−3x−5 ÷ x+2; 2x(x+7)−10(x+7)) appear only in oracle golden-case
tests, never in samplers, prompts, contracts, or neutral statements. Formal validation
requires: fresh seeds, a frozen manifest, and a frozen commit of prompts/functions/oracles;
validation outcomes must not be fed back into treatment changes.

## 14. Exact Files and Tests

Modified / added in this round:

- `tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl` — +12 task rows
- `agent_tools/finals_rebuild/math_task_sampler.py` — 4 new sampler branches + exact decimal helper
- `agent_tools/finals_rebuild/math_task_oracles.py` — 4 new oracle evaluators + dispatch entries
- `agent_tools/finals_rebuild/math_answer_contracts.py` — 4 contracts + 4 neutral task statements
- `agent_skills/*/skill.json` — 4 new direct aliases (3 files)
- `tests/test_ce115_computation_tasks.py` — 70 targeted tests: determinism, no-float,
  oracle accept/reject, per-family invariants, golden cases, fail-closed behavior,
  contract/statement registration, leakage, direct-alias routing
- `docs/experiments/ce115_computation_task_design.md` — this document
