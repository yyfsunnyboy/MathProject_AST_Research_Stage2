# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 39.80s | Tokens: In=586, Out=1268
# Created At: 2026-02-20 02:08:29
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def simplify_radical(c, n):
    d = 2
    while d * d <= n:
        while n % (d * d) == 0:
            c *= d
            n //= (d * d)
        d += 1
    return c, n

def format_expression(terms):
    bases = sorted([b for b in terms if terms[b] != 0])
    if not bases:
        return "0"
    res = ""
    for i, b in enumerate(bases):
        c = terms[b]
        if b == 1:
            term_str = str(abs(c))
        else:
            coeff_str = "" if abs(c) == 1 else str(abs(c))
            term_str = coeff_str + "\\sqrt{" + str(b) + "}"
        
        if i == 0:
            res += ("-" if c < 0 else "") + term_str
        else:
            res += (" - " if c < 0 else " + ") + term_str
    return res

def generate(level=1, **kwargs):
    res_terms = {}
    
    def add_term(c, n):
        c_simp, n_simp = simplify_radical(c, n)
        res_terms[n_simp] = res_terms.get(n_simp, 0) + c_simp

    if level == 1:
        p = random.choice([2, 3, 5, 7])
        k1, k2, k3 = random.sample(range(1, 6), 3)
        s1, s2, s3 = [random.choice([1, -1]) for _ in range(3)]
        n1, n2, n3 = k1*k1*p, k2*k2*p, k3*k3*p
        
        add_term(s1, n1)
        add_term(s2, n2)
        add_term(s3, n3)
        
        q1 = ("" if s1 > 0 else "-") + "\\sqrt{" + str(n1) + "}"
        q2 = (" + " if s2 > 0 else " - ") + "\\sqrt{" + str(n2) + "}"
        q3 = (" + " if s3 > 0 else " - ") + "\\sqrt{" + str(n3) + "}"
        question = f"{q1}{q2}{q3}"
        
    elif level == 2:
        b1, b2 = random.sample([2, 3, 5, 6, 7, 10], 2)
        c1, c2 = random.randint(1, 3), random.randint(1, 3)
        c3, c4 = random.randint(1, 3), random.randint(1, 3)
        s = random.choice([1, -1])
        
        add_term(c1 * c3, b1 * b1)
        add_term(c1 * s * c4, b1 * b2)
        add_term(c2 * c3, b2 * b1)
        add_term(c2 * s * c4, b2 * b2)
        
        part1 = f"{c1}\\sqrt{{{b1}}} + {c2}\\sqrt{{{b2}}}"
        op = "+" if s > 0 else "-"
        part2 = f"{c3}\\sqrt{{{b1}}} {op} {c4}\\sqrt{{{b2}}}"
        question = f"({part1})({part2})"
        
    else:
        p = random.choice([2, 3, 5])
        k1, k2 = random.sample(range(2, 5), 2)
        add_term(k1, p)
        add_term(k2, p)
        
        b1, b2 = random.sample([2, 3, 5, 6], 2)
        add_term(1, b1 * b2)
        add_term(-1, 1)
        
        q_part1 = f"\\sqrt{{{k1*k1*p}}} + \\sqrt{{{k2*k2*p}}}"
        q_part2 = f"(\\sqrt{{{b1}}} + 1)(\\sqrt{{{b2}}} - \\sqrt{{{b1}}})"
        
        # Recalculate res_terms for level 3 to match a specific structure
        res_terms = {}
        add_term(k1, p)
        add_term(k2, p)
        add_term(1, b1 * b2)
        add_term(-b1, 1)
        add_term(1, b2)
        add_term(-1, b1)
        question = f"({q_part1}) + {q_part2}"

    return {
        'question_text': f"Simplify ${question}$",
        'answer': '',
        'correct_answer': format_expression(res_terms),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}