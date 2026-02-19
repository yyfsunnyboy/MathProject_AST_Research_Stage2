import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    A_expression = f"({a}+{b})×{c}/{d}"
    A_value = Fraction(a + b) * Fraction(c, d)
    
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    B_expression = f"{e}/{f}"
    B_value = Fraction(e, f)
    
    g = random.randint(-5, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)
    C_expression = f"{g}×{h}/{i}-{j}"
    C_value = Fraction(g * h, i) - j
    C_abs_value = abs(C_value)
    
    total = (A_value / B_value) + C_abs_value
    
    if total.denominator == 1:
        correct_answer = str(total.numerator)
    else:
        correct_answer = f"{total.numerator}/{total.denominator}"
    
    question_text = f"計算 [{A_expression}]÷{B_expression} + |{C_expression}| 的值。"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
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