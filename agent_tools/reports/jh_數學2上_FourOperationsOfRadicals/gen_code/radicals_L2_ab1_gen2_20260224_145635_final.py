# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 299.56s | Tokens: In=586, Out=1023
# Created At: 2026-02-24 14:56:35
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def get_sq_free(n):
    out, ins = 1, n
    d = 2
    while d * d <= ins:
        while ins % (d * d) == 0:
            out *= d
            ins //= (d * d)
        d += 1
    return out, ins

def format_radical(coeffs):
    parts = []
    for r in sorted(coeffs.keys()):
        c = coeffs[r]
        if c == 0: continue
        term = ""
        if c > 0 and parts:
            term += "+"
        if r == 1:
            term += str(c)
        else:
            if c == 1:
                term += f"\\sqrt{{{r}}}"
            elif c == -1:
                term += f"-\\sqrt{{{r}}}"
            else:
                term += f"{c}\\sqrt{{{r}}}"
        parts.append(term)
    return "".join(parts) if parts else "0"

def generate(level=1, **kwargs):
    rads = [2, 3, 5, 6, 7, 10, 11]
    res_dict = {}
    
    if level == 1:
        r = random.choice(rads)
        a, b, c = random.sample(range(1, 6), 3)
        s1, s2 = random.choice([1, -1]), random.choice([1, -1])
        n1, n2, n3 = r * a * a, r * b * b, r * c * c
        op1 = "+" if s1 > 0 else "-"
        op2 = "+" if s2 > 0 else "-"
        q = f"\\sqrt{{{n1}}} {op1} \\sqrt{{{n2}}} {op2} \\sqrt{{{n3}}}"
        
        o_r, i_r = get_sq_free(r)
        ans_coeff = a * o_r + s1 * b * o_r + s2 * c * o_r
        res_dict[i_r] = ans_coeff
        
    elif level == 2:
        a = random.choice(rads)
        b, c = random.sample([r for r in rads if r != a], 2)
        s = random.choice([1, -1])
        op = "+" if s > 0 else "-"
        q = f"\\sqrt{{{a}}}(\\sqrt{{{b}}} {op} \\sqrt{{{c}}})"
        
        o1, i1 = get_sq_free(a * b)
        o2, i2 = get_sq_free(a * c)
        res_dict[i1] = res_dict.get(i1, 0) + o1
        res_dict[i2] = res_dict.get(i2, 0) + (s * o2)
        
    else:
        a, b = random.sample(rads, 2)
        c, d = random.sample([r for r in rads if r != a and r != b], 2)
        s1, s2 = random.choice([1, -1]), random.choice([1, -1])
        op1 = "+" if s1 > 0 else "-"
        op2 = "+" if s2 > 0 else "-"
        q = f"(\\sqrt{{{a}}} {op1} \\sqrt{{{b}}})(\\sqrt{{{c}}} {op2} \\sqrt{{{d}}})"
        
        pairs = [(a*c, 1), (a*d, s2), (b*c, s1), (b*d, s1*s2)]
        for val, sign in pairs:
            o, i = get_sq_free(val)
            res_dict[i] = res_dict.get(i, 0) + (sign * o)

    return {
        'question_text': f"${q}$",
        'answer': '',
        'correct_answer': format_radical(res_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}