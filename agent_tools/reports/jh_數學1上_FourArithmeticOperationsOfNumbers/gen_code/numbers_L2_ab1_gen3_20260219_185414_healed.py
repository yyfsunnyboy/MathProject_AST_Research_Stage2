import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    e = random.randint(-10, 10)
    while e == 0:
        e = random.randint(-10, 10)
    f = random.randint(1, 10)
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(1, 10)
    j = random.randint(-10, 10)
    
    part1 = f"[({a}+{b})×{c}/{d}]"
    part2 = f"÷({e}/{f})"
    part3 = f"+ |{g}×({h}/{i}) - {j}|"
    question_text = part1 + part2 + part3
    
    part1_val = Fraction(a + b) * Fraction(c, d)
    part2_val = part1_val * Fraction(f, e)
    part3_val = abs(Fraction(g) * Fraction(h, i) - j)
    correct_answer = part2_val + part3_val
    
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