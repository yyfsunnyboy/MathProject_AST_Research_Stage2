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
   - ✅ **必須** `from fractions import Fraction` (若需要)
   - ❌ **嚴禁** `import IntegerOps` (系統已自動注入，直接使用 `IntegerOps.xxx`)

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

【核心規則】
1. **題目結構**：
   - Level 1: Part 1 + Part 2
   - Level 2: Part 1 - Part 2 + Part 3
   - Level 3: -Part 1 + Part 2 - Part 3 + K
2. **數值範圍**：
   - Level 1: -20 ~ 20
   - Level 2: -50 ~ 50
   - Level 3: -100 ~ 100
3. **格式化要求**：
   - 所有負數必須使用 `IntegerOps.fmt_num(n)` 包裹。
   - 題目中的乘號用 `\times`，除號用 `\div`。

=== SKILL_END_PROMPT ===

【強烈建議程式碼結構】
```python
import random
import math
# IntegerOps is injected automatically

def generate(level=1, **kwargs):
    # 1. Scaling
    if level == 1:
        r_min, r_max = -20, 20
        div_max = 10
    elif level == 2:
        r_min, r_max = -50, 50
        div_max = 20
    else:
        r_min, r_max = -100, 100
        div_max = 30
        
    def rand_nz(a, b):
        choices = [x for x in range(a, b+1) if x != 0 and x not in [1, -1]]
        if not choices: return 2
        return random.choice(choices)

    fmt = IntegerOps.fmt_num

    if level == 1:
        # Level 1: A / B or A * B
        op = random.choice(['*', '/'])
        if op == '*':
            a = rand_nz(-15, 15)
            b = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a)} \\times {fmt(b)}$$ 的值。"
            ans = a * b
        else:
            b = rand_nz(-15, 15)
            ans = rand_nz(-10, 10)
            a = b * ans
            question_text = f"計算 $${fmt(a)} \\div {fmt(b)}$$ 的值。"
            
    elif level == 2:
        # Level 2: A / B * C (Like user's example: 72 ÷ (-8) × 3)
        b = rand_nz(-15, 15)
        temp_ans = rand_nz(-15, 15)
        a = b * temp_ans  # Ensuring a / b is an integer
        
        c = rand_nz(-10, 10)
        
        # Decide order: A / B * C  or  A * B / C
        if random.choice([True, False]):
            question_text = f"計算 $${fmt(a)} \\div {fmt(b)} \\times {fmt(c)}$$ 的值。"
            ans = (a // b) * c
        else:
            # For A * B / C, ensure (A*B) is divisible by C
            c2 = rand_nz(-15, 15)
            ans2 = rand_nz(-10, 10)
            prod = c2 * ans2
            # Find factors for prod
            a2 = rand_nz(-10, 10)
            # Just do something simpler: A * B / C where B is divisible by C
            q = rand_nz(-5, 5)
            b2 = c2 * q
            a2 = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a2)} \\times {fmt(b2)} \\div {fmt(c2)}$$ 的值。"
            ans = a2 * (b2 // c2)

    else:
        # Level 3: A * B + C / D or A - B / C * D
        if random.choice([True, False]):
            a = rand_nz(-10, 10)
            b = rand_nz(-10, 10)
            d = rand_nz(-15, 15)
            q = rand_nz(-10, 10)
            c = d * q
            question_text = f"計算 $${fmt(a)} \\times {fmt(b)} + {fmt(c)} \\div {fmt(d)}$$ 的值。"
            ans = a * b + (c // d)
        else:
            a = rand_nz(-20, 20)
            c = rand_nz(-15, 15)
            q = rand_nz(-10, 10)
            b = c * q
            d = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a)} - {fmt(b)} \\div {fmt(c)} \\times {fmt(d)}$$ 的值。"
            ans = a - (b // c) * d

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}

❌ 輸出 Markdown 代碼塊 → 直接寫 code
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think