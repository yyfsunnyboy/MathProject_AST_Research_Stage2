# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 6.46s | Tokens: In=630, Out=269
# Created At: 2026-02-24 13:25:44
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    num_operands = random.randint(3, 5)
    numbers = [random.randint(-50, 50) for _ in range(num_operands)]
    signs = [random.choice(['+', '-']) for _ in range(num_operands)]
    
    for i in range(num_operands):
        if signs[i] == '-':
            numbers[i] = -numbers[i]
        if i == 0:
            question.append(f"{numbers[i]}")
        else:
            question.append(f"{random.choice(operations)}")
            question.append(f"{numbers[i]}")
    
    question_text = " ".join(question)
    correct_answer = eval(question_text)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct = user_answer == int(correct_answer)
        result = '正確' if correct else '錯誤'
    except:
        correct = False
        result = '錯誤'
    return {
        'correct': correct,
        'result': result
    }