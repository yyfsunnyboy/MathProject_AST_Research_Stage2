# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 63.09s | Tokens: In=460, Out=370
# Created At: 2026-02-24 23:23:58
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-10, 11) if i != 0])
    m = random.randint(-10, 10)
    s = c * m
    a = random.randint(-20, 20)
    b = s - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.choice([i for i in range(-20, 21) if i != 0])
    def p(n):
        return f"({n})" if n < 0 else str(n)
    expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}+|{p(e)}×{p(f)}{'+' if g > 0 else ''}{g}|"
    ans = (a + b) // c * d + abs(e * f + g)
    return {
        'question_text': f"計算 {expr} 的值。",
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