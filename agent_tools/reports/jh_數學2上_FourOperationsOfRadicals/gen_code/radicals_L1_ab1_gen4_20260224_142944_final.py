# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 95.78s | Tokens: In=586, Out=1149
# Created At: 2026-02-24 14:29:44
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def simplify_sqrt(n):
    a, b = 1, n
    d = 2
    while d * d <= b:
        while b % (d * d) == 0:
            a *= d
            b //= (d * d)
        d += 1
    return a, b

def format_term(coeff, rad, first=False):
    if coeff == 0:
        return ""
    res = ""
    if coeff > 0:
        if not first:
            res += "+"
    else:
        res += "-"
    abs_c = abs(coeff)
    if rad == 1:
        res += str(abs_c)
    else:
        if abs_c == 1:
            res += "\\sqrt{" + str(rad) + "}"
        else:
            res += str(abs_c) + "\\sqrt{" + str(rad) + "}"
    return res

def expr_to_latex(terms):
    items = {r: c for r, c in terms.items() if c != 0}
    if not items:
        return "0"
    sorted_rads = sorted(items.keys())
    res = ""
    first = True
    for r in sorted_rads:
        s = format_term(items[r], r, first)
        if s:
            res += s
            first = False
    return res

def generate(level=1, **kwargs):
    def mul(e1, e2):
        res = {}
        for r1, c1 in e1.items():
            for r2, c2 in e2.items():
                c, r = c1 * c2, r1 * r2
                a, b = simplify_sqrt(r)
                res[b] = res.get(b, 0) + c * a
        return res

    def add(e1, e2):
        res = e1.copy()
        for r, c in e2.items():
            res[r] = res.get(r, 0) + c
        return res

    t = random.randint(1, 4)
    if t == 1:
        r = random.choice([2, 3, 5, 6, 7])
        c1, c2, c3 = random.randint(1, 4), random.randint(1, 4), random.randint(1, 4)
        q = f"Simplify $\\sqrt{{{c1*c1*r}}} + \\sqrt{{{c2*c2*r}}} - \\sqrt{{{c3*c3*r}}}$"
        ans_dict = {r: c1 + c2 - c3}
    elif t == 2:
        r1 = random.choice([2, 3, 5])
        r2, r3 = random.sample([2, 3, 5, 6, 7], 2)
        q = f"Simplify $\\sqrt{{{r1}}}(\\sqrt{{{r2}}} + \\sqrt{{{r3}}})$"
        ans_dict = mul({r1: 1}, {r2: 1, r3: 1})
    elif t == 3:
        r1, r2 = random.sample([2, 3, 5, 6], 2)
        q = f"Simplify $(\\sqrt{{{r1}}} + \\sqrt{{{r2}}})(\\sqrt{{{r1}}} - \\sqrt{{{r2}}})$"
        ans_dict = mul({r1: 1, r2: 1}, {r1: 1, r2: -1})
    else:
        r1 = random.choice([2, 3, 5])
        c1, c2 = random.randint(2, 3), random.randint(4, 5)
        v1, v2 = c1*c1*r1, c2*c2*r1
        r2 = random.choice([2, 3])
        q = f"Simplify $(\\sqrt{{{v1}}} - \\sqrt{{{v2}}}) + (\\sqrt{{{r2}}} + 1)(\\sqrt{{{r2}}} - 1)$"
        p1 = {r1: c1 - c2}
        p2 = mul({r2: 1, 1: 1}, {r2: 1, 1: -1})
        ans_dict = add(p1, p2)

    return {
        'question_text': q,
        'answer': '',
        'correct_answer': expr_to_latex(ans_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}