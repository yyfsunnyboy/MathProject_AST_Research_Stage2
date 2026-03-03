import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        v1 = IntegerOps.random_nonzero(-100, 100)
        v2 = IntegerOps.random_nonzero(-10, 10)
        v3 = IntegerOps.random_nonzero(-10, 10)
        v4 = IntegerOps.random_nonzero(-15, 15)

        # 預先計算，確保整除
        try:
            ans_init = Fraction(v1, (v2 * v3 - v4))
            if ans_init.denominator != 1:
                v1 = v1 * ans_init.denominator
                ans_init = Fraction(v1, (v2 * v3 - v4))
        except:
            continue

        eval_str = f"{v1} / ({v2} * {v3} - {v4})"
        math_str = f"{fmt(v1)} \\div [({fmt(v2)} \\times {fmt(v3)}) - {fmt(v4)}]"

        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-6:
            final_ans = int(round(ans))
            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': str(final_ans),
                'mode': 1,
                '_o1_healed': False
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