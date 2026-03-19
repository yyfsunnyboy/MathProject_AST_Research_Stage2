pattern_id = "p1b"
difficulty = "mid"
term_count = 4

```python
def generate(level=1, **kwargs):
    import random
    c1 = random.choice([2, 3, 4])
    c2 = random.choice([1, 2, 3])
    c3 = random.choice([1, 2, 3])
    c4 = random.choice([1, 2, 3])

    r1 = random.choice([2, 3, 5, 7, 8, 12, 18])
    r2 = random.choice([2, 3, 5, 7, 8, 12, 18])
    r3 = random.choice([2, 3, 5, 7, 8, 12, 18])
    r4 = random.choice([2, 3, 5, 7, 8, 12, 18])

    # 化簡各項
    t1 = RadicalOps.simplify(c1, r1)
    t2 = RadicalOps.simplify(c2, r2)
    t3 = RadicalOps.simplify(c3, r3)
    t4 = RadicalOps.simplify(c4, r4)

    # 格式化題目
    t1_str = RadicalOps.format_term_unsimplified(t1[0], t1[1], is_leading=True)
    t2_str = RadicalOps.format_term_unsimplified(t2[0], t2[1], is_leading=True)
    t3_str = RadicalOps.format_term_unsimplified(t3[0], t3[1], is_leading=True)
    t4_str = RadicalOps.format_term_unsimplified(t4[0], t4[1], is_leading=True)

    # 組裝題目文字
    question_text = f"化簡 ${t1_str} + {t2_str} - ({t3_str} - {t4_str})$"

    # 合併項
    container = {}
    RadicalOps.add_term(container, t1[0], t1[1])
    RadicalOps.add_term(container, t2[0], t2[1])
    RadicalOps.add_term(container, -t3[0], t3[1])
    RadicalOps.add_term(container, t4[0], t4[1])

    # 格式化答案
    correct_answer = RadicalOps.format_expression(container)

    return {
        'question_text': question_text,
        'correct_answer': correct_answer,
        'mode': 1
    }