# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 44.47s | Tokens: In=460, Out=341
# Created At: 2026-02-24 13:13:15
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.randint(2, 10) * random.choice([-1, 1])
    k = random.randint(-10, 10)
    a = random.randint(-20, 20)
    b = c * k - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    def fmt(n):
        return f"({n})" if n < 0 else str(n)
    q = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}+|{e}×{fmt(f)}{'+' if g>=0 else ''}{g}|"
    ans = k * d + abs(e * f + g)
    return {
        'question_text': f"計算 {q} 的值。",
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