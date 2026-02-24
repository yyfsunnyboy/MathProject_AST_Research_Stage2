# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 13.25s | Tokens: In=759, Out=307
# Created At: 2026-02-23 23:22:39
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
    operations = ['+', '-']
    radicals = []
    for _ in range(3):
        radicand = random.randint(1, 100)
        coefficient = random.randint(1, 5)
        radicals.append(f"{coefficient}\\sqrt{{{radicand}}}")
    for _ in range(2):
        radicand1 = random.randint(1, 100)
        radicand2 = random.randint(1, 100)
        coefficient1 = random.randint(1, 5)
        coefficient2 = random.randint(1, 5)
        operation = random.choice(operations)
        radicals.append(f"({coefficient1}\\sqrt{{{radicand1}}} {operation} {coefficient2}\\sqrt{{{radicand2}}})")
    random.shuffle(radicals)
    question += "化簡 $"
    question += " + ".join(radicals)
    question += "$"
    answer = ""
    correct_answer = ""
    return {'question_text': question, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}