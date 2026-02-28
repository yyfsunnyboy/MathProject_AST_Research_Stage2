import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-15, 15)
        v2 = IntegerOps.random_nonzero(-15, 15)
        v3 = IntegerOps.random_nonzero(-15, 15)
        v4 = IntegerOps.random_nonzero(-15, 15)
        v5 = IntegerOps.random_nonzero(-15, 15)
        v6 = IntegerOps.random_nonzero(-15, 15)
        v7 = IntegerOps.random_nonzero(-15, 15)
        
        op1 = random.choice(['*', '/'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['*', '/'])
        op4 = random.choice(['+', '-'])
        op5 = random.choice(['*', '/'])
        op6 = random.choice(['+', '-'])
        
        try:
            inner_str = f"({fmt(v1)}) {op1} ({fmt(v2)}) {op2} ({fmt(v3)}) {op3} ({fmt(v4)})"
            val_inner = eval(inner_str)
            part_abs = abs(val_inner)
            
            bracket_str = f"({fmt(v5)}) {op5} ({fmt(v6)}) {op6} ({fmt(v7)})"
            part_bracket = eval(bracket_str)
            
            ans = eval(f"{part_abs} {op4} {part_bracket}")
            
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                
                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op
                
                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                l_op3 = to_latex(op3)
                l_op4 = to_latex(op4)
                l_op5 = to_latex(op5)
                l_op6 = to_latex(op6)
                
                str_abs = f"({fmt(v1)}) {l_op1} ({fmt(v2)}) {l_op2} ({fmt(v3)}) {l_op3} ({fmt(v4)})"
                str_bracket = f"({fmt(v5)}) {l_op5} ({fmt(v6)}) {l_op6} ({fmt(v7)})"
                
                math_str = f"({str_abs}) {l_op4} ({str_bracket})"
                
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