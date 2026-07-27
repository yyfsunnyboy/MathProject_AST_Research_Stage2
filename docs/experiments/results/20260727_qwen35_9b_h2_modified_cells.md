# qwen3.5:9b H2 Modified Cells: Full Case Ledger

Generated from read-only analysis of `artifacts/public_benchmark_governance/qwen35_9b_h2_full_replay_v1/` and `artifacts/public_benchmark_governance/qwen35_9b_h2_full_evalplus_v1/` journals. No re-execution performed.

Total Raw/H2 pairs: 1084. Modified (transformed=true): **137**. Rule: `module_assert_entrypoint_selftest_quarantine_v0` (source: `agent_tools/finals_rebuild/mbpp_h2_module_assert_quarantine.py`).

All 137 modified cells follow the identical transform: a top-level `assert ...` self-test statement is relocated behind an `if __name__ == "__main__":` guard. Function body segments are verified unchanged via AST segment-hash comparison (`function_segments_unchanged` guard) before the rule commits to `transformed=true` -- this is a structural guarantee from the frozen rule code, not an inference.

## Case Table

| # | Dataset | Task ID | Treatment | Raw Pass | H2 Pass | Outcome | Trigger Rule | Diff (removed/added lines) | Modification Level | Final EvalPlus base/plus (H2) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MBPP | Mbpp/100 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 2 | MBPP | Mbpp/102 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 3 | MBPP | Mbpp/106 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 4 | MBPP | Mbpp/11 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 5 | MBPP | Mbpp/116 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 6 | MBPP | Mbpp/118 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 7 | MBPP | Mbpp/123 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 8 | MBPP | Mbpp/127 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 9 | MBPP | Mbpp/127 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 10 | MBPP | Mbpp/129 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 11 | MBPP | Mbpp/130 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 12 | MBPP | Mbpp/133 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 13 | MBPP | Mbpp/135 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 14 | MBPP | Mbpp/161 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 15 | MBPP | Mbpp/162 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 16 | MBPP | Mbpp/166 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 17 | MBPP | Mbpp/170 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 18 | MBPP | Mbpp/171 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 19 | MBPP | Mbpp/18 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 20 | MBPP | Mbpp/2 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 21 | MBPP | Mbpp/20 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 22 | MBPP | Mbpp/227 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 23 | MBPP | Mbpp/230 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 24 | MBPP | Mbpp/234 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 25 | MBPP | Mbpp/235 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 26 | MBPP | Mbpp/252 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 27 | MBPP | Mbpp/257 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 28 | MBPP | Mbpp/257 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 29 | MBPP | Mbpp/259 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -3/+4 | statement-level (module assert relocation only) | base=True, plus=True |
| 30 | MBPP | Mbpp/266 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 31 | MBPP | Mbpp/269 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 32 | MBPP | Mbpp/269 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 33 | MBPP | Mbpp/270 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 34 | MBPP | Mbpp/271 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 35 | MBPP | Mbpp/272 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 36 | MBPP | Mbpp/274 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 37 | MBPP | Mbpp/280 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 38 | MBPP | Mbpp/287 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 39 | MBPP | Mbpp/292 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 40 | MBPP | Mbpp/308 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 41 | MBPP | Mbpp/309 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 42 | MBPP | Mbpp/309 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 43 | MBPP | Mbpp/310 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 44 | MBPP | Mbpp/389 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 45 | MBPP | Mbpp/397 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 46 | MBPP | Mbpp/404 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 47 | MBPP | Mbpp/404 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 48 | MBPP | Mbpp/405 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 49 | MBPP | Mbpp/410 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 50 | MBPP | Mbpp/413 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -3/+4 | statement-level (module assert relocation only) | base=True, plus=True |
| 51 | MBPP | Mbpp/413 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 52 | MBPP | Mbpp/419 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 53 | MBPP | Mbpp/420 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 54 | MBPP | Mbpp/428 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 55 | MBPP | Mbpp/429 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 56 | MBPP | Mbpp/432 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 57 | MBPP | Mbpp/433 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 58 | MBPP | Mbpp/436 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 59 | MBPP | Mbpp/437 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 60 | MBPP | Mbpp/447 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 61 | MBPP | Mbpp/451 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 62 | MBPP | Mbpp/457 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 63 | MBPP | Mbpp/458 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 64 | MBPP | Mbpp/468 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 65 | MBPP | Mbpp/470 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 66 | MBPP | Mbpp/476 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 67 | MBPP | Mbpp/555 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 68 | MBPP | Mbpp/556 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 69 | MBPP | Mbpp/556 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 70 | MBPP | Mbpp/557 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 71 | MBPP | Mbpp/558 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 72 | MBPP | Mbpp/56 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 73 | MBPP | Mbpp/560 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 74 | MBPP | Mbpp/562 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 75 | MBPP | Mbpp/565 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 76 | MBPP | Mbpp/565 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 77 | MBPP | Mbpp/568 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 78 | MBPP | Mbpp/573 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 79 | MBPP | Mbpp/579 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 80 | MBPP | Mbpp/594 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 81 | MBPP | Mbpp/597 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 82 | MBPP | Mbpp/598 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 83 | MBPP | Mbpp/604 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 84 | MBPP | Mbpp/605 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 85 | MBPP | Mbpp/619 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 86 | MBPP | Mbpp/62 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 87 | MBPP | Mbpp/620 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 88 | MBPP | Mbpp/628 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 89 | MBPP | Mbpp/629 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 90 | MBPP | Mbpp/63 | ab2g | fail | pass | verified_rescue | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 91 | MBPP | Mbpp/630 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -3/+4 | statement-level (module assert relocation only) | base=True, plus=False |
| 92 | MBPP | Mbpp/64 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -2/+3 | statement-level (module assert relocation only) | base=True, plus=True |
| 93 | MBPP | Mbpp/641 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 94 | MBPP | Mbpp/65 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 95 | MBPP | Mbpp/66 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 96 | MBPP | Mbpp/71 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=True |
| 97 | MBPP | Mbpp/723 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 98 | MBPP | Mbpp/724 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 99 | MBPP | Mbpp/726 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 100 | MBPP | Mbpp/731 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 101 | MBPP | Mbpp/735 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 102 | MBPP | Mbpp/735 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 103 | MBPP | Mbpp/736 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 104 | MBPP | Mbpp/740 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 105 | MBPP | Mbpp/742 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 106 | MBPP | Mbpp/743 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 107 | MBPP | Mbpp/75 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 108 | MBPP | Mbpp/750 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 109 | MBPP | Mbpp/751 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 110 | MBPP | Mbpp/752 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 111 | MBPP | Mbpp/755 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 112 | MBPP | Mbpp/763 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 113 | MBPP | Mbpp/764 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 114 | MBPP | Mbpp/766 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -9/+10 | statement-level (module assert relocation only) | base=True, plus=True |
| 115 | MBPP | Mbpp/771 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 116 | MBPP | Mbpp/772 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 117 | MBPP | Mbpp/775 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 118 | MBPP | Mbpp/777 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 119 | MBPP | Mbpp/780 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 120 | MBPP | Mbpp/782 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 121 | MBPP | Mbpp/786 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 122 | MBPP | Mbpp/786 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 123 | MBPP | Mbpp/787 | ab2g | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 124 | MBPP | Mbpp/791 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 125 | MBPP | Mbpp/792 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 126 | MBPP | Mbpp/796 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 127 | MBPP | Mbpp/797 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 128 | MBPP | Mbpp/798 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 129 | MBPP | Mbpp/799 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 130 | MBPP | Mbpp/8 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 131 | MBPP | Mbpp/80 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 132 | MBPP | Mbpp/803 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 133 | MBPP | Mbpp/804 | ab2g | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 134 | MBPP | Mbpp/806 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=False |
| 135 | MBPP | Mbpp/84 | ab1 | fail | fail | modified_but_still_failed | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=False, plus=False |
| 136 | MBPP | Mbpp/86 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |
| 137 | MBPP | Mbpp/91 | ab1 | pass | pass | modified_and_preserved_pass | module_assert_entrypoint_selftest_quarantine_v0 | -1/+2 | statement-level (module assert relocation only) | base=True, plus=True |

Note: the frozen journal schema records only boolean `evalplus_base_pass` / `evalplus_plus_pass` / `evalplus_final_pass`. It does not distinguish "module import crash" from "ran but assertion failed" from "timeout" -- so a per-cell crash-vs-logic-fail classification is **N/A** (not recoverable from the existing schema without re-execution, which this round does not perform).

## Unique Verified Rescue

- **task_id**: `Mbpp/63`
- **treatment**: `ab2g`
- **dataset**: MBPP
- **entry_point**: `max_difference`
- **rule**: `module_assert_entrypoint_selftest_quarantine_v0`
- **Raw EvalPlus**: base=False, plus=False, final=False
- **H2 EvalPlus**: base=True, plus=True, final=True

**Why it succeeded**: independently executing the Raw candidate's `max_difference` on its own self-test input `[(3, 5), (1, 7), (10, 3), (1, 2)]` returns `7` (the `(10, 3)` pair has the largest `abs(a-b)`), but the candidate's own module-level assert checks `== 6` -- the self-test is simply wrong, and in Raw this assert executes unconditionally at module import time, raising `AssertionError` before the harness can ever call the function, which is why Raw scores fail/fail on both EvalPlus base and plus. The H2 journal shows this exact assert relocated behind `if __name__ == "__main__":` (confirmed by the rule's `function_segments_unchanged` guard reporting the function body untouched), so on import the module loads cleanly, the buggy self-check never runs, and the function -- which is actually correct against the official hidden tests -- is scored and passes both base and plus.

```python
# Raw output_source (Mbpp/63, ab2g)
def max_difference(pairs):
    if len(pairs) < 2:
        return None
    
    min_val = float('inf')
    max_diff = 0
    
    for a, b in pairs:
        diff = abs(a - b)
        if diff > max_diff:
            max_diff = diff
        
        if a < min_val:
            min_val = a
            
    return max_diff

assert max_difference([(3, 5), (1, 7), (10, 3), (1, 2)]) == 6
```

```python
# H2 output_source (Mbpp/63, ab2g) -- assert relocated, function body unchanged (verified via AST segment-hash guard)
def max_difference(pairs):
    if len(pairs) < 2:
        return None
    
    min_val = float('inf')
    max_diff = 0
    
    for a, b in pairs:
        diff = abs(a - b)
        if diff > max_diff:
            max_diff = diff
        
        if a < min_val:
            min_val = a
            
    return max_diff

if __name__ == "__main__":
    assert max_difference([(3, 5), (1, 7), (10, 3), (1, 2)]) == 6
```

Function body (`max_difference`) is byte-identical between Raw and H2, per the rule's own `function_segments_unchanged` guard (recorded True in the underlying decision path for every `transformed=true` cell, including this one). The rescue is attributable to quarantining a module-level self-test assertion that previously executed at import time -- not to any change in the candidate's function logic.
