# Healer 候選完成實作並等待功能驗證：development 階段性小結

> **截至2026年7月18日，本階段完成的是Healer候選實作、離線安全稽核與2×2 development qualification協定凍結；正式功能資格測試尚未執行。**

## 一、研究目標

本研究的 development 階段聚焦於以下比較與概念區分：

- 比較 P0 與 P1 Scaffold。
- 比較 H0 與 H1 evaluator-blind Healer。
- 嚴格區分 Observed、Pipeline、Scaffold 與 Healer，避免將不同層次的結果或處理機制混為一談。

## 二、已完成的 development 資料

- discovery：20 題 × 5 seeds。
- expansion：40 題 × 5 seeds。
- 合計：60 題、300 個 task-seed identities。
- P0 與 Scaffold-like 合計產生 600 個 generated programs。

## 三、Scaffold 結果

- v0 明顯改善直接可評估性。
- Candidate A 的 Pipeline pass 由 38/200 提升至 53/200。
- 配對變化為 30 rescues、15 regressions。
- exact McNemar p = 0.035697803555194696。
- strict Python-only 為 89%，未達 90% format gate。
- 因此，Candidate A 不能升格為 official v1。

## 四、Healer 候選

- 唯一實作規則為 entry-point unique arity-compatible alias。
- 僅追加名稱 alias，不修改 function body。
- 整個機制維持 evaluator-blind。
- 設有嚴格 guards 與 abstention。
- P0 轉換 39 格，Scaffold-like 轉換 2 格，合計 41 格。
- 尚未執行功能評估，因此目前尚不知道 rescue、regression 與 net effect。

## 五、已凍結但尚未執行的 2×2 qualification

- 既有 600 programs 的 H0/H1 帳已納入協定。
- Candidate B 使用新的 28 題。
- P0 與 Candidate B 各規劃 140 次 generations。
- 合計為 280 次 planned generations，以及 560 個 evaluation accounts。
- Candidate B 仍不是 official P1。
- 模型生成與 EvalPlus 均尚未執行。

## 六、目前可以主張

- Scaffold 改善格式與直接可評估性。
- Candidate A 在 40 題 development expansion 中出現功能正確性改善。
- entry-point alias 已有靜態安全候選與可執行實作。

## 七、目前不能主張

- 不能主張 Healer 已產生真正 rescue。
- 不能主張 Healer 沒有 regression。
- 不能主張 Candidate B 優於 P0。
- 不能主張 final P1 或 final Healer 已凍結。
- 不能主張結果可以泛化到 validation 或外部資料集。

## 八、下一步

1. 先完成既有 600 programs 中 41 個轉換 cell 的 H0 vs H1 功能驗證。
2. 再決定是否授權 Candidate B 的 280 次 generation。
3. 通過 development gates 後，才進入 validation。

本文件僅記錄上述 development checkpoint；本輪不執行正式功能資格測試、不啟動新 generation，也不進入下一個 Milestone。
