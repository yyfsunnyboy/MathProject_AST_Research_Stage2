# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 268.78s | Tokens: In=548, Out=463
# Created At: 2026-02-14 09:55:59
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)

    c = random.choice([i for i in range(-12, 13) if i != 0])
    sum_ab = c * random.randint(-6, 6)
    a = random.randint(-25, 25)
    b = sum_ab - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-25, 25)
    op_sign = random.choice(['+', '-'])
    
    part1 = (a + b) // c * d
    part2 = abs(e * f + g)
    ans = part1 + part2 if op_sign == '+' else part1 - part2

    abs_content = f"{fmt(e)}×{fmt(f)}{g:+d}"
    expr = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}{op_sign}|{abs_content}|"
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        is_correct = int(float(ua)) == int(float(ca))
    except:
        is_correct = str(user_answer).strip() == str(correct_answer).strip()
        
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }