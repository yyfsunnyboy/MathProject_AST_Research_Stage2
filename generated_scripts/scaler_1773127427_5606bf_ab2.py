import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(200):
        # 1) 根据原始常数位置生成变量（只换数字，不動結構）
        v1 = IntegerOps.random_nonzero(-100, -1)  # 第一個變數：負數 [-100,-1]
        v2 = IntegerOps.random_nonzero(-10, -1)   # 第二個變數：負數 [-10,-1]
        v3 = IntegerOps.random_nonzero(1, 10)     # 第三個變數：正數 [1,10]
        v4 = IntegerOps.random_nonzero(1, 15)     # 第四個變數：正數 [1,15]
        
        # 2) 直接計算分子/分母整數值（不用 safe_eval，不用 Fraction 縮放）
        numerator = v1
        denominator = (v2 * v3 - v4)
        
        # 3) 整除預檢：用 % 判斷
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue
        
        final_ans = abs(numerator) // abs(denominator)
        # 若分母為負，結果取負號（依題目運算方向而定）
        if denominator < 0:
            final_ans *= -1
        
        # 4) 組裝 eval_str（純 Python 可計算，含 abs()）與 math_str（LaTeX 顯示）
        eval_str = f"abs({v1}) / ({v2} * {v3} - {v4})"
        math_str = f"\\left| {fmt(v1)} \\right| \\div ({fmt(v2)} \\times {fmt(v3)} - {fmt(v4)})"
        
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