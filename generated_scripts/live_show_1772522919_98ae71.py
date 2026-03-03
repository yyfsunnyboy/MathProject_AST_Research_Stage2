import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(25):
        v1 = IntegerOps.random_nonzero(-200, 200)
        v2 = IntegerOps.random_nonzero(-10, 10)
        v3 = IntegerOps.random_nonzero(-20, 20)
        v4 = IntegerOps.random_nonzero(-15, 15)
        _o1_healed = False
        try:
            ans_init = IntegerOps.safe_eval(f'[{fmt(v1)}+{fmt(v2)}] / {fmt(v3)} * {fmt(v4)}')
            if type(ans_init).__name__ == 'Fraction' and ans_init.denominator != 1:
                v1 = v1 * ans_init.denominator
                _o1_healed = True
            eval_str = f'[{fmt(v1)}+{fmt(v2)}] / {fmt(v3)} * {fmt(v4)}'
            math_str = f'[{fmt(v1)}+{fmt(v2)}] \\div {fmt(v3)} \\times {fmt(v4)}'
            ans = IntegerOps.safe_eval(eval_str)
            if abs(ans - round(ans)) < 1e-06:
                final_ans = int(round(ans))
                return {'question_text': '計算 $' + math_str + '$ 的值。', 'answer': '', 'correct_answer': str(final_ans), 'mode': 1, '_o1_healed': _o1_healed}
        except Exception:
            continue
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-06:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}