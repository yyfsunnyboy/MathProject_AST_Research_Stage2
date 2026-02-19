import random
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def simplify_fraction(numerator, denominator):
    if denominator == 0:
        raise ValueError("Denominator cannot be zero")
    if denominator < 0:
        numerator *= -1
        denominator *= -1
    common_divisor = gcd(abs(numerator), abs(denominator))
    numerator //= common_divisor
    denominator //= common_divisor
    return numerator, denominator

def generate_part1():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    num1 = (-a + b)
    den1 = 1
    num_part1 = num1 * c
    den_part1 = den1 * d
    num_part1, den_part1 = simplify_fraction(num_part1, den_part1)
    part1_str = f"({-a}+{b})×{c}/{d}"
    return part1_str, (num_part1, den_part1)

def generate_part2():
    e = random.randint(1, 10)
    f = random.randint(1, 10)
    num_part2 = -e
    den_part2 = f
    num_part2, den_part2 = simplify_fraction(num_part2, den_part2)
    part2_str = f"-{e}/{f}"
    return part2_str, (num_part2, den_part2)

def generate_part3():
    g = random.randint(1, 10)
    h = random.randint(1, 10)
    i = random.randint(1, 10)
    j = random.randint(1, 10)
    num1 = g * h
    den1 = i
    num1, den1 = simplify_fraction(num1, den1)
    num_part3 = num1 * 1 - j * den1
    den_part3 = den1 * 1
    num_part3, den_part3 = simplify_fraction(num_part3, den_part3)
    part3_str = f"{g}×{h}/{i}-{j}"
    return part3_str, (num_part3, den_part3)

def calculate_expression(part1_num, part1_den, part2_num, part2_den, part3_num, part3_den):
    num_step1 = part1_num * part2_den
    den_step1 = part1_den * part2_num
    num_step1, den_step1 = simplify_fraction(num_step, den_step1)
    part3_abs_num = abs(part3_num)
    part3_abs_den = part3_den
    num_total = num_step1 * part3_abs_den + part3_abs_num * den_step1
    den_total = den_step1 * part3_abs_den
    num_total, den_total = simplify_fraction(num_total, den_total)
    return num_total, den_total

def generate(level=1, **kwargs):
    part1_str, part1_num_den = generate_part1()
    part2_str, part2_num_den = generate_part2()
    part3_str, part3_num_den = generate_part3()
    question_text = f"計算 [{part1_str}]÷{part2_str} + |{part3_str}| 的值。"
    num_total, den_total = calculate_expression(part1_num_den[0], part1_num_den[1], part2_num_den[0], part2_num_den[1], part3_num_den[0], part3_num_den[1])
    if den_total == 1:
        correct_answer = f"{num_total}"
    else:
        correct_answer = f"{num_total}/{den_total}"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    def parse_user_answer(user_answer):
        if '/' in user_answer:
            parts = user_answer.split('/')
            if len(parts) == 2:
                numerator = int(parts[0])
                denominator = int(parts[1])
                return numerator, denominator
            else:
                return None, None
        elif user_answer.isdigit():
            return int(user_answer), 1
        elif ' ' in user_answer:
            whole, fraction = user_answer.split()
            whole_num = int(whole)
            frac_parts = fraction.split('/')
            if len(frac_parts) == 2:
                frac_num = int(frac_parts[0])
                frac_den = int(frac_parts[1])
                numerator = whole_num * frac_den + frac_num
                denominator = frac_den
                return numerator, denominator
            else:
                return None, None
        else:
            return None, None
    user_num, user_den = parse_user_answer(user_answer)
    correct_parts = correct_answer.split('/')
    if len(correct_parts) == 1:
        correct_num = int(correct_parts[0])
        correct_den = 1
    else:
        correct_num = int(correct_parts[0])
        correct_den = int(correct_parts[1])
    if user_den == 0 or correct_den == 0:
        return {'correct': False, 'result': '錯誤'}
    if user_num * correct_den == correct_num * user_den:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}