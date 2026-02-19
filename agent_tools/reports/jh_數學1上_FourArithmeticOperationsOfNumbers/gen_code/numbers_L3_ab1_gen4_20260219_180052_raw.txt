import random
import math

def generate(level=1, **kwargs):
    def standardize(num, den):
        if den < 0:
            num = -num
            den = -den
        return num, den
    
    def simplify(num, den):
        if den == 0:
            return (0, 1)
        gcd_val = math.gcd(abs(num), abs(den))
        return (num // gcd_val, den // gcd_val)
    
    def format_fraction(num, den):
        if den == 1:
            return f"{num}"
        return f"{num}/{den}"
    
    def add(a_num, a_den, b_num, b_den):
        num = a_num * b_den + b_num * a_den
        den = a_den * b_den
        return simplify(num, den)
    
    def multiply(a_num, a_den, b_num, b_den):
        num = a_num * b_num
        den = a_den * b_den
        return simplify(num, den)
    
    def divide(a_num, a_den, b_num, b_den):
        return multiply(a_num, a_den, b_den, b_num)
    
    def subtract(a_num, a_den, b_num, b_den):
        return add(a_num, a_den, -b_num, b_den)
    
    def abs_value(num, den):
        if num < 0:
            return (-num, den)
        return (num, den)
    
    a_num = random.randint(-10, 10)
    a_den = random.randint(1, 10)
    a_num, a_den = standardize(a_num, a_den)
    
    b_num = random.randint(-10, 10)
    b_den = random.randint(1, 10)
    b_num, b_den = standardize(b_num, b_den)
    
    c_num = random.randint(-10, 10)
    c_den = random.randint(1, 10)
    c_num, c_den = standardize(c_num, c_den)
    
    d_num = random.randint(-10, 10)
    d_den = random.randint(1, 10)
    d_num, d_den = standardize(d_num, d_den)
    
    e_num = random.randint(-10, 10)
    e_den = random.randint(1, 10)
    e_num, e_den = standardize(e_num, e_den)
    
    f_num = random.randint(-10, 10)
    f_den = random.randint(1, 10)
    f_num, f_den = standardize(f_num, f_den)
    
    g_num = random.randint(-10, 10)
    g_den = random.randint(1, 10)
    g_num, g_den = standardize(g_num, g_den)
    
    h_num = random.randint(-10, 10)
    h_den = random.randint(1, 10)
    h_num, h_den = standardize(h_num, h_den)
    
    part1_num, part1_den = add(a_num, a_den, b_num, b_den)
    part2_num, part2_den = multiply(part1_num, part1_den, c_num, c_den)
    part3_num, part3_den = divide(part2_num, part2_den, d_num, d_den)
    
    part4_num, part4_den = multiply(e_num, e_den, f_num, f_den)
    part5_num, part5_den = subtract(part4_num, part4_den, g_num, g_den)
    part6_num, part6_den = abs_value(part5_num, part5_den)
    
    final_num, final_den = add(part3_num, part3_den, part6_num, part6_den)
    
    question_text = f"[({format_fraction(a_num, a_den)} + {format_fraction(b_num, b_den)}) × {format_fraction(c_num, c_den)}] ÷ ({format_fraction(d_num, d_den)}) + |{format_fraction(e_num, e_den)} × {format_fraction(f_num, f_den)} - {format_fraction(g_num, g_den)}|"
    
    correct_answer = format_fraction(final_num, final_den)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }