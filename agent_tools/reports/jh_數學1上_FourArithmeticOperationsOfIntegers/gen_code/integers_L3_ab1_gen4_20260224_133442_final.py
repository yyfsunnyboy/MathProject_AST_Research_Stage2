# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 8.00s | Tokens: In=630, Out=339
# Created At: 2026-02-24 13:34:42
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '×', '÷']
    num_operands = random.randint(3, 5)
    signs = [random.choice(['+', '-']) for _ in range(num_operands)]
    numbers = [random.randint(1, 20) for _ in range(num_operands)]
    
    # 產生數學式子
    for i in range(num_operands):
        if signs[i] == '-':
            question.append(f'(-{numbers[i]})')
        else:
            question.append(f'({numbers[i]})')
    
    # 插入運算子
    for i in range(num_operands - 1):
        question.insert(2 * i + 1, random.choice(operations))
    
    # 加入絕對值運算
    if random.random() < 0.5:
        abs_index = random.randint(0, len(question) - 1)
        question.insert(abs_index, '|')
        question.insert(abs_index + 2, '|')
    
    # 計算正確答案
    expr = ''.join(question).replace('×', '*').replace('÷', '/')
    correct_answer = eval(expr)
    
    return {
        'question_text': ''.join(question),
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }