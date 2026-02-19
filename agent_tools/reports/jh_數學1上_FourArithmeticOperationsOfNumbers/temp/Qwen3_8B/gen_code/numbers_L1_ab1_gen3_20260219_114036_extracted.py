import random
from fractions import Fraction

def fraction_to_str(frac):
    if frac.denominator == 1:
        return str(frac.numerator)
    else:
        return f"{frac.numerator}/{frac.denominator}"

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-5, 5)
        b = random.randint(-5, 5)
        c = random.randint(1, 5)
        d = random.randint(1, 5)
        e = random.randint(-5, 5)
        f = random.randint(1, 5)
        g = random.randint(1, 5)
        h = random.randint(1, 5)
        k = random.randint(1, 5)
        part1 = f"[({a}+{b})×{c}/{d}]÷({e}/{f})"
        abs_part = f"|{g}×({h}/{k}) - {k}|"
        question_text = f"計算 {part1} + {abs_part} 的值。"
        part1_val = ((a + b) * Fraction(c, d)) / Fraction(e, f)
        abs_val = abs(Fraction(g * h, k) - Fraction(k, 1))
        total = part1_val + abs_val
        correct_answer = fraction_to_str(total)
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        return generate(level=1)

def check(user_answer, correct_answer):
    try:
        user_frac = Fraction(user_answer)
        correct_frac = Fraction(correct_answer)
        return {'correct': user_frac == correct_frac, 'result': '正確' if user_frac == correct_frac else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}