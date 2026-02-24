import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, p=False):
        s = f"{f.numerator}/{f.denominator}" if f.denominator != 1 else str(f.numerator)
        return f"({s})" if p and f < 0 else s

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    
    c_n = random.randint(1, 9)
    c_d = random.randint(2, 9)
    c = Fraction(c_n, c_d)
    
    d_n = random.choice([i for i in range(-9, 10) if i != 0])
    d_d = random.randint(2, 9)
    d = Fraction(d_n, d_d)
    
    e = random.randint(-10, 10)
    while e == 0:
        e = random.randint(-10, 10)
        
    f_n = random.choice([i for i in range(-9, 10) if i != 0])
    f_d = random.randint(2, 9)
    f = Fraction(f_n, f_d)
    
    g = random.randint(-10, 10)
    
    v1 = (Fraction(a) + Fraction(b)) * c
    v2 = v1 / d
    v3 = abs(Fraction(e) * f + Fraction(g))
    res = v2 + v3
    
    op1 = "+" if b >= 0 else "-"
    op2 = "+" if g >= 0 else "-"
    
    expr = f"[({a}{op1}{abs(b)})×{f_str(c)}]÷{f_str(d, True)} + |{e}×{f_str(f, True)}{op2}{abs(g)}|"
    ans_str = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        def parse(s):
            s = s.strip().replace(' ', '')
            if '/' in s:
                parts = s.split('/')
                return Fraction(int(parts[0]), int(parts[1]))
            return Fraction(s)
        
        u = parse(user_answer)
        c = parse(correct_answer)
        is_correct = (u == c)
        return {
            'correct': is_correct,
            'result': '正確' if is_correct else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }