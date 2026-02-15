# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 101.34s | Tokens: In=513, Out=6679
# Created At: 2026-02-15 15:03:44
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    op1 = random.choice(['+', '-'])
    part1_value = a + b if op1 == '+' else a - b
    part1_str = f"({a}{op1}{b})"
    
    numerator1 = random.randint(1, 5)
    denominator1 = random.randint(2, 5)
    part2_value = Fraction(numerator1, denominator1)
    part2_str = f"{numerator1}/{denominator1}"
    
    numerator2 = random.randint(1, 5)
    denominator2 = random.randint(2, 5)
    part3_value = Fraction(-numerator2, denominator2)
    part3_str = f"-{numerator2}/{denominator2}"
    
    c = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(2, 5)
    part4_value = Fraction(c * e, f)
    d = random.randint(1, 5)
    part5_value = d
    absolute_value = abs(part4_value - part5_value)
    part4_str = f"{c}×({e}/{f})"
    part5_str = str(d)
    
    question_text = f"計算 [{part1_str}×{part2_str}]÷{part3_str} + |{part4_str}-{part5_str}|"
    
    result_part1 = part1_value * part2_value
    result_part1 = result_part1 / part3_value
    result = result_part1 + absolute_value
    correct_answer = str(result)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct_fraction = Fraction(correct_answer)
    try:
        user_fraction = Fraction(user_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    if user_fraction == correct_fraction:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}