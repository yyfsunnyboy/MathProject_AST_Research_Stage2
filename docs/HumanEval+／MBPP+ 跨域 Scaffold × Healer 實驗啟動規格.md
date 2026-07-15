---
title: HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格

---

# HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格

> 文件狀態：規劃中，尚未開始正式 confirmatory run  
> 版本日期：2026-07-15  
> 對應研究：旺宏科學獎決賽－AST Active Healer  
> 本文件用途：在實作前固定研究問題、資料切分、實驗分組、開發邊界與正式凍結條件，避免事後調整與 benchmark 洩漏。

---

## 一、研究定位

初賽版本的 Active Healer 是為「數學出題程式生成」建立的領域專用修復管線。決賽階段不主張原有數學規則可以直接套用所有程式任務，而是檢驗：

> 同一套「失敗普查 → 規則萃取 → 語意安全審查 → 規則凍結 → 未見資料驗證」方法，能否由數學出題領域遷移至 HumanEval+／MBPP+ 一般程式生成任務，建立新的通用程式生成 Scaffold 與 deterministic Healer，並在不使用正式答案或題目特例的前提下，提高可評估率與官方測試通過率。

本研究遷移的是**建構流程、治理原則與驗證方法**，不是把數學專用規則原封不動搬到公開 benchmark。

### 跨領域保留與重新建立的部分

| 跨領域保留的核心 | 依領域重新建立的內容 |
|---|---|
| 失敗普查與 failure taxonomy | HumanEval+／MBPP+ 常見失敗類型 |
| eligibility gate（修復資格審查） | 一般函式生成任務的安全判定條件 |
| Regex／AST 修復引擎 | 函式名稱、簽名、程式擷取、頂層副作用等規則 |
| 語意安全與禁止修復原則 | 各類錯誤的可修／不可修界線 |
| 前後 diff、hash 與稽核紀錄 | 新規則的正例、反例、不得修復案例 |
| 凍結後 replay 與完整重評 | EvalPlus 對應的正式 evaluator |
| Observed／Pipeline-corrected／Post-Healer 三帳制 | 各 benchmark 的任務契約與輸出格式 |

---

## 二、研究問題

### RQ1：Scaffold 主效應

凍結的 Generic Code Scaffold，是否能提高小型本地模型在 HumanEval+／MBPP+ 的：

- raw first-attempt pass@1；
- evaluability rate；
- parse／execution success rate；
- 指定函式與簽名遵守率？

### RQ2：Healer 主效應

凍結的 deterministic Code Healer，是否能在不使用正式答案、不依賴題目特例且不增加誤修的條件下，提高 pipeline pass rate？

### RQ3：Scaffold × Healer 交互作用

Scaffold 是否改變失敗的數量與組成，進而擴大、縮小或平移 Healer 的介入窗口？

### RQ4：跨資料集遷移

在 development／validation tasks 建立並凍結的 Scaffold 與 Healer，能否在未參與設計的 HumanEval+／MBPP+ tasks 上維持效果？

---

## 三、核心假說

- **H1：**Generic Code Scaffold 主要改善輸出紀律與可評估性，但不預設一定提升語意正確率。
- **H2：**Deterministic Healer 的增益集中在格式、擷取、介面與可證明安全的結構性錯誤；對演算法語意錯誤的增益有限。
- **H3：**Healer 的效果依原始 Prompt 條件而變；Scaffold 可能減少可修錯誤，也可能把不可評估輸出轉成可安全修復的結構錯誤。
- **H4：**若規則具有跨題泛化能力，凍結後仍可在未見 tasks 上取得 verified rescue，且 false repair／regression 接近零。

以上均為待驗證假說，不預先保證方向成立。

---

## 四、實驗分組：兩個生成組，各自比較 Healer 前後

本實驗**不是讓模型獨立生成四次**。模型只有兩種生成條件：Ab1 與 Ab2；每種條件產生的同一份原始程式，再分別評測「修復前」與「修復後」。因此會得到四個分析結果。

### 第一層：兩個模型生成組

| 生成組 | 給模型的內容 | 模型生成次數 | 用途 |
|---|---|---:|---|
| **Ab1：Bare Benchmark Prompt** | HumanEval+／MBPP+ 官方 task prompt 原樣，不加提示 | 每個 `task × model × seed` 一次 | 原始生成基準 |
| **Ab2：Generic Scaffold Prompt** | 同一份官方 task prompt，加上凍結的通用程式生成 Scaffold | 每個 `task × model × seed` 一次 | 測量前端鷹架效果 |

Ab1 與 Ab2 是兩次獨立的 first-attempt generation。兩者必須使用相同模型版本、解碼參數、seed 規則與輸出限制；唯一計畫內差異是是否加入 Generic Scaffold。

### 第二層：每份輸出都評測 Healer 前後

| 分析條件 | 原始輸出來源 | 是否經過 Healer | 實際意義 |
|---|---|---|---|
| **Ab1-Raw** | Ab1 生成的原始程式 | 否 | 官方 Prompt 下的原始 pass@1 基準 |
| **Ab1-Healed** | 與 Ab1-Raw 完全相同的程式 | 是 | Healer 在沒有 Scaffold 時能救回多少 |
| **Ab2-Raw** | Ab2 生成的原始程式 | 否 | Scaffold 單獨造成的變化 |
| **Ab2-Healed** | 與 Ab2-Raw 完全相同的程式 | 是 | Scaffold＋Healer 完整系統結果 |

`Ab1-Healed` 不是重新請模型生成，而是把 `Ab1-Raw` 保存下來的同一份程式交給凍結 Healer。`Ab2-Healed` 也只能由同一份 `Ab2-Raw` 轉換。如此才能將前後差異歸因於 deterministic repair。

### 單一 task 的實際流程範例

假設現在評測 `HumanEval/0 × 4B模型 × seed 42`：

1. 官方 prompt 原樣呼叫模型一次，得到 `output_ab1_raw.py`；
2. 直接以 EvalPlus 評測它，記為 `Ab1-Raw`；
3. 將同一個 `output_ab1_raw.py` 交給凍結 Healer，得到 `output_ab1_healed.py`，評測後記為 `Ab1-Healed`；
4. 官方 prompt 加 Generic Scaffold，再呼叫模型一次，得到 `output_ab2_raw.py`；
5. 直接評測它，記為 `Ab2-Raw`；
6. 將同一個 `output_ab2_raw.py` 交給相同的凍結 Healer，得到 `output_ab2_healed.py`，評測後記為 `Ab2-Healed`。

因此，一個 `task × model × seed` 的總成本是：

- **模型生成：2次**（Ab1一次、Ab2一次）；
- **Healer 執行：2次**（各處理一份已保存的 raw output）；
- **主要評測：4份結果**（Ab1-Raw、Ab1-Healed、Ab2-Raw、Ab2-Healed）。

等成本 retry 若執行，另列為次要對照，不屬於上述四個主要條件。

### 各比較回答的問題

| 比較 | 回答的問題 |
|---|---|
| `Ab2-Raw − Ab1-Raw` | 不使用 Healer 時，Scaffold 本身提升多少？ |
| `Ab1-Healed − Ab1-Raw` | 沒有 Scaffold 時，Healer 能救回多少？ |
| `Ab2-Healed − Ab2-Raw` | 已有 Scaffold 時，Healer 還能額外救回多少？ |
| `Ab2-Healed − Ab1-Raw` | 完整系統相對原始基準總共提升多少？ |
| 前兩種 Healer 增益的差異 | Scaffold 是否改變 Healer 的介入窗口？ |

正式報告時，`Ab1-Raw` 與 `Ab2-Raw` 報 raw first-attempt pass@1；`Ab1-Healed` 與 `Ab2-Healed` 則明確標為 Post-Healer pipeline pass rate，不得混稱為模型原始 pass@1。

---


## 五、資料切分與污染規則

### 基本三分法

若以 HumanEval+ 內部分割進行開發：

| 資料區 | 建議規模 | 可否反覆查看 | 用途 |
|---|---:|---|---|
| Development | 20 tasks | 可以 | 失敗普查、Scaffold／Healer 開發 |
| Validation | 20 tasks | 僅限版本選擇階段 | 選擇最終版本、排除誤修規則 |
| Confirmatory test | 其餘 tasks | 正式凍結前不可查看結果 | 唯一正式推論資料 |

實際 task 數量與資料集版本必須由正式 manifest 自動讀取並記錄，不只寫在文件中。

### 優先推薦的跨資料集方案

若 MBPP 有合適的非正式測試分割，優先採：

- MBPP development tasks：建立 failure taxonomy、Scaffold 與 Healer；
- 獨立 validation tasks：選擇最終版本；
- 完整未使用的 HumanEval+：跨資料集外部驗證；
- MBPP+ held-out tasks：同領域內部確認。

此方案可保留完整 HumanEval+ 作為外部驗證，證據強度高於從 HumanEval+ 切出20題後再測剩餘題目。

### 已看過資料的處理

- 任何已經逐題查看輸出、失敗原因，或曾用於修改 Prompt／Healer 的 task，自動歸入 development，不得再列入 confirmatory test。
- 先前20題 engineering smoke 若已被檢視，固定視為 development evidence。
- 只看過整體摘要但未用來調整規則的資料，需在紀錄中揭露；是否保留為正式資料應在開跑前一次決定。
- 若某批 tasks 已被用於 failure census，即使尚未修復，也不得再稱為完全未見測試資料。

### 切分固定方式

正式實作時應：

1. 記錄 dataset 名稱、版本、revision 與完整 task ID 清單；
2. 先標記所有已污染／已查看 tasks；
3. 對剩餘 tasks 使用固定 seed 或 task ID hash 產生 validation／confirmatory split；
4. 輸出 split manifest；
5. 計算 SHA-256；
6. 凍結後不得交換 task 歸屬。

若能取得 difficulty／category 等客觀標籤，可採分層切分；若沒有可靠標籤，不得以人工主觀挑選「代表性題目」。

---

## 六、Generic Code Scaffold 的開發邊界

### 允許內容

Scaffold 只能包含跨題可重用的程式契約，例如：

- 只輸出可執行 Python 程式碼；
- 不輸出 Markdown fence、解釋或思考文字；
- 保留 task 指定的函式名稱、參數與簽名；
- 不使用互動式 `input()`；
- 不在頂層加入示範呼叫、測試輸出或額外副作用；
- 遵守題目明示的輸入輸出型別與邊界條件；
- 不自行改寫題目契約；
- 只使用正式環境允許的相依套件。

### 禁止內容

- task ID、正式測試答案或 canonical solution；
- 只適用單一正式題目的演算法提示；
- 從 confirmatory failures 反推出來的特例；
- 暗示或洩漏 evaluator 隱藏測試內容；
- 為了提高某題分數而硬編碼的輸入輸出對；
- 正式凍結後再修改字句並把新結果混入原正式結果。

### 候選版本選擇

Development 階段可以產生多個 Scaffold 版本，但 Validation 階段只能依預先固定的選擇準則選出一版。建議依序比較：

1. raw first-attempt pass@1；
2. evaluability rate；
3. reasoning／prose leakage；
4. 函式契約遵守率；
5. token、duration 與 empty output；
6. 跨模型一致性。

不得因單一 task 表現而人工挑版。

---

## 七、Code Healer 的建立與治理

### 建立流程

1. 對 development set 的 P0、P1 原始輸出進行 failure census。
2. 將錯誤分類為 extraction、syntax、interface、runtime、semantic、safety 等類別。
3. 找出跨 task、跨 seed 或跨模型重複出現的候選模式。
4. 為每個候選規則定義偵測條件、適用條件、拒絕條件與預期不變量。
5. 建立正例、反例、不得修復案例及 regression tests。
6. Validation 階段排除會造成誤修或只對 development tasks 有效的規則。
7. 凍結規則內容、順序、版本、測試與 SHA-256。
8. 對 confirmatory outputs 只允許自動套用，不允許人工逐題修改。

### 允許修復

只允許能提出語意安全理由的轉換，例如：

- 移除 Markdown fence 或明確的程式碼外文字；
- 修正純格式與可證明等價的 Unicode／標點問題；
- 修復程式擷取造成的非模型責任缺失，但必須另列 Pipeline-corrected；
- 移除不影響函式結果的頂層示範呼叫或輸出副作用；
- 在能證明函式主體與介面不變時，處理 evaluator 無法載入的包裝問題。

### 禁止修復

- 根據官方答案、隱藏測試或 canonical solution 改演算法；
- 猜測模型意圖後補寫實質邏輯；
- 依 task ID 套用不同答案；
- 對正式失敗題新增專屬條件；
- 將語意錯誤包裝成格式錯誤；
- 修復後未重新通過完整 evaluator 就宣稱成功。

### 每條規則必備紀錄

- `rule_id` 與版本；
- failure type；
- detection predicate；
- eligibility predicate；
- rejection／abstention conditions；
- transformation；
- semantic-safety rationale；
- positive tests；
- negative tests；
- do-not-repair tests；
- pre／post hash 與 diff；
- applied／abstained／verified／regressed 狀態。

---

## 八、三帳制與責任歸屬

每筆結果至少分列：

1. **Observed：**模型 first-attempt 原始輸出直接評測結果；
2. **Pipeline-corrected：**只修正研究管線自身錯誤後的結果，例如 extractor 誤切 import；
3. **Post-Healer：**凍結 Healer 對 Pipeline-corrected 輸出修復後的結果。

Raw pass@1 不得以 Post-Healer 數值取代。若報「完整系統通過率」，必須明確標示為 pipeline pass rate 或 Post-Healer pass rate。

---

## 九、主要與次要結果指標

### Primary outcomes

- raw first-attempt pass@1；
- Post-Healer pipeline pass rate；
- verified rescue count／rate；
- false repair／regression count／rate。

### Secondary outcomes

- evaluability rate；
- extraction／parse／execution／interface success rate；
- eligibility rate；
- attempted repair rate；
- abstention rate；
- failure taxonomy 分布；
- Scaffold × Healer 交互作用；
- 不同模型大小與資料集的效果差異。

### Cost／efficiency outcomes

- prompt_eval_count；
- eval_count；
- prompt token、output token、total token；
- total_duration、load_duration、prompt_eval_duration、eval_duration；
- wall_clock_seconds；
- repair_cpu_seconds；
- cold_start／warm_run；
- hardware、quantization、runtime 與版本。

成本為 secondary／descriptive outcomes，不取代正確性結果。

### 分母規則

所有比例必須同時報分子與分母。例如：

- `verified rescue = 6/18 eligible outputs`；
- `overall uplift = 6/124 confirmatory tasks`；
- `regression = 0/106 originally passing or evaluable outputs`。

---

## 十、Retry 對照

若資源允許，增加一次**等成本重生成**作為對照：

- 使用相同模型、Prompt 條件與解碼設定；
- 每筆最多一次 retry；
- retry 結果另列，不改寫 first-attempt ITT；
- 比較 verified rescue、retry recovery、token、duration 與穩定性；
- 不得只保留兩次中較好的結果作為 raw pass@1。

此對照用來判斷 Healer 的效果是否優於「再抽一次可能剛好成功」。

---

## 十一、正式凍結門檻

進入 confirmatory run 前，以下項目必須全部完成：

- [ ] dataset／EvalPlus 版本與 task manifest 已記錄；
- [ ] development／validation／confirmatory task IDs 已凍結；
- [ ] 已看過的20題 smoke 全部排除於 confirmatory；
- [ ] P0 官方 prompt 保持原樣；
- [ ] P1 Generic Code Scaffold 已凍結；
- [ ] Healer 規則、順序與 eligibility gate 已凍結；
- [ ] evaluator 與 raw-output extraction 已通過 targeted tests；
- [ ] Pipeline-corrected 規則與 Healer 規則已分帳；
- [ ] model tag、digest、quantization、runtime、參數與 seed 已凍結；
- [ ] primary／secondary outcomes 已固定；
- [ ] retry 是否執行及成本配對方式已固定；
- [ ] 所有 manifest、Prompt、規則與測試已產生 SHA-256；
- [ ] zero-model preflight 已通過；
- [ ] 正式 run 的停止與異常處理規則已固定。

任何一項未完成，不得稱為正式 confirmatory run。

---

## 十二、正式執行後的禁止事項

- 不得因正式結果不佳修改 Scaffold 或 Healer 後覆蓋原結果；
- 不得移除困難題、空輸出、timeout 或不利樣本；
- 不得把 pipeline bug 算成模型失敗而不揭露；
- 不得把語意修補稱為 deterministic syntax repair；
- 不得用 Healer 後 Edge 模型對未修復 Cloud 模型宣稱「反超」；
- 不得只報成功案例，不報 eligibility、abstention 與 regression；
- 不得把 exploratory 新規則混入 confirmatory 統計。

正式凍結後若發現新規則，只能放入 `Exploratory vNext`，不可回寫正式主分析。

---

## 十三、統計與呈現方式

因同一 task 在不同條件下成對比較，分析時應保留 task-level paired data，而非只比較總平均。

建議呈現：

1. A／B／C／D 四條件的分子、分母與95%信賴區間；
2. task-level pass／fail 配對轉移表；
3. Scaffold 前後 failure taxonomy 轉移；
4. eligibility → attempted → transformed → evaluator pass 的 Healer 漏斗；
5. rescued／unchanged／regressed／abstained 四類結果；
6. model size × dataset × Prompt × Healer 的分層結果；
7. 必要時使用 paired bootstrap 或 McNemar test，效果量優先於只報 p 值。

### 最重要的圖

- 四條件通過率圖；
- Scaffold 前後錯誤分布轉移圖；
- Healer intervention funnel；
- 模型能力 × 任務困難度下的介入窗口圖；
- verified rescue 與等成本 retry 的成本－效果比較。

---

## 十四、作者研發角色與可追溯性

為回應評審對參賽者實質角色的要求，實驗期間另留：

- 每次 failure review 的日期、參與者與判斷；
- 規則提出者、理由、測試設計與採納／拒絕紀錄；
- Prompt 版本差異與修改理由；
- AI 工具協助的範圍；
- 由參賽者完成的分析、程式、測試與口頭解釋；
- 是否有教師、大學實驗室或外部專家協助及其具體範圍。

目標不是宣稱完全沒有工具協助，而是讓每項研究判斷與實作責任可被清楚追溯。

---

## 十五、建議執行順序

### Milestone 0：範圍與資料治理

1. 盤點現有 HumanEval+／MBPP+ outputs、task IDs 與已查看範圍；
2. 將已使用的20題 smoke 鎖為 development；
3. 決定採 HumanEval+ 內部三分法，或 MBPP development → HumanEval+ 外部驗證；
4. 建立並凍結 split manifest。

### Milestone 1：Development failure census

1. 固定 P0 與候選 P1；
2. 在 development tasks 收集 P0／P1 first-attempt outputs；
3. 完成 extraction、syntax、interface、runtime、semantic、safety 分類；
4. 形成候選 Scaffold 約束與 Healer rules。

### Milestone 2：Validation 與規則治理

1. 在 validation tasks 比較候選 Scaffold；
2. 逐條執行 positive／negative／do-not-repair tests；
3. 排除誤修、特例化與跨模型不穩定規則；
4. 選定唯一 P1 與唯一正式 Healer；
5. 完成凍結與 SHA-256。

### Milestone 3：Zero-model preflight

1. 驗證 manifest、runner、輸出目錄、斷點續跑與異常紀錄；
2. 以固定假資料驗證 A／B／C／D 分帳；
3. 確認 official task prompt 不被重複拼接；
4. 確認 Healer 永遠作用於已保存的同一份 raw output。

### Milestone 4：Confirmatory run

1. 一次執行凍結 plan；
2. 不於中途查看個別錯誤並修改規則；
3. 保存完整 provenance、raw outputs、logs 與 costs；
4. 執行官方 EvalPlus；
5. 輸出 Observed／Pipeline-corrected／Post-Healer 三帳。

### Milestone 5：分析與成果報告

1. 完成主結果、錯誤分布、介入窗口與成本分析；
2. 對零增益、窄窗口或負結果照實解釋；
3. 分清既有技術與本研究新增貢獻；
4. 產出可供決賽報告與簡報使用的圖表。

---

## 十六、成功與失敗都可接受的結論

| 正式結果 | 可支持的結論 |
|---|---|
| Scaffold 與 Healer 均有增益 | 前端預防與後端修復具有互補效果 |
| Scaffold 有效、Healer 增益小 | 大部分可預防錯誤已被前端消除，介入窗口狹窄 |
| Scaffold 無效、Healer 有效 | 輸出約束未穩定改變語意表現，但確定性後處理仍能救回結構錯誤 |
| 兩者皆近零 | 公開 benchmark 的主要失敗屬語意／演算法層，確定性非語意修復的邊界被外部資料清楚刻畫 |
| Healer 出現 regression | 現有 eligibility gate 不足，不能宣稱安全有效；應將問題列為主要限制 |

研究目標不是保證提高分數，而是公平回答「能提高多少、救哪種錯、在哪裡失效、是否值得介入」。

---

## 十七、成果發表核心句

> 我們沒有把數學 Healer 的規則硬搬到公開程式題庫，而是把它的建構方法搬過去：先從獨立開發資料觀察失敗，建立可證明安全的通用鷹架與修復規則，凍結後再由 HumanEval+／MBPP+ 的官方測試判定是否真正有效。

更精簡的口試版本：

> 我們研究的不是某幾個修復檔案，而是一套能否跨領域重建、凍結並接受外部 benchmark 檢驗的 Healer 方法。

---

## 十八、開工前第一個決策

正式實作前，只需先決定以下一題：

> **採用「HumanEval+ 20 development＋20 validation＋其餘 confirmatory」；還是採用「MBPP development／validation＋完整 HumanEval+ 外部驗證」？**

在這個決策完成、既有資料污染範圍盤點清楚之前，先不修改正式 Scaffold、不新增正式 Healer 規則，也不啟動 confirmatory model run。