import random
import math

def generate(level=1, **kwargs):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a

    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    op1 = random.choice(['+', '-'])
    part1 = f"({a} {op1} {b})"

    c = random.randint(1, 5)
    d = random.randint(1, 5)
    part2 = f"× {c}/{d}"

    e = random.randint(1, 5)
    f = random.randint(1, 5)
    part3 = f"÷ {e}/{f}"

    g = random.randint(1, 5)
    h1 = random.randint(1, 5)
    h2 = random.randint(1, 5)
    i = random.randint(1, 5)
    part4 = f"|{g} × {h1}/{h2} - {i}|"

    question_text = f"計算 [{part1}{part2}{part3}] + {part4} 的值。"

    numerator1 = (a + b) * c
    denominator1 = d
    numerator1 *= f
    denominator1 *= e

    numerator2 = g * h1 - i * h2
    denominator2 = h2
    numerator2 = abs(numerator2)
    denominator2 = abs(denominator2)

    total_numerator = numerator1 * denominator2 + numerator2 * denominator1
    total_denominator = denominator1 * denominator2

    gcd_val = gcd(total_numerator, total_denominator)
    simplified_numerator = total_numerator // gcd_val
    simplified_denominator = total_denominator // gcd_val

    if simplified_denominator < 0:
        simplified_numerator = -simplified_numerator
        simplified_denominator = -simplified_denominator

    if simplified_denominator == 1:
        correct_answer = f"{simplified_numerator}"
    else:
        correct_answer = f"{simplified_numerator}/{simplified_denominator}"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    if '/' in user_answer:
        user_num, user_den = map(int, user_answer.split('/'))
    else:
        user_num = int(user_answer)
        user_den = 1

    if '/' in correct_answer:
        correct_num, correct_den = map(int, correct_answer.split('/'))
    else:
        correct_num = int(correct_answer)
        correct_den = 1

    return {
        'correct': (user_num * correct_den == correct_num * user_den),
        'result': '正確' if (user_num * correct_den == correct_num * user_den) else '錯誤'
    }