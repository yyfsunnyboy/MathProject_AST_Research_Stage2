import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        # 1) 依原始常數位置產生變數（只換數字，不動結構）
        # 原題：| 8*(-2)-5 | div 7*(-3)
        # 常數位置：8 → v1, -2 → v2, 5 → v3, 7 → v4, -3 → v5
        # 正負號：v1正, v2負, v3正, v4正, v5負
        v1 = IntegerOps.random_nonzero(1, 100)  # 正數 [1,100]
        v2 = -IntegerOps.random_nonzero(1, 10)  # 負數 [-10,-1]
        v3 = IntegerOps.random_nonzero(1, 10)    # 正數 [1,10]
        v4 = IntegerOps.random_nonzero(1, 15)    # 正數 [1,15]
        v5 = -IntegerOps.random_nonzero(1, 15)   # 負數 [-15,-1]

        # 2) 預先測試算式，使用 Fraction 保留除法分母以攔截截斷
        # 原式：| v1*v2 - v3 | / (v4*v5)
        eval_str_init = f"abs({v1}*{v2} - {v3}) / ({v4}*{v5})"
        try:
            ans_init = IntegerOps.safe_eval(eval_str_init)
            if isinstance(ans_init, Fraction) and ans_init.denominator != 1:
                if ans_init.denominator > 1000:
                    continue
                v1 = v1 * ans_init.denominator
                _o1_healed = True
            else:
                _o1_healed = False
        except Exception:
            continue

        # 3) 變數縮放完成後，重新組裝真正的字串
        eval_str = f"abs({v1}*{v2} - {v3}) / ({v4}*{v5})"
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div \\left( {fmt(v4)} \\times {fmt(v5)} \\right)"

        # 4) 計算最終答案
        try:
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