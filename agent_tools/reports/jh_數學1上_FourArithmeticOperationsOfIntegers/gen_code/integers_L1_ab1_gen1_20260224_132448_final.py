# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 12.52s | Tokens: In=630, Out=280
# Created At: 2026-02-24 13:24:48
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '×', '÷']
    num_operators = random.randint(3, 5)
    numbers = [random.randint(-50, 50) if level == 1 else random.randint(-100, 100) for _ in range(num_operators + 1)]
    signs = [random.choice(['+', '-']) for _ in range(num_operators)]
    
    for i in range(len(numbers)):
        if i > 0:
            question.append(signs[i-1])
        if numbers[i] < 0:
            question.append(f'({numbers[i]})')
        else:
            question.append(str(numbers[i]))
    
    question = ''.join(question)
    correct_answer = eval(question.replace('×', '*').replace('÷', '/'))
    
    return {
        'question_text': f'計算 `{question}` 的值。',
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        correct = str(int(user_answer)) == correct_answer
    except:
        correct = False
    
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }