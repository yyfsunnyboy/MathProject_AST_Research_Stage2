# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 226.86s | Tokens: In=622, Out=6320
# Created At: 2026-02-14 01:11:59
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = FAILED: maximum recursion depth exceeded
# ==============================================================================

import random
import re

def generate(level=1, **kwargs):
    while True:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        op1 = random.choice(['+', '-', '*', '/'])
        if op1 == '/' and b == 0:
            continue
        bracket_expr = f"({a} {op1} {b})"
        break
    
    while True:
        c = random.randint(-10, 10)
        if c == 0:
            continue
        op2 = random.choice(['/', '*'])
        break
    
    op3 = random.choice(['+', '-'])
    
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-10, 10)
    abs_expr = f"abs({e} * {f} - {g})"
    
    full_expr = f"{bracket_expr} {op2} {c} {op3} {abs_expr}"
    question_text = full_expr.replace('/', '÷').replace('*', '×').replace('abs(', '|').replace(')', '|')
    
    expr_for_eval = question_text.replace('÷', '/').replace('×', '*')
    expr_for_eval = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr_for_eval)
    
    try:
        correct_answer = eval(expr_for_eval)
    except:
        return generate(level=level)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct_answers = correct_answer.split(',') if ',' in correct_answer else [correct_answer]
    user_answers = user_answer.split(',') if ',' in user_answer else [user_answer]
    
    correct_answers = [a.strip() for a in correct_answers]
    user_answers = [a.strip() for a in user_answers]
    
    correct = any(user in correct_answers for user in user_answers)
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
}