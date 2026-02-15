# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 307.91s | Tokens: In=470, Out=604
# Created At: 2026-02-15 16:15:21
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(f, p=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({s})" if p and f < 0 else s

    def get_f():
        n = random.randint(-10, 10)
        d = random.randint(2, 6)
        return Fraction(n, d)

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = get_f()
    while c == 0: c = get_f()
    d = get_f()
    while d == 0: d = get_f()
    e = random.randint(-10, 10)
    f = get_f()
    while f == 0: f = get_f()
    g = random.randint(-10, 10)

    p1_val = ((a + b) * c) / d
    p2_val = abs(e * f + g)
    
    op = random.choice(['+', '-'])
    if op == '+':
        total_val = p1_val + p2_val
    else:
        total_val = p1_val - p2_val

    q_str = f"[({a}{'+' if b>=0 else ''}{b})×{fmt(c, True)}]÷{fmt(d, True)} {op} |{fmt(Fraction(e), True)}×{fmt(f, True)}{'+' if g>=0 else ''}{g}|"
    ans_str = str(total_val.numerator) if total_val.denominator == 1 else f"{total_val.numerator}/{total_val.denominator}"

    return {
        'question_text': f"計算 {q_str} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        u = Fraction(user_answer.strip().replace(' ', ''))
        c = Fraction(correct_answer.strip().replace(' ', ''))
        is_correct = (u == c)
    except:
        is_correct = (user_answer.strip() == correct_answer.strip())
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }