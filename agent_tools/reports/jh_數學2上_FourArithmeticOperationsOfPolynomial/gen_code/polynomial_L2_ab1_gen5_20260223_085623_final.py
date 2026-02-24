# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 66.41s | Tokens: In=556, Out=759
# Created At: 2026-02-23 08:56:23
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def format_poly(coeffs):
    res = ""
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = n - i
        if c == 0:
            continue
        sign = ""
        if c > 0:
            if res:
                sign = "+"
        else:
            sign = "-"
        val = abs(c)
        if val == 1 and p > 0:
            c_str = ""
        else:
            c_str = str(val)
        if p == 0:
            v_str = ""
        elif p == 1:
            v_str = "x"
        else:
            v_str = f"x^{{{p}}}"
        res += sign + c_str + v_str
    return res if res else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(["+", "-"])
        p1 = [random.randint(-9, 9) for _ in range(3)]
        p2 = [random.randint(-9, 9) for _ in range(3)]
        while p1[0] == 0: p1[0] = random.randint(-9, 9)
        while p2[0] == 0: p2[0] = random.randint(-9, 9)
        s1, s2 = format_poly(p1), format_poly(p2)
        if op == "+":
            res_coeffs = [p1[i] + p2[i] for i in range(3)]
            txt = f"Calculate $({s1}) + ({s2})$"
        else:
            res_coeffs = [p1[i] - p2[i] for i in range(3)]
            txt = f"Calculate $({s1}) - ({s2})$"
        ans = format_poly(res_coeffs)
    else:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(3)]
        while p1[0] == 0: p1[0] = random.randint(-5, 5)
        while p2[0] == 0: p2[0] = random.randint(-5, 5)
        s1, s2 = format_poly(p1), format_poly(p2)
        res_coeffs = [0] * 4
        for i in range(2):
            for j in range(3):
                res_coeffs[i+j] += p1[i] * p2[j]
        txt = f"Expand and simplify $({s1})({s2})$"
        ans = format_poly(res_coeffs)
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}