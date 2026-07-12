"""
finals_rebuild – immutable paired artifact schema for ablation pipeline.

Two metadata layers:
  PairMetadata  – one record per experimental sample (study/model/skill/index).
  RunMetadata   – one record per treatment execution (ab1/ab2/ab3_core/ab3_full).

Modules:
  artifacts         – schema, ID builders, validators, immutable write
                      helpers.
  extraction        – canonical code extraction from raw model responses.
  trace             – TreatmentTrace / TraceStep schema for Core/Spec
                      adapters.
  core_adapter      – Core Adapter rule registry (generic Python; one
                      safe_format rule enabled since Commit 3B-1).
  spec_adapter      – Spec Adapter rule registry and K12-math
                      applicability boundary (all rules disabled).
  evaluation         – EvaluationResult schema (Commit 4A static +
                       Commit 4B execution + Commit 4C tests; MCRI fields
                       are explicit not-evaluated markers this commit).
  static_evaluator   – produces EvaluationResult via ast.parse() only; no
                       import/exec/subprocess against artifact code.
  execution_evaluator – bounded-subprocess execution (Commit 4B); AST
                       preflight denylist; NOT a security sandbox.
  execution_worker   – disposable subprocess entry point for execution
                       (never imported by the main pipeline process).
  test_contract      – TestCase / TestSuite fixture schema (Commit 4C);
                       JSON-compatible values only, no code/callables.
  test_evaluator     – runs a TestSuite against one treatment's code in
                       one bounded subprocess; reuses execution_evaluator's
                       denylist and minimal-env helpers.
  test_worker        – disposable subprocess entry point that calls only
                       the fixture-named top-level function per case.
  pipeline           – paired ablation pipeline runner (no model calls).
"""
