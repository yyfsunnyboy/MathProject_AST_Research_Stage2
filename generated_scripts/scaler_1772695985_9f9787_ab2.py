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
            a_num, a_den = random.randint(-50, 50), random.randint(2, 10)
            b_num, b_den = random.randint(-50, 50), random.randint(2, 10)
            
            if a_den == 0 or b_den == 0:
                continue
            
            part1 = Fraction(a_num, a_den)
            part2 = Fraction(b_num, b_den)
            
            if random.choice([True, False]):
                part1 = -part1
                part2 = -part2
                
            math_str = f"\\left({fmt_num(part1.numerator)} \\div {fmt_num(part2.numerator)}\\right) + {fmt_num(int(part1))}"
            ans = (part1 / part2) + int(part1)
            
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