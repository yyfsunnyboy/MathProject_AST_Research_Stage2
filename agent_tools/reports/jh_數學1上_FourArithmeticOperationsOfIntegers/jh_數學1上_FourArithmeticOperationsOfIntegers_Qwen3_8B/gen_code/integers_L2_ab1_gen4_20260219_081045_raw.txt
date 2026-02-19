import random

def generate(level=1, **kwargs):
    if level == 1:
        min_val = -10
        max_val = 10
    elif level == 2:
        min_val = -100
        max_val = 100
    else:
        min_val = -100
        max_val = 100

    a = random.randint(min_val, max_val)
    b = random.randint(min_val, max_val)
    c = random.randint(min_val, max_val)
    while True:
        d = random.randint(min_val, max_val)
        if d != 0 and ((a + b) * c) % d == 0:
            break

    e = random.randint(min_val, max_val)
    f = random.randint(min_val, max_val)
    g = random.randint(min_val, max_val)

    main_expr = f"(({a}) + ({b})) × ({c}) ÷ ({d})"
    abs_expr = f"| ({e}) × ({f}) - ({g}) |"
    question_text = f"{main_expr} + {abs_expr}"

    expr = question_text.replace("×", "*").replace("÷", "/")
    expr = expr.replace("|", "abs(", 1).replace("|", ")", 1)

    correct_answer = eval(expr)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }