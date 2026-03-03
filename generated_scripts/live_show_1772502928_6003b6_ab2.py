import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-100, 100)
        v2 = IntegerOps.random_nonzero(-100, 100)
        v3 = IntegerOps.random_nonzero(-100, 100)
        v4 = IntegerOps.random_nonzero(-100, 100)

        # 原題結構：(-60) \div [(-7) \times 2 - 1]
        # 保持運算順序：divide -> times -> minus
        # 保持中括號結構
        # 保持負數括號形式

        # 確保 v1 為負數（原題 -60）
        if v1 >= 0:
            v1 = -v1
        # 確保 v2 為負數（原題 -7）
        if v2 >= 0:
            v2 = -v2
        # 確保 v3 為正數（原題 2）
        if v3 < 0:
            v3 = -v3
        # 確保 v4 為正數（原題 1）
        if v4 < 0:
            v4 = -v4

        eval_str = f"{v1} / ({v2} * {v3} - {v4})"
        math_str = f"{fmt(v1)} \\div [ {fmt(v2)} \\times {fmt(v3)} - {fmt(v4)} ]"

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