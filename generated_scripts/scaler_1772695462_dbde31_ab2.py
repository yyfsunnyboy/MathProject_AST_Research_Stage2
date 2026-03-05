def generate():
    import random
    from fractions import Fraction
    
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        return str(n)
    
    while True:
        # Generate components based on level structure
        a = Fraction(random.randint(-50, 50), random.randint(1, 10))
        b = Fraction(random.randint(-50, 50), random.randint(1, 10))
        c = Fraction(random.randint(-50, 50), random.randint(1, 10))
        d = Fraction(random.randint(-50, 50), random.randint(1, 10))
        e = Fraction(random.randint(-50, 50), random.randint(1, 10))
        f = Fraction(random.randint(-50, 50), random.randint(1, 10))
        g = Fraction(random.randint(-50, 50), random.randint(1, 10))
        
        # Calculate answer based on level structure
        try:
            if abs(a.numerator) > 50 or abs(b.numerator) > 50 or abs(c.numerator) > 50 or abs(d.numerator) > 50 or abs(e.numerator) > 50 or abs(f.numerator) > 50 or abs(g.numerator) > 50:
                continue
                
            # Level 1: [Part1] ÷ Part2 + |Part3|
            part1 = f"\\frac{{{a.numerator}}}{{{a.denominator}}}"
            part2 = fmt_num(b.numerator) if b.denominator == 1 else f"\\frac{{{b.numerator}}}{{{b.denominator}}}"
            part3 = f"|{fmt_num(e.numerator)} \\times {fmt_num(f.numerator)} - {fmt_num(g.numerator)}|"
            
            math_str = f"\\left[{part1} \\div {part2}\\right] + {part3}"
            ans = a / b + abs(e * f - g)
            
            # Level 2: [Part1 - Part4] ÷ Part2 + |Part5|
            part4 = fmt_num(c.numerator) if c.denominator == 1 else f"\\frac{{{c.numerator}}}{{{c.denominator}}}"
            part5 = f"|{fmt_num(d.numerator)} \\times {fmt_num(e.numerator)} - {fmt_num(f.numerator)}|"
            
            math_str = f"\\left[{part1} - {part4}\\right] \\div {part2} + {part5}"
            ans = (a - c) / b + abs(d * e - f)
            
            # Level 3: -[Part1] + |Part3| - (Part4 ÷ Part5) + Part6
            part6 = fmt_num(g.numerator) if g.denominator == 1 else f"\\frac{{{g.numerator}}}{{{g.denominator}}}"
            
            math_str = f"-\\left[{part1}\\right] + {part3} - \\left({fmt_num(d.numerator)} \\div {fmt_num(e.numerator)}\\right) + {part6}"
            ans = -a + abs(d * e - f) - (d / e) + g
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
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