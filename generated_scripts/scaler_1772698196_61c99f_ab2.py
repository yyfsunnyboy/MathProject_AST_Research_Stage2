import random
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
        if numerator < 0:
            neg = "-"
            num = -numerator
        else:
            neg = ""
            num = numerator
        if mixed:
            whole = num // denominator
            rem = num % denominator
            if rem == 0:
                return str(whole)
            return f"{whole}\\frac{{{rem}}}{{{denominator}}}"
        return f"\\frac{{{neg}{num}}}{{{denominator}}}"

def generate():
    while True:
        try:
            a1 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            a2 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            b1 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            b2 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            c1 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            c2 = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            part1 = f"\\left({IntegerOps.fmt_num(a1.numerator)} \\frac{{{a1.denominator}}}{{{a1.denominator}}}\right)"
            part2 = f"\\left({IntegerOps.fmt_num(b1.numerator)} \\frac{{{b1.denominator}}}{{{b1.denominator}}}\right)"
            part3 = f"\\left({IntegerOps.fmt_num(c1.numerator)} \\frac{{{c1.denominator}}}{{{c1.denominator}}}\right)"
            
            expr = f"-{part1} + {part2} - \\left(-{part3}\\right)"
            
            ans = -a1 + b2 - (-c1)
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            
            return {
                'question_text': f'計算 ${expr}$ 的值。',
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