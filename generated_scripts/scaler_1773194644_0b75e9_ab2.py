import random
import math
from fractions import Fraction

def generate():
    v1 = random.randint(-100, -1)
    v2 = random.randint(1, 100)
    v3 = random.randint(-100, -1)
    v4 = random.randint(1, 100)
    v5 = random.randint(1, 100)

    numerator = v1 * v2
    abs_expr = abs(v3 * v4 - v5)
    total = numerator + abs_expr

    eval_str = f"({v1} * {v2}) + abs({v3} * {v4} - {v5})"
    math_str = f"\\left( {v1} \\times {v2} \\right) + \\left| {v3} \\times {v4} - {v5} \\right|"

    return {
        'question_text': f'計算 ${math_str}$ 的值。',
        'answer': '',
        'correct_answer': str(total),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}