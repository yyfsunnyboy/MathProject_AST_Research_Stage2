```python
【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)`，生成整數四則運算題目。
題目結構必須為：括號內混合運算 + 絕對值 + (Level 3: 高難度多層混和)。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ✅ **必須** `import math`
   - ❌ **嚴禁** `import IntegerOps` (系統已自動注入，直接使用 `IntegerOps.xxx`)
   - ❌ **嚴禁** 引入 `fractions.Fraction` 或產生分數（本單元為整數四則運算）。

2. **核心邏輯**：
   - 使用標準 Python 運算生成數值。
   - **絕對禁止** 使用 `eval` 處理未經信任的字串（但可用 `IntegerOps.safe_eval`）。
   - 確保除法整除：先生成 `divisor` 和 `quotient`，再反推 `dividend`。

3. **函數介面**：
   ```python
   def generate(level=1, **kwargs):
       # ... logic ...
       return {
           'question_text': str,
           'answer': '',           # 必須為空字串，前端會自動處理
           'correct_answer': str,
           'mode': 1
       }

   def check(user_answer, correct_answer):
       # 簡單比對字串即可
       try:
           if str(user_answer).strip() == str(correct_answer).strip():
               return {'correct': True, 'result': '正確'}
           if float(user_answer) == float(correct_answer):
               return {'correct': True, 'result': '正確'}
       except:
           pass
       return {'correct': False, 'result': '錯誤'}
   ```

【系統已注入的輔助函式（API）】（直接調用 `IntegerOps.xxx`）
- `IntegerOps.fmt_num(n)` → 格式化數字（負數自動加括號，如 `(-5)`）
- `IntegerOps.safe_eval(expr)` → 安全計算表達式
- `IntegerOps.rand_nz(a, b)` → 隨機生成 a 到 b 之間的非零、非 ±1 整數

【核心規則】
1. **題目結構**：
   - Level 1: Part 1 + Part 2
   - Level 2: Part 1 - Part 2 + Part 3
   - Level 3: -Part 1 + Part 2 - Part 3 + K
2. **數值範圍**：
   - Level 1: -20 ~ 20
   - Level 2: -50 ~ 50
   - Level 3: -100 ~ 100
3. **格式化與 LaTeX 渲染要求**：
   - 所有負數必須使用 `IntegerOps.fmt_num(n)` 包裹。
   - 題目中的乘號用 `\times`，除號用 `\div`。
   - ⚠️ **極度重要**：最後的算式字串【必須】用雙錢號 `$$` 包起來，否則前端無法渲染！
     ✅ 正確範例：`question_text = f"計算 $${fmt(a)} \\times {fmt(b)}$$ 的值。"`
     ❌ 錯誤範例：`question_text = f"計算 {fmt(a)} \\times {fmt(b)} 的值。"`

