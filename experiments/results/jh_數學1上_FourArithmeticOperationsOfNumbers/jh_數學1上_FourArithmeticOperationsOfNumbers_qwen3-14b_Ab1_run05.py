# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 131.47s | Tokens: In=635, Out=3174
# Created At: 2026-02-15 15:37:20
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = Fraction(random.randint(-10, 10), random.randint(1, 10))
    b = Fraction(random.randint(-10, 10), random.randint(1, 10))
    c = Fraction(random.randint(-10, 10), random.randint(1, 10))
    d = Fraction(random.randint(-10, 10), random.randint(1, 10))
    while d == 0:
        d = Fraction(random.randint(-10, 10), random.randint(1, 10))
    e = Fraction(random.randint(-10, 10), random.randint(1, 10))
    f = Fraction(random.randint(-10, 10), random.randint(1, 10))
    g = Fraction(random.randint(-10, 10), random.randint(1, 10))
    
    part1 = f"({a} + {b})"
    part2 = f"×{c}"
    part3 = f"÷({d})"
    part4 = f"|{e}×{f} - {g}|"
    
    question_text = f"計算 ${part1}{part2}{part3} + {part4}$ 的值。"
    
    val1 = (a + b) * c
    val2 = val1 / d
    val3 = abs(e * f - g)
    correct_answer = val2 + val3
    
    if correct_answer.denominator == 1:
        correct_answer_str = str(correct_answer.numerator)
    else:
        correct_answer_str = f"{correct_answer.numerator}/{correct_answer.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }