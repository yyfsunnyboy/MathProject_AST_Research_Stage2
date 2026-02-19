import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    op = random.choice(['+', '-'])
    bracket_expr = f"({a}{op}{b})"
    
    d = random.randint(-5, 5)
    e = random.randint(1, 5)
    f = random.choice([n for n in range(-5, 6) if n != 0])
    g = random.randint(1, 5)
    h = random.randint(-10, 10)
    i = random.randint(-5, 5)
    j = random.randint(1, 5)
    k = random.randint(-10, 10)
    
    question_text = f"[{bracket_expr}×{d}/{e}]÷{f}/{g} + |{h}×({i}/{j})-{k}|"
    
    part1 = Fraction(a + b) * Fraction(d, e)
    part2 = part1 * Fraction(g, f)
    abs_value = abs(h * Fraction(i, j) - k)
    correct_answer = part2 + abs_value
    
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