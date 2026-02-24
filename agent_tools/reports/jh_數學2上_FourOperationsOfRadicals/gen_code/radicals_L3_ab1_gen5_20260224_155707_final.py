# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 6.72s | Tokens: In=759, Out=280
# Created At: 2026-02-24 15:57:07
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    operations = ['+', '-', '*', '/']
    radical_terms = []
    for _ in range(2):
        term = random.choice(operations)
        coefficient = random.randint(1, 5)
        radicand = random.randint(2, 20)
        radical_terms.append(f"{coefficient}\\sqrt{{{radicand}}}")
    expr1 = " + ".join(radical_terms)
    radical_terms2 = []
    for _ in range(2):
        term = random.choice(operations)
        coefficient = random.randint(1, 5)
        radicand = random.randint(2, 20)
        radical_terms2.append(f"{coefficient}\\sqrt{{{radicand}}}")
    expr2 = " + ".join(radical_terms2)
    question_text = f"化簡 $({expr1}) + ({expr2})$"
    answer = ""
    correct_answer = ""
    mode = 1
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}