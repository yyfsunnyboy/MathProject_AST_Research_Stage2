# MBPP+ Scaffold v1 候選設計與錯誤歸因分析（Milestone 2C）

## 範圍與證據界線

本輪只重讀既有 P0、P1 與 Milestone 2B development artifacts；沒有模型呼叫、程式生成、EvalPlus 重跑、Healer 建置或執行，也沒有讀取 validation、confirmatory 或 sealed reserve。Pipeline correction 不是 Healer。本報告是候選設計與探索性證據整理，不是 Scaffold v1 有效性的證明。

100 組 `task_id + seed` 身分已重新驗證：無重複、無缺漏；四組為 rescue 17、regression 17、common pass 13、persistent failure 53，與 Milestone 2B 一致。

## 六個直接回答

1. **v0 確定解決了什麼？** 它確定改善直接可評估性：code fences 96→0、fence 外文字 79→0、多段程式 25→0、extraction failure 21→0、raw compile pass 0→94；missing entry-point failures 17→3 是強關聯但不能拆解到單一指令。它沒有改善 Pipeline-corrected 總正確率（30/100→30/100）。
2. **17 個 Pipeline regressions 能否歸因於 Scaffold？** 不能。逐格分類為 `{"model_sampling_variation": 3, "scaffold_plausibly_related": 14}`；其中 repeated within-task direction 只支持低信心的 `scaffold_plausibly_related` 推論，沒有因果識別；方向混合／孤立者只作低信心 sampling variation 推論。
3. **v1 最需要處理什麼？** 保留已證實的純 Python／無 fence／正確 entry-point 輸出契約，同時縮短重複與未被單獨支持的禁令，降低對語意解題的注意力干擾風險。
4. **哪些問題不應交給 Scaffold？** unknown evaluator failures、需要 assertion／oracle 才能辨識的功能錯誤、runtime 語意與資源行為不應由 Scaffold 猜修。
5. **現在是否足以凍結 v1？** 不足：尚不凍結，只保留候選。現有 20 題是 pilot，Pipeline 淨增益為 0，且 line-level 與 semantic causality 未識別。
6. **下一輪先凍結 v1 還是先擴充 development？** 先預註冊 development expansion 與候選比較規則，再從 historical development pool 新增 40 題形成 60 題；本輪不選題、不讀題、不建 split。取得更廣 development evidence 後再決定凍結哪個 v1。validation／confirmatory／sealed reserve 維持封存。

## Rescue 與 regression 歸因

17 個 rescues：`{"compile_or_entry_improvement": 7, "format_compliance_rescue": 5, "insufficient_evidence": 5}`。只有格式或 compile／entry 的可觀察障礙消失時才使用 mechanistic label；5 個 P0 unknown→P1 pass 保持證據不足。任何 rescue 都不是 Healer 效果。

17 個 regressions 的 P1 輸出皆需依保存的 compile、entry、extraction 與 evaluator 診斷判讀。generic evaluator failure 不被重編為 functional failure；同 task 多 seed 的一致方向只是 scaffold-related plausibility，不是因果證明。逐格直接證據與信心見 `milestone_2c_cell_evidence.csv`。

## 剩餘問題的治理分流

- 適合 Scaffold：明確的輸出格式與 requested entry-point 契約。
- 可能適合 evaluator-blind Healer：可由 parser／compiler 直接看見的 syntax defect；仍須另案預註冊且不得使用 evaluator feedback。
- 需要 oracle／語意資訊：已被可靠診斷的功能、runtime、import/name 或資源錯誤；本批 generic unknown 不能擅自放入此類。
- 證據不足：P1 的 generic unknown evaluator failures；不得硬分配給 Healer。

## v0 指令審查與 v1 候選

逐條審查見 `scaffold_v0_instruction_review.csv`。最強直接證據支持 no-fence 與 output-only；entry-point 改善是 aggregate association；imports 與禁止 assertions/tests/prints 等沒有各自可識別的直接證據。因 v0 是 bundled treatment，所有 line-level 因果主張均受限。

最多三個 exact UTF-8 候選見 `scaffold_v1_candidates.json`。推薦最保守的 Candidate A：保留格式、signature、imports 與相同 appended prompt composition，只壓縮重複禁令。這是供下一個獨立、已預註冊 Milestone 評估的候選，不建立 v1 run directory，也不凍結或執行。

## Development expansion 建議

把目前 20 題明確標為 pilot。下一輪先預註冊：historical development pool 的資格規則、盲選程序、排除規則、40 題新增數量、固定 seeds、主次指標、paired analysis、停止規則與候選選擇門檻；之後才建立 60 題 development set。不得用 validation、confirmatory 或 sealed reserve 補足題數。
