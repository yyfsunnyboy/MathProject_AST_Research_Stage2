# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 299.82s | Tokens: In=586, Out=853
# Created At: 2026-02-20 00:35:52
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def simplify_radical(n):
    coeff = 1
    d = 2
    temp = n
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def format_radical_term(c, r):
    if c == 0:
        return "0"
    if r == 1:
        return str(c)
    
    res = ""
    if c == 1:
        res = ""
    elif c == -1:
        res = "-"
    else:
        res = str(c)
    
    return res + f"\\sqrt{{{r}}}"

def generate(level=1, **kwargs):
    mode = random.randint(1, 3)
    
    if mode == 1:
        p = random.choice([2, 3, 5, 6, 7, 10])
        m1, m2, m3 = random.sample(range(2, 6), 3)
        c1 = random.randint(1, 3)
        c2 = random.randint(1, 3)
        c3 = -random.randint(1, 3)
        
        t1 = c1 * m1 * m1 * p
        t2 = c2 * m2 * m2 * p
        t3 = abs(c3) * m3 * m3 * p
        
        q_text = f"\\sqrt{{{t1}}} + \\sqrt{{{t2}}} - \\sqrt{{{t3}}}"
        ans_val = c1 * m1 + c2 * m2 + c3 * m3
        correct_ans = format_radical_term(ans_val, p)
        
    elif mode == 2:
        a = random.choice([2, 3, 5])
        b = random.choice([2, 3, 5])
        while a == b:
            b = random.choice([2, 3, 5])
        c = random.choice([2, 3, 5])
        
        q_text = f"\\sqrt{{{c}}}(\\sqrt{{{a}}} + \\sqrt{{{b}}})"
        
        r1 = a * c
        r2 = b * c
        co1, rt1 = simplify_radical(r1)
        co2, rt2 = simplify_radical(r2)
        
        t1_str = format_radical_term(co1, rt1)
        t2_str = format_radical_term(co2, rt2)
        correct_ans = f"{t1_str} + {t2_str}"
        
    else:
        a = random.choice([2, 3, 5])
        b = random.choice([2, 3, 5])
        while a == b:
            b = random.choice([2, 3, 5])
            
        q_text = f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{a}}} - \\sqrt{{{b}}})"
        correct_ans = str(a - b)

    return {
        'question_text': f"${q_text}$",
        'answer': '',
        'correct_answer': correct_ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Incorrect'}