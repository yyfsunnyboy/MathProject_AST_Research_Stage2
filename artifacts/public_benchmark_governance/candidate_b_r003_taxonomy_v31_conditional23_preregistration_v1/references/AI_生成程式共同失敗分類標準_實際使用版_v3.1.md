---
title: AI 生成程式共同失敗分類標準（實際使用版 v3.1）
version: 3.1
date: 2026-07-21
status: common_codebook
---

# AI 生成程式共同失敗分類標準（實際使用版 v3.1）

> 適用範圍：CE115／Math16、MBPP+、HumanEval+，以及後續同類 Python 程式生成實驗  
> 文件性質：跨專案共同分類與裁決標準  
> 核心原則：分開記錄「在哪一層失敗、怎麼失敗、證據是否充分、責任屬於誰、Healer 是否應介入」  
> 版本相容：本版不覆寫任何既有 artifact、分類、統計、manifest、hash 或 frozen revision

---

## 0. 本版最重要的結論

1. L0–L5 主層級保持不變，不因個案複雜而任意增加 L6。
2. `UNRESOLVED` 不是新的失敗層，而是「已完成審查，但現有證據不足以閉合到單一 L0–L5」的合法裁決結果。
3. `PENDING_REVIEW` 是尚未完成審查，不能與 `UNRESOLVED` 混用。
4. 具體錯法放入 `mechanism_tags`；需要更多細節時增加 mechanism tag 或 unresolved reason code，不先增加主層級。
5. 已凍結或已完成正式裁決審查的資料不得覆寫。本版不觸發全面重新分類。
6. 只有取得新證據且足以改變個案判斷時，才建立新的 adjudication revision；舊 revision 永久保留。

---

## 1. 不可竄改與版本治理

### 1.1 不可覆寫的內容

- raw response、extracted candidate 與 candidate hash；
- first-attempt evaluator 結果；
- 舊分類、舊統計與原 evidence role；
- prompt、contract、toolbox、evaluator 與 rule-pack 版本；
- manifest、SHA-256、frozen revision 與 audit revision。

### 1.2 合法更新方式

| 情況 | 合法處理 |
|---|---|
| 只調整 codebook 用語或欄位對照 | 建立新版 codebook／crosswalk，不改舊資料 |
| 新 diagnostics 使根因可閉合 | 建立新的 adjudication revision，引用原始 cell 與新證據 |
| evaluator 有錯 | 建立 evaluation revision，以同一 raw artifact 重評 |
| prompt、任務契約或模型輸入改變 | 建立新 run，不得回填舊 run |
| Healer 規則改變 | 建立新 rule-pack revision；正式資料不得事後回填原結果 |

### 1.3 Stage2 既有97格治理範圍的相容聲明

- 原已凍結77格：不變。
- 新增20格：截至本文件起草時已通過 v2 final freeze audit；在正式 freeze／commit／push 完成前，不提前稱為已凍結。
- 上述77+20格的既有逐格分類、統計、manifest 與 SHA 均不因 v3.1 而改寫。
- 其中使用 `primary_layer=UNRESOLVED` 的資料是合法的既有 operational representation。
- v3.1 只提供語意澄清與欄位對照，不要求把這97格重新看一次。
- 只有新增20格正式 freeze／commit／push 成功後，才能更新為「已凍結97格、剩餘101格」。
- 後續未處理資料可依 v3.1 繼續裁決，但須沿用 repo 已凍結的 schema 與 immutable revision 慣例。

---

## 2. 每個 cell 必須分開記錄的六個維度

| 維度 | 問題 | 主要欄位 |
|---|---|---|
| Gate | 程式通過哪些正式檢查？ | G1–G4 |
| Failure layer | 最早可證明的失敗層在哪裡？ | `primary_layer` |
| Mechanism | 具體怎麼錯？ | `mechanism_tags`、`failure_subtype` |
| Evidence resolution | 已審完嗎？能否閉合至單一層？ | `classification_status`、`unresolved_reason_codes` |
| Responsibility | 結果能否公平歸因於模型？ | `outcome_validity` |
| Healer disposition | 是否應修、實際有無介入、結果如何？ | `healer_eligibility`、`healer_decision`、`healer_outcome` |

不得用一個詞同時代替六個維度。例如：

- `truncation` 是形成機制，不是固定層級；
- Entry-point 錯誤是 L2，但不代表一定可修；
- `UNRESOLVED` 表示證據不能閉合，不表示尚未分析；
- 修後 PASS 是 Healer outcome，不會改寫 raw first-attempt 的原始失敗層。

---

## 3. G1–G4 正式 Gate

| Gate | 名稱 | 判定內容 |
|---|---|---|
| G1 | Candidate／Parse | 是否取得唯一可判定的 Python candidate，且能建立 AST |
| G2 | Execution | 在凍結環境與限制內，是否能完成執行而無例外、逾時或非終止 |
| G3 | Contract | Entry point、signature、required API、return type、schema、packaging、canonical form 是否符合事前契約 |
| G4 | Correctness | 是否通過凍結的 oracle、公開／隱藏測試或 benchmark evaluator |

只有全部適用 Gate 均 PASS 才是 `final_status=PASSED`。不適用填 `NOT_APPLICABLE`；尚未能檢查填 `NOT_ASSESSED`。

G3 可拆為：

- `G3e`：entry point／signature；
- `G3a`：事前明定的 required API adoption；
- `G3s`：output schema／packaging；
- `G3c`：事前明定的 canonical form。

Gate 是判定條件，不代表 evaluator 程式只能依 G1→G2→G3→G4 的固定順序執行。例如 entry point 可在執行前檢查；output schema 通常要在執行後檢查。

---

## 4. 共同失敗層級 L0–L5

### L0：Infrastructure／Pipeline Failure

模型生成或評測流程未可靠完成，無法公平判定 candidate 能力。

常見機制：模型服務失敗、runner 中斷、raw response 遺失、寫檔失敗、系統資源錯誤、研究方 extractor／bridge 破壞合法輸出。

原則：

- `outcome_validity` 通常為 `INVALID_INFRASTRUCTURE`；
- 不送入 Healer；
- 若已有 raw response，而問題只發生在後續 extractor，仍須保存可觀察症狀與 failure chain，不得把模型錯誤與研究管線錯誤混帳。

### L1：Candidate／Parse／Syntax Failure

已有輸出，但無法取得唯一可判定的 Python candidate，或 candidate 無法建立 AST。

常見機制：`SyntaxError`、`IndentationError`、括號或字串未閉合、非法語法、無法排除的自然語言污染、多段候選無法選定、截斷後無法解析。

典型 Gate：`G1=FAIL`，G2–G4=`NOT_ASSESSED`。

注意：

- 只有無法解析才把 truncation 的結果歸 L1；
- Format 只有在阻止可靠 extraction／parse 時才是 L1；
- 看起來容易補一個括號，不代表語意安全，也不自動成為 Healer eligible。

### L2：Contract／Entry-point／Output Packaging Failure

candidate 可解析，但違反事前明確的介面或輸出契約。

常見機制：指定 entry point 缺失或名稱錯誤、signature 不符、return type／schema／key 不符、generator 與 list 契約不符、多包或少包一層、canonical form 違約、使用契約禁止的依賴。

Entry-point 固定歸 L2。即使 harness 最後拋出 `NameError` 或 `AttributeError`，只要根因是 required entry point 不符，就不能改歸 L4。

#### Entry-point 的 Healer 邊界

只有下列條件全部成立才可標 `eligible`：

1. 契約明文指定唯一 entry point 與 signature；
2. candidate 中恰有一個結構相容的安全候選；
3. 修法只是唯一 alias、rename 或薄 wrapper；
4. 不改函式主體、參數資料流與回傳內容；
5. 不使用 oracle、hidden tests、reference answer 或該格 PASS／FAIL；
6. 規則與正反例已在正式測試前凍結。

零個或多個合理候選、重複定義導致綁定不清、signature 無法唯一對應時，標：

```text
primary_layer = L2
mechanism_tags += entry_point_mismatch, ambiguous_entry_point
healer_eligibility = abstain
```

### L3：Domain API／Tool-use／Required Assembly Failure

程式誤用任務事前提供或要求的 Domain API、工具或正式 toolbox contract。

常見機制：Domain API import 路徑／名稱錯、API 名稱或 arity 錯、argument shape 錯、required API 未採用、選錯工具、本地重寫或遮蔽 required API、臆測回傳 schema、API 結果未接入必要資料流。

只有 API／tool 已在 prompt、toolbox 或 contract 中事前明定，才可使用 L3。不得在看過失敗後補設 required API。

Import 分流：

- import statement 本身無法解析 → L1；
- Domain API／tool 的 import 或使用錯誤 → L3；
- 一般 Python 標準庫、允許依賴或 candidate 自有 helper 的 missing import，執行時造成錯誤 → 通常 L4；
- 契約禁止外部依賴而模型仍使用 → 通常 L2 + `unauthorized_dependency`；
- runtime 缺少契約承諾提供的套件 → 依可見症狀記 chain，validity=`INVALID_INFRASTRUCTURE`。

### L4：Runtime／Control-flow／General Assembly Failure

candidate 可解析，且不存在更早可證明的 L2／L3 阻斷，但執行時因一般程式組裝、資料流、狀態或控制流程錯誤而失敗。

常見機制：一般 `NameError`、`TypeError`、`KeyError`、`IndexError`、`RecursionError`、非終止、execution timeout、未定義變數、錯誤資料結構取值、一般 missing import、錯誤參數來源、缺失 return path。

典型 Gate：`G1=PASS`、`G2=FAIL`；G3／G4 尚未完整判定。

### L5：Semantic／Algorithm／Answer Incorrect Failure

程式可解析、可執行、介面與輸出契約符合，但答案、公式或演算法未通過正式 correctness evaluator。

常見機制：公式錯誤、演算法錯誤、邊界條件漏處理、錯誤去重邏輯、順序判斷錯誤、硬編碼錯答、目標偏移、可執行但內容不完整。

典型 Gate：G1–G3=`PASS`、G4=`FAIL`，且 evaluator 已確認有效。

L5 原則上超出 deterministic Healer 邊界。需要重解題、依測試反推、改寫核心演算法或在多個合理方案中猜測者，一律 abstain。

---

## 5. `UNRESOLVED` 與 `PENDING_REVIEW`

### 5.1 正式定義

| 值 | 定義 | 是否已完成審查 | 是否屬 L0–L5 |
|---|---|---:|---:|
| `PENDING_REVIEW` | 尚未完成必要裁決，或等待既定審查程序 | 否 | 否 |
| `UNRESOLVED` | 已完成合法審查，但允許證據不足以閉合至單一 L0–L5 | 是 | 否；它是 resolution status |
| `L0`–`L5` | 證據足以支持單一 primary layer | 是 | 是 |

`sufficient evidence` 的意思是「足以做出合法裁決」，合法裁決可以是 `UNRESOLVED`；不等於一定足以閉合到 L0–L5。

### 5.2 何時使用 `UNRESOLVED`

至少符合：

1. 已核對允許使用的 raw source、公開契約與既定 machine signals；
2. 已排除只是尚未閱讀或漏做步驟；
3. 存在兩個以上仍合理的根因層，或缺少區分它們所需的合法證據；
4. 不允許靠猜測、hidden oracle 或事後答案硬判；
5. `failure_chain`、citations、confidence 與 abstain reason 均完整。

### 5.3 unresolved reason codes

- `insufficient_static_evidence`
- `runtime_vs_semantic_not_closed`
- `contract_vs_semantic_not_closed`
- `multiple_plausible_root_causes`
- `public_examples_non_discriminating`
- `diagnostic_execution_required`
- `artifact_incomplete_for_resolution`
- `contract_evidence_insufficient`

這些是證據缺口，不是新 failure layer。

### 5.4 Stage2 schema 相容

Stage2 已凍結 revision 可繼續使用：

```text
primary_layer = UNRESOLVED
```

共同語意解讀為：

```text
classification_status = ADJUDICATED
layer_resolution_status = UNRESOLVED
canonical_primary_failure_layer = null
```

這是衍生 crosswalk，不修改原 row。其他新系統若分欄實作，可用 `primary_failure_layer=null` 搭配 `layer_resolution_status=UNRESOLVED`；兩種表示法在合併時視為同義。

---

## 6. Truncation 是跨層 mechanism tag

| 截斷後結果 | Primary layer |
|---|---|
| 無法解析 | L1 |
| 可解析，但 required entry point／signature 缺失 | L2 |
| 可解析，但 Domain API／tool 片段錯誤 | L3（須有明確 API 證據） |
| 可解析，但執行時缺定義、return path 或資料流 | L4 |
| 可執行且 contract 正確，但演算法／case coverage 不完整 | L5 |

規則：

- `truncation` 不參與 L0–L5 互斥計數；
- 只有明確證據才用 `truncation`，否則用 `possible_truncation`；
- 不再宣稱「截斷補全是安全 Healer」；
- 截斷通常代表內容遺失，補全需要猜測，因此原則上 abstain；
- 未來若提出極窄且可證明唯一、不加入新語意的規則，須建立新 rule ID、安全證明、反例測試與 validation，不能回寫既有結果。

---

## 7. Format／Packaging、Import 與例外名稱

### 7.1 Format／Packaging

| 可觀察症狀 | 分類 |
|---|---|
| 程式外文字、多候選、抽取邊界導致無法可靠 parse | L1 |
| 可解析但 callable、signature、return schema、容器或 canonical form 違約 | L2 |
| 研究方 extractor／包裝器破壞合法輸出 | 依症狀記 L0／L1／L2 chain；validity 指向 infrastructure |

### 7.2 Import

不得建立一個不分情境的 `Import Error` 主類別。依來源分流至 L1、L2、L3 或 L4，並用 mechanism tag 保留具體錯法。

### 7.3 Exception type 不是 root cause

看到 `NameError`、`AttributeError` 或 `TypeError` 不得直接判 L4。必須先問：

1. 是否因 required entry point 不符？若是 → L2。
2. 是否因 Domain API／tool 契約誤用？若是 → L3。
3. 是否為一般 candidate 執行與資料流問題？若是 → L4。
4. 現有證據無法區分？完成審查後 → `UNRESOLVED`；尚未審查 → `PENDING_REVIEW`。

---

## 8. Mechanism tag 共同字典

Mechanism tags 可多選、可跨層，但不能代替 primary layer。

| 類群 | 建議標籤 |
|---|---|
| 產出完整性 | `truncation`, `possible_truncation`, `code_bloat` |
| 擷取／語法 | `format_contamination`, `candidate_extraction_failure`, `multiple_candidates`, `syntax_error`, `indentation_error` |
| Contract | `entry_point_mismatch`, `ambiguous_entry_point`, `signature_mismatch`, `return_type_mismatch`, `generator_vs_list`, `output_packaging`, `schema_mismatch`, `canonical_form_mismatch`, `unauthorized_dependency` |
| Domain API | `domain_api_import_error`, `invalid_api_call`, `wrong_argument_shape`, `tool_routing_failure`, `local_api_shadowing`, `partial_adoption`, `return_shape_hallucination`, `api_result_disconnected` |
| Runtime | `general_missing_import`, `undefined_name`, `arity_error`, `wrong_parameter_source`, `control_flow_failure`, `recursion_failure`, `nontermination`, `execution_timeout`, `state_mutation_error` |
| Semantic | `algorithmic_error`, `incorrect_formula`, `edge_case_omission`, `hardcoded_wrong_answer`, `dedupe_instead_of_unique_occurrence`, `order_sensitive_counter`, `semantic_goal_drift`, `algorithm_reconstruction_required` |
| Pipeline／治理 | `pipeline_extraction_error`, `prompt_api_mismatch`, `evaluator_error`, `answer_leak`, `needs_human_review` |

新增 tag 的條件：定義清楚、能與既有 tag 區分、至少有一個可引用案例、不得暗示未被證明的根因、不得改變舊 tag 的語意。

---

## 9. outcome_validity

`outcome_validity` 記錄責任歸因，不是 failure layer。

| 值 | 定義 | 模型主統計 |
|---|---|---|
| `VALID_MODEL_OUTCOME` | 契約、evaluator、infrastructure 有效，結果可歸因於模型 | 納入 |
| `INVALID_EVALUATOR` | oracle、測試、正規化或判分錯誤 | 排除並建立 revision |
| `INVALID_CONTRACT` | prompt、API、schema 或任務契約錯誤／矛盾 | 排除並修正契約 |
| `INVALID_INFRASTRUCTURE` | 服務、runner、extractor、序列化或環境故障 | 排除或另列 ITT |
| `PENDING_REVIEW` | 尚未完成 validity 裁決 | 暫不納入 |

`UNRESOLVED` 可以同時是 `VALID_MODEL_OUTCOME`：代表這確實是有效的模型失敗，只是現有證據不足以確定根因層。不得因 layer unresolved 就自動把 validity 改成 pending。

---

## 10. Failure chain

`failure_chain` 記錄同一 cell 在 raw、pipeline correction、diagnostics、post-Healer 或 evaluator revision 中依序暴露的問題。

失敗且已完成裁決的 cell 最低要求：

- `failure_chain` 非空且有順序；正式 PASSED 且沒有階段轉移的 cell 可為空陣列；
- 每一節點包含 stage、layer／resolution、gate、mechanism、validity 與 evidence citation；
- raw primary layer 永遠保留；
- 修掉前層後暴露的新問題加入 chain，不回寫 raw first-attempt；
- partial gate progress 不等於 verified rescue。

範例：

```json
[
  {"stage":"raw_first_attempt","layer":"L4","gate":"G2","mechanism":"wrong_parameter_source"},
  {"stage":"post_diagnostic","layer":"L2","gate":"G3s","mechanism":"schema_mismatch"},
  {"stage":"post_healer","layer":null,"gate":"G1-G4","final_status":"PASSED"}
]
```

---

## 11. Healer eligibility、decision 與 outcome

### 11.1 目前共同 operational 欄位

為與已凍結 Stage2 資料相容，`healer_eligibility` 使用：

| 值 | 意義 |
|---|---|
| `eligible` | 已有唯一、局部、answer-free、凍結規則，可安全嘗試轉換 |
| `conditional` | 只有在額外明確 guard／契約證據成立時才可能修；不得直接視為已可修 |
| `abstain` | 不符合安全介入條件，Healer 應拒絕修改 |

若某專案另拆 `eligibility` 與 `decision`，可用衍生欄位，但不得回寫舊值。建議：

- `healer_decision`：`transformed`, `abstained`, `no_trigger`, `rejected`, `not_run`；
- `healer_outcome`：`rescue_to_pass`, `changed_partial_progress`, `preserved_pass`, `unchanged_fail`, `regression`, `rollback`, `not_assessed`。

### 11.2 Eligibility 十項必要條件

Local、Deterministic、Answer-free、Task-agnostic、Unique／Conservative、Invariant-supported、Tested、Frozen、Evaluator-blind、Re-evaluated。

任一條不成立，預設 abstain。`conditional` 只能記錄明確 guard 尚未閉合的候選，不得為了保留希望而使用。

### 11.3 各層原則

| Layer／狀態 | Healer 原則 |
|---|---|
| L0 | 不送 Healer |
| L1 | 只有唯一且可證明不加入新語意的凍結規則才可能 eligible；truncation 原則上 abstain |
| L2 | 主要候選區，但 entry point、container、schema 仍需契約明確且修法唯一 |
| L3 | 只有事前契約清楚、局部且唯一的 API 接線錯誤才可能 eligible |
| L4 | 只有機械、局部、唯一的 runtime／assembly 修法才可能 eligible；需重建流程者 abstain |
| L5 | 原則上 abstain；不得用 deterministic Healer 重新解題 |
| UNRESOLVED | 在根因與安全修法未閉合前預設 abstain |

修後必須重跑相同版本的全部適用 G1–G4。只有 FAIL→PASS 且無其他回歸，才是 `rescue_to_pass`。

---

## 12. 共同裁決流程

```text
0. 鎖定 cell 身分、raw artifact、prompt、contract、runtime、evaluator revision 與允許證據。

1. 審查是否尚未完成？
   是 → PENDING_REVIEW，不提前猜 layer。

2. infrastructure 是否有效？
   否 → L0；outcome_validity=INVALID_INFRASTRUCTURE。

3. 是否取得唯一且可解析 candidate？
   否 → L1；若截斷，加 truncation。

4. G3e entry point／signature 是否符合？
   否 → L2；唯一安全候選才可能 eligible，多候選則 ambiguous + abstain。

5. 執行是否成功？
   否 →
      Domain API／tool 證據充分：L3；
      一般 runtime／assembly 證據充分：L4；
      兩者或其他根因無法區分：完成審查後 UNRESOLVED。

6. 執行後 schema／packaging／canonical form 是否符合？
   否 → L2。

7. required API 是否事前明定且符合？
   否 → L3。

8. correctness 是否通過？
   否 → 先排除 evaluator／contract 問題；證據充分才標 L5，否則 UNRESOLVED。

9. 全部適用 Gate PASS → PASSED。

10. 獨立判 outcome_validity、mechanism tags、failure_chain 與 Healer disposition。
```

---

## 13. 每格最小資料欄位

```json
{
  "dataset": "MBPP+",
  "task_id": "Mbpp/123",
  "program_id": "...",
  "source_sha256": "...",
  "model": "qwen3.5:9b",
  "condition": "Candidate_B/H0",
  "seed": 11,
  "evidence_role": "development",
  "run_id": "...",
  "evaluator_revision": "...",

  "g1_parse": "PASS",
  "g2_execution": "NOT_ASSESSED",
  "g3_contract": "NOT_ASSESSED",
  "g4_correctness": "NOT_ASSESSED",

  "classification_status": "ADJUDICATED",
  "primary_layer": "UNRESOLVED",
  "mechanism_tags": [],
  "unresolved_reason_codes": ["runtime_vs_semantic_not_closed"],
  "failure_chain": [],
  "outcome_validity": "VALID_MODEL_OUTCOME",
  "confidence": "LOW",
  "evidence_citations": [],

  "healer_eligibility": "abstain",
  "eligibility_reason": "根因與唯一安全修法均未閉合。",
  "healer_decision": "not_run",
  "healer_outcome": "not_assessed",

  "adjudication_identity": "AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW",
  "adjudication_revision": "...",
  "notes": ""
}
```

不同專案欄位名若已凍結，可建立 crosswalk view，不必改 schema。跨專案合併時至少要能對應 identity、G1–G4、primary layer／resolution、mechanisms、validity、failure chain、Healer disposition 與 evidence role。

---

## 14. 統計與報告規則

至少分開報告：

- dataset、model、condition、seed policy；
- historical development、development、validation、confirmatory、post-hoc exploratory；
- evaluator／contract／rule-pack revision；
- raw observed、pipeline-corrected、post-Healer；
- L0–L5 互斥分布；
- `UNRESOLVED` 與 `PENDING_REVIEW`；
- outcome validity；
- mechanism tags 非互斥分布；
- eligible、conditional、abstain；
- transformed、rescue、partial progress、preserved pass、regression。

重要分母規則：

1. L0–L5 相加時不得加入 `UNRESOLVED`、`PENDING_REVIEW` 或重疊 mechanism tags。
2. Mechanism tags 每格可多標，總數可大於 cell 數。
3. source、program、cell、task 是不同分析單位，不得把20個 source-level units 說成20個獨立 tasks。
4. 只把完成裁決且 validity 合法的資料納入對應模型主分析；排除量必須明列。
5. Development 結果可以報，但不得冒稱 validation／confirmatory 泛化證據。

---

## 15. 舊資料 crosswalk 與是否需要重分類

### 15.1 不需要重分類的情況

- 只是把 `primary_layer` 對應到 `primary_failure_layer`；
- 把 frozen `UNRESOLVED` 解讀為 adjudicated-but-not-layer-closed；
- 新增 mechanism tag 顯示欄位，但不改原判斷；
- 把既有 `eligible／conditional／abstain` 映射到分析表；
- 增加版本說明、欄位別名或報告用衍生 view。

### 15.2 需要建立新 adjudication revision 的情況

- 原判斷與已存在證據矛盾；
- 新 diagnostics 使 `UNRESOLVED` 可以閉合；
- evaluator／contract 先前有錯；
- 原本把 L2、L3、L4、L5 判錯；
- 新 evidence 會實質改變 Healer eligibility 或 abstain 理由。

即使需要重裁決，也只重裁決受影響 cells，並建立新 revision；不能整批覆寫或把新版結果偽裝成原始結果。

### 15.3 何時才考慮新增主層級

必須同時符合：

1. 根因已明確，不是證據不足；
2. L0–L5 都確實容納不了；
3. 在 CE115、MBPP+、HumanEval+ 中重複出現；
4. 新層級會實質改變 evaluator、責任歸因或 Healer 邊界；
5. 經跨專案方法學審查與版本化遷移。

目前不符合，因此 v3.1 不新增 L6。

---

## 16. 跨專案一致性審查

1. 使用共同 training examples 校準標註者，不用 confirmatory 個案當教學材料。
2. 固定抽樣比例，由兩名標註者獨立判定。
3. 先看 raw、contract、Gate evidence 與 exception，不先看 Healer 最終是否救回。
4. 保存 machine label、reviewer A、reviewer B、disagreement 與 adjudication。
5. 報百分比一致率；樣本與類別數足夠時再報 Cohen's kappa。
6. 證據不足時合法使用 `UNRESOLVED`，不得為提高一致率硬塞 L4 或 L5。
7. 正式凍結後的新規則只屬 vNext／post-hoc exploratory，不回填原 confirmatory。

---

## 17. Stage2 legacy census 鎖定與 crosswalk

下列是既有歷史普查數字，不因 v3.1 改名或重算：

| Legacy category | 既有數量 | v3.1 處理 |
|---|---:|---|
| Format／packaging | 68 | 不能整批映射；阻止 extraction／parse 才是 L1，介面／schema 違約為 L2 |
| Syntax | 60 | 通常對應 L1，但只有 G1 FAIL 的逐格證據才能正式 crosswalk |
| Entry-point 安全候選 | 42 | L2；仍須逐格通過唯一安全候選 guard 才是 eligible |
| Entry-point 模糊候選 | 4 | L2 + `ambiguous_entry_point`；abstain |
| Import 明確證據 | 0 | 只代表該次普查沒有可計數的明確證據，不代表模型從未出現 import 問題 |
| Unknown | 275 | 不直接映射 L5；完成審查後可為 L0–L5 或 UNRESOLVED |
| Truncation | 80 | 重疊 mechanism tag，不加入互斥類別總和；原則上 abstain |

禁止事項：

- 不把 Truncation 80 加入其他互斥類別求和；
- 不把 Unknown 275 直接改名為 L5 或 UNRESOLVED；
- 不在未逐格重審下任意拆分 Format／packaging 68；
- 不因 Entry-point 都屬 L2，就把安全候選與模糊候選合併；
- 不把 crosswalk 衍生表當成當時原始分類。

---

## 18. v3.1 共同研究敘述

> 本研究以 G1–G4 判定 AI 生成 Python 程式在 candidate／parse、execution、contract 與 correctness 各 Gate 的表現，以 L0–L5 記錄有充分證據支持的主要失敗層，並以 mechanism tags 描述截斷、entry point、import、資料流與演算法等具體錯誤機制。`UNRESOLVED` 表示個案已完成審查，但現有合法證據不足以閉合至單一失敗層；它不同於尚未審查的 `PENDING_REVIEW`，也不是新的 L6。`outcome_validity`、`failure_chain` 與 Healer eligibility／decision／outcome 分開記錄，使 CE115、MBPP+ 與 HumanEval+ 能在不覆寫既有 artifact、frozen revision 與舊統計的前提下進行共同分析。

---

## 19. 版本差異

### v3.1（2026-07-21）

- 明確區分 `UNRESOLVED` 與 `PENDING_REVIEW`。
- 明定 `UNRESOLVED` 是裁決／證據解析狀態，不是 L6。
- 接受 Stage2 frozen schema 的 `primary_layer=UNRESOLVED`，並提供 canonical crosswalk。
- 保留 operational `eligible／conditional／abstain`，避免為欄位理想化而改寫既有資料。
- 新增 unresolved reason codes 與更多 mechanism tags。
- 明文保護 Stage2 既有77格 frozen revision 與新增20格已通過 final audit 的 revision，不觸發全面重分類，也不提前宣布97格已凍結。
- 規定只有新證據改變實質判斷時，才對受影響 cell 建立新 adjudication revision。

### v3（2026-07-20）

- 固定 L0–L5、G1–G4、`outcome_validity` 與 `failure_chain`。
- Truncation 改為跨層 mechanism tag，原則上 abstain。
- Entry-point 固定歸 L2；唯一安全候選與 ambiguous 候選分流。
- Import 依 Domain API／tool 與一般 runtime 問題分流。
- Format／packaging 依最早 Gate 拆為 L1 或 L2。

---

## 20. 最終執行口訣

> **先看 Gate，再判 Layer；具體錯法放 Tag；證據不足可 UNRESOLVED；責任另看 Validity；能不能修另過 Healer safety gate；所有新版判斷都建立 revision，不覆寫舊結果。**
