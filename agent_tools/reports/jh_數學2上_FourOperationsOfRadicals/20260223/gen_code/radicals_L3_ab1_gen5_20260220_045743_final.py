# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 147.67s | Tokens: In=631, Out=9675
# Created At: 2026-02-20 04:57:43
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    base_rad = random.choice([2, 3, 5, 7])
    square_factors = [random.choice([4, 9, 16, 25, 36, 49, 64, 81, 100]) for _ in range(2, 4)]
    radicands = [base_rad * sf for sf in square_factors]
    terms = [f"\\sqrt{{{r}}}" for r in radicands]
    first_part = " + ".join(terms)
    
    a = random.choice([2, 3, 5, 7])
    b = random.choice([2, 3, 5, 7])
    while b == a:
        b = random.choice([2, 3, 5, 7])
    c = random.choice([2, 3, 5, 7])
    d = random.randint(1, 5)
    binomial1 = f"\\sqrt{{{a}}} + \\sqrt{{{b}}}"
    binomial2 = f"\\sqrt{{{c}}} - {d}"
    second_part = f"({binomial1})({binomial2})"
    
    question_text = f"({first_part}) + ({second_part})"
    
    sum_coeff = sum([int(math.isqrt(sf)) for sf in square_factors])
    simplified_first = f"{sum_coeff}\\sqrt{{{base_rad}}}"
    
    terms_expanded = [
        f"\\sqrt{{{a}}}\\sqrt{{{c}}}",
        f"-{d}\\sqrt{{{a}}}",
        f"\\sqrt{{{b}}}\\sqrt{{{c}}}",
        f"-{d}\\sqrt{{{b}}}"
    ]
    expanded = " + ".join(terms_expanded)
    
    simplified_terms = []
    for term in terms_expanded:
        if term.startswith("-"):
            simplified_terms.append(term)
        else:
            simplified_terms.append(term)
    
    simplified_second = " + ".join(simplified_terms)
    
    correct_answer = f"{simplified_first} + {simplified_second}"
    
    return {
        'question_text': f"${question_text}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}