import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a, b, c, d, e, f, g = [random.randint(1, 20) for _ in range(7)]
        expr = f"[(-{a})+(-{b})]÷(-{c})×{d}+|{e}×(-{f})-{g}|"
        calc = ((-a - b) // (-c)) * d + abs(e * (-f) - g)
    else:
        a, b, c, d, e, f, g = [random.randint(-50, 50) for _ in range(7)]
        expr = f"[({a})+({b})]÷({c})×{d}+|{e}×({f})-{g}|"
        calc = ((a + b) // c) * d + abs(e * f - g)
    return {
        'question_text': f"計算 `{expr}` 的值。",
        'answer': '',
        'correct_answer': str(calc),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': int(user_answer) == int(correct_answer),
            'result': '正確' if int(user_answer) == int(correct_answer) else '錯誤'
        }
    except:
        return {'correct': False, 'result': '錯誤'}