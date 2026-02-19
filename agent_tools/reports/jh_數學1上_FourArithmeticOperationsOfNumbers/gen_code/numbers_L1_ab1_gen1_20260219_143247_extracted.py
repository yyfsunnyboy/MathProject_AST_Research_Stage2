import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(n, bracket=False):
        if isinstance(n, Fraction):
            txt = f"{n.numerator}/{n.denominator}" if n.denominator != 1 else str(n.numerator)
        else:
            txt = str(n)
        if bracket and txt.startswith("-"):
            return f"({txt})"
        return txt

    def get_frac():
        while True:
            num = random.randint(-9, 9)
            den = random.randint(2, 9)
            if num != 0:
                res = Fraction(num, den)
                if res.denominator != 1:
                    return res

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = get_frac()
    d = get_frac()
    e = random.randint(-10, 10)
    f = get_frac()
    g = random.randint(-10, 10)

    val1 = (Fraction(a) + Fraction(b)) * c / d
    val2 = abs(Fraction(e) * f + Fraction(g))
    result = val1 + val2
    
    ans_str = f"{result.numerator}/{result.denominator}" if result.denominator != 1 else str(result.numerator)
    
    expr1 = f"[({a}{'+' if b>=0 else ''}{b})×{fmt(c, True)}]÷{fmt(d, True)}"
    expr2 = f"|{e}×{fmt(f, True)}{'+' if g>=0 else ''}{g}|"
    
    return {
        'question_text': f"計算 {expr1} + {expr2} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(" ", "")
    ca = str(correct_answer).strip().replace(" ", "")
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }