import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-10, 10)
        v2 = IntegerOps.random_nonzero(-10, 10)
        v3 = IntegerOps.random_nonzero(-10, 10)
        v4 = IntegerOps.random_nonzero(-10, 10)

        # 原題結構：(-9) × [24 - 8 × (-2)]
        # 負數需保留括號格式
        if v1 < 0:
            v1_str = fmt(v1)
        else:
            v1_str = fmt(v1)

        if v2 < 0:
            v2_str = fmt(v2)
        else:
            v2_str = fmt(v2)

        if v3 < 0:
            v3_str = fmt(v3)
        else:
            v3_str = fmt(v3)

        if v4 < 0:
            v4_str = fmt(v4)
        else:
            v4_str = fmt(v4)

        # 結構同構：A × [B - C × D]
        eval_str = f"{v1} * ({v2} - {v3} * {v4})"
        math_str = f"{fmt(v1)} \\times [{fmt(v2)} - {fmt(v3)} \\times {fmt(v4)}]"

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