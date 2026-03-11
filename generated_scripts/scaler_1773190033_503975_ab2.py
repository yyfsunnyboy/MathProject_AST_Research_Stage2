import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(200):
        # 1) 原題結構：v1 × v2 - v3 ÷ v4（v4為負數）
        # 2) 變數範圍：v1[1-100]正, v2[1-10]正, v3[1-10]正, v4[-15--1]負
        v1 = IntegerOps.random_nonzero(1, 100)
        v2 = IntegerOps.random_nonzero(1, 10)
        v3 = IntegerOps.random_nonzero(1, 10)
        v4 = IntegerOps.random_nonzero(-15, -1)
        
        # 3) 整除預檢
        numerator = v1 * v2 - v3
        denominator = v4
        
        if abs(numerator) % abs(denominator) != 0:
            continue
        
        final_ans = abs(numerator) // abs(denominator)
        if denominator < 0:  # 分母為負時取反
            final_ans *= -1
        
        # 4) 組裝 eval_str（純計算）與 math_str（LaTeX）
        eval_str = f"abs({v1} * {v2} - {v3}) / ({v4})"
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div {fmt(v4)}"
        
        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-6:
            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': str(int(round(ans))),
                'mode': 1,
            }

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}