import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c_num = random.randint(1, 5)
    c_den = random.randint(1, 5)
    d_num = random.randint(1, 5)
    d_den = random.randint(1, 5)
    part1 = f"[({a}+{b})×{c_num}/{c_den}÷{d_num}/{d_den}]"
    
    e = random.randint(-10, 10)
    f_num = random.randint(1, 5)
    f_den = random.randint(1, 5)
    g = random.randint(-10, 10)
    part2 = f"|{e}×{f_num}/{f_den}-{g}|"
    
    question = f"計算 {part1} + {part2} 的值。"
    
    part1_value = ((Fraction(a, 1) + Fraction(b, 1)) * Fraction(c_num, c_den)) / Fraction(d_num, d_den)
    part2_value = abs(Fraction(e, 1) * Fraction(f_num, f_den) - Fraction(g, 1))
    correct_answer = part1_value + part2_value
    
    if correct_answer.denominator == 1:
        correct_answer_str = f"{correct_answer.numerator}"
    else:
        correct_answer_str = f"{correct_answer.numerator}/{correct_answer.denominator}"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }