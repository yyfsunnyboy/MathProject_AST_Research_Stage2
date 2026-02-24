# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 34.33s | Tokens: In=460, Out=848
# Created At: 2026-02-22 23:57:38
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        c = random.choice([i for i in range(-10, 11) if i != 0])
        q = random.randint(-10, 10)
        s = c * q
        a = random.randint(-20, 20)
        b = s - a
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-20, 20)
        txt = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}+|{p(e)}×{p(f)}-{p(g)}|"
        ans = q * d + abs(e * f - g)
    elif t == 2:
        e = random.choice([i for i in range(-10, 11) if i != 0])
        q = random.randint(-10, 10)
        d = e * q
        a = random.randint(-10, 10)
        b = random.randint(-15, 15)
        c = random.randint(-15, 15)
        f = random.randint(-20, 20)
        txt = f"{p(a)}×({p(b)}-{p(c)})+{p(d)}÷{p(e)}-|{p(f)}|"
        ans = a * (b - c) + q - abs(f)
    elif t == 3:
        f = random.choice([i for i in range(-10, 11) if i != 0])
        q = random.randint(-10, 10)
        de = q * f
        d = random.randint(-20, 20)
        e = de - d
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-20, 20)
        txt = f"|{p(a)}×{p(b)}-{p(c)}|+({p(d)}+{p(e)})÷{p(f)}"
        ans = abs(a * b - c) + q
    else:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        txt = f"{p(a)}×{p(b)}-{p(c)}×{p(d)}+{p(e)}"
        ans = a * b - c * d + e
    return {
        'question_text': f"計算 {txt} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    res = ua == ca
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }