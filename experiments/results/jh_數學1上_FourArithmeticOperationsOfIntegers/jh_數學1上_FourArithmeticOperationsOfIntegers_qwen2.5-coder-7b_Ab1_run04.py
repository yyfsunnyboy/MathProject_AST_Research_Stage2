# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 5.41s | Tokens: In=617, Out=397
# Created At: 2026-02-06 20:09:15
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    num1 = random.randint(-20, 20)
    num2 = random.randint(-20, 20)
    num3 = random.randint(1, 20)
    num4 = random.randint(1, 20)

    if level == 1:
        question_text = f"計算 {num1} + {num2} 的值。"
        correct_answer = str(num1 + num2)
    elif level == 2:
        question_text = f"計算 ({num1}) × ({num2}) ÷ ({num3}) 的值。"
        correct_answer = str((num1 * num2) // num3)
    elif level == 3:
        question_text = f"計算 {num1} + (-{num2}) - {num3} 的值。"
        correct_answer = str(num1 - num2 - num3)
    else:
        question_text = f"計算 ({num1}) × ({num2}) ÷ ({num3}) + |{num4} × (-2) - 5| 的值。"
        correct_answer = str((num1 * num2 // num3) + abs(num4 * (-2) - 5))

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    if user_answer == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}

# Example usage:
question = generate(level=3)
print(question['question_text'])
user_input = input("你的答案是：")
result = check(user_input.strip(), question['correct_answer'])
print(result['result'])