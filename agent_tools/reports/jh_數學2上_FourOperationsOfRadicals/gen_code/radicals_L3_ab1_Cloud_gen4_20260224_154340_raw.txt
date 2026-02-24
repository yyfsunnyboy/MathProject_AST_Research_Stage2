import random
import math

def generate(level=1, **kwargs):
    def get_rad(n):
        c, i = 1, n
        d = 2
        while d * d <= i:
            if i % (d * d) == 0:
                c *= d
                i //= (d * d)
            else:
                d += 1
        return c, i

    def fmt_term(c, i):
        if i == 1:
            return str(c)
        s = "\\sqrt{" + str(i) + "}"
        if c == 1:
            return s
        if c == -1:
            return "-" + s
        return str(c) + s

    base = random.choice([2, 3, 5])
    m1 = random.randint(2, 4)
    m2 = random.randint(2, 4)
    while m2 == m1:
        m2 = random.randint(2, 4)
    k1 = random.randint(1, 3)
    k2 = random.randint(1, 3)
    if random.random() > 0.5:
        k2 = -k2
    
    v1 = base * m1 * m1
    v2 = base * m2 * m2
    
    x = random.choice([2, 3, 5])
    a = random.randint(1, 4)
    b = random.randint(1, 4)
    if random.random() > 0.5:
        a = -a
    if random.random() > 0.5:
        b = -b
    
    t1_str = fmt_term(k1, v1)
    t2_str = fmt_term(abs(k2), v2)
    op1 = "+" if k2 > 0 else "-"
    
    a_str = f"+ {a}" if a > 0 else f"- {abs(a)}"
    b_str = f"+ {b}" if b > 0 else f"- {abs(b)}"
    
    q = f"({t1_str} {op1} {t2_str}) + (\\sqrt{{{x}}} {a_str})(\\sqrt{{{x}}} {b_str})"
    
    res = {}
    c1, r1 = get_rad(v1)
    res[r1] = res.get(r1, 0) + k1 * c1
    c2, r2 = get_rad(v2)
    res[r2] = res.get(r2, 0) + k2 * c2
    
    res[1] = res.get(1, 0) + x + (a * b)
    res[x] = res.get(x, 0) + (a + b)
    
    ans_parts = []
    if 1 in res and res[1] != 0:
        ans_parts.append(str(res[1]))
    
    for r in sorted(res.keys()):
        if r == 1 or res[r] == 0:
            continue
        term = fmt_term(res[r], r)
        if res[r] > 0 and ans_parts:
            ans_parts.append("+" + term)
        else:
            ans_parts.append(term)
            
    ans_str = "".join(ans_parts)
    if not ans_str:
        ans_str = "0"
        
    return {
        'question_text': f'Simplify ${q}$',
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}