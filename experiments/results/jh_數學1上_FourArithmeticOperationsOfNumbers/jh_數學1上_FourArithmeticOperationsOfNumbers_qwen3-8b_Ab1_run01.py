# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 92.73s | Tokens: In=513, Out=5988
# Created At: 2026-02-15 14:59:23
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(1, 5)
    g = random.randint(-5, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)
    
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i})-{j}|"
    
    part1 = (a + b) * Fraction(c, d)
    part2 = part1 / Fraction(e, f)
    abs_part = abs(g * Fraction(h, i) - j)
    correct_answer = part2 + abs_part
    
    correct_answer_str = str(correct_answer)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        return {'correct': user_fraction == correct_fraction, 'result': '正確' if user_fraction == correct_fraction else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}