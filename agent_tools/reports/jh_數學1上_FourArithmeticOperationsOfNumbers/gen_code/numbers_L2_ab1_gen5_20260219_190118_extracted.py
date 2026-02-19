import random
import math

def simplify_fraction(num, den):
    if den == 0:
        return (num, den)
    gcd_val = math.gcd(abs(num), abs(den))
    simplified_num = num // gcd_val
    simplified_den = den // gcd_val
    if simplified_den < 0:
        simplified_num *= -1
        simplified_den *= -1
    return (simplified_num, simplified_den)

def multiply_int_fraction(int_val, numerator, denominator):
    num = int_val * numerator
    den = denominator
    return simplify_fraction(num, den)

def divide_fractions(frac1, frac2):
    num = frac1[0] * frac2[1]
    den = frac1[1] * frac2[0]
    return simplify_fraction(num, den)

def add_fractions(frac1, frac2):
    num = frac1[0] * frac2[1] + frac2[0] * frac1[1]
    den = frac1[1] * frac2[1]
    return simplify_fraction(num, den)

def subtract_fractions(frac, int_val):
    num = frac[0] - int_val * frac[1]
    den = frac[1]
    return simplify_fraction(num, den)

def format_fraction(frac):
    num, den = frac
    if den == 1:
        return f"{num}"
    else:
        return f"{num}/{den}"

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    numerator_c = random.randint(-10, 10)
    denominator_c = random.randint(1, 10)
    numerator_d = random.randint(-10, 10)
    denominator_d = random.randint(1, 10)
    e = random.randint(-10, 10)
    numerator_f = random.randint(-10, 10)
    denominator_f = random.randint(1, 10)
    g = random.randint(-10, 10)

    left_part = f"({a}+{b})×{numerator_c}/{denominator_c}"
    right_part = f"{numerator_d}/{denominator_d}"
    main_part = f"[{left_part}]÷{right_part}"
    abs_part = f"{e}×{numerator_f}/{denominator_f}-{g}"
    question_text = f"{main_part} + |{abs_part}|"

    sum_ab = a + b
    left_value = multiply_int_fraction(sum_ab, numerator_c, denominator_c)
    main_value = divide_fractions(left_value, (numerator_d, denominator_d))

    product_ef = multiply_int_fraction(e, numerator_f, denominator_f)
    abs_value = subtract_fractions(product_ef, g)
    abs_value = abs(abs_value)
    final_answer = add_fractions(main_value, abs_value)

    correct_answer = format_fraction(final_answer)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }