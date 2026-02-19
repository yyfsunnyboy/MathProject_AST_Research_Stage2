# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 259.60s | Tokens: In=514, Out=15874
# Created At: 2026-02-19 18:58:36
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    def simplify(numerator, denominator):
        if denominator == 0:
            return (0, 1)
        gcd_val = math.gcd(abs(numerator), abs(denominator))
        numerator //= gcd_val
        denominator //= gcd_val
        if denominator < 0:
            numerator *= -1
            denominator *= -1
        return (numerator, denominator)

    def add_fractions(a_num, a_den, b_num, b_den):
        num = a_num * b_den + b_num * a_den
        den = a_den * b_den
        return simplify(num, den)

    def multiply_fractions(a_num, a_den, b_num, b_den):
        num = a_num * b_num
        den = a_den * b_den
        return simplify(num, den)

    def divide_fractions(a_num, a_den, b_num, b_den):
        num = a_num * b_den
        den = a_den * b_num
        return simplify(num, den)

    def abs_fraction(num, den):
        return (abs(num), den)

    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(1, 5)
    g = random.randint(-5, 5)
    h = random.randint(1, 5)
    i = random.randint(1, 5)
    j = random.randint(-5, 5)

    part1_num = a + b
    part1_num, part1_den = multiply_fractions(part1_num, 1, c, d)
    part1_num, part1_den = divide_fractions(part1_num, part1_den, e, f)

    part2_num = g * h
    part2_num = part2_num - j * i
    part2_num, part2_den = abs_fraction(part2_num, i)

    total_num = part1_num * part2_den + part2_num * part1_den
    total_den = part1_den * part2_den
    total_num, total_den = simplify(total_num, total_den)

    question_text = f"計算 [({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h}/{i})-{j}| 的值。"
    correct_answer = f"{total_num}/{total_den}" if total_den != 1 else f"{total_num}"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = user_answer.strip()
        correct_answer = correct_answer.strip()
        if user_answer == correct_answer:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}