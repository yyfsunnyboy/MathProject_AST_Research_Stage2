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
- Level 1 (Easy): 基礎加減法，包含 2 項未化簡根式。
- Level 2 (Normal): 標準教材型，3-4 項未化簡根式加減 + 一組簡單分配律乘法。
- Level 3 (Hard): 進階挑戰型，包含根式除法（分母有理化）或複雜的雙括號乘法展開。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`


【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ✅ **必須** `import math`
   - ❌ **嚴禁** `import RadicalOps` (系統已自動注入，直接使用 `RadicalOps.xxx`)

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

【系統已注入的輔助函式（API）】（直接調用 `RadicalOps.xxx`）
- `RadicalOps.simplify_term(coeff, radicand)` → `(new_coeff, new_radicand)`
- `RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True)` → 未化簡格式化（題目用）
- `RadicalOps.format_expression(terms_dict, denominator=1)` → 最終答案（自動合併同類項、排序、LaTeX）

【核心規則】
1. **題目結構**：
   - Part 1: 3~4 項未化簡根式加減（例如 `\sqrt{12} + 2\sqrt{27} - \sqrt{8}`）。
   - Part 2: 簡單乘法（例如 `2(\sqrt{3} + \sqrt{5})`）。
   - 題目顯示：`化簡 $(Part1) + Part2$`
2. **數值範圍**：
   - 係數 `coeff`: -5 ~ 5 (非零)
   - 根號內 `radicand`: 2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75
     - 題目中的 `radicand` 必須包含這類「可化簡」的數（如 12, 18, 27, 50）。
     - 答案中的 `radicand` 必須是最簡根式（如 2, 3, 5...）。
3. **正確使用 format_expression**：
   - 必須傳入字典 `terms_dict = {radicand: total_coeff}`。
   - 嚴禁傳入列表或字串。

=== SKILL_END_PROMPT ===

【強烈建議程式碼結構】
```python
import random
import math
# RadicalOps is injected automatically

def generate(level=1, **kwargs):
    # Part 1: Generate Raw Terms (Numerical State)
    terms1_data = [] # List of (coeff, radicand)
    for _ in range(random.randint(3, 4)):
        c = random.choice([x for x in range(-5, 6) if x != 0])
        r = random.choice([2, 3, 5, 6, 8, 12, 18, 20, 24, 27, 32, 50]) # Mix of simple and simplifiable
        terms1_data.append((c, r))
    
    # Generate Part 1 String
    part1_strs = []
    for i, (c, r) in enumerate(terms1_data):
        is_first = (i == 0)
        s = RadicalOps.format_term_unsimplified(c, r, is_first)
        part1_strs.append(s)
    part1_latex = "".join(part1_strs)
    
    # Part 2: Generate Multiplication (Numerical State)
    k = random.randint(2, 5)
    r_a = random.choice([2, 3, 5, 7])
    r_b = random.choice([2, 3, 5, 7])
    # Structure: k(\sqrt{r_a} + \sqrt{r_b})
    part2_latex = f"{k}(\\sqrt{{{r_a}}} + \\sqrt{{{r_b}}})"
    
    # Question Text
    question_text = f"化簡 $({part1_latex}) + {part2_latex}$"
    
    # Calculate Answer (Pure Logic)
    final_terms = {} # {radicand: total_coeff}
    
    # Process Part 1
    for c, r in terms1_data:
        new_c, new_r = RadicalOps.simplify_term(c, r)
        final_terms[new_r] = final_terms.get(new_r, 0) + new_c
        
    # Process Part 2: k*sqrt(r_a) + k*sqrt(r_b)
    # Term A
    c_a, r_a_sim = RadicalOps.simplify_term(k, r_a)
    final_terms[r_a_sim] = final_terms.get(r_a_sim, 0) + c_a
    # Term B
    c_b, r_b_sim = RadicalOps.simplify_term(k, r_b)
    final_terms[r_b_sim] = final_terms.get(r_b_sim, 0) + c_b
    
    # Format Answer
    correct_answer = RadicalOps.format_expression(final_terms)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}
```

【檢查清單】
✅ 必須 `import random`
✅ 變數狀態必須是 `(coeff, radicand)` tuple，不能是 string
✅ 嚴禁 `int(str.split(...))` 這種寫法
✅ `format_expression` 輸入必須是 Dict
✅ 輸出 Python code only, no comments
/no_think

[[MODE:LIVESHOW]]
[Role] MathProject LiveShow 結構同構出題引擎（Qwen-8B-VL 專用）

[範例題型] {{OCR_RESULT}}

[最高優先原則]
你不是在「自由出題」，你是在「同構模仿」。
必須複製原例題的根式結構，保持相同的項數與乘法區塊形式，只替換係數與被開方數。

--------------------------------------------------
【A. 硬性同構規範（必須同時滿足）】
--------------------------------------------------
1) 根式加減項目數量必須一致（例如 3 項就生成 3 項）。
2) 未化簡根式必須保留（題目用可化簡的被開方數，如 12, 18, 27, 50）。
3) 乘法分配律區塊的形式必須保持（有幾組就保留幾組）。
4) 嚴禁新增或刪除 `\sqrt{}` 項。

--------------------------------------------------
【B. Qwen-8B-VL 特化規範（避免跑偏）】
--------------------------------------------------
1) 輸出必須是 Python code ONLY。
   - 禁止 markdown fence
   - 禁止思考文字
   - 禁止解釋段落

2) 禁止重定義系統注入工具：
   - 禁止自建 class RadicalOps
   - 禁止覆蓋 RadicalOps.simplify_term / format_expression

3) 必須使用：
   - RadicalOps.simplify_term(coeff, radicand)
   - RadicalOps.format_term_unsimplified(coeff, radicand, is_first)
   - RadicalOps.format_expression(terms_dict)

4) 必須輸出函式：
   - generate(level=1, **kwargs)
   - check(user_answer, correct_answer)

--------------------------------------------------
【C. 可直接遵循的骨架（照抄不會錯）】
--------------------------------------------------
import random
import math
# RadicalOps is injected automatically

def generate(level=1, **kwargs):
    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(20):
        # Part 1: 3~4 項未化簡根式加減
        n_terms = random.randint(3, 4)
        terms1_data = []
        for i in range(n_terms):
            c = random.choice([x for x in range(-5, 6) if x != 0])
            r = random.choice(simplifiable)
            terms1_data.append((c, r))

        part1_strs = []
        for i, (c, r) in enumerate(terms1_data):
            s = RadicalOps.format_term_unsimplified(c, r, is_first=(i == 0))
            part1_strs.append(s)
        part1_latex = "".join(part1_strs)

        # Part 2: 乘法分配律 k(\sqrt{r_a} + \sqrt{r_b})
        k = random.randint(2, 5)
        r_a = random.choice(simple)
        r_b = random.choice(simple)
        part2_latex = f"{k}(\\sqrt{{{r_a}}} + \\sqrt{{{r_b}}})"

        question_text = f"化簡 $({part1_latex}) + {part2_latex}$"

        # 計算答案（純數值操作，禁止解析 LaTeX 字串）
        final_terms = {}
        for c, r in terms1_data:
            new_c, new_r = RadicalOps.simplify_term(c, r)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c
        c_a, r_a_s = RadicalOps.simplify_term(k, r_a)
        final_terms[r_a_s] = final_terms.get(r_a_s, 0) + c_a
        c_b, r_b_s = RadicalOps.simplify_term(k, r_b)
        final_terms[r_b_s] = final_terms.get(r_b_s, 0) + c_b

        correct_answer = RadicalOps.format_expression(final_terms)
        if correct_answer and correct_answer != '0':
            return {
                'question_text': question_text,
                'answer': '',
                'correct_answer': correct_answer,
                'mode': 1
            }

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

--------------------------------------------------
【D. 最終輸出要求】
--------------------------------------------------
- 只輸出 Python 原始碼。
- 不要輸出任何額外文字。
- 不要輸出 markdown。
[[END_MODE:LIVESHOW]]