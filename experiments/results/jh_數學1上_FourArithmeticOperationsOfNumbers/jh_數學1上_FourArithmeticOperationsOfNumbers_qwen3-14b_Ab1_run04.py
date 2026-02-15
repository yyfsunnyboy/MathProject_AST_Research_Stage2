# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 298.48s | Tokens: In=635, Out=7114
# Created At: 2026-02-15 15:35:08
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = FAILED: maximum recursion depth exceeded
# ==============================================================================

import random
import re
from fractions import Fraction

def generate(level=1, **kwargs):
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        if denominator < 0:
            numerator *= -1
            denominator *= -1
        return numerator, denominator
    
    def replace_fractions(expr):
        pattern = r'(-?\d+)/(\d+)'
        def repl(match):
            numerator = match.group(1)
            denominator = match.group(2)
            return f'Fraction({numerator}, {denominator})'
        return re.sub(pattern, repl, expr)
    
    def fraction_to_string(frac):
        numerator = frac.numerator
        denominator = frac.denominator
        if denominator == 1:
            return f"{numerator}"
        else:
            return f"{numerator}/{denominator}"
    
    a, b = generate_fraction()
    c, d = generate_fraction()
    e, f = generate_fraction()
    g, h = generate_fraction()
    i, j = generate_fraction()
    
    question_text = f"[(-{a} + {b}) * {c}/{d}] / ({e}/{f}) + abs({g} * {h}/{i} - {j})"
    
    expr = replace_fractions(question_text)
    
    try:
        correct_answer_value = eval(expr)
    except:
        return generate(level=level, **kwargs)
    
    correct_answer_str = fraction_to_string(correct_answer_value)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        correct_fraction = Fraction(correct_answer)
    except:
        correct_fraction = Fraction(correct_answer, 1)
    
    try:
        user_fraction = Fraction(user_answer)
    except:
        user_fraction = Fraction(user_answer, 1)
    
    correct = user_fraction == correct_fraction
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }