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