import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        # 原題結構：| 8×(-2)-5 | ÷ 7×(-3)
        # 變數映射：v1=8, v2=-2, v3=5, v4=7, v5=-3
        # 結構：| v1×v2 - v3 | ÷ v4×v5
        # 二元運算子：×, -, ÷ → 各1個（×2個：×在v1×v2與v4×v5）
        # 絕對值：1個區塊，內含 v1×v2 - v3 → 數字3個，運算子2個（×, -）
        # 括號：1層絕對值，1層分母（無括號在除法中）
        # 負數：v2, v5 帶負號，需保留括號風格

        # Step D1: 建立結構模板（只替換數字）
        # Step D2: 變數映射
        v1 = IntegerOps.random_nonzero(1, 100)  # 正數 [1,100]
        v2 = IntegerOps.random_nonzero(-10, -1) # 負數 [-10,-1]
        v3 = IntegerOps.random_nonzero(1, 10)   # 正數 [1,10]
        v4 = IntegerOps.random_nonzero(1, 15)   # 正數 [1,15]
        v5 = IntegerOps.random_nonzero(-15, -1) # 負數 [-15,-1]

        # Step D3: 結構與運算符保持原題
        # Step D4: 組 eval_str（純 Python，用 abs）
        eval_str_init = f"Fraction({v1} * {v2} - {v3}, {v4} * {v5})"
        try:
            ans_init = IntegerOps.safe_eval(eval_str_init)
        except:
            continue

        # Step D6: 智慧型倒算法（O(1)）
        if isinstance(ans_init, Fraction) and ans_init.denominator != 1:
            if ans_init.denominator > 1000:
                continue
            v1 = v1 * ans_init.denominator
            _o1_healed = True
        else:
            _o1_healed = False

        # Step D5: 組 math_str（LaTeX）
        math_str = f"| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} | \\div {fmt(v4)} \\times {fmt(v5)}"

        # Step D7: 最終計算
        eval_str = f"abs({v1} * {v2} - {v3}) / ({v4} * {v5})"
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