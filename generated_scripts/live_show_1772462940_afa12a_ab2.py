import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-10, 10)
        v2 = IntegerOps.random_nonzero(-10, 10)
        v3 = IntegerOps.random_nonzero(-10, 10)
        v4 = IntegerOps.random_nonzero(-10, 10)
        v5 = IntegerOps.random_nonzero(-10, 10)

        # 原例題結構：(-8) \times 6 + |(-5) \times 10 - 1|
        # 負數位置：v1, v3 → 負數區間
        # 正數位置：v2, v4, v5 → 正數區間
        if v1 < 0:
            v1 = -abs(v1)
        if v3 < 0:
            v3 = -abs(v3)

        eval_str = f"({v1}) * {v2} + abs(({v3}) * {v4} - {v5})"
        math_str = f"({fmt(v1)}) \\times {fmt(v2)} + |{fmt(v3)} \\times {fmt(v4)} - {fmt(v5)}|"

        try:
            ans = IntegerOps.safe_eval(eval_str)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                return {
                    'question_text': '計算 $' + math_str + '$ 的值。',
                    'answer': '',
                    'correct_answer': str(final_ans),
                    'mode': 1
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