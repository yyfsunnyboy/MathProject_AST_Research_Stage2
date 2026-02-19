import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    op1 = random.choice(['+', '-'])
    part1 = f"({a}{op1}{b})×{c}/{d}"
    
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    part2 = f"[{part1}]÷{e}/{f}"
    
    g = random.randint(1, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(1, 5)
    part3 = f"|{g}×{h}/{i}-{j}|"
    
    question_text = f"{part2} + {part3}"
    
    part1_val = Fraction(a + b) * Fraction(c, d)
    part2_val = part1_val * Fraction(f, e)
    abs_part = Fraction(g) * Fraction(h, i) - Fraction(j)
    abs_val = abs(abs_part)
    correct_answer = part2_val + abs_val
    correct_answer_str = str(correct_answer)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_frac = Fraction(user_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    try:
        correct_frac = Fraction(correct_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    if user_frac == correct_frac:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}