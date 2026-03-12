import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    # 變數個數: 4 個
    # 運算符號數與種類: 3 個 (分別為 ÷, ×, -)
    # 特殊結構: 1 個中括號區塊

    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # Step D1: 解析題型結構
        # Step D2: 將常數映射為變數 v1, v2, v3, v4
        # Step D3: 給變數取值範圍（根據原題正負號與 D3 規範）
        v1 = IntegerOps.random_nonzero(1, 100) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)

        # Step D4: 組出 eval_str（純 Python 可計算）
        # 注意：中括號內運算為 (-7) * 2 - 1 → 保持結構
        # 原題：(-60) ÷ [(-7) × 2 - 1]
        # 結構：分子 = v1，分母 = [v2 * v3 - v4]
        numerator = v1
        denominator = (v2 * v3) - v4

        # Step D6: 整除預檢
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 分母為負時，結果應為負（根據原題運算方向）
        if denominator < 0:
            final_ans = -final_ans

        # Step D5: 組裝 eval_str 與 math_str
        # eval_str 必須用純 Python 表達，不使用 LaTeX 符號
        eval_str = f"{v1} / ({v2} * {v3} - {v4})"
        math_str = f"\\left({fmt(v1)}\\right) \\div \\left[ \\left({fmt(v2)} \\times {fmt(v3)}\\right) - {fmt(v4)} \\right]"

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