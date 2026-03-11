import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # 1) 依原始常數位置產生變數（只換數字，不動結構）
        # 原題有 2 個數字 → 只能生成 v1, v2
        v1 = IntegerOps.random_nonzero(1, 100) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)

        # 2) 直接計算分子/分母整數值（不用 safe_eval，不用 Fraction 縮放）
        numerator = v1
        denominator = v2

        # 3) 整除預檢：用 % 判斷
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 負號由運算方向決定：若 v1 / v2 為負，則結果為負
        if (v1 < 0) ^ (v2 < 0):
            final_ans = -final_ans

        # 4) 組裝 eval_str（純 Python 可計算，含 abs()）與 math_str（LaTeX 顯示）
        # 原題無絕對值，故 eval_str 不用 abs
        eval_str = f"{v1} / {v2}"
        math_str = f"{fmt(v1)} \\div {fmt(v2)}"

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