import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = Fraction(-7, 8)
    b = Fraction(-3, 8)
    result = a - b
    correct_answer = f'{result.numerator}/{result.denominator}'
    question_text = f'\\left(-\\frac{{7}}{{8}}\\right) - \\left(-\\frac{{3}}{{8}}\\right)'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}