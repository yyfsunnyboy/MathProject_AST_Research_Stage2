# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 304.38s | Tokens: In=470, Out=507
# Created At: 2026-02-15 16:10:14
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(v, p=False):
        s = str(v)
        if p and v < 0:
            return f"({s})"
        return s
    
    def get_f():
        den = random.randint(2, 9)
        num = random.choice([i for i in range(-9, 10) if i != 0 and i % den != 0])
        return Fraction(num, den)
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    f1 = get_f()
    f2 = get_f()
    g = random.randint(-10, 10)
    f3 = get_f()
    j = random.randint(-10, 10)
    
    val1 = (a + b) * f1
    val2 = val1 / f2
    val3 = abs(g * f3 + j)
    ans = val2 + val3
    
    op1 = "+" if b >= 0 else ""
    op2 = "+" if j >= 0 else ""
    
    term1 = f"[({a}{op1}{b})×{fmt(f1)}]"
    term2 = f"{term1}÷{fmt(f2, True)}"
    term3 = f"|{g}×{fmt(f3, True)}{op2}{j}|"
    
    question = f"計算 {term2} + {term3} 的值。"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(" ", "")
    ca = str(correct_answer).strip().replace(" ", "")
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }