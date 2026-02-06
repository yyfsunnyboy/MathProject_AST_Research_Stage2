# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 4.39s | Tokens: In=646, Out=347
# Created At: 2026-02-05 22:05:04
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    coefficients = [random.randint(-5, 5) for _ in range(3)]
    while coefficients[0] == 0:
        coefficients[0] = random.randint(-5, 5)
    
    f_x = f"{coefficients[0]}x^3 + {coefficients[1]}x^2 + {coefficients[2]}"
    f_prime_x = f"{3 * coefficients[0]}x^2 + {2 * coefficients[1]}x"
    f_double_prime_x = f"{6 * coefficients[0]}x + {2 * coefficients[1]}"
    
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
    
    if len(user_answers) != len(correct_answers):
        return {'correct': False, 'result': '錯誤'}
    
    for i in range(len(user_answers)):
        if user_answers[i] != correct_answers[i]:
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}

# 程式碼結束