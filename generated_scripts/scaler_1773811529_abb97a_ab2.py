pattern_id = "p2g_rad_mult_frac"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import fractions
    c1 = random.choice([1, 2, 3, 4, 5])
    r1 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    c2 = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    r2 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])

    # 確保 r1 和 r2 無平方因子
    r1 = r1
    r2 = r2

    # 生成分數係數
    frac = fractions.Fraction(c2, random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10]))

    # 單項化簡
    t1 = RadicalOps.simplify(c1, r1)
    t2 = RadicalOps.simplify(frac, r2)

    # 根式乘法
    new_c, new_r = RadicalOps.mul_terms(t1[0], t1[1], frac.numerator, r2)

    # 格式化題目
    t1_str = RadicalOps.format_term_unsimplified(c1, r1, is_leading=True)
    t2_str = RadicalOps.format_term_unsimplified(frac, r2, is_leading=True)

    # 防護：負數根式加括號
    if t1_str.startswith("-"):
        t1_str = f"({t1_str})"
    if t2_str.startswith("-"):
        t2_str = f"({t2_str})"

    return {
        'question_text': f"化簡 ${t1_str} \\times {t2_str}$ 的值",
        'correct_answer': RadicalOps.format_expression({new_r: new_c}),
        'mode': 1
    }