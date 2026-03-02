import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        # 原題數字位置：(-5), 3, 4, 2, 28, (-7), (-3)
        # 絕對值內：(-5)×3-4×2 → 4 個數字，3 個運算子
        # 中括號內：28÷(-7)-(-3) → 3 個數字，2 個運算子
        # 數字範圍：負數取 [-10, -1]，正數取 [1, 10]

        v1 = IntegerOps.random_nonzero(-10, -1)  # 原為 -5
        v2 = IntegerOps.random_nonzero(1, 10)    # 原為 3
        v3 = IntegerOps.random_nonzero(1, 10)    # 原為 4
        v4 = IntegerOps.random_nonzero(1, 10)    # 原為 2
        v5 = IntegerOps.random_nonzero(1, 10)    # 原為 28
        v6 = IntegerOps.random_nonzero(-10, -1)  # 原為 -7
        v7 = IntegerOps.random_nonzero(-10, -1)  # 原為 -3

        try:
            # eval_str：可計算版本（* /，必要時 abs(...)）
            eval_str = f"abs({v1} * {v2} - {v3} * {v4}) + [{v5} / {v6} - {v7}]"

            # math_str：顯示版本（\\times / \\div + fmt_num）
            math_str = f"|{fmt(v1)}\\times{v2}-{v3}\\times{v4}|+[{v5}\\div{fmt(v6)}-{fmt(v7)}]"

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