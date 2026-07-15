# Candidate Healer / Healer-vNext Official EvalPlus Counterfactual Replay

## Scope and provenance

The isolated WSL/Linux replay completed for exactly Mbpp/255, Mbpp/279, and Mbpp/410 under Raw, Original Ab3, and Candidate Healer-vNext. The result workbook is `isolated_results/exp1_pass_at_1_mbpp.xlsx` (SHA256 `95ba84a6cd5ded07d85ed0fb445f35262ae7e5fc36a38eacf31c97906710e1da`). The recorded environment is EvalPlus 0.3.1, Python 3.14.4, Linux/WSL2; the replay manifest records MBPP+ v0.2.0.

These isolated results are counterfactual evidence only. They are not merged into the historical official workbook or original pass@1.

The runner's `passed` column is aggregate: it is true only when both official base and plus statuses are `pass`. Therefore `base=pass,plus=fail` is displayed as aggregate `fail`.

## Nine official outcomes

| Task | Condition | Base | Plus | Aggregate | Error / worker error | SHA256 |
|---|---|---|---|---|---|---|
| Mbpp/255 | Raw | pass | pass | pass | none | `6fe16f25b1ad17653705af5fb2583e1b682a61b6f17f393b6af9141d3d708c5f` |
| Mbpp/255 | Original Ab3 | fail | fail | fail | `base=fail,plus=fail` | `7df412ff3b6a37b5786051ef9b06dd23b99839d1682d6ecea6d5087f7b589d7b` |
| Mbpp/255 | Candidate Healer-vNext | pass | pass | pass | none | `fc39f33436cecca7a9b31e5a7f7a22606a6ce0ebdc52e77b8cba17fa47da8852` |
| Mbpp/279 | Raw | not run | not run | worker_error | duplicate `is_num_decagonal` entry point (2 definitions), rejected before official tests | `99cd93576f0d52ba046dc7d13edc8d00d002758fdd13701af5de1f556cadeff4` |
| Mbpp/279 | Original Ab3 | fail | fail | fail | `base=fail,plus=fail` | `ee50da9fb9035bcd62f28e7578dba0a7fa8ec16ef548778743699bbfa7cbea49` |
| Mbpp/279 | Candidate Healer-vNext | fail | fail | fail | wrong-output assertions in base and plus | `c620f5a9a76b16303dd2090a1fcaa0a89e07ce054f021351a12c06bcea2fac08` |
| Mbpp/410 | Raw | pass | fail | fail | `base=pass,plus=fail` | `65d5a9fcec96b2edb4dc1c7f0e9c280d025258e1b678df984deec3455a91d534` |
| Mbpp/410 | Original Ab3 | fail | fail | fail | `base=fail,plus=fail` | `3a446dfa1bfe8122ca7569d2a827a36d95d6545a5616d621205427cd8c74b4e4` |
| Mbpp/410 | Candidate Healer-vNext | pass | fail | fail | `base=pass,plus=fail` | `dfc5304573e4a81a9235d93641df86ebc099cea9f1b1139fe89c8323ac3310a5` |

The origin and evaluated source paths for every row are recorded in `evalplus_results.json` and `replay_manifest.csv`.

## Mbpp/255: official full rescue

Original Ab3 removed the still-used `combinations_with_replacement` import and fails both official layers. Candidate preserves the import and passes both official base and plus tests. The final Candidate classification is **official full rescue**, not merely base-regression recovery.

Replay Raw also passes both layers, while the historical reviewed Ab2g row reports base pass / plus fail. The two records have the same task ID, sample index, normalized source SHA256, and EvalPlus 0.3.1. Historical dataset version/hash and per-test details are absent, while Python and WSL runtime versions differ. The Raw-baseline difference is therefore an **unresolved provenance discrepancy**; it does not alter Candidate-versus-Original classification within this replay.

## Mbpp/279: residual semantic failure

Raw never reaches EvalPlus because the official runner rejects two module-level `is_num_decagonal` entry-point definitions. Candidate keep-LAST reduces the entry point to one and preserves Python's actual last-definition binding, so structural execution and runtime semantics are recovered.

Candidate nevertheless fails both official base and plus layers. Its retained function uses `(1 + sqrt(1 + 24*n)) / 6`. Algebraically inverting the same sample's `nth_decagonal_number(k) = k*(3*k-1)` requires discriminant `1 + 12*n`, so the retained self-correction is still semantically wrong. This conclusion is derived from the submitted sample itself, without a reference solution. Final classification: **structural/runtime-semantics recovery only**.

## Mbpp/410: aggregate reconciliation

There is no result conflict. Replay Raw is `base=pass,plus=fail`, exactly matching the historical reviewed forensic row. It appears as `passed=false` only because runner aggregate semantics require both layers to pass.

The reconciliation checks match on task ID `Mbpp/410`, sample index 0, normalized source SHA256 `65d5a9f...d534`, and EvalPlus 0.3.1. Replay records MBPP+ v0.2.0; the historical workbook does not record dataset version, but no dataset-version hypothesis is needed because the decomposed statuses already agree. Candidate restores base pass from Original Ab3's base failure while plus remains failing. Final classification: **official base-regression recovery**.

## Classification summary

| Task | Candidate classification |
|---|---|
| Mbpp/255 | official full rescue |
| Mbpp/279 | structural/runtime-semantics recovery only |
| Mbpp/410 | official base-regression recovery |

No Candidate is classified as `no recovery`. The only `unresolved provenance discrepancy` is the Mbpp/255 Raw historical-plus result, not a Candidate result.

## SHA256 reconciliation

The result workbook copies normalized-text SHA256 values from the replay manifest. Eight current files use CRLF while the manifest was generated from LF text; Python `Path.read_text()` performs universal-newline normalization before evaluation. After CRLF-to-LF normalization, all nine hashes exactly match the manifest and workbook. The G: official eval-ready files show the same content and line-ending relationship. No semantic source drift was found.

The earlier `logs/preflight.txt` and `logs/evalplus_import_error.txt` describe the blocked native-Windows attempt, not the later completed WSL replay. See `logs/reconciliation_note.md` for the audit trail.
