```python
【角色】K12 數學演算法工程師

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

【任務】
實作 `def generate(level=1, **kwargs)`，生成整數四則運算題目。
題目結構必須為：括號內混合運算 + 絕對值 + (Level 3: 高難度多層混和)。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

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
[Role] MathProject 動態出題引擎

[範例題型] {{OCR_RESULT}}

[核心策略]
小模型在遇到各種未知結構 (絕對值、括號、巢狀) 時，如果給出太死板的範例容易「背答案」。
請採用 **「積木組裝替換法 (Lego Block Assembly)」**，並嚴格遵守以下安全規範：
**絕對禁止在 `eval()` 內直接執行 `abs()`，以避開 Sandbox 錯誤。**

1. **化整為零 (Divide and Conquer)**：
   - 不要試圖寫一個巨大的 `ans = eval(...)`。
   - 看到 `|絕對值|`，就獨立寫一行算出 `val_abs = abs(eval("..."))`。
   - 看到 `[中括號]`，就獨立寫一行算出 `val_bracket = eval("...")`。
   - 看到 `(小括號)`，也獨立寫一行算出 `val_paren = eval("...")`。

2. **變數拼裝 (Variable Assembling)**：
   - 最後把算出來的 `val_abs`, `val_bracket` 等這些「積木」，用 f-string 拼湊成最終算式 `ans = eval(f"{val_abs} + {val_bracket}")`。

3. **暴力重試 (Retry Loop)**：
   - 依然保留 `for` 迴圈機制，利用 CPU 快速試錯來保證整除。

[實作範例：通用骨架 (請根據 {{OCR_RESULT}} 的實際結構自由變形)]
```python
import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    # [Step 1: 定義重試迴圈]
    # 不管題目長短，直接跑 3000 次測試
    for _ in range(3000):
        
        # [Step 2: 隨機生成變數 (依據範例題型有幾個數字就生成幾個)]
        # v1: 主數值，範圍大
        v1 = IntegerOps.random_nonzero(-20, 20) 
        
        # v2: 乘除因子，範圍小但包含負數 (增加難度！)
        v2 = IntegerOps.random_nonzero(-9, 9)   
        
        # v3, v4, v5: 混合使用，讓題目充滿變化
        v3 = IntegerOps.random_nonzero(-15, 15)
        v4 = IntegerOps.random_nonzero(-9, 9)
        v5 = IntegerOps.random_nonzero(-10, 10)
        
        # [Step 3: 隨機生成運算符 (依據範例題型有幾個符號就生成幾個)]
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '/'])
        # ... 依此類推
        
        try:
            # [Step 4: 積木組裝替換 (Lego Block Assembly)]
            # 這裡只是一個概念展示！請依照你目前看到的範例題型，靈活組裝！
            
            # 假設範例題型裡有一個絕對值區塊
            # val_abs = abs(eval(f"({v1}) {op1} {v2}"))
            
            # 假設範例題型裡有一個中括號區塊 (把算好的絕對值塞進去)
            # val_bracket = eval(f"{v3} {op2} {val_abs}")
            
            # 最終答案組合
            # ans = eval(f"({v1}) * {val_bracket} + {v3}") 
            
            # ---------------------------------------------------------
            # 以下為實際填寫區 (請根據範例題型自行發揮，勿抄寫上方註解範例)
            
            # 積木 1: ...
            
            # 積木 2: ...
            
            ans = eval(...) # 最終計算
            
            # ---------------------------------------------------------
            
            # [Step 5: 黃金判斷 - 是否整除?]
            # 檢查是否為整數 (允許些微浮點誤差)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                
                # [Step 6: 成功！組裝 LaTeX]
                # 定義符號轉換 helper
                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op
                
                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                # ...
                
                # 填入 LaTeX (使用 fmt 處理負號，請模仿原圖結構)
                # str_abs = f"|{fmt(v1)} {l_op1} {fmt(v2)}|"
                # math_str = f"{str_abs} {l_op2} {fmt(v3)}"
                
                math_str = ... # 最終 LaTeX 字串
                
                question_text = r"計算 $$" + math_str + r"$$ 的值。"
                
                return {
                    'question_text': question_text,
                    'correct_answer': str(final_ans),
                    'mode': 1
                }
        except (ZeroDivisionError, SyntaxError):
            continue
            
    # 保底機制
    return {'question_text': "Error", 'correct_answer': "0", 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip(): return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6: return {'correct': True, 'result': '正確'}
    except: pass
    return {'correct': False, 'result': '錯誤'}
[[END_MODE:LIVESHOW]]
```