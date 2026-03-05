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
            a_num, a_den = random.randint(-50, 50), random.randint(1, 10)
            b_num, b_den = random.randint(-50, 50), random.randint(1, 10)
            c_num, c_den = random.randint(-50, 50), random.randint(1, 10)
            
            a = Fraction(a_num, a_den)
            b = Fraction(b_num, b_den)
            c = Fraction(c_num, c_den)
            
            part1 = to_latex(a)
            part2 = to_latex(b)
            part3 = to_latex(c)
            
            if random.choice([True, False]):
                part1 = f"\\left({part1}\\right)"
                part2 = f"\\left({part2}\\right)"
                part3 = f"\\left({part3}\\right)"
            
            if random.choice([True, False]):
                part1 = f"{fmt_num(a_num)} \\frac{{{a_den}}}{{{b_den}}}"
                part2 = f"{fmt_num(b_num)} \\frac{{{b_den}}}{{{c_den}}}"
                part3 = f"{fmt_num(c_num)} \\frac{{{c_den}}}{{{a_den}}}"
            
            if random.choice([True, False]):
                part1 = f"\\left({part1}\\right)"
                part2 = f"\\left({part2}\\right)"
                part3 = f"\\left({part3}\\right)"
            
            math_str = f"{part1} \\div {part2} + {part3}"
            ans = a / b + c
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            
            if any(abs(x.numerator) > 50 for x in [a, b, c]):
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