# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 272.24s | Tokens: In=636, Out=5399
# Created At: 2026-02-19 16:10:41
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)

def simplify(numerator, denominator):
    if denominator == 0:
        raise ValueError("Denominator cannot be zero")
    common_divisor = gcd(abs(numerator), abs(denominator))
    simplified_num = numerator // common_divisor
    simplified_den = denominator // common_divisor
    if simplified_den < 0:
        simplified_num *= -1
        simplified_den *= -1
    return (simplified_num, simplified_den)

def format_fraction(numerator, denominator):
    if denominator < 0:
        numerator *= -1
        denominator *= -1
    if denominator == 1:
        return f"{numerator}"
    else:
        return f"{numerator}/{denominator}"

def generate_fraction():
    numerator = random.randint(-10, 10)
    denominator = random.randint(1, 10)
    return (numerator, denominator)

def add(frac1, frac2):
    num1, den1 = frac1
    num2, den2 = frac2
    new_num = num1 * den2 + num2 * den1
    new_den = den1 * den2
    return simplify(new_num, new_den)

def subtract(frac1, frac2):
    num1, den1 = frac1
    num2, den2 = frac2
    new_num = num1 * den2 - num2 * den1
    new_den = den1 * den2
    return simplify(new_num, new_den)

def multiply(frac1, frac2):
    num1, den1 = frac1
    num2, den2 = frac2
    new_num = num1 * num2
    new_den = den1 * den2
    return simplify(new_num, new_den)

def divide(frac1, frac2):
    if frac2[0] == 0:
        raise ValueError("Division by zero")
    num1, den1 = frac1
    num2, den2 = frac2
    new_num = num1 * den2
    new_den = den1 * num2
    return simplify(new_num, new_den)

def generate(level=1, **kwargs):
    a_num, a_den = generate_fraction()
    b_num, b_den = generate_fraction()
    c_num, c_den = generate_fraction()
    d_num, d_den = generate_fraction()
    e_num, e_den = generate_fraction()
    f_num, f_den = generate_fraction()
    g_num, g_den = generate_fraction()
    
    part1 = f"({format_fraction(a_num, a_den)}+{format_fraction(b_num, b_den)})×{format_fraction(c_num, c_den)}"
    part2 = f"÷({format_fraction(d_num, d_den)}) + |{format_fraction(e_num, e_den)}×{format_fraction(f_num, f_den)}-{format_fraction(g_num, g_den)}|"
    question_text = f"計算 `{part1}{part2}` 的值。"
    
    add_result = add((a_num, a_den), (b_num, b_den))
    multiply_result = multiply(add_result, (c_num, c_den))
    divide_result = divide(multiply_result, (d_num, d_den))
    
    abs_part_multiply = multiply((e_num, e_den), (f_num, f_den))
    abs_part_subtract = subtract(abs_part_multiply, (g_num, g_den))
    abs_num = abs(abs_part_subtract[0])
    abs_den = abs(abs_part_subtract[1])
    abs_result = (abs_num, abs_den)
    
    total_result = add(divide_result, abs_result)
    
    if total_result[1] == 1:
        correct_answer = f"{total_result[0]}"
    else:
        correct_answer = f"{total_result[0]}/{total_result[1]}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answers = correct_answer.split(',') if ',' in correct_answer else [correct_answer]
    for ans in correct_answers:
        ans = ans.strip()
        if user_answer == ans:
            return {'correct': True, 'result': '正確'}
    return {'correct': False, 'result': '錯誤'}