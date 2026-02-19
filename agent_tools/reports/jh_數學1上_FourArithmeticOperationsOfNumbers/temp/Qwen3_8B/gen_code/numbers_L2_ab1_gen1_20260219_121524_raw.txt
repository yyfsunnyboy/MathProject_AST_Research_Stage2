import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    op = random.choice(['+', '-'])
    c = random.randint(-10, 10)
    d = random.randint(1, 10)
    e = random.randint(-10, 10)
    f = random.randint(1, 10)
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(1, 10)
    j = random.randint(-10, 10)
    question_text = f"[({a} {op} {b}) × {c}/{d}] ÷ ({e}/{f}) + |{g} × ({h}/{i}) - {j}|"
    part1 = Fraction(a + b) * Fraction(c, d) / Fraction(e, f)
    abs_part = abs(Fraction(g * h, i) - j)
    total = part1 + abs_part
    correct_answer = str(total)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }