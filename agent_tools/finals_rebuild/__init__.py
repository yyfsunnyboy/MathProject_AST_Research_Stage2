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
  evaluation        – EvaluationResult schema (Commit 4A: static-only —
                      syntax + contract inspection; execution/test/MCRI
                      fields are explicit not-evaluated markers).
  static_evaluator  – produces EvaluationResult via ast.parse() only; no
                      import/exec/subprocess against artifact code.
  pipeline          – paired ablation pipeline runner (no model calls).
"""
