# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 40.88s | Tokens: In=460, Out=457
# Created At: 2026-02-23 00:18:01
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    r1 = 10 + level * 2
    r2 = 20 + level * 5
    
    c = random.choice([i for i in range(-r1, r1 + 1) if i != 0])
    m = random.randint(-10, 10)
    sum_ab = c * m
    a = random.randint(-r2, r2)
    b = sum_ab - a
    d = random.randint(-10, 10)
    e = random.randint(-r1, r1)
    f = random.randint(-r1, r1)
    g = random.randint(-r2, r2)
    
    val1 = (sum_ab // c) * d
    val2 = abs(e * f + g)
    ans = val1 + val2
    
    sa, sb, sc, sd, se, sf = p(a), p(b), p(c), p(d), p(e), p(f)
    sg_op = "+" if g >= 0 else "-"
    sg_val = abs(g)
    
    expr = f"[{sa}+{sb}]÷{sc}×{sd}+|{se}×{sf}{sg_op}{sg_val}|"
    
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