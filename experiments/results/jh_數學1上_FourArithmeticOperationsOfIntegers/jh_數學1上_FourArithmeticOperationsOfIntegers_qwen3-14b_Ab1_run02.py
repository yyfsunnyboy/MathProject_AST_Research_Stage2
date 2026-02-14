# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 307.19s | Tokens: In=622, Out=7100
# Created At: 2026-02-14 14:28:56
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = FAILED: unsupported operand type(s) for /: 'list' and 'int'
# ==============================================================================

import random
import re

def generate(level=1, **kwargs):
    a = random.randint(-50, 50)
    b = random.randint(-50, 50)
    op1 = random.choice(['+', '-', '×', '÷'])
    
    c = random.randint(-50, 50)
    while c == 0:
        c = random.randint(-50, 50)
    
    d = random.randint(-50, 50)
    
    e = random.randint(-50, 50)
    f = random.randint(-50, 50)
    g = random.randint(-50, 50)
    
    def format_number(x):
        if x < 0:
            return f"({x})"
        else:
            return str(x)
    
    bracket_expr = f"[{format_number(a)}{op1}{format_number(b)}]"
    abs_expr = f"|{format_number(e)}×{format_number(f)}-{format_number(g)}|"
    
    question_text = f"{bracket_expr}÷{format_number(c)}×{format_number(d)}+{abs_expr}"
    
    expr = question_text.replace('÷', '/').replace('×', '*')
    expr = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr)
    
    correct_answer = eval(expr)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }