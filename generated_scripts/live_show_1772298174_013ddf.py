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

        try:
            # 積木 1: 計算絕對值內的運算
            val_inner = eval(f"{v1} * ({v2} - {v3})")
            val_abs = abs(val_inner)

            # 積木 2: 計算除法與乘法
            val_div = val_abs / v4
            ans = val_div * v5

            # 黃金判斷 - 是否整除
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))

                # 組裝 LaTeX
                l_times = '\\times'
                l_div = '\\div'

                str_abs = f"|{fmt(v1)} \\times ({fmt(v2)} - {fmt(v3)})|"
                math_str = f"{str_abs} {l_div} {fmt(v4)} \\times {fmt(v5)}"

                question_text = r"計算 $$" + math_str + r"$$ 的值。"

                return {
                    'question_text': question_text,
                    'correct_answer': str(final_ans),
                    'mode': 1
                }
        except (ZeroDivisionError, SyntaxError):
            continue

    return {'question_text': "Error", 'correct_answer': "0", 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip(): return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6: return {'correct': True, 'result': '正確'}
    except: pass
    return {'correct': False, 'result': '錯誤'}