# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 276.32s | Tokens: In=548, Out=400
# Created At: 2026-02-14 10:09:51
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    c = random.randint(-10, 10)
    if c == 0: c = 1
    q = random.randint(-10, 10)
    num = c * q
    a = random.randint(-20, 20)
    b = num - a
    d = random.randint(-10, 10)
    part1_val = (a + b) // c * d
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    part2_val = abs(e * f - g)
    op = random.choice(['+', '-'])
    if op == '+':
        ans = part1_val + part2_val
    else:
        ans = part1_val - part2_val
    def p(n):
        return f"({n})" if n < 0 else str(n)
    txt = f"計算 [({a})+({b})]÷{p(c)}×{p(d)}{op}|{e}×{p(f)}-{p(g)}| 的值。"
    return {
        'question_text': txt,
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