# Candidate Healer / Healer-vNext import-preservation counterfactual replay

## Outcome

The reviewed forensic set contains nine eligible `wrong_transformation` cases caused by stripping an import whose binding remains used. All nine imports are Python standard-library imports with low import-time risk, unambiguous AST loads, and no intervening rebinding.

Candidate replay structurally rescues 9/9 cases: every output parses, retains its entry point, retains the original referenced import, and has a valid post-import load. Every Candidate-vs-Original-Ab3 diff only restores an import that existed in raw source.

No official pass@1 or runtime rescue is claimed. Formal generated cases were not executed. Three synthetic runtime controls execute successfully, and all safety/gate controls pass.

## Conservative Gate

The gate preserves only aliases from a direct-scope absolute import when the module is in Python's standard-library inventory, the module is not explicitly blocked, and a later AST load resolves to that binding before any rebinding.

- `import module [as alias]` requires a later `alias.attr` load.
- `from module import name [as alias]` requires a later alias `Name` load.
- Strings and comments do not count.
- Star imports, relative imports, unknown third-party modules, dangerous modules, and ambiguous rebinding fail closed.
- Mixed import statements retain only necessary safe aliases.
- The Candidate never synthesizes an import absent from raw source.

The existing safe math-module behavior remains, except star and relative imports now fail closed as required. Regex cleanup, duplicate cleanup, XOR rewriting, safety-loop rewriting, and all other Healer rules are unchanged.

## Residual Failures

Seven cases already failed base and plus tests in raw. Import preservation removes the additional unresolved-name failure layer but cannot repair their pre-existing solution errors.

Mbpp/255 and Mbpp/410 passed base and failed plus in raw, then failed both after Original Ab3. The raw official baseline supports an inferred structural removal of the base regression, while the plus failure remains. No single-case EvalPlus run was performed, so this is not reported as an official runtime result.

## Regression Validation

Targeted validation passed 17/17 tests. It covers module and symbol imports, aliases, unused imports, string-only references, local rebinding, dangerous modules, star imports, relative imports, unknown third-party modules, mixed aliases, entry-point behavior, and existing AST safe-import safeguards.

An attempted broader `radical_auto_test.py` run produced 43 passes and 62 failures because Flask is absent from this environment; one additional existing fallback expectation is also unrelated to this gate. That suite is recorded as unavailable as a clean regression baseline and is not counted against the targeted result.

No regression was detected in the targeted import-removal scope. Official Ab3 files and official Excel files were not modified, and no model, full benchmark, or EvalPlus run was performed.
