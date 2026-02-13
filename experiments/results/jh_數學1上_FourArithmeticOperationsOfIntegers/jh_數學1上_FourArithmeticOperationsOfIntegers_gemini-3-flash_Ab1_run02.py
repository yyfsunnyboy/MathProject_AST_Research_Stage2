# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 23.73s | Tokens: In=0, Out=0
# Created At: 2026-02-13 23:06:03
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)

    # Part 1: [ (a + b) / c ] * d
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    sum_ab = a + b
    # Ensure c is a divisor of (a+b) and not zero
    divisors = [i for i in range(-15, 16) if i != 0 and sum_ab % i == 0]
    c = random.choice(divisors)
    d = random.randint(-10, 10)
    
    part1_val = (sum_ab // c) * d
    part1_str = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}"

    # Part 2: | e * f + g |
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    
    part2_val = abs(e * f + g)
    if g < 0:
        part2_str = f"|{p(e)}×{p(f)}-{abs(g)}|"
    elif g > 0:
        part2_str = f"|{p(e)}×{p(f)}+{g}|"
    else:
        part2_str = f"|{p(e)}×{p(f)}|"

    # Combine Part 1 and Part 2
    op = random.choice(['+', '-'])
    if op == '+':
        ans = part1_val + part2_val
    else:
        ans = part1_val - part2_val
        
    question = f"計算 {part1_str}{op}{part2_str} 的值。"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
}