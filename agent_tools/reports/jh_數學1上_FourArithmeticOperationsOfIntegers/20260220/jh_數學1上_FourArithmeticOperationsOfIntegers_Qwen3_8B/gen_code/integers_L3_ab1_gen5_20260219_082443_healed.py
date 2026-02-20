import random

def generate(level=1, **kwargs):
    a = random.randint(-100, 100)
    b = random.randint(-100, 100)
    op1 = random.choice(['+', '-'])
    parentheses_expr = f"({a} {op1} {b})"
    parentheses_result = a + b if op1 == '+' else a - b

    c = random.randint(1, 10)
    while parentheses_result % c != 0:
        c = random.randint(1, 10)
    div_result = parentheses_result // c

    d = random.randint(1, 10)
    mul_result = div_result * d

    e = random.randint(-100, 100)
    f = random.randint(-100, 100)
    g = random.randint(-100, 100)
    abs_expr = f"|{e} × {f} - {g}|"
    abs_result = abs(e * f - g)

    question_text = f"{parentheses_expr} ÷ {c} × {d} + {abs_expr}"
    correct_answer = str(mul_result + abs_result)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_num = int(user_answer)
        correct_num = int(correct_answer)
        return {'correct': user_num == correct_num, 'result': '正確' if user_num == correct_num else '錯誤'}
    except ValueError:
        return {'correct': False, 'result': '錯誤'}