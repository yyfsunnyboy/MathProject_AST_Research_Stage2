# Stage2 通用鷹架 × 演算法鷹架 × 累積 Healer Validation 20 題預登錄規格 v2

> 版本日期：2026-07-25
> 專案：`MathProject_AST_Research_Stage2`
> 狀態：**草案，不可凍結**——前置條件（H4 完成並封存 H1→H2→H3→H4 累積管線）尚未滿足
> 本版取代 v1；v1 的 Existing600 母體描述、母體軸、Healer 規則順序與結果分類錯誤已於此修正

---

## 〇、與 v1 的差異摘要（本次審查修正項）

1. Existing600 母體重新寫對：60 tasks × 5 seeds × 2 prompts = 600（Ab1 300 + Ab2g 300）。
2. 本實驗改為正式 **Validation**，不是 development-only 探索；四個 prompt 全部在未見的
   Validation 20 題上新生成，不沿用 development 的 Ab1/Ab2g 輸出。
3. 新增模型軸：2B、4B 兩個模型皆須跑滿四個 prompt。
4. 設計名稱改為「2×2 Prompt factorial × paired Healer pre/post design」，不再稱 2×2×2。
5. 累積 Healer 補回 H3，正確順序為 Pipeline correction → H1 → H2 → H3 → H4 → EvalPlus。
6. 區分 `implementation_frozen_for_validation` 與 `qualification_status`。
7. Ab2gA 版本改用 `Ab2gA-factorial-v1`，與既有 `Ab2gA-short-v1` 明確區隔。
8. Raw 不再全面替換為 pipeline-corrected；Scaffold／Pipeline／Healer 效果分開列帳。
9. 八類結果改為非互斥的多維標籤系統。
10. `confirmed_algorithm_only_residual` 拆成四個子類別，僅後兩者可彙整為
    `confirmed_algorithmic_residual`。
11. 移除評測前唯讀動態觀察，改為正式 EvalPlus 執行後的 post-hoc 分析。
12. McNemar 改為描述性統計，並額外報告 unique task 層級的受益/受害計數。

---

## 一、研究問題（不變）

1. 通用方法論層級的演算法自我檢查提示，能否在生成前預先減少後續殘留的演算法層失敗？
2. 通用鷹架與演算法鷹架是否存在交互作用？
3. 累積版 Healer（H1→H2→H3→H4）在四種 prompt 條件、兩種模型規模下，造成的
   repair depth 與 execution transition 分佈為何？
4. 套用鷹架與 Healer 之後，殘餘失敗的組成如何隨條件改變？

**核心目標重申**：不以「全部通過」為成功定義，而是觀察殘餘失敗能否更乾淨地歸因為
演算法/語意層問題，而非結構性雜訊。

---

## 二、實驗設計

### 2.1 因子

| 因子 | 水準 |
|---|---|
| 通用鷹架 | 有 / 無 |
| 演算法鷹架 | 有 / 無 |
| 模型 | 2B / 4B |
| Healer 狀態 | Raw / Post-Healer（同一份程式的配對前後處理，非獨立生成） |

命名為 **2×2 Prompt factorial × paired Healer pre/post design**，並以 2 個模型各自重複。

### 2.2 Prompt 條件

| Prompt 條件 | 通用鷹架 | 演算法鷹架 |
|---|:---:|:---:|
| `Ab1` | ✗ | ✗ |
| `Ab2g` | ✓ | ✗ |
| `Ab2A` | ✗ | ✓ |
| `Ab2gA-factorial-v1` | ✓ | ✓ |

`Ab2gA-factorial-v1` = frozen `Ab2g` 原文 + frozen `Ab2A` 原文直接串接，中間空行分隔。
**不與既有 `Ab2gA-short-v1` 混用**——short-v1 保留給原本的 pilot，本實驗一律使用
factorial-v1，兩者不得互相替代或比較解釋交互作用。

### 2.3 資料規模

**正式 Validation，不沿用 development 資料**：

| 項目 | 規模 |
|---|---:|
| Validation tasks | 20（獨立、未參與任何規則開發的分區） |
| Seeds | 5 |
| Prompt 條件 | 4（Ab1／Ab2g／Ab2A／Ab2gA-factorial-v1） |
| 模型 | 2（2B／4B） |
| **Raw generations** | 20 × 5 × 4 × 2 = **800** |
| Post-Healer（配對，非獨立生成） | 800 |
| **主要評測帳目（Raw + Post-Healer）** | **1,600** |
| Pipeline-corrected | 另列，不計入額外生成數 |

Manifest 須列出這 20 題的確切 task IDs，並確認與 development（60 題）、
confirmatory（HumanEval+ 108 + MBPP+ 60）、sealed reserve（182）分區互斥。

### 2.4 生成參數（凍結）

| 參數 | 值 |
|---|---|
| 溫度 | 0.2（四條件、兩模型一致） |
| Seeds | 5（11 / 22 / 33 / 44 / 55） |
| 模型 | 2B、4B（版本號於生成前寫入 manifest） |
| Task 集合 | Validation 20 題（manifest 凍結 task ID 清單） |

---

## 三、鷹架文字（凍結版本）

### 3.1 通用鷹架（Ab2g）

```
Return exactly one complete Python source file.
Do not use Markdown code fences.
Do not include explanations, analysis, assertions, tests, print statements, example calls, or alternative implementations.
Implement the exact function name and parameter list required by the task.
Include every import required by the submitted program.
Do not rename or redefine the requested public function.
The response must begin with Python code and contain no text outside the source file.
```

### 3.2 演算法鷹架（Ab2A）——含第 5 點（已確認加入）

```
Before writing the final code, internally:
1. identify an algorithm that handles all valid inputs;
2. check important edge cases and index boundaries;
3. verify the return value and type;
4. mentally test one normal case and one edge case;
5. verify that every loop and recursive call has a guaranteed termination condition.
```

### 3.3 Ab2gA-factorial-v1

`Ab2g` 原文 + 空行 + `Ab2A` 原文，逐字串接，不精簡、不融合。

---

## 四、累積版 Healer 規則集（正確順序，凍結前置條件：H4 須先完成）

```
Pipeline correction
→ H1 entry-point unique arity-compatible alias
→ H2 module-level assert quarantine
→ H3 empty-suite pass insertion
→ H4 top-level demo/print quarantine
→ EvalPlus
```

| 規則 | qualification_status | implementation_frozen_for_validation | 備註 |
|---|---|:---:|---|
| H1 entry-point alias | development qualification 已通過（9 verified rescue, 0 regression） | 待設 true | |
| H2 module-assert quarantine | `development_candidate_not_frozen` | 待設 true | 71/91 blocker removed, 46 partial repair, 0 regression |
| H3 empty-suite pass insertion | `development_candidate_not_frozen` | 待設 true | parse_rescue=3, transformed_known_pass=0, preserved_known_pass=151, evalplus_executed=false, new_verified_rescue=0, new_execution_regression=not_evaluated |
| H4 top-level demo/print quarantine | **尚未正式建立、接入累積管線及封存** | **false（阻塞項）** | 需先完成 rule ID、檔案 SHA、guard 版本、順序登錄，才能寫入本規格 |

**`implementation_frozen_for_validation=true` 只代表「Validation 期間不得修改此規則」，
不代表規則已通過 qualification。是否升格為正式 frozen qualified rule，取決於本次
Validation 的結果，而非本規格文件的登錄動作。**

**本文件在 H4 完成封存前不可凍結執行。**

---

## 五、結果帳目（非互斥多維標籤，取代 v1 的八類互斥分類）

每個 cell（task × seed × prompt × model）記錄以下四組獨立維度，彼此可共存：

### 5.1 Healer decision

- `transformed`
- `abstained`

### 5.2 Execution transition（配對，Raw → Post-Healer）

- `PASS → PASS`
- `FAIL → PASS`
- `PASS → FAIL`（regression）
- `FAIL → FAIL`

### 5.3 Repair depth tags（可複選，非互斥）

- `parse_rescue`
- `blocker_removed`
- `executable_or_diagnosable`
- `partial_repair`

同一格可同時具備 `blocker_removed` + `partial_repair` + `executable_or_diagnosable`。

### 5.4 Rule trace

- `first_effective_rule`：依 H1→H2→H3→H4 順序，第一個實際觸發轉換的規則
- `rules_applied`：完整套用軌跡（可能多條規則依序作用於同一程式）

---

## 六、殘餘失敗分類（拆分自 v1 的 `confirmed_algorithm_only_residual`）

僅適用於 Post-Healer 仍為 FAIL 的 cell：

| 子類別 | 定義 | 是否計入 `confirmed_algorithmic_residual` |
|---|---|:---:|
| `generation_incomplete_residual` | 截斷、核心內容遺失、函式 body 僅 `pass`／`raise NotImplementedError` | 否——屬內容不完整/生成失敗，非演算法錯誤 |
| `algorithmic_runtime_residual` | 正式 EvalPlus 執行中記錄到的 timeout／RecursionError／IndexError | 是（需證據充分） |
| `semantic_algorithm_residual` | 結構完整、可執行，答案與規格不符，根因可定位於演算法邏輯 | 是（需證據充分） |
| `unresolved_intent_residual` | 需猜測作者意圖才能判斷正確修法 | 否——歸類為未解語意殘差，不併入 algorithmic residual |

無法歸入以上任一子類別者，標記為 `unresolved_residual`，不強行分類。

### 6.1 三種必報統計

1. **Algorithmic residual rate**：以全部 800 cells 為分母。
2. **Residual composition**：以 Post-Healer 仍失敗的 cells 為分母，四子類別 + unresolved 佔比。
3. **Algorithmic residual 實際格數**：原始計數，不換算比例。

「演算法錯誤數量下降」與「殘差更集中於演算法錯誤」是兩個不同主張，須分開報告，不得互相替代。

---

## 七、動態觀察原則（移除 v1 的評測前唯讀觀察例外）

不允許在正式 EvalPlus 之前另外執行候選程式以判定 timeout／exception。正確順序：

1. Prompt、Pipeline、Healer 全部凍結；
2. evaluator-blind 完成所有轉換；
3. 正式執行 EvalPlus；
4. 評測完成後，才使用 EvalPlus 執行過程中已記錄的 exception／timeout 資訊，
   進行 post-hoc residual taxonomy（第六節）；
5. 不得因 post-hoc 分析結果回頭修改任何規則。

無法在此原則下判定的案例，一律標記 `unresolved_residual`。

---

## 八、統計比較方式

### 8.1 主要比較維度（避免把全部差異算給 Healer）

| 比較 | 資料來源 | 回答的問題 |
|---|---|---|
| Scaffold 效果 | Raw first-attempt（各 prompt 條件間比較） | 鷹架本身對生成品質的影響 |
| Pipeline 責任 | Raw vs Pipeline-corrected | 格式/抽取層造成的差異，獨立列帳 |
| Healer 效果 | Pipeline-corrected vs Post-Healer | Healer 實際貢獻，排除 Pipeline 效果污染 |
| 完整系統（僅描述性） | Raw `Ab1` vs Post-Healer `Ab2gA-factorial-v1` | 端到端差異，但明確聲明不可全數歸因於 Healer |

### 8.2 McNemar 使用限制

- 同一 task 的 5 個 seeds 具群聚性，**不視為完全獨立樣本**。
- 主要報告：cell-level 通過率、discordant pairs 計數。
- 額外報告：**unique task 層級**的受益／受害 task 數（例如「20 題中有幾題因某條件由
  FAIL 轉 PASS」）。
- p 值僅作輔助描述，不作為正式顯著性推論依據。
- 交互作用（通用鷹架 × 演算法鷹架）維持描述性 difference-in-differences 呈現，
  不宣稱統計顯著性。

---

## 九、可以主張／不可以主張

### 可以主張（本輪完成後填入實際數據）

- 2B／4B 兩模型在 Validation 20 題、四種 prompt 條件下，Scaffold／Pipeline／Healer
  三層分開歸因的效果方向與幅度。
- H1→H4 累積管線在 800 配對帳目中的 repair depth 標籤分布與 execution transition 計數。
- Post-Healer 殘餘失敗的四子類別組成，以及 algorithmic residual rate 的條件間差異。
- Unique task 層級的受益／受害 task 數。

### 不可以主張

- 不可外推至 confirmatory 分區、其他模型規模或其他 benchmark。
- 不可宣稱 McNemar p 值代表獨立樣本下的正式統計顯著性。
- 不可宣稱交互作用效果具統計顯著性。
- 不可將 `algorithmic_runtime_residual` 的 post-hoc 觀察證據回頭用於觸發或調整 Healer 規則。
- 不可把 Pipeline 效果算進 Healer 貢獻，也不可把 Scaffold 效果算進 Healer 貢獻。
- 不可在 H4 未完成封存前執行本規格。
- 不可宣稱本輪已窮盡演算法鷹架或殘差分類的所有可能設計。

---

## 十、執行前置條件清單（阻塞項）

本規格**目前不可凍結執行**，須先完成：

1. **H4 top-level demo/print quarantine** 正式建立、接入 H1→H2→H3→H4 累積管線，
   並完成 rule ID、檔案 SHA、guard 版本登錄。
2. H1→H2→H3→H4 累積管線本身完成封存（`implementation_frozen_for_validation=true`）。
3. Validation 20 題 manifest 確認，列出確切 task IDs，並驗證與 development／
   confirmatory／sealed reserve 分區互斥。
4. 2B、4B 模型版本號確認並寫入 manifest。

以上四項全部完成後，本文件才可正式凍結並開始 800 次新生成。
