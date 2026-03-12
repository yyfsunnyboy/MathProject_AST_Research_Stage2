/no_think
【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)`，生成根式化簡與四則運算題目。
依照 level 選擇難度：
- Level 1 (Easy): 根號化簡 (Simplifying Radicals)。只生成單一項需要化簡的根式（例如 `\sqrt{12}` 或 `\sqrt{2^5}`），不包含加減乘除。
- Level 2 (Normal): 同類方根的合併 (Combining Like Radicals)。只生成同類方根的加減法（例如 `2\sqrt{12} - \sqrt{27}`），不包含乘除法。
- Level 3 (Hard): 四則運算 (Four Arithmetic Operations)。包含根式的乘法分配律、展開與加減混合運算。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`


【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ✅ **必須** `import math`
   - ✅ **必須** `from fractions import Fraction`
   - ❌ **嚴禁** `import RadicalOps` 或是 `import FractionOps` (系統已自動注入，直接使用 `RadicalOps.xxx`)

2. **核心邏輯**：
   - 使用 `terms = [(coeff, radicand), ...]` 列表來儲存數學狀態。
   - **絕對禁止** 解析 LaTeX 字串來獲取數值（例如 `int(term.split(...))` 是被禁止的）。
   - 計算過程必須純粹基於整數操作 `(coeff, radicand)`。
   - 只有在最後一步（生成題目文字或答案文字）才調用 `RadicalOps` 進行格式化。

3. **函數介面**：
   ```python
   def generate(level=1, **kwargs):
       # ... logic ...
       return {
           'question_text': str,
           'answer': '',
           'correct_answer': str,
           'mode': 1
       }

   def check(user_answer, correct_answer):
       # 簡單比對字串即可
       correct = str(user_answer).strip() == str(correct_answer).strip()
       return {'correct': correct, 'result': '正確' if correct else '錯誤'}
   ```

【系統已注入的輔助函式（API）】（直接調用 `RadicalOps.xxx` 或 `FractionOps.xxx`）
- `RadicalOps.simplify_term(coeff, radicand)` → `(new_coeff, new_radicand)`
- `RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True)` → 未化簡格式化（題目用，支援 Fraction）
- `RadicalOps.format_expression(terms_dict, denominator=1)` → 最終答案（自動合併同類項、排序、LaTeX，支援 Fraction）
- `FractionOps.create(value)` → 建立分數
- `FractionOps.to_latex(frac, mixed=False)` → 分數轉 LaTeX

【核心規則】
1. **題目結構 (依據 Level)**：
   - Level 1: 單一未化簡根式，題目顯示：`化簡 $\sqrt{...}$`
   - Level 2: 3~4 項同類方根的加減，題目顯示：`化簡 $... + ... - ...$`
   - Level 3: 乘法分配律混合加減，題目顯示：`化簡 $(...) \times (...) + ...$` 或單純 `(...) \times (...)`
2. **數值範圍**：
   - 係數 `coeff`: -5 ~ 5 (非零)
   - 根號內 `radicand`: 2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75
     - 題目中的 `radicand` 必須包含這類「可化簡」的數（如 12, 18, 27, 50）。
     - 答案中的 `radicand` 必須是最簡根式（如 2, 3, 5...）。
3. **正確使用 format_expression**：
   - 必須傳入字典 `terms_dict = {radicand: total_coeff}`。
   - 嚴禁傳入列表或字串。
=== SKILL_END_PROMPT ===
