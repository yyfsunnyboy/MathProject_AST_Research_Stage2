import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f():
        n = random.randint(-9, 9)
        d = random.randint(2, 9)
        return Fraction(n, d)

    def fmt_f(f):
        s = f"{abs(f.numerator)}/{f.denominator}" if f.denominator != 1 else f"{abs(f.numerator)}"
        if f.numerator < 0:
            return f"(-{s})"
        return s

    a = random.randint(-9, 9)
    b = random.randint(-9, 9)
    f1 = get_f()
    while f1.numerator == 0:
        f1 = get_f()
    f2 = get_f()
    while f2.numerator == 0:
        f2 = get_f()
    g = random.randint(-9, 9)
    while g == 0:
        g = random.randint(-9, 9)
    f3 = get_f()
    while f3.numerator == 0:
        f3 = get_f()
    j = random.randint(-9, 9)

    val1 = (a + b) * f1
    val2 = val1 / f2
    val3 = abs(g * f3 + j)
    res = val2 + val3

    sa = str(a)
    sb = f"+{b}" if b >= 0 else str(b)
    sf1 = fmt_f(f1)
    sf2 = fmt_f(f2)
    sf3 = fmt_f(f3)
    sj = f"+{j}" if j >= 0 else str(j)

    q = f"[({sa}{sb})×{sf1}]÷{sf2} + |{g}×{sf3}{sj}|"
    
    ans_str = str(res.numerator) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        u_str = user_answer.replace(' ', '')
        c_str = correct_answer.replace(' ', '')
        u_val = Fraction(u_str)
        c_val = Fraction(c_str)
        is_correct = (u_val == c_val)
    except:
        is_correct = (user_answer.strip() == correct_answer.strip())

    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }