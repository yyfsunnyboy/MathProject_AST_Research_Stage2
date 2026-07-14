# Ab2d-local prompt design — 2026-07-14

## Treatment distinction

Ab2d-full remains the existing skill-markdown treatment.  This experiment adds
an isolated, deterministic Ab2d-local treatment; it is not wired into routing,
any diagnostic runner, or production generation.

The local prompt is assembled exactly as:

```text
CORE_SCAFFOLD + TASK_LOCAL_PRIMITIVE + TASK_CONTRACT + FROZEN_PARAMETERS
```

It intentionally excludes the domain catalogue, sub-skill graph, generator
priority, LiveShow material, examples, and unrelated family guidance.

## Core scaffold

The shared scaffold requires one complete Python `generate(level=1, **kwargs)`
implementation, the exact three-key return schema, exact frozen
`oracle_payload`, no unsafe or external operations, exact arithmetic where the
contract requires it, no extra keys, and no self-retry instruction.

## Task-local primitive registry

| Family | Local primitive focus |
|---|---|
| `polynomial_division_quotient_remainder` | `PolynomialOps.div_qr`, highest-degree-first coefficients, `x-r -> [1, -r]`, scalar linear remainder, exact arithmetic. |
| `largest_proper_divisor_reasoning` | `n = L * p` with `p` the smallest prime factor; return frozen-order Boolean necessity claims. |
| `rpm_circumference_to_kph` | `Fraction`, 60 rotations/hour, cm-to-km conversion, reduced fraction and exact `km/h`. |
| `alternating_training_progression_threshold` | Frozen alternating recurrence, odd/even or equivalent recurrence, exact strict first threshold crossing. |

Each primitive is task-family specific and does not import a full domain
catalogue or a frozen answer.

## Size comparison

The metadata is local and deterministic: character count, UTF-8 byte count,
and whitespace-separated approximate wordpiece count.  It is explicitly not a
provider tokenizer result.

| Family | Local chars | Full chars | Local/full chars |
|---|---:|---:|---:|
| polynomial | 2763 | 11817 | 23.38% |
| largest proper divisor | 2677 | 7343 | 36.46% |
| rpm | 2599 | 8814 | 29.49% |
| alternating | 3325 | 7845 | 42.38% |

All local prompts are below 50% of the corresponding existing Ab2d-full prompt
by both character and UTF-8 byte count.  This is a prompt-length treatment for
future 4B/8B capacity diagnostics, not a claim about their performance.

## Boundaries

This change does not alter Ab2d-full, task definitions, frozen seeds or
parameters, task contracts, samplers, oracles, evaluator semantics, Healer,
provider wrapper, model configuration, retries, timeouts, dependencies, or any
existing diagnostic JSONL, summary, or forensic record.  No model/API request
was made.
