# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b-nothink:latest | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 179.54s | Tokens: In=635, Out=4805
# Created At: 2026-02-15 14:08:00
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    signs = ['+', '-']
    
    # 生成括号內運算
    a = Fraction(random.randint(1, 10), random.randint(1, 10))
    b = Fraction(random.randint(1, 10), random.randint(1, 10))
    op1 = random.choice(ops[:2])
    bracket_expr = f'({a} {op1} {b})'
    
    # 生成乘除運算
    c = Fraction(random.randint(1, 10), random.randint(1, 10))
    d = Fraction(random.randint(-10, -1), random.randint(1, 10))
    multiply_divide = f'× {c} ÷ ({d})'
    
    # 生成絕對值運算
    e = Fraction(random.randint(1, 10), random.randint(1, 10))
    f = Fraction(random.randint(1, 10), random.randint(1, 10))
    g = Fraction(random.randint(1, 10), random.randint(1, 10))
    abs_expr = f'|{e} × (-{f}/{g}) - {random.randint(1, 10)}|'
    
    # 組合完整題目
    question_text = f'計算 [{bracket_expr} {multiply_divide}] + {abs_expr} 的值。'
    
    # 計算正確答案
    bracket_value = a + b if op1 == '+' else a - b
    part1 = (bracket_value * c) / d
    abs_value = abs(e * (-f/g) - random.randint(1, 10))
    correct_answer = part1 + abs_value
    
    # 格式化答案
    if correct_answer.denominator == 1:
        correct_answer_str = str(correct_answer.numerator)
    else:
        correct_answer_str = f"{correct_answer.numerator}/{correct_answer.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        correct = user_fraction == correct_fraction
    except:
        correct = False
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }