# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 12.10s | Tokens: In=759, Out=278
# Created At: 2026-02-23 23:29:04
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question = ""
    answer = ""
    correct_answer = ""
    mode = 1
    operations = ['+', '-', '*', '/']
    num_terms = random.randint(2, 4)
    terms = []
    for _ in range(num_terms):
        radicand = random.randint(1, 100)
        coefficient = random.randint(1, 5)
        terms.append(f"{coefficient}\\sqrt{{{radicand}}}")
    operation1 = random.choice(operations)
    operation2 = random.choice(operations)
    operation3 = random.choice(operations)
    question += f"({terms[0]} {operation1} {terms[1]} {operation2} {terms[2]}) {operation3} ({terms[3]} {operation1} {terms[0]} {operation2} {terms[1]})"
    answer = question
    correct_answer = question
    return {'question_text': f"化簡 ${question}$", 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}