# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 303.26s | Tokens: In=470, Out=669
# Created At: 2026-02-15 16:05:09
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_s(f):
        if f.denominator == 1:
            return str(f.numerator)
        return f"{f.numerator}/{f.denominator}"
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    
    c_num = random.randint(1, 9)
    c_den = random.randint(2, 9)
    c = Fraction(c_num, c_den)
    
    d_num = random.choice([i for i in range(-9, 10) if i != 0])
    d_den = random.randint(2, 9)
    d = Fraction(d_num, d_den)
    
    e = random.randint(-10, 10)
    while e == 0:
        e = random.randint(-10, 10)
        
    f_num = random.choice([i for i in range(-9, 10) if i != 0])
    f_den = random.randint(2, 9)
    f = Fraction(f_num, f_den)
    
    g = random.randint(-10, 10)
    
    val1 = (Fraction(a + b) * c) / d
    val2 = abs(Fraction(e) * f + g)
    ans = val1 + val2
    
    sa = str(a)
    sb = f"+{b}" if b >= 0 else str(b)
    sc = f_s(c)
    sd = f_s(d)
    if d < 0:
        sd = f"({sd})"
    se = str(e)
    sf = f_s(f)
    if f < 0:
        sf = f"({sf})"
    sg = f"+{g}" if g >= 0 else str(g)
    
    txt = f"計算 [({sa}{sb})×{sc}]÷{sd} + |{se}×{sf}{sg}| 的值。"
    
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': f_s(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(' ', '')
    ca = str(correct_answer).strip().replace(' ', '')
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }