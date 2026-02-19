import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(-5, 5)
    d = random.randint(1, 5)
    d1 = random.randint(1, 5)
    e1 = random.randint(1, 5)
    f = random.randint(-5, 5)
    g = random.randint(1, 5)
    h = random.randint(1, 5)
    i = random.randint(-5, 5)
    
    A_str = f"({a}+{b})×{c}/{d}"
    B_str = f"{d1}/{e1}"
    C_str = f"|{f}×{g}/{h}-{i}|"
    question_text = f"[{A_str}]÷{B_str} + {C_str}"
    
    A_val = Fraction(a + b) * Fraction(c, d)
    B_val = Fraction(d1, e1)
    C_val = abs(Fraction(f) * Fraction(g, h) - Fraction(i))
    total = A_val / B_val + C_val
    correct_answer = str(total)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_frac = Fraction(user_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    correct_frac = Fraction(correct_answer)
    if user_frac == correct_frac:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}