# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 262.65s | Tokens: In=598, Out=15977
# Created At: 2026-02-14 08:29:03
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def generate_number():
        if level == 1:
            return random.randint(-10, 10)
        elif level == 2:
            return random.randint(-100, 100)
        else:
            return random.randint(-10, 10)

    def generate_parentheses():
        a = generate_number()
        b = generate_number()
        op = random.choice(['+', '-', '×', '÷'])
        if op == '÷':
            while b == 0:
                b = generate_number()
        return f"{a}{op}{b}"

    def generate_abs():
        a = generate_number()
        b = generate_number()
        c = generate_number()
        op1 = random.choice(['+', '-', '×', '÷'])
        op2 = random.choice(['+', '-', '×', '÷'])
        if op1 == '÷':
            while b == 0:
                b = generate_number()
        if op2 == '÷':
            while c == 0:
                c = generate_number()
        return f"{a}{op1}{b}{op2}{c}"

    part1 = generate_parentheses()
    part2 = generate_parentheses()
    abs_part = generate_abs()
    op1 = random.choice(['+', '-', '×', '÷'])
    op2 = random.choice(['+', '-', '×', '÷'])
    op3 = random.choice(['+', '-', '×', '÷'])
    expr = f"({part1}){op1}({part2}){op2}|{abs_part}|"
    expr = expr.replace('×', '×').replace('÷', '÷').replace('+', '+').replace('-', '-')
    return {
        'question_text': f'計算 [{part1}]{op1}({part2}){op2}|{abs_part}| 的值。',
        'answer': '',
        'correct_answer': str(eval(expr.replace('×', '*').replace('÷', '/').replace('|', ''))),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_val = eval(user_answer.replace('×', '*').replace('÷', '/').replace('|', ''))
        correct_val = eval(correct_answer.replace('×', '*').replace('÷', '/').replace('|', ''))
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}