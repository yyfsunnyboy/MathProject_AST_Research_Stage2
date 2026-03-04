import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = Fraction(2, 3)
    b = Fraction(3, 4)
    c = Fraction(1, 6)
    expr = f'\\frac{{{a.numerator}}}{{{a.denominator}}} - (-\\frac{{{b.numerator}}}{{{b.denominator}}}) + (-\\frac{{{c.numerator}}}{{{c.denominator}}})'
    result = a - -b + -c
    correct_answer = f'{result.numerator}/{result.denominator}'
    return {'question_text': f'計算 $   {expr}   $ 的值。', 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}