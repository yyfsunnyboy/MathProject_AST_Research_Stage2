# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 7.26s | Tokens: In=630, Out=305
# Created At: 2026-02-24 13:25:21
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    numbers = []
    signs = ['+', '-']
    
    if level == 1:
        num_range = (1, 20)
    else:
        num_range = (10, 100)
    
    for _ in range(4):
        num = random.randint(*num_range)
        sign = random.choice(signs)
        numbers.append(f"{sign}{num}")
    
    for i in range(3):
        op = random.choice(operations)
        question.append(numbers[i])
        question.append(op)
    
    question.append(numbers[3])
    question_str = ''.join(question)
    question_str = question_str.replace('//', '÷').replace('*', '×')
    
    try:
        answer = eval(question_str)
        correct_answer = str(answer)
    except:
        correct_answer = "Error"
    
    return {
        'question_text': f"計算 `{question_str}` 的值。",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        correct_bool = user == correct
    except:
        correct_bool = False
    
    return {
        'correct': correct_bool,
        'result': '正確' if correct_bool else '錯誤'
    }