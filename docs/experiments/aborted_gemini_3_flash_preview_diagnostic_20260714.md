# Aborted Gemini 3 Flash Preview diagnostic — 2026-07-14

- run_status = `aborted_engineering_run`
- exclude_from_analysis = `true`
- rows_recorded = `1`
- model = `gemini-3-flash-preview`
- abort_reason = `unexplained_child_process_and_stalled_runner`
- exact root cause = `undetermined`

The preserved single row is archived at
`docs/experiments/results/aborted_gemini_3_flash_preview_diagnostic_20260714.jsonl`.
It must not be included in any subsequent Gemini 3.5 diagnostic. The observed
child process does not establish Windows subprocess re-entry as the cause.
