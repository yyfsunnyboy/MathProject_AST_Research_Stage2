# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 267.73s | Tokens: In=548, Out=475
# Created At: 2026-02-14 10:05:15
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)

    # Template: [(a + b)] ÷ c × d ± |e × f + g|
    c = random.choice([i for i in range(-10, 11) if i != 0])
    k = random.randint(-8, 8)
    sum_ab = c * k
    a = random.randint(-20, 20)
    b = sum_ab - a
    d = random.randint(-6, 6)
    e = random.randint(-10, 10)
    f = random.randint(-6, 6)
    g = random.randint(-20, 20)
    op_sym = random.choice(['+', '-'])
    
    if g < 0:
        abs_expr = f"{p(e)}×{p(f)}-{abs(g)}"
    else:
        abs_expr = f"{p(e)}×{p(f)}+{g}"
        
    q_text = f"計算 [({a})+({b})]÷{p(c)}×{p(d)}{op_sym}|{abs_expr}| 的值。"
    
    term1 = (a + b) // c * d
    term2 = abs(e * f + g)
    ans = term1 + term2 if op_sym == '+' else term1 - term2
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans),
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