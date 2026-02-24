# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 36.58s | Tokens: In=460, Out=461
# Created At: 2026-02-24 13:07:23
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-10, 11) if i != 0])
    q = random.randint(-10, 10)
    s = c * q
    a = random.randint(-20, 20)
    b = s - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    op_abs = random.choice(['+', '-'])
    op_main = random.choice(['+', '-'])
    def f_s(n):
        return f"({n})" if n < 0 else str(n)
    p1 = f"[{f_s(a)}+{f_s(b)}]÷{f_s(c)}×{f_s(d)}"
    p2 = f"|{f_s(e)}×{f_s(f)}{op_abs}{f_s(g)}|"
    txt = f"計算 {p1}{op_main}{p2} 的值。"
    v1 = q * d
    v2_inner = e * f + g if op_abs == '+' else e * f - g
    v2 = abs(v2_inner)
    ans = v1 + v2 if op_main == '+' else v1 - v2
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