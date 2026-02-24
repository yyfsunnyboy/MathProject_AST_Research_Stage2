# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 29.26s | Tokens: In=460, Out=806
# Created At: 2026-02-24 12:53:59
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def fmt(n, bracket=True):
        return f"({n})" if n < 0 and bracket else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        c = random.choice([i for i in range(-10, 11) if i != 0])
        m = random.randint(-5, 5)
        s = c * m
        a = random.randint(-20, 20)
        b = s - a
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-20, 20)
        q = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}+|{fmt(e)}×{fmt(f)}+{fmt(g)}|"
        ans = (a + b) // c * d + abs(e * f + g)
    elif t == 2:
        e = random.choice([i for i in range(-10, 11) if i != 0])
        m = random.randint(-10, 10)
        d = e * m
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-10, 10)
        h = random.randint(-10, 10)
        q = f"{fmt(a)}×({fmt(b)}-{fmt(c)})+{fmt(d)}÷{fmt(e)}-|{fmt(f)}×{fmt(g)}+{fmt(h)}|"
        ans = a * (b - c) + (d // e) - abs(f * g + h)
    else:
        f = random.choice([i for i in range(-10, 11) if i != 0])
        m = random.randint(-10, 10)
        s = f * m
        d = random.randint(-20, 20)
        e = s - d
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-20, 20)
        g = random.randint(-10, 10)
        q = f"|{fmt(a)}×{fmt(b)}+{fmt(c)}|-({fmt(d)}+{fmt(e)})÷{fmt(f)}×{fmt(g)}"
        ans = abs(a * b + c) - (d + e) // f * g

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }