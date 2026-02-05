# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 22.98s | Tokens: In=625, Out=404
# Created At: 2026-02-04 23:31:28
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = FAILED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    coefficients = [random.randint(-5, 5) for _ in range(4)]
    f_x = f"{coefficients[0]}x^3 + {coefficients[1]}x^2 + {coefficients[2]}x + {coefficients[3]}"
    
    if level == 1:
        derivative = f"{3*coefficients[0]}x^2 + {2*coefficients[1]}x + {coefficients[2]}"
        correct_answer = f"{derivative}"
    elif level == 2:
        second_derivative = f"{6*coefficients[0]}x + {2*coefficients[1]}"
        third_derivative = f"6*{coefficients[0]}"
        correct_answer = f"{second_derivative},{third_derivative}"
    
    question_text = f"已知 $f(x) = {f_x}$，求 $f'(x)$ 與 $f'''(x)$。"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = [ua.strip() for ua in user_answer.split(',')]
    correct_answers = [ca.strip() for ca in correct_answer.split(',')]
    
    if len(user_answers) != len(correct_answers):
        return {'correct': False, 'result': '錯誤'}
    
    for i in range(len(user_answers)):
        if user_answers[i] != correct_answers[i]:
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}

# Example usage:
question = generate(level=2)
print(question['question_text'])
user_answer = input("你的答案: ")
result = check(user_answer, question['correct_answer'])
print(result['result'])