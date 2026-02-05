# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 19.64s | Tokens: In=646, Out=446
# Created At: 2026-02-04 15:49:53
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
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
        return " + ".join(terms).replace("+ -", "- ").strip()
    
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
    
    def normalize_expression(expr):
        return expr.replace(" ", "").replace("+", "+").replace("-", "-")
    
    normalized_user_answers = sorted([normalize_expression(ans) for ans in user_answers])
    normalized_correct_answers = sorted([normalize_expression(ans) for ans in correct_answers])
    
    is_correct = normalized_user_answers == normalized_correct_answers
    
    return {
        'correct': is_correct,
        'result': "正確" if is_correct else "錯誤"
    }