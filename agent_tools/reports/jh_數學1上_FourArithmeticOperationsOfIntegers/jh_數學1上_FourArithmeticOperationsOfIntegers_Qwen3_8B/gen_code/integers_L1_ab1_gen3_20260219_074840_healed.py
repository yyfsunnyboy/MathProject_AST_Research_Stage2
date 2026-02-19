import random

def generate(level=1, **kwargs):
    import random
    c = random.randint(-10, 10)
    while c == 0:
        c = random.randint(-10, 10)
    k = random.randint(-5, 5)
    numerator = c * k
    a = random.randint(-20, 20)
    b = numerator - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-10, 10)
    expr = f"([{a} + {b}]) ÷ {c} × {d} + |{e} × {f} - {g}|"
    expr_abs = expr.replace('|', 'abs(').replace('|', ')')
    expr_abs = expr_abs.replace('÷', '/').replace('×', '*')
    try:
        correct = eval(expr_abs)
    except:
        return generate(level)
    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': str(int(correct)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}