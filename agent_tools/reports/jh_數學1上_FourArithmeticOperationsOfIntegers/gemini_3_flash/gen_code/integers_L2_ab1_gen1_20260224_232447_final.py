# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 46.17s | Tokens: In=460, Out=441
# Created At: 2026-02-24 23:24:47
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-12, 13) if i != 0])
    m = random.randint(-10, 10)
    a = random.randint(-30, 30)
    b = (c * m) - a
    d = random.randint(-10, 10)
    
    e = random.randint(-10, 10)
    g = random.randint(-10, 10)
    h = random.randint(-30, 30)
    
    op_mid = random.choice(['+', '-'])
    
    p1 = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}"
    p2 = f"|{f(e)}×{f(g)}{'+' if h >= 0 else '-'}{abs(h)}|"
    
    val1 = m * d
    val2 = abs(e * g + h)
    
    if op_mid == '+':
        ans = val1 + val2
    else:
        ans = val1 - val2
        
    return {
        'question_text': f"計算 {p1}{op_mid}{p2} 的值。",
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