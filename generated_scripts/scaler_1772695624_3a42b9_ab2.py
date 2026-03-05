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
    
    for _ in range(40):
        try:
            a = Fraction(random.randint(-50, 50), random.randint(1, 10))
            b = Fraction(random.randint(-50, 50), random.randint(1, 10))
            c = Fraction(random.randint(-50, 50), random.randint(1, 10))
            d = Fraction(random.randint(-50, 50), random.randint(1, 10))
            e = Fraction(random.randint(-50, 50), random.randint(1, 10))
            f = Fraction(random.randint(-50, 50), random.randint(1, 10))
            g = Fraction(random.randint(-50, 50), random.randint(1, 10))
            h = Fraction(random.randint(-50, 50), random.randint(1, 10))
            
            part1 = (a + b) * c
            part2 = d
            part3 = abs(e * f - g)
            
            if part1.denominator == 1 and part2.denominator == 1 and part3.denominator == 1:
                ans = part1 / part2 + part3
                
                if ans.denominator == 1:
                    correct = str(ans.numerator)
                else:
                    correct = f"{ans.numerator}/{ans.denominator}"
                
                if abs(ans.numerator) > 120 or ans.denominator > 30:
                    continue
                
                math_str = f"\\left[{to_latex(a)} + {to_latex(b)}\\right] \\div {to_latex(c)} + \\left|{to_latex(e)} \\times {to_latex(f)} - {to_latex(g)}\\right|"
                
                if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f, g]):
                    continue
                
                return {
                    'question_text': f'計算 $' + math_str + '$ 的值。',
                    'answer': '',
                    'correct_answer': correct,
                    'mode': 1
                }
        except Exception:
            continue
    
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

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