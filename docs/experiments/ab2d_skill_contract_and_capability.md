# Ab2d Skill Contract and Capability Audit

## 1. Task-to-Skill Mapping

Under the current implementation of the policy registry (`core/skill_policies/registry.py`), the task's `skill_id` is passed as `raw_skill_id` to `normalize_skill_id`. Because these IDs are not registered in the `aliases` of any `skill.json` manifests or policies, and their similarity scores are below the registry's case-sensitive edit distance threshold of `0.300`, all five task skill IDs resolve to **`"Unknown"`**.

During Stage A pilot runs (`math_boundary_pilot.py`), folder mapping is bypassed because prompts are constructed dynamically in Python code. However, logically mapping tasks to their corresponding mathematical skill domains yields the following:

1. `ce115_q07_polynomial_division_l1`
   - **Task skill_id**: `polynomial_division_quotient_remainder`
   - **Normalized skill ID (registry)**: `Unknown` (no alias match; difflib ratio is `0.244` vs `Polynomial` candidate)
   - **Logical Skill Folder**: `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial` (family: `polynomial`)
   - **Evidence**: `skill.json` manifest in the polynomial folder defines `"family": "polynomial"` and `"injected_apis": ["PolynomialOps"]`.

2. `ce115_q24_rotation_speed_conversion_l1` / `l2`
   - **Task skill_id**: `rpm_circumference_to_kph`
   - **Normalized skill ID (registry)**: `Unknown` (no alias match; difflib ratio is `0.215` vs `Numbers` candidate)
   - **Logical Skill Folder**: `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers` (family: `fraction`)
   - **Evidence**: `skill.json` manifest in the numbers folder defines `"family": "fraction"` and `"injected_apis": ["IntegerOps", "FractionOps"]`.

3. `ce115_q20_largest_proper_divisor_l3`
   - **Task skill_id**: `largest_proper_divisor_reasoning`
   - **Normalized skill ID (registry)**: `Unknown` (no alias match; difflib ratio is `0.378` vs `Integers` candidate, but because `difflib.get_close_matches` is case-sensitive, it yields empty matches)
   - **Logical Skill Folder**: `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers` (family: `integer`)
   - **Evidence**: `skill.json` manifest in the integers folder defines `"family": "integer"` and `"injected_apis": ["IntegerOps"]`.

4. `ce115_cr01_training_sequence_threshold_l3`
   - **Task skill_id**: `alternating_training_progression_threshold`
   - **Normalized skill ID (registry)**: `Unknown` (no alias match; difflib ratio is `0.310` vs `Integers` candidate, but yields no matches due to case-sensitivity)
   - **Logical Skill Folder**: `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers` (family: `integer`)
   - **Evidence**: `skill.json` manifest defines `"family": "integer"`.

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
- **Deterministic Check**: Verify if $(\text{quotient\_poly}(x) \times (x - \text{divisor\_root})) + \text{remainder} == \text{dividend\_poly}(x)$ identically.
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
- **Deterministic Check**: For each claim $C$ (subject $S$, candidate factor $F$):
  - Generate possible numbers $N_{possible}$ from $L = \text{largest\_proper\_divisors}[S]$ using primes.
  - Check if all numbers in $N_{possible}$ are divisible by $F$.
  - Compare with the submitted claim boolean value.
- **Pass Condition**: Truth value of each claim matches the mathematical necessity check.
- **Catches**: Logic errors in claim necessity logic, incorrect prime factorization mappings.
- **Does Not Catch**: Capitalization differences in subject labels.

### 4. `alternating_sequence_threshold_boundary_invariant` (Task 5)
- **Required Inputs**: `track_length_m`, `initial_first_day_laps`, `same_week_increment_laps`, `threshold_km`, `day_labels`, `first_exceed_week`, `first_exceed_day`, `specified_session_laps`, `specified_week`, `specified_day`.
- **Deterministic Check**:
  - Calculate `laps(specified_week, specified_day)` and verify it equals `specified_session_laps`.
  - Let $s$ be the session index of the first exceed week and day.
  - Verify that $\text{distance}(s) > \text{threshold\_km} \times 1000$ AND $\text{distance}(s - 1) \le \text{threshold\_km} \times 1000$.
- **Pass Condition**: Specified laps are correct, the exceed session strictly crosses the boundary, and the prior session does not.
- **Catches**: Week/day indexing off-by-one errors, sequence calculation errors, inequality comparison errors.
- **Does Not Catch**: Day name translations or formatting differences in text labels.

---

## 4. Revised RPM Readiness

- **實際 skill folder**: **None** (does not exist in `agent_skills/`; maps to `"Unknown"` under registry normalization).
- **Prompt coverage**: **None** (no prompt file is checked in for this skill; the prompt is hardcoded inside `math_boundary_pilot.py`'s `build_ab1_prompt`/`build_ab2g_prompt`).
- **Circumference formula**: Circumference $C$ is passed directly as `circumference_cm` (integer) from task spec; no circumference calculation (such as $2\pi r$ or $\pi d$) is performed.
- **Unit conversion**: Convert cm/min to km/h: $\text{coefficient} = \text{circumference\_cm} \times 60 / 100000 = \frac{3 \times \text{circumference\_cm}}{5000}$.
- **π representation**: None (not used in this task).
- **Rounding / tolerance / return type**: Output must be exact. Return type is `str` representing the simplified ratio `p/q` (or `int` if denominator is 1). Tolerance is None (exact equality).
- **Evaluator contract**: Exact dictionary match on `{"coefficient": str, "unit": "km/h"}`.
- **Readiness Verdict**: **UNCERTAIN_NEEDS_RUNTIME_CONFIRMATION**. While the mathematical conversion is extremely simple and easily solved with standard Fraction arithmetic (making the tools ready), the lack of a dedicated skill folder and prompt coverage in `agent_skills/` means the Ab2d/Ab3 pipeline cannot resolve the prompt path without modifications to the task spec or runner configuration.

---

## 5. Final check() Decision

We aligned the `check()` function at the bottom of [prompt_benchmark.md](file:///C:/Projects/MathProject_AST_Research/agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_benchmark.md) with the standard contract in [SKILL.md](file:///C:/Projects/MathProject_AST_Research/agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/SKILL.md):
- Uses double quotes for strings.
- Uses exact float equality `float(user_answer) == float(correct_answer)` instead of epsilon tolerance comparison.
- Verified that all code fences are balanced and `ast.parse` checks pass with a 100% success rate.
- **Note**: `check()` semantic contract remains unresolved and is deferred to the next round.

---

## 6. Unresolved Items and Deferred Decisions

- **5/5 Task Skill IDs**: All five task skill IDs currently resolve to `Unknown` under registry normalization.
- **Logical Folder Mapping**: Logical mapping is not yet runtime mapping; active routing remains unconfigured.
- **RPM Golden-Path**: The RPM golden-path runtime contract has not yet been validated.
- **check() Semantics**: The check() semantic contract remains unresolved and is deferred to the next round.
- **Proposed Primitives**: Proposed primitives are not yet approved or implemented.
- **K-12 Capability Coverage**: K-12 capability coverage is not yet established; the five tasks are pilot-only.

---

## 7. Files Inspected

- `GEMINI.md`
- `tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl`
- `agent_tools/finals_rebuild/math_boundary_pilot.py`
- `agent_tools/finals_rebuild/math_task_oracles.py`
- `agent_tools/finals_rebuild/math_task_sampler.py`
- `tests/finals_rebuild/test_math_task_schema.py`
- `core/skill_policies/registry.py`
- `core/skill_policies/fraction.py`
- `core/engine/classifier.py`
- `core/engine/scaler.py`
- `agent_tools/benchmark.py`
- `core/scaffold/domain_libs.py`
- `core/code_generator.py`
- `core/prompts/domain_function_library.py`
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_benchmark.md`
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/skill.json`
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers/prompt_benchmark.md`
- `agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers/skill.json`
- `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial/prompt_benchmark.md`
- `agent_skills/jh_數學2上_FourArithmeticOperationsOfPolynomial/skill.json`
- `agent_skills/jh_數學2上_FourOperationsOfRadicals/prompt_benchmark.md`
- `agent_skills/jh_數學2上_FourOperationsOfRadicals/skill.json`
- `agent_tools/check_fake_api.py`

---

## 8. Files Modified

- [prompt_benchmark.md](file:///C:/Projects/MathProject_AST_Research/agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_benchmark.md)
- [ab2d_skill_contract_and_capability.md](file:///C:/Projects/MathProject_AST_Research/docs/experiments/ab2d_skill_contract_and_capability.md)
