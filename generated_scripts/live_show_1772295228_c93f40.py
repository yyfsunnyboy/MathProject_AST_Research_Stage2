import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(3000):
        dividend = IntegerOps.random_nonzero(-100, 100)
        divisor = IntegerOps.random_nonzero(-10, -1)
        
        try:
            quotient = dividend // divisor
            remainder = dividend % divisor
            if remainder != 0:
                continue
                
            # 組裝 LaTeX
            math_str = f"({fmt(dividend)}) \\div ({fmt(divisor)})"
            
            question_text = r"計算 $$" + math_str + r"$$ 的值。"
            
            return {
                'question_text': question_text,
                'correct_answer': str(quotient),
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