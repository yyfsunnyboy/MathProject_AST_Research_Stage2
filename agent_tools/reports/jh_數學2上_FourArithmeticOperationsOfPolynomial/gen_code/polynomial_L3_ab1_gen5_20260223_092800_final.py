# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 37.82s | Tokens: In=556, Out=815
# Created At: 2026-02-23 09:28:00
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def format_poly(coeffs, is_latex=True):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        if c > 0 and res != "":
            res += "+"
        if i == 0:
            res += str(c)
        else:
            if c == 1:
                pass
            elif c == -1:
                res += "-"
            else:
                res += str(c)
            if i == 1:
                res += "x"
            else:
                if is_latex:
                    res += "x^{" + str(i) + "}"
                else:
                    res += "x^" + str(i)
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        p1 = [random.randint(-5, 5) for _ in range(3)]
        p2 = [random.randint(-5, 5) for _ in range(3)]
        while all(c == 0 for c in p1): p1 = [random.randint(-5, 5) for _ in range(3)]
        while all(c == 0 for c in p2): p2 = [random.randint(-5, 5) for _ in range(3)]
        op = random.choice(['+', '-'])
        s1, s2 = format_poly(p1, True), format_poly(p2, True)
        q = f"計算 $({s1}) {op} ({s2})$"
        if op == '+':
            ans_coeffs = [p1[i] + p2[i] for i in range(3)]
        else:
            ans_coeffs = [p1[i] - p2[i] for i in range(3)]
        ans_str = format_poly(ans_coeffs, False)
    else:
        p1 = [random.randint(-3, 3) for _ in range(2)]
        p2 = [random.randint(-3, 3) for _ in range(2)]
        while all(c == 0 for c in p1): p1 = [random.randint(-3, 3) for _ in range(2)]
        while all(c == 0 for c in p2): p2 = [random.randint(-3, 3) for _ in range(2)]
        s1, s2 = format_poly(p1, True), format_poly(p2, True)
        q = f"展開並化簡 $({s1})({s2})$"
        ans_coeffs = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                ans_coeffs[i+j] += p1[i] * p2[j]
        ans_str = format_poly(ans_coeffs, False)
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}