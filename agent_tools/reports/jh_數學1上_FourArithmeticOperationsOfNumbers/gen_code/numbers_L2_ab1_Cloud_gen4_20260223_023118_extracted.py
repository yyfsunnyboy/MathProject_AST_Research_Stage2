import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_s(f, p=False):
        if f.denominator == 1:
            s = str(f.numerator)
        else:
            s = f"{f.numerator}/{f.denominator}"
        return f"({s})" if (p and f < 0) else s

    t = random.randint(1, 3)
    if t == 1:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = Fraction(random.randint(1, 9), random.randint(2, 9))
        d_n = random.choice([i for i in range(-9, 10) if i != 0])
        d = Fraction(d_n, random.randint(2, 9))
        e = random.randint(-10, 10)
        f_v = Fraction(random.randint(-9, 9), random.randint(2, 9))
        g = random.randint(-10, 10)
        b_p = f"+{b}" if b >= 0 else f"{b}"
        g_p = f"+{g}" if g >= 0 else f"{g}"
        q = f"計算 [({a}{b_p})×{f_s(c, True)}]÷{f_s(d, True)} + |{e}×{f_s(f_v, True)}{g_p}| 的值。"
        val = ((a + b) * c) / d + abs(e * f_v + g)
    elif t == 2:
        a = Fraction(random.randint(-9, 9), random.randint(2, 9))
        b = Fraction(random.randint(-9, 9), random.randint(2, 9))
        c = Fraction(random.randint(-9, 9), random.randint(2, 9))
        d = Fraction(random.randint(-9, 9), random.randint(2, 9))
        if (c + d) == 0: d = Fraction(1, 2)
        q = f"計算 ({f_s(a)} - {f_s(b, True)}) ÷ ({f_s(c)} + {f_s(d, True)}) 的值。"
        val = (a - b) / (c + d)
    else:
        a = Fraction(random.randint(-9, 9), random.randint(2, 9))
        b = random.randint(-5, 5)
        c = Fraction(random.randint(-9, 9), random.randint(2, 9))
        d = random.randint(-5, 5)
        q = f"計算 {f_s(a)} × {b} - {f_s(c, True)} × {d} 的值。"
        val = a * b - c * d

    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        def parse(s):
            s = s.strip().replace(' ', '')
            if '/' in s:
                n, d = s.split('/')
                return Fraction(int(n), int(d))
            return Fraction(s)
        ua = parse(user_answer)
        ca = parse(correct_answer)
        res = (ua == ca)
    except:
        res = False
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }