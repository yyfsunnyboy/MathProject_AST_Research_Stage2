import random
from fractions import Fraction
from math import gcd

def simplify_fraction(numerator, denominator):
    if denominator == 0:
        raise ValueError("Denominator cannot be zero")
    if denominator < 0:
        numerator *= -1
        denominator *= -1
    g = gcd(abs(numerator), denominator)
    return numerator // g, denominator // g

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        d = random.randint(1, 10)
        e = random.randint(-10, 10)
        f = random.randint(1, 10)
        g = random.randint(-10, 10)
        h = random.randint(-10, 10)
        i = random.randint(-10, 10)
        c_simplified, d_simplified = simplify_fraction(c, d)
        e_simplified, f_simplified = simplify_fraction(e, f)
        part1 = f"[({a}+{b})×{c_simplified}/{d_simplified}]÷({e_simplified}/{f_simplified})"
        part2 = f"|{g}×{h}-{i}|"
        question_text = f"計算 {part1} + {part2} 的值。"
        part1_val = Fraction((a + b) * c, d) / Fraction(e, f)
        part2_val = abs(Fraction(g * h) - i)
        correct_answer = part1_val + part2_val
        correct_answer_str = str(correct_answer)
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer_str,
            'mode': 1
        }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }