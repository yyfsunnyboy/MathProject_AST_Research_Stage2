import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    op = random.choice(['+', '-'])
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    g = random.randint(-5, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)
    
    if op == '+':
        part1 = a + b
    else:
        part1 = a - b
    
    part1_fraction = Fraction(part1) * Fraction(c, d)
    part2 = Fraction(e, f)
    part1_divide_part2 = part1_fraction / part2
    
    part3 = Fraction(g) * Fraction(h, i) - Fraction(j)
    part3_abs = abs(part3)
    
    total = part1_divide_part2 + part3_abs
    
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i}) - {j}|"
    correct_answer = str(total)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        return {'correct': user_fraction == correct_fraction, 'result': '正確' if user_fraction == correct_fraction else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}