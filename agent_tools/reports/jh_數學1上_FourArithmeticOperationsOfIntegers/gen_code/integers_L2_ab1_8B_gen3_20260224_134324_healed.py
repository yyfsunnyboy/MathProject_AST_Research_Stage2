import random
import math

def generate(level=1, **kwargs):
    def generate_number():
        if level == 1:
            return random.randint(-10, 10)
        elif level == 2:
            return random.randint(-100, 100)
        elif level == 3:
            return random.randint(-1000, 1000)
        else:
            return random.randint(-10000, 10000)

    a = generate_number()
    b = generate_number()
    c = generate_number()
    d = generate_number()
    e = generate_number()
    f = generate_number()
    g = generate_number()
    h = generate_number()
    i = generate_number()
    j = generate_number()
    
    op1 = random.choice(['+', '-', '×', '÷'])
    op2 = random.choice(['+', '-', '×', '÷'])
    op3 = random.choice(['+', '-', '×', '÷'])
    op4 = random.choice(['+', '-', '×', '÷'])
    op5 = random.choice(['+', '-', '×', '÷'])
    op6 = random.choice(['+', '-', '×', '÷'])
    op7 = random.choice(['+', '-', '×', '÷'])
    op8 = random.choice(['+', '-', '×', '÷'])
    op9 = random.choice(['+', '-', '×', '÷'])
    
    question_text = f'計算 [{a}{op1}{b}{op2}{c}]{op3}{d}{op4}{e}×{f}+|{g}{op5}{h}{op6}{i}|{op7}{j}'
    correct_answer = str(eval(question_text.replace('×', '*').replace('÷', '/').replace('|', '').replace('|', '')))
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
        if user_answer == correct_answer:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}