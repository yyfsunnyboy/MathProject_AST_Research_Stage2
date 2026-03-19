pattern_id = "p2g_rad_mult_frac"
difficulty = "easy"
term_count = 2

```python
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction

    # 題型：k√r × (a/b) —— 根式 × 分數
    # 結構：4√2 × (1/6) → 數字=4, 運算子=2 (×, ÷), 中括號=1, 第1個中括號內數字=1, 運算子=0
    # 題型同構硬性約束：數字=4, 運算子=2 (×, ÷), 中括號=1, 第1個中括號內數字=1, 運算子=0

    # 生成 k (整數係數)
    c1 = random.choice([2, 3, 4, 5])
    # 生成 r (根式內數)
    r = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    # 生成分母 a (分數分子)
    a = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    # 生成分母 b (分數分母)
    b = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])

    # 確保分數不為 0，且分母不為 1（避免 trivial case）
    while b == 1:
        b = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])

    # 計算結果：c1 * a / b → 但保留分數形式
    result_c = c1 * a
    result_r = r
    result_denom = b

    # 格式化題目：k√r × (a/b)
    t1 = RadicalOps.format_term_unsimplified(c1, r, is_leading=True)
    t2 = f"({a})/({b})"  # 保留中括號結構

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    # 本題無負數，無需處理

    return {
        'question_text': f"化簡 ${t1} \\times {t2}$ 的值",
        'correct_answer': RadicalOps.format_expression({r: Fraction(result_c, result_denom)}),
        'mode': 1
    }