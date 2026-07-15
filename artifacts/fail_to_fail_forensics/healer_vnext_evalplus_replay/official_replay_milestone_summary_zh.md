# Healer-vNext 三題官方 EvalPlus Replay 里程碑摘要

- 日期：2026-07-15（Asia/Taipei）
- 範圍：Mbpp/255、Mbpp/279、Mbpp/410 × Raw / Original Ab3 / Candidate Healer-vNext
- 環境：WSL/Linux、EvalPlus 0.3.1、Python 3.14.4、MBPP+ v0.2.0
- 結果簿：`isolated_results/exp1_pass_at_1_mbpp.xlsx`

本摘要為對照實驗（counterfactual）證據封存，**不回填**歷史官方 workbook，**不納入**原始 pass@1，**不宣稱**整體 benchmark 提升。

## 官方結果與分類

| 題目 | Raw | Original Ab3 | Candidate Healer-vNext | 官方分類 |
|---|---|---|---|---|
| Mbpp/255 | base/plus = pass/pass | fail/fail | pass/pass | **official full rescue** |
| Mbpp/279 | worker_error（entry_point 重複 2 次） | fail/fail | fail/fail | **structural/runtime-semantics recovery only** |
| Mbpp/410 | base/plus = pass/fail（聚合 fail） | fail/fail | pass/fail（聚合 fail） | **official base-regression recovery** |

說明：runner 的聚合 `passed` 僅在 base 與 plus 皆 pass 時為真；因此 `base=pass,plus=fail` 顯示為聚合 fail。

## 必保留結論

1. **Mbpp/255**：相對同一 replay 內的 Original Ab3，Candidate 為 official full rescue（保留仍被使用的 import）。同時保留 **historical Raw provenance discrepancy**：歷史 Ab2g 記為 pass/fail，本 replay Raw 為 pass/pass；task/sample/正規化 SHA256/EvalPlus 版本一致，歷史 dataset version/hash 與逐測細節缺失，執行環境不同，原因列為 **unresolved provenance discrepancy**。此差異不改變 Candidate-versus-Original 的 full rescue 判定。
2. **Mbpp/279**：**不得宣稱 official rescue / official full rescue**。keep-LAST 恢復結構執行與 Python 後定義語意，但保留定義的公式仍錯（`1+24n` 無法反演同檔 `n*(3*n-1)` 所需的 `1+12n`），官方 base/plus 仍 fail。
3. **Mbpp/410**：Candidate 相對 Original Ab3 恢復 official base pass，plus 仍 fail → official base-regression recovery。Raw 與歷史 reviewed 列一致（pass/fail）。
4. **不回填原始 pass@1**；**不宣稱整體 benchmark 提升**。

## 證據檔案

- `evalplus_results.json`：九列官方結果、分類、對帳與 provenance
- `replay_report.md`：英文完整報告
- `logs/reconciliation_note.md`：對帳審計
- `isolated_results/exp1_pass_at_1_mbpp.xlsx`：官方 runner 產出
- `isolated_outputs/`、`diffs/`、`replay_manifest.csv`：樣本與對照差

原生 Windows 的 `logs/preflight.txt` / `logs/evalplus_import_error.txt` 僅保留作為早期 blocked 嘗試紀錄，不是本次 WSL 官方結果來源。
