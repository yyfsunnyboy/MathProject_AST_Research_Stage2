import random
from fractions import Fraction
import re

def generate(level=1, **kwargs):
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        return numerator, denominator
    
    a, b = generate_fraction()
    c, d = generate_fraction()
    e, f = generate_fraction()
    g, h = generate_fraction()
    i, j = generate_fraction()
    
    part1 = f"(-{a} + {b}) × {c}/{d}"
    part2 = f"÷ ({e}/{f})"
    abs_part = f"|{g} × {h}/{i} - {j}|"
    question_text = f"[{part1}]{part2} + {abs_part}"
    
    expression_str = question_text.replace('×', '*').replace('÷', '/')
    expression_str = re.sub(r'(-?\d+)/(-?\d+)', r'Fraction(\1, \2)', expression_str)
    
    try:
        correct_answer_value = eval(expression_str)
    except:
        return generate(level=level, **kwargs)
    
    if correct_answer_value.denominator == 1:
        correct_answer_str = str(correct_answer_value.numerator)
    else:
        correct_answer_str = f"{correct_answer_value.numerator}/{correct_answer_value.denominator}"
    
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