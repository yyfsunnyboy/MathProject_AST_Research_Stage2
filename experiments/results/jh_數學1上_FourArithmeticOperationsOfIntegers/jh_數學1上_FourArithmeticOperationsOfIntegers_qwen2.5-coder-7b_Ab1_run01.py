# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 5.55s | Tokens: In=617, Out=313
# Created At: 2026-02-06 20:07:22
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    num1 = random.randint(-10, 10)
    num2 = random.randint(-10, 10)
    num3 = random.randint(1, 10) if level > 1 else random.randint(-5, 5)
    num4 = random.randint(1, 10) if level > 1 else random.randint(-5, 5)

    operations = ['+', '-', '*', '/']
    operation1 = safe_choice(operations)
    operation2 = safe_choice(operations)
    
    question_text = f"計算 [ ({num1}){operation1}({num2}) ] {operation2}({num3})×{num4} + |{num4}*(-{num5})-{num6}| 的值。"
    correct_answer = str(eval(question_text.replace(' ', '')))
    
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
question = generate()
print(question['question_text'])
user_input = input("你的答案是：")
result = check(user_input.strip(), question['correct_answer'])
print(result['result'])