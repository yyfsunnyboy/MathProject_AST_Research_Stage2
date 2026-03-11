import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # Step D1: 原題結構為 [(-20)+(-10)]÷(-5)×3 → 4 個數字，3 個運算子，1 個中括號
        # Step D2: 映射變數 v1, v2, v3, v4 → 對應原題位置
        v1 = IntegerOps.random_nonzero(-100, -1)  # 第一個負數
        v2 = IntegerOps.random_nonzero(-10, -1)   # 第二個負數
        v3 = IntegerOps.random_nonzero(-15, -1)   # 除數（負數）
        v4 = IntegerOps.random_nonzero(1, 15)     # 乘數（正數）

        # Step D3: 整除預檢（分子 = (v1 + v2), 分母 = v3 * v4）
        numerator = v1 + v2
        denominator = v3 * v4

        # Step D4: 整除檢查（強制整除）
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 計算結果符號：原題為正（因負負得正，再除負得負，再乘正得負？需驗證）
        # 但題型結構中：[(-a)+(-b)]÷(-c)×d → 符號：(-a -b) = 負，÷(-c) = 正，×d = 正 → 最終為正
        # 所以最終結果應為正數
        final_ans = abs(final_ans)  # 強制正數

        # Step D5: 組裝 eval_str 與 math_str
        eval_str = f"({v1}+{v2})/({v3}*{v4})"
        math_str = f"\\left[\\left({fmt(v1)}+{fmt(v2)}\\right}\\right]\\div \\left({fmt(v3)}\\right) \\times {fmt(v4)}"

        # Step D6: 驗證計算結果（安全評估）
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