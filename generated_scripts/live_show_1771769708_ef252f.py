import random

def _poly_to_latex(coeffs):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        sign = "+" if c > 0 and res else ""
        if c < 0:
            sign = "-"
        val = abs(c)
        if i == 0:
            term = str(val)
        elif i == 1:
            term = "x" if val == 1 else f"{val}x"
        else:
            term = f"x^{i}" if val == 1 else f"{val}x^{i}"
        res += sign + term
    return res if res else "0"

def generate(level=1, **kwargs):
    t = random.randint(1, 3)
    if t == 1:
        p1 = [random.randint(-10, 10) for _ in range(3)]
        p2 = [random.randint(-10, 10) for _ in range(3)]
        op = random.choice(["+", "-"])
        if op == "+":
            res = [p1[i] + p2[i] for i in range(3)]
        else:
            res = [p1[i] - p2[i] for i in range(3)]
        q = f"計算 $({_poly_to_latex(p1)}) {op} ({_poly_to_latex(p2)})$"
    elif t == 2:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(2)]
        res = [0] * 3
        for i in range(2):
            for j in range(2):
                res[i+j] += p1[i] * p2[j]
        q = f"計算 $({_poly_to_latex(p1)})({_poly_to_latex(p2)})$"
    else:
        p1 = [random.randint(-5, 5) for _ in range(3)]
        p2 = [random.randint(-5, 5) for _ in range(3)]
        p3 = [random.randint(-5, 5) for _ in range(3)]
        res = [p1[i] - (p2[i] - p3[i]) for i in range(3)]
        q = f"計算 $({_poly_to_latex(p1)}) - [({_poly_to_latex(p2)}) - ({_poly_to_latex(p3)})]$"
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': _poly_to_latex(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}