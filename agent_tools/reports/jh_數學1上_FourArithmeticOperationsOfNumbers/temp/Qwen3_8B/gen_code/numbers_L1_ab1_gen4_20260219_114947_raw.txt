import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    numerator_b = random.randint(-5, 5)
    denominator_b = random.randint(1, 5)
    if denominator_b == 1:
        part1_expr = f"({a} + {numerator_b})"
    else:
        part1_expr = f"({a} + {numerator_b}/{denominator_b})"
    part1_val = a + Fraction(numerator_b, denominator_b)

    numerator_c = random.randint(-5, 5)
    denominator_c = random.randint(1, 5)
    if denominator_c == 1:
        part2_expr = f"{numerator_c}"
    else:
        part2_expr = f"{numerator_c}/{denominator_c}"
    part2_val = Fraction(numerator_c, denominator_c)

    d = random.randint(1, 5)
    numerator_e = random.randint(-5, 5)
    denominator_e = random.randint(1, 5)
    f = random.randint(-5, 5)
    if denominator_e == 1:
        part3_expr = f"{d}×({numerator_e}) - {f}"
    else:
        part3_expr = f"{d}×({numerator_e}/{denominator_e}) - {f}"
    part3_val = d * Fraction(numerator_e, denominator_e) - f

    question_text = f"[{part1_expr}] ÷ {part2_expr} + |{part3_expr}|"
    total = (part1_val / part2_val) + abs(part3_val)
    correct_answer = str(total)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_val = Fraction(user_answer)
        correct_val = Fraction(correct_answer)
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}