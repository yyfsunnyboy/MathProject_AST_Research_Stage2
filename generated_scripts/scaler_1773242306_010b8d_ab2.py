import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    # 變數個數: 4 個
    # 運算符號數與種類: 3 個 (分別為 +, ÷, ×)
    # 特殊結構: 1 個中括號區塊

    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # Step D1: 解析題型結構
        # Step D2: 將常數映射為變數 v1, v2, v3, v4
        # Step D3: 根據正負號與區間生成變數
        v1 = IntegerOps.random_nonzero(1, 100) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(1, 15) if random.choice([True, False]) else -IntegerOps.random_nonzero(1, 15)

        # Step D4: 組出 eval_str 與 math_str
        # 保持原題結構：[v1 + v2] ÷ v3 × v4
        # 但注意：v3 是除數，必須用 IntegerOps.random_nonzero 保證非零
        numerator = v1 + v2
        denominator = v3
        final_ans = abs(numerator) // abs(denominator) if abs(numerator) % abs(denominator) == 0 else None

        # 若不整除，重試
        if final_ans is None:
            continue

        # 計算最終結果（考慮符號）
        if (numerator < 0 and denominator < 0) or (numerator > 0 and denominator > 0):
            final_ans = abs(numerator) // abs(denominator)
        else:
            final_ans = -abs(numerator) // abs(denominator)

        # Step D5: 組裝 eval_str 與 math_str
        eval_str = f"({v1} + {v2}) / {v3} * {v4}"
        math_str = f"\\left({fmt(v1)} + {fmt(v2)}\\right) \\div {fmt(v3)} \\times {fmt(v4)}"

        # Step D6: 整除預檢（已做）
        # Step D7: 回傳

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