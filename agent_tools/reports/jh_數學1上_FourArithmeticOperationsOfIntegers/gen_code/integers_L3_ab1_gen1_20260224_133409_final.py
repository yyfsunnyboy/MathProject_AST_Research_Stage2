# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 9.37s | Tokens: In=630, Out=386
# Created At: 2026-02-24 13:34:09
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    numbers = []
    signs = ['+', '-']
    abs_used = False

    if level == 1:
        num_range = (1, 20)
    elif level == 2:
        num_range = (10, 50)
    else:
        num_range = (50, 100)

    for _ in range(3):
        num = random.randint(*num_range)
        sign = random.choice(signs)
        numbers.append(f"{sign}{num}")

    for _ in range(2):
        op = random.choice(operations)
        question.append(random.choice(numbers))
        question.append(op)

    question.append(random.choice(numbers))
    question.append('+')
    question.append('|')

    abs_num = random.randint(1, 20)
    abs_sign = random.choice(signs)
    abs_num = f"{abs_sign}{abs_num}"
    abs_expr = f"{abs_num}*{random.choice(signs)}{random.randint(1, 10)}-{random.randint(1, 10)}"
    question.append(abs_expr)
    question.append('|')

    question_text = ' '.join(question)
    correct_answer = eval(question_text)
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
        correct_flag = user == correct
        return {
            'correct': correct_flag,
            'result': '正確' if correct_flag else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }