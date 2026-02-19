import random

def generate(level=1, **kwargs):
    a = random.randint(-100, 100)
    b = random.randint(-100, 100)
    op1 = random.choice(['+', '-'])
    if op1 == '+':
        result1 = a + b
    else:
        result1 = a - b

    while True:
        c = random.randint(-100, 100)
        if c != 0 and result1 % c == 0:
            break

    d = random.randint(-100, 100)

    e = random.randint(-100, 100)
    f = random.randint(-100, 100)
    g = random.randint(-100, 100)
    op2 = random.choice(['*', '×'])
    op3 = random.choice(['-', '+'])
    if op2 == '*':
        result2 = e * f
    else:
        result2 = e * f
    if op3 == '-':
        result3 = result2 - g
    else:
        result3 = result2 + g
    absolute_value = abs(result3)

    result2_main = (result1 // c) * d
    total_result = result2_main + absolute_value

    question_text = f"[{a}{op1}{b}]÷{c}×{d}+|{e}{op2}{f}{op3}{g}|"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(total_result),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }