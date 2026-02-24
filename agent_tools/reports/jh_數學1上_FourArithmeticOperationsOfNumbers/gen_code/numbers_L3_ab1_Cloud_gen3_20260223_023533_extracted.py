import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fs(f):
        s = str(f)
        return f"({s})" if f < 0 else s
    def fi(n, p=True):
        return f"({n})" if n < 0 and p else str(n)
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(-10, 10)
    d = random.randint(2, 9)
    e = random.randint(-10, 10)
    f = random.randint(2, 9)
    while e == 0:
        e = random.randint(-10, 10)
    
    f_c_d = Fraction(c, d)
    f_e_f = Fraction(e, f)
    
    part1_expr = f"[({fi(a, False)} + {fi(b)}) × {fs(f_c_d)}] ÷ {fs(f_e_f)}"
    part1_val = ((Fraction(a) + b) * f_c_d) / f_e_f
    
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(2, 9)
    j = random.randint(-10, 10)
    
    f_h_i = Fraction(h, i)
    part2_expr = f"|{fi(g, False)} × {fs(f_h_i)} {'+' if j>=0 else '-'} {abs(j)}|"
    part2_val = abs(Fraction(g) * f_h_i + j)
    
    op = random.choice(['+', '-'])
    q_text = f"計算 {part1_expr} {op} {part2_expr} 的值。"
    
    if op == '+':
        correct_val = part1_val + part2_val
    else:
        correct_val = part1_val - part2_val
        
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(correct_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip().replace(" ", "")
        ca = str(correct_answer).strip().replace(" ", "")
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        u_f = Fraction(ua)
        c_f = Fraction(ca)
        if u_f == c_f:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}