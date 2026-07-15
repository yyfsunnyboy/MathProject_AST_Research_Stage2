# Fail-to-Fail Forensics

Extractor output for Ab2g fail -> Ab3 fail paired cases.

Included strategies: raw Ab2g and healed/original Ab3 rows where both pass values are false.
Pairing key: dataset + normalized model + normalized task_id + sample_idx.
Missing or duplicate artifacts are marked as missing or ambiguous; the extractor does not infer replacements.

## Census

| dataset | model | total | complete | missing | ambiguous |
|---|---:|---:|---:|---:|---:|
| humaneval | google_gemini-3-flash-preview | 7 | 0 | 7 | 0 |
| humaneval | qwen3-8b | 38 | 38 | 0 | 0 |
| mbpp | google_gemini-3-flash-preview | 76 | 0 | 76 | 0 |
| mbpp | qwen3-8b | 116 | 116 | 0 | 0 |

## Files

- `pairing_manifest.jsonl` and `pairing_manifest.csv`: case-level manifest.
- `cell_census.csv`: counts by dataset/model cell and pairing status.
- `unpaired_or_ambiguous_cases.csv`: cases needing artifact follow-up.
- `schema_inventory.json`: observed source headers and resolved logical columns.
- `diffs/`: normalized text and AST-signature unified diffs when available.

Total cases: 237
