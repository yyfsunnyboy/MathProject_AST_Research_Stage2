# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-7b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 3.53s | Tokens: In=617, Out=280
# Created At: 2026-02-09 16:48:11
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    operators = ['+', '-', '*', '/']
    numbers = [random.randint(-20, 20) for _ in range(4)]
    question_text = f"計算 {numbers[0]}{operators[0]}{numbers[1]}{operators[1]}({numbers[2]}{operators[2]}{numbers[3]}) 的值。"
    
    # 計算正確答案
    correct_answer = eval(question_text)
    correct_answer_str = str(correct_answer).replace(' ', '')
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.replace(' ', '')
    try:
        if eval(user_answer) == float(correct_answer):
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except Exception as e:
        return {'correct': False, 'result': '錯誤'}

# Example usage
question = generate()
print(question['question_text'])
user_input = 0
result = check(user_input, question['correct_answer'])
print(result['result'])