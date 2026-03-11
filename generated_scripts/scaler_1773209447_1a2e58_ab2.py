import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(200):
        # 1) 依原始常數位置產生變數（只換數字，不動結構）
        v1 = IntegerOps.random_nonzero(-100, -1)  # 第一個變數為負數
        v2 = IntegerOps.random_nonzero(1, 10)     # 第二個變數為正數
        v3 = IntegerOps.random_nonzero(-10, -1)   # 第三個變數為負數
        v4 = IntegerOps.random_nonzero(1, 15)     # 第四個變數為正數
        v5 = IntegerOps.random_nonzero(1, 15)     # 第五個變數為正數
        
        # 2) 直接計算分子/分母整數值（不用 safe_eval，不用 Fraction 縮放）
        numerator = abs(v3 * v4 - v5)
        denominator = v1 * v2
        
        # 3) 整除預檢：用 % 判斷
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue
        
        final_ans = abs(numerator) // abs(denominator)
        # 若分母為負，結果取負號（依題目運算方向而定）
        
        # 4) 組裝 eval_str（純 Python 可計算，含 abs()）與 math_str（LaTeX 顯示）
        eval_str = f"abs({v3} * {v4} - {v5}) / ({v1} * {v2})"
        math_str = f"\\left| {fmt(v3)} \\times {fmt(v4)} - {fmt(v5)} \\right| \\div {fmt(v1)} \\times {fmt(v2)}"
        
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