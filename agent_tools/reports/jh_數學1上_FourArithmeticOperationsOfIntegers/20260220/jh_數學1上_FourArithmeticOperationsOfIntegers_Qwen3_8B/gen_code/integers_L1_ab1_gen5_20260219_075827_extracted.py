import random

def generate(level=1, **kwargs):
    part1 = generate_bracket()
    part2 = generate_abs()
    op = random.choice(['+', '-', '*', '/'])
    full_expr = f"{part1}{op}{part2}"
    python_expr = convert_to_python(full_expr)
    correct_value = eval(python_expr)
    return {
        'question_text': full_expr,
        'answer': '',
        'correct_answer': str(correct_value),
        'mode': 1
    }

def generate_bracket():
    a = random.randint(-100, 100)
    b = random.randint(-100, 100)
    op = random.choice(['+', '-', '*', '/'])
    if op == '/':
        while True:
            b = random.randint(1, 100)
            if b != 0 and a % b == 0:
                break
    return f"({a}{op}{b})"

def generate_abs():
    c = random.randint(-100, 100)
    d = random.randint(-100, 100)
    op = random.choice(['+', '-', '*', '/'])
    if op == '/':
        while True:
            d = random.randint(1, 100)
            if d != 0 and c % d == 0:
                break
    return f"|{c}{op}{d}|"

def convert_to_python(expr):
    expr = expr.replace('÷', '/')
    expr = expr.replace('×', '*')
    expr = expr.replace('−', '-')
    expr = expr.replace('+', '+')
    expr = expr.replace('|', 'abs(', 1).replace('|', ')', 1)
    return expr

def check(user_answer, correct_answer):
    try:
        user_val = int(user_answer)
        correct_val = int(correct_answer)
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}