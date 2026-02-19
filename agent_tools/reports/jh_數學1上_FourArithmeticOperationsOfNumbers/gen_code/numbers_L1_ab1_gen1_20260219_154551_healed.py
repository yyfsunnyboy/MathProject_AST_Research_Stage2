import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def random_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        if denominator == 0:
            denominator = 1
        return Fraction(numerator, denominator)
    
    def format_fraction(frac):
        if frac.denominator == 1:
            return str(frac.numerator)
        else:
            return f"{frac.numerator}/{frac.denominator}"
    
    a = random_fraction()
    b = random_fraction()
    c = random_fraction()
    d = random_fraction()
    while d == 0:
        d = random_fraction()
    e = random_fraction()
    f = random_fraction()
    g = random_fraction()
    
    part1 = f"({format_fraction(-a)} + {format_fraction(b)})"  
    abs_part = f"|{format_fraction(e)} × {format_fraction(f)} - {format_fraction(g)}|"
    question_text = f"[{part1} × {format_fraction(c)}] ÷ {format_fraction(d)} + {abs_part}"
    
    bracket_result = (-a + b)
    multiply_result = bracket_result * c
    division_result = multiply_result / d
    abs_inside = e * f - g
    abs_value = abs(abs_inside)
    total = division_result + abs_value
    
    correct_answer = str(total)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        correct_frac = Fraction(correct_answer)
    except:
        correct_frac = Fraction(0)
    
    try:
        user_frac = Fraction(user_answer)
    except:
        user_frac = Fraction(0)
    
    correct = user_frac == correct_frac
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }