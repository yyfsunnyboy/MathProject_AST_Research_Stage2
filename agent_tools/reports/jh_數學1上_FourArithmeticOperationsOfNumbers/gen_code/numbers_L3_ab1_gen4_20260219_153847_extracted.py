import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, p=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        if f < 0 and p:
            return f"({s})"
        return s

    def get_f(allow_zero=True):
        while True:
            n = random.randint(-10, 10)
            d = random.choice([1, 2, 3, 4, 5, 8])
            res = Fraction(n, d)
            if not allow_zero and res == 0:
                continue
            return res

    a = get_f()
    b = get_f()
    c = get_f(False)
    d = get_f(False)
    e = get_f()
    f = get_f(False)
    g = get_f()

    res_val = ((a + b) * c) / d + abs(e * f + g)
    
    sa = f_str(a)
    sb = f_str(b, True)
    sc = f_str(c, True)
    sd = f_str(d, True)
    se = f_str(e)
    sf = f_str(f, True)
    sg = f_str(g, True)
    
    q_text = f"計算 [({sa}+{sb})×{sc}]÷{sd} + |{se}×{sf}+{sg}| 的值。"
    ans_str = str(res_val.numerator) if res_val.denominator == 1 else f"{res_val.numerator}/{res_val.denominator}"
    
    return {
        'question_text': q_text,
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