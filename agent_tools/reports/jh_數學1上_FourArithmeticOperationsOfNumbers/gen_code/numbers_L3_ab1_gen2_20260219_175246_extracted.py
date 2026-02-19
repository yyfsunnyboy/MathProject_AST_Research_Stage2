import random
import math

def generate_fraction():
    numerator = random.randint(-10, 10)
    denominator = random.randint(1, 10)
    gcd_val = math.gcd(abs(numerator), abs(denominator))
    numerator //= gcd_val
    denominator //= gcd_val
    if denominator < 0:
        numerator *= -1
        denominator *= -1
    return (numerator, denominator)

def add(a, b):
    numerator = a[0] * b[1] + b[0] * a[1]
    denominator = a[1] * b[1]
    return simplify(numerator, denominator)

def subtract(a, b):
    numerator = a[0] * b[1] - b[0] * a[1]
    denominator = a[1] * b[1]
    return simplify(numerator, denominator)

def multiply(a, b):
    numerator = a[0] * b[0]
    denominator = a[1] * b[1]
    return simplify(numerator, denominator)

def divide(a, b):
    return multiply(a, (b[1], b[0]))

def simplify(numerator, denominator):
    gcd_val = math.gcd(abs(numerator), abs(denominator))
    numerator //= gcd_val
    denominator //= gcd_val
    if denominator < 0:
        numerator *= -1
        denominator *= -1
    return (numerator, denominator)

def format_fraction(frac):
    numerator, denominator = frac
    if denominator == 1:
        return str(numerator)
    else:
        return f"{numerator}/{denominator}"

def generate(level=1, **kwargs):
    part1 = generate_fraction()
    part2 = generate_fraction()
    part3 = generate_fraction()
    part4 = generate_fraction()
    part5 = generate_fraction()
    part6 = generate_fraction()
    part7 = generate_fraction()
    
    result1 = add(part1, part2)
    result2 = multiply(result1, part3)
    result3 = divide(result2, part4)
    
    abs_part1 = multiply(part5, part6)
    abs_part2 = subtract(abs_part1, part7)
    if abs_part2[0] < 0:
        abs_part2 = (-abs_part2[0], abs_part2[1])
    
    final_result = add(result3, abs_part2)
    
    question_text = f"[({format_fraction(part1)} + {format_fraction(part2)}) × {format_fraction(part3)} ÷ {format_fraction(part4)}] + |{format_fraction(part5)} × {format_fraction(part6)} - {format_fraction(part7)}|"
    
    correct_answer = format_fraction(final_result)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()
    if ',' in correct_answer:
        correct_answers = correct_answer.split(',')
        return {'correct': user_answer in correct_answers, 'result': '正確' if user_answer in correct_answers else '錯誤'}
    else:
        return {'correct': user_answer == correct_answer, 'result': '正確' if user_answer == correct_answer else '錯誤'}