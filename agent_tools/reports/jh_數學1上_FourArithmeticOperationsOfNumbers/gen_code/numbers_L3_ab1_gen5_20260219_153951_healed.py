import random
from fractions import Fraction

def f_str(f, b=False):
    s = str(f)
    return f"({s})" if f < 0 and b else s

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0: b = random.randint(-10, 10)
    c_num = random.randint(1, 9)
    c_den = random.randint(2, 9)
    c = Fraction(c_num, c_den)
    d_num = random.choice([i for i in range(-9, 10) if i != 0])
    d_den = random.randint(2, 9)
    d = Fraction(d_num, d_den)
    e = random.randint(-10, 10)
    while e == 0: e = random.randint(-10, 10)
    f_num = random.choice([i for i in range(-9, 10) if i != 0])
    f_den = random.randint(2, 9)
    f = Fraction(f_num, f_den)
    g = random.randint(-10, 10)
    p1 = (Fraction(a + b) * c) / d
    p2 = abs(Fraction(e) * f + Fraction(g))
    res = p1 + p2
    t1 = f"[({a}{b:+})×{f_str(c, True)}]÷{f_str(d, True)}"
    t2 = f"|{e}×{f_str(f, True)}{g:+}|"
    return {
        'question_text': f"計算 `{t1} + {t2}` 的值。",
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).replace(" ", "")
    c = str(correct_answer).replace(" ", "")
    ok = (u == c)
    return {'correct': ok, 'result': '正確' if ok else '錯誤'}