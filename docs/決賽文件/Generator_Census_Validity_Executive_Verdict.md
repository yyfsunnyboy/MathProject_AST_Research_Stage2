# Generator Census Validity Executive Verdict

## Decision

The initial 30-case generator failure census is invalid for Math Track inference:
invalid_sampling_implementation. Its sampling implementation selected only
applications_of_derivatives from a 125-file, three-domain eligible frame.

## Sampling evidence

- applications_of_derivatives: 35
- four_arithmetic_operations_of_integers: 45
- four_arithmetic_operations_of_numbers: 45

The replacement is cross_domain_calibration_census: ten deterministic, unique
cases per domain, 30 total, seed 20260713. It is not the formal Junior High
four-family census.

## Safety attribution

The raw evaluator safety policy is unchanged. Rejections caused by injected
utilities containing import os are safe_harness_incompatibility;
model-generated input() is intrinsic_generator_risk.

## Tier 1 adjudication

The prior five preliminary candidates are catastrophic truncations. They are
incomplete_generation / catastrophic_truncation, are not deterministically
repairable, and are not Tier 1 candidates. Therefore true Tier 1 candidates
are 0/5.

## Treatment

Retain the original census only as single_domain_sampling_bug_forensics:
sampling-bug evidence, safety-harness calibration, and truncation examples.
It must not support aggregate Math Track effectiveness claims.

## Sampling implementation status

A production deterministic stratified sampler now generates the calibration
manifest from the eligible source frame: three required domains, ten cases per
domain, fixed seed 20260713, and fail-fast availability validation.

## Cross-domain calibration census result

Baseline commit: 15ad47fa. The calibration manifest
tests/finals_rebuild/fixtures/generator_failure_census_manifest.json was
evaluated into artifacts/finals_rebuild/cross_domain_generator_census.json.
All three domains contributed ten cases. The result contains six passed,
four parse failures, eighteen safety rejections, and two execution failures.
All parse failures were adjudicated as catastrophic truncation; true Tier 1
candidates are zero, so a Healer repair pilot does not proceed.

## Safety harness contract correction

The evaluator now scans model-generated source for safety before the trusted
injected-utilities block. Full source remains available for parse, load, and
execution. The safety blacklist is unchanged. Corrected census artifacts record
raw and corrected outcomes plus safety provenance and attribution.

## Execution failure adjudication

The two corrected execution-failure rows are census_011 and census_013, both
from four_arithmetic_operations_of_integers, qwen3-14b, Ab1. Each fails at the
entry-point stage with GenerateEntryPointMissing: generate is not defined.
This is an intrinsic generator failure, not a legacy-harness incompatibility.
There is no existing deterministic Core repair rule, so neither is a true Tier
1 candidate. With zero true candidates across the calibration census, the
decision remains do_not_proceed_to_healer_pilot.

## Corpus provenance correction

The 125 files under experiments/results are a legacy mixed-model corpus with
historical filename tags, not verified current-runtime Qwen3 4B or 8B output.
The corrected 30-case census is therefore evaluator and harness calibration
only. Its 22/30 pass rate, failure counts, and zero true Tier 1 candidates do
not support current 4B inference, current 8B inference, or a 4B-versus-8B
comparison.

Future generation provenance requires model tag, digest, size, architecture,
parameters, quantization, runtime/version, timestamp, hardware, prompt
condition, task, seed, source commit, and generation timing/token metadata.

Get-ChildItem : 拒絕存取路徑 'C:\Projects\MathProject_AST_Research\.pytest_cache'。
位於 線路:2 字元:78
+ ... erdict.md'; Get-ChildItem -Recurse -File -Include 'test_generator_fai ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Projects\Mat...h\.pytest_cache:String) [Get-ChildItem], Unauthoriz 
   edAccessException
    + FullyQualifiedErrorId : DirUnauthorizedAccessError,Microsoft.PowerShell.Commands.GetChildItemCommand
