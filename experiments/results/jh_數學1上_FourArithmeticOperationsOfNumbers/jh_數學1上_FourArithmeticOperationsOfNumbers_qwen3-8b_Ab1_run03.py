# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 85.41s | Tokens: In=513, Out=5667
# Created At: 2026-02-15 15:02:03
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(-5, 5)
    d = random.randint(1, 5)
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    g = random.randint(-5, 5)
    h = random.randint(-5, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)
    
    expr = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×{h}/{i}-{j}|"
    
    part1 = Fraction((a + b) * c, d)
    part2 = Fraction(e, f)
    part3 = Fraction(g * h, i)
    part4 = Fraction(j, 1)
    result = (part1 / part2) + abs(part3 - part4)
    
    correct_answer = str(result)
    
    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_frac = Fraction(user_answer)
        correct_frac = Fraction(correct_answer)
        return {'correct': user_frac == correct_frac, 'result': '正確' if user_frac == correct_frac else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}