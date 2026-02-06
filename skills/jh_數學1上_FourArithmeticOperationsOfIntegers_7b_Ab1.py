# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder:7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 44.11s | Tokens: In=616, Out=337
# Created At: 2026-02-06 19:40:37
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = FAILED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    operators = ['+', '-', '*', '/']
    numbers = [random.randint(-20, 20) for _ in range(4)]
    
    # Generate the question text
    question_text = f"計算 {numbers[0]}{operators[0]}{numbers[1]}{operators[1]}{numbers[2]}{operators[2]}{numbers[3]} 的值。"
    
    # Calculate the correct answer
    expression = str(numbers[0]) + operators[0] + str(numbers[1]) + operators[1] + str(numbers[2]) + operators[2] + str(numbers[3])
    correct_answer = eval(expression)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_result = float(user_answer.replace(',', '.'))
        correct_result = float(correct_answer)
        if abs(user_result - correct_result) < 0.001:  # Allowing a small margin for floating point comparison
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except ValueError:
        return {'correct': False, 'result': '錯誤'}

# Example usage:
question = generate()
print(question['question_text'])
user_answer = input("你的答案是：")
result = check(user_answer, question['correct_answer'])
print(result['result'])