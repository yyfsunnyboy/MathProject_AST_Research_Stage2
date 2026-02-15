# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3:8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 98.35s | Tokens: In=513, Out=6297
# Created At: 2026-02-15 14:45:16
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-5, 5)
        frac_range = (-5, 5)
    elif level == 2:
        int_range = (-10, 10)
        frac_range = (-10, 10)
    else:
        int_range = (-10, 10)
        frac_range = (-10, 10)

    a = random.randint(*int_range)
    b = random.randint(*int_range)
    while True:
        c = random.randint(*frac_range)
        d = random.randint(*frac_range)
        if d != 0:
            break
    while True:
        e = random.randint(*frac_range)
        f = random.randint(*frac_range)
        if f != 0:
            break
    g = random.randint(*int_range)
    h = random.randint(*int_range)
    i = random.randint(*int_range)

    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×{h}-{i}|"

    part1 = (a + b) * Fraction(c, d)
    part2 = part1 / Fraction(e, f)
    abs_part = abs(g * h - i)
    total = part2 + abs_part

    if total.denominator == 1:
        correct_answer = f"{total.numerator}"
    else:
        correct_answer = f"{total.numerator}/{total.denominator}"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_str = user_answer.replace(' ', '').replace('⁄', '/')
    correct_str = correct_answer.replace(' ', '').replace('⁄', '/')
    try:
        user_fraction = Fraction(user_str)
        correct_fraction = Fraction(correct_str)
        correct = user_fraction == correct_fraction
    except:
        correct = False
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }