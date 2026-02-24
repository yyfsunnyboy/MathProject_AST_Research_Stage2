# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 32.27s | Tokens: In=753, Out=939
# Created At: 2026-02-20 02:58:02
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        c = random.randint(2, 20)
        d = random.randint(2, 20)
        term = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - \\sqrt{{{c}}} + \\sqrt{{{d}}}"
        terms.append(term)
    expr = f"({terms[0]}) + ({terms[1]})" if random.random() > 0.5 else f"({terms[0]}) * ({terms[1]})"
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(2, 20)}}} + \\sqrt{{{random.randint(2, 20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}