# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 4.89s | Tokens: In=617, Out=365
# Created At: 2026-02-06 20:09:20
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    operators = ['+', '-', '*', '/']
    numbers = [random.randint(-20, 20) for _ in range(4)]
    
    # Ensure the divisor is not zero
    for _safety_counter in range(1000):  # Safety: converted from while True
        if numbers[3] == 0:
            numbers[3] = random.randint(-19, -1)
        else:
            break
    
    question_text = f"計算 [{numbers[0]} {operators[0]} {numbers[1]}] {operators[2]} ({numbers[2]} {operators[1]} {numbers[3]}) 的值。"
    
    # Calculate the correct answer
    inner_bracket = numbers[0] + numbers[1]
    division_multiplication = (inner_bracket / numbers[2]) * 3
    absolute_value = abs(numbers[2] * (-2) - 5)
    correct_answer = str(division_multiplication + absolute_value)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_result = eval(user_answer.replace(' ', ''))
        if str(user_result) == correct_answer:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except Exception as e:
        return {'correct': False, 'result': '錯誤'}

# Example usage
question = generate()
print(question['question_text'])
user_answer = input("你的答案是：")
result = check(user_answer, question['correct_answer'])
print(result['result'])