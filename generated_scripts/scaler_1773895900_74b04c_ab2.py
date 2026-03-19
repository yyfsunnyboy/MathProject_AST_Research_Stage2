pattern_id = "p0"
difficulty = "easy"
term_count = 1

```python
def generate(level=1, **kwargs):
    import random
    c = random.choice([1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36])
    r = random.choice([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31])

    t1 = RadicalOps.format_term_unsimplified(c, r, is_leading=True)

    return {
        'question_text': f"化簡 ${t1}$",
        'correct_answer': RadicalOps.format_expression({r: c}),
        'mode': 1
    }