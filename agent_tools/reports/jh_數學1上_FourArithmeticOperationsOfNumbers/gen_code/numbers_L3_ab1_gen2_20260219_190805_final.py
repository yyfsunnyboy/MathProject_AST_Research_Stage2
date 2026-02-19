# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 102.50s | Tokens: In=514, Out=6938
# Created At: 2026-02-19 19:08:05
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    operator = random.choice(['+', '-'])
    if operator == '+':
        bracket_result = a + b
    else:
        bracket_result = a - b
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    e = random.randint(1, 10)
    f = random.randint(1, 10)
    k = random.randint(-10, 10)
    l = random.randint(-10, 10)
    m = random.randint(-10, 10)
    question_text = f"計算 [({a}{operator}{b})×{c}/{d}]÷({e}/{f}) + |{k}×{l}-{m}| 的值。"
    part1 = Fraction(bracket_result * c, d)
    part1 = part1 * Fraction(f, e)
    abs_part = abs(k * l - m)
    correct_answer = part1 + abs_part
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