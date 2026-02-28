import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-30, 30)
        v2 = IntegerOps.random_nonzero(-15, 15)
        v3 = IntegerOps.random_nonzero(-10, 10)
        v4 = IntegerOps.random_nonzero(-5, 5)
        v5 = IntegerOps.random_nonzero(-3, 3)

        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['*', '/'])

        try:
            # 積木 1: 計算絕對值內的運算
            val_inner = eval(f"{fmt(v1)} {op1} {fmt(v2)}")
            val_abs = abs(val_inner)

            # 積木 2: 計算中括號內的運算
            val_bracket = eval(f"{fmt(v3)} {op2} {val_abs}")

            # 積木 3: 最終運算
            ans = eval(f"{fmt(v4)} {op3} {val_bracket}")

            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))

                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op

                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                l_op3 = to_latex(op3)

                str_abs = f"|{fmt(v1)} {l_op1} {fmt(v2)}|"
                math_str = f"({fmt(v4)}) {l_op3} [{fmt(v3)} {l_op2} {str_abs}]"

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