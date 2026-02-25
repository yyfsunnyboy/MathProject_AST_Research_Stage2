import random
import math

def generate(level=1, **kwargs):
    def simplify(n, d):
        if d == 0: d = 1
        common = math.gcd(n, d)
        n //= common
        d //= common
        if d < 0: n, d = -n, -d
        return n, d

    def to_str(n, d):
        n, d = simplify(n, d)
        return str(n) if d == 1 else f"{n}/{d}"

    def to_str_p(n, d):
        n, d = simplify(n, d)
        s = str(n) if d == 1 else f"{n}/{d}"
        return f"({s})" if n < 0 else s

    def add(n1, d1, n2, d2): return simplify(n1*d2 + n2*d1, d1*d2)
    def sub(n1, d1, n2, d2): return simplify(n1*d2 - n2*d1, d1*d2)
    def mul(n1, d1, n2, d2): return simplify(n1*n2, d1*d2)
    def div(n1, d1, n2, d2): return simplify(n1*d2, d1*n2)

    n1, d1 = random.randint(-10, 10), random.randint(2, 10)
    n2, d2 = random.randint(-10, 10), random.randint(2, 10)
    
    ops = [('+', add), ('-', sub), ('×', mul), ('÷', div)]
    o1_s, o1_a = random.choice(ops)
    
    if o1_s == '÷' and n2 == 0:
        n2 = random.randint(1, 10)
        
    if level == 1:
        q = f"{to_str_p(n1, d1)} {o1_s} {to_str_p(n2, d2)}"
        rn, rd = o1_a(n1, d1, n2, d2)
    else:
        n3, d3 = random.randint(-10, 10), random.randint(2, 10)
        o2_s, o2_a = random.choice(ops)
        if o2_s == '÷' and n3 == 0:
            n3 = random.randint(1, 10)
        
        q = f"({to_str_p(n1, d1)} {o1_s} {to_str_p(n2, d2)}) {o2_s} {to_str_p(n3, d3)}"
        in_n, in_d = o1_a(n1, d1, n2, d2)
        rn, rd = o2_a(in_n, in_d, n3, d3)

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': to_str(rn, rd),
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).strip().replace(' ', '')
    c = str(correct_answer).strip().replace(' ', '')
    res = (u == c)
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }