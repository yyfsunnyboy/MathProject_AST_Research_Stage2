import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    numerator1 = random.randint(-10, 10)
    denominator1 = random.randint(1, 10)
    numerator2 = random.randint(-10, 10)
    denominator2 = random.randint(1, 10)
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    e = random.randint(1, 10)
    e_rand = random.randint(1, 10)
    question_text = f"[({a}+{b})×{numerator1}/{denominator1}]÷({numerator2}/{denominator2}) + |{c}×(-{d}/{e})-{e_rand}|"
    part1 = Fraction(a + b)
    part1 *= Fraction(numerator1, denominator1)
    part1 /= Fraction(numerator2, denominator2)
    abs_part = Fraction(c) * Fraction(-d, e)
    abs_part -= e_rand
    abs_part = abs(abs_part)
    correct_answer = part1 + abs_part
    if correct_answer.denominator == 1:
        correct_answer_str = str(correct_answer.numerator)
    else:
        correct_answer_str = f"{correct_answer.numerator}/{correct_answer.denominator}"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    try:
        correct_fraction = Fraction(correct_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    if user_fraction == correct_fraction:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}