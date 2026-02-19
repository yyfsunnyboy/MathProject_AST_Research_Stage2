# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 110.50s | Tokens: In=514, Out=7432
# Created At: 2026-02-19 18:44:32
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    op1 = random.choice(['+', '-'])
    part1 = f"({a}{op1}{b})×{c}/{d}"
    
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    part2 = f"[{part1}]÷{e}/{f}"
    
    g = random.randint(1, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(1, 5)
    part3 = f"|{g}×{h}/{i}-{j}|"
    
    question_text = f"{part2} + {part3}"
    
    part1_val = Fraction(a + b) * Fraction(c, d)
    part2_val = part1_val * Fraction(f, e)
    abs_part = Fraction(g) * Fraction(h, i) - Fraction(j)
    abs_val = abs(abs_part)
    correct_answer = part2_val + abs_val
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