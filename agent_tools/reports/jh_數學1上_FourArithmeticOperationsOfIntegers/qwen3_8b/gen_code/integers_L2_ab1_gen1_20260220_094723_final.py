# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 23.46s | Tokens: In=502, Out=1671
# Created At: 2026-02-20 09:47:23
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def generate_bracket():
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        op = random.choice(['+', '-', '*', '/'])
        if op == '+':
            expr = f'({a}+{b})'
            result = a + b
        elif op == '-':
            expr = f'({a}-{b})'
            result = a - b
        elif op == '*':
            expr = f'({a}*{b})'
            result = a * b
        elif op == '/':
            if b == 0:
                return generate_bracket()
            if a % b != 0:
                return generate_bracket()
            expr = f'({a}/{b})'
            result = a // b
        return expr, result

    def generate_abs():
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-10, 10)
        op1 = random.choice(['*', '-'])
        op2 = random.choice(['+', '-'])
        if op1 == '*':
            part1 = f'{e}*{f}'
        else:
            part1 = f'{e}-{f}'
        if op2 == '+':
            part2 = f'+{g}'
        else:
            part2 = f'-{g}'
        expr = f'|{part1}{part2}|'
        inner = eval(f'{e}{op1}{f}{op2}{g}')
        return expr, abs(inner)

    bracket_expr, bracket_result = generate_bracket()
    abs_expr, abs_result = generate_abs()
    full_expr = f'[{bracket_expr}]÷{random.randint(1, 10)}×{random.randint(1, 10)}+{abs_expr}'
    full_result = eval(full_expr.replace('÷', '/').replace('×', '*'))
    return {
        'question_text': f'計算 [{bracket_expr}]÷{random.randint(1, 10)}×{random.randint(1, 10)}+{abs_expr} 的值。',
        'answer': '',
        'correct_answer': str(full_result),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}