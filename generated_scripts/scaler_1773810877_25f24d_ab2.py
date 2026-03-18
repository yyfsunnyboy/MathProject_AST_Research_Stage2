pattern_id = "p2g_rad_mult_frac"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction

    # 選擇根式被開方數（無平方因子）
    radicands = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    r = random.choice(radicands)

    # 選擇根式係數（整數或分數）
    coeffs = [Fraction(1, 2), Fraction(1, 3), Fraction(1, 4), Fraction(1, 6), Fraction(1, 8), Fraction(1, 12)]
    c1 = random.choice(coeffs)
    c2 = random.choice([Fraction(1, 2), Fraction(1, 3), Fraction(1, 4), Fraction(1, 6), Fraction(1, 8), Fraction(1, 12)])

    # 單項化簡
    t1 = RadicalOps.format_term_unsimplified(c1, r, is_leading=True)
    t2 = RadicalOps.format_term_unsimplified(c2, r, is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t2.startswith("-"):
        t2 = f"({t2})"

    # 計算結果
    new_c = c1 * c2
    new_r = r

    # 格式化答案
    answer_container = {new_r: new_c}

    return {
        'question_text': f"計算 ${t1} \\times {t2}$ 的值",
        'correct_answer': RadicalOps.format_expression(answer_container),
        'mode': 1
    }