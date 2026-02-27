```python
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
- `IntegerOps.fmt_num(n)` → 格式化負數加括號。
- `IntegerOps.random_nonzero(min_val, max_val)` → 生成指定範圍內且「絕對不為 0」的整數。
- `IntegerOps.safe_eval(expr)` → 安全計算表達式

=== SKILL_END_PROMPT ===

# [[MODE:BENCHMARK]]
【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

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
        choices = [x for x in range(a, b+1) if x != 0]
        if not choices: return 1
        return random.choice(choices)

    # Part 1: Complex Division [(a*m + b) / divisor]
    divisor = rand_nz(2, div_max)
    quotient = rand_nz(-15, 15)
    dividend = divisor * quotient
    
    m = rand_nz(2, 5)
    a_approx = dividend // m
    if a_approx == 0: a_approx = 5
    a = rand_nz(a_approx - 5, a_approx + 5)
    b = dividend - (a * m)
    
    # 格式化 Part 1
    fmt = IntegerOps.fmt_num
    part1_str = f"[({fmt(a)} \\times {fmt(m)}) + {fmt(b)}] \\div {fmt(divisor)}"
    part1_val = quotient
    
    # Part 2: Absolute Value |d*e - f + g|
    d = rand_nz(-10, 15)
    e = rand_nz(-10, 10)
    f = rand_nz(1, 20)
    g = rand_nz(-10, 10)
    
    if level == 1:
        part2_str = f"|{fmt(d)} \\times {fmt(e)} - {fmt(f)}|"
        part2_val = abs(d * e - f)
    else:
        part2_str = f"|{fmt(d)} \\times {fmt(e)} - {fmt(f)} + {fmt(g)}|"
        part2_val = abs(d * e - f + g)

    # Part 3: Extra Term (h*i - j)
    h = rand_nz(-10, 10)
    i = rand_nz(2, 5)
    j = rand_nz(1, 10)
    part3_str = f"({fmt(h)} \\times {fmt(i)} - {fmt(j)})"
    part3_val = h * i - j
        
    # Final Assembly
    k = rand_nz(-50, 50)
    
    if level == 1:
        question_text = f"計算 $${part1_str} + {part2_str}$$ 的值。"
        ans = part1_val + part2_val
    elif level == 2:
        question_text = f"計算 $${part1_str} - {part2_str} + {part3_str}$$ 的值。"
        ans = part1_val - part2_val + part3_val
    else:
        question_text = f"計算 $$- {part1_str} + {part2_str} - {part3_str} + {fmt(k)}$$ 的值。"
        ans = -part1_val + part2_val - part3_val + k
        
    return {
        'question_text': question_text,
        'answer': '',       # 必須為空字串
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
❌ 輸出 Markdown 代碼塊 → 直接寫 code
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think        
[[END_MODE:BENCHMARK]]

[[MODE:LIVESHOW]]
[Role] 你現在是 MathProject 專案的 「核心架構設計師 (AI Architect)」。

[Task] 
1. 深入解析 {{TARGET_QUESTION}}，辨識其數學結構（如：多項式除法、根式化簡、分數混合運算）。
2. 參考本檔案 (SKILL.md) 的知識庫，產出一份給 Coder (Qwen) 的 Coding Spec JSON。
3. 你的任務是規劃「如何寫 Code」，而不是直接寫 Code。

[API 引用手冊] (僅限選用以下已注入工具)
- IntegerOps: 處理整數格式化 (.fmt_num) 與安全運算 (.safe_eval)。
- FractionOps: 處理精確分數 (.create) 與 LaTeX 轉換 (.to_latex)。
- PolynomialOps: 處理多項式係數運算 (.add, .mul) 與格式化 (.format_latex)。
- RadicalOps: 處理根式化簡 (.create) 與多項根式合併 (.format_expression)。

[輸出格式] 必須嚴格輸出 JSON：
{
  "skill_id": "請由題目特徵判定 (例如: jh_數學2上_FourOperationsOfRadicals)",
  "logic_spec": {
    "structure": "描述題目的數學邏輯結構",
    "steps": [
      "1. 使用 [特定API] 生成變數...",
      "2. 描述計算 ans 的純數值邏輯...",
      "3. 描述如何套用【實作模板】組合 question_text"
    ]
  },
  "injected_functions": ["填入本次需要的類別名稱，例如 ['RadicalOps']"]
}

[最高禁令] 
只准輸出 JSON，不准有任何前言、後語或 Python 代碼。
確保 `steps` 極致詳細，讓 Coder 看到後能直接在【實作模板】中填空。

[Coding Spec 細節提醒]
1. 轉義字元 (Escaping)：若要在 Python f-string 輸出 LaTeX 的 `\times` 或 `div`，只需提醒 Coder 寫 `\\times` 與 `\\div`，避免 Python 語法錯誤。例如：`f"{{fmt(a)}} \\times {{fmt(b)}}"`。
2. 動態工具注入：`injected_functions` 必須根據你在前處理階段判斷需要的功能，動態給出 List (如 `["FractionOps", "IntegerOps"]`)。
[[END_MODE:LIVESHOW]]