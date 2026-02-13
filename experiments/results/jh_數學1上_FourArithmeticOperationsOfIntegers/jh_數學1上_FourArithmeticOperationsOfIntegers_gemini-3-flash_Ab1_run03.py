# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 42.05s | Tokens: In=0, Out=0
# Created At: 2026-02-13 23:06:45
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)

    # Part 1: [(a + b) / c] * d
    # Ensure division results in an integer
    c = random.choice([x for x in range(-10, 11) if x != 0])
    res_div = random.randint(-10, 10)
    sum_ab = res_div * c
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    
    # Part 2: |e * f ± g|
    e = random.randint(-12, 12)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    op_inner = random.choice(['+', '-'])
    
    # Construct strings for the expression
    part1_str = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}"
    
    if op_inner == '+':
        part2_str = f"|{fmt(e)}×{fmt(f)}+{fmt(g)}|"
        inner_val = e * f + g
    else:
        part2_str = f"|{fmt(e)}×{fmt(f)}-{fmt(g)}|"
        inner_val = e * f - g
        
    op_outer = random.choice(['+', '-'])
    
    # Calculate the correct answer
    # term1 = ((a + b) / c) * d
    term1 = res_div * d
    term2 = abs(inner_val)
    
    if op_outer == '+':
        correct_val = term1 + term2
    else:
        correct_val = term1 - term2
        
    question_text = f"計算 {part1_str}{op_outer}{part2_str} 的值。"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
}