# 以下是根据需求生成分数四则运算题目的完整代码实现
import random
import math
from fractions import Fraction

class IntegerOps:
    @staticmethod
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        return str(n)

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        if mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator) % val.denominator
            if val.numerator < 0:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
            return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def generate():
    while True:
        try:
            # Level 1: [Part1] ÷ Part2 + |Part3|
            part1_num = random.randint(-5, 5)
            part1_den = random.randint(2, 7)
            part2_num = random.randint(-5, 5)
            part2_den = random.randint(2, 7)
            part3_num = random.randint(-5, 5)
            part3_den = random.randint(2, 7)
            
            # 计算分数部分
            part1 = Fraction(part1_num, part1_den)
            part2 = Fraction(part2_num, part2_den)
            part3 = Fraction(part3_num, part3_den)
            
            # 构建题目结构
            math_str = f"\\left[{FractionOps.to_latex(part1)}\\right] \\div {FractionOps.to_latex(part2)} + \\left|{FractionOps.to_latex(part3)}\\right|"
            
            # 计算答案
            ans = (part1 / part2) + abs(part3)
            
            # 格式化正确答案
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            # 检查是否符合所有限制条件
            if (abs(ans.numerator) <= 120 and ans.denominator <= 30 and 
                all(abs(x.numerator) <= 50 for x in [part1, part2, part3])):
                return {
                    'question_text': f'計算 $' + math_str + '$ 的值。',
                    'answer': '',
                    'correct_answer': correct,
                    'mode': 1
                }
        except:
            continue

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}