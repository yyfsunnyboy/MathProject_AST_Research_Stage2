# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 187.06s | Tokens: In=622, Out=5308
# Created At: 2026-02-14 01:30:21
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = FAILED: maximum recursion depth exceeded
# ==============================================================================

import random

def generate(level=1, **kwargs):
    if level == 1:
        num_range = (-20, 20)
    else:
        num_range = (-50, 50)
    
    numbers = [random.randint(*num_range) for _ in range(5)]
    ops = [random.choice(['+', '-', '*', '/']) for _ in range(4)]
    
    # Generate expression structure with parentheses and absolute value
    expr = f"({numbers[0]} {ops[0]} {numbers[1]}) {ops[1]} |{numbers[2]} {ops[2]} {numbers[3]}| {ops[3]} {numbers[4]}"
    
    # Replace operators with Chinese symbols
    expr = expr.replace('+', '+').replace('-', '−').replace('*', '×').replace('/', '÷')
    
    # Calculate correct answer
    correct_expr = expr.replace('÷', '/').replace('×', '*').replace('−', '-').replace('|', 'abs(').replace(']', ')')
    correct_expr = correct_expr.replace('abs(', 'abs(').replace(']', ')')
    
    try:
        correct_answer = str(eval(correct_expr))
    except:
        return generate(level)
    
    return {
        'question_text': f"計算 `{expr}` 的值。",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer.strip() == correct_answer.strip(),
        'result': '正確' if user_answer.strip() == correct_answer.strip() else '錯誤'
}