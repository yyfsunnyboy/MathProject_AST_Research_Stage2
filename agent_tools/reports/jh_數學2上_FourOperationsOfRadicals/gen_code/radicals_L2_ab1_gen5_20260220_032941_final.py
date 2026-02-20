# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 32.08s | Tokens: In=753, Out=934
# Created At: 2026-02-20 03:29:41
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    terms = []
    for _ in range(2 if level == 1 else 3):
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        term = f"{a}\\sqrt{{{b}}}"
        if random.random() < 0.5:
            term += f" {random.choice(ops)} {c}\\sqrt{{{d}}}"
        terms.append(term)
    expr = " ".join(terms)
    answer = eval(expr.replace('sqrt', 'math.sqrt'))
    simplified = simplify(answer)
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': simplified,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(val):
    if val < 0:
        return f"-\\sqrt{{{int(-val)}}}"
    return f"\\sqrt{{{int(val)}}}"