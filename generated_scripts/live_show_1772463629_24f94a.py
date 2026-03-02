import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(1, 20)
        v2 = IntegerOps.random_nonzero(1, 20)
        v3 = IntegerOps.random_nonzero(-20, -1)
        v4 = IntegerOps.random_nonzero(1, 20)
        v5 = IntegerOps.random_nonzero(1, 20)
        v6 = IntegerOps.random_nonzero(1, 20)
        v7 = IntegerOps.random_nonzero(-20, -1)
        try:
            eval_str = f"abs({v1}-{v2}*({v3})+{v4})-{v5}*{v6}/({v7})"
            ans = IntegerOps.safe_eval(eval_str)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                math_str = f"|{fmt(v1)}-{fmt(v2)}\\times({v3})+{fmt(v4)}|-{fmt(v5)}\\times{fmt(v6)}\\div({v7})"
                question_text = "計算 $" + math_str + "$ 的值。"
                return {
                    'question_text': question_text,
                    'correct_answer': str(final_ans),
                    'mode': 1
                }
        except Exception:
            continue
    return {'question_text': 'Error', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}
