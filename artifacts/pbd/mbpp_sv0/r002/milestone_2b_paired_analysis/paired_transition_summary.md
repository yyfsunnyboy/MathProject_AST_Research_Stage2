# Milestone 2B paired transition summary

> MBPP+ active development exploratory analysis only; no external-generalization claim.

## Observed

| P0 \ P1 | fail | pass |
|---|---:|---:|
| fail | 70 | 30 |
| pass | 0 | 0 |

- Paired rescues: 30
- Paired regressions: 0
- Net change: +30/100 (+30.0 percentage points)
- Exact McNemar two-sided p: `1.86265e-09`
- Discordant superiority: `1`; exact 95% CI `0.884297`–`1`
- Matched-pairs odds ratio: `∞`; exact 95% CI `7.6428`–`∞`

## Pipeline-corrected

| P0 \ P1 | fail | pass |
|---|---:|---:|
| fail | 53 | 17 |
| pass | 17 | 13 |

- Paired rescues: 17
- Paired regressions: 17
- Net change: +0/100 (+0.0 percentage points)
- Exact McNemar two-sided p: `1`
- Discordant superiority: `0.5`; exact 95% CI `0.324269`–`0.675731`
- Matched-pairs odds ratio: `1`; exact 95% CI `0.479879`–`2.08386`

## Per-task five-seed pass counts

| task_id | Observed P0→P1 (Δ) | Pipeline P0→P1 (Δ) |
|---|---:|---:|
| Mbpp/633 | 0→0 (+0) | 2→0 (-2) |
| Mbpp/769 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/453 | 0→5 (+5) | 0→5 (+5) |
| Mbpp/259 | 0→1 (+1) | 1→1 (+0) |
| Mbpp/739 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/124 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/72 | 0→2 (+2) | 3→2 (-1) |
| Mbpp/792 | 0→0 (+0) | 3→0 (-3) |
| Mbpp/435 | 0→1 (+1) | 0→1 (+1) |
| Mbpp/597 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/732 | 0→5 (+5) | 3→5 (+2) |
| Mbpp/721 | 0→5 (+5) | 1→5 (+4) |
| Mbpp/765 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/777 | 0→0 (+0) | 2→0 (-2) |
| Mbpp/473 | 0→5 (+5) | 4→5 (+1) |
| Mbpp/420 | 0→5 (+5) | 3→5 (+2) |
| Mbpp/742 | 0→1 (+1) | 5→1 (-4) |
| Mbpp/279 | 0→0 (+0) | 3→0 (-3) |
| Mbpp/125 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/603 | 0→0 (+0) | 0→0 (+0) |
