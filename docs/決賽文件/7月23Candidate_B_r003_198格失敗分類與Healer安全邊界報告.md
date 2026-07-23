# Candidate B r003：198 格失敗分類與 Healer 安全邊界研究報告

**專案：** MathProject_AST_Research_Stage2

**研究範圍：** Candidate B r003、MBPP+、H0

**分類標準：** AI 生成程式共同失敗分類標準 taxonomy v3.1

**報告狀態：** 已完成獨立稽核並正式封存

**封存日期：** 2026 年 7 月 23 日

**最終版本：** `6f17101e0f832d921b004028695905198c722355`

**最終裁決：** `AUDITED_198CELL_REPORT_FINALIZED`


---

## 摘要

本研究分析 Candidate B r003 在公開程式解題資料集 MBPP+ 中的 198 個正式失敗案例，目的不是追求「盡量多修」，而是判斷 AI 生成 Python 程式發生失敗時，哪些錯誤能由 deterministic Healer 安全修復、哪些需要補充診斷，以及哪些情況應主動拒絕修改。

198 格依 taxonomy v3.1 完成凍結分類後，主要失敗層級為 L2 7 格、L4 70 格、L5 54 格，以及 UNRESOLVED 67 格。Healer 安全裁決結果為：可立即修復的 `eligible` 0 格、需要額外診斷或安全 guard 的 `conditional` 23 格、應拒絕修復的 `abstain` 175 格。

結果顯示，錯誤位於某一失敗層級，不代表它就能被安全修復。即使有 70 格被定位在 L4，也只有 23 格被判定為 conditional，其餘仍須 abstain。另有 31 格需要重建演算法，已超出局部 deterministic repair 的研究邊界。

本研究的核心發現不是「Healer 修得很多」，而是建立了一條可稽核的安全界線：

> **只有錯誤能被穩定定位、修法唯一、不需參考答案，且能以明確 guard 限制適用範圍時，才可能交由 Healer 修改；其餘案例應保守拒修。**

---

## 一、研究背景與問題

大型語言模型生成 Python 程式時，失敗可能來自格式、語法、函式契約、執行例外、資料流或演算法語意。若只用通過率表示結果，無法回答下列問題：

1. 程式究竟在哪一層失敗？
2. 錯誤是否能在不偷看答案的情況下被定位？
3. 是否存在唯一且安全的局部修法？
4. 哪些案例需要更多診斷才能決定？
5. 哪些案例已超出 deterministic Healer 的能力邊界？
6. 系統何時應停止修改並選擇 abstain？

因此，本研究將 Scaffold 與 Healer 分開：

- **Scaffold**：在模型生成前提供結構與輸出限制，目標是預防錯誤。
- **Healer**：在生成後處理已發生、可定位且具有安全修法的局部錯誤。

兩者不能合併計功。被 prompt 或 Scaffold 預先避免的錯誤，不能再次計為 Healer rescue。

---

## 二、資料與實驗單位

### 2.1 資料規模

| 項目 | 數量 |
|---|---:|
| Programs | 198 |
| Cells | 198 |
| Sources | 155 |
| Tasks | 50 |
| MBPP+ cells | 198 |
| HumanEval+ cells | 0 |
| H0 cells | 198 |
| H1 cells | 0 |

本報告的正式範圍全部為 MBPP+ 與 H0，因此不能用來宣稱 HumanEval+、H1、跨 benchmark 或 Scaffold 前後的效果。

### 2.2 為何 198 格只有 155 份 source

`program`、`cell` 與 `source` 是不同的治理單位：

- `cell` 是實驗帳目中的唯一分析單位。
- `program` 是與該 cell 對應的正式程式紀錄。
- `source` 是實際保存的程式原始碼內容。

共有 25 組共享 source，涉及 68 格，占全部 198 格的 34.3%。這表示不同 cell 可以合法保存相同的原始碼內容，但其 cell identity 與 program identity 仍各自獨立。

因此：

- 198 programs 與 198 cells 沒有重複帳目；
- 155 sources 反映內容層級的重複；
- 共享 source 的 cells 不能被解讀為完全獨立的 198 次不同程式內容。

### 2.3 Candidate B r003 的位置

Candidate B r003 是本研究既定且已凍結的生成條件。本輪 198 格工作只針對保存的正式失敗紀錄進行 taxonomy 分類與 Healer 安全邊界分析：

- 不修改既有 Scaffold；
- 不重新生成程式；
- 不重新執行模型；
- 不用診斷結果反向修改既有分類；
- 不把本輪分類當成已完成的 Healer 成效實驗。

---

## 三、分類與裁決方法

### 3.1 失敗層級

本研究沿用 taxonomy v3.1 的 L0–L5 架構，並保留 UNRESOLVED。實際判定以正式 frozen codebook 與 records 為準。

| 層級 | 研究意義 |
|---|---|
| L0 | 研究管線、抽取或包裝責任；應與模型錯誤及 Healer 成效分帳 |
| L1 | 無法可靠解析或必要程式結構不成立 |
| L2 | 函式名稱、參數、entry point、輸入輸出等契約錯誤 |
| L3 | 名稱綁定、組裝、資料流或局部結構關係錯誤 |
| L4 | 程式可解析，但執行時發生例外、逾時或其他 runtime failure |
| L5 | 程式可執行，但答案、演算法或邊界條件在語意上錯誤 |
| UNRESOLVED | 現有證據不足以安全定位主要根因 |

### 3.2 Primary 與 Secondary

- `primary_failure_layer`：目前證據支持的主要失敗層級。
- `secondary_failure_layers`：在主要問題之外，同時存在的其他失敗層級。

Primary 是主要裁決，不代表程式只有一個問題。Secondary 也不能取代 Primary。

### 3.3 Confidence

Confidence 表示現有證據對分類判斷的支持程度：

- `HIGH`：證據足以穩定支持目前分類。
- `MEDIUM`：已有相當證據，但仍存在有限不確定性。
- `LOW`：現有靜態證據不足，不宜進一步推定修法。

Confidence 是「分類證據強度」，不是程式正確率，也不是修復成功率。

### 3.4 Outcome validity

`outcome_validity` 判斷該失敗是否為可納入研究的有效模型結果。本報告 198 格全部為 `VALID_MODEL_OUTCOME`，表示這些案例均可納入失敗分類；不表示它們已被修復。

### 3.5 Failure chain 與 mechanism tags

- `failure_chain`：記錄一個案例中錯誤可能依序顯現的關係。
- `mechanism_tags`：記錄具體錯誤機制，例如需要診斷執行、module exception、plus failure 尚未定位或需要演算法重建。

Mechanism tags 可以同時出現在同一格，因此各 tag 數量不能相加後當成 198 格的互斥分布。

### 3.6 Truncation 的分類原則

Truncation 是跨層 mechanism tag，不是固定等同於某一層：

- 截斷造成無法解析時，可能呈現為 L1；
- 可解析但執行失敗時，可能呈現為 L4；
- 可執行但演算法內容不完整時，可能呈現為 L5。

截斷表示部分程式內容已遺失，通常不存在唯一安全的補法，因此原則上應 abstain，而不是由 Healer 猜測缺失內容。

### 3.7 Entry point 的分類原則

Entry-point 問題歸入 L2 Contract：

- 只有一個符合完整契約的安全候選時，才可能進入 Healer eligibility 評估；
- 有多個候選、函式簽章不明或需猜測模型意圖時，必須標示 ambiguous 並 abstain。

### 3.8 Healer 三種安全裁決

| 裁決 | 意義 |
|---|---|
| `eligible` | 已有充分證據支持唯一、局部、確定且不需答案的安全修法 |
| `conditional` | 可能可修，但必須先取得指定診斷證據或滿足安全 guard |
| `abstain` | 證據不足、修法不唯一、風險過高或需要重建演算法，應拒絕修改 |

`conditional` 不是「已經可以修」，`abstain` 也不是「Healer 執行後修復失敗」。

### 3.9 Oracle-free 原則

Healer 不得使用下列資料反推修法：

- 隱藏測試的答案；
- 官方 reference answer；
- canonical solution；
- 單題 task ID 或 seed 特例；
- evaluator 的正確答案資訊。

修復規則必須先由可觀察的程式結構、公開契約與允許的診斷證據決定；修後才交由相同 evaluator 驗證。

---

## 四、198 格完整統計

### 4.1 Primary failure layer

| Primary layer | N | 百分比 |
|---|---:|---:|
| L2 | 7 | 3.5% |
| L4 | 70 | 35.4% |
| L5 | 54 | 27.3% |
| UNRESOLVED | 67 | 33.8% |
| **合計** | **198** | **100.0%** |

L4 是數量最多的已定位層級，共 70 格；但 UNRESOLVED 也有 67 格，顯示僅靠現有靜態證據，仍有約三分之一案例無法安全定位。

### 4.2 Secondary failure layers

| Secondary layer | N | 百分比 |
|---|---:|---:|
| 無 Secondary | 154 | 77.8% |
| L4 | 2 | 1.0% |
| L5 | 42 | 21.2% |
| **合計** | **198** | **100.0%** |

42 格帶有 L5 secondary，表示部分程式即使先排除前層問題，仍可能顯露語意或演算法層問題。修復較前層的錯誤，不能直接宣稱程式已正確。

### 4.3 Confidence

| Confidence | N | 百分比 |
|---|---:|---:|
| HIGH | 126 | 63.6% |
| MEDIUM | 5 | 2.5% |
| LOW | 67 | 33.8% |
| **合計** | **198** | **100.0%** |

67 格 LOW confidence 全部採取 abstain，符合「證據不足時不猜測修法」的安全原則。

### 4.4 Outcome validity

| Outcome validity | N | 百分比 |
|---|---:|---:|
| VALID_MODEL_OUTCOME | 198 | 100.0% |
| 其他 | 0 | 0.0% |
| **合計** | **198** | **100.0%** |

### 4.5 Healer decision

| Healer decision | N | 百分比 |
|---|---:|---:|
| eligible | 0 | 0.0% |
| conditional | 23 | 11.6% |
| abstain | 175 | 88.4% |
| **合計** | **198** | **100.0%** |

這項統計是本報告最重要的安全邊界：

- 沒有任何案例已具備可立即部署的安全規則；
- 23 格值得進一步診斷，但還不能直接修；
- 175 格依現有證據應維持拒修。

### 4.6 主要 active mechanism tags

| Mechanism tag | N | 占198格比例 |
|---|---:|---:|
| `diagnostic_execution_required` | 49 | 24.7% |
| `public_examples_non_discriminating` | 49 | 24.7% |
| `module_execution_exception` | 48 | 24.2% |
| `plus_failure_not_localized` | 38 | 19.2% |
| `algorithm_reconstruction_required` | 31 | 15.7% |

以上 tags 非互斥，同一格可能同時具有多個 mechanism。

其中：

- `diagnostic_execution_required` 表示靜態證據不足，需受控執行診斷；
- `public_examples_non_discriminating` 表示公開例子不足以區分可能根因；
- `module_execution_exception` 表示 module 執行階段出現例外；
- `plus_failure_not_localized` 表示已知未通過 plus tests，但目前不能安全定位失敗位置；
- `algorithm_reconstruction_required` 表示若要改正，必須重建演算法，不能稱為局部 Healer 修復。

---

## 五、交叉分析

### 5.1 Dataset 與實驗條件

| 比較 | 分母 | N | 百分比 |
|---|---:|---:|---:|
| MBPP+ | 198 | 198 | 100.0% |
| HumanEval+ | 0 | 0 | NA |
| H0 | 198 | 198 | 100.0% |
| H1 | 0 | 0 | NA |

由於 HumanEval+ 與 H1 的分母都是 0，本報告不能比較：

- HumanEval+ 與 MBPP+；
- H0 與 H1；
- Healer 前後效果。

### 5.2 Scaffold-like 與非 Scaffold-like

Frozen records 沒有正式的 scaffold-like 欄位，因此本報告不事後推定、不重建該分組，也不宣稱 Scaffold 對這 198 格造成何種效果。

### 5.3 Failure layer × Healer decision

| Primary layer | 分母 | eligible | conditional | abstain |
|---|---:|---:|---:|---:|
| L2 | 7 | 0（0.0%） | 0（0.0%） | 7（100.0%） |
| L4 | 70 | 0（0.0%） | 23（32.9%） | 47（67.1%） |
| L5 | 54 | 0（0.0%） | 0（0.0%） | 54（100.0%） |
| UNRESOLVED | 67 | 0（0.0%） | 0（0.0%） | 67（100.0%） |
| **合計** | **198** | **0** | **23** | **175** |

23 格 conditional 全部位於 L4，但不能反過來說 L4 都可修。L4 中只有 32.9% 進入 conditional，仍有 67.1% 應 abstain。

### 5.4 Confidence × Healer decision

目前可由正式統計直接確認：

| Confidence | 分母 | 已知裁決 |
|---|---:|---|
| LOW | 67 | 67 格全部 abstain（100.0%） |
| HIGH／MEDIUM | 131 | 本摘要不再推定未提供的細部分布 |

這顯示分類信心不足時，系統採取保守拒修，而不是把不確定性轉化成猜測式修改。

### 5.5 Outcome validity × Failure layer

198 格全部是有效模型結果，因此 L2、L4、L5 與 UNRESOLVED 都是在 `VALID_MODEL_OUTCOME` 內進行分類。Outcome validity 與 failure layer 回答的是不同問題：

- Outcome validity：這筆紀錄是否能納入研究；
- Failure layer：這筆有效紀錄主要在哪一層失敗。

---

## 六、可修與不可修的邊界

### 6.1 可安全確定性修復

本批資料的 `eligible=0`，因此目前沒有規則能直接進入正式 deterministic Healer。

這不表示 deterministic repair 永遠不存在，而是表示在這 198 格的現有證據下，尚未有任何案例同時滿足：

1. 根因已穩定定位；
2. 修改位置明確；
3. 修法唯一；
4. 不需猜測程式意圖；
5. 不需參考答案；
6. 可用 guard 排除相似但不可修的案例。

### 6.2 需要額外診斷後才可能修復

共有 23 格 conditional，占 11.6%，全部位於 L4。

這些案例的正確處理方式是：

1. 先凍結候選名冊；
2. 依共同錯誤機制分群；
3. 預先登錄允許的 diagnostics；
4. 定義每群的安全 guard；
5. 定義升格、淘汰與 abstain 標準；
6. 完成方案稽核後才執行診斷；
7. 只有通過全部條件的群組才能升為 eligible。

23 格不等於 23 條規則。多格可能共享同一根因，也可能在診斷後全部或部分被淘汰。

### 6.2.1 跨題 Healer 規則通用性搜尋結論 (Development-only 跨題搜尋)

為探索是否能從 `conditional` 機制中提煉出通用的 deterministic Healer 規則，本研究在合法的開發數據分區下進行了跨題失敗機制檢索。

#### 一、 數據覆蓋範圍與合法邊界 (Evidence Coverage)

由正式 `frozen_split.csv`、`development60` replay 與 EvalPlus H0 結果重算後，本輪可稽核數字為：

| 項目 | 數量 | 說明 |
|---|---:|---|
| 合法 development task 母體 | **116** | `historical_development_pool`（含 20 active + 96 其餘 historical） |
| development60 實際涵蓋 distinct tasks | **60** | 未宣稱已完整搜尋 116 題母體 |
| H0 總格數 | **300** | 60 tasks × 5 seeds |
| H0 失敗格數（EvalPlus plus=fail） | **224** | 不得把總格數寫成失敗格數 |
| H0 通過格數（plus=pass） | **76** | negative controls／非失敗格 |
| Conditional 23 實際 coverage | **23** | 198 格正式分類中的 Healer conditional 子集 |

- **明確排除**：本輪跨題檢索已嚴格排除所有 `validation`、`confirmatory`、`sealed_reserve` 等非開發分區資料，確保研究不發生 project contamination。
- **不得外推**：不得把 116 題母體誤寫成已完整搜尋 116 題；本輪僅在 development60 的實際可用 evidence 上定案。

#### 二、 跨題搜尋結果與機制分析

本研究重點檢索了兩類代表性機制，正式結論如下：

1. **Index Off-by-One 偏一錯誤（`Mbpp/739`）**
   - `Mbpp/739` 的 $k-1$ 偏一錯誤在同一 task 的 **5 個 seeds**（11/22/33/44/55）重現。
   - 在其他 59 個 tasks 的失敗格中，未發現可安全且具備通用性的同構模式。
   - **task-level 獨立證據數 = 1**。
2. **Distinct / Unique 語意混淆（`Mbpp/777`）**
   - `Mbpp/777` 的 distinct／unique 混淆在同一 task 的 **多 seeds（development60 上為 5 seeds）** 重現。
   - 其餘 59 個 tasks 未發現可安全跨題泛化的同構 Counter 混淆。
   - **task-level 獨立證據數 = 1**。

因此：

1. 每一機制都只有 **1 個** task-level evidence。
2. 多 seed 只能證明**可重現**，不能證明**跨題泛化**。
3. 判斷這兩種錯誤必須理解題意或讀取 task contract。
4. **不得**將 Task ID 白名單納入正式通用 Healer。
5. 僅保留為 **task-specific repair hypothesis／counterfactual example**。
6. 正式通用 Healer 對這兩類機制一律 **ABSTAIN**（`TASK_SPECIFIC_REPAIR_ONLY`／`NO_SAFE_GENERALIZABLE_RULE_FOUND`／`GENERAL_HEALER_ABSTAIN`）。
7. 現有 Healer **凍結**，不修改任何 repair 規則。

#### 三、 六項安全條件之文字修正

通用 Healer 的安全條件維持，但下列三點必須正確理解：

1. **repair 在已知題意後唯一、局部，不代表它是通用安全規則。**
2. **regression guard 可驗證結構與可執行性，但不能在不看答案時保證語意無 regression。**
3. **public test 或修後 PASS 不得作為 Healer 接受修改的 oracle gate。**

其餘安全條件（錯誤可穩定定位、不需猜測意圖、可用 guard 排除相似但不可修案例）維持不變。

#### 四、 研究主張限縮與分帳聲明

- **限縮主張**：在本輪指定機制及實際可用 development evidence 範圍內，未找到安全跨題規則。本研究**不得宣稱已窮盡所有可能 Healer 機制**。
- **數據完整性**：本輪跨題分析僅對 Healer 規則邊界進行定案與同步，**未修改任何既有 198 格分類結果、L0–L5、EvalPlus、Rescue／Regression 數值或已凍結證物 SHA**，確保歷史數據的唯讀完整性。


### 6.3 應直接 abstain

共有 175 格，占 88.4%。常見原因包括：

- 現有證據不足以定位；
- 修法不唯一；
- 公開例子不足以判別根因；
- 修改可能改變演算法語意；
- 需猜測缺失或截斷內容；
- 需要 oracle 或隱藏測試才能決定；
- 需要重建演算法。

Abstain 是 Healer 的安全功能，不是系統漏做工作，也不是修復執行失敗。

### 6.4 需要重建演算法

共有 31 格带有 `algorithm_reconstruction_required`，占 15.7%。

這些案例若要變成正確程式，需要重新設計或重寫核心演算法。這屬於再生成、重新解題或 capability augmentation 的研究範圍，不能包裝成 deterministic local Healer rescue。

---

## 七、Scaffold 與 Healer 的研究發現

### 7.1 兩者作用時間不同

| 方法 | 介入時間 | 主要功能 |
|---|---|---|
| Scaffold | 生成前 | 約束輸出、預防常見錯誤 |
| Healer | 生成後 | 對已定位且修法唯一的局部錯誤進行確定性處理 |

### 7.2 不可合併計功

- Scaffold 預防的錯誤不算 Healer rescue。
- Pipeline correction 不算 Healer rescue。
- 只修到可解析或可執行，不等於修到答案正確。
- Healer 有修改程式，不等於修復成功。
- 修後必須通過相同完整 evaluator，才能稱為 verified rescue。

### 7.3 本批資料目前能支持的結論

本批資料支持：

- 失敗層級與安全可修性是不同維度；
- deterministic Healer 的安全介入窗口很窄；
- runtime failure 不等於可直接修復；
- abstain 是避免 regression 的必要設計；
- 演算法與語意錯誤不能由局部修補冒充修復。

本批資料尚不能支持：

- Scaffold 提升了多少通過率；
- Healer 已成功 rescue 多少格；
- Healer 沒有造成 regression；
- H1 優於 H0；
- 結果可推廣至 HumanEval+、其他模型或所有 LLM。

---

## 八、UNRESOLVED 的研究意義

UNRESOLVED 共 67 格，占 33.8%。

UNRESOLVED 不等於：

- L5；
- 沒有錯誤；
- 一定是演算法錯誤；
- 一定不可修；
- Healer 已執行但失敗。

它的正確意義是：

> **現有靜態證據不足以安全定位主要根因，因此不能進一步猜測修法。**

後續 diagnostics 的角色是補充根因定位證據，不是用隱藏答案反推程式應如何修改。未來診斷可能使部分案例得到更清楚的分類，但在正式完成以前，不能把可能結果寫成既成結論。

---

## 九、研究限制

1. **資料範圍限制**

   本報告只涵蓋 Candidate B r003 的 198 格 MBPP+、H0 紀錄。

2. **無 HumanEval+ 與 H1 樣本**

   HumanEval+=0、H1=0，相關效果不能估計，百分比應列為 NA。

3. **無正式 scaffold-like 欄位**

   不得事後依主觀判斷重建 Scaffold 分組。

4. **靜態分類與動態診斷不同**

   Taxonomy records 主要整理現有證據；dynamic diagnostics 尚未在本輪執行。

5. **共享 source 的獨立性限制**

   25 組共享 source 涉及 68 格。198 cells 是正式帳目數，不等於 198 份完全不同的程式內容。

6. **模型與生成條件限制**

   結論只對本研究凍結的模型、prompt、sampling、資料分布與 runtime 條件負責。

7. **高中專題的規模限制**

   樣本規模、人工複核能力與可執行的外部驗證範圍有限，因此重視證據治理與保守外推。

8. **Abstain 不能解釋為失敗率**

   88.4% abstain 表示規則未獲安全授權，不表示 Healer 實際執行後有 88.4% 修復失敗。

9. **尚未測量正式 rescue 與 regression**

   本輪是 taxonomy 與 eligibility 研究，不是完成 Healer 後的 frozen replay。

---

## 十、研究結論

### 10.1 正式學術版

本研究以 taxonomy v3.1 對 Candidate B r003 的 198 個 MBPP+、H0 正式失敗案例進行可稽核分類。結果顯示，主要失敗層級為 L2 7 格、L4 70 格、L5 54 格及 UNRESOLVED 67 格；Healer 安全裁決則為 eligible 0 格、conditional 23 格及 abstain 175 格。雖然 L4 是數量最多的已定位層級，但僅 23/70（32.9%）具有進一步診斷價值，其餘仍應拒修；另有 31 格需要演算法重建，已超出 deterministic local repair 的合理邊界。研究結果支持「錯誤層級不等於安全可修性」，並顯示具備明確 abstention 機制，是降低猜測式修復與語意 regression 風險的必要條件。此結論僅適用於本次凍結的 MBPP+、H0、Candidate B r003 資料，不外推至 HumanEval+、H1、其他模型或所有大型語言模型。

### 10.2 高中生口頭報告版

我們分析了 198 個 AI 生成 Python 程式的失敗案例，想知道哪些錯誤真的能安全修，而不是看到錯誤就硬改。結果發現，198 格裡沒有任何一格現在就能直接寫成安全修復規則；有 23 格可能可以修，但必須先做診斷並加上 guard；另外 175 格目前都應該拒絕修改。這不是代表 Healer 完全沒用，而是表示安全的修復範圍比想像中窄。尤其有 31 格需要重做演算法，這已經不是局部修復。我們的成果是建立一套會判斷「什麼時候能修、什麼時候一定要停」的方法。

### 10.3 一句話核心成果

> **真正安全的 Healer，不是修得最多，而是只在證據充分、修法唯一時介入，並在其餘情況主動 abstain。**

---

## 十一、後續實驗規劃

後續研究應依下列順序進行，不回頭修改已凍結的 Candidate B r003 Scaffold：

1. 凍結 23 格 conditional 候選名冊；
2. 依共同 failure mechanism 分群；
3. 預先登錄每群允許的 diagnostics；
4. 定義必要證據、安全 guard、升格與淘汰標準；
5. 獨立稽核並封存診斷方案；
6. 執行 diagnostics，但不使用結果作為正式 Healer 的隱藏 runtime input；
7. 將通過全部條件的候選升為 eligible；
8. 建置 deterministic Healer 與 positive、negative、do-not-repair tests；
9. 凍結 rule pack、順序、版本與 SHA；
10. 以 frozen replay 同時檢驗 rescue、regression、unchanged 與 abstain；
11. 將 Healer 成效與 prompt／Scaffold 效果分開；
12. 未來再進行跨模型或跨 benchmark 外部驗證。

---

## 十二、證據治理與獨立稽核

### 12.1 數量閉合

- `198 = 177 + 21`
- program = 198
- cell = 198
- source = 155
- task = 50
- duplicate cell = 0
- omission = 0
- remaining = 0

### 12.2 獨立稽核結果

| Finding | 數量 |
|---|---:|
| AFFIRMED | 22 |
| NON_MATERIAL | 0 |
| MATERIAL | 0 |

獨立稽核確認：

- 253 項數字、分母與百分比全部吻合；
- UNRESOLVED 未被誤寫為 L5 或沒有錯誤；
- abstain 未被寫成 Healer 執行失敗；
- conditional 未被宣稱為已可安全修復；
- eligible=0 未被暗示為已有可部署規則；
- algorithm reconstruction 未計為 Healer rescue；
- Scaffold 與 Healer 未合併計功；
- 未對 HumanEval+、H1 或跨 benchmark 效果過度外推。

### 12.3 驗證結果

- Report 與 audit builders 雙重重建逐 byte 一致；
- `py_compile` 通過；
- targeted pytest：11 passed；
- `git diff --check` 通過；
- candidate、model、EvalPlus、diagnostics、validation、Healer execution counts 均為 0；
- taxonomy、frozen records、complete ledger／manifest 與上游實驗證據逐 byte 未變。

### 12.4 正式 SHA-256

| 產物 | SHA-256 |
|---|---|
| Report | `12789f5b458fceeafc93ceead7f1dc65e54b32d72c06c5063b94a230d0386b7f` |
| Summary | `03169d8cbafb7e24f2e75210a7b6707a2c228216828df9dc35e949d1ab699b53` |
| Report builder | `c67148f5542427eaf601fc6c46eb0c929608eef3e5f58acc60f28a0e3ecc4a5e` |
| Audit findings | `ecae69602974d86e5725c3688be6c7a4543043176aa59b00508b181d303d0ed9` |
| Audit manifest | `4031f1780bf012fa07a3c2741107cacf27968d956cb5a8b90060fa1783d607e6` |

---

## 附錄：數字解讀注意事項

1. 百分比以 198 格為分母時，統一四捨五入至小數點後 1 位。
2. 分母為 0 的比較顯示 NA，不得計算或推論效果。
3. Mechanism tags 非互斥，不能直接相加。
4. Primary layer、outcome validity 與 Healer decision 是三種不同維度。
5. 23 格 conditional 是診斷候選，不是 23 次 rescue，也不是 23 條規則。
6. 175 格 abstain 是安全裁決，不是 175 次 Healer 執行失敗。
7. 31 格 algorithm reconstruction required 不屬於局部 deterministic repair。
8. 本報告不宣稱已完成 HumanEval+、H1、跨模型或跨 benchmark 驗證。
