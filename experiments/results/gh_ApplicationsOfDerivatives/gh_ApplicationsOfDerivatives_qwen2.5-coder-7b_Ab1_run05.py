# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 4.46s | Tokens: In=646, Out=350
# Created At: 2026-02-05 22:05:13
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    coefficients = [random.randint(-5, 5) for _ in range(3)]
    while coefficients[0] == 0:
        coefficients[0] = random.randint(-5, 5)
    
    f_x = f"{coefficients[0]}x^2 + {coefficients[1]}x + {coefficients[2]}"
    f_prime_x = f"{2 * coefficients[0]}x + {coefficients[1]}"
    f_double_prime_x = str(2 * coefficients[0])
    
    question_text = f"已知 f(x) = {f_x}，求 f'(x) 與 f''(x) 的值。"
    correct_answer = f"{f_prime_x}, {f_double_prime_x}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = user_answer.split(',')
    correct_answers = correct_answer.split(',')
    
    if len(user_answers) != len(correct_answers):
        return {'correct': False, 'result': '錯誤'}
    
    for i in range(len(user_answers)):
        if user_answers[i].strip() != correct_answers[i].strip():
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}

# Example usage:
question = generate()
print(question['question_text'])
user_answer = input("你的答案: ")
result = check(user_answer, question['correct_answer'])
print(result['result'])