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
        b = random.randint(1, 100)
        return f"{a}÷{b}"

    def generate_abs():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        return f"|{a}×{b}-5|"

    def generate_complex():
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        c = random.randint(-100, 100)
        d = random.randint(-100, 100)
        e = random.randint(-100, 100)
        f = random.randint(-100, 100)
        g = random.randint(-100, 100)
        h = random.randint(-100, 100)
        return f"[{a}+{b}]÷{c}×{d}+{generate_abs()}+{e}×{f}-{g}÷{h}"

    if level == 1:
        operation = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
        question_text = operation()
    elif level == 2:
        operation1 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
        operation2 = random.choice([generate_addition, generate_subtraction, generate_multiplication, generate_division])
        question_text = f"{operation1()}+{operation2()}"
    elif level == 3:
        question_text = generate_complex()
    else:
        question_text = generate_complex()

    def calculate(expression):
        try:
            return str(eval(expression))
        except:
            return ""

    correct_answer = calculate(question_text)
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
        return {
            'correct': False,
            'result': '錯誤'
        }