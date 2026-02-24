# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 79.59s | Tokens: In=556, Out=803
# Created At: 2026-02-23 07:53:20
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def format_poly(coeffs, is_latex=True):
    res = ""
    degree = len(coeffs) - 1
    for i in range(degree, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        term = ""
        if c > 0 and res != "":
            term += "+"
        if c < 0:
            term += "-"
        abs_c = abs(c)
        if abs_c != 1 or i == 0:
            term += str(abs_c)
        if i > 0:
            term += "x"
            if i > 1:
                if is_latex:
                    term += "^{" + str(i) + "}"
                else:
                    term += "^" + str(i)
        res += term
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(['+', '-'])
        d = random.randint(1, 2)
        p1 = [random.randint(-10, 10) for _ in range(d)] + [random.choice([i for i in range(-10, 11) if i != 0])]
        p2 = [random.randint(-10, 10) for _ in range(d)] + [random.choice([i for i in range(-10, 11) if i != 0])]
        if op == '+':
            res = [p1[i] + p2[i] for i in range(d + 1)]
            txt = "(" + format_poly(p1) + ") + (" + format_poly(p2) + ")"
        else:
            res = [p1[i] - p2[i] for i in range(d + 1)]
            txt = "(" + format_poly(p1) + ") - (" + format_poly(p2) + ")"
        q_text = "Calculate $" + txt + "$"
    else:
        d1 = 1
        d2 = random.randint(1, 2)
        p1 = [random.randint(-5, 5) for _ in range(d1)] + [random.choice([i for i in range(-5, 6) if i != 0])]
        p2 = [random.randint(-5, 5) for _ in range(d2)] + [random.choice([i for i in range(-5, 6) if i != 0])]
        res = [0] * (d1 + d2 + 1)
        for i in range(d1 + 1):
            for j in range(d2 + 1):
                res[i+j] += p1[i] * p2[j]
        txt = "(" + format_poly(p1) + ")(" + format_poly(p2) + ")"
        q_text = "Expand and simplify $" + txt + "$"
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': format_poly(res, False),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}