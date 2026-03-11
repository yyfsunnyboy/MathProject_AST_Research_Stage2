import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(200):
        # 生成变量 v1~v4 根据原题正负号与区间规范
        v1 = IntegerOps.random_nonzero(-100, -1)  # 第一个数字是负数
        v2 = IntegerOps.random_nonzero(-10, -1)   # 第二个数字是负数
        v3 = IntegerOps.random_nonzero(-15, -1)   # 第三个数字是负数
        v4 = IntegerOps.random_nonzero(1, 100)    # 第四个数字是正数
        
        # 计算分子/分母整数值（不用 safe_eval）
        numerator = (v1 + v2) * v4
        denominator = v3
        
        # 整除预检
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue
        
        final_ans = abs(numerator) // abs(denominator)
        # 根据运算方向确定符号（原题是负数除以负数得正，再乘正数）
        if (v1 < 0 and v2 < 0 and v3 < 0) or (v1 > 0 and v2 > 0 and v3 < 0):
            final_ans = -final_ans
        
        # 组装 eval_str（纯Python可计算）与 math_str（LaTeX显示）
        eval_str = f"abs(({v1} + {v2}) / {v3} * {v4})"
        math_str = f"\\left| {fmt(v1)} + {fmt(v2)} \\right| \\div {fmt(v3)} \\times {fmt(v4)}"
        
        # 安全计算验证
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