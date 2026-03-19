pattern_id = "p3a"
difficulty = "mid"
term_count = 3

```python
def generate(level=1, **kwargs):
    import random
    c1 = random.choice([2, 3, 4])
    c2 = random.choice([-3, -2, 2, 3])
    c3 = random.choice([2, 3, 4])

    t1 = RadicalOps.format_term_unsimplified(c1, 2, is_leading=True)
    t2 = RadicalOps.format_term_unsimplified(c2, 3, is_leading=True)
    t3 = RadicalOps.format_term_unsimplified(c3, 5, is_leading=True)

    # 🚨 數學排版防護：乘號後面的負數必須加括號！
    if t2.startswith("-"):
        t2 = f"({t2})"

    return {
        'question_text': f"化簡 ${t1} \\div {t2} \\times {t3}$ 的值",
        'correct_answer': RadicalOps.format_expression({2: c1 * c3 // abs(c2), 3: -c1 * c3 // abs(c2)}),
        'mode': 1
    }