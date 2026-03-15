[Role] MathProject LiveShow — Edge AI Orchestrator（根式四則運算 專用）

[範例題型] {{OCR_RESULT}}

════════════════════════════════════════════════════════════════
【架構切換公告】Edge AI Coder → Edge AI Orchestrator
════════════════════════════════════════════════════════════════
本技能已升級為 Orchestrator 模式。

<<<<<<< HEAD
舊模式（Edge AI Coder）：
  模型從頭生成根式化簡、有理化計算邏輯 → 高幻覺風險，低計算能力設備不穩定
=======
**【格式鐵律】根式係數禁止使用 `IntegerOps.fmt_num`！係數直接傳入 `RadicalOps` 函式即可。**

--------------------------------------------------
【A. 硬性同構規範（必須同時滿足）】
--------------------------------------------------
1) 根式加減項目數量必須一致（例如 3 項就生成 3 項）。
2) 乘法與除法區塊的形式必須保持（有幾組 \times 或 \div 就保留幾組）。
3) 若原題的被開方數包含指數（例如 \sqrt{2^5}），生成題也必須包含指數形式（不需實際算出，可用 2**5 或 Fraction 表現，最後答案要是化簡的）。
4) 若原題包含分數係數（例如 -\frac{2}{3}\sqrt{5}），生成題對應位置也必須是分數係數，並以 Fraction(num, den) 計算。
5) 嚴禁新增或刪除 \sqrt{} 項，不可將乘除恣意改為加減。
6) 每個係數與被開方數都必須用 `random` 亂數生成，確保無限出題時數字不同。
>>>>>>> 72cf81989b7a6d8116c44aff7624336031261894

新模式（Edge AI Orchestrator）：
  模型只負責「識別 pattern + 設定 difficulty」→ 呼叫預寫引擎完成所有計算
  → 100% 數學正確性，完全不依賴模型的計算能力

════════════════════════════════════════════════════════════════
【STEP 0】Pattern 辨識（必須先填寫，再寫程式碼）
════════════════════════════════════════════════════════════════
在 generate() 函式開頭，用 # 注釋填寫辨識結果：

<<<<<<< HEAD
# [辨識1] Pattern ID: ___  （從下方 Pattern Catalogue 選擇）
# [辨識2] Difficulty: ___  （easy / mid / hard）
# [辨識3] 辨識依據: ___   （描述 OCR 語義中讓你選擇此 pattern 的關鍵特徵）
=======
3) 必須使用：
   - RadicalOps.add_term(terms_dict, coeff, radicand)
   - RadicalOps.mul_terms(c1, r1, c2, r2)
   - RadicalOps.div_terms(c1, r1, c2, r2)
   - RadicalOps.format_term_unsimplified(coeff, radicand, is_first)
   - RadicalOps.format_expression(terms_dict)
   - Fraction(num, den) (若遇到分數係數)
>>>>>>> 72cf81989b7a6d8116c44aff7624336031261894

─────────────────────────────────────────────────────────────
Pattern Catalogue（按優先順序匹配第一個符合的）
─────────────────────────────────────────────────────────────
p5b | √p/(b√q±c)  共軛有理化（分子為根式）      | √2/(3√2+4)
p5a | 1/(b√q±c)   共軛有理化（分子為整數1）      | 1/(√3-√2)
p2c | (a+b)(c+d)  雙括號多項×多項展開           | (√3+√2)(√6-1)
p2b | k√r×(…)     單項×多項分配律              | 2√3×(√12-√2)
p2a | k√r × k√r   兩根式直接相乘（無括號）       | 2√8×3√45
p4  | (a/b)×(√r/c) 分數×含根式的分數            | (2/3)×(√3/3)
p3a | (…)÷√d      表達式÷單一根式              | (-3√2+√15)÷√3
p3b | a/√b         純分數形式分母有理化           | 5/√3
p6  | 複合多步驟     加減+有理化等多步              | 多步混合
p1  | √r₁±√r₂     純加減法（化簡後合併同類項）    | 2√12-√27
p0  | √r           單一根式化簡                 | √72

⚠ p5b 優先於 p5a；p2c 優先於 p2b；p2a 不是 p2b（無括號！）

════════════════════════════════════════════════════════════════
【STEP 1】唯一合法程式碼格式
════════════════════════════════════════════════════════════════
/no_think
【絕對禁止輸出 thinking 或任何非 code 內容】

<<<<<<< HEAD
模型只需輸出以下格式，僅修改 pattern_id 和 difficulty 兩個值：

```python
from core.domain_functions import DomainFunctionHelper
df = DomainFunctionHelper()
=======
3. **根式除法 (\div) 的處理機制 (非常重要)**:
   - 遇到 `c1\sqrt{r1} \div c2\sqrt{r2}` 時，必須使用 `RadicalOps.div_terms(c1, r1, c2, r2)`
   - 這個函數會自動處理整除與有理化，返回化簡後的 `(new_c, new_r)`。
   - **為確保題目品質，建議使用「倒算法」**：先決定除數 `c2, r2` 和商的整數部分 `k`，再反推被除數 `c1, r1`，確保能整除。
   - **【雙重保險】若隨機生成的除數（係數 c2 或被開方數 r2）為 0，必須重抽，防止除以零錯誤。**

4. **遇到分子分母皆有根式的分數結構 (例如 \frac{\sqrt{A}}{\sqrt{B}})**:
   - 必須將這視為「被開方數為分數」的單項根式，並將 `radicand` 宣告為 `Fraction`。
   - 例如遇到 `\frac{\sqrt{33}}{\sqrt{7}}`，宣告 `c1 = 1` 與 `r1 = Fraction(33, 7)`。
   - 這樣呼叫 `RadicalOps.format_term_unsimplified(1, r1)` 就會自動生成 `\frac{\sqrt{33}}{\sqrt{7}}` 的結構。
   - 相乘除時，直接調用 `RadicalOps.mul_terms` 或 `RadicalOps.div_terms` 即可。

--------------------------------------------------
【D. 可直接遵循的骨架（照抄不會錯）】
--------------------------------------------------
import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically
>>>>>>> 72cf81989b7a6d8116c44aff7624336031261894

def generate(level=1, **kwargs):
    # [辨識1] Pattern ID: ___
    # [辨識2] Difficulty: ___
    # [辨識3] 辨識依據: ___

    pattern_id = "p1_add_sub"   # ← 填入辨識結果
    difficulty  = "mid"          # ← 填入難度

<<<<<<< HEAD
    # 以下為固定 scaffold，禁止修改
    vars = df.get_safe_vars_for_pattern(pattern_id, difficulty)
    ans, sol = df.solve_problem_pattern(pattern_id, vars, difficulty)
    question_text = df.format_question_LaTeX(pattern_id, vars)
=======
    for _ in range(50):
        try:
            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數
            # 【最高禁令】原題有幾項根式、是否有乘法分配律區塊，你就必須 100% 照做宣告對應的變數！
            # 若有分數係數，請使用 Fraction宣告，例: c1 = Fraction(random.randint(-5, -1), random.randint(2, 5))
            # 若無分數係數，請宣告整數，例: c1 = random.choice([-3, -2, 2, 3, 4, 5])
            # r1 = random.choice(simple)
            # r2 = random.choice(simplifiable)
            
            # 2. 組合題目字串
            # ★ 你必須宣告 question_text 這個變數！
            # 若原題包含乘除運算，必須構造出正確的 LaTeX 顯示：
            # q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)   # is_first=True 避免產生 + 號
            # q_part2 = RadicalOps.format_term_unsimplified(c2, r2, True)   # 乘除運算的後項也視為獨立項，設為 True
            # 
            # 若係數為負，手動加入圓括號；若為正，則不加括號：
            # str_p1 = f"({q_part1})" if c1 < 0 else q_part1
            # str_p2 = f"({q_part2})" if c2 < 0 else q_part2
            # question_text = f"計算 ${str_p1} \\times {str_p2}$ 的值。"
            question_text = f"..."
            
            # 3. 計算答案（純數值操作）
            final_terms = {}
            
            # 狀況 A: 若是單純加減法
            # RadicalOps.add_term(final_terms, c1, r1)
            
            # 狀況 B: 若是根式相乘 ( c1\sqrt{r1} * c2\sqrt{r2} )
            # new_c, new_r = RadicalOps.mul_terms(c1, r1, c2, r2)
            # RadicalOps.add_term(final_terms, new_c, new_r)
            
            # 狀況 C: 若是根式相除 ( c1\sqrt{r1} ÷ c2\sqrt{r2} )
            # [倒算法] 先決定除數與商，再反推被除數，確保能整除
            # c2 = random.choice([-3, -2, 2, 3])
            # r2 = random.choice(simple)
            # k_c = random.choice([-4, -3, -2, 2, 3, 4]) # 商的係數
            # k_r = random.choice(simple + [4, 9])      # 商的被開方數
            # c1 = c2 * k_c
            # r1 = r2 * k_r
            # new_c, new_r = RadicalOps.div_terms(c1, r1, c2, r2) # 驗算
            # RadicalOps.add_term(final_terms, new_c, new_r)
            
            # 狀況 D: 若被開方數 (radicand) 是 Fraction (例如 \frac{\sqrt{A}}{\sqrt{B}}) 相除
            # new_c, new_r = RadicalOps.div_terms(c1, r1, c2, r2)
            # RadicalOps.add_term(final_terms, new_c, new_r)
>>>>>>> 72cf81989b7a6d8116c44aff7624336031261894

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': ans,
        'solution_steps': sol,
        'mode': 1,
        '_o1_healed': False
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}
```

════════════════════════════════════════════════════════════════
【STEP 2】DomainFunctionHelper API 速查
════════════════════════════════════════════════════════════════

df.get_golden_pattern_for_liveshow(skill_name, difficulty, ocr_text)
  → str  ：自動從 OCR 語義辨識 pattern_id（可選用，模型也可手動辨識）

df.get_safe_vars_for_pattern(pattern_id, difficulty)
  → dict ：生成符合 pattern 約束的隨機整數變數字典（無浮點數）

df.solve_problem_pattern(pattern_id, vars, difficulty)
  → (str, List[str]) ：(LaTeX 答案, 解題步驟列表)

df.format_question_LaTeX(pattern_id, vars)
  → str ：格式化題目文字，含 $...$ 包裹，MathJax 可直接渲染

════════════════════════════════════════════════════════════════
【STEP 3】各 Pattern 的 vars 結構參考
════════════════════════════════════════════════════════════════

p0_simplify      : {"r": int}
p1_add_sub       : {"terms": [(coeff, radicand, op), ...]}   op ∈ {"+", "-"}
p2a_mult_direct  : {"c1": int, "r1": int, "c2": int, "r2": int}
p2b_mult_distrib : {"c1", "r1", "c2", "r2", "c3", "r3", "op"}
p2c_mult_binomial: {"c1","r1","c2","r2","c3","r3","c4","r4"}
p3a_div_expr     : {"c1","r1","c2","r2","denom_r","op"}
p3b_div_simple   : {"a": int, "b": int}
p4_frac_mult     : {"a","b","r","c"}
p5a_conjugate_int: {"b","q","c","sign"}   sign ∈ {1,-1}
p5b_conjugate_rad: {"p","b","q","c","sign"}
p6_combo         : {"sub_pattern1","vars1","sub_pattern2","vars2","combo_op"}

（vars 由 get_safe_vars_for_pattern 自動生成，模型無需手動構造）

════════════════════════════════════════════════════════════════
【STEP 4】Difficulty 對應難度說明
════════════════════════════════════════════════════════════════
  easy  → 2 項加減 / 直接乘法 / 純分母有理化
  mid   → 3 項加減 / 分配律展開 / P3a / P4 / P5a
  hard  → 4 項加減 / 雙括號展開 / P5b / P6 複合題

════════════════════════════════════════════════════════════════
【STEP 5】硬性禁令（違反任何一條均導致 0 分）
════════════════════════════════════════════════════════════════
1. 嚴禁 import math / import sympy / import numpy
2. 嚴禁 math.sqrt, **, sympy.sqrt, float 等任何根式或浮點運算
3. 嚴禁解析 LaTeX 字串取數值（如 int(s.split(...)）
4. 嚴禁自定義 simplify_radical, rationalize 等計算函數
5. 嚴禁修改 df.get_safe_vars_for_pattern 以下的 scaffold 內容
6. 嚴禁呼叫 RadicalOps.xxx（本模式不注入 RadicalOps）
7. 嚴禁生成超過 2 行有效 Python 程式邏輯（pattern_id 和 difficulty 各 1 行）
8. 輸出只能是 Python 原始碼，不輸出任何解釋文字或 markdown fence

════════════════════════════════════════════════════════════════
【STEP 6】最終輸出要求
════════════════════════════════════════════════════════════════
- 只輸出 Python 原始碼
- 不輸出任何額外文字或說明
- 不輸出 markdown fence (```python)
- pattern_id 必須是 Pattern Catalogue 中存在的值
- difficulty 必須是 "easy" / "mid" / "hard" 之一
