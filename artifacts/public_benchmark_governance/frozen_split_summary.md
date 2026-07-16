# Frozen Public Benchmark Split

- Generated: 2026-07-16 (Asia/Taipei)
- Starting Git commit: `23a430538f44fbe8e57a025a19ca0f49778e1ab1`
- Attestation date: `2026-07-16`
- Attestation scope: `project-process contamination`
- Split assignment status: `frozen`

## Source evidence

| Repository path | SHA-256 |
|---|---|
| `artifacts/public_benchmark_governance/contamination_manifest.csv` | `d19a136ab6c58c5f52e803b6351290cc628db73ff202e1546e7eea931bf18857` |
| `artifacts/public_benchmark_governance/split_proposal.csv` | `6d55ad54c8784fc4134e011d61f3060b7c69b6468615d370039b41f13f7bf618` |
| `artifacts/public_benchmark_governance/researcher_attestation.md` | `acb447c631131d4d360227184aaf3ac2c8ec4d81a27a2026e7e1e07321b2109f` |
| `data/humaneval_plus/dataset_manifest.json` | `6e3dc590c17a2987e4c3718eb1f6436526d03fb9c020c538252608fa92964dd8` |
| `data/mbpp_plus/dataset_manifest.json` | `502e946fb273751805ec74472856a8d2e6cd732368547c9f45e2310495b831be` |

## Frozen counts

| Measure | Count |
|---|---:|
| Total unique tasks | 542 |
| Frozen assignments | 542 |
| Confirmatory eligible | 168 |
| HumanEval+ confirmatory | 108 |
| MBPP+ confirmatory | 60 |
| Non-confirmatory | 374 |

## Roles preserved from proposal

| Proposed role | Count |
|---|---:|
| `excluded_historical` | 56 |
| `external_confirmatory_candidate` | 108 |
| `historical_development_pool` | 116 |
| `validation` | 20 |
| `internal_confirmatory_candidate` | 60 |
| `sealed_reserve` | 182 |

Only the 108 HumanEval+ external candidates and 60 MBPP+ internal candidates are `confirmatory_eligible=true`; validation, reserve, historical development, and excluded tasks remain false.

The original pre-attestation `pending/false` value is preserved as `source_contamination_status`. Selection hashes, ranks, and proposed roles are unchanged from `split_proposal.csv`.

## Scope and limitations

- The attestation establishes no known project-process exposure for the 168 confirmatory tasks.
- It cannot establish whether model pretraining encountered these public benchmarks.
- The original contamination manifest and split proposal remain immutable source evidence and are not overwritten.
