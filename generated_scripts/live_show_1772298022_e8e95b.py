import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(1, 30)
        v2 = IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(-20, 20)
        v4 = IntegerOps.random_nonzero(-15, 15)
        v5 = IntegerOps.random_nonzero(-10, 10)

        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['*', '/'])
        op4 = random.choice(['+', '-'])

        try:
            # 積木 1: 計算中括號內的內容
            val_bracket = eval(f"{v1} {op1} {v2}")

            # 積木 2: 計算絕對值內的內容
            val_abs_inner = eval(f"({v3}) {op2} ({v4})")
            val_abs = abs(val_abs_inner)

            # 積木 3: 最終計算
            ans = eval(f"({val_bracket}) {op3} {val_abs} {op4} {v5}")

            # 黃金判斷 - 是否整除?
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))

                # 組裝 LaTeX
                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op

                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                l_op3 = to_latex(op3)
                l_op4 = to_latex(op4)

                str_bracket = f"[{fmt(v1)} {l_op1} {fmt(v2)}]"
                str_abs = f"|{fmt(v3)} {l_op2} {fmt(v4)}|"
                math_str = f"{str_bracket} {l_op3} {str_abs} {l_op4} {fmt(v5)}"

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