import random
import math

def generate(level=1, **kwargs):
    question_text = ''
    answer = ''
    correct_answer = ''
    mode = 1
    operations = ['+', '-', '*', '/']
    radicals = []
    for _ in range(4):
        radicand = random.randint(1, 100)
        sqrt = math.isqrt(radicand)
        if sqrt * sqrt == radicand:
            radicand = radicand // sqrt
            radicals.append(f"{sqrt}\\sqrt{{{radicand}}}")
        else:
            radicals.append(f"\\sqrt{{{radicand}}}")
    op1 = random.choice(operations)
    op2 = random.choice(operations)
    op3 = random.choice(operations)
    op4 = random.choice(operations)
    op5 = random.choice(operations)
    op6 = random.choice(operations)
    question_text = f"化簡 $({radicals[0]} {op1} {radicals[1]} {op2} {radicals[2]} {op3} {radicals[3]}) + ({radicals[4]} {op4} {radicals[5]} {op5} {radicals[6]} {op6} {radicals[7]})$"
    correct_answer = f"{random.randint(1, 10)}\\sqrt{{{random.randint(1, 10)}}}"
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}