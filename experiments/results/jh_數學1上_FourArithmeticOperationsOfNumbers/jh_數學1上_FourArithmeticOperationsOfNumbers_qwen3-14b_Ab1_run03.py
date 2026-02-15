# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 330.81s | Tokens: In=635, Out=7837
# Created At: 2026-02-15 15:30:10
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import math

def generate_fraction():
    numerator = random.randint(-10, 10)
    denominator = random.randint(1, 10)
    return numerator, denominator

def add_fraction(a_num, a_den, b_num, b_den):
    numerator = a_num * b_den + b_num * a_den
    denominator = a_den * b_den
    gcd_val = math.gcd(abs(numerator), abs(denominator))
    return numerator // gcd_val, denominator // gcd_val

def multiply_fraction(a_num, a_den, b_num, b_den):
    numerator = a_num * b_num
    denominator = a_den * b_den
    gcd_val = math.gcd(abs(numerator), abs(denominator))
    return numerator // gcd_val, denominator // gcd_val

def divide_fraction(a_num, a_den, b_num, b_den):
    return multiply_fraction(a_num, a_den, b_den, b_num)

def subtract_fraction(a_num, a_den, b_num, b_den):
    return add_fraction(a_num, a_den, -b_num, b_den)

def generate(level=1, **kwargs):
    a_num, a_den = generate_fraction()
    b_num, b_den = generate_fraction()
    c_num, c_den = generate_fraction()
    d_num, d_den = generate_fraction()
    e_num, e_den = generate_fraction()
    f_num, f_den = generate_fraction()
    g_num, g_den = generate_fraction()

    bracket_num, bracket_den = add_fraction(-a_num, a_den, b_num, b_den)
    multiply_num, multiply_den = multiply_fraction(bracket_num, bracket_den, c_num, c_den)
    divide_num, divide_den = divide_fraction(multiply_num, multiply_den, d_num, d_den)
    e_f_num, e_f_den = multiply_fraction(e_num, e_den, f_num, f_den)
    subtract_num, subtract_den = subtract_fraction(e_f_num, e_f_den, g_num, g_den)
    abs_num = abs(subtract_num)
    abs_den = subtract_den
    final_num, final_den = add_fraction(divide_num, divide_den, abs_num, abs_den)

    question_text = f"[(-{a_num}/{a_den} + {b_num}/{b_den}) × {c_num}/{c_den}] ÷ ({d_num}/{d_den}) + |{e_num}/{e_den} × {f_num}/{f_den} - {g_num}/{g_den}|"
    if final_den == 1:
        correct_answer = f"{final_num}"
    else:
        correct_answer = f"{final_num}/{final_den}"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct_answers = correct_answer.split(',')
    user_answers = user_answer.split(',')
    for ua in user_answers:
        if ua.strip() in correct_answers:
            return {'correct': True, 'result': '正確'}
    return {'correct': False, 'result': '錯誤'}