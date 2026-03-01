import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-20, 20)
        v2 = IntegerOps.random_nonzero(-9, 9)
        v3 = IntegerOps.random_nonzero(-15, 15)
        v4 = IntegerOps.random_nonzero(-9, 9)
        v5 = IntegerOps.random_nonzero(-10, 10)

        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '/'])
        op3 = random.choice(['+', '-'])

        try:
            val_bracket = eval(f"({fmt(v1)} {op1} {fmt(v2)})")
            val_div = eval(f"{val_bracket} {op2} {fmt(v3)}")
            ans = eval(f"{val_div} {op3} {fmt(v4)}")

            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))

                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op

                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                l_op3 = to_latex(op3)

                math_str = f"[{fmt(v1)} {l_op1} {fmt(v2)}] {l_op2} {fmt(v3)} {l_op3} {fmt(v4)}"

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