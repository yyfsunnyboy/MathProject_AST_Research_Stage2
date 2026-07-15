# 公開 Benchmark Healer-vNext 最終中文總結

- 日期：2026-07-15（Asia/Taipei）
- 對象：Qwen8B 公開 HumanEval / MBPP fail→fail 取證與 targeted official EvalPlus counterfactual replay
- 性質：deterministic Healer 邊界驗證；**不回填**原始 pass@1；**不宣稱**整體 benchmark 提升

## 1. Fail→fail 母體與 eligibility

| 項目 | 數值 |
|---|---:|
| fail→fail 母體 | **154**（HumanEval 38 + MBPP 116） |
| eligible | **18** |
| ineligible | **134** |
| uncertain | **2**（Mbpp/233、Mbpp/732） |

公開 benchmark 上可安全做局部、唯一、deterministic、無需 reference answer 的干預窗口很窄；大多數殘差仍屬邊界外的語意／演算法錯誤。

## 2. 已驗證規則（regression-safe）

1. **duplicate keep-LAST**：模組層同名函式保留最後一個定義（對齊 Python binding／常見 LLM self-correction）。
2. **referenced stdlib import preservation**：保留仍被引用的 import／fence 清理不得刪掉被用到的名稱。
3. **benchmark XOR preservation**：預設 `domain_mode=benchmark` 不將 BitXor `^` 改寫成 `**`；僅 `math_generator` 保有舊轉換。
4. **benchmark safety-loop preservation**：預設不把 `while True` 改成固定次數迴圈／合成 `return`；逾時由 evaluator 負責，不作 AST 語意改寫。

Math 出題路徑仍可透過 `ASTHealer(..., domain_mode="math_generator")` 保留舊行為。

## 3. 官方 targeted replay 最終累積

合併兩批 counterfactual official EvalPlus（三題 import／keep-LAST + 六題 XOR／safety-loop）：

| 分類 | 累積 |
|---|---:|
| official full rescue | **1**（Mbpp/255） |
| official base-regression recovery | **3**（Mbpp/410、Mbpp/6、Mbpp/633） |
| structural/runtime-semantics recovery only | **5**（Mbpp/279、Mbpp/311、Mbpp/735、HumanEval/39、Mbpp/739） |
| Candidate regression versus Raw | **0** |

本批 XOR／safety-loop 六題結果：

| 題目 | Candidate 分類 |
|---|---|
| Mbpp/6 | official base-regression recovery |
| Mbpp/311 | structural/runtime-semantics recovery only |
| Mbpp/633 | official base-regression recovery |
| Mbpp/735 | structural/runtime-semantics recovery only |
| HumanEval/39 | structural/runtime-semantics recovery only |
| Mbpp/739 | structural/runtime-semantics recovery only |

## 4. 分類語意區分

- **full rescue**：Candidate 官方 base 與 plus 皆 pass。
- **base-regression recovery**：相對 Original Ab3 回復 official base pass，但 plus 仍 fail。
- **structural/runtime-semantics recovery only**：消除結構／runtime 破壞（例如錯誤操作符改寫、危險迴圈改寫、重複 entry_point 的 keep-LAST），但官方 base 仍 fail 或與 Raw 同為 pass/fail 而無满分救援。
- **semantic error outside boundary**：原始解本身邏輯錯；保守 Healer 規則不負責也不應改寫為「猜答案」。

## 5–6. 證據邊界

- targeted cases **不回填**歷史官方 workbook／原始 pass@1。
- **不宣稱**整體 HumanEval／MBPP pass@1 提升。
- Candidate 對 Raw 無 regression（本批六題 Candidate base/plus 皆與 Raw 對齊）。

## 7. 結論

公開 benchmark 的 **deterministic intervention window 很窄**。Healer-vNext 在公開程式碼基準上的主要價值，是：

1. **regression prevention**（避免 Healer 自己把能跑／能過 base 的解弄壞）；
2. **runtime-semantics preservation**（保留 Python 真實運算與控制流語意）。

它不是廣域 pass@1 拉升器；大多數 fail→fail 殘差仍落在邊界外的語意錯誤。

## 證據路徑

- 三題 import／keep-LAST：`artifacts/fail_to_fail_forensics/healer_vnext_evalplus_replay/`
- XOR／safety-loop：`artifacts/fail_to_fail_forensics/xor_safetyloop_validation/`
- 複核分類：`artifacts/fail_to_fail_forensics/qwen8b_forensic_reviewed.csv`
