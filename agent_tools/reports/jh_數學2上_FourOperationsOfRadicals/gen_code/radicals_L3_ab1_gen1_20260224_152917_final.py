# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 297.56s | Tokens: In=586, Out=1194
# Created At: 2026-02-24 15:29:17
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def simplify_radical(c, r):
    out_coeff = 1
    d = 2
    temp_r = r
    while d * d <= temp_r:
        while temp_r % (d * d) == 0:
            out_coeff *= d
            temp_r //= (d * d)
        d += 1
    return c * out_coeff, temp_r

def format_latex(terms):
    res = ""
    sorted_radicands = sorted([r for r in terms if terms[r] != 0])
    for i, r in enumerate(sorted_radicands):
        c = terms[r]
        abs_c = abs(c)
        if i == 0:
            if c < 0:
                res += "-"
        else:
            res += " + " if c > 0 else " - "
        if r == 1:
            res += str(abs_c)
        else:
            if abs_c != 1:
                res += str(abs_c)
            res += "\\sqrt{" + str(r) + "}"
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    primes = [2, 3, 5, 6, 7, 10]
    
    def get_random_term():
        base = random.choice(primes)
        k = random.randint(1, 4)
        coeff = random.randint(1, 3) * random.choice([1, -1])
        return coeff, k * k * base, base

    def add_to_result(res_dict, c, r):
        nc, nr = simplify_radical(c, r)
        res_dict[nr] = res_dict.get(nr, 0) + nc

    final_terms = {}
    
    c1, r1, b1 = get_random_term()
    c2, r2, b2 = get_random_term()
    c3, r3, b3 = get_random_term()
    
    add_to_result(final_terms, c1, r1)
    add_to_result(final_terms, c2, r2)
    add_to_result(final_terms, c3, r3)
    
    part1_str = ""
    for i, (c, r) in enumerate([(c1, r1), (c2, r2), (c3, r3)]):
        if i > 0 and c > 0: part1_str += " + "
        elif i > 0 and c < 0: part1_str += " - "
        elif i == 0 and c < 0: part1_str += "-"
        
        abs_c = abs(c)
        if abs_c == 1: part1_str += f"\\sqrt{{{r}}}"
        else: part1_str += f"{abs_c}\\sqrt{{{r}}}"

    c4, r4, b4 = get_random_term()
    c5, r5, b5 = get_random_term()
    c6, r6, b6 = get_random_term()
    c7, r7, b7 = get_random_term()
    
    add_to_result(final_terms, c4 * c6, r4 * r6)
    add_to_result(final_terms, c4 * c7, r4 * r7)
    add_to_result(final_terms, c5 * c6, r5 * r6)
    add_to_result(final_terms, c5 * c7, r5 * r7)
    
    def fmt_bin(ca, ra, cb, rb):
        s = ""
        if ca < 0: s += "-"
        if abs(ca) == 1: s += f"\\sqrt{{{ra}}}"
        else: s += f"{abs(ca)}\\sqrt{{{ra}}}"
        
        if cb > 0: s += " + "
        else: s += " - "
        if abs(cb) == 1: s += f"\\sqrt{{{rb}}}"
        else: s += f"{abs(cb)}\\sqrt{{{rb}}}"
        return s

    bin1 = fmt_bin(c4, r4, c5, r5)
    bin2 = fmt_bin(c6, r6, c7, r7)
    
    question = f"({part1_str}) + ({bin1})({bin2})"
    correct_answer = format_latex(final_terms)
    
    return {
        'question_text': f"${question}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}