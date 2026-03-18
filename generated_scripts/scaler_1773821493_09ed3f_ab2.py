pattern_id = "p2a_mult_direct"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import random
    c1 = random.choice([2, 3, 4])
    r1 = random.choice([2, 3, 5, 7, 8, 12, 18, 20, 27, 32, 45])
    c2 = random.choice([1, 2, 3, 4, 5, 6])
    r2 = random.choice([2, 3, 5, 7, 8, 12, 18, 20, 27, 32, 45])

    # 化簡每個根式項
    simplified_r1 = RadicalOps.simplify_term(c1, r1)
    simplified_r2 = RadicalOps.simplify_term(c2, r2)

    # 計算乘積
    new_c = simplified_r1[0] * simplified_r2[0]
    new_r = simplified_r1[1] * simplified_r2[1]

    # 格式化題目與答案
    t1 = RadicalOps.format_term_unsimplified(c1, r1, is_leading=True)
    t2 = RadicalOps.format_term_unsimplified(c2, r2, is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t2.startswith("-"):
        t2 = f"({t2})"

    return {
        'question_text': f"計算 ${t1} \\times {t2}$ 的值",
        'correct_answer': RadicalOps.format_expression({new_r: new_c}),
        'mode': 1
    }