pattern_id = "p0"
difficulty = "easy"
term_count = 1

```python
def generate(level=1, **kwargs):
    import random
    c, r = random.choice([1, 2, 3]), random.choice([8, 12, 18, 20, 27, 32, 50])

    t1 = RadicalOps.format_term_unsimplified(c, r, is_leading=True)

    return {
        'question_text': f"化簡 ${t1}$",
        'correct_answer': RadicalOps.format_expression(RadicalOps.simplify(c, r)),
        'mode': 1
    }