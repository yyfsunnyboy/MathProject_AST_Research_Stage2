import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    # 變數個數: 2 個
    # 運算符號數與種類: 1 個 (分別為 +)
    # 特殊結構: 無

    fmt = IntegerOps.fmt_num

    for _ in range(200):
        v1 = IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 100)

        numerator = v1 + v2
        denominator = 1

        if abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)

        eval_str = f"{v1} + {v2}"
        math_str = f"{fmt(v1)} + {fmt(v2)}"

        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-6:
            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': str(int(round(ans))),
                'mode': 1,
            }

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}