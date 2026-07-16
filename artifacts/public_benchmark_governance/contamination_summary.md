# Public Benchmark Contamination Summary

- Generated: 2026-07-16 (Asia/Taipei)
- Starting Git commit: `7efd2542261e8d5c3e3c0bac2dd3011b7b4002e7`
- Milestone: 0B complete MBPP+ manifest and data-governance inventory

## Dataset versions

| Dataset | Version evidence | Manifest status |
|---|---|---|
| HumanEval+ | release `v0.1.10`; EvalPlus `0.3.1` | complete, 164 tasks |
| MBPP+ | release `v0.2.0`; EvalPlus `0.3.1` | complete, 378 tasks |

## Repository evidence and SHA-256

| Repository path | SHA-256 |
|---|---|
| `data/humaneval_plus/tasks.jsonl` | `7c6181cc059d3b28bce462fc90e761b2ebf26cb296da419bd3be38cb6d6e0a46` |
| `data/humaneval_plus/dataset_manifest.json` | `6e3dc590c17a2987e4c3718eb1f6436526d03fb9c020c538252608fa92964dd8` |
| `agent_tools/finals_rebuild/ollama_generation_runner.py` | `c12dbc2c0f4b05ac7fb97e6b40980253759a84a4adf1788ef521dd0cfeb94a86` |
| `artifacts/fail_to_fail_forensics/qwen8b_forensic_reviewed.csv` | `6df8acbc0a7304008e24e25cad1c73baf46f409e4fcd83afca0580d2c63262ac` |
| `artifacts/fail_to_fail_forensics/import_preservation_validation/candidate_manifest.csv` | `fc0d939c95a2eac346cb3dc3f244aced1eddef617d51c80c0418ee535b37b82b` |
| `artifacts/fail_to_fail_forensics/xor_safetyloop_validation/candidate_manifest.csv` | `042fdee9ef35395cf6fe7356d7313c0a3819ab9647a6f217b666ff98e96fc326` |
| `artifacts/fail_to_fail_forensics/healer_vnext_evalplus_replay/replay_manifest.csv` | `5b80912ad587698beca35d6ea00cfb571342ec100a1df2e6a257f4765bdb7754` |
| `artifacts/fail_to_fail_forensics/healer_vnext_public_benchmark_final_summary_zh.md` | `5c6ad7fe01534a8fc381c71514163b22ced13cd5590887d93d91f081d39bcc7f` |
| `data/mbpp_plus/tasks.jsonl` | `b816022b8b587047cb1d275417a96acb009de328684e5914e7ac010c9d8c6f3c` |
| `data/mbpp_plus/dataset_manifest.json` | `502e946fb273751805ec74472856a8d2e6cd732368547c9f45e2310495b831be` |

## HumanEval+ counts

| Measure | Count |
|---|---:|
| Total tasks | 164 |
| Engineering smoke, official first-N | 20 |
| Forensic reviewed unique | 38 |
| Smoke/forensic overlap | 2 |
| Excluded union | 56 |
| Unreviewed candidate | 108 |

Overlap IDs: `HumanEval/10`, `HumanEval/19`.

The 108 remaining HumanEval+ tasks are `unreviewed_candidate` with `confirmatory_eligible=pending`; they are not a formal confirmatory set.

## MBPP+ counts

| Measure | Count |
|---|---:|
| Forensic reviewed unique | 116 |
| Total tasks | 378 |
| Excluded union | 116 |
| Unreviewed candidate | 262 |

The 116 reviewed MBPP+ rows are individually reviewed failure-census sources and have `confirmatory_eligible=false`. The remaining 262 rows are `unreviewed_candidate` with `confirmatory_eligible=pending`, not a formal confirmatory set.

## Contamination status counts

| Status | Count |
|---|---:|
| `excluded_rule_development` | 16 |
| `excluded_failure_census` | 138 |
| `excluded_individual_review` | 0 |
| `excluded_engineering_smoke` | 18 |
| `pending_generated_or_aggregate_only` | 0 |
| `unreviewed_candidate` | 370 |
| `evidence_ambiguous` | 0 |

## Governance statements

- This milestone does not establish a formal development, validation, or confirmatory split.
- `unreviewed_candidate` does not mean confirmatory or clean.
- `generated_only` is not automatically treated as individual contamination.
- Formal task eligibility must be decided by the next milestone.
- No row in this manifest has `confirmatory_eligible=true`.

## Limitations

- The complete MBPP+ task list records only model-visible fields; official tests, canonical solutions, contracts, and expected outputs remain outside the repository export.
- Repository evidence cannot prove that an apparently unreviewed task was never generated or viewed elsewhere; lower-level history is therefore `unknown` for unreviewed candidates.
- Rule-development attribution is limited to task IDs directly present in the structured candidate/replay manifests listed above.
- The inventory does not inspect new model outputs, task solutions, cloud-drive history, or formal EvalPlus results.
