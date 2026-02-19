import random

def generate(level=1, **kwargs):
    if level == 1:
        num_range = (-10, 10)
    elif level == 2:
        num_range = (-100, 100)
    else:
        num_range = (-10, 10)
    
    while True:
        a = random.randint(*num_range)
        b = random.randint(*num_range)
        op1 = random.choice(['+', '-'])
        if op1 == '+':
            part1_val = a + b
        else:
            part1_val = a - b
        c = random.randint(1, 10)
        if part1_val % c == 0:
            break
    
    d = random.randint(1, 10)
    
    while True:
        e = random.randint(*num_range)
        f = random.randint(*num_range)
        g = random.randint(*num_range)
        op3 = random.choice(['*', '-'])
        if op3 == '*':
            abs_part = e * f - g
        else:
            abs_part = e - f - g
        break
    
    part1 = f"({a}{op1}{b})"
    part2 = f"{part1}÷{c}×{d}"
    part3 = f"|{e}{op3}{f}-{g}|"
    question_text = f"計算 [{part1}]÷{c}×{d}+{part3} 的值。"
    
    part2_val = (part1_val // c) * d
    abs_val = abs(abs_part)
    correct_answer = str(part2_val + abs_val)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = user_answer.strip()
        correct_answer = correct_answer.strip()
        return {
            'correct': user_answer == correct_answer,
            'result': '正確' if user_answer == correct_answer else '錯誤'
        }
    except:
        return {'correct': False, 'result': '錯誤'}