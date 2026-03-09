import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        # 原題結構：| 8*(-2)-5 | div 7*(-3)
        # 變數映射：v1=8, v2=-2, v3=5, v4=7, v5=-3
        # 結構：| v1*v2 - v3 | div v4*v5
        # 運算符：乘、減、絕對值、除
        # 數字數量：5
        # 運算子數量：4（乘、減、絕對值、除）
        # 絕對值區塊數量：1
        # 絕對值內：數字2個，運算子1個（減）

        v1 = IntegerOps.random_nonzero(1, 100)  # 正數
        v2 = IntegerOps.random_nonzero(-10, -1) # 負數
        v3 = IntegerOps.random_nonzero(1, 10)   # 正數
        v4 = IntegerOps.random_nonzero(1, 10)   # 正數
        v5 = IntegerOps.random_nonzero(-15, -1) # 負數

        # 建立 eval_str_init（保留分母，用 Fraction 預先計算）
        eval_str_init = f"Fraction({v1} * {v2} - {v3}, {v4} * {v5})"
        try:
            ans_init = IntegerOps.safe_eval(eval_str_init)
        except:
            continue

        # 智慧型倒算法：若分母不為1，乘回 v1 強制整除
        if isinstance(ans_init, Fraction) and ans_init.denominator != 1:
            if ans_init.denominator > 1000:
                continue
            v1 = v1 * ans_init.denominator
            _o1_healed = True
        else:
            _o1_healed = False

        # 重新組裝 eval_str（純 Python 可計算）
        eval_str = f"abs({v1} * {v2} - {v3}) / ({v4} * {v5})"
        math_str = f"abs({fmt(v1)} \\times {fmt(v2)} - {fmt(v3)}) \\div ({fmt(v4)} \\times {fmt(v5)})"

        # 計算最終答案
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