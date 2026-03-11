import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    # 變數個數: 5 個
    # 運算符號數與種類: 4 個 (分別為 ×=2, -=1, ÷=1)
    # 特殊結構: 絕對值 1 個，負數括號 2 個

    fmt = IntegerOps.fmt_num

    for _ in range(200):
        v1 = IntegerOps.random_nonzero(1, 100) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)
        v5 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)

        # 組合分子與分母（純整數運算，不使用 Fraction）
        numerator = abs(v1 * v2) - v3
        denominator = v4 * v5

        # 整除預檢
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 計算最終符號（根據運算方向）
        if denominator < 0:
            final_ans = -final_ans

        # 組裝 eval_str 與 math_str
        eval_str = f"abs({v1} * {v2}) - {v3} / ({v4} * {v5})"
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} \\right| - {fmt(v3)} \\div ({fmt(v4)} \\times {fmt(v5)})"

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