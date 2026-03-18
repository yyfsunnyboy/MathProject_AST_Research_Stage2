pattern_id = "p2a_mult_direct"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import random
    c1 = random.choice([1, 2, 3, 4])
    r1 = random.choice([2, 3, 5, 7, 8, 12, 18, 20])
    c2 = random.choice([1, 2, 3, 4, 5, 6])
    r2 = random.choice([2, 3, 5, 7, 8, 12, 18, 20])

    # 化簡根式
    s1 = RadicalOps.simplify(c1, r1)
    s2 = RadicalOps.simplify(c2, r2)

    # 計算乘積
    new_c = s1[0] * s2[0]
    new_r = s1[1] * s2[1]

    # 格式化題目
    t1 = RadicalOps.format_term_unsimplified(s1[0], s1[1], is_leading=True)
    t2 = RadicalOps.format_term_unsimplified(s2[0], s2[1], is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t2.startswith("-"):
        t2 = f"({t2})"

    return {
        'question_text': f"計算 ${t1} \\times {t2}$ 的值",
        'correct_answer': RadicalOps.format_expression({new_r: new_c}),
        'mode': 1
    }