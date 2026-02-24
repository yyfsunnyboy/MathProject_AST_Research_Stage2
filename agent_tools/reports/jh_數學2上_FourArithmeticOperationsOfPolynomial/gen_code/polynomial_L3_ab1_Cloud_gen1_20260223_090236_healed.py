import random

def format_poly_latex(coeffs):
    res = ""
    degree = len(coeffs) - 1
    for i in range(degree, -1, -1):
        c = coeffs[i]
        if c == 0: continue
        term = ""
        if i == 0:
            term = str(abs(c))
        elif i == 1:
            term = "x" if abs(c) == 1 else f"{abs(c)}x"
        else:
            term = f"x^{{{i}}}" if abs(c) == 1 else f"{abs(c)}x^{{{i}}}"
        if res == "":
            res = ("-" if c < 0 else "") + term
        else:
            res += (" - " if c < 0 else " + ") + term
    return res if res != "" else "0"

def format_poly_simple(coeffs):
    res = ""
    degree = len(coeffs) - 1
    for i in range(degree, -1, -1):
        c = coeffs[i]
        if c == 0: continue
        term = ""
        if i == 0:
            term = str(abs(c))
        elif i == 1:
            term = "x" if abs(c) == 1 else f"{abs(c)}x"
        else:
            term = f"x^{i}" if abs(c) == 1 else f"{abs(c)}x^{i}"
        if res == "":
            res = ("-" if c < 0 else "") + term
        else:
            res += ("-" if c < 0 else "+") + term
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(['add', 'sub'])
        d1, d2 = 2, 2
    elif level == 2:
        op = 'mul'
        d1, d2 = 1, 1
    else:
        op = random.choice(['add', 'sub', 'mul'])
        d1, d2 = random.randint(1, 2), random.randint(1, 2)
    p1 = [random.randint(-5, 5) for _ in range(d1 + 1)]
    while p1[-1] == 0: p1[-1] = random.randint(-5, 5)
    p2 = [random.randint(-5, 5) for _ in range(d2 + 1)]
    while p2[-1] == 0: p2[-1] = random.randint(-5, 5)
    if op == 'add':
        res_len = max(len(p1), len(p2))
        res_coeffs = [0] * res_len
        for i in range(res_len):
            v1 = p1[i] if i < len(p1) else 0
            v2 = p2[i] if i < len(p2) else 0
            res_coeffs[i] = v1 + v2
        q_text = f"Calculate $({format_poly_latex(p1)}) + ({format_poly_latex(p2)})$"
    elif op == 'sub':
        res_len = max(len(p1), len(p2))
        res_coeffs = [0] * res_len
        for i in range(res_len):
            v1 = p1[i] if i < len(p1) else 0
            v2 = p2[i] if i < len(p2) else 0
            res_coeffs[i] = v1 - v2
        q_text = f"Calculate $({format_poly_latex(p1)}) - ({format_poly_latex(p2)})$"
    else:
        res_coeffs = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                res_coeffs[i+j] += p1[i] * p2[j]
        q_text = f"Expand and simplify $({format_poly_latex(p1)})({format_poly_latex(p2)})$"
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': format_poly_simple(res_coeffs),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}