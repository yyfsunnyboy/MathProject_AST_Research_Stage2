---
name: math-problem-generator
version: v0.6
status: Iterating
description: 國中根式化簡題目生成器 (Based on RadicalOps)
last_successful_model: Gemini Flash / Qwen 14B (Ab2/Ab3)
---

# Skill: 國中根式化簡題目生成器 (jh_數學2上_FourOperationsOfRadicals)

## 核心任務
將使用者的需求轉換為一段 **Python 程式碼**，執行後能生成一道「根式化簡題目」。
該程式碼必須是 **Standalone (可獨立執行)** 的，並包含正確的答案計算邏輯。

## 生成規範 (Spec)
- **題目結構**：`(多項未化簡根式加減括號) + (簡單乘法結構)`
- **主要特徵**：
    - 題目顯示 **未化簡** 形式 (Unsimplified)
    - 答案必須是 **已化簡** 最簡根式 (Simplified)
    - 運算符號與數字必須符合 LaTeX 格式 ($...$)
- **工具限制**：
    - 必須使用系統注入的 `RadicalOps` 工具
    - 嚴禁自行實作 `gcd`, `sqrt` 等邏輯
    - 嚴禁 `import RadicalOps` (因為是注入的)

## 參考例題 (Reference)
**目標是以此結構為模板：**
化簡 $(\sqrt{18} + \sqrt{50} - 2\sqrt{8}) + 3(\sqrt{12} + \sqrt{27})$

## 唯一允許的工具 (API)
1. `RadicalOps.simplify_term(coeff, radicand) -> (c, r)` : 化簡单項
2. `RadicalOps.format_term(coeff, radicand, is_first=True)` : 格式化 (化簡後)
3. `RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True)` : 格式化 (未化簡)
4. `RadicalOps.format_expression(terms_dict, denominator=1)` : 組合最終答案

## 核心規則 (Rules)
1. **結構強制**：第一部分 3~4 項 (未化簡)，第二部分 小整數 $k \times (\sqrt{a} \pm \sqrt{b})$。
2. **格式對應**：題目用 `format_term_unsimplified`，答案計算過程用 `simplify_term`。
3. **字串串接**：禁止使用 `.join()` 處理複雜符號，建議使用 `+=` 或 `f-string` 並注意 `is_first` 參數。
4. **輸出淨化**：只輸出 Python Code，不包含 Markdown 標記或解釋文字。
5. **Validation**: 必須實作 `def check(user_ans, correct_ans) -> bool` 以驗證答案正確性。

## 當前問題紀錄 (Known Issues)
- [x] **v0.5**: `join` 導致的 `++` 運算符問題 (已由 Healer 修復)
- [x] **v0.5**: Hardcode 數字問題 (已由 Ab3 Prompt 強制 `random` 修復)
- [ ] **v0.6**: 偶爾出現 `clean_latex_output` 未定義 (需確保注入)

## 評估指標 (Metrics)
| Metric | Target | Description |
| :--- | :--- | :--- |
| **Pass Rate** | > 95% | Code runs without syntax/runtime errors |
| **MCRI Score** | > 9.0 | Correctness + Formatting compliance |
| **Healer Fixes** | < 2 | Number of automated fixes required |

## Appendix: Golden Prompt Template (V3.0)

以下是經過驗證的最佳 Prompt 結構，建議所有新技能開發都遵循此模板。

```markdown
【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)`，生成 [技能名稱] 題目。
返回 dict: {'question_text': str, 'correct_answer': str, 'answer': str, 'mode': 1}

【必要函數】
1. `def generate(level=1, **kwargs)`: 主生成邏輯
2. `def check(user_ans, correct_ans) -> bool`: 驗證答案 (MCRI Score 關鍵)
   - 範例:
     try:
         val_user = eval(str(user_ans).replace("^", "**").replace("{", "(").replace("}", ")"))
         val_corr = eval(str(correct_ans).replace("^", "**").replace("{", "(").replace("}", ")"))
         return abs(val_user - val_corr) < 1e-6
     except:
         return str(user_ans).strip() == str(correct_ans).strip()

【參考例題】
[在此貼上具體的 LaTeX 題目範例]

【可用工具】
(根據題型選擇 A 或 B)

[Option A: 系統注入工具 (推薦用於複雜題型)]
- RadicalOps / PolynomialOps (系統已注入，直接調用)
- 嚴禁 import 或重新定義

[Option B: 自包含工具 (推薦用於簡單題型)]
- 允許 import random, math, fractions
- 所有輔助函式 (如 to_latex, fmt_num) 必須寫在 generate() 內部

【核心規則】
1. **結構規範**：嚴格遵守參考例題的數學結構。
2. **格式規範**：題目必須用 $...$ 包裹數學式。
3. **驗證規範**：必須實作 check() 函數。
4. **輸出淨化**：只輸出 Python Code，不包含 Markdown 標記。
5. **程式碼結構**：
   - 使用 `while True` 包裹生成邏輯以支援重試 (Retry Logic)。
   - 避免使用 `input()` 或危險函數。

【程式碼結構範例】
def generate(level=1, **kwargs):
    # 1. 定義內部輔助函式 (若需要)
    def inner_tool(): pass
    
    while True: # Retry Loop
        try:
            # 2. 生成參數
            # 3. 計算答案
            # 4. 格式化輸出
            return {...}
        except:
            continue
            
def check(user, ans):
    # 驗證邏輯
    pass
```
