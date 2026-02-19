import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f():
        d = random.choice([2, 3, 4, 5, 6, 8, 10, 12])
        n = random.randint(-12, 12)
        return Fraction(n, d)

    def fmt(f, bracket=False):
        s = str(f)
        if bracket and f < 0:
            return f"({s})"
        return s

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = get_f()
    while c == 0: c = get_f()
    d = get_f()
    while d == 0: d = get_f()
    e = random.randint(-10, 10)
    f_val = get_f()
    while f_val == 0: f_val = get_f()
    g = random.randint(-10, 10)

    res = ((a + b) * c) / d + abs(e * f_val + g)

    op_b = "+" if b >= 0 else ""
    op_g = "+" if g >= 0 else ""

    q = f"計算 [({a}{op_b}{b})×{fmt(c, True)}]÷{fmt(d, True)} + |{e}×{fmt(f_val, True)}{op_g}{g}| 的值。"

    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).replace(" ", "")
        ca = str(correct_answer).replace(" ", "")
        is_correct = Fraction(ua) == Fraction(ca)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }