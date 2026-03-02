import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-20, 20)
        v2 = IntegerOps.random_nonzero(-9, 9)
        v3 = IntegerOps.random_nonzero(-15, 15)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '/'])
        l_op1 = IntegerOps.op_to_latex(op1)
        l_op2 = IntegerOps.op_to_latex(op2)
        inner_eval = f'{v1} {op1} {v2}'
        inner_val = IntegerOps.safe_eval(inner_eval)
        val_abs = abs(inner_val)
        eval_str = f'[{v1} {op1} {v2}] {l_op2} {v3}'
        math_str = f'[{fmt(v1)} {l_op1} {fmt(v2)}] {l_op2} {fmt(v3)}'
        try:
            ans = IntegerOps.safe_eval(eval_str)
            if abs(ans - round(ans)) < 1e-06:
                final_ans = int(round(ans))
                question_text = '計算 $' + math_str + '$ 的值。'
                return {'question_text': question_text, 'correct_answer': str(final_ans), 'mode': 1}
        except (ZeroDivisionError, SyntaxError, Exception):
            continue
    return {'question_text': 'Error', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-06:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}