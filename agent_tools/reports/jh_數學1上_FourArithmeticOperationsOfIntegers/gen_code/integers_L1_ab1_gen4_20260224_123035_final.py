# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 30.72s | Tokens: In=460, Out=383
# Created At: 2026-02-24 12:30:35
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    a = random.randint(-30, 30)
    b = k * c - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    def f_n(n):
        return f"({n})" if n < 0 else str(n)
    p1 = k * d
    p2 = abs(e * f - g)
    op = random.choice(['+', '-'])
    ans = p1 + p2 if op == '+' else p1 - p2
    txt = f"計算 [{f_n(a)}+{f_n(b)}]÷{f_n(c)}×{f_n(d)}{op}|{f_n(e)}×{f_n(f)}-{f_n(g)}| 的值。"
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }