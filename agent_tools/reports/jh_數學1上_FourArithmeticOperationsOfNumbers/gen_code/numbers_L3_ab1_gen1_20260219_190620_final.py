# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 97.53s | Tokens: In=514, Out=6616
# Created At: 2026-02-19 19:06:20
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    operation = random.choice(['+', '-'])
    part1 = f"({a} {operation} {b})"
    
    c = random.randint(-5, 5)
    d = random.randint(1, 5)
    
    e = random.randint(-5, 5)
    f = random.randint(1, 5)
    
    g = random.randint(-5, 5)
    h = random.randint(-5, 5)
    i = random.randint(-5, 5)
    
    expression = f"[{part1} × {c}/{d}] ÷ {e}/{f} + |{g} × {h} - {i}|"
    
    if operation == '+':
        value1 = Fraction(a) + Fraction(b)
    else:
        value1 = Fraction(a) - Fraction(b)
    
    value2 = value1 * Fraction(c, d)
    value3 = value2 * Fraction(f, e)
    value4 = abs(Fraction(g) * Fraction(h) - Fraction(i))
    result = value3 + value4
    
    if result.denominator == 1:
        correct_answer = f"{result.numerator}"
    else:
        correct_answer = f"{result.numerator}/{result.denominator}"
    
    return {
        'question_text': expression,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer.replace('/', ' '))
    except:
        return {'correct': False, 'result': '錯誤'}
    try:
        correct_fraction = Fraction(correct_answer.replace('/', ' '))
    except:
        return {'correct': False, 'result': '錯誤'}
    if user_fraction == correct_fraction:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}