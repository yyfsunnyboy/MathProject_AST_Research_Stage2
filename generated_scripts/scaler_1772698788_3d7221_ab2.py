def generate():
    import random
    from fractions import Fraction
    
    def create_fraction():
        numerator = random.randint(-50, 50)
        denominator = random.randint(2, 10)
        while denominator < 0:
            denominator *= -1
        return Fraction(numerator, denominator)
    
    def format_fraction(frac):
        if frac.denominator == 1:
            return str(frac.numerator)
        else:
            return f"{frac.numerator}/{frac.denominator}"
    
    def format_negative(num):
        return f"({num})" if num < 0 else str(num)
    
    while True:
        try:
            a = create_fraction()
            b = create_fraction()
            c = create_fraction()
            
            part1 = a + b
            part2 = c
            part3 = abs(a - b)
            
            ans = (part1 / part2) + part3
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            
            question = (
                r"計算 $\frac{" + format_negative(part1.numerator) + "}" +
                r"{" + str(part1.denominator) + "}$ ÷ $\frac{" + 
                format_negative(part2.numerator) + "}" + 
                r"{" + str(part2.denominator) + "}$ + $" + 
                r"|\frac{" + format_negative(a.numerator) + "}" +
                r"{" + str(a.denominator) + "} - \frac{" + 
                format_negative(b.numerator) + "}" + 
                r"{" + str(b.denominator) + "}|$ 的值。"
            )
            
            return {
                'question_text': question,
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except:
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