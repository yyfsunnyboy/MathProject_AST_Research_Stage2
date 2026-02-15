# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 215.42s | Tokens: In=635, Out=5176
# Created At: 2026-02-15 15:24:39
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = FAILED: maximum recursion depth exceeded
# ==============================================================================

import random
import math

def generate(level=1, **kwargs):
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        if denominator == 0:
            denominator = 1
        g = math.gcd(abs(numerator), denominator)
        numerator //= g
        denominator //= g
        if denominator < 0:
            numerator *= -1
            denominator *= -1
        return (numerator, denominator)
    
    def fraction_to_str(numerator, denominator):
        if denominator == 1:
            return str(numerator)
        else:
            return f"{numerator}/{denominator}"
    
    a_num, a_den = generate_fraction()
    b_num, b_den = generate_fraction()
    c_num, c_den = generate_fraction()
    d_num, d_den = generate_fraction()
    e_num, e_den = generate_fraction()
    f_num, f_den = generate_fraction()
    g_num, g_den = generate_fraction()
    
    a_str = fraction_to_str(a_num, a_den)
    b_str = fraction_to_str(b_num, b_den)
    c_str = fraction_to_str(c_num, c_den)
    d_str = fraction_to_str(d_num, d_den)
    e_str = fraction_to_str(e_num, e_den)
    f_str = fraction_to_str(f_num, f_den)
    g_str = fraction_to_str(g_num, g_den)
    
    question_text = f"[({a_str} + {b_str}) × {c_str}] ÷ {d_str} + |{e_str} × {f_str} - {g_str}|"
    
    expr = question_text.replace('×', '*').replace('÷', '/')
    try:
        correct_value = eval(expr)
    except:
        return generate(level, **kwargs)
    
    def float_to_fraction(f):
        s = str(f)
        if '.' in s:
            integer_part, decimal_part = s.split('.')
            decimal_part = decimal_part.rstrip('0')
            if not decimal_part:
                return s
            denominator = 10 ** len(decimal_part)
            numerator = int(integer_part + decimal_part)
            g = math.gcd(numerator, denominator)
            numerator //= g
            denominator //= g
            if denominator == 1:
                return str(numerator)
            else:
                return f"{numerator}/{denominator}"
        else:
            return s
    
    correct_answer_str = float_to_fraction(correct_value)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct_answers = correct_answer.split(',')
    user_answers = user_answer.split(',')
    
    for ua in user_answers:
        if ua.strip() in correct_answers:
            return {'correct': True, 'result': '正確'}
    return {'correct': False, 'result': '錯誤'}