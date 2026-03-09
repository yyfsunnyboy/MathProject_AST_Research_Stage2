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
        # 絕對值區塊數量：1，內部：2數字+1運算子（乘、減）

        v1 = IntegerOps.random_nonzero(1, 100)  # 第一數字，正數
        v2 = IntegerOps.random_nonzero(-10, -1) # 第二數字，負數
        v3 = IntegerOps.random_nonzero(1, 10)   # 第三數字，正數
        v4 = IntegerOps.random_nonzero(1, 10)   # 第四數字，正數
        v5 = IntegerOps.random_nonzero(-15, -1) # 第五數字，負數

        # 建立 eval_str_init（預先計算，保留分數）
        eval_str_init = f"Fraction({v1} * {v2} - {v3})"

        try:
            ans_init = IntegerOps.safe_eval(eval_str_init)
            if type(ans_init).__name__ == "Fraction" and ans_init.denominator != 1:
                if ans_init.denominator > 1000:
                    continue
                v1 = v1 * ans_init.denominator
                _o1_healed = True
            else:
                _o1_healed = False
        except Exception:
            continue

        # 組 eval_str（純 Python 可計算）
        eval_str = f"abs({v1} * {v2} - {v3}) / ({v4} * {v5})"

        # 組 math_str（LaTeX 顯示）
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div \\left( {fmt(v4)} \\times {fmt(v5)} \\right)"

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
        else:
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