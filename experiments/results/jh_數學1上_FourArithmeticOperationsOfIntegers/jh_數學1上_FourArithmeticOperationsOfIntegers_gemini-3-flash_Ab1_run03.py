# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 246.57s | Tokens: In=548, Out=572
# Created At: 2026-02-14 10:00:47
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-10, 11) if i not in [0, 1, -1]])
    m = random.choice([i for i in range(-8, 9) if i != 0])
    sum_ab = c * m
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.choice([i for i in range(-6, 7) if i != 0])
    e = random.randint(-12, 12)
    f = random.choice([i for i in range(-8, 9) if i != 0])
    g = random.choice([i for i in range(-30, 31) if i != 0])
    op = random.choice(['+', '-'])
    res1 = m * d
    res2 = abs(e * f + g)
    ans = res1 + res2 if op == '+' else res1 - res2
    def p(n): return f"({n})" if n < 0 else str(n)
    s_a = p(a)
    s_b = f"+{p(b)}"
    s_c = p(c)
    s_d = p(d)
    s_e = str(e) if e >= 0 else f"({e})"
    s_f = p(f)
    s_g = f"+{g}" if g >= 0 else str(g)
    question = f"計算 [{s_a}{s_b}]÷{s_c}×{s_d}{op}|{s_e}×{s_f}{s_g}| 的值。"
    return {
        'question_text': question,
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