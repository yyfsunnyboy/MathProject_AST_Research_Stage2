pattern_id = "p2g_rad_mult_frac"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction

    # 題型：k√r × (a/b) → 4√2 × (1/6)
    # 數字總數量：4 個數字（4, 2, 1, 6）
    # 運算子：× 和 ÷ → 各 1 個
    # 中括號：1 個，內含 1 個數字，0 個運算子
    # 統計嚴格對應：數字=4，運算子=2（×=1, ÷=1），中括號=1，負數括號=0

    c1 = random.choice([2, 3, 4])
    r = random.choice([2, 3, 5, 7])
    a = random.choice([1, 2, 3])
    b = random.choice([2, 3, 4, 6])

    # 確保分母不為 1，避免無意義的分數
    if b == 1:
        b = random.choice([2, 3, 4, 6])

    # 確保 a/b 為最簡分數
    frac = Fraction(a, b)
    a, b = frac.numerator, frac.denominator

    # 單項化簡
    t1 = RadicalOps.simplify(c1, r)
    c1_simplified, r_simplified = t1

    # 計算乘積
    new_c = c1_simplified * a
    new_r = r_simplified

    # 格式化題目
    t1_unsimplified = RadicalOps.format_term_unsimplified(c1, r, is_leading=True)
    t2_unsimplified = RadicalOps.format_term_unsimplified(a, b, is_leading=False)

    # 題目文字：4√2 × (1/6)
    question_text = f"化簡 ${t1_unsimplified} \\times \\left[{t2_unsimplified}\\right]$"

    # 正確答案：(new_c, new_r)
    correct_answer = RadicalOps.format_expression({new_r: new_c})

    return {
        'question_text': question_text,
        'correct_answer': correct_answer,
        'mode': 1
    }