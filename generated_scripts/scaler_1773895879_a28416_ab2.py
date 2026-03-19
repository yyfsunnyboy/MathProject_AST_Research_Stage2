pattern_id = "p0"
difficulty = "easy"
term_count = 1

```python
def generate(level=1, **kwargs):
    import random
    c, r = random.choice([1, 2, 3, 4, 5]), random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 18, 20, 24, 27, 32, 36, 48, 50, 64, 72, 81, 100])
    t1 = RadicalOps.format_term_unsimplified(c, r, is_leading=True)
    return {
        'question_text': f"化簡 ${t1}$",
        'correct_answer': RadicalOps.format_expression(RadicalOps.simplify(c, r)),
        'mode': 1
    }