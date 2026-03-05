def generate():
    import random
    from fractions import Fraction
    
    def fmt_num(n):
        return f"({n})" if n < 0 else str(n)
    
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        if mixed:
            whole = val.numerator // val.denominator
            frac = Fraction(val.numerator % val.denominator, val.denominator)
            return f"{whole}\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
        return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
    
    while True:
        try:
            a = Fraction(random.randint(-50, 50), random.randint(2, 10))
            b = Fraction(random.randint(-50, 50), random.randint(2, 10))
            c = Fraction(random.randint(-50, 50), random.randint(2, 10))
            d = Fraction(random.randint(-50, 50), random.randint(2, 10))
            
            if abs(a.numerator) > 50 or abs(b.numerator) > 50 or abs(c.numerator) > 50 or abs(d.numerator) > 50:
                continue
            
            if random.choice([True, False]):
                part1 = f"{fmt_num(a.numerator)} {to_latex(a, True)}"
            else:
                part1 = to_latex(a)
            
            if random.choice([True, False]):
                part2 = f"{fmt_num(b.numerator)} {to_latex(b, True)}"
            else:
                part2 = to_latex(b)
            
            if random.choice([True, False]):
                part3 = f"{fmt_num(c.numerator)} {to_latex(c, True)}"
            else:
                part3 = to_latex(c)
            
            if random.choice([True, False]):
                part4 = f"{fmt_num(d.numerator)} {to_latex(d, True)}"
            else:
                part4 = to_latex(d)
            
            if random.choice([True, False]):
                op1 = "\\div"
            else:
                op1 = "\\times"
            
            if random.choice([True, False]):
                op2 = "\\div"
            else:
                op2 = "\\times"
            
            if random.choice([True, False]):
                op3 = "\\div"
            else:
                op3 = "\\times"
            
            if random.choice([True, False]):
                op4 = "\\div"
            else:
                op4 = "\\times"
            
            if random.choice([True, False]):
                op5 = "\\div"
            else:
                op5 = "\\times"
            
            if random.choice([True, False]):
                op6 = "\\div"
            else:
                op6 = "\\times"
            
            if random.choice([True, False]):
                op7 = "\\div"
            else:
                op7 = "\\times"
            
            if random.choice([True, False]):
                op8 = "\\div"
            else:
                op8 = "\\times"
            
            if random.choice([True, False]):
                op9 = "\\div"
            else:
                op9 = "\\times"
            
            if random.choice([True, False]):
                op10 = "\\div"
            else:
                op10 = "\\times"
            
            if random.choice([True, False]):
                op11 = "\\div"
            else:
                op11 = "\\times"
            
            if random.choice([True, False]):
                op12 = "\\div"
            else:
                op12 = "\\times"
            
            if random.choice([True, False]):
                op13 = "\\div"
            else:
                op13 = "\\times"
            
            if random.choice([True, False]):
                op14 = "\\div"
            else:
                op14 = "\\times"
            
            if random.choice([True, False]):
                op15 = "\\div"
            else:
                op15 = "\\times"
            
            if random.choice([True, False]):
                op16 = "\\div"
            else:
                op16 = "\\times"
            
            if random.choice([True, False]):
                op17 = "\\div"
            else:
                op17 = "\\times"
            
            if random.choice([True, False]):
                op18 = "\\div"
            else:
                op18 = "\\times"
            
            if random.choice([True, False]):
                op19 = "\\div"
            else:
                op19 = "\\times"
            
            if random.choice([True, False]):
                op20 = "\\div"
            else:
                op20 = "\\times"
            
            if random.choice([True, False]):
                op21 = "\\div"
            else:
                op21 = "\\times"
            
            if random.choice([True, False]):
                op22 = "\\div"
            else:
                op22 = "\\times"
            
            if random.choice([True, False]):
                op23 = "\\div"
            else:
                op23 = "\\times"
            
            if random.choice([True, False]):
                op24 = "\\div"
            else:
                op24 = "\\times"
            
            if random.choice([True, False]):
                op25 = "\\div"
            else:
                op25 = "\\times"
            
            if random.choice([True, False]):
                op26 = "\\div"
            else:
                op26 = "\\times"
            
            if random.choice([True, False]):
                op27 = "\\div"
            else:
                op27 = "\\times"
            
            if random.choice([True, False]):
                op28 = "\\div"
            else:
                op28 = "\\times"
            
            if random.choice([True, False]):
                op29 = "\\div"
            else:
                op29 = "\\times"
            
            if random.choice([True, False]):
                op30 = "\\div"
            else:
                op30 = "\\times"
            
            if random.choice([True, False]):
                op31 = "\\div"
            else:
                op31 = "\\times"
            
            if random.choice([True, False]):
                op32 = "\\div"
            else:
                op32 = "\\times"
            
            if random.choice([True, False]):
                op33 = "\\div"
            else:
                op33 = "\\times"
            
            if random.choice([True, False]):
                op34 = "\\div"
            else:
                op34 = "\\times"
            
            if random.choice([True, False]):
                op35 = "\\div"
            else:
                op35 = "\\times"
            
            if random.choice([True, False]):
                op36