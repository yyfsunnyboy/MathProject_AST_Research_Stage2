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
        if mixed and numerator > denominator:
            whole = numerator // denominator
            remainder = numerator % denominator
            return f"{whole}\\frac{{{remainder}}}{{{denominator}}}"
        return f"\\frac{{{numerator}}}{{{denominator}}}"

def generate_problem():
    terms = []
    for _ in range(3):
        sign = random.choice(['+', '-'])
        whole = random.randint(1, 5)
        numerator = random.randint(1, 4)
        denominator = random.randint(2, 5)
        frac = Fraction(numerator, denominator)
        term = f"{sign}{whole} {numerator}/{denominator}"
        terms.append(term)
    
    problem = "計算 $".format(" + ".join(terms)) + "$ 的值。"
    return problem

def check_answer(user_ans, correct_ans):
    try:
        ua = Fraction(user_ans.replace(" ", ""))
        ca = Fraction(correct_ans.replace(" ", ""))
        return ua == ca
    except:
        return False

problem = generate_problem()
correct_ans = "0"  # Placeholder for actual calculation