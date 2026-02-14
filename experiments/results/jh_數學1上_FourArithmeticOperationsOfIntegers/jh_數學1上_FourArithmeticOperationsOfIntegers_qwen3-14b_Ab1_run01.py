# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 376.83s | Tokens: In=622, Out=10282
# Created At: 2026-02-14 01:08:10
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import re

def generate(level=1, **kwargs):
    a = random.randint(-50, 50)
    b = random.randint(-50, 50)
    c = random.randint(-50, 50)
    d = random.randint(-50, 50)
    e = random.randint(-50, 50)
    f = random.randint(-50, 50)
    
    op1 = random.choice(['+', '-', '*', '/'])
    op2 = random.choice(['÷', '×'])
    op3 = random.choice(['+', '-'])
    op4 = random.choice(['+', '-', '*', '/'])
    op5 = random.choice(['+', '-', '*', '/'])
    
    if op2 == '÷':
        while c == 0:
            c = random.randint(-50, 50)
    if op4 == '÷':
        while e == 0:
            e = random.randint(-50, 50)
    if op5 == '÷':
        while f == 0:
            f = random.randint(-50, 50)
    
    bracket_part = f"({a} {op1} {b})"
    abs_part = f"|{d} {op4} {e} {op5} {f}|"
    question_text = f"[{bracket_part}] {op2} {c} {op3} {abs_part}"
    
    expr_for_calc = question_text.replace('÷', '/').replace('×', '*')
    expr_for_calc = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr_for_calc)
    
    try:
        correct_answer = eval(expr_for_calc)
    except:
        correct_answer = 0
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct_answers = correct_answer.split(',') if ',' in correct_answer else [correct_answer]
    user_answers = user_answer.split(',') if ',' in user_answer else [user_answer]
    
    correct_answers = [ans.strip() for ans in correct_answers]
    user_answers = [ans.strip() for ans in user_answers]
    
    correct = any(user_ans in correct_answers for user_ans in user_answers)
    
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
}