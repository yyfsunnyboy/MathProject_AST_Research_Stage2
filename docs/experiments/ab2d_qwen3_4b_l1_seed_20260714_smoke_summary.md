# Ab2d 4B L1 Minimal Smoke — 2026-07-14

**This is a minimal engineering smoke test, not a formal experiment. No effect
inference is drawn and no comparison to Ab1/Ab2g is made.**

## 1. Git Commit and Model

- branch: `main`
- HEAD (start): `27f872e38bfc2588554a4efa3b388884d6e49629`
- Ollama server version: `0.31.2`
- Model: `qwen3:4b-instruct-2507-q4_K_M` (digest `0edcdef34593`, from `ALLOWED_MODELS`)

## 2. Exact Commands

```
ollama list                       # existence check only, no pull
curl http://localhost:11434/api/tags      # server reachability check
curl http://localhost:11434/api/version   # runtime_version evidence
python <scratch>/run_ab2d_smoke.py        # one-off invocation of existing production functions:
                                           #   sample_task_parameters, build_ab2d_prompt,
                                           #   classify_response, call_ollama_chat
```

No project source or test files were executed as a runner CLI: `math_boundary_pilot.run_pilot()`
enforces a fixed `MODEL_TAGS = (qwen3:4b-instruct-2507-q4_K_M, qwen3:8b)` pair and refuses a
single-model call. Per the do-not-modify boundary, its underlying already-exposed functions
were invoked directly instead of altering that guard.

## 3. Task Family Selection (explicit assumption — please confirm)

The instructions named `polynomial_division_quotient_remainder` and `rpm_circumference_to_kph`
as expected members, but also scoped this smoke to "the four completed 115 CAP
computation-only task families" (§3 heading). Those two identifiers are the **older CE115
pilot** families (temporary-family-mapped, context-bearing for RPM). The four families that
literally match "已完成的 115 會考純計算 task families" are the ones built in the immediately
preceding round and documented in `docs/experiments/ce115_computation_task_design.md`
(Q3/Q5/Q7/Q9, computation-only, no context). This run used those four; if the older pilot pair
was intended instead, say so and a follow-up smoke can target them.

| # | task_family (skill_id) | task_id | oracle_type |
|---|---|---|---|
| 1 | `radical_simplification` | `ce115_calc_radical_simplification_l1` | `radical_simplification` |
| 2 | `exact_rational_expression` | `ce115_calc_exact_rational_expression_l1` | `exact_rational_expression` |
| 3 | `polynomial_division_general` | `ce115_calc_polynomial_division_l1` | `polynomial_division_general` |
| 4 | `polynomial_factor_roots` | `ce115_calc_polynomial_factor_roots_l1` | `polynomial_factor_roots` |

Fixed seed: `20260714`. Condition: `Ab2d` only. One generation per task, no retry, no Healer.

## 4. Per-Task Results

| task_family | generation | extraction | evaluable | oracle_pass | failure_category |
|---|---|---|---|---|---|
| radical_simplification | done (HTTP 400 from Ollama on this attempt) | N/A | NO | NO | `infrastructure_failure` |
| exact_rational_expression | done | extracted, `generate()` ran | YES | NO | `answer_incorrect` |
| polynomial_division_general | done | extracted, `generate()` ran | YES | NO | `runtime_failure` (`NameError: name 'PolynomialOps' is not defined`) |
| polynomial_factor_roots | done | extracted, `generate()` ran | YES | YES | none — passed |

## 5. End-to-End Stage Success

- L1 sampler → task instance: **OK** (4/4, deterministic under seed 20260714)
- Ab2d prompt construction (`build_ab2d_prompt`): **OK** (4/4)
- Ollama qwen3:4b generation, first attempt only: **3/4 returned content**, 1/4 returned
  HTTP 400 from the Ollama server on this single attempt (no retry performed)
- Extraction / evaluability: **3/4 evaluable** (the HTTP 400 case has no content to extract)
- Independent oracle evaluation: **ran for all 3 evaluable cases**
- Result serialization: **OK**, one JSONL record per task, all fields captured (`null` where
  Ollama did not return a metric for the failed HTTP call)

## 6. Blockers / Anomalies (recorded, not fixed this round)

- **Task 1 (radical_simplification): HTTP 400 Bad Request** from the Ollama `/api/chat` call
  on the single attempt made. Not retried, per instructions. Root cause not investigated.
- **Task 3 (polynomial_division_general): `NameError: PolynomialOps is not defined`** at
  runtime inside the sandboxed `generate()` — the model's code called `PolynomialOps.div_qr(...)`
  as instructed by the Ab2d reusable API block, but the raw sandbox executor used by
  `classify_response._execute_generate` does not inject the `PolynomialOps` runtime class into
  the candidate's execution namespace (unlike `core.code_generator._inject_domain_libs`, which
  is a separate, non-pilot code path). This is an existing gap between the Ab2d prompt's API
  promise and the pilot evaluator's sandbox capabilities — not something this smoke round
  modifies.
- **Task 2 (exact_rational_expression): answer_incorrect** — the model returned a well-formed,
  schema-valid answer that the oracle recomputed as `1452/5` but which did not match; this is
  an ordinary model-quality miss on the first (and only) attempt, not a pipeline defect.

## 7. Output Files

- `artifacts/finals_rebuild/math_boundary_pilot/ab2d_qwen3_4b_l1_seed_20260714_smoke.jsonl`
  (machine-readable, 4 records)
- `docs/experiments/ab2d_qwen3_4b_l1_seed_20260714_smoke_summary.md` (this file)

No existing snapshot, experiment result, or report was overwritten.
