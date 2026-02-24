import random
import math

def generate(level=1, **kwargs):
    def generate_number():
        if level == 1:
            return random.randint(-10, 10)
        elif level == 2:
            return random.randint(-100, 100)
        else:
            return random.randint(-1000, 1000)

    num1 = generate_number()
    num2 = generate_number()
    num3 = generate_number()
    num4 = generate_number()
    num5 = generate_number()
    num6 = generate_number()
    num7 = generate_number()
    num8 = generate_number()
    num9 = generate_number()
    num10 = generate_number()

    op1 = random.choice(['+', '-', '×', '÷'])
    op2 = random.choice(['+', '-', '×', '÷'])
    op3 = random.choice(['+', '-', '×', '÷'])
    op4 = random.choice(['+', '-', '×', '÷'])
    op5 = random.choice(['+', '-', '×', '÷'])
    op6 = random.choice(['+', '-', '×', '÷'])
    op7 = random.choice(['+', '-', '×', '÷'])
    op8 = random.choice(['+', '-', '×', '÷'])
    op9 = random.choice(['+', '-', '×', '÷'])
    op10 = random.choice(['+', '-', '×', '÷'])

    expression = f"[{num1}{op1}{num2}] {op3} [{num3}{op4}{num4}] {op5} [{num5}{op6}{num6}] {op7} [{num7}{op8}{num8}] {op9} [{num9}{op10}{num10}]"

    try:
        correct_answer = eval(expression)
    except:
        correct_answer = generate_number()

    return {
        'question_text': f'計算 {expression} 的值。',
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        return {'correct': user_answer == correct_answer, 'result': '正確' if user_answer == correct_answer else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}