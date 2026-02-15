# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 74.23s | Tokens: In=513, Out=4945
# Created At: 2026-02-15 15:00:38
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(1, 5)
    g = random.randint(1, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    
    part1 = f"({a} + {b})"
    part2 = f"× {c}/{d}"
    part3 = f"÷ {e}/{f}"
    part4 = f"|{g} × {h}/{i} - {i}|"
    
    question_text = f"計算 [{part1}{part2}{part3}] + {part4} 的值。"
    
    part1_val = Fraction(a + b, 1)
    part1_val *= Fraction(c, d)
    part1_val *= Fraction(f, e)
    
    abs_part = Fraction(g * h, i) - Fraction(i, 1)
    abs_val = abs(abs_part)
    
    correct_answer = part1_val + abs_val
    correct_answer_str = str(correct_answer)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_frac = Fraction(user_answer)
        correct_frac = Fraction(correct_answer)
        return {'correct': user_frac == correct_frac, 'result': '正確' if user_frac == correct_frac else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}