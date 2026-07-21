# G2_module 27格雙人獨立review操作說明

1. Reviewer A與Reviewer B分別取得自己的blank worksheet；兩份表的evidence相同，但在B完成前不得向B顯示A的任何decision。
2. `review_packets.csv`只含公開contract、source/AST最小結構證據與固定identity，不含hidden input、expected/actual、exception message或traceback。
3. `provisional_recommendations.csv`是AI輔助建議，固定標示 `AI_ASSISTED_PROVISIONAL_NOT_FORMAL_ADJUDICATION`；不得預填或複製到reviewer worksheet。
4. 25格top-level assert須逐格判定：公開assert是否精確、required function是否另有semantic問題、assert是否單獨阻斷G2及failure chain是否多層。不得整批貼label。
5. Reviewer須親自查看evidence references後填入reviewer_id與UTC時間；空白不得由script或AI補值。
6. 兩位review完成後才建立比較；有任一欄不一致即填入disagreement表並由第三位adjudicator處理。
7. top-level assert移除僅是候選假說。本輪不得轉換、執行或以移除後結果判定安全性。
8. 本批不執行模型、EvalPlus、diagnostics、Healer或validation。
