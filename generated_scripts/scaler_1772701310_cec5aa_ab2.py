import random
from fractions import Fraction

class IntegerOps:
    @staticmethod
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        else:
            return str(n)

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        elif mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator) % val.denominator
            return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def generate_question():
    # Generate three mixed fractions with negative signs
    terms = []
    for _ in range(3):
        sign = random.choice([-1, 1])
        whole = random.randint(1, 5)
        numerator = random.randint(1, whole)
        denominator = random.randint(numerator + 1, whole * 2)
        frac = Fraction(numerator, denominator) * sign
        terms.append(frac)
    
    # Format the question with proper LaTeX structure
    term_strs = []
    for