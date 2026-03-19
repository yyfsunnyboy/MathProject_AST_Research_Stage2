pattern_id = "p2c"
difficulty = "hard"
term_count = 4

```python
def generate(level=1, **kwargs):
    import random
    c1, r1 = random.choice([2, 3]), random.choice([2, 3, 5])
    c2, r2 = random.choice([1, 2]), random.choice([2, 3, 5])
    c3, r3 = random.choice([1, 2]), random.choice([2, 3, 5])
    c4, r4 = random.choice([1, 2]), random.choice([2, 3, 5])

    # 確保運算子順序：plus -> minus，且中括號結構嚴格
    # 題型：(a + b)(c - d)
    # 數字總數：4，運算子：2（+1, -1），中括號：3（各含1數字，0運算子）

    t1 = RadicalOps.format_term_unsimplified(c1, r1, is_leading=True)
    t2 = RadicalOps.format_term_unsimplified(c2, r2, is_leading=True)
    t3 = RadicalOps.format_term_unsimplified(c3, r3, is_leading=True)
    t4 = RadicalOps.format_term_unsimplified(c4, r4, is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t4.startswith("-"):
        t4 = f"({t4})"

    # 組裝題目：嚴格保留中括號結構
    question_text = f"化簡 ${t1} + {t2})({t3} - {t4}$"

    # 計算：先乘開，再化簡
    # (a + b)(c - d) = a*c - a*d + b*c - b*d
    terms = {}
    # a*c
    c1c3, r1r3 = RadicalOps.mul_terms(c1, r1, c3, r3)
    RadicalOps.add_term(terms, c1c3, r1r3)
    # -a*d
    c1c4, r1r4 = RadicalOps.mul_terms(c1, r1, c4, r4)
    RadicalOps.add_term(terms, -c1c4, r1r4)
    # b*c
    c2c3, r2r3 = RadicalOps.mul_terms(c2, r2, c3, r3)
    RadicalOps.add_term(terms, c2c3, r2r3)
    # -b*d
    c2c4, r2r4 = RadicalOps.mul_terms(c2, r2, c4, r4)
    RadicalOps.add_term(terms, -c2c4, r2r4)

    # 合併所有項
    final_terms = {}
    for radicand, coeff in terms.items():
        if radicand not in final_terms:
            final_terms[radicand] = 0
        final_terms[radicand] += coeff

    correct_answer = RadicalOps.format_expression(final_terms)

    return {
        'question_text': question_text,
        'correct_answer': correct_answer,
        'mode': 1
    }