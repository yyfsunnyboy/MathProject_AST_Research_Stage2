# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 16.05s | Tokens: In=759, Out=370
# Created At: 2026-02-23 23:14:48
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question_text = ''
    answer = ''
    correct_answer = ''
    mode = 1
    operations = ['+', '-', '*', '/']
    radicals = []
    for _ in range(4):
        radicand = random.randint(1, 100)
        sqrt = math.isqrt(radicand)
        if sqrt * sqrt == radicand:
            radicand = radicand // sqrt
            radicals.append(f"{sqrt}\\sqrt{{{radicand}}}")
        else:
            radicals.append(f"\\sqrt{{{radicand}}}")
    op1 = random.choice(operations)
    op2 = random.choice(operations)
    op3 = random.choice(operations)
    op4 = random.choice(operations)
    op5 = random.choice(operations)
    op6 = random.choice(operations)
    question_text = f"化簡 $({radicals[0]} {op1} {radicals[1]} {op2} {radicals[2]} {op3} {radicals[3]}) + ({radicals[4]} {op4} {radicals[5]} {op5} {radicals[6]} {op6} {radicals[7]})$"
    correct_answer = f"{random.randint(1, 10)}\\sqrt{{{random.randint(1, 10)}}}"
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}