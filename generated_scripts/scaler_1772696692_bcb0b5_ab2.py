import random
import math
from fractions import Fraction

class IntegerOps:
    @staticmethod
    def op_to_latex(op_str):
        return op_str
    
    @staticmethod
    def fmt_num(n):
        if n > 0:
            return str(n)
        elif n < 0:
            return f"({n})"
        else:
            return "0"
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        return random.randint(min_val, max_val) if random.randint(0,1) else -random.randint(min_val, max_val)
    
    @staticmethod
    def is_divisible(a, b):
        return a % b == 0
    
    @staticmethod
    def safe_eval(expr):
        try:
            return eval(expr)
        except:
            return None

class FractionOps:
    @staticmethod
    def create(value):
        if isinstance(value, float):
            value = str(value)
        return Fraction(value)
    
    @staticmethod
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return f"{val.numerator}"
        elif mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator % val.denominator)
            if val.numerator < 0:
                return f"({whole}\\frac{{{frac}}}{{{val.denominator}}})"
            else:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
    
    @staticmethod
    def add(a, b):
        return a + b
    
    @staticmethod
    def sub(a, b):
        return a - b
    
    @staticmethod
    def mul(a, b):
        return a * b
    
    @staticmethod
    def div(a, b):
        return a / b

def generate():
    while True:
        try:
            a = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            b = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            c = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            d = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            e = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            f = FractionOps.create(IntegerOps.random_nonzero(-50, 50))
            
            part1 = FractionOps.div(a, b)
            part2 = FractionOps.add(part1, c)
            part3 = FractionOps.mul(d, e)
            part4 = FractionOps.sub(f, part3)
            
            ans = FractionOps.div(part2, d) + part4
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
                
            if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f]):
                continue
                
            math_str = f"\\left( {FractionOps.to_latex(a)} \\div {FractionOps.to_latex(b)} \\right) + \\left( {FractionOps.to_latex(c)} \\times {FractionOps.to_latex(d)} \\right) - {FractionOps.to_latex(e)}"
            
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