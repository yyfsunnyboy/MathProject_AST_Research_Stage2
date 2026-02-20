import random

def generate(level=1, **kwargs):
    if level == 1:
        num_range = (-10, 10)
    elif level == 2:
        num_range = (-100, 100)
    else:
        num_range = (-10, 10)
    
    a = random.randint(*num_range)
    b = random.randint(*num_range)
    c = random.randint(*num_range)
    d = random.randint(*num_range)
    e = random.randint(*num_range)
    f = random.randint(*num_range)
    g = random.randint(*num_range)
    
    while c == 0:
        c = random.randint(*num_range)
    while d == 0:
        d = random.randint(*num_range)
    while g == 0:
        g = random.randint(*num_range)
    
    op1 = random.choice(['+', '-', '*', '/'])
    op2 = random.choice(['+', '-', '*', '/'])
    op3 = random.choice(['+', '-', '*', '/'])
    op4 = random.choice(['+', '-', '*', '/'])
    
    part1 = f"({a}{op1}{b})"
    part2 = f"({c}{op2}{d})"
    part3 = f"({e}{op3}{f})"
    part4 = f"({g})"
    
    question_text = f"[{part1}]÷{part2}×{part3}+|{part4}|"
    
    expr = question_text.replace('÷', '/').replace('×', '*')
    correct_answer = str(eval(expr))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }