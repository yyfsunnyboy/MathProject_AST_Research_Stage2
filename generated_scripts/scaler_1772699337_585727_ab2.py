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
        if mixed and numerator >= denominator:
            whole = numerator // denominator
            remainder = numerator % denominator
            return f"{whole}\\frac{{{remainder}}}{{{denominator}}}"
        return f"\\frac{{{numerator}}}{{{denominator}}}"

def generate():
    while True:
        try:
            # Generate three mixed numbers with negative values
            a_whole = random.randint(1, 5)
            a_frac_num = random.randint(1, 5)
            a_frac_den = random.randint(2, 5)
            a_sign = -1 if random.random() < 0.5 else 1
            
            b_whole = random.randint(1, 5)
            b_frac_num = random.randint(1, 5)
            b_frac_den = random.randint(2, 5)
            b_sign = -1 if random.random() < 0.5 else 1
            
            c_whole = random.randint(1, 5)
            c_frac_num = random.randint(1, 5)
            c_frac_den = random.randint(2, 5)
            c_sign = -1 if random.random() < 0.5 else 1
            
            # Convert to fractions
            a = Fraction(a_sign * (a_whole * a_frac_den + a_frac_num), a_frac_den