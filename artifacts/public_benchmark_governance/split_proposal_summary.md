# Public Benchmark Deterministic Split Proposal

- Generated: 2026-07-16 (Asia/Taipei)
- Starting Git commit: `e6201938b824f96429fdbf35db02fad2291dc024`
- Split version: `public_benchmark_split_proposal_v1`
- Salt: `2026-07-16|e6201938b824f96429fdbf35db02fad2291dc024`
- Status: proposal only; no formal confirmatory set is frozen

## Deterministic selection

Each task is ordered by the full ascending SHA-256 of:

`split_version|dataset|dataset_version|task_id|salt`

No prompt, model output, answer, test, Python built-in hash, or manual task selection is used.

## Source files

| Repository path | SHA-256 |
|---|---|
| `artifacts/public_benchmark_governance/contamination_manifest.csv` | `d19a136ab6c58c5f52e803b6351290cc628db73ff202e1546e7eea931bf18857` |
| `data/humaneval_plus/dataset_manifest.json` | `6e3dc590c17a2987e4c3718eb1f6436526d03fb9c020c538252608fa92964dd8` |
| `data/mbpp_plus/dataset_manifest.json` | `502e946fb273751805ec74472856a8d2e6cd732368547c9f45e2310495b831be` |

## Proposed roles

| Proposed role | Count |
|---|---:|
| `excluded_historical` | 56 |
| `external_confirmatory_candidate` | 108 |
| `historical_development_pool` | 116 |
| `validation` | 20 |
| `internal_confirmatory_candidate` | 60 |
| `sealed_reserve` | 182 |

The historical MBPP+ development pool contains 116 tasks; its first 20 by selection hash are marked `active_development_generation_subset=true`.

All 108 HumanEval+ external candidates and 60 MBPP+ internal candidates have `formal_status=awaiting_manual_attestation`. None is frozen or formally confirmatory.

## Governance limits

- This artifact is a deterministic grouping proposal, not a frozen development/validation/confirmatory split.
- No row has `formal_status=frozen` or `confirmatory_eligible=true`.
- Manual attestation remains required before either candidate pool can receive any formal status.
