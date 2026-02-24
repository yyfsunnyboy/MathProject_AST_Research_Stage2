# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 28.67s | Tokens: In=460, Out=400
# Created At: 2026-02-24 12:56:40
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    q_p = random.randint(-10, 10)
    num = c * q_p
    a = random.randint(-50, 50)
    b = num - a
    d = random.randint(-10, 10)
    e = random.randint(-12, 12)
    f = random.randint(-12, 12)
    g = random.randint(-50, 50)
    op = random.choice(['+', '-'])
    v1 = q_p * d
    v2 = abs(e * f - g)
    ans = v1 + v2 if op == '+' else v1 - v2
    def f_n(n):
        return f"({n})" if n < 0 else str(n)
    txt = f"計算 [{f_n(a)}+{f_n(b)}]÷{f_n(c)}×{f_n(d)}{op}|{f_n(e)}×{f_n(f)}-{f_n(g)}| 的值。"
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_c = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_c,
        'result': '正確' if is_c else '錯誤'
    }