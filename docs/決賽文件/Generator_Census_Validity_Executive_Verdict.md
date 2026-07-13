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

Get-ChildItem : 拒絕存取路徑 'C:\Projects\MathProject_AST_Research\.pytest_cache'。
位於 線路:2 字元:78
+ ... erdict.md'; Get-ChildItem -Recurse -File -Include 'test_generator_fai ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (C:\Projects\Mat...h\.pytest_cache:String) [Get-ChildItem], Unauthoriz 
   edAccessException
    + FullyQualifiedErrorId : DirUnauthorizedAccessError,Microsoft.PowerShell.Commands.GetChildItemCommand
