import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        dividend = IntegerOps.random_nonzero(-100, 100)
        base = IntegerOps.random_nonzero(-10, 10)
        multiplier = IntegerOps.random_nonzero(-5, 5)
        subtractor = IntegerOps.random_nonzero(-5, 5)

        try:
            # 積木組裝替換法
            val_bracket = eval(f"({fmt(base)}) \\times {fmt(multiplier)} - {fmt(subtractor)}")
            ans = eval(f"{fmt(dividend)} \\div {val_bracket}")

            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))

                # LaTeX 組裝
                math_str = f"({fmt(dividend)}) \\div [({fmt(base)}) \\times {fmt(multiplier)} - {fmt(subtractor)}]"

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