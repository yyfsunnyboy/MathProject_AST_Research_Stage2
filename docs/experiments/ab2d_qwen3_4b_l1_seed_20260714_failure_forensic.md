# Ab2d 4-task L1 smoke failure forensic — 2026-07-14

## Scope and method

This is a read-only forensic analysis of the tracked result
`docs/experiments/results/ab2d_qwen3_4b_l1_seed_20260714_smoke.jsonl` at
`main @ 52eec4763b6f13a758f5cbba17e4ba6655feb44f`.  No model request, retry,
Healer, prompt, sampler, oracle, or evaluator change was made.

Each record was replayed locally from its stored `candidate_extracted` source
through the production evaluator helper
`agent_tools.finals_rebuild.math_boundary_pilot._execute_generate(source,
skill_id=...)`, followed by
`evaluate_math_task_oracle(task["oracle_type"], task_parameters, correct_answer)`.
The replay uses the same no-argument invocation as production: `generate()`.
For polynomial candidates the execution namespace includes `PolynomialOps`; all
candidates also receive `IntegerOps` and `FractionOps`.  The stored raw response
has exactly one `python` fence in every case, so extraction selects its sole
fenced body.

For every row, the stored final Ab2d prompt contains the exact sorted frozen
`task_parameters`; the candidate's returned `oracle_payload` equals those same
parameters whenever the candidate returns.  The JSONL's `question` field is
`null` by design; the generated `question_text` below is the actual value
returned by the candidate.

## Production data flow

`sample_task_parameters(task, 20260714)` -> frozen `oracle_payload` ->
`build_ab2d_prompt(task, frozen)` -> Ollama raw first-attempt response ->
`extract_code` (one Python fence) -> AST validation (one `generate`) ->
`_execute_generate` (no positional/keyword arguments) -> exact dictionary
comparison by `evaluate_math_task_oracle`.

No first divergence was found in `task_id`, seed, L1 difficulty, frozen
parameters, or candidate-returned payload.  The sampler task ids and oracle
types were read from
`tests/finals_rebuild/fixtures/math_generation_tasks_ce115_pilot.jsonl`.

## Task: polynomial_division_quotient_remainder

**Sampled parameters:** `{"dividend_coefficients": [3, -5, -2], "divisor_root": 2}`

**Oracle expected:** `{"quotient_coefficients": [3, 1], "remainder": 0}`.
Independent calculation gives
`3x^2 - 5x - 2 = (x - 2)(3x + 1) + 0`; the oracle is correct.

**Answer contract / final prompt:** the stored Ab2d prompt requires exactly
`question_text`, `correct_answer`, and `oracle_payload`; its polynomial contract
requires `quotient_coefficients` and a scalar `remainder`.  It embeds the frozen
parameters above.  Raw first-attempt output is one `python` fence; canonical
extraction returned the following candidate source unchanged.

```python
def generate(level=1, **kwargs):
    dividend_coefficients = [3, -5, -2]
    divisor_root = 2
    quotient_coefficients, remainder = PolynomialOps.div_qr(
        dividend_coefficients, [1, -2]
    )
    question_text = f"求 $({3}x^{{2}}-5x-2)$ 除以 $(x-2)$ 的商式與餘式。"
    return {
        "question_text": question_text,
        "correct_answer": {
            "quotient_coefficients": quotient_coefficients,
            "remainder": remainder,
        },
        "oracle_payload": {
            "dividend_coefficients": [3, -5, -2],
            "divisor_root": 2,
        },
    }
```

**Candidate intended logic:** call the injected division API using the right
divisor coefficients `[1, -2]`, then return its quotient and remainder.

**Candidate actual result / replay returned value:**
`{"quotient_coefficients": [3, 1], "remainder": [0]}`; replay traceback:
none.  The candidate entry point is exactly one `generate(level=1, **kwargs)`;
production and replay pass no arguments.  The returned question is
`求 $(3x^2-5x-2)$ 除以 $(x-2)$ 的商式與餘式。`.

**Comparison-normalized candidate:** unchanged, with `remainder: [0]`.
**Comparison-normalized oracle:** unchanged, with `remainder: 0`.
Python exact-dictionary comparison therefore returns false; there is no numeric,
Fraction, rounding, or field-order conversion in this oracle.

**Failure stage:** oracle comparison after successful extraction and execution.

**Root cause classification:** `prompt_contract_misunderstanding`.

**Evidence:** `PolynomialOps.div_qr` returned a one-element remainder list, and
the candidate copied it into a contract that explicitly requires a scalar.
Quotient, dividend, divisor, invocation, and mathematical value are otherwise
correct.

**Responsible file/function:** candidate source stored in the JSONL;
production classification is `classify_response` and
`evaluate_polynomial_division`.

**Recommended minimal fix:** in a future generation/prompt repair, unpack the
one-element API remainder before assigning the scalar contract field.  Do not
change the current oracle or smoke record.

**Confidence:** high.

## Task: largest_proper_divisor_reasoning

**Sampled parameters:**
`{"largest_proper_divisors": {"A": 10}, "claims": [{"subject": "A", "candidate_factor": 2, "asks_necessity": true}]}`

**Oracle expected:** `{"claims": [true]}`.  Independently, the smallest prime
factor of 10 is 2, so the oracle's only possible number is `10 * 2 = 20`.
The largest proper divisor of 20 is 10 and 2 divides 20; the claim is true.
The oracle is correct.

**Answer contract / final prompt:** the stored Ab2d prompt embeds the parameters
above and requires a three-key return whose `correct_answer` is
`{"claims": list[bool]}` in frozen claim order.  Raw output has one Python
fence and extraction returned the following material logic.

```python
def generate(level=1, **kwargs):
    claims = [{"asks_necessity": True, "candidate_factor": 2, "subject": "A"}]
    largest_proper_divisors = {"A": 10}
    return {
        "question_text": "已知數 A 的最大真因數為 10。...",
        "correct_answer": {"claims": [False]},
        "oracle_payload": {
            "claims": claims,
            "largest_proper_divisors": largest_proper_divisors,
        },
    }
```

**Candidate intended logic:** it concludes that because 2 is not itself the
largest proper divisor 10, the requested necessity claim is false.

**Candidate actual result / replay returned value:**
`{"claims": [false]}`; replay traceback: none.  The entry point is one
no-argument `generate`; its payload is byte-for-value identical to the frozen
payload.  Its returned question asks whether factor 2 is logically necessary.

**Comparison-normalized candidate:** `{"claims": [false]}`.
**Comparison-normalized oracle:** `{"claims": [true]}`.  Both are matching
bool/list/dict types; no normalization, indexing, or structural coercion occurs.

**Failure stage:** oracle comparison after successful extraction and execution.

**Root cause classification:** `model_logic_error`.

**Evidence:** the candidate conflates “candidate factor is a necessary divisor
of every number compatible with largest proper divisor 10” with “candidate is
itself the largest proper divisor.”  The independent possible-number check is
20, for which 2 is a divisor.

**Responsible file/function:** candidate source stored in the JSONL;
production oracle function `evaluate_largest_proper_divisor`.

**Recommended minimal fix:** future candidate guidance should distinguish
necessity of a factor from equality to the largest proper divisor.  No oracle
change is indicated.

**Confidence:** high.

## Task: rpm_circumference_to_kph

**Sampled parameters:**
`{"circumference_cm": 130, "rpm_symbol": "rpm", "requested_unit": "km/h"}`

**Oracle expected:** `{"coefficient": "39/500", "unit": "km/h"}`.
Independent calculation is `130 cm/rev * 60 rev/h / 100000 cm/km = 7800/100000
= 39/500 km/h`; the oracle and unit conversion are correct.

**Answer contract / final prompt:** the stored Ab2d prompt embeds the parameters
and requires a reduced exact fraction string `coefficient` plus unit exactly
`km/h`.  Raw output has one Python fence and extraction returned:

```python
def generate(level=1, **kwargs):
    circumference_cm = 130
    rpm_symbol = "rpm"
    requested_unit = "km/h"
    from fractions import Fraction
    coefficient_fraction = Fraction(780, 10000)
    reduced_coefficient = coefficient_fraction.reduce()
    if reduced_coefficient.denominator == 1:
        coefficient_str = str(reduced_coefficient.numerator)
    else:
        coefficient_str = f"{reduced_coefficient.numerator}/{reduced_coefficient.denominator}"
    return {
        "question_text": f"Calculate the linear speed in km/h for 1 {rpm_symbol} given a wheel circumference of {circumference_cm} cm.",
        "correct_answer": {"coefficient": coefficient_str, "unit": "km/h"},
        "oracle_payload": {"circumference_cm": 130, "requested_unit": "km/h", "rpm_symbol": "rpm"},
    }
```

**Candidate intended logic:** compute `780/10000`, reduce it, and format the
fraction with `km/h`.  Its arithmetic target is correct.

**Candidate actual result / replay returned value:** no return value.  Replay
traceback and production failure detail are both
`AttributeError: 'Fraction' object has no attribute 'reduce'`.  The entry point
is correctly named and invoked with no arguments; it fails before constructing
the answer or returning a payload.

**Comparison-normalized candidate:** unavailable because execution failed.
**Comparison-normalized oracle:** `{"coefficient": "39/500", "unit": "km/h"}`.

**Failure stage:** candidate execution, before schema or oracle comparison.

**Root cause classification:** `model_logic_error`.

**Evidence:** Python's standard `fractions.Fraction` normalizes during
construction and has no `.reduce()` method.  The production namespace and
argument invocation are correct; no external runtime dependency is missing.

**Responsible file/function:** candidate source stored in the JSONL;
production executor `_execute_generate` faithfully reports the candidate
exception.

**Recommended minimal fix:** future candidate code should use the constructed
`Fraction` directly (already reduced) rather than call `.reduce()`.  No unit,
oracle, or environment repair is warranted.

**Confidence:** high.

## Task: alternating_training_progression_threshold

**Sampled parameters:**
`{"track_length_m": 400, "initial_first_day_laps": 7, "same_week_increment_laps": 1, "threshold_km": 5, "specified_week": 3, "specified_day": "Thursday", "day_labels": ["Monday", "Thursday"]}`

**Oracle expected:**
`{"specified_session_laps": 10, "first_exceed_week": 6, "first_exceed_day": "Thursday"}`.
Independent calculation uses the oracle's session rule
`laps = 7 + 1 * (week_index + day_index)`: sessions are 7, 8, 8, 9, 9, 10,
10, 11, 11, 12, 12, 13.  The strict threshold is `laps > 5000/400 = 12.5`,
so the first crossing is week 6 Thursday (13 laps); week 3 Thursday is 10.
The strict `>` comparison, one-based week, and day index are correct.

**Answer contract / final prompt:** the stored Ab2d prompt embeds these
parameters and requires the three specified answer keys.  Raw output has one
Python fence and extraction returned a candidate that computes
`initial + (specified_week - 1) * increment` for both weekly days and scans
only `range(1, specified_week + 1)` for the threshold.

```python
def generate(level=1, **kwargs):
    track_length_m, initial_first_day_laps, same_week_increment_laps = 400, 7, 1
    threshold_km, specified_week, specified_day = 5, 3, "Thursday"
    day_labels = ["Monday", "Thursday"]
    day_to_laps = {
        "Monday": initial_first_day_laps + (specified_week - 1) * same_week_increment_laps,
        "Thursday": initial_first_day_laps + (specified_week - 1) * same_week_increment_laps,
    }
    specified_session_laps = day_to_laps[specified_day]
    cumulative_distance = 0.0
    for w in range(1, specified_week + 1):
        for day in day_labels:
            laps_in_day = initial_first_day_laps + (w - 1) * same_week_increment_laps
            cumulative_distance += laps_in_day * (track_length_m / 1000.0)
            if cumulative_distance > threshold_km:
                first_exceed_week, first_exceed_day = w, day
                break
        if cumulative_distance > threshold_km:
            break
    return {
        "question_text": "在一個訓練計畫中，每週訓練兩天：星期一與星期四。...",
        "correct_answer": {"specified_session_laps": specified_session_laps, "first_exceed_week": first_exceed_week, "first_exceed_day": first_exceed_day},
        "oracle_payload": {"track_length_m": 400, "initial_first_day_laps": 7, "same_week_increment_laps": 1, "threshold_km": 5, "specified_week": 3, "specified_day": "Thursday", "day_labels": ["Monday", "Thursday"]},
    }
```

**Candidate intended logic:** increase laps once per week for both training
days and stop the threshold search at the requested week.

**Candidate actual result / replay returned value:**
`{"specified_session_laps": 9, "first_exceed_week": 1,
"first_exceed_day": "Thursday"}`; replay traceback: none.  The candidate
entry point and no-argument invocation are correct, and it returns the frozen
payload exactly.  Its question text uses the same task constants.

**Comparison-normalized candidate:** unchanged integer/string dictionary above.
**Comparison-normalized oracle:** unchanged integer/string dictionary with
`10`, week `6`, and `Thursday`.  There is no float-vs-Fraction comparison:
candidate floats are internal only; submitted fields are integers/strings.

**Failure stage:** oracle comparison after successful extraction and execution.

**Root cause classification:** `model_logic_error`.

**Evidence:** candidate code omits the day index in both the requested-session
calculation and schedule, and artificially stops threshold search after week 3.
The oracle follows the frozen two-day sequence through the first strict
crossing.

**Responsible file/function:** candidate source stored in the JSONL;
production oracle function `evaluate_alternating_sequence_threshold`.

**Recommended minimal fix:** future candidate guidance should state the exact
per-session progression and require scanning until the first strict crossing,
not merely through `specified_week`.  No sampler/oracle repair is indicated.

**Confidence:** high.

## Root-cause summary

| task_family | model_logic | extraction | invocation | oracle | comparison | root_cause |
|---|---:|---:|---:|---:|---:|---|
| polynomial_division_quotient_remainder | no | no | no | no | no | prompt_contract_misunderstanding |
| largest_proper_divisor_reasoning | yes | no | no | no | no | model_logic_error |
| rpm_circumference_to_kph | yes | no | no | no | not reached | model_logic_error |
| alternating_training_progression_threshold | yes | no | no | no | no | model_logic_error |

There is no evidence of an instance mismatch, extraction error, candidate
invocation error, oracle error, or comparison-normalization error in the four
records.  The polynomial failure is a shape mismatch at comparison caused by
candidate misunderstanding of the scalar remainder contract, not a defect in
the comparison itself.
