import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(25):
        v1 = IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(1, 15)
        v5 = IntegerOps.random_nonzero(1, 15)
        v6 = IntegerOps.random_nonzero(1, 15)
        eval_str_init = f'[{v1} * ({v2} - {v3})] / abs({v4} * {v5} - {v6})'
        ans_init = IntegerOps.safe_eval(eval_str_init)
        if isinstance(ans_init, Fraction) and ans_init.denominator != 1:
            if ans_init.denominator > 1000:
                continue
            v1 = v1 * ans_init.denominator
            _o1_healed = True
        else:
            _o1_healed = False
        eval_str = f'[{v1} * ({v2} - {v3})] / abs({v4} * {v5} - {v6})'
        math_str = f'[{fmt(v1)} \\times ({fmt(v2)} - {fmt(v3)})] \\div |{fmt(v4)} \\times {fmt(v5)} - {fmt(v6)}|'
        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-06:
            final_ans = int(round(ans))
            return {'question_text': '計算 $' + math_str + '$ 的值。', 'answer': '', 'correct_answer': str(final_ans), 'mode': 1, '_o1_healed': _o1_healed}
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1000000.0:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}