import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, p=False):
        s = str(f)
        return "(" + s + ")" if p and f < 0 else s
    
    def get_f():
        return Fraction(random.randint(-12, 12), random.choice([1, 1, 1, 2, 3, 4, 5, 6, 8, 10]))

    a, b, c, d, e, f, g = [get_f() for _ in range(7)]
    while d == 0: d = get_f()
    
    res = ((a + b) * c) / d + abs(e * f + g)
    
    if b >= 0:
        ab = f_str(a) + "+" + f_str(b)
    else:
        ab = f_str(a) + f_str(b)
        
    if g >= 0:
        efg = f_str(e) + "×" + f_str(f, True) + "+" + f_str(g)
    else:
        efg = f_str(e) + "×" + f_str(f, True) + f_str(g)
        
    q = "計算 [(" + ab + ")×" + f_str(c, True) + "]÷" + f_str(d, True) + " + |" + efg + "| 的值。"
    
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(res),
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