# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash-preview | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 43.02s | Tokens: In=548, Out=862
# Created At: 2026-02-13 22:43:56
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)

    t = random.randint(1, 3)
    if t == 1:
        # Template: [(a + b) ÷ c] × d + |e × f - g|
        c = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
        k = random.randint(-10, 10)
        sum_ab = c * k
        a = random.randint(-20, 20)
        b = sum_ab - a
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-20, 20)
        val = (k * d) + abs(e * f - g)
        q = f"[({fmt(a)})+({fmt(b)})]÷{fmt(c)}×{fmt(d)}+|{fmt(e)}×{fmt(f)}-{fmt(g)}|"
    elif t == 2:
        # Template: a - |b × c + d| + [e × (f - g)] ÷ h
        h = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
        k = random.randint(-10, 10)
        e = h
        f = random.randint(-20, 20)
        g = f - k
        a = random.randint(-30, 30)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        d = random.randint(-20, 20)
        val = a - abs(b * c + d) + k
        q = f"{fmt(a)}-|{fmt(b)}×{fmt(c)}+{fmt(d)}|+[{fmt(e)}×({fmt(f)}-{fmt(g)})]÷{fmt(h)}"
    else:
        # Template: |a × b - c| + d × [e - (f + g)]
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-20, 20)
        d = random.randint(-10, 10)
        e = random.randint(-20, 20)
        f = random.randint(-20, 20)
        g = random.randint(-20, 20)
        val = abs(a * b - c) + d * (e - (f + g))
        q = f"|{fmt(a)}×{fmt(b)}-{fmt(c)}|+{fmt(d)}×[{fmt(e)}-({fmt(f)}+{fmt(g)})]"

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        is_correct = (ua == ca)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }