# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 35.26s | Tokens: In=460, Out=411
# Created At: 2026-02-23 00:06:05
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-10, 11) if i != 0])
    r1 = random.randint(-10, 10)
    div = c * r1
    a = random.randint(-30, 30)
    b = div - a
    d = random.randint(-10, 10)
    e = random.randint(2, 12)
    f = random.randint(-10, -2)
    g = random.randint(-20, 20)
    
    v1 = r1 * d
    v2 = abs(e * f - g)
    
    op = random.choice(['+', '-'])
    if op == '+':
        ans = v1 + v2
    else:
        ans = v1 - v2
        
    q = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}{op}|{e}×{p(f)}-{p(g)}|"
    
    return {
        'question_text': f"計算 {q} 的值。",
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