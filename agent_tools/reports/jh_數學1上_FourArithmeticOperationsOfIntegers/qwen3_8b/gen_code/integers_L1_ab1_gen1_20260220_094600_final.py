# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 127.90s | Tokens: In=502, Out=8242
# Created At: 2026-02-20 09:46:00
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    if level == 1:
        num_range = (-10, 10)
    elif level == 2:
        num_range = (-100, 100)
    else:
        num_range = (-1000, 1000)
    
    a = random.randint(*num_range)
    b = random.randint(*num_range)
    c = random.randint(*num_range)
    d = random.randint(*num_range)
    e = random.randint(*num_range)
    f = random.randint(*num_range)
    g = random.randint(*num_range)
    
    op1 = random.choice(['+', '-', '×', '÷'])
    op2 = random.choice(['+', '-', '×', '÷'])
    op3 = random.choice(['+', '-', '×', '÷'])
    op4 = random.choice(['+', '-', '×', '÷'])
    
    part1 = f"({a} {op1} {b})"
    part2 = f"{c} {op2} {d}"
    part3 = f"|{e} {op3} {f} - {g}|"
    
    expr = f"{part1} ÷ {part2} × {part3} + {random.randint(*num_range)}"
    
    try:
        correct = eval(expr.replace('×', '*').replace('÷', '/').replace('|', '').replace('}', '').replace('{', ''))
    except:
        correct = generate(level)
    
    return {
        'question_text': f'計算 [{part1}]÷{part2}×{part3} 的值',
        'answer': '',
        'correct_answer': str(correct),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}