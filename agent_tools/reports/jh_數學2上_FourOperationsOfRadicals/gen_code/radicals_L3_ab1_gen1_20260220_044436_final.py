# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 183.17s | Tokens: In=631, Out=11714
# Created At: 2026-02-20 04:44:36
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import math
import random

def generate(level=1, **kwargs):
    a = random.randint(2, 50)
    b = random.randint(2, 50)
    c = random.randint(2, 50)
    d = random.randint(2, 50)
    e = random.randint(2, 50)
    f = random.randint(2, 50)
    
    def largest_square_factor(n):
        for i in range(int(math.isqrt(n)), 0, -1):
            if i*i <= n and n % (i*i) == 0:
                return i*i
        return 1
    
    def simplify_sqrt(n):
        square_factor = largest_square_factor(n)
        coefficient = int(math.isqrt(square_factor))
        radical = n // square_factor
        return (coefficient, radical)
    
    term1 = simplify_sqrt(a)
    term2 = simplify_sqrt(b)
    term3 = simplify_sqrt(c)
    
    first_part = {}
    coeff1, radical1 = term1
    if radical1 in first_part:
        first_part[radical1] += coeff1
    else:
        first_part[radical1] = coeff1
    
    coeff2, radical2 = term2
    if radical2 in first_part:
        first_part[radical2] += coeff2
    else:
        first_part[radical2] = coeff2
    
    coeff3, radical3 = term3
    if radical3 in first_part:
        first_part[radical3] += -2 * coeff3
    else:
        first_part[radical3] = -2 * coeff3
    
    term4 = simplify_sqrt(d * f)
    term5 = simplify_sqrt(d)
    term6 = simplify_sqrt(e * f)
    term7 = simplify_sqrt(e)
    
    second_part = {}
    coeff4, radical4 = term4
    if radical4 in second_part:
        second_part[radical4] += coeff4
    else:
        second_part[radical4] = coeff4
    
    coeff5, radical5 = term5
    if radical5 in second_part:
        second_part[radical5] += -coeff5
    else:
        second_part[radical5] = -coeff5
    
    coeff6, radical6 = term6
    if radical6 in second_part:
        second_part[radical6] += coeff6
    else:
        second_part[radical6] = coeff6
    
    coeff7, radical7 = term7
    if radical7 in second_part:
        second_part[radical7] += -coeff7
    else:
        second_part[radical7] = -coeff7
    
    total = {}
    for radical, coeff in first_part.items():
        if radical in total:
            total[radical] += coeff
        else:
            total[radical] = coeff
    for radical, coeff in second_part.items():
        if radical in total:
            total[radical] += coeff
        else:
            total[radical] = coeff
    
    correct_answer_parts = []
    for radical, coeff in total.items():
        if coeff == 0:
            continue
        if coeff > 0:
            if radical == 1:
                correct_answer_parts.append(f"{coeff}")
            else:
                correct_answer_parts.append(f"{coeff}\\sqrt{{{radical}}}")
        else:
            if radical == 1:
                correct_answer_parts.append(f"-{abs(coeff)}")
            else:
                correct_answer_parts.append(f"-{abs(coeff)}\\sqrt{{{radical}}}")
    
    correct_answer = " + ".join(correct_answer_parts)
    
    question_text = f"(${\\sqrt{{{a}}} + \\sqrt{{{b}}} - 2\\sqrt{{{c}}} + (\\sqrt{{{d}}} + \\sqrt{{{e}}}) (\\sqrt{{{f}}} - 1)$"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}