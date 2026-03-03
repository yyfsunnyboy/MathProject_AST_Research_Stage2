import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        v1 = IntegerOps.random_nonzero(-100, 100)
        v2 = IntegerOps.random_nonzero(-10, 10)
        v3 = IntegerOps.random_nonzero(-10, 10)

        _o1_healed = False
        try:
            # 預先測試算式，使用 Fraction 保留除法分母以攔截截斷
            ans_init = IntegerOps.safe_eval(f"{v1} * {v2} / {v3}")

            # 智慧型倒算法 (O(1) 攔截)：遇到除不盡，直接把分母乘回第一個變數
            if type(ans_init).__name__ == "Fraction" and ans_init.denominator != 1:
                if ans_init.denominator > 1000:
                    continue
                v1 = v1 * ans_init.denominator
                _o1_healed = True

            # 變數縮放完成後，重新組裝真正的字串
            eval_str = f"{v1} * {v2} / {v3}"
            math_str = f"{fmt(v1)} \\times {fmt(v2)} \\div {fmt(v3)}"

            ans = IntegerOps.safe_eval(eval_str)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                return {
                    'question_text': '計算 $' + math_str + '$ 的值。',
                    'answer': '',
                    'correct_answer': str(final_ans),
                    'mode': 1,
                    '_o1_healed': _o1_healed
                }
        except Exception:
            continue

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