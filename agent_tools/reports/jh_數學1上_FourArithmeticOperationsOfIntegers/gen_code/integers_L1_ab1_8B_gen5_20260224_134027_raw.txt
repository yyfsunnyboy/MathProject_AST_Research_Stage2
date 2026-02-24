import random
import math

def generate(level=1, **kwargs):
    def generate_addition():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        return f"{a}+{b}"

    def generate_subtraction():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        return f"{a}-{b}"

    def generate_multiplication():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        return f"{a}×{b}"

    def generate_division():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        while b == 0:
            b = random.randint(-100, 100)
        return f"{a}÷{b}"

    def generate_abs():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        return f"|{a}×{b}-5|"

    def generate_expression():
        if level == 1:
            op1 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op2 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            return f"{op1()} {op2()}"

        elif level == 2:
            op1 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op2 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op3 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            return f"{op1()} {op2()} {op3()}"

        elif level == 3:
            op1 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op2 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op3 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op4 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            return f"{op1()} {op2()} {op3()} {op4()}"

        elif level == 4:
            op1 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op2 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op3 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op4 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            op5 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
            return f"{op1()} {op2()} {op3()} {op4()} {op5()}"

        else:
            return generate_expression()

    expression = generate_expression()
    question_text = f"計算 {expression} 的值。"
    try:
        correct_answer = eval(expression.replace("×", "*").replace("÷", "/"))
        correct_answer = str(int(correct_answer))
    except:
        correct_answer = "0"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        return {'correct': user_answer == correct_answer, 'result': '正確' if user_answer == correct_answer else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}