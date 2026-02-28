import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-10, 10)
        v2 = IntegerOps.random_nonzero(2, 9)
        v3 = IntegerOps.random_nonzero(-15, 15)
        v4 = IntegerOps.random_nonzero(-5, 5)
        v5 = IntegerOps.random_nonzero(1, 10)
        
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '/'])
        op3 = random.choice(['+', '-'])
        
        try:
            # 積木 1: 計算絕對值內的運算
            val_abs_inner = eval(f"({v1}) {op1} {v2}")
            val_abs = abs(val_abs_inner)
            
            # 積木 2: 計算絕對值外的運算
            val_outer = eval(f"({v3}) {op2} ({v4})")
            
            # 積木 3: 最終組合
            ans = eval(f"({v5}) {op3} {val_abs} + {val_outer}")
            
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                
                l_op1 = op1
                l_op2 = op2
                l_op3 = op3
                
                str_abs_inner = f"({fmt(v1)} {l_op1} {fmt(v2)})"
                str_abs = f"|{str_abs_inner}|"
                str_outer = f"({fmt(v3)} {l_op2} {fmt(v4)})"
                math_str = f"{str_abs} {l_op3} {fmt(v5)} + {str_outer}"
                
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