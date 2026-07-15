# Official replay reconciliation note

Date reviewed: 2026-07-15 Asia/Taipei

## Authoritative result

- Workbook: `isolated_results/exp1_pass_at_1_mbpp.xlsx`
- Workbook SHA256: `95ba84a6cd5ded07d85ed0fb445f35262ae7e5fc36a38eacf31c97906710e1da`
- Last write: `2026-07-15T20:30:38.3941238+08:00`
- Environment recorded per row: EvalPlus 0.3.1, Python 3.14.4, Linux/WSL2
- Dataset version recorded by replay manifest: MBPP+ v0.2.0

The pre-existing `preflight.txt` and `evalplus_import_error.txt` are retained as records of an earlier native-Windows blocked attempt. They do not describe the later WSL result workbook.

## Aggregate semantics

`run_eval.py::classify_eval_outcome` returns aggregate pass only for `base=pass` and `plus=pass`. Any base or plus failure produces aggregate fail. This explains Mbpp/410 Raw: its workbook row is aggregate fail and explicitly says `base=pass,plus=fail`, identical to the historical reviewed row.

## Source and hash checks

- All replay and historical rows use `sample_idx=0`.
- Historical and replay Raw Mbpp/410 use normalized-text SHA256 `65d5a9fcec96b2edb4dc1c7f0e9c280d025258e1b678df984deec3455a91d534`.
- Historical and replay use EvalPlus 0.3.1.
- Current isolated and G: official files may have CRLF byte hashes different from the manifest. After universal-newline CRLF-to-LF normalization, all nine replay source hashes match exactly.
- The official eval path reads with `Path.read_text(encoding="utf-8")`, which applies universal-newline normalization before passing code to EvalPlus.

## Residual and unresolved findings

- Mbpp/279 Candidate reaches official tests but fails base and plus. The retained last definition has a semantic formula defect: `1 + 24*n` does not invert its own `n*(3*n-1)` generator, whose discriminant is `1 + 12*n`. No reference solution was used for this derivation.
- Mbpp/255 historical Raw reports base pass / plus fail, while replay Raw reports base pass / plus pass. Task, sample, normalized source hash, and EvalPlus version match. Historical dataset version/hash and per-test detail are unavailable; Python/WSL runtime versions differ. Cause remains an unresolved provenance discrepancy.
- Mbpp/255 Candidate versus Original Ab3 is still an official full rescue within one replay environment.
- Mbpp/410 Candidate versus Original Ab3 is an official base-regression recovery.

No result was changed to match an expectation, and none of these three-task results is included in the original pass@1.
