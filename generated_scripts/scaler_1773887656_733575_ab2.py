pattern_id = "p2f_int_mult_rad"
difficulty = "easy"
term_count = 3

```python
def generate(level=1, **kwargs):
    import random
    c1 = random.choice([-2, -3, -4, 2, 3, 4])
    c2 = random.choice([1, 2, 3, 5, 7, 11])
    r = random.choice([2, 3, 5, 7, 11, 13])

    t1 = str(c1)
    t2 = RadicalOps.format_term_unsimplified(c2, r, is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t2.startswith("-"):
        t2 = f"({t2})"

    return {
        'question_text': f"計算 ${t1} \\times {t2}$ 的值",
        'correct_answer': RadicalOps.format_expression({r: c1 * c2}),
        'mode': 1
    }