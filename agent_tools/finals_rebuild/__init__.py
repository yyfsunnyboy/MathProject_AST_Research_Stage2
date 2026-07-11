"""
finals_rebuild – immutable paired artifact schema for ablation pipeline.

Two metadata layers:
  PairMetadata  – one record per experimental sample (study/model/skill/index).
  RunMetadata   – one record per treatment execution (ab1/ab2/ab3_core/ab3_full).

Modules:
  artifacts   – schema, ID builders, validators, immutable write helpers.
  extraction  – canonical code extraction from raw model responses.
  pipeline    – paired ablation pipeline runner (no model calls).
"""
