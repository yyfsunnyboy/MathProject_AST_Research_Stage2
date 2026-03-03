import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-100, 100)
        v2 = IntegerOps.random_nonzero(-100, 100)
        v3 = IntegerOps.random_nonzero(-100, 100)
        v4 = IntegerOps.random_nonzero(-100, 100)

        # 確保結構同構：(-60) \div [(-7) \times 2 - 1]
        # 原題中：-60 → 負數，-7 → 負數，2 → 正數，1 → 正數
        # 生成時：v1 負數，v2 負數，v3 正數，v4 正數
        if v1 >= 0:
            v1 = -v1
        if v2 >= 0:
            v2 = -v2
        if v3 < 0:
            v3 = -v3
        if v4 < 0:
            v4 = -v4

        # eval_str：純 Python 可計算，用 * / 且保留中括號
        eval_str = f"{v1} / ({v2} * {v3} - {v4})"

        # math_str：LaTeX 顯示，用 \times \div fmt_num
        math_str = f"{fmt(v1)} \\div [{fmt(v2)} \\times {fmt(v3)} - {fmt(v4)}]"

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