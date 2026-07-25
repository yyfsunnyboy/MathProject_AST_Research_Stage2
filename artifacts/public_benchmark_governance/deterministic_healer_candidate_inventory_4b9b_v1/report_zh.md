# 4B／9B 下一條 deterministic Healer 只讀盤點

## 結論

372 個既有 development 錯誤格（4B 148、9B 224）完成逐格靜態盤點。沒有新的 unique entry-point mismatch；唯一安全映射屬於既有 H1，多候選一律 abstain。沒有 uniquely inferable missing standard-library import。Packaging／Markdown／extractor 問題歸 Scaffold 或 Pipeline；truncation、演算法、邊界與無法唯一定位的語意錯誤均不 eligible。

最多推薦一條下一階段 development candidate：`top_level_literal_only_demo_print_quarantine_v0`。它只應進入另一次預登錄與 static audit，本輪未實作、未凍結、未驗證。

## 重複證據

- `Mbpp/138` seed `33`，cell `01b6bac38cef8f198113a5cd475e8be41beccd60d7c559172443b76df714e34c`，source SHA-256 `5ac277bdc6b75e21aa18043943c5f72d3c2ebdb67c21a4b75b6f5a1d405433fc`
- `Mbpp/787` seed `33`，cell `1ed09edb92c4da77d9ccb4eac0e420c2cbd4319a9d8a55e3340ea9f1a20544d8`，source SHA-256 `93e763a6916038e0e019b7d602e32aa1daccaa75365b3a053b1dc89ad7425b1b`

兩格都有 required entry point、可解析 AST、頂層 public self-test `Assert` 後緊接 `print`；`print` 只含 literal，或以 literal 參數呼叫 required entry point，回傳值未被使用，且沒有其他未分類頂層呼叫。`Assert` 本身仍屬 H2，候選只能處理剩餘 print side effect，不得合併或修改 H2。

## 安全界線

若 required entry point 缺失、存在多個相容函式、print 非相鄰 self-test、參數含非 literal data-flow、結果被使用、存在其他頂層呼叫或需依測試結果判斷，全部 abstain。特別是 `Mbpp/765` 有兩個相容函式，已排除。

本盤點沒有查看 hidden tests 或 canonical solution；錯誤狀態只用來固定使用者要求的既有 error cohort，不作規則選擇證據。模型、candidate import／execution、EvalPlus、H1/H2 修改及規則實作皆為 0。
