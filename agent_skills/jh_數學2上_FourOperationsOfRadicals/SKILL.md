# Skill: jh_數學2上_FourOperationsOfRadicals

## [DOMAIN_API]
- `RadicalOps.simplify_term(coeff, radicand)`: 傳入係數與根號值，回傳化簡後的 `(new_coeff, new_radicand)` tuple。
- `RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True)`: 將 tuple 變成未化簡的 LaTeX 顯示字串，提供給題幹使用。
- `RadicalOps.format_expression(terms_dict, denominator=1)`: 輸入字典 `{radicand: total_coeff}` 產生最終化簡合併對齊的 LaTeX 答案。

## [NUMERICAL_SPEC]
- **核心數學操作**：使用 `terms = [(coeff, radicand), ...]` 來儲存狀態，絕對禁止使用字串切割（如 `int(term.split())`）的方式提取根式數值。
- 所有計算都必須純粹基於整數操作 `(coeff, radicand)`，只有在最後的題目與答案字串產生步驟，才允許將資料送給 `RadicalOps` 進行字串編排。
- 根號內 `radicand` 限制：只允許從 `2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75` 選取。這其中混合了可化簡與最簡根式。
- 係數 `coeff` 限制：介於 -5 到 5 之間且非零。
- `format_expression` 函數必須輸入 Dictionary 結構的 `{radicand: total_coeff}`，嚴禁傳入列表。
- **f-string LaTeX 嚴格安全規範**：
  - 在 f-string 內，`{{ }}` 表示印出大括號字元，單一 `{ }` 是放置變數的地方。
  - **嚴禁**在 f-string 直接寫複雜巢狀如 `\\frac{{{a}\\sqrt{{{b}}}}}{{\\sqrt{{{d}}}}}`，極易因為括號層數出錯而拋出 `SyntaxError`。應分段宣告字串（先定義 `numer` 再塞入 `\\frac`）再組合。

## [LEGACY_CODE_DNA]
```python
import random
import math

def generate(level=1, **kwargs):
    # Part 1: Generate Raw Terms (Numerical State)
    terms1_data = [] # List of (coeff, radicand)
    for _ in range(random.randint(3, 4)):
        c = random.choice([x for x in range(-5, 6) if x != 0])
        r = random.choice([2, 3, 5, 6, 8, 12, 18, 20, 24, 27, 32, 50])
        terms1_data.append((c, r))
    
    # Generate Part 1 String
    part1_strs = []
    for i, (c, r) in enumerate(terms1_data):
        is_first = (i == 0)
        s = RadicalOps.format_term_unsimplified(c, r, is_first)
        part1_strs.append(s)
    part1_latex = "".join(part1_strs)
    
    # Part 2: Generate Multiplication
    k = random.randint(2, 5)
    r_a = random.choice([2, 3, 5, 7])
    r_b = random.choice([2, 3, 5, 7])
    part2_latex = f"{k}(\\sqrt{{{r_a}}} + \\sqrt{{{r_b}}})"
    
    # Question Text
    question_text = f"化簡 $$({part1_latex}) + {part2_latex}$$ 的值。"
    
    # Calculate Answer (Pure Logic)
    final_terms = {} # {radicand: total_coeff}
    
    for c, r in terms1_data:
        new_c, new_r = RadicalOps.simplify_term(c, r)
        final_terms[new_r] = final_terms.get(new_r, 0) + new_c
        
    c_a, r_a_sim = RadicalOps.simplify_term(k, r_a)
    final_terms[r_a_sim] = final_terms.get(r_a_sim, 0) + c_a
    c_b, r_b_sim = RadicalOps.simplify_term(k, r_b)
    final_terms[r_b_sim] = final_terms.get(r_b_sim, 0) + c_b
    
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