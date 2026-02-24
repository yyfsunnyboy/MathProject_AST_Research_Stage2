# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 294.25s | Tokens: In=460, Out=425
# Created At: 2026-02-24 12:30:02
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.randint(-12, 12)
    while c == 0:
        c = random.randint(-12, 12)
    
    q1 = random.randint(-10, 10)
    sum_ab = c * q1
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    
    e = random.randint(-12, 12)
    fv = random.randint(-12, 12)
    g = random.randint(-30, 30)
    
    op = random.choice(['+', '-'])
    
    term1 = q1 * d
    term2 = abs(e * fv - g)
    
    if op == '+':
        ans = term1 + term2
    else:
        ans = term1 - term2
        
    expr = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}{op}|{f(e)}×{f(fv)}-{f(g)}|"
    
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