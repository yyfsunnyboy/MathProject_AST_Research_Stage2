# Milestone 1C: MBPP+ development failure census

## Integrity result

- Generation cells: 100 (20 task IDs × seeds 11, 22, 33, 44, 55)
- Observed: 0 pass / 100 fail
- Pipeline-corrected: 30 pass / 70 fail
- Pipeline-corrected failed tasks: 19
- Expansion triggered: false
- Retry, duplicate, missing, and out-of-scope cells: none
- Model/protocol: qwen3.5:9b, frozen digest and sampling settings verified, `think=false`

`evaluated 200/200` means that the same 100 generation cells were evaluated under the Observed and Pipeline-corrected accounts. It does not mean 200 generations occurred.

## Failure categories

| Category | Cells |
|---|---:|
| `extraction_or_format_failure` | 21 |
| `syntax_failure` | 6 |
| `missing_or_wrong_entry_point` | 17 |
| `import_or_name_failure` | 0 |
| `runtime_exception` | 0 |
| `timeout_or_resource_failure` | 0 |
| `functional_test_failure` | 0 |
| `unknown` | 26 |

## Candidate counts

- Scaffold candidates: 21
- Healer candidates: 23
- Unknown/manual review: 26

Candidate labels are triage hypotheses only; they do not establish safe repair rules. Functional test failures are never automatically labeled Healer candidates. The 30 Pipeline rescues are Pipeline correction outcomes and are excluded from Healer effectiveness.

Rows classified as `unknown` remain manual-review-required because the saved evaluator artifact collapses assertion failures and runtime exceptions into a generic failure outcome. No hidden tests, expected outputs, canonical solutions, or sealed model outputs were read or stored.

Pipeline correction and Healer accounting remain completely separate. No Scaffold or Healer was modified or built, and no generation or EvalPlus execution was performed.
