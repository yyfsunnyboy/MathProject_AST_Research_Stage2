# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 11.21s | Tokens: In=630, Out=476
# Created At: 2026-02-24 13:34:22
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '×', '÷']
    signs = ['+', '-']
    absolute = ['|', '|']
    parentheses = ['(', ')']
    numbers = []
    ops = []
    abs_count = 0
    abs_positions = []
    
    if level == 1:
        max_num = 20
    else:
        max_num = 50
    
    for i in range(5):
        if i == 0:
            num = random.randint(-max_num, max_num)
            numbers.append(num)
        else:
            num = random.randint(-max_num, max_num)
            numbers.append(num)
        op = random.choice(operations)
        ops.append(op)
    
    abs_positions = random.sample(range(1, len(numbers) - 1), 2)
    abs_positions.sort()
    
    for i in range(len(numbers)):
        if i in abs_positions:
            question.append(absolute[0])
        if i == 0:
            question.append(str(numbers[i]))
        else:
            question.append(ops[i - 1])
            question.append(str(numbers[i]))
    
    for i in range(len(abs_positions)):
        if i == 0:
            question.insert(abs_positions[i] * 2, absolute[0])
        else:
            question.insert(abs_positions[i] * 2, absolute[0])
    
    for i in range(len(abs_positions)):
        question.append(absolute[1])
    
    for i in range(len(question)):
        if question[i] == '×':
            question[i] = '×'
        elif question[i] == '÷':
            question[i] = '÷'
    
    question = ''.join(question)
    
    try:
        correct_answer = eval(question.replace('×', '*').replace('÷', '/'))
    except:
        correct_answer = 0
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    if user_answer == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}