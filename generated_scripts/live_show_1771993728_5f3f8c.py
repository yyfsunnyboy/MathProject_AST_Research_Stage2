import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f():
        n = random.randint(-12, 12)
        while n == 0:
            n = random.randint(-12, 12)
        d = random.randint(2, 10)
        return Fraction(n, d)

    def fmt(f):
        s = str(abs(f.numerator)) if f.denominator == 1 else f"{abs(f.numerator)}/{f.denominator}"
        return f"( - {s} )" if f < 0 else s

    ops = [('+', '+'), ('-', '-'), ('*', '×'), ('/', '÷')]
    
    if level == 1:
        f1, f2 = get_f(), get_f()
        o_s, o_c = random.choice(ops)
        if o_s == '+': res = f1 + f2
        elif o_s == '-': res = f1 - f2
        elif o_s == '*': res = f1 * f2
        else: res = f1 / f2
        txt = f"{fmt(f1)} {o_c} {fmt(f2)}"
    else:
        f1, f2, f3 = get_f(), get_f(), get_f()
        (o1_s, o1_c), (o2_s, o2_c) = random.choice(ops), random.choice(ops)
        if o2_s in ['*', '/'] and o1_s in ['+', '-']:
            if o2_s == '*': i = f2 * f3
            else: i = f2 / f3
            res = f1 + i if o1_s == '+' else f1 - i
            txt = f"{fmt(f1)} {o1_c} {fmt(f2)} {o2_c} {fmt(f3)}"
        else:
            if o1_s == '+': i = f1 + f2
            elif o1_s == '-': i = f1 - f2
            elif o1_s == '*': i = f1 * f2
            else: i = f1 / f2
            if o2_s == '+': res = i + f3
            elif o2_s == '-': res = i - f3
            elif o2_s == '*': res = i * f3
            else: res = i / f3
            txt = f"( {fmt(f1)} {o1_c} {fmt(f2)} ) {o2_c} {fmt(f3)}"

    ans_str = str(res.numerator) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
    
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).replace(" ", "")
    c = str(correct_answer).replace(" ", "")
    is_correct = (u == c)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }