import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(1, 5)
    g = random.randint(1, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(1, 5)
    op1 = random.choice(['+', '-'])
    op2 = random.choice(['×', '-'])
    part1 = f"({a} {op1} {b})"
    part2 = f"{c}/{d}"
    part3 = f"{e}/{f}"
    part4 = f"{g} {op2} ({h}/{i}) - {j}"
    question_text = f"[{part1} × {part2}] ÷ ({part3}) + |{part4}|"
    value1 = Fraction(a) + Fraction(b) if op1 == '+' else Fraction(a) - Fraction(b)
    value2 = value1 * Fraction(c, d)
    value3 = value2 / Fraction(e, f)
    value4 = Fraction(g) * Fraction(h, i) - Fraction(j)
    absolute_value = abs(value4)
    correct_answer = value3 + absolute_value
    correct_answer_str = str(correct_answer)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        return {'correct': user_fraction == correct_fraction, 'result': '正確' if user_fraction == correct_fraction else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}