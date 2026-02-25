import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f():
        n = random.randint(-15, 15)
        d = random.randint(2, 10)
        return Fraction(n, d)

    def fmt(f):
        s = f"{f.numerator}/{f.denominator}" if f.denominator != 1 else f"{f.numerator}"
        return f"({s})" if f.numerator < 0 else s

    if level == 1:
        f1, f2 = get_f(), get_f()
        op = random.choice(['+', '-'])
        res = f1 + f2 if op == '+' else f1 - f2
        q = f"計算 {fmt(f1)} {op} {fmt(f2)} 的值。"
    elif level == 2:
        f1, f2 = get_f(), get_f()
        op = random.choice(['×', '÷'])
        if op == '÷':
            while f2 == 0: f2 = get_f()
            res = f1 / f2
        else:
            res = f1 * f2
        q = f"計算 {fmt(f1)} {op} {fmt(f2)} 的值。"
    else:
        f1, f2, f3 = get_f(), get_f(), get_f()
        o1, o2 = random.choice(['+', '-', '×', '÷']), random.choice(['+', '-', '×', '÷'])
        if o1 == '+': v = f1 + f2
        elif o1 == '-': v = f1 - f2
        elif o1 == '×': v = f1 * f2
        else:
            while f2 == 0: f2 = get_f()
            v = f1 / f2
        if o2 == '+': res = v + f3
        elif o2 == '-': res = v - f3
        elif o2 == '×': res = v * f3
        else:
            while f3 == 0: f3 = get_f()
            res = v / f3
        q = f"計算 ({fmt(f1)} {o1} {fmt(f2)}) {o2} {fmt(f3)} 的值。"

    ans_str = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else f"{res.numerator}"
    
    return {
        'question_text': q,
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