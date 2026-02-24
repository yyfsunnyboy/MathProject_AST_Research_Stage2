# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 299.04s | Tokens: In=586, Out=1286
# Created At: 2026-02-24 15:12:56
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def _simplify(c, b):
    d = 2
    while d * d <= b:
        while b % (d * d) == 0:
            c *= d
            b //= (d * d)
        d += 1
    return c, b

def _to_latex(d):
    sorted_bases = sorted([b for b in d if d[b] != 0])
    if not sorted_bases:
        return "0"
    res = ""
    for b in sorted_bases:
        c = d[b]
        if c > 0 and res:
            res += "+"
        if b == 1:
            res += str(c)
        else:
            if c == -1:
                res += "-"
            elif c != 1:
                res += str(c)
            res += "\\sqrt{" + str(b) + "}"
    return res

def _fmt_q(c, b, first=False):
    res = ""
    if c > 0:
        if not first:
            res += " + "
    else:
        if first:
            res += "-"
        else:
            res += " - "
    abs_c = abs(c)
    if abs_c != 1:
        res += str(abs_c)
    res += "\\sqrt{" + str(b) + "}"
    return res

def _get_val(c, b):
    nc, nb = _simplify(c, b)
    return {nb: nc}

def _add(d1, d2):
    res = d1.copy()
    for b, c in d2.items():
        res[b] = res.get(b, 0) + c
    return res

def _mul(d1, d2):
    res = {}
    for b1, c1 in d1.items():
        for b2, c2 in d2.items():
            nc, nb = _simplify(c1 * c2, b1 * b2)
            res[nb] = res.get(nb, 0) + nc
    return res

def generate(level=1, **kwargs):
    rads = [2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 40, 45, 48, 50, 54, 63, 72, 75, 80, 98]
    s = random.sample(rads, 10)
    c = [random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]) for _ in range(10)]
    
    if level == 1:
        expr = f"{_fmt_q(c[0], s[0], True)}{_fmt_q(c[1], s[1])}{_fmt_q(c[2], s[2])}"
        ans_dict = _add(_add(_get_val(c[0], s[0]), _get_val(c[1], s[1])), _get_val(c[2], s[2]))
    elif level == 2:
        expr = f"({_fmt_q(c[0], s[0], True)}{_fmt_q(c[1], s[1])})({_fmt_q(c[2], s[2], True)}{_fmt_q(c[3], s[3])})"
        ans_dict = _mul(_add(_get_val(c[0], s[0]), _get_val(c[1], s[1])), _add(_get_val(c[2], s[2]), _get_val(c[3], s[3])))
    else:
        part1 = f"({_fmt_q(c[0], s[0], True)}{_fmt_q(c[1], s[1])}{_fmt_q(c[2], s[2])})"
        part2 = f"({_fmt_q(c[3], s[3], True)}{_fmt_q(c[4], s[4])})({_fmt_q(c[5], s[5], True)}{_fmt_q(c[6], s[6])})"
        expr = f"{part1} + {part2}"
        d1 = _add(_add(_get_val(c[0], s[0]), _get_val(c[1], s[1])), _get_val(c[2], s[2]))
        d2 = _mul(_add(_get_val(c[3], s[3]), _get_val(c[4], s[4])), _add(_get_val(c[5], s[5]), _get_val(c[6], s[6])))
        ans_dict = _add(d1, d2)

    return {
        'question_text': f"Simplify the following expression: ${expr}$",
        'answer': '',
        'correct_answer': _to_latex(ans_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}