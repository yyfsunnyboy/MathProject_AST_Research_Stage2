# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3:14b-q4_K_M | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 282.64s | Tokens: In=622, Out=7797
# Created At: 2026-02-13 20:51:12
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    op1 = random.choice(['+', '-'])
    c = random.randint(-10, 10)
    while c == 0:
        c = random.randint(-10, 10)
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-10, 10)
    op2 = random.choice(['*', '+'])
    question_text = f"[{a} {op1} {b}] ÷ {c} × {d} + |{e} {op2} {f} - {g}|"
    expr = f"(({a}) {op1} ({b})) / ({c}) * ({d}) + abs(({e}) {op2} ({f}) - ({g}))"
    correct_answer = str(eval(expr))
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = user_answer.split(',')
    correct_answers = correct_answer.split(',')
    for ua in user_answers:
        if ua.strip() in correct_answers:
            return {'correct': True, 'result': '正確'}
    return {'correct': False, 'result': '錯誤'}