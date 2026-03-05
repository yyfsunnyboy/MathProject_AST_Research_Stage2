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
        if mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator) % val.denominator
            if val.numerator < 0:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
            else:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def generate():
    while True:
        a = Fraction(random.randint(-50, 50), 1)
        b = Fraction(random.randint(-10, 10), 1)
        c = Fraction(random.randint(-10, 10), 1)
        d = Fraction(random.randint(-10, 10), 1)
        e = Fraction(random.randint(-10, 10), 1)
        f = Fraction(random.randint(-10, 10), 1)
        
        try:
            part1 = FractionOps.to_latex(a) + " + " + FractionOps.to_latex(b)
            part2 = FractionOps.to_latex(c)
            part3 = FractionOps.to_latex(d) + " - " + FractionOps.to_latex(e)
            
            question = f"計算 $({part1}) \\div {part2} + ({part3})$ 的值。"
            
            ans = (a + b) / c + (d - e)
            
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 40 or ans.denominator > 12:
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