# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 32.84s | Tokens: In=753, Out=956
# Created At: 2026-02-20 03:28:19
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2 if level == 1 else 3):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        terms.append(f"\\sqrt{{{a}}}")
        terms.append(f"\\sqrt{{{b}}}")
    expr = []
    for _ in range(2 if level == 1 else 3):
        expr.append(terms.pop(random.randint(0, len(terms)-1)))
        expr.append(ops[random.randint(0, 3)])
    expr.pop()
    expr = ' '.join(expr)
    expr = f"({expr}) + ({expr})" if level == 1 else f"({expr}) * ({expr})"
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(2, 20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}