pattern_id = "p0"
difficulty = "easy"
term_count = 1

```python
def generate(level=1, **kwargs):
    import random
    r = random.choice([12, 18, 20, 27, 32, 48, 50, 72, 80, 98])

    c, rad = RadicalOps.simplify(1, r)
    t1 = RadicalOps.format_term_unsimplified(c, rad, is_leading=True)

    return {
        'question_text': f"化簡 ${t1}$",
        'correct_answer': RadicalOps.format_expression({rad: c}),
        'mode': 1
    }