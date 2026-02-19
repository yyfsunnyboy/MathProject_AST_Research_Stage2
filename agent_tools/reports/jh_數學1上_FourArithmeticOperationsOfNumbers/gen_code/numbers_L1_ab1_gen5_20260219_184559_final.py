# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 84.73s | Tokens: In=514, Out=5810
# Created At: 2026-02-19 18:45:59
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
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
    question_text = f"計算 [({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i})-{j}| 的值。"
    num1 = a + b
    part1 = Fraction(num1 * c, d) / Fraction(e, f)
    abs_part = Fraction(g * h, i) - j
    abs_part = abs(abs_part)
    total = part1 + abs_part
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
    try:
        user_frac = Fraction(user_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    try:
        correct_frac = Fraction(correct_answer)
    except:
        return {'correct': False, 'result': '錯誤'}
    if user_frac == correct_frac:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}