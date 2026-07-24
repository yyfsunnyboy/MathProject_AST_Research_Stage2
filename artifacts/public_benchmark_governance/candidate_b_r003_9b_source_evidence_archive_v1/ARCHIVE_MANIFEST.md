# Candidate B r003 9B Source Evidence Archive

## Purpose

封存支撐 9B Candidate B r003 **198 格逐程式深入分析**所需、本機已存在但先前未被 Git 追蹤的正式原始證據。本輪只做證據補齊，不重新生成、不重新評測、不重新分類、不修改候選程式。

## 9B data source

正式 run 目錄（development-only replay）：

`artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/`

引用鏈依據：

- `candidate_b_r003_taxonomy_v31_complete_198cell_closure_v1/complete_cumulative_frozen_identity_ledger.csv`（198 cell identities）
- `candidate_b_r003_taxonomy_v3_formal_classification_preparation_v1/classification_preparation.csv`
- Conditional23 prereg／diagnostics 對 `h0_h1_accounts.jsonl` 的正式路徑引用
- 既有分析腳本釘選的 SHA（raw／accounts）

## Expected scope

- Expected cells（taxonomy 198）：**198**
- Underlying Candidate_B generation cells in run：300（含 pass＋fail）
- 分析對象：ledger／prep 的 198 失敗格；證據檔保留完整 r003 正式產物以便 identity 追溯

## Archived files and roles

| Relative path | Role | Bytes | SHA-256 |
|---|---|---:|---|
| `.../r003/raw_generations.jsonl` | 300 格 raw response 原文與 generation metadata | 1231474 | `3d8295ff5e7260d733d8f68736a792afa79501d70ca8bde8d4dd88c1b2b002b3` |
| `.../r003/h0_h1_accounts.jsonl` | Candidate_B H0/H1 逐格 accounts（含 program_id／generation_id／seed／task） | 1212361 | `b1313615bf41840bc1c45c36d2b8ac9b544f37fb5bb801c104aad1657ca2c2ec` |
| `.../r003/pipeline_normalized.jsonl` | pipeline-corrected／extracted candidate source | 482556 | `70de0164f85b231f2cbd6ab0505bb391fa422c3064ac1ebef38977a4028aef8b` |
| `.../r003/frozen_manifest.json` | r003 frozen run manifest | 7100 | `e8d0f8e9198848e8708d910f6c859622c272de850a2b1045d62993c114c98fbd` |
| `.../r003/model_provenance.json` | 模型 provenance | 1041 | `ddc1eb489e48de69af9ad6404a51c5dfd9b1b54e36beb715b2fd12cda347c777` |
| `.../r003/materialization_manifest.json` | materialization 完成紀錄 | 547 | `d78ba6b371dbbe8e69e3f83d29fcbfc0c126d1239912970f7ecdefab7a092b92` |

路徑前綴：`artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/`

## Integrity check (198 taxonomy cells)

| Metric | Count |
|---|---:|
| expected | 198 |
| unique `cell_identity_sha256` | 198 |
| duplicate identity | 0 |
| matched to Candidate_B_H0 accounts via `program_id` | 198 |
| raw available（non-empty `raw_response`） | 198 |
| extracted available（`extraction_status=extracted` 且 source 非空） | 198 |
| ambiguous／extraction failure | 0 |
| missing | 0 |
| ledger `source_sha256` vs pipeline／account SHA mismatch | 0 |

Notes:

- 未納入 `j/` 下 300 個 per-cell journal：內容已彙整於 `raw_generations.jsonl`；且部分路徑長度在 Windows 上不易穩定操作。逐格分析以 jsonl 為準。
- raw／accounts SHA 與既有腳本釘選值一致。
- 本輪掃描未發現 API key／token／private key 等憑證字樣。

## Explicit non-actions

本輪：**零模型呼叫、零候選程式執行、零重新評測、零證據內容改寫**。未修改 taxonomy／eligibility／Conditional23 結論或研究報告數字。未納入任何 4B 檔案。
