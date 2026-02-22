import random

def _format_poly(coeffs):
    res = ""
    n = len(coeffs) - 1
    for i in range(n, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        term = ""
        if c > 0 and res != "":
            term += "+"
        if c == -1 and i > 0:
            term += "-"
        elif c != 1 or i == 0:
            term += str(c)
        if i > 1:
            term += "x^" + str(i)
        elif i == 1:
            term += "x"
        res += term
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(["+", "-"])
        d1, d2 = random.randint(1, 2), random.randint(1, 2)
    else:
        op = random.choice(["+", "-", "*"])
        if op == "*":
            d1, d2 = 1, random.randint(1, min(level, 2))
        else:
            d1, d2 = random.randint(1, 2), random.randint(1, 2)
    
    p1 = [random.randint(-10, 10) for _ in range(d1 + 1)]
    p2 = [random.randint(-10, 10) for _ in range(d2 + 1)]
    while all(c == 0 for c in p1): p1 = [random.randint(-10, 10) for _ in range(d1 + 1)]
    while all(c == 0 for c in p2): p2 = [random.randint(-10, 10) for _ in range(d2 + 1)]
    
    s1, s2 = _format_poly(p1), _format_poly(p2)
    
    if op in ["+", "-"]:
        q = f"(${s1}$){op}(${s2}$)"
        max_d = max(len(p1), len(p2))
        p1_ext = p1 + [0] * (max_d - len(p1))
        p2_ext = p2 + [0] * (max_d - len(p2))
        if op == "+":
            res_p = [p1_ext[i] + p2_ext[i] for i in range(max_d)]
        else:
            res_p = [p1_ext[i] - p2_ext[i] for i in range(max_d)]
    else:
        q = f"(${s1}$)\\cdot(${s2}$)"
        res_p = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                res_p[i+j] += p1[i] * p2[j]
    
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': _format_poly(res_p),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}