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
        numerator = val.numerator
        denominator = val.denominator
        if mixed and numerator >= denominator:
            whole = numerator // denominator
            remainder = numerator % denominator
            if remainder == 0:
                return str(whole)
            return f"{whole}\\frac{{{remainder}}}{{{denominator}}}"
        if numerator < 0:
            return f"-\\frac{{{abs(numerator)}}}{{{denominator}}}"
        return f"\\frac{{{numerator}}}{{{denominator}}}"

def generate():
    while True:
        try:
            a = Fraction(random.randint(-5, 5), random.randint(1, 4))
            b = Fraction(random.randint(-5, 5), random.randint(1, 4))
            c = Fraction(random.randint(-5, 5), random.randint(1, 4))
            
            part1 = f"\\left({IntegerOps.fmt_num(a.numerator)} \\div {IntegerOps.fmt_num(b.denominator)}\\right) \\times {IntegerOps.fmt_num(c.numerator)}"
            part2 = f"\\left({IntegerOps.fmt_num(a.numerator)} + {IntegerOps.fmt_num(b.numerator)}\\right) \\div {IntegerOps.fmt_num(c.denominator)}"
            
            math_str = f"\\frac{{{part1}}}{{{part2}}}"
            
            ans = (a / b) * c
            correct = FractionOps.to_latex(ans)
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
                
            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
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