[[MODE:BENCHMARK]]
【說明】本檔為實驗/大量出題用程式碼結構。Pattern Catalogue 與辨識規則由憲法 (SKILL.md) 提供，scaler 組裝時會一併注入，此處不重複定義。

【強烈建議程式碼結構】
```python
import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    if level == 1:
        # Level 1: 根號化簡 (Simplifying Radicals)
        # 單一項需要化簡的根式
        c = random.choice([-3, -2, 1, 2, 3])
        r = random.choice([8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75])
        
        # Format the question
        question_text = f"化簡 ${RadicalOps.format_term_unsimplified(c, r, True)}$"
        
        # Calculate answer
        final_terms = {}
        RadicalOps.add_term(final_terms, c, r)
        correct_answer = RadicalOps.format_expression(final_terms)
        
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
        
    elif level == 2:
        # Level 2: 同類方根的合併 (Combining Like Radicals)
        # 加減法，確保化簡後是同類方根
        base_r = random.choice([2, 3, 5, 7])
        # 產生能化簡為 base_r 的數列，例如 base=2: 8, 18, 32, 50
        candidates = [base_r * (i**2) for i in range(2, 6)]
        
        terms = []
        for _ in range(random.randint(3, 4)):
            c = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
            r = random.choice(candidates)
            terms.append((c, r))
            
        part_strs = []
        for i, (c, r) in enumerate(terms):
            part_strs.append(RadicalOps.format_term_unsimplified(c, r, i == 0))
            
        question_text = f"化簡 ${''.join(part_strs)}$"
        
        final_terms = {}
        for c, r in terms:
            RadicalOps.add_term(final_terms, c, r)
            
        correct_answer = RadicalOps.format_expression(final_terms)
        
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
        
    else:
        # Level 3: 四則運算 (Four Arithmetic Operations)
        # 乘法分配律
        c1 = random.choice([-3, -2, 2, 3])
        r1 = random.choice([2, 3, 5])
        
        c2 = random.choice([1, 2, 3])
        r2 = random.choice([6, 10, 15]) 
        
        c3 = random.choice([-3, -2, 2, 3])
        r3 = random.choice([2, 3, 5])
        
        # Structure: c1\sqrt{r1} * (c2\sqrt{r2} + c3\sqrt{r3})
        t1 = RadicalOps.format_term_unsimplified(c1, r1, True)
        t2 = RadicalOps.format_term_unsimplified(c2, r2, True)
        t3 = RadicalOps.format_term_unsimplified(c3, r3, False)
        
        question_text = f"化簡 $({t1}) \\times ({t2}{t3})$"
        
        final_terms = {}
        # Term 1: t1 * t2
        new_c1, new_r1 = RadicalOps.mul_terms(c1, r1, c2, r2)
        RadicalOps.add_term(final_terms, new_c1, new_r1)
        
        # Term 2: t1 * t3
        new_c2, new_r2 = RadicalOps.mul_terms(c1, r1, c3, r3)
        RadicalOps.add_term(final_terms, new_c2, new_r2)
        
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
✅ 必須 `import random`、`import math`、`from fractions import Fraction`
✅ 變數狀態必須是 `(coeff, radicand)` tuple，不能是 string
✅ 嚴禁 `int(str.split(...))` 這種寫法
✅ `format_expression` 輸入必須是 Dict
✅ 輸出 Python code only, no comments
[[END_MODE:BENCHMARK]]