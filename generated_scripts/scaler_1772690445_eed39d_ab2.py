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
            # Level 1: [Part1] ÷ Part2 + |Part3|
            part1_num = random.randint(-50, 50)
            part1_den = random.choice([2, 3, 4, 5])
            part1 = Fraction(part1_num, part1_den)
            
            part2_num = random.randint(1, 10)
            part2_den = random.choice([2, 3, 4, 5])
            part2 = Fraction(part2_num, part2_den)
            
            part3_num = random.randint(-50, 50)
            part3_den = random.choice([2, 3, 4, 5])
            part3 = Fraction(abs(part3_num), part3_den)
            
            # Calculate answer
            ans = (part1 / part2) + part3
            
            # Format question
            q_part1 = to_latex(part1)
            q_part2 = to_latex(part2)
            q_part3 = to_latex(part3, mixed=True)
            
            math_str = f"\\left[{q_part1}\\right] \\div {q_part2} + \\left|{q_part3}\\right|"
            
            # Format answer
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            # Check constraints
            if (abs(ans.numerator) > 120 or ans.denominator > 30 or 
                any(abs(x.numerator) > 50 for x in [part1, part2, part3])):
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