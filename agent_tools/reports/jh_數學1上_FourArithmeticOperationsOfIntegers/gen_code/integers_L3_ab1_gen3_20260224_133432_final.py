# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 7.64s | Tokens: In=630, Out=319
# Created At: 2026-02-24 13:34:32
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
    elif level == 2:
        num_range = (10, 50)
    elif level == 3:
        num_range = (20, 100)
    else:
        num_range = (1, 100)
    
    for _ in range(4):
        num = random.randint(*num_range)
        sign = random.choice(signs)
        numbers.append(f"{sign}{num}")
    
    for i in range(3):
        op = random.choice(operations)
        question.append(numbers[i])
        question.append(op)
    question.append(numbers[3])
    
    question_text = "計算 `" + " ".join(question) + "` 的值。"
    correct_answer = eval(" ".join(question))
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {
            'correct': user == correct,
            'result': '正確' if user == correct else '錯誤'
        }
    except ValueError:
        return {
            'correct': False,
            'result': '錯誤'
        }