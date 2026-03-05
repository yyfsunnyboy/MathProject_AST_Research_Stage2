def generate():
    from random import randint
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
            # Level 1: [Part1] ÷ Part2 + |Part3|
            part1_num = randint(-50, 50)
            part1_den = randint(2, 10)
            part2_num = randint(-50, 50)
            part2_den = randint(2, 10)
            part3_num = randint(-50, 50)
            part3_den = randint(2, 10)
            
            # Ensure no division by zero
            if part2_den == 0 or part3_den == 0:
                continue
            
            # Format parts
            part1 = to_latex(Fraction(part1_num, part1_den))
            part2 = to_latex(Fraction(part2_num, part2_den))
            part3 = to_latex(Fraction(part3_num, part3_den))
            
            # Build question string
            question = f"計算 $\\left[{part1}\\right] \\div {part2} + \\left|{part3}\\right|$ 的值。"
            
            # Calculate answer
            ans = (Fraction(part1_num, part1_den) / Fraction(part2_num, part2_den)) + abs(Fraction(part3_num, part3_den))
            
            # Format correct answer
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            # Check constraints
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            
            if any(abs(x.numerator) > 50 for x in [Fraction(part1_num, part1_den), Fraction(part2_num, part2_den), Fraction(part3_num, part3_den)]):
                continue
            
            return {
                'question_text': question,
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