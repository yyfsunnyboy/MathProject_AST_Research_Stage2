# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 162.63s | Tokens: In=598, Out=10236
# Created At: 2026-02-14 08:20:10
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def generate_bracket():
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        op = random.choice(['+', '-', '*', '/'])
        if op == '/':
            while b == 0:
                b = random.randint(-20, 20)
        return f"({a} {op} {b})"
    
    def generate_abs():
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        op = random.choice(['+', '-', '*', '/'])
        if op == '/':
            while b == 0:
                b = random.randint(-20, 20)
        return f"abs({a} {op} {b})"
    
    if level == 1:
        part1 = generate_bracket()
        part2 = random.randint(-20, 20)
        part3 = random.randint(-20, 20)
        op1 = random.choice(['÷', '×', '+', '-'])
        op2 = random.choice(['÷', '×', '+', '-'])
        expr = f"{part1} {op1} {part2} {op2} {part3}"
    elif level == 2:
        part1 = generate_bracket()
        part2 = random.randint(-20, 20)
        part3 = random.randint(-20, 20)
        op1 = random.choice(['÷', '×'])
        op2 = random.choice(['÷', '×'])
        abs_part = generate_abs()
        expr = f"{part1} {op1} {part2} {op2} {part3} + {abs_part}"
    else:
        expr = generate_bracket()
    
    try:
        correct_answer = str(eval(expr.replace('÷', '/').replace('×', '*')))
    except:
        correct_answer = ''
    
    return {
        'question_text': f'計算 [{expr}] 的值。',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_val = float(user_answer.strip())
        correct_val = float(correct_answer)
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}