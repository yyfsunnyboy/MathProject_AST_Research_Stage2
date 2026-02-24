# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 294.26s | Tokens: In=556, Out=872
# Created At: 2026-02-23 08:45:04
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def to_latex(coeffs):
    res = ""
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = n - i
        if c == 0: continue
        s = "+" if c > 0 and res != "" else ""
        if c == -1 and p > 0: val = "-"
        elif c == 1 and p > 0: val = ""
        else: val = str(c)
        x = "" if p == 0 else ("x" if p == 1 else f"x^{{{p}}}")
        res += s + val + x
    return res if res != "" else "0"

def to_plain(coeffs):
    res = ""
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = n - i
        if c == 0: continue
        s = "+" if c > 0 and res != "" else ""
        if c == -1 and p > 0: val = "-"
        elif c == 1 and p > 0: val = ""
        else: val = str(c)
        x = "" if p == 0 else ("x" if p == 1 else f"x^{p}")
        res += s + val + x
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(['+', '-'])
        p1 = [random.randint(-5, 5) for _ in range(3)]
        p2 = [random.randint(-5, 5) for _ in range(3)]
        while p1[0] == 0: p1[0] = random.randint(-5, 5)
        while p2[0] == 0: p2[0] = random.randint(-5, 5)
        t1, t2 = to_latex(p1), to_latex(p2)
        if op == '+':
            res = [p1[i] + p2[i] for i in range(3)]
            q = f"Calculate $({t1}) + ({t2})$"
        else:
            res = [p1[i] - p2[i] for i in range(3)]
            q = f"Calculate $({t1}) - ({t2})$"
    else:
        p1 = [random.randint(-3, 3) for _ in range(2)]
        p2 = [random.randint(-3, 3) for _ in range(3 if level > 2 else 2)]
        while p1[0] == 0: p1[0] = random.randint(-3, 3)
        while p2[0] == 0: p2[0] = random.randint(-3, 3)
        t1, t2 = to_latex(p1), to_latex(p2)
        res = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                res[i+j] += p1[i] * p2[j]
        q = f"Expand and simplify $({t1})({t2})$"
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': to_plain(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}