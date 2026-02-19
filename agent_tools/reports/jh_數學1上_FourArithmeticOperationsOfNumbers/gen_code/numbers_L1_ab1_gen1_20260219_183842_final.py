# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 69.12s | Tokens: In=514, Out=4512
# Created At: 2026-02-19 18:38:42
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    op = random.choice(['+', '-'])
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    g = random.randint(-5, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)
    
    if op == '+':
        part1 = a + b
    else:
        part1 = a - b
    
    part1_fraction = Fraction(part1) * Fraction(c, d)
    part2 = Fraction(e, f)
    part1_divide_part2 = part1_fraction / part2
    
    part3 = Fraction(g) * Fraction(h, i) - Fraction(j)
    part3_abs = abs(part3)
    
    total = part1_divide_part2 + part3_abs
    
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i}) - {j}|"
    correct_answer = str(total)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        return {'correct': user_fraction == correct_fraction, 'result': '正確' if user_fraction == correct_fraction else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}