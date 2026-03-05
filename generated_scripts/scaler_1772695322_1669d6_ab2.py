def generate():
    import random
    from fractions import Fraction
    
    def fmt_num(n):
        return f"({n})" if n < 0 else str(n)
    
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        elif mixed:
            whole = val.numerator // val.denominator
            frac = Fraction(val.numerator % val.denominator, val.denominator)
            return f"{whole}\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
    
    while True:
        try:
            if random.random() < 0.5:
                a = Fraction(random.randint(-50, 50), random.randint(1, 10))
                b = Fraction(random.randint(-50, 50), random.randint(1, 10))
                c = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                a = Fraction(random.randint(-50, 50), random.randint(1, 10))
                b = Fraction(random.randint(-50, 50), random.randint(1, 10))
                c = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                d = Fraction(random.randint(-50, 50), random.randint(1, 10))
                e = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                d = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                f = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                f = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                g = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                g = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                h = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                h = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                i = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                i = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                j = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                j = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                k = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                k = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                l = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                l = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                m = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                m = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                n = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                n = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                o = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                o = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                p = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                p = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                q = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                q = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                r = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                r = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                s = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                s = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                t = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                t = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            if random.random() < 0.5:
                u = Fraction(random.randint(-50, 50), random.randint(1, 10))
            else:
                u