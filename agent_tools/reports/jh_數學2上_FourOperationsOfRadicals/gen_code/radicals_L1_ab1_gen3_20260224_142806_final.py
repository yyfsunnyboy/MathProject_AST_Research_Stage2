# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 295.36s | Tokens: In=586, Out=1470
# Created At: 2026-02-24 14:28:06
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def _get_factors(n):
    a, b = 1, n
    d = 2
    while d * d <= b:
        if b % (d * d) == 0:
            a *= d
            b //= (d * d)
        else:
            d += 1
    return a, b

def _to_map(coeff, radicand):
    a, b = _get_factors(radicand)
    return {b: coeff * a}

def _add(m1, m2):
    res = m1.copy()
    for r, c in m2.items():
        res[r] = res.get(r, 0) + c
    return {r: v for r, v in res.items() if v != 0}

def _mul(m1, m2):
    res = {}
    for r1, c1 in m1.items():
        for r2, c2 in m2.items():
            a, b = _get_factors(r1 * r2)
            res[b] = res.get(b, 0) + c1 * c2 * a
    return {r: v for r, v in res.items() if v != 0}

def _format(m):
    if not m: return "0"
    items = sorted(m.items(), key=lambda x: (x[0] != 1, x[0]))
    res = ""
    for r, c in items:
        term = ""
        if c > 0 and res: term += " + "
        if c < 0 and res: term += " - "
        elif c < 0 and not res: term += "-"
        abs_c = abs(c)
        if r == 1: term += str(abs_c)
        else:
            if abs_c != 1: term += str(abs_c)
            term += "\\sqrt{" + str(r) + "}"
        res += term
    return res

def _q_term(c, r, first=False):
    s = ""
    if c > 0 and not first: s += " + "
    if c < 0:
        if first: s += "-"
        else: s += " - "
    abs_c = abs(c)
    if r == 1: s += str(abs_c)
    else:
        if abs_c != 1: s += str(abs_c)
        s += f"\\sqrt{{{r}}}"
    return s

def generate(level=1, **kwargs):
    rads = [2, 3, 5, 6, 7, 10]
    def rand_t():
        return random.randint(1, 3), random.choice(rads) * (random.randint(1, 3)**2)
    if level == 1:
        c1, r1 = rand_t()
        c2, r2 = rand_t()
        c3, r3 = rand_t()
        c3 = -c3
        q = f"{_q_term(c1, r1, True)}{_q_term(c2, r2)}{_q_term(c3, r3)}"
        ans = _add(_add(_to_map(c1, r1), _to_map(c2, r2)), _to_map(c3, r3))
    elif level == 2:
        c1, r1 = rand_t()
        c2, r2 = rand_t()
        c3, r3 = rand_t()
        c4, r4 = rand_t()
        c4 = -c4
        q = f"({_q_term(c1, r1, True)}{_q_term(c2, r2)})({_q_term(c3, r3, True)}{_q_term(c4, r4)})"
        m1 = _add(_to_map(c1, r1), _to_map(c2, r2))
        m2 = _add(_to_map(c3, r3), _to_map(c4, r4))
        ans = _mul(m1, m2)
    else:
        c1, r1 = rand_t()
        c2, r2 = rand_t()
        c3, r3 = -random.randint(1, 2), random.choice(rads) * (random.randint(1, 2)**2)
        m1 = _add(_add(_to_map(c1, r1), _to_map(c2, r2)), _to_map(c3, r3))
        q1 = f"({_q_term(c1, r1, True)}{_q_term(c2, r2)}{_q_term(c3, r3)})"
        c4, r4 = 1, random.choice(rads)
        c5, r5 = 1, random.choice(rads)
        m2 = _add(_to_map(c4, r4), _to_map(c5, r5))
        q2 = f"({_q_term(c4, r4, True)}{_q_term(c5, r5)})"
        c6, r6 = 1, random.choice(rads)
        c7, r7 = -1, 1
        m3 = _add(_to_map(c6, r6), _to_map(c7, r7))
        q3 = f"({_q_term(c6, r6, True)}{_q_term(c7, r7)})"
        q = f"{q1} + {q2}{q3}"
        ans = _add(m1, _mul(m2, m3))
    return {'question_text': f"${q}$", 'answer': '', 'correct_answer': _format(ans), 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}