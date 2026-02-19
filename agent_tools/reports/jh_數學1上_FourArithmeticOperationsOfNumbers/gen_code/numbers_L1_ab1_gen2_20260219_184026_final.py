# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 101.32s | Tokens: In=514, Out=6857
# Created At: 2026-02-19 18:40:26
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        range_min = -5
        range_max = 5
    elif level == 2:
        range_min = -10
        range_max = 10
    else:
        range_min = -15
        range_max = 15

    a = random.randint(range_min, range_max)
    b = random.randint(range_min, range_max)
    op1 = random.choice(['+', '-'])

    c = random.randint(1, 10)
    d = random.randint(1, 10)

    e = random.randint(1, 10)
    f = random.randint(1, 10)

    g = random.randint(range_min, range_max)
    h = random.randint(1, 10)
    i = random.randint(1, 10)
    j = random.randint(range_min, range_max)

    part1 = f"[({a}{op1}{b})×{c}/{d}]"
    part2 = f"÷({e}/{f})"
    part3 = f" + |{g}×({h}/{i})-{j}|"

    question_text = part1 + part2 + part3

    part1_val = Fraction(a + b) if op1 == '+' else Fraction(a - b)
    part2_val = part1_val * Fraction(c, d)
    part3_val = part2_val * Fraction(f, e)
    abs_part = Fraction(g * h, i) - j
    abs_part = abs(abs_part)
    total = part3_val + abs_part

    correct_answer = str(Fraction(total).limit_denominator())

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    from fractions import Fraction
    try:
        user_frac = Fraction(user_answer)
        correct_frac = Fraction(correct_answer)
        return {'correct': user_frac == correct_frac, 'result': '正確' if user_frac == correct_frac else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}