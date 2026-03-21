# SHOWREEL_LOGIC (2026-03-21)

本文件是給 AI/工程師接手用的「今日修復總結 + 可複用規則」。
目標：穩定 `live_show.html` 的「生成 / 下一題」循環，並可遷移到下一單元「多項式四則運算」。

---

## 1) 今日異動重點（已完成）

### A. 修正 `下一題` 行為（核心）
問題：
- 使用者在 `live_show.html` 按「下一題」時，理論要重跑 `generate()` 產生同題型新亂數題。
- 實際曾出現：無反應、固定同一題、答案空白、偶發 500。

修正：
- 在 Radical fallback 路徑，Ab3 落地腳本不再優先固定題面。
- 改為優先落地「可執行的隨機同構 generator 腳本」，確保 `run_generated_code` 每次會重新抽數值。
- 落地前強制檢查：腳本必須包含 `def generate(` 且可 `compile(...)`。

主檔：
- `core/routes/live_show_pipeline.py`

### B. 修正答案空白 / 0（answer sync）
問題：
- 題目有出來但 `answer=''` 或 `answer='0'`（明顯不合理）。

修正：
- 加強 `answer` 回填：
  - Ab2/Ab3 若空答案，從 `question_text` 重算。
  - Radical 題若答案為 `0/0.0` 且題目有 `\sqrt`/乘除，視為可疑值，強制再重算。
- Ab2 回填後，若最終輸出來源是 Ab2，會同步更新 top-level `output.answer`。

主檔：
- `core/routes/live_show.py`
- `core/routes/live_show_pipeline.py`

### C. 強化 `_recompute_correct_answer_from_question`
問題：
- 部分題面是雙跳脫 `\\sqrt`，原 parser 不命中。
- 根號內帶分數（如 `\sqrt{1\frac{9}{16}}`）容易回傳 `None`。

修正：
- 正規化反斜線（`\\sqrt` -> `\sqrt`）。
- 保留簡單根式加減 parser。
- 新增 `sympy` fallback：處理較複雜根式/分數混合結構。

主檔：
- `core/code_utils/live_show_math_utils.py`

### D. 前端按鈕穩定性（先前已修，今日驗證）
- 「下一題」按鈕使用 `type="button"` + 傳入 `this`，避免事件/DOM selector 失配。
- 生成新題前會清理上次 `file_path` 快取，避免點到舊腳本。

主檔：
- `templates/live_show.html`

---

## 2) 今日驗證結論

已驗證（本地 test_client）：
- `\sqrt{12}+\sqrt{18}-\sqrt{27}+\sqrt{50}`
- `\sqrt{1\frac{9}{16}}+\sqrt{4\frac{25}{36}}`

結果：
- `generate_live` 可回題目。
- `run_generated_code` 可連續觸發。
- 答案不再是空字串。
- `下一題` 可連續出新題（同結構、不同數值）。

---

## 3) 目前規則（AI 必須遵守）

### Rule R1: `下一題` 必須依賴可執行 `generate()`
- 任何落地到 `generated_scripts/*.py` 的檔案，只要會被「下一題」使用，必須：
  1. 有 `def generate(level=1, **kwargs)`
  2. 可 `compile()`
- 若不符合，不能落地為最終腳本。

### Rule R2: 不要讓 Ab3 把 Ab2 已成功結果退化
- 若 Ab2 題型/格式/風格守規且有有效題面，Ab3 不得覆蓋成更差結果。
- 特別是 Radical：Ab3 fallback 不能把可用結果打回固定壞題或空答案。

### Rule R3: 答案欄位不能空白
- 回 API 前，若 `question_text` 有值且 `answer/correct_answer` 為空，必須嘗試重算。
- 若為根式題且得到 `0`，要做可疑值檢查，再重算一次。

### Rule R4: fallback 優先順序
1. 隨機同構 generator（首選，支援下一題連續出題）
2. 可編譯 isomorphic generator
3. 可編譯 Ab2 generator
4. 最後才是固定題面腳本（僅作災難備援）

### Rule R5: 輸出前一致性檢查
至少檢查：
- 題型家族（加減乘除、是否有分母有理化需求）
- 數值 token 數量
- 運算子序列與統計
- 根式相關計數（rad_count / simplifiable / rationalize）

---

## 4) 待完成事項（TODO）

### P0（建議立即）
1. 全量重跑壓測：`tests/comprehensive_stress_test.py`，更新 `tests/stress_test_report.html`。
2. 清理 mojibake/亂碼文案（目前部分舊模板字串仍有編碼殘留）。
3. 對 `generated_scripts` 加定期清理策略（避免大量暫存腳本堆積）。

### P1（穩定性）
1. 將「可編譯 generator gate」提取成共用函式，避免多處重複。
2. 對 `run_generated_code` 加更明確錯誤碼（區分：語法錯、缺 helper、答案回填失敗）。
3. 補 regression tests：
   - `下一題` 連續 20 次
   - fallback 後仍可隨機出題
   - answer 不為空

### P2（技術債）
1. 遷移 `google.generativeai` -> `google-genai`（目前仍有 deprecated warning）。

---

## 5) 推廣到下一單元：多項式四則運算（Polynomial）

目標：複製 Radical 的穩定策略，但保留 Polynomial 專屬結構約束。

### 必做映射
1. 在 pattern/style gate 建立 Polynomial 專屬白名單（同 Radical 的 style gate 概念）。
2. 定義 Polynomial 的 quality gate：
   - 項數
   - 次數分布（degree profile）
   - 運算子序列
   - 是否需要合併同類項/展開
3. 建立 `_build_randomized_polynomial_question_script(...)`：
   - 保持運算結構
   - 隨機係數
   - 每次 `generate()` 可變題
4. 套用同樣 answer sync 流程：
   - 空答案重算
   - 可疑答案重算

### 遷移順序（建議）
1. 先做「可編譯 generator gate」共用化。
2. 接著做 Polynomial random fallback generator。
3. 最後再接 style gate + quality gate 的嚴格比對。

---

## 6) 這次主要異動檔案

- `core/routes/live_show_pipeline.py`
- `core/routes/live_show.py`
- `core/code_utils/live_show_math_utils.py`
- `templates/live_show.html`

---

## 7) 交接備註

- 當前版本已可支撐 `live_show` 連續「生成 -> 下一題 -> 下一題」流程。
- 若使用者回報「下一題沒反應」，先查：
  1. `file_path` 是否存在
  2. 檔案是否有 `def generate(`
  3. 腳本是否可 `compile`
  4. `run_generated_code` 回傳是否帶 `problem/answer`
