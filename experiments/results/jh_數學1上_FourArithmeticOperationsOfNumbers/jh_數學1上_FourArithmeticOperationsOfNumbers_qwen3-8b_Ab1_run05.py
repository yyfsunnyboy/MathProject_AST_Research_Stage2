# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 149.33s | Tokens: In=513, Out=9485
# Created At: 2026-02-15 15:06:14
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import math

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(-10, 10)
    d = random.randint(1, 10)
    e = random.randint(-10, 10)
    f = random.randint(1, 10)
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(1, 10)
    j = random.randint(-10, 10)
    
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i}) - {j}|"
    
    value1 = (-a + b)
    numerator1 = value1 * c
    denominator1 = d
    numerator2 = numerator1 * f
    denominator2 = denominator1 * e
    gcd1 = math.gcd(numerator2, denominator2)
    simplified_num1 = numerator2 // gcd1
    simplified_den1 = denominator2 // gcd1
    if simplified_den1 < 0:
        simplified_num1 *= -1
        simplified_den1 *= -1
    
    numerator3 = g * h
    denominator3 = i
    numerator4 = numerator3 - j * denominator3
    denominator4 = denominator3
    abs_numerator = abs(numerator4)
    abs_denominator = denominator4
    
    total_numerator = simplified_num1 * abs_denominator + abs_numerator * simplified_den1
    total_denominator = simplified_den1 * abs_denominator
    gcd_total = math.gcd(total_numerator, total_denominator)
    final_num = total_numerator // gcd_total
    final_den = total_denominator // gcd_total
    if final_den < 0:
        final_num *= -1
        final_den *= -1
    
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
    def parse_answer(ans):
        if '/' in ans:
            num_str, den_str = ans.split('/')
            num = int(num_str)
            den = int(den_str)
            if den == 0:
                return None
            gcd_val = math.gcd(num, den)
            simplified_num = num // gcd_val
            simplified_den = den // gcd_val
            if simplified_den < 0:
                simplified_num *= -1
                simplified_den *= -1
            return (simplified_num, simplified_den)
        else:
            try:
                num = int(ans)
                return (num, 1)
            except:
                return None
    
    user_num, user_den = parse_answer(user_answer)
    if user_num is None:
        return {'correct': False, 'result': '錯誤'}
    
    correct_parts = correct_answer.split('/')
    if len(correct_parts) == 1:
        correct_num = int(correct_parts[0])
        correct_den = 1
    else:
        correct_num = int(correct_parts[0])
        correct_den = int(correct_parts[1])
    
    gcd_correct = math.gcd(correct_num, correct_den)
    simplified_correct_num = correct_num // gcd_correct
    simplified_correct_den = correct_den // gcd_correct
    if simplified_correct_den < 0:
        simplified_correct_num *= -1
        simplified_correct_den *= -1
    
    if user_num == simplified_correct_num and user_den == simplified_correct_den:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}