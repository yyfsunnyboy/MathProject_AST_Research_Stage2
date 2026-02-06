# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 26.59s | Tokens: In=646, Out=453
# Created At: 2026-02-05 21:43:13
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    degree = random.randint(2, 4) if level == 1 else random.randint(3, 5)
    coefficients = [random.randint(-10, 10) for _ in range(degree + 1)]
    
    def polynomial(coefficients):
        terms = []
        for i, coeff in enumerate(coefficients):
            if coeff != 0:
                term = f"{coeff}x^{degree - i}" if degree - i > 1 else "x" if degree - i == 1 else str(coeff)
                terms.append(term)
        return " + ".join(terms).replace("+ -", "- ")
    
    def derivative(coefficients):
        deriv_coeffs = [i * coeff for i, coeff in enumerate(coefficients)][1:]
        return polynomial(deriv_coeffs)
    
    f_x = polynomial(coefficients)
    f_prime_x = derivative(coefficients)
    f_double_prime_x = derivative([i * coeff for i, coeff in enumerate(coefficients)][1:])
    
    question_text = f"已知 f(x) = {f_x}，求 f'(x) 與 f''(x) 的值。"
    correct_answer = f"{f_prime_x}, {f_double_prime_x}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = [ans.strip() for ans in user_answer.split(',')]
    correct_answers = [ans.strip() for ans in correct_answer.split(',')]
    
    def simplify(expr):
        expr = expr.replace(" ", "")
        if "^1" in expr:
            expr = expr.replace("^1", "")
        return expr
    
    simplified_user_answers = sorted([simplify(ans) for ans in user_answers])
    simplified_correct_answers = sorted([simplify(ans) for ans in correct_answers])
    
    return {
        'correct': simplified_user_answers == simplified_correct_answers,
        'result': "正確" if simplified_user_answers == simplified_correct_answers else "錯誤"
    }