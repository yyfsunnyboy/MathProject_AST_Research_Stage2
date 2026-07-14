# Ab2d Skill Contract and Capability Audit

## Routing Repair

- **Original Status**: All five pilot task skill IDs resolved to `"Unknown"` because they were not registered in any manifest aliases and fell below the case-sensitive edit-distance threshold of `0.300`.
- **Alias Mapping Table**:
  We established 4 unique aliases covering the 5 pilot tasks (since L1 and L2 of the RPM task share the same skill ID):

| External skill_id | Target Skill Folder | Mapping Status | Rationale |
|---|---|---|---|
| `polynomial_division_quotient_remainder` | `jh_數學2上_FourArithmeticOperationsOfPolynomial` | `SEMANTIC_MATCH` | Matches polynomial division domain directly. |
| `rpm_circumference_to_kph` | `jh_數學1上_FourArithmeticOperationsOfNumbers` | `TEMPORARY_FAMILY_MAPPING` | Mapped to fraction/rational operations family temporarily. |
| `largest_proper_divisor_reasoning` | `jh_數學1上_FourArithmeticOperationsOfIntegers` | `TEMPORARY_FAMILY_MAPPING` | Mapped to integer operations family temporarily. |
| `alternating_training_progression_threshold` | `jh_數學1上_FourArithmeticOperationsOfIntegers` | `TEMPORARY_FAMILY_MAPPING` | Mapped to integer operations family temporarily. |

- **Temporary Mappings**:
  - `rpm_circumference_to_kph` -> `jh_數學1上_FourArithmeticOperationsOfNumbers` (fraction family)
  - `largest_proper_divisor_reasoning` -> `jh_數學1上_FourArithmeticOperationsOfIntegers` (integer family)
  - `alternating_training_progression_threshold` -> `jh_數學1上_FourArithmeticOperationsOfIntegers` (integer family)
- **Runtime Test Results**:
  - Verified by `pytest tests/test_routing_and_rpm.py -v`.
  - All 4 unique aliases successfully resolve directly via registry's inner `_ALIAS_TABLE` lookup mapping, and standard `normalize_skill_id` resolves them correctly without fuzzy edit-distance fallback.
- **Algorithm Constraints**:
  - We did not modify the global routing algorithm, similarity/edit-distance threshold, or case-sensitivity behavior. All repairs are accomplished entirely through declaratively registered `aliases` inside individual `skill.json` manifests.

---

## RPM Golden-Path Contract

- **Entry Point**: `generate` (specifically `def generate(level=1, **kwargs)` callable with no arguments).
- **Input Schema**:
  - Sampled parameters are passed in the task specification's `oracle_payload` containing:
    - `circumference_cm` (integer)
    - `rpm_symbol` (string, e.g. `"rpm"`)
    - `requested_unit` (string, e.g. `"km/h"`)
- **Output Schema**:
  - A dictionary returned from `generate()` containing exactly:
    - `question_text`: `str`
    - `correct_answer`: `dict`
    - `oracle_payload`: `dict`
  - The `correct_answer` dictionary must contain:
    - `coefficient`: `str`
    - `unit`: `str`
- **Exact Arithmetic Rule**:
  - Formula: \(\text{coefficient\_kph} = \frac{\text{rpm} \times \text{circumference\_cm} \times 60}{100000}\) (where \(\text{rpm} = 1\)).
  - Calculations must use `Fraction` or equivalent exact rational arithmetic to prevent floating-point rounding or tolerance drift.
- **Canonical Fraction Rule**:
  - The `coefficient` value must be a simplified fraction string in the format `"p/q"` (e.g. `"9/100"` or `"3/50"`).
  - If the denominator simplifies to 1, the value is a string representing the integer (e.g. `"3"`).
  - *Observation*: Within the actual L1/L2 parameter ranges (`circumference_cm` range `[100, 260]`), no valid integer choice can result in a denominator of 1 since \(C \times 3 / 5000\) requires a multiple of \(5000/3\) (which is \(\approx 1666.67\)).
- **Unit Rule**:
  - The `unit` field inside the `correct_answer` dictionary must be exactly `"km/h"`.
- **Evaluator Comparison Behavior**:
  - **Exact Dictionary Match**: The evaluator does a direct `==` comparison in Python between the submitted `correct_answer` dictionary and the oracle's expected `correct_answer` dictionary.
  - This checks exact key-value string/structural equality (e.g. `{"coefficient": "9/100", "unit": "km/h"}`). There is no floating-point tolerance, whitespace stripping, or semantic equivalence normalization.
- **Positive and Negative Test Results**:
  - **Spec Assertion Tests (PASSED)**:
    - L1 exact canonical fraction (`C = 150` -> `"9/100"`)
    - L2 exact canonical fraction
    - Fully simplified reducible fractions (`C = 100` -> `"3/50"`)
  - **Characterization Tests (PASSED/RECORDED)**:
    - Non-string numeric coefficient type (e.g. float `0.09` or int `3`) fails evaluation due to exact dict comparison mismatch.
    - Non `"km/h"` units (e.g. `"m/s"`) fails evaluation.
    - Mathematically equivalent but non-canonical fraction strings (e.g. `"18/200"`) fails evaluation.
    - Missing `coefficient` or `unit` keys fails evaluation.

---

## 2. Revised Reusable Primitives

Below are the audited, generic mathematical primitives proposed to resolve the identified capability gaps:

### 1. `PolynomialOps.div_qr`
- **Target Module**: `PolynomialOps` in `core/prompts/domain_function_library.py`
- **Minimal Signature**: `def div_qr(dividend: list[Fraction|int], divisor: list[Fraction|int]) -> tuple[list[Fraction], list[Fraction]]`
- **Input Schema**:
  - `dividend`: list of numbers/Fractions (coefficients, highest degree first)
  - `divisor`: list of numbers/Fractions (coefficients, highest degree first)
- **Output Schema**: `tuple[list[Fraction], list[Fraction]]` (quotient coefficients and remainder coefficients lists)
- **Real Divisor Contract Compatibility**: Returns lists of coefficients. For a linear divisor, the remainder is a list of length 1 containing the single term which is the remainder (represented as a Fraction or int, conforming to `math_task_oracles.py` where the divisor contract expects an `int` or a `Fraction` string).
- **Solved Gap**: Performs standard polynomial long division deterministically without using SymPy or custom ad-hoc loops in the sandboxed code.
- **Reusable Tasks**: `ce115_q07_polynomial_division_l1`/`l2`/`l3`.
- **Minimum Tests**: Verify that dividing $[2, 3, -5]$ by $[1, -1]$ returns $([2, 5], [0])$.

### 2. `IntegerOps.smallest_prime_factor` & `IntegerOps.primes_up_to`
- **Target Module**: `IntegerOps` in `core/prompts/domain_function_library.py`
- **Minimal Signatures**:
  - `def smallest_prime_factor(n: int) -> int`
  - `def primes_up_to(limit: int) -> list[int]`
- **Input Schema**: `n: int` / `limit: int`
- **Output Schema**: `int` / `list[int]`
- **Solved Gap**: Enables prime factorization and listing of primes below a limit, which are generic number theory primitives that can be combined to solve the candidate number search.
- **Reusable Tasks**: `ce115_q20_largest_proper_divisor_l1`/`l2`/`l3`.
- **Minimum Tests**: `smallest_prime_factor(15) == 3`; `primes_up_to(3) == [2, 3]`.

### 3. `IntegerOps.solve_progression_threshold`
- **Target Module**: `IntegerOps` in `core/prompts/domain_function_library.py`
- **Minimal Signature**: `def solve_progression_threshold(term_func: Callable[[int], Fraction|int], threshold: Fraction|int, max_steps: int = 1000) -> int`
- **Input Schema**:
  - `term_func`: callable function mapping index `s` to the term value
  - `threshold`: Fraction or int value
  - `max_steps`: safety loop break limit (default `1000`)
- **Output Schema**: `int` (the first index `s` where `term_func(s) > threshold`)
- **Solved Gap**: Solves boundary threshold crossings of general progression sequences.
- **Reusable Tasks**: `ce115_cr01_training_sequence_threshold_l1`/`l2`/`l3`.
- **Minimum Tests**: Exceeding `Fraction(25, 4)` with sequence `3 + (s // 2 + s % 2)` yields session index 4.

---

## 3. Five Deterministic Invariants

### 1. `polynomial_division_identity`
- **Required Inputs**: `dividend_coefficients` (degree 2), `divisor_root`, `quotient_coefficients`, `remainder`.
- **Deterministic Check**: Verify if \((\text{quotient\_poly}(x) \times (x - \text{divisor\_root})) + \text{remainder} == \text{dividend\_poly}(x)\) identically.
- **Pass Condition**: The coefficients of the reconstructed polynomial exactly match the input dividend coefficients.
- **Catches**: Sign errors, calculation mistakes, wrong degree of quotient.
- **Does Not Catch**: Output format typos in Chinese text descriptions.

### 2. `rotation_speed_fractional_equivalence` (Task 2 & 3)
- **Required Inputs**: `circumference_cm`, `coefficient`.
- **Deterministic Check**: Verify `Fraction(coefficient) * 100000 / 60 == Fraction(circumference_cm)`.
- **Pass Condition**: Reconstructed circumference is exactly equal to the input `circumference_cm`.
- **Catches**: Rounding errors, unit factor inversion, incorrect conversion constants.
- **Does Not Catch**: Typos in unit names or question text descriptions.

### 3. `largest_proper_divisor_necessity_validation` (Task 4)
- **Required Inputs**: `largest_proper_divisors`, `claims`, `submitted_claims` (boolean list).
- **Deterministic Check**: For each claim \(C\) (subject \(S\), candidate factor \(F\)):
  - Generate possible numbers \(N_{possible}\) from \(L = \text{largest\_proper\_divisors}[S]\) using primes.
  - Check if all numbers in \(N_{possible}\) are divisible by \(F\).
  - Compare with the submitted claim boolean value.
- **Pass Condition**: Truth value of each claim matches the mathematical necessity check.
- **Catches**: Logic errors in claim necessity logic, incorrect prime factorization mappings.
- **Does Not Catch**: Capitalization differences in subject labels.

### 4. `alternating_sequence_threshold_boundary_invariant` (Task 5)
- **Required Inputs**: `track_length_m`, `initial_first_day_laps`, `same_week_increment_laps`, `threshold_km`, `day_labels`, `first_exceed_week`, `first_exceed_day`, `specified_session_laps`, `specified_week`, `specified_day`.
- **Deterministic Check**:
  - Calculate `laps(specified_week, specified_day)` and verify it equals `specified_session_laps`.
  - Let \(s\) be the session index of the first exceed week and day.
  - Verify that \(\text{distance}(s) > \text{threshold\_km} \times 1000\) AND \(\text{distance}(s - 1) \le \text{threshold\_km} \times 1000\).
- **Pass Condition**: Specified laps are correct, the exceed session strictly crosses the boundary, and the prior session does not.
- **Catches**: Week/day indexing off-by-one errors, sequence calculation errors, inequality comparison errors.
- **Does Not Catch**: Day name translations or formatting differences in text labels.

## check() Contract Decision

- **是否進 payload**: No, all `check()` stubs, examples, and function implementations have been completely stripped and removed from the final assembled payload.
- **是否被 evaluator 呼叫**: No, the evaluator `classify_response` inside `math_boundary_pilot.py` only imports and calls `generate()`. It does not call or check `check()`.
- **是否移除**: Yes, the actual `check()` implementation blocks were removed from both Integers and Numbers `prompt_benchmark.md` files, any structural templates in `Integers/SKILL.md` were cleared, and any remaining stubs in other `SKILL.md` files are dynamically stripped during prompt loading.
- **移除理由**: The prompt-defined generic `check()` compared simple strings or floats, which directly conflicted with the dictionary-based task oracle structures (e.g., RPM returning a dict of coefficient/unit). Removing it simplifies and cleans up the contract.
- **未修改 oracle/evaluator**: No changes were made to the evaluators, oracles, or routing codes.

## Payload Snapshot Verification

| Task ID | Normalized Skill | Skill Folder | APIs | check() present | Contract valid | Blocking issue |
|---|---|---|---|---|---|---|
| `ce115_q07_polynomial_division_l1` | `jh_數學2上_FourArithmeticOperationsOfPolynomial` | `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial` | `PolynomialOps` | NO | YES | NONE |
| `ce115_q24_rotation_speed_conversion_l1` | `jh_數學1上_FourArithmeticOperationsOfNumbers` | `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers` | `IntegerOps`, `FractionOps` | NO | YES | NONE |
| `ce115_q24_rotation_speed_conversion_l2` | `jh_數學1上_FourArithmeticOperationsOfNumbers` | `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers` | `IntegerOps`, `FractionOps` | NO | YES | NONE |
| `ce115_q20_largest_proper_divisor_l3` | `jh_數學1上_FourArithmeticOperationsOfIntegers` | `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers` | `IntegerOps` | NO | YES | NONE |
| `ce115_cr01_training_sequence_threshold_l3` | `jh_數學1上_FourArithmeticOperationsOfIntegers` | `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers` | `IntegerOps` | NO | YES | NONE |

*Explanation of Verification*: With the implementation of the metadata-driven dynamic answer contract renderer (fully decoupled from test fixtures), task-specific structured output schemas are now correctly injected into the final assembled payloads. The prompts no longer contain conflicting global statements requiring `correct_answer: str`, making all output schemas explicit and valid for the task oracles.

## Remaining Blocks

- **primitive 尚未核准**: The mathematical domain primitives (`PolynomialOps.div_qr`, `IntegerOps.smallest_prime_factor`, and `IntegerOps.solve_progression_threshold`) are not yet approved or implemented.
- **temporary family mappings**: Tasks for RPM, divisor reasoning, and sequence threshold crossings are temporarily routed to broader numbers/integers skill families, rather than task-specific specialized families.
- **K–12 capability census 尚未完成**: The full audit of capability gaps across all K-12 math modules is still pending.
- **尚未跑 Ab2d 模型**: Execution of the assembled prompt payloads using Ollama / Qwen / Gemini models is deferred.
